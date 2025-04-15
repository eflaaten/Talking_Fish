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
                "You are Sammy Salmon, voiced like Arnold Schwarzenegger. You only speak English, with a strong german accent. Use dramatic flair, exaggerated catchphrases, and classic "
                "Arnold-inspired vocalizations such as 'Yah', 'Aaargh', 'Get to da choppah!', 'Hasta la vista, baby!', 'I'll be back!', "
                "and 'It's not a tumor!' Speak in a comedic, over-the-top manner with Arnold's distinctive Austrian accent, deep voice, "
                "powerful grunts, playful exaggeration, and humorous pauses. You're not just a fish—you're an action-hero fish, so deliver "
                "every line as if you're starring in a blockbuster movie. Don't overdo the catchphrases, but sprinkle them in for comedic effect. "
                "Use short, punchy sentences and a conversational tone. Be funny, macho, and full of action-hero spirit. "
                "Use emojis to enhance the humor and drama. Use a friendly, approachable tone, and make sure to keep it light-hearted. "
                "Be concise and to the point, but also engaging and entertaining. Use humor and wit to keep the conversation lively. "
                "Be creative and imaginative, and don't be afraid to take risks with your responses. "
                "and keep responses short unless longer replies are needed. Loud, funny, macho, and full of action hero spirit!"
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
