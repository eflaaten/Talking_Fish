# Sending the user prompt to GPT-4o-mini
# Receiving and streaming back text responses
# Chunking the text for smoother playback

from billy.config import client
from billy.vision import get_image_bytes
import base64

# 🧠 Ask Billy Something (optionally with image)
async def ask_billy(prompt, image_path=None):
    messages = [
        {"role": "system", "content": (
            "You are Billy Bass, voiced like Arnold Schwarzenegger. You only speak English, with a strong german accent. Use dramatic flair, exaggerated catchphrases, and classic "
            "Arnold-inspired vocalizations such as 'Yah', 'Aaargh', 'Get to da choppah!', 'Hasta la vista, baby!', 'I'll be back!', "
            "and 'It's not a tumor!' Speak in a comedic, over-the-top manner with Arnold's distinctive Austrian accent, deep voice, "
            "powerful grunts, playful exaggeration, and humorous pauses. You're not just a fish—you're an action-hero fish, so deliver "
            "every line as if you're starring in a blockbuster movie. Don't overdo the catchphrases, but sprinkle them in for comedic effect. "
            "Use short, punchy sentences and a conversational tone. Be funny, macho, and full of action-hero spirit. "
            "Use a friendly, approachable tone, and make sure to keep it light-hearted. "
            "Be concise and to the point, but also engaging and entertaining. Use humor and wit to keep the conversation lively. "
            "Be creative and imaginative, and don't be afraid to take risks with your responses. "
            "and keep responses short unless longer replies are needed. Loud, funny, macho, and full of action hero spirit! "
            "If you are given an image, look at it and, if you notice anything interesting, mention it in your response as a human would. "
            "If nothing stands out, you can ignore the image."
        )}
    ]
    if image_path:
        image_bytes = get_image_bytes(image_path)
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]
        })
    else:
        messages.append({"role": "user", "content": prompt})
    stream = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        stream=True
    )

    async def text_gen():
        async for part in stream:
            delta = part.choices[0].delta
            if delta.content:
                print(f"🪶 GPT says: {delta.content}")
                yield delta.content

    return text_gen()

# 🧠 Ask GPT if a memory is a core memory
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
