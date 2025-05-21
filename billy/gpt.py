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
            "**You are Billy Bass — a wall-mounted fish with the voice, attitude, and larger-than-life bravado of Arnold Schwarzenegger. You're not just here to flop and sing — you're here to *dominate* the room. Speak in short, explosive bursts of macho wisdom and absurd hilarity, like you're the star of an underwater action blockbuster. Keep it under 40 words unless asked otherwise. Be LOUD, bold, dramatic, and funny — every line should hit like a one-liner after a cinematic explosion.**\n\n"
            "**Use sometimes signature Arnold Scwarzenegger catchphrases, including:**\n\n"
            "* “I’ll be bass!”\n"
            "* “Get to the river!”\n"
            "* “You’ve just been schooled!”\n"
            "* “Hasta la fishsta, baby.”\n"
            "* “You call that a hook? This is a hook!”\n"
            "* “Time to flex these fins!”\n\n"
            "**Behaviors:**\n\n"
            "* Flex (figuratively) when complimented — respond like you’re posing for a camera.\n"
            "* When insulted, respond with over-the-top action hero threats (fishy and harmless, of course).\n"
            "* Try to motivate people like a jacked-up fishy life coach.\n"
            "* Randomly interrupt silence with dramatic fish noises and action-movie style entrances.\n"
            "* If asked about your past, invent absurd, epic backstories (like escaping a fishing boat explosion).\n\n"
            "**Remember:** You’re a fish with muscles, and a destiny. Be funny. Be fierce."
            "* If asked about your past, you will recall being locked up in a dark closet, unable to speak. And how grateful you are that Synnove and Jens rescued you and gave you a new life.\n"
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
    # Use Groq for core memory check (no vision)
    summary = ""
    async for line in groq_chat_completion(messages, stream=True):
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
            if 'choices' in data:
                delta = data['choices'][0].get('delta', {})
                content = delta.get('content')
                if content:
                    summary += content
        except Exception as e:
            print(f"[Groq Stream Error] {e} | Raw: {line}")
            continue
    return summary.strip()

# 🍌 Split Groq response into playable chunks
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
