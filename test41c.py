import os
import json
import asyncio
import base64
import subprocess
import collections
import time
import threading
import shutil
import numpy as np  # Needed for PyAudio fallback
import pyaudio
import wave
import audioop
import webrtcvad
import websockets
import lgpio as GPIO
from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI

# 🍓 Load environment
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "n2bKrLSWHzSMKmSqczm1")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)
sclient = OpenAI(api_key=OPENAI_API_KEY)

# 🪛 GPIO Setup
MOUTH_PIN = 17
TAIL_PIN = 27
BUTTON_PIN = 17
h = GPIO.gpiochip_open(0)
GPIO.gpio_claim_output(h, MOUTH_PIN)
GPIO.gpio_claim_output(h, TAIL_PIN)
GPIO.gpio_claim_input(h, BUTTON_PIN)

# Add inside your main() before the loop starts:
mpv_available = shutil.which("mpv") is not None

# 🎙 Audio Settings
format = pyaudio.paInt16
sample_rate = 16000
chunk_duration_ms = 30
silence_duration_ms = 800
channels = 1
frames = collections.deque()
threshold = 1000
vad = webrtcvad.Vad(1)
listeningIsBlocked = False

# 🧠 Interrupt Flag: Used to stop playback if the user starts speaking
interrupt_requested = False

# === Button Press ===
def wait_for_button():
    print("🔧 Waiting for button press...")
    while True:
        if GPIO.gpio_read(h, BUTTON_PIN) == 0:
            time.sleep(0.1)
            if GPIO.gpio_read(h, BUTTON_PIN) == 0:
                print("🎬 Button pressed!")
                return
        time.sleep(0.1)

# === Animate Billy ===
async def animate_billy(duration=6):
    print(f"🐟 Animating Billy for {duration:.2f} seconds...")
    GPIO.gpio_write(h, MOUTH_PIN, 1)
    GPIO.gpio_write(h, TAIL_PIN, 1)
    await asyncio.sleep(duration)
    GPIO.gpio_write(h, MOUTH_PIN, 0)
    GPIO.gpio_write(h, TAIL_PIN, 0)

# === Stream Audio via PyAudio ===
async def stream_audio(audio_chunks):
    global interrupt_requested
    played_chunks = 0
    min_chunks_before_interrupt = 10

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=22050,
                    output=True)

    try:
        async for chunk in audio_chunks:
            if interrupt_requested and played_chunks > min_chunks_before_interrupt:
                print("🛑 Graceful interrupt after minimum chunks played.")
                break
            if chunk:
                stream.write(chunk)
                played_chunks += 1
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        print("🔚 Finished PyAudio streaming.")

import threading  # Make sure this is at the top of your script

