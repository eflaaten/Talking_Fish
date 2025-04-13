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
    tail_direction = True
    swap_time = asyncio.get_event_loop().time() + 2

    try:
        while True:
            # 👄 Mouth flap
            GPIO.gpio_write(h, MOUTH_PIN, 1)
            await asyncio.sleep(random.uniform(0.03, 0.08))
            GPIO.gpio_write(h, MOUTH_PIN, 0)
            await asyncio.sleep(random.uniform(0.03, 0.1))

            # 🐟 Tail flip every 2 seconds
            if asyncio.get_event_loop().time() >= swap_time:
                tail_direction = not tail_direction
                GPIO.gpio_write(h, TAIL_PIN, int(tail_direction))
                GPIO.gpio_write(h, TAIL_PIN_2, int(not tail_direction))  # 🔁 flip both
                swap_time = asyncio.get_event_loop().time() + 2
                
    except asyncio.CancelledError:
        GPIO.gpio_write(h, MOUTH_PIN, 0)
        GPIO.gpio_write(h, TAIL_PIN, 0)
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
                GPIO.gpio_write(h, MOUTH_PIN, 1)  # Open mouth
            else:
                GPIO.gpio_write(h, MOUTH_PIN, 0)  # Close mouth

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

        await asyncio.gather(
            play_audio(audio_listener()),
            stream_text()
        )
