from abc import ABC, abstractmethod 
import cv2 
from typing import Any, Callable
import logging
import time
import threading
import numpy as np
import queue
import sounddevice as sd
import dataclasses
import glob
import base64 

@dataclasses.dataclass
class SpeechData:
    data: np.ndarray
    sample_rate: int
    channels: int

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class IDevice(ABC):
    def __init__(self):
        self.callbacks: list[Callable[[Any], None]] = []
        self.running: bool = False

    def register_callback(self, callback: Callable[[Any], None]):
        self.callbacks.append(callback)

    def unregister_callback(self, callback):
        try:
            self.callbacks.remove(callback)
        except ValueError:
            logger.error(f"Callback not found: {callback}")
            pass

    @abstractmethod
    def get_device_info(self) -> dict[str, Any]:
        return {}

    @abstractmethod
    def run():
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def stop(self):
        raise NotImplementedError("Subclasses must implement this method")

def get_available_video_capture_device_ids() -> list[int | str]:
    available_device_ids: list[int | str] = []
 
    for device_id in glob.glob("/dev/video*"):
        cap = cv2.VideoCapture(device_id)
        if not cap.isOpened():
            continue

        cap.release()
        available_device_ids.append(device_id)

    return available_device_ids


def get_available_speaker_device_ids() -> list[int | str]:
    devices = sd.query_devices()
    return [
        sd.default.device[0],
        *[device["index"] 
        for device in devices 
        if device["max_output_channels"] > 0
        and ("hw:" in device["name"].lower() or "plughw:" in device["name"].lower())]
    ]


def get_available_audio_capture_device_ids() -> list[int | str]:
    devices = sd.query_devices()
    return [
        sd.default.device[1],
        *[device["index"] 
        for device in devices 
        if device["max_input_channels"] > 0
        and ("hw:" in device["name"].lower() or "plughw:" in device["name"].lower())]
    ]


class VideoCaptureDevice(IDevice):
    def __init__(
        self,
        device_id: int | str, 
        fps: int = 5,
        max_width: int = 384
    ):
        super().__init__()

        self.device_id: int | str = device_id
        self.fps: int = fps
        self.max_width: int = max_width 
        self.lock = threading.Lock()
        self.frame = None

    def get_device_info(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "device_name": "VideoCaptureDevice",
            "device_type": "video",
            "device_status": "connected",
            "fps": self.fps,
            "max_width": self.max_width
        }

    def run(self):
        self.running = True
        cap = cv2.VideoCapture(self.device_id)

        fps = cap.get(cv2.CAP_PROP_FPS)
        h, w = cap.get(cv2.CAP_PROP_FRAME_HEIGHT), cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        

        interval = 0 if fps < self.fps else 1 / self.fps - 1e-5
        last_frame_time = time.time() 

        while self.running:
            ret, frame = cap.read()
            current_time = time.time()

            if not ret:
                logger.warning("Failed to read frame from video capture device")
                break

            if current_time - last_frame_time < interval:
                continue

            new_w = min(w, self.max_width)
            new_h = int(h * (new_w / w)) 

            frame = cv2.resize(frame, (new_w, new_h))

            for callback in self.callbacks:
                callback(frame)

            last_frame_time = current_time

            with self.lock:
                self.frame = frame

        cap.release()

    def stop(self):
        self.running = False
        self.frame = None


class SpeakerDevice(IDevice):
    def __init__(self, device_id: int | str, interval: float = 0.3):
        super().__init__()

        self.device_id: int | str = device_id
        self.queue: queue.Queue[SpeechData] = queue.Queue()
        self.interval: float = interval

    def get_device_info(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "device_name": "SpeakerDevice",
            "device_type": "speaker",
            "device_status": "connected"
        }

    def run(self):
        self.running = True

        while self.running:
            speech_data = self.queue.get()

            sd.play(
                data=speech_data.data,
                samplerate=speech_data.sample_rate,
                device=self.device_id,
                blocking=True
            )

            time.sleep(self.interval)

    def speak(self, data: SpeechData):
        self.queue.put(data)

    def stop(self):
        self.running = False

class AudioCaptureDevice(IDevice):
    def __init__(self, device_id: int | str):
        super().__init__()

        self.device_id: int | str = device_id

    def get_device_info(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "device_name": "AudioCaptureDevice",
            "device_type": "audio",
            "device_status": "connected"
        }

    def run(self):
        self.running = True

        while self.running:
            data = sd.rec(frames=1024, samplerate=44100, channels=2, dtype='int16')
            sd.wait()
            self.callbacks.append(data)

def image_filter(messages: list[dict[str, Any]], k: int = 2) -> list[dict[str, Any]]:
    total_images = sum(
        1 for message in messages if message["role"] == "user"
        and any(content["type"] == "image_url" for content in message["content"])
    )

    if total_images <= k:
        return messages

    to_removed = total_images - k

    for i in range(len(messages)):
        if messages[i]["role"] == "user" and any(content["type"] == "image_url" for content in messages[i]["content"]):
            to_removed -= 1

            messages[i]["content"] = [
                content for content in messages[i]["content"]
                if content["type"] == "image_url"
            ]

            if to_removed == 0:
                break

    return messages

