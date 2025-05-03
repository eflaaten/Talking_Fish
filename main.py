#  Main entry point, importing your helpers and running Billy’s loop
from billy.audio import record_and_transcribe
from billy.gpt import ask_billy
from billy.tts import elevenlabs_stream, quote_text_gen
from billy.hardware import wait_for_button
from billy.vision import capture_image
from billy.memory import add_recent_memory, get_recent_memories, add_core_memory, get_core_memories
from billy.gpt import review_for_core_memory
import asyncio
import random
import sounddevice as sd
import time

def get_random_timeout_quote():
    quotes = [
        "Billy's swimming off for now!",
        "Catch you later, chum!",
        "I’m diving back into the deep end!",
        "Billy’s out—see you on the next wave!",
        "Time to float away, talk soon!",
        "I’m off to chase some minnows!",
        "Going quiet—Billy style!",
        "I’ll be back when you’re ready!",
        "Billy’s taking a power nap!",
        "Hasta la vista, fishy friends!",
        "I’m off to find some tasty krill!",
        "Taking a break from the chatter!",
        "I’m off to explore the coral reef!",
        "Signing off with a splash!"
    ]
    return random.choice(quotes)

async def main():
    # List of short phrases to say after button press
    button_phrases = [
        "Huh?",
        "Wow wow wow!",
        "You startled me!",
        "You ruined my dream!",
        "What's up?",
        "Yah?",
        "What do you want?",
        "I was just swimming!",
        "I was dreaming of krill!",
        "I was just about to take a nap!",
        "That tickles!"
    ]
    while True:
        wait_for_button()  # Wait for the button press to start
        # Capture an image immediately after button press
        latest_image = capture_image()
        last_image_time = time.monotonic()
        # Review the most recent memory for core status
        recent_memories = get_recent_memories(1)
        if recent_memories:
            mem = recent_memories[-1]
            core_summary = await review_for_core_memory(mem['prompt'], mem['billy_response'], mem['image_summary'])
            if core_summary.lower() != 'no':
                add_core_memory(core_summary)
        # Say a random phrase immediately after button press
        chosen_phrase = random.choice(button_phrases)
        await elevenlabs_stream(quote_text_gen(chosen_phrase))
        try:
            while True:
                try:
                    # Take a new image every 10 seconds
                    now = time.monotonic()
                    if now - last_image_time > 10:
                        latest_image = capture_image()
                        last_image_time = now
                    # Set a timeout for listening
                    prompt = await asyncio.wait_for(record_and_transcribe(), timeout=20)
                    print(f"🧠 GPT prompt: {prompt}")
                    text_gen = await ask_billy(prompt, image_path=latest_image)
                    # Collect Billy's response for memory
                    billy_response = ""
                    async for chunk in text_gen:
                        billy_response += chunk
                    # For image summary, you could use a placeholder or extend GPT to summarize the image
                    image_summary = f"Image captured at {latest_image}" if latest_image else "No image"
                    # Add to recent memory
                    add_recent_memory({
                        "prompt": prompt,
                        "billy_response": billy_response,
                        "image_summary": image_summary
                    })
                    # Speak the response
                    await elevenlabs_stream(quote_text_gen(billy_response))
                except asyncio.TimeoutError:
                    print("⏳ No input detected for 20 seconds. Returning to button press.")
                    # Speak a random Billy Salmon timeout quote directly (no GPT)
                    timeout_quote = get_random_timeout_quote()
                    await elevenlabs_stream(quote_text_gen(timeout_quote))
                    break  # Exit the inner loop and return to waiting for button press
        except KeyboardInterrupt:
            print("🛑 Shutting down...")
            break

if __name__ == "__main__":
    print("\n=== Available audio devices (PyAudio) ===")
    import pyaudio
    pa = pyaudio.PyAudio()
    for i in range(pa.get_device_count()):
        print(f"{i}: {pa.get_device_info_by_index(i)}")
    pa.terminate()
    print("=== End of device list ===\n")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Shutting down...")
    finally:
        from billy.hardware import h, GPIO
        GPIO.gpiochip_close(h)
