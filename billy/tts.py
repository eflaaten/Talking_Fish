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
from billy.config import (
    ELEVENLABS_API_KEY, VOICE_ID,
    format, channels, sample_rate, chunk_duration_ms, vad
)
from billy.hardware import GPIO, MOUTH_PIN, TAIL_PIN, TAIL_PIN_2, h
from billy.gpt import text_chunker

# 🐟 Flap mouth & tail until cancelled
async def continuous_billy_animation():
    """
    Continuously animates the mouth and tail until canceled.
    """
    tail_direction = True
    swap_time = asyncio.get_event_loop().time() + 1  # Flip tail every 1 second

    try:
        while True:
            # 👄 Mouth flap more frequently
            GPIO.gpio_write(h, MOUTH_PIN, 1)
            await asyncio.sleep(0.01)  # Faster mouth movement
            GPIO.gpio_write(h, MOUTH_PIN, 0)
            await asyncio.sleep(0.01)  # Shorter pause

            # 🐟 Tail flip every 1 second
            if asyncio.get_event_loop().time() >= swap_time:
                tail_direction = not tail_direction
                GPIO.gpio_write(h, TAIL_PIN, int(tail_direction))
                GPIO.gpio_write(h, TAIL_PIN_2, int(not tail_direction))  # 🔁 flip both
                swap_time = asyncio.get_event_loop().time() + 1

    except asyncio.CancelledError:
        # Reset GPIO pins for mouth and tail motors
        GPIO.gpio_write(h, MOUTH_PIN, 0)
        GPIO.gpio_write(h, TAIL_PIN, 0)
        GPIO.gpio_write(h, TAIL_PIN_2, 0)
        print("🛑 Animation cancelled.")

# 🔊 Play audio while animating
async def play_audio(audio_stream):
    """
    Plays audio chunks while analyzing their volume to control mouth animation.
    """
    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=22050, output=True)

    try:
        async for chunk in audio_stream:
            # Play the audio chunk
            stream.write(chunk)

            # 📊 Analyze volume from audio chunk
            audio_np = np.frombuffer(chunk, dtype=np.int16)
            volume = np.sqrt(np.mean(audio_np**2))  # RMS volume calculation

            # 👄 Open/close mouth based on volume threshold
            if volume > 30:  # 🔧 Lower threshold for more frequent movement
                for _ in range(2):  # Open and close mouth twice per chunk
                    GPIO.gpio_write(h, MOUTH_PIN, 1)  # Open mouth
                    await asyncio.sleep(0.02)  # Shorter duration for quick movement
                    GPIO.gpio_write(h, MOUTH_PIN, 0)  # Close mouth
                    await asyncio.sleep(0.02)  # Shorter pause

    finally:
        # 🛑 Ensure mouth is closed when audio stops
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

        # Run audio playback and animations concurrently
        animation_task = asyncio.create_task(continuous_billy_animation())
        try:
            await asyncio.gather(
                play_audio(audio_listener()),
                stream_text()
            )
        finally:
            # Ensure the animation task is canceled when done
            animation_task.cancel()
            try:
                await animation_task
            except asyncio.CancelledError:
                pass
