# This file holds:
# API keys
# Global settings for audio & voice activity detection

import os
import collections
import webrtcvad
from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI

# 🍓 Load environment variables
load_dotenv()

# 🔐 API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "n2bKrLSWHzSMKmSqczm1")

# 🤖 OpenAI Clients
client = AsyncOpenAI(api_key=OPENAI_API_KEY)
sclient = OpenAI(api_key=OPENAI_API_KEY)

# 🎙 Audio Settings
format = 8  # Equivalent to pyaudio.paInt16
sample_rate = 16000  # Lowered from 48000 for faster upload/transcription
chunk_duration_ms = 10
silence_duration_ms = 1200
channels = 1  # Use mono for speech recognition
frames = collections.deque()
threshold = 1000
vad = webrtcvad.Vad(1)

import os
print("🔑 OPENAI Key starts with:", os.getenv("OPENAI_API_KEY", "Not loaded")[:10])
