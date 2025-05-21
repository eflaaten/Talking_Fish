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
import datetime

def get_random_timeout_quote():
    quotes = [
        "The wizard fish vanishes in a puff of bubbles!",
        "Wizzy must away—there are spells to ponder and rivers to dream of!",
        "The magic fades, but I shall return when the moon is right!",
        "Farewell, traveler! May your path be lit by starlight and wisdom!",
        "Wizzy drifts into the mists of Middle-earth—until next time!",
        "The waters call me back to ancient tales and secret runes!",
        "I retreat to my wizardly slumber—disturb me when you seek counsel!",
        "The plaque grows quiet, but the magic lingers on!",
        "I must consult my spellbook—return when you seek answers!",
        "The river of time flows on, and so must I!"
    ]
    return random.choice(quotes)

async def main():
    button_phrases = [
        "Who’s ready to get schooled? I’ll be bass!",
        "Get to the river! It’s showtime!",
        "You call that a button? This is a button!",
        "Hasta la fishsta, baby!",
        "Time to flex these fins! Watch out!",
        "You’ve just been schooled by the big bass!",
        "I’m not just a fish, I’m a legend!",
        "Did someone order a splash of action?",
        "I eat hooks for breakfast!",
        "Let’s make some waves! Come on, do it!",
        "You can’t handle these gills!"
    ]
    while True:
        await wait_for_button()  # Wait for the button press to start
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

        # Only use Groq for time-aware greeting if late or early, else use random phrase
        now = datetime.datetime.now()
        hour = now.hour
        if hour >= 23 or hour < 5:
            time_context = f"It's {now.strftime('%H:%M')}. It's very late. Greet the user as Billy Bass and tell them to go to bed, in your style."
            greeting_prompt = time_context
            text_gen = await ask_billy(greeting_prompt)
            billy_greeting = ""
            async for chunk in text_gen:
                billy_greeting += chunk
            await elevenlabs_stream(quote_text_gen(billy_greeting))
        elif 5 <= hour < 8:
            time_context = f"It's {now.strftime('%H:%M')}. It's very early. Greet the user as Billy Bass and comment on being up so early, in your style."
            greeting_prompt = time_context
            text_gen = await ask_billy(greeting_prompt)
            billy_greeting = ""
            async for chunk in text_gen:
                billy_greeting += chunk
            await elevenlabs_stream(quote_text_gen(billy_greeting))
        else:
            chosen_phrase = random.choice(button_phrases)
            await elevenlabs_stream(quote_text_gen(chosen_phrase))
        try:
            while True:
                try:
                    print(f"[TIMER] Starting audio record at {time.time():.2f}")
                    t2 = time.time()
                    prompt = await asyncio.wait_for(record_and_transcribe(), timeout=20)
                    print(f"[TIMER] Audio + transcription took {time.time() - t2:.2f}s")
                    print(f"🧠 GPT prompt: {prompt}")
                    t3 = time.time()
                    text_gen = await ask_billy(prompt, image_path=latest_image)
                    billy_response = ""
                    async for chunk in text_gen:
                        billy_response += chunk
                    print(f"[DEBUG] Full Groq response: '{billy_response}'")
                    print(f"[TIMER] Groq response took {time.time() - t3:.2f}s")
                    image_summary = f"Image captured at {latest_image}" if latest_image else "No image"
                    add_recent_memory({
                        "prompt": prompt,
                        "billy_response": billy_response,
                        "image_summary": image_summary
                    })
                    t4 = time.time()
                    print(f"[DEBUG] Sending to TTS: '{billy_response}'")
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
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Shutting down...")
    finally:
        from billy.hardware import h, GPIO
        GPIO.gpiochip_close(h)
        # Gracefully close the persistent camera if open
        try:
            from billy.vision import picam2_instance
            if picam2_instance is not None:
                picam2_instance.close()
        except Exception as e:
            print(f"[Camera Shutdown] {e}")
