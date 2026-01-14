import numpy as np
import logging
import asyncio
import sounddevice as sd
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
load_dotenv()
logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

class Resampler:
    """Optimized resampler for 24kHz -> 48kHz (exact 2x)"""
    def __init__(self, input_rate=24000, output_rate=48000, target_dtype=np.int16, input_dtype=np.int16):
        self.input_rate = input_rate
        self.output_rate = output_rate
        self.ratio = output_rate / input_rate
        logger.info("Resampler: %d Hz -> %d Hz (ratio: %.2f)", 
                   input_rate, output_rate, self.ratio)
        
        # Keep previous sample for interpolation continuity
        self.prev_sample = 0.
        self.target_dtype = target_dtype
        self.input_dtype = input_dtype
    
    def process(self, pcm16_bytes: bytes) -> np.ndarray:
        if len(pcm16_bytes) == 0:
            return np.array([], dtype=self.target_dtype)
        
        # Convert int16 to float32 [-1, 1]
        samples = np.frombuffer(pcm16_bytes, dtype=self.input_dtype).astype(np.float32) / 32768.0
        
        if len(samples) == 0:
            return np.array([], dtype=self.target_dtype)

        if self.input_rate == self.output_rate:
            return samples.astype(self.target_dtype)

        # Simple and fast 2x upsampling with linear interpolation
        output_len = int(len(samples) * (self.output_rate / self.input_rate))
        upsampled = np.zeros(int(output_len), dtype=np.float32)
        
        # First sample uses previous chunk's last sample
        upsampled[0] = (self.prev_sample + samples[0]) * 0.5
        upsampled[1] = samples[0]
        
        # Interleave original samples and interpolated values
        for i in range(1, len(samples)):
            upsampled[i*2] = (samples[i-1] + samples[i]) * 0.5  # Interpolated
            upsampled[i*2 + 1] = samples[i]  # Original
        
        # Save last sample for next chunk
        self.prev_sample = samples[-1]
        return upsampled.astype(self.target_dtype)


async def openai_tts_realtime(
    text: str, 
    voice: str = "coral",
    target_sample_rate: int = 48000,
    target_dtype: np.dtype = np.int16,
    white_buffer_seconds: float = 1 # 1 second of silence at the beginning
):
    logger.info("Starting TTS for text: '%s...'", text[:50])

    resampler = Resampler(
        input_rate=24000, 
        output_rate=target_sample_rate,
        target_dtype=target_dtype,
        input_dtype=np.int16
    )
    
    client = AsyncOpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
    )

    logger.info("Requesting TTS from OpenAI...")
    chunk_count = 0

    if white_buffer_seconds > 0:
        silence = np.zeros(int(white_buffer_seconds * target_sample_rate), dtype=target_dtype)
    else:
        silence = None

    async with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice=voice,
        input=text,
        instructions="Speak loud, fast and clearly.",
        response_format="pcm",
    ) as response:
        async for chunk in response.iter_bytes(chunk_size=2048):  # Increased from 4096
            if not chunk:
                continue

            # Resample 24kHz -> 48kHz
            resampled = resampler.process(chunk)
            
            if len(resampled) > 0:
                if chunk_count == 0 and silence is not None:
                    yield silence

                chunk_count += 1
                yield resampled.reshape(-1, 1)

        logger.info("TTS completed. Total chunks: %d", chunk_count)
            



async def main():
    text = "Hello, how are you? This is a test of Darren's streaming text to speech test. I am speaking in a cheerful and positive tone. Today, I would like to share with you a story about a cat. My cat's name is Whiskers. He is a very cute and playful cat. He loves to chase after balls and play with his toys. He is also very friendly and loves to cuddle with me. He is a very good cat and I love him very much."
    sd.default.device = "0"
    sd.default.latency = "high"
    sd.default.blocksize = 1024
    with sd.OutputStream(
            samplerate=48000,
            channels=1,
            dtype=np.float32,
            blocksize=1024,
    ) as stream:
            async for chunk in openai_tts_realtime(
                text, 
                voice="coral", 
                target_sample_rate=48000, 
                target_dtype=np.float32,
                white_buffer_seconds=.5
            ):
                stream.write(chunk)

if __name__ == "__main__":
    asyncio.run(main())