# ElevenLabs WebSocket connection
# Real-time TTS playback
# Random mouth/tail animation while audio plays

import json
import base64
import asyncio
import websockets
import pyaudio
import random
import numpy as np
import time
from contextlib import suppress
from billy.config import (
    ELEVENLABS_API_KEY, VOICE_ID,
    format, channels, sample_rate, chunk_duration_ms, vad
)
from billy.hardware import GPIO, MOUTH_PIN, HEAD_PIN, HEAD_PIN_2, h
from billy.gpt import text_chunker

# 🐟 Flap mouth & tail until cancelled
async def continuous_billy_animation():
    # Always start with head movement (HEAD_PIN active)
    GPIO.gpio_write(h, HEAD_PIN, 1)
    GPIO.gpio_write(h, HEAD_PIN_2, 0)
    next_swap = asyncio.get_event_loop().time() + random.uniform(3, 6)
    tail_state = True  # True = HEAD_PIN, False = HEAD_PIN_2

    try:
        while True:
            await asyncio.sleep(0.05)  # Just yield control

            now = asyncio.get_event_loop().time()
            if now >= next_swap:
                if tail_state:
                    # Turn off head (HEAD_PIN)
                    GPIO.gpio_write(h, HEAD_PIN, 0)
                    await asyncio.sleep(random.uniform(1, 2))  # Pause before tail
                    GPIO.gpio_write(h, HEAD_PIN_2, 1)
                else:
                    # Turn off tail (HEAD_PIN_2)
                    GPIO.gpio_write(h, HEAD_PIN_2, 0)
                    await asyncio.sleep(random.uniform(0.5, 1))  # Pause before head
                    GPIO.gpio_write(h, HEAD_PIN, 1)
                tail_state = not tail_state
                next_swap = now + random.uniform(3, 5)

    except asyncio.CancelledError:
        GPIO.gpio_write(h, MOUTH_PIN, 0)
        GPIO.gpio_write(h, HEAD_PIN, 0)
        GPIO.gpio_write(h, HEAD_PIN_2, 0)
        print("🛑 Animation cancelled.")

# 🦷 Jittery, random mouth flap task
async def random_mouth_flap():
    try:
        while True:
            # Randomize open duration (short, normal, or long)
            open_time = random.choices(
                [random.uniform(0.03, 0.08), random.uniform(0.09, 0.18), random.uniform(0.18, 0.35)],
                weights=[0.3, 0.6, 0.1]
            )[0]
            # Occasionally jitter mid-flap
            if random.random() < 0.2:
                open_time += random.uniform(-0.02, 0.02)
                open_time = max(0.02, open_time)

            GPIO.gpio_write(h, MOUTH_PIN, 1)
            print(f"OPEN {time.time()} for {open_time:.3f}s")
            await asyncio.sleep(open_time)

            # Sometimes do a double-flap (quick close/open)
            if random.random() < 0.15:
                GPIO.gpio_write(h, MOUTH_PIN, 0)
                await asyncio.sleep(random.uniform(0.02, 0.06))
                GPIO.gpio_write(h, MOUTH_PIN, 1)
                print(f"DOUBLE-OPEN {time.time()}")
                await asyncio.sleep(random.uniform(0.03, 0.09))

            GPIO.gpio_write(h, MOUTH_PIN, 0)

            # Randomize closed duration (short or normal)
            close_time = random.choices(
                [random.uniform(0.04, 0.12), random.uniform(0.13, 0.28)],
                weights=[0.4, 0.6]
            )[0]
            # Occasionally jitter mid-close
            if random.random() < 0.15:
                close_time += random.uniform(-0.02, 0.02)
                close_time = max(0.02, close_time)

            print(f"CLOSE {time.time()} for {close_time:.3f}s")
            await asyncio.sleep(close_time)
    except asyncio.CancelledError:
        GPIO.gpio_write(h, MOUTH_PIN, 0)

# 🔊 Play audio while animating
async def play_audio(audio_stream):
    """
    Plays audio chunks while randomizing mouth animation.
    """
    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=22050, output=True)

    # Start random mouth flapping in the background
    mouth_task = asyncio.create_task(random_mouth_flap())
    loop = asyncio.get_running_loop()

    try:
        async for chunk in audio_stream:
            await loop.run_in_executor(None, stream.write, chunk)
    finally:
        mouth_task.cancel()
        with suppress(asyncio.CancelledError):
            await mouth_task
        GPIO.gpio_write(h, MOUTH_PIN, 0)
        stream.stop_stream()
        stream.close()
        audio.terminate()
        print("🔇 Audio stream closed.")

# 🎙 ElevenLabs Real-Time Speech
async def elevenlabs_stream(text_iterator):
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

        # 📥 Audio chunks from ElevenLabs
        async def audio_listener():
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                audio_b64 = data.get("audio")
                if audio_b64:
                    yield base64.b64decode(audio_b64)
                elif data.get("isFinal"):
                    break

        # 📨 Text to ElevenLabs
        async def stream_text():
            async for text in text_chunker(text_iterator):
                await ws.send(json.dumps({"text": text, "try_trigger_generation": True}))
            await ws.send(json.dumps({"text": ""}))

        # Start animation in background
        animation_task = asyncio.create_task(continuous_billy_animation())
        try:
            await asyncio.gather(
                play_audio(audio_listener()),
                stream_text()
            )
        finally:
            animation_task.cancel()
            with suppress(asyncio.CancelledError):
                await animation_task