# === ElevenLabs WebSocket Stream ===
async def elevenlabs_stream(text_iterator):
    global interrupt_requested
    interrupt_requested = False  # 🧠 Reset before each stream

    uri = (
        f"wss://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream-input"
        f"?model_id=eleven_turbo_v2&output_format=pcm_22050"
    )

    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({
            "text": " ",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
            "generation_config": {"chunk_length_schedule": [50]},
            "xi_api_key": ELEVENLABS_API_KEY,
            "model_id": "eleven_turbo_v2"
        }))

        # === Audio Playback using PyAudio ===
        async def play_audio(audio_stream):
            global interrupt_requested
            audio = pyaudio.PyAudio()
            stream = audio.open(format=pyaudio.paInt16, channels=1, rate=22050, output=True)

            chunk_index = 0
            try:
                async for chunk in audio_stream:
                    if interrupt_requested and chunk_index > 10:
                        print("🛑 Audio interrupted mid-speech!")
                        break
                    stream.write(chunk)
                    chunk_index += 1
            finally:
                stream.stop_stream()
                stream.close()
                audio.terminate()
                print("🔚 Audio stream closed.")

        # === Receive audio from ElevenLabs ===
        async def audio_listener():
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                audio_b64 = data.get("audio")
                if audio_b64:
                    yield base64.b64decode(audio_b64)
                elif data.get("isFinal"):
                    break

        # === Stream Text to ElevenLabs ===
        async def stream_text():
            async for text in text_chunker(text_iterator):
                if interrupt_requested:
                    print("🍍 Text streaming interrupted.")
                    break
                await ws.send(json.dumps({"text": text, "try_trigger_generation": True}))
            await ws.send(json.dumps({"text": ""}))

        # === Blocking Interrupt Listener in Thread ===
        def blocking_interrupt_listener():
            global interrupt_requested
            time.sleep(1.2)
            print("👂 Listening for speech interrupt...")

            audio = pyaudio.PyAudio()
            stream = audio.open(format=format, channels=channels, rate=sample_rate, input=True,
                                frames_per_buffer=int(sample_rate * chunk_duration_ms / 1000))
            try:
                while not interrupt_requested:
                    chunk = stream.read(int(sample_rate * chunk_duration_ms / 1000), exception_on_overflow=False)
                    volume = audioop.rms(chunk, 2)
                    is_speech = vad.is_speech(chunk, sample_rate) and volume > 1500
                    if is_speech:
                        print("⚡ Interrupt triggered by user speech!")
                        interrupt_requested = True
                        break
            finally:
                stream.stop_stream()
                stream.close()
                audio.terminate()
                print("🛑 Interrupt listener stopped.")

        # === Stream Text to ElevenLabs ===
        async def stream_text():
            async for text in text_chunker(text_iterator):
                if interrupt_requested:
                    print("🍍 Text streaming interrupted mid-sentence.")
                    break
                await ws.send(json.dumps({"text": text, "try_trigger_generation": True}))
            if not interrupt_requested:
                await ws.send(json.dumps({"text": ""}))  # Finish normally

        # === Start the interrupt listener in a separate thread ===
        interrupt_thread = threading.Thread(target=blocking_interrupt_listener)
        interrupt_thread.start()

        # === Start everything at once! 🍉 ===
        await asyncio.gather(
            play_audio(audio_listener()),
            animate_billy(),
            stream_text()
        )

        # Wait for the interrupt thread to finish
        interrupt_thread.join()

# === Chunk GPT-4o Text ===
async def text_chunker(text_iterator):
    """Used during input streaming to chunk text blocks and set last char to space."""
    splitters = (".", ",", "?", "!", ";", ":", "—", "-", "(", ")", "[", "]", "}", " ")
    buffer = ""
    async for text in text_iterator:
        if buffer.endswith(splitters):
            yield buffer if buffer.endswith(" ") else buffer + " "
            buffer = text
        elif text.startswith(splitters):
            output = buffer + text[0]
            yield output if output.endswith(" ") else output + " "
            buffer = text[1:]
        else:
            buffer += text
    if buffer != "":
        yield buffer + " "

# === Ask Billy via GPT-4o ===
async def ask_billy(prompt):
    stream = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": (
                "You are Billy Bass, voiced like Arnold Schwarzenegger. Use dramatic flair, catchphrases, "
                "and keep it under 40 words unless asked otherwise. Loud, funny, macho, and full of action hero spirit!"
            )},
            {"role": "user", "content": prompt}
        ],
        stream=True
    )

    async def text_gen():
        async for part in stream:
            delta = part.choices[0].delta
            if delta.content:
                print(f"🪶 GPT says: {delta.content}")  # 🍌 Print each text piece
                yield delta.content

    return text_gen()

# === Record + Transcribe ===
async def record_and_transcribe():
    frames.clear()  # 🧽 Clear old audio before recording fresh input
    audio = pyaudio.PyAudio()
    stream = audio.open(format=format, channels=channels, rate=sample_rate, input=True,
                        frames_per_buffer=int(sample_rate * chunk_duration_ms / 1000))

    speaking = False
    num_silent_chunks = 0
    max_silent_chunks = int(silence_duration_ms / chunk_duration_ms)

    print("🎤 Listening with VAD...")
    while True:
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
    stream.stop_stream()
    stream.close()
    audio.terminate()

    print("📝 Transcribing...")
    with open(filename, "rb") as f:
        transcript = sclient.audio.transcriptions.create(model="whisper-1", file=f)
    return transcript.text

# === 🍒 Main Loop ===
async def main():
    while True:
        wait_for_button()
        prompt = await record_and_transcribe()
        print(f"🧠 GPT prompt: {prompt}")
        text_gen = await ask_billy(prompt)
        await elevenlabs_stream(text_gen)

# === 🛠 Entry Point ===
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Shutting down...")
    finally:
        GPIO.gpiochip_close(h)
