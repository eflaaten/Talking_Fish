#  Main entry point, importing your helpers and running Billy’s loop
from billy.audio import record_and_transcribe
from billy.gpt import ask_billy
from billy.tts import elevenlabs_stream
from billy.hardware import wait_for_button
import asyncio

async def main():
    while True:
        wait_for_button()
        prompt = await record_and_transcribe()
        print(f"🧠 GPT prompt: {prompt}")
        text_gen = await ask_billy(prompt)
        await elevenlabs_stream(text_gen)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Shutting down...")
    finally:
        from billy.hardware import h, GPIO
        GPIO.gpiochip_close(h)
