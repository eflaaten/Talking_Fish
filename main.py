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
        print(f"[TIMER] Button pressed at {time.time():.2f}")
        # Capture an image immediately after button press
        t0 = time.time()
        latest_image = capture_image()
        print(f"[TIMER] Image captured after button press in {time.time() - t0:.2f}s")
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
            def update_latest_image():
                pass  # No longer used
            def capture_on_speech():
                nonlocal latest_image
                t1 = time.time()
                latest_image = capture_image()
                print(f"[TIMER] Image captured at speech start in {time.time() - t1:.2f}s")
            while True:
                try:
                    print(f"[TIMER] Starting audio record at {time.time():.2f}")
                    t2 = time.time()
                    prompt = await asyncio.wait_for(record_and_transcribe(on_speech_start=capture_on_speech), timeout=20)
                    print(f"[TIMER] Audio + transcription took {time.time() - t2:.2f}s")
                    print(f"🧠 GPT prompt: {prompt}")
                    t3 = time.time()
                    text_gen = await ask_billy(prompt, image_path=latest_image)
                    billy_response = ""
                    async for chunk in text_gen:
                        billy_response += chunk
                    print(f"[TIMER] GPT-4o response took {time.time() - t3:.2f}s")
                    image_summary = f"Image captured at {latest_image}" if latest_image else "No image"
                    add_recent_memory({
                        "prompt": prompt,
                        "billy_response": billy_response,
                        "image_summary": image_summary
                    })
                    t4 = time.time()
                    await elevenlabs_stream(quote_text_gen(billy_response))
                    print(f"[TIMER] TTS took {time.time() - t4:.2f}s")
                except asyncio.TimeoutError:
                    print("⏳ No input detected for 20 seconds. Returning to button press.")
                    timeout_quote = get_random_timeout_quote()
                    await elevenlabs_stream(quote_text_gen(timeout_quote))
                    break
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
