# import asyncio
# import os
# import time
# from pathlib import Path
# from typing import AsyncGenerator
# import numpy as np
# from dotenv import load_dotenv
# from openai import AsyncOpenAI, OpenAI
# from openai.helpers import LocalAudioPlayer

# load_dotenv()

# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# PARAGRAPH = """
# The city I would like to talk about is Paris, the capital city of France. Paris is world-famous for its rich history, culture, and romantic atmosphere. Often referred to as the “City of Lights,” it is home to many iconic landmarks such as the Eiffel Tower and the Louvre Museum, which attract millions of visitors every year.
# """

# def sycn_speak():
#     client = OpenAI()
#     speech_file_path = Path(__file__).parent / "speech2.wav"

#     with client.audio.speech.with_streaming_response.create(
#         model="gpt-4o-mini-tts",
#         voice="marin",
#         input=PARAGRAPH,
#         instructions="Speak in a cheerful and positive tone.",
#         response_format="wav",
#         stream_format="audio",
#     ) as response:
#         response.stream_to_file(speech_file_path)
        
        
        
# if __name__ == "__main__":
#     sycn_speak()

import sounddevice as sd
import soundfile as sf


print(sd.query_devices())

sd.default.device = 0
sd.default.latency = "high"
sd.default.blocksize = 2048

data, sr = sf.read("tts_48k.wav", dtype="int16")

sd.play(data, 48000)
sd.wait()
