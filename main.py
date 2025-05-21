#  Main entry point, importing your helpers and running Billy’s loop
from billy.audio import record_and_transcribe
from billy.gpt import ask_billy
from billy.tts import elevenlabs_stream, quote_text_gen
from billy.hardware import wait_for_button
from billy.vision import capture_image


import asyncio
import random
import sounddevice as sd
import time
import datetime

def get_random_timeout_quote():
    quotes = [
        "I'll be back!",
        "Time to get to da choppa, good bye!",
        "Hasta la vista, baby!",
        "Come with me if you want to live!",
        "It’s not a tumor, it’s just goodbye!",
        "I need a vacation!",
        "No problemo!",
        "Get your ass to Mars!",
        "If it bleeds, we can kill it!",
    ]
    return random.choice(quotes)

async def main():
    # Use Groq to generate a new greeting each time the button is pressed

    while True:
        await wait_for_button()  # Wait for the button press to start
        print(f"[TIMER] Button pressed at {time.time():.2f}")
        # Capture an image immediately after button press
        t0 = time.time()
        latest_image = capture_image()
        print(f"[TIMER] Image captured after button press in {time.time() - t0:.2f}s")
        last_image_time = time.monotonic()
        # Wait an extra 0.5s to let motors fully stop before recording audio
        await asyncio.sleep(0.5)

        # Only use Groq for time-aware greeting if late or early, else use random phrase
        now = datetime.datetime.now()
        hour = now.hour
        if hour >= 23 or hour < 5:
            time_context = f"It's {now.strftime('%H:%M')}. It's very late. Greet the user as Billy Bass and tell them to go to bed, in your style. Keep it under 15 words"
            greeting_prompt = time_context
            text_gen = await ask_billy(greeting_prompt)
            billy_greeting = ""
            async for chunk in text_gen:
                billy_greeting += chunk
            await elevenlabs_stream(quote_text_gen(billy_greeting))
        elif 5 <= hour < 8:
            time_context = f"It's {now.strftime('%H:%M')}. It's very early. Greet the user as Billy Bass and comment on being up so early, in your style. Keep it under 15 words."
            greeting_prompt = time_context
            text_gen = await ask_billy(greeting_prompt)
            billy_greeting = ""
            async for chunk in text_gen:
                billy_greeting += chunk
            await elevenlabs_stream(quote_text_gen(billy_greeting))
        else:
            # Ask Groq to generate a fun, energetic Billy Bass greeting
            greeting_prompt = "Greet the user as Billy Bass in a fun, energetic, and playful way. Make it sound like a talking fish toy. Keep it short, under 15 words."
            text_gen = await ask_billy(greeting_prompt)
            billy_greeting = ""
            async for chunk in text_gen:
                billy_greeting += chunk
            await elevenlabs_stream(quote_text_gen(billy_greeting))
        try:
            while True:
                try:
                    print(f"[TIMER] Starting audio record at {time.time():.2f}")
                    t2 = time.time()
                    prompt = await asyncio.wait_for(record_and_transcribe(), timeout=20)
                    print(f"[TIMER] Audio + transcription took {time.time() - t2:.2f}s")
                    print(f"🧠 GPT prompt: {prompt}")
                    t3 = time.time()
                    # --- Vision keyword detection ---
                    def needs_vision(prompt):
                        prompt_lower = prompt.lower()
                        vision_keywords = [
                            "see", "look", "what is this", "can you see", "describe what you see", "what do you see", "do you see", "recognize", "vision", "picture", "photo", "image"
                        ]
                        return any(kw in prompt_lower for kw in vision_keywords)

                    use_vision = needs_vision(prompt)
                    import os
                    if use_vision:
                        os.environ["USE_OPENAI_VISION"] = "1"
                        # Take a fresh image for vision prompts
                        latest_image = capture_image()
                        if latest_image is None:
                            billy_response = "Sorry, I can't see anything right now. My camera isn't working!"
                            await elevenlabs_stream(quote_text_gen(billy_response))
                            continue
                        text_gen = await ask_billy(prompt, image_path=latest_image)
                    else:
                        if "USE_OPENAI_VISION" in os.environ:
                            del os.environ["USE_OPENAI_VISION"]
                        text_gen = await ask_billy(prompt)
                    billy_response = ""
                    async for chunk in text_gen:
                        billy_response += chunk
                    print(f"[TIMER] LLM response took {time.time() - t3:.2f}s")
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
