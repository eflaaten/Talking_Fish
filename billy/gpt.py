# Sending the user prompt to GPT-4o-mini
# Receiving and streaming back text responses
# Chunking the text for smoother playback

from billy.config import client

# 🧠 Ask Billy Something
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
                print(f"🪶 GPT says: {delta.content}")
                yield delta.content

    return text_gen()

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
