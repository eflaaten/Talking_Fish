# Voice recording using PyAudio
# Silence detection using VAD
# Saving audio to .wav
# Transcription using Whisper (via OpenAI)

import pyaudio
import wave
import audioop
import time
import asyncio
from billy.config import (
    format, sample_rate, chunk_duration_ms, silence_duration_ms,
    channels, frames, threshold, vad, sclient
)

# 🎙 Record & Transcribe User Speech
async def record_and_transcribe(timeout=20):
    frames.clear()  # 🧽 Clean up old frames
    audio = pyaudio.PyAudio()
    stream = audio.open(format=format, channels=channels, rate=sample_rate, input=True,
                        frames_per_buffer=int(sample_rate * chunk_duration_ms / 1000))

    try:
        speaking = False
        num_silent_chunks = 0
        max_silent_chunks = int(silence_duration_ms / chunk_duration_ms)
        start_time = time.monotonic()

        print("🎤 Listening with VAD...")
        while True:
            # Check for timeout before any speech is detected
            if not speaking and (time.monotonic() - start_time) > timeout:
                print(f"⏳ No speech detected for {timeout} seconds. Timing out.")
                raise asyncio.TimeoutError("No speech detected within timeout.")
            chunk = stream.read(int(sample_rate * chunk_duration_ms / 1000))
            volume = audioop.rms(chunk, 2)
            is_speech = vad.is_speech(chunk, sample_rate) and volume > threshold

            if speaking:
                frames.append(chunk)
                if not is_speech:
                    num_silent_chunks += 1
                    if num_silent_chunks > max_silent_chunks:
                        break
                else:
                    num_silent_chunks = 0
            else:
                if is_speech:
                    speaking = True
                    frames.append(chunk)

        filename = "recording.wav"
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(audio.get_sample_size(format))
            wf.setframerate(sample_rate)
            wf.writeframes(b''.join(frames))

        print("📝 Transcribing...")
        with open(filename, "rb") as f:
            transcript = sclient.audio.transcriptions.create(model="whisper-1", file=f)

        return transcript.text
    finally:
        # Ensure proper cleanup
        stream.stop_stream()
        stream.close()
        audio.terminate()
