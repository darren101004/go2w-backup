import asyncio
import logging
import queue
from typing import Any, AsyncGenerator, Callable, Union
import os

import numpy as np
import numpy.typing as npt
import sounddevice as sd
from openai import AsyncOpenAI
from dotenv import load_dotenv
from scipy import signal

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

SAMPLE_RATE = 48000
INPUT_SAMPLE_RATE = 24000
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE_URL = os.getenv("OPENAI_API_BASE_URL")

class LocalAudioPlayer:
    def __init__(self, should_stop: Union[Callable[[], bool], None] = None):
        self.channels = 1
        self.dtype = np.float32
        self.should_stop = should_stop
        # Much larger buffer for Jetson
        self.device = 0  

        self.blocksize = 4096  # Increased from 2048
        logger.info("Initialized LocalAudioPlayer with blocksize=%s", self.blocksize)

    async def play_stream(
        self,
        buffer_stream: AsyncGenerator[Union[npt.NDArray[np.float32], None], None],
        sample_rate: int = SAMPLE_RATE,
    ) -> None:
        logger.info("Starting play_stream with sample_rate=%d...", sample_rate)
        loop = asyncio.get_event_loop()
        event = asyncio.Event()
        
        # Much larger queue
        buffer_queue: queue.Queue[Union[npt.NDArray[np.float32], None]] = queue.Queue(maxsize=200)
        
        # Pre-buffer some data before starting playback
        prebuffer_count = 10
        prebuffer_done = asyncio.Event()

        async def buffer_producer():
            logger.info("Starting buffer producer...")
            count = 0
            async for buffer in buffer_stream:
                if buffer is None:
                    logger.info("Received None, finishing producer.")
                    break
                
                # Ensure correct dtype and shape
                if buffer.dtype != np.float32:
                    buffer = buffer.astype(np.float32)
                if buffer.ndim == 1:
                    buffer = buffer.reshape(-1, 1)
                
                await loop.run_in_executor(None, buffer_queue.put, buffer)
                count += 1
                
                # Signal when prebuffer is ready
                if count == prebuffer_count:
                    prebuffer_done.set()
                    logger.info("Prebuffer complete (%d chunks)", prebuffer_count)
            
            logger.info("Producer finished. Total chunks: %d", count)
            await loop.run_in_executor(None, buffer_queue.put, None)

        current_buffer = None
        buffer_pos = 0

        def callback(outdata: npt.NDArray[np.float32], frame_count: int, 
                    _time_info: Any, _status: Any):
            nonlocal current_buffer, buffer_pos

            if _status:
                logger.warning("Audio callback status: %s", _status)

            frames_written = 0
            while frames_written < frame_count:
                if current_buffer is None or buffer_pos >= len(current_buffer):
                    try:
                        current_buffer = buffer_queue.get_nowait()
                        if current_buffer is None:
                            logger.info("Stream ended, stopping playback.")
                            outdata[frames_written:] = 0
                            loop.call_soon_threadsafe(event.set)
                            raise sd.CallbackStop
                        buffer_pos = 0
                    except queue.Empty:
                        logger.warning("Buffer underrun at frame %d/%d (queue size: %d)", 
                                     frames_written, frame_count, buffer_queue.qsize())
                        outdata[frames_written:] = 0
                        return

                remaining = len(current_buffer) - buffer_pos
                to_write = min(frame_count - frames_written, remaining)
                outdata[frames_written:frames_written + to_write] = \
                    current_buffer[buffer_pos:buffer_pos + to_write]
                buffer_pos += to_write
                frames_written += to_write

        # Start producer
        producer_task = asyncio.create_task(buffer_producer())
        
        # Wait for prebuffer
        logger.info("Waiting for prebuffer...")
        await prebuffer_done.wait()
        
        # List available devices
        logger.info("Available audio devices:")
        logger.info(sd.query_devices())
        
        logger.info("Opening audio stream with high latency settings...")
        try:
            with sd.OutputStream(
                samplerate=sample_rate,
                channels=self.channels,
                dtype=self.dtype,
                callback=callback,
                blocksize=self.blocksize,
                latency='high',  # Explicit high latency
                prime_output_buffers_using_stream_callback=False,
                device=self.device,
            ):
                logger.info("Stream opened, queue size: %d", buffer_queue.qsize())
                await event.wait()
        except Exception as e:
            logger.error("Error in audio stream: %s", e)
            raise
        finally:
            await producer_task
            logger.info("play_stream finished.")


class Resampler:
    """Optimized resampler for 24kHz -> 48kHz (exact 2x)"""
    def __init__(self, input_rate=24000, output_rate=48000):
        self.input_rate = input_rate
        self.output_rate = output_rate
        self.ratio = output_rate / input_rate
        logger.info("Resampler: %d Hz -> %d Hz (ratio: %.2f)", 
                   input_rate, output_rate, self.ratio)
        
        # Keep previous sample for interpolation continuity
        self.prev_sample = 0.0
    
    def process(self, pcm16_bytes: bytes) -> np.ndarray:
        if len(pcm16_bytes) == 0:
            return np.array([], dtype=np.float32)
        
        # Convert int16 to float32 [-1, 1]
        samples = np.frombuffer(pcm16_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        
        if len(samples) == 0:
            return np.array([], dtype=np.float32)
        
        # Simple and fast 2x upsampling with linear interpolation
        output_len = len(samples) * 2
        upsampled = np.zeros(output_len, dtype=np.float32)
        
        # First sample uses previous chunk's last sample
        upsampled[0] = (self.prev_sample + samples[0]) * 0.5
        upsampled[1] = samples[0]
        
        # Interleave original samples and interpolated values
        for i in range(1, len(samples)):
            upsampled[i*2] = (samples[i-1] + samples[i]) * 0.5  # Interpolated
            upsampled[i*2 + 1] = samples[i]  # Original
        
        # Save last sample for next chunk
        self.prev_sample = samples[-1]
        
        return upsampled


async def openai_tts_realtime(text: str, voice: str = "coral"):
    logger.info("Starting TTS for text: '%s...'", text[:50])
    resampler = Resampler(input_rate=INPUT_SAMPLE_RATE, output_rate=SAMPLE_RATE)
    
    client = AsyncOpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_API_BASE_URL,
    )

    logger.info("Requesting TTS from OpenAI...")
    chunk_count = 0
    async with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice=voice,
        input=text,
        response_format="pcm",
    ) as response:
        # Larger chunks = fewer iterations = less overhead
        async for chunk in response.iter_bytes(chunk_size=8192):  # Increased from 4096
            if not chunk:
                continue

            # Resample 24kHz -> 48kHz
            resampled = resampler.process(chunk)
            
            if len(resampled) > 0:
                chunk_count += 1
                yield resampled.reshape(-1, 1)
        
        logger.info("TTS completed. Total chunks: %d", chunk_count)


PARA = " Hello! I see the robot is in an office environment with several desks, computers, chairs, and a whiteboard in the center of its view. There are people working at some desks"

async def main():
    logger.info("=== Audio Test Starting ===")
    
    # Test audio device first
    try:
        logger.info("Testing audio device...")
        sd.check_output_settings(samplerate=SAMPLE_RATE, channels=1, dtype=np.float32)
        logger.info("Audio device OK")
    except Exception as e:
        logger.error("Audio device error: %s", e)
        return
    
    player = LocalAudioPlayer()
    await player.play_stream(openai_tts_realtime(PARA))
    logger.info("=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(main())