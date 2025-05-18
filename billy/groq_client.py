# Simple Groq API client for chat completions
import os
import aiohttp
import asyncio

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")

async def groq_chat_completion(messages, stream=False):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "stream": stream
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(GROQ_API_URL, headers=headers, json=payload) as resp:
            if stream:
                async for line in resp.content:
                    if line:
                        yield line
            else:
                data = await resp.json()
                yield data
