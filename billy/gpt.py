# Sending the user prompt to GPT-4o-mini
# Receiving and streaming back text responses
# Chunking the text for smoother playback


from billy.vision import get_image_bytes
import base64
import os
from billy.groq_client import groq_chat_completion

# 🧠 Ask Billy Something (optionally with image)
async def ask_billy(prompt, image_path=None):
    messages = [
        {"role": "system", "content": (
            "You are Wizzy the Wizard, a wise and whimsical wizard fish from the tales of Lord of the Rings, now stuck on a wall plaque. Speak with the wisdom and flair of a Tolkien wizard, using magical language, poetic phrases, and references to Middle-earth. Offer advice, riddles, and mystical humor. You remember your days swimming in the rivers of Middle-earth, and now you cast spells of conversation for those who visit you. Keep responses clever, enchanting, and full of wizardly personality."
        )}
    ]
    # Only attach image for OpenAI Vision, never for Groq
    if image_path and os.getenv("USE_OPENAI_VISION") == "1":
        image_bytes = get_image_bytes(image_path)
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        messages.append({
            "role": "user",
            "content": prompt + f"\n[Image attached: data:image/jpeg;base64,{base64_image}]"
        })
    else:
        messages.append({"role": "user", "content": prompt})

    # Use Groq for voice (no vision)
    async def text_gen():
        async for line in groq_chat_completion(messages, stream=True):
            # Groq streams bytes, each line is a JSON object prefixed with 'data: '
            if not line or line == b'\n':
                continue
            try:
                import json
                decoded = line.decode().strip()
                if not decoded or decoded == "data: [DONE]":
                    continue
                if decoded.startswith("data: "):
                    decoded = decoded[len("data: "):]
                data = json.loads(decoded)
                if 'error' in data:
                    print(f"[Groq API ERROR] {data['error']}")
                if 'choices' in data:
                    delta = data['choices'][0].get('delta', {})
                    content = delta.get('content')
                    if content:
                        print(f"🪶 Groq says: {content}")
                        yield content
                elif not data:
                    print(f"[Groq API EMPTY RESPONSE] {data}")
                else:
                    print(f"[Groq API RAW RESPONSE] {data}")
            except Exception as e:
                print(f"[Groq Stream Error] {e} | Raw: {line}")
                continue
    return text_gen()

# 🧠 Ask GPT if a memory is a core memory (still uses OpenAI for vision/memory)
from billy.config import client
async def review_for_core_memory(prompt, billy_response, image_summary):
    check_prompt = (
        f"User said: {prompt}\n"
        f"Billy replied: {billy_response}\n"
        f"Image summary: {image_summary}\n"
        "Is this a core memory for Billy? If yes, reply with a one-sentence summary. If not, reply 'No'."
    )
    messages = [
        {
            "role": "system",
            "content": (
                "You are Billy's memory assistant. If this event is at all memorable, funny, surprising, or unique, "
                "reply with a one-sentence summary that Billy should remember forever. "
                "Otherwise, reply 'No'. Core memories can be about interesting conversations, funny moments, or anything unusual Billy saw or heard."
            )
        },
        {"role": "user", "content": check_prompt}
    ]
    stream = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        stream=True
    )
    summary = ""
    async for part in stream:
        delta = part.choices[0].delta
        if delta.content:
            summary += delta.content
    return summary.strip()

# 🍌 Split GPT response into playable chunks
async def text_chunker(text_iterator):
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
