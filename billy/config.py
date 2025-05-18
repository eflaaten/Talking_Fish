# This file holds:
# API keys
# Global settings for audio & voice activity detection

import os
import collections
import webrtcvad
from dotenv import load_dotenv


# 🍓 Load environment variables
load_dotenv()

# 🔐 API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "n2bKrLSWHzSMKmSqczm1")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")

# 🤖 OpenAI Clients (for vision/memory only)
try:
    from openai import AsyncOpenAI, OpenAI
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    sclient = OpenAI(api_key=OPENAI_API_KEY)
except ImportError:
    client = None
    sclient = None

# 🎙 Audio Settings
format = 8  # Equivalent to pyaudio.paInt16
sample_rate = 16000  # Lowered from 48000 for faster upload/transcription
chunk_duration_ms = 10
silence_duration_ms = 1200
channels = 1  # Use mono for speech recognition
frames = collections.deque()
threshold = 800
vad = webrtcvad.Vad(1)

