import sys
from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.g1.audio.g1_audio_client import AudioClient
from wav import read_wav, play_pcm_stream
from pathlib import Path
path = Path(__file__).parent / "speech.wav"
wav_path = path.as_posix()

def main():
    ChannelFactoryInitialize(0, "eth0")
    audioClient = AudioClient()
    audioClient.SetTimeout(10.0)
    audioClient.Init()

    pcm_list, sample_rate, num_channels, is_ok = read_wav(path)
    print(f"[DEBUG] Read success: {is_ok}")
    print(f"[DEBUG] Sample rate: {sample_rate} Hz")
    print(f"[DEBUG] Channels: {num_channels}")
    print(f"[DEBUG] PCM byte length: {len(pcm_list)}")
    
    if not is_ok or sample_rate != 16000 or num_channels != 1:
        print("[ERROR] Failed to read WAV file or unsupported format (must be 16kHz mono)")
        return

    play_pcm_stream(audioClient, pcm_list, "example")

    audioClient.PlayStop("example")

if __name__ == "__main__":
    main()