def imgb64(frame: np.ndarray, extension: str = '.jpg', quality: int = 90) -> str:
    _, buffer = cv2.imencode(extension, frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return f"data:image/{extension[1:]};base64,{base64.b64encode(buffer).decode('utf-8')}"

import asyncio
from typing import Awaitable


def sync2async(func: Callable[[], Any]) -> Callable[[], Awaitable[Any]]:
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper if asyncio.iscoroutinefunction(func) else func

@dataclasses.dataclass
class SessionInput:
    get_input: Callable[[], str]
    send_response: Callable[[str], None] = lambda x: logger.info(f"Robot: {x}") 
    send_tool_result: Callable[[Any, Any], None] = lambda x, y: logger.info(f"call: {x} --> {y}") 
    context: list[dict[str, Any]] = dataclasses.field(default_factory=list)
    interactive: bool = True

class Session:
    max_img_width: int = 384

    def __init__(
        self,
        ses_input: SessionInput,
        video_capture_device: VideoCaptureDevice | None = None,
        audio_capture_device: AudioCaptureDevice | None = None,
        speaker_device: SpeakerDevice | None = None,
        patience: int = 10
    ):
        self.interactive: bool = ses_input.interactive
        self.context: list[dict[str, Any]] = ses_input.context or []

        self.video_capture_device: VideoCaptureDevice | None = video_capture_device
        self.audio_capture_device: AudioCaptureDevice | None = audio_capture_device
        self.speaker_device: SpeakerDevice | None = speaker_device

        self.patience: int = patience

        self.get_input: Callable[[], str] = sync2async(ses_input.get_input)
        self.send_response: Callable[[str], None] = sync2async(ses_input.send_response)
        self.send_tool_result: Callable[[Any, Any], None] = sync2async(ses_input.send_tool_result)

    async def build_complete_context(self) -> list[dict[str, Any]]:
        msg_content = [
            {
                "type": "text",
                "text": await asyncio.wait_for(
                    self.get_input(), 
                    timeout=self.patience
                )
            }
        ]

        if self.video_capture_device is not None:
            msg_content.append( 
                {
                    "type": "image_url",
                    "image_url": {
                        "url": imgb64(self.video_capture_device.frame, quality=70)
                    }
                },
                {
                    "type": "text",
                    "text": "<system-reminder>The image include more information.</system-reminder>"
                }
            )

        prebuilt_context = self.context + [
            {
                "role": "user",
                "content": msg_content
            }
        ]

        return image_filter(prebuilt_context, k=2)

    async def run(self) -> bool:

        while True:
            messages: list[dict[str, Any]] = await self.build_complete_context()

            # @todo: call llm

            # @todo: execute tool

            if not self.interactive:
                break

        return True

class RobotBrain():
    def __init__(self):
        self.que: queue.Queue[SessionInput] = queue.Queue()
        self.running: bool = False

        self.video_capture_device_ids: list[int | str] = get_available_video_capture_device_ids()
        self.audio_capture_device_ids: list[int | str] = get_available_audio_capture_device_ids()
        self.speaker_device_ids: list[int | str] = get_available_speaker_device_ids()

        self.video_capture_device: VideoCaptureDevice | None = None
        self.audio_capture_device: AudioCaptureDevice | None = None
        self.speaker_device: SpeakerDevice | None = None
        self.patience: int = 10 # 10 seconds wait for interactive session

        if len(self.video_capture_device_ids) > 0:
            self.video_capture_device = VideoCaptureDevice(self.video_capture_device_ids[0])

        if len(self.audio_capture_device_ids) > 0:
            self.audio_capture_device = AudioCaptureDevice(self.audio_capture_device_ids[0])

        if len(self.speaker_device_ids) > 0:
            self.speaker_device = SpeakerDevice(self.speaker_device_ids[0])

    # a job to listen audio capture device, wait for hot word
    def enqueue(
        self,
        session_input: SessionInput
    ) -> bool:
        if session_input.interactive and not self.que.empty():
            logger.warning("Cannot create new interactive session, because one is already running")
            return False

        self.que.put(session_input)
        return True

    def run(self):
        self.running = True

        while self.running:
            session_input = self.que.get()

            try:
                session = Session(
                    session_input,
                    self.video_capture_device, 
                    self.audio_capture_device, 
                    self.speaker_device,
                    self.patience
                )

                asyncio.run(session.run())

            except Exception as e:
                logger.error(f"Error in session: {e}")
                continue

            finally:
                logger.info("session ended")

    def stop(self):
        self.running = False

if __name__ == "__main__":
    video_capture = VideoCaptureDevice(0, 5, 384)

    video_capture.register_callback(
        lambda frame: (cv2.imshow("Frame", frame), print(len(imgb64(frame))), cv2.waitKey(1))
    )

    try:
        video_capture.run()
    except KeyboardInterrupt:
        video_capture.stop()
        cv2.destroyAllWindows()

    # x = get_available_video_capture_device_ids() 

    # video_capture = VideoCaptureDevice(x[0], fps=10, max_width=384)

    # video_capture.register_callback(
    #     lambda frame: (cv2.imshow("Frame", frame), cv2.waitKey(1))
    # )

    # video_capture.run()

    # import wave

    # speaker = SpeakerDevice(0)

    # device_ids = get_available_speaker_device_ids()

    # device = SpeakerDevice(device_ids[0])
    # path = 'data/1.wav'
    # import wave

    # with wave.open(path, 'rb') as f:
    #     data = f.readframes(f.getnframes())
    #     sample_rate = f.getframerate()
    #     channels = f.getnchannels()
    #     sample_width = f.getsampwidth()
    #     npdata = np.frombuffer(data, dtype=np.int16)

    #     device.speak(SpeechData(npdata[:sample_rate], sample_rate, channels))
    #     device.speak(SpeechData(npdata[sample_rate:2*sample_rate], sample_rate, channels))

    # device.run()

    # print(sd.query_devices())
    # print(sd.default.device)