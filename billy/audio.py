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

# Helper to select a likely working input/output device index for PyAudio
def get_pyaudio_device(kind='output'):
    # Always use BY Y02: USB Audio (index 1) for both input and output
    return 1

def get_pyaudio_device_index(name_substring, kind='output'):
    import pyaudio
    pa = pyaudio.PyAudio()
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        if name_substring in info['name'] and (
            (kind == 'output' and info['maxOutputChannels'] > 0) or
            (kind == 'input' and info['maxInputChannels'] > 0)
        ):
            pa.terminate()
            return i
    pa.terminate()
    return None

# 🎙 Record & Transcribe User Speech
async def record_and_transcribe(timeout=20, on_listen_start=None, on_speech_start=None):
    frames.clear()  # 🧽 Clean up old frames
    import pyaudio
    input_device = get_pyaudio_device('input')
    audio = pyaudio.PyAudio()
    try:
        stream = audio.open(format=format, channels=channels, rate=sample_rate, input=True,
                            frames_per_buffer=int(sample_rate * chunk_duration_ms / 1000),
                            input_device_index=input_device)
    except Exception as e:
        print(f"[AUDIO ERROR] Could not open input device: {e}")
        print("Try running the program and selecting a different input device.")
        return "[AUDIO ERROR] No input device available."

    try:
        speaking = False
        num_silent_chunks = 0
        max_silent_chunks = int(silence_duration_ms / chunk_duration_ms)
        start_time = time.monotonic()

        print("🎤 Listening with VAD...")
        if on_listen_start:
            on_listen_start()
        while True:
            # Check for timeout before any speech is detected
            if not speaking and (time.monotonic() - start_time) > timeout:
                print(f"⏳ No speech detected for {timeout} seconds. Timing out.")
                raise asyncio.TimeoutError("No speech detected within timeout.")
            try:
                chunk = stream.read(int(sample_rate * chunk_duration_ms / 1000), exception_on_overflow=False)
            except Exception as e:
                print(f"[AUDIO WARNING] Input overflowed or error: {e}")
                # Try to recover by stopping and restarting the stream
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception:
                    pass
                try:
                    stream = audio.open(format=format, channels=channels, rate=sample_rate, input=True,
                                       frames_per_buffer=int(sample_rate * chunk_duration_ms / 1000),
                                       input_device_index=input_device)
                except Exception as e2:
                    print(f"[AUDIO ERROR] Could not recover input device: {e2}")
                    return "[AUDIO ERROR] No input device available."
                await asyncio.sleep(0.05)
                continue
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
                    if on_speech_start:
                        on_speech_start()
                    frames.append(chunk)

        filename = "recording.wav"
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(audio.get_sample_size(format))
            wf.setframerate(sample_rate)
            wf.writeframes(b''.join(frames))

        print("📝 Transcribing...")
        with open(filename, "rb") as f:
            transcript = sclient.audio.transcriptions.create(model="whisper-1", file=f, language="en")

        return transcript.text
    finally:
        # Ensure proper cleanup
        try:
            stream.stop_stream()
            stream.close()
        except Exception:
            pass
        audio.terminate()
