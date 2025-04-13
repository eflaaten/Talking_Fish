#  Main entry point, importing your helpers and running Billy’s loop
from billy.audio import record_and_transcribe
from billy.gpt import ask_billy
from billy.tts import elevenlabs_stream
from billy.hardware import wait_for_button
import asyncio

async def main():
    while True:
        wait_for_button()  # Wait for the button press to start
        try:
            while True:
                try:
                    # Set a timeout for listening
                    prompt = await asyncio.wait_for(record_and_transcribe(), timeout=20)
                    print(f"🧠 GPT prompt: {prompt}")
                    text_gen = await ask_billy(prompt)
                    await elevenlabs_stream(text_gen)
                except asyncio.TimeoutError:
                    print("⏳ No input detected for 20 seconds. Returning to button press.")
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
