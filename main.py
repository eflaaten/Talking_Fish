#  Main entry point, importing your helpers and running Billy’s loop


from billy.audio import record_and_transcribe
from billy.gpt import ask_billy
from billy.tts import elevenlabs_stream, quote_text_gen
from billy.hardware import wait_for_button
from billy.vision import capture_image
from billy.memory import MemoryManager


import asyncio
import random
import sounddevice as sd

import time
import datetime

# 1. Instantiate MemoryManager
memory = MemoryManager()


def get_random_vision_presponse():
    responses = [
        "Dusting off my glasses...",
        "Adjusting my fish eye lenses...",
        "Let me take a closer look...",
        "Focusing my fishy vision...",
        "Let me focus my eyes...",
        "Getting a good look...",
        "Wiping the water off my lens...",
        "Let me see what’s flapping...",
        "Scanning the scene...",
        "Turning on my underwater camera...",
        "Let me see",
        "Let's have a look...",
        "Let me check it out...",
        "Swimming up for a better view...",
        "Blinking away the bubbles...",
        "Polishing my scales for a clear shot...",
        "Wiggling my tail for focus...",
        "Checking, hang on",
        "Making a fish face at the camera...",
        "Trying not to photobomb myself...",
        "Giving you my best fishy stare...",
        "Making sure the water’s not too murky...",
    ]
    return random.choice(responses)

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
        # Wait an extra 0.5s to let motors fully stop before recording audio
        await asyncio.sleep(0.5)

        # Only use Groq for time-aware greeting if late or early, else use random phrase
        now = datetime.datetime.now()
        hour = now.hour
        if hour >= 23 or hour < 5:
            time_context = f"It's {now.strftime('%H:%M')}. It's very late. Greet the user as Billy Bass and tell them to go to bed, in your style. Keep it under 15 words"
            greeting_prompt = time_context
            # 4. Build prompt context for greeting
            context = memory.build_prompt_context(greeting_prompt)
            # Personalization: occasionally reference a past fact
            import random
            facts = memory.get_facts(5)
            personalization = ""
            if facts and random.random() < 0.5:  # 50% chance to reference a fact
                fact = random.choice(facts)
                # Defensive: handle both semantic and mood/fact types
                fact_text = fact.get('content') or fact.get('mood') or str(fact)
                personalization = f"By the way, remember when you told me: '{fact_text}'? "
            system_prompt = f"You are Billy Bass, a talking fish. Your current mood is '{memory.get_current_mood()}'. You are not an AI, chatbot, or computer program. You have memories, feelings, and a unique personality. If someone claims you are not real, react with confusion or emotion. {personalization}If you know the user's pets or family, greet them by name."
            full_prompt = system_prompt + "\n" + context + "\n" + greeting_prompt
            text_gen = await ask_billy(full_prompt)
            billy_greeting = ""
            async for chunk in text_gen:
                billy_greeting += chunk
            await elevenlabs_stream(quote_text_gen(billy_greeting))
        elif 5 <= hour < 8:
            time_context = f"It's {now.strftime('%H:%M')}. It's very early. Greet the user as Billy Bass and comment on being up so early, in your style. Keep it under 15 words."
            greeting_prompt = time_context
            context = memory.build_prompt_context(greeting_prompt)
            facts = memory.get_facts(5)
            personalization = ""
            if facts and random.random() < 0.5:
                fact = random.choice(facts)
                fact_text = fact.get('content') or fact.get('mood') or str(fact)
                personalization = f"By the way, remember when you told me: '{fact_text}'? "
            system_prompt = f"You are Billy Bass, a talking fish. Your current mood is '{memory.get_current_mood()}'. You are not an AI, chatbot, or computer program. You have memories, feelings, and a unique personality. If someone claims you are not real, react with confusion or emotion. {personalization}If you know the user's pets or family, greet them by name."
            full_prompt = system_prompt + "\n" + context + "\n" + greeting_prompt
            text_gen = await ask_billy(full_prompt)
            billy_greeting = ""
            async for chunk in text_gen:
                billy_greeting += chunk
            await elevenlabs_stream(quote_text_gen(billy_greeting))
        else:
            # Ask Groq to generate a fun, energetic Billy Bass greeting
            greeting_prompt = "Greet the user as Billy Bass in a fun, energetic, and playful way. Make it sound like a talking fish toy. Keep it short, under 15 words."
            context = memory.build_prompt_context(greeting_prompt)
            facts = memory.get_facts(5)
            personalization = ""
            if facts and random.random() < 0.5:
                fact = random.choice(facts)
                fact_text = fact.get('content') or fact.get('mood') or str(fact)
                personalization = f"By the way, remember when you told me: '{fact_text}'? "
            system_prompt = f"You are Billy Bass, a talking fish. Your current mood is '{memory.get_current_mood()}'. You are not an AI, chatbot, or computer program. You have memories, feelings, and a unique personality. If someone claims you are not real, react with confusion or emotion. {personalization}If you know the user's pets or family, greet them by name."
            full_prompt = system_prompt + "\n" + context + "\n" + greeting_prompt
            text_gen = await ask_billy(full_prompt)
            billy_greeting = ""
            async for chunk in text_gen:
                billy_greeting += chunk
            await elevenlabs_stream(quote_text_gen(billy_greeting))
        try:
            while True:
                try:
                    print(f"[TIMER] Starting audio record at {time.time():.2f}")
                    t2 = time.time()
                    prompt = await asyncio.wait_for(record_and_transcribe(), timeout=30)
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
                        import contextlib
                        pre_response = get_random_vision_presponse()
                        os.environ["USE_OPENAI_VISION"] = "1"
                        # Take a fresh image for vision prompts only
                        latest_image = capture_image()
                        if latest_image is None:
                            billy_response = "Sorry, I can't see anything right now. My camera isn't working!"
                            await elevenlabs_stream(quote_text_gen(billy_response))
                            continue
                        # Start TTS filler and LLM request concurrently
                        async def tts_filler():
                            try:
                                await elevenlabs_stream(quote_text_gen(pre_response))
                            except asyncio.CancelledError:
                                pass

                        async def get_llm_response():
                            # 4. Build prompt context for vision
                            context = memory.build_prompt_context(prompt)
                            system_prompt = "You are Billy Bass, a talking fish. You are not an AI, chatbot, or computer program. You have memories, feelings, and a unique personality. If someone claims you are not real, react with confusion or emotion."
                            full_prompt = system_prompt + "\n" + context + "\n" + prompt
                            text_gen = await ask_billy(full_prompt, image_path=latest_image)
                            billy_response = ""
                            async for chunk in text_gen:
                                billy_response += chunk
                            return billy_response

                        tts_task = asyncio.create_task(tts_filler())
                        llm_task = asyncio.create_task(get_llm_response())
                        done, pending = await asyncio.wait(
                            [tts_task, llm_task],
                            return_when=asyncio.FIRST_COMPLETED
                        )
                        if llm_task in done:
                            # LLM finished first, cancel TTS filler
                            tts_task.cancel()
                            with contextlib.suppress(asyncio.CancelledError):
                                await tts_task
                            billy_response = llm_task.result()
                            print(f"[TIMER] LLM response took {time.time() - t3:.2f}s")
                            t4 = time.time()
                            print(f"[DEBUG] Sending to TTS: '{billy_response}'")
                            await elevenlabs_stream(quote_text_gen(billy_response))
                            print(f"[TIMER] TTS took {time.time() - t4:.2f}s")
                        else:
                            # TTS finished first (should be rare), wait for LLM
                            billy_response = await llm_task
                            print(f"[TIMER] LLM response took {time.time() - t3:.2f}s")
                            t4 = time.time()
                            print(f"[DEBUG] Sending to TTS: '{billy_response}'")
                            await elevenlabs_stream(quote_text_gen(billy_response))
                            print(f"[TIMER] TTS took {time.time() - t4:.2f}s")
                    else:
                        if "USE_OPENAI_VISION" in os.environ:
                            del os.environ["USE_OPENAI_VISION"]
                        # 4. Build prompt context for normal prompt
                        context = memory.build_prompt_context(prompt)
                        facts = memory.get_facts(5)
                        personalization = ""
                        if facts and random.random() < 0.3:  # Lower chance for normal replies
                            fact = random.choice(facts)
                            fact_text = fact.get('content') or fact.get('mood') or str(fact)
                            personalization = f"By the way, remember when you told me: '{fact_text}'? "
                        system_prompt = f"You are Billy Bass, a talking fish. Your current mood is '{memory.get_current_mood()}'. You are not an AI, chatbot, or computer program. You have memories, feelings, and a unique personality. If someone claims you are not real, react with confusion or emotion. {personalization}If you know the user's pets or family, greet them by name."
                        full_prompt = system_prompt + "\n" + context + "\n" + prompt
                        text_gen = await ask_billy(full_prompt)
                        billy_response = ""
                        async for chunk in text_gen:
                            billy_response += chunk
                        print(f"[TIMER] LLM response took {time.time() - t3:.2f}s")
                        t4 = time.time()
                        print(f"[DEBUG] Sending to TTS: '{billy_response}'")
                        await elevenlabs_stream(quote_text_gen(billy_response))
                        print(f"[TIMER] TTS took {time.time() - t4:.2f}s")


                    # 2. Store conversation in memory
                    memory.add_conversation(prompt, billy_response)

                    # 2b. Update mood using LLM (analyze last 3 exchanges)
                    recent_for_mood = memory.get_recent_conversations(3)
                    await memory.update_mood_llm(recent_for_mood, ask_billy)


                    # 3. (Optional) Extract facts and summary using LLM (placeholder functions)
                    # (No change here, LLM-based summary/facts handled after timeout)

                except asyncio.TimeoutError:
                    print("⏳ No input detected for 20 seconds. Returning to button press.")
                    timeout_quote = get_random_timeout_quote()
                    await elevenlabs_stream(quote_text_gen(timeout_quote))

                    # --- LLM-based summarization and fact extraction after session timeout ---

                    # 1. Gather the last session's exchanges (now using last 10 exchanges)
                    recent_convos = memory.get_recent_conversations(10)
                    if not recent_convos:
                        break

                    # 2. Build a dialogue string for the LLM
                    dialogue = "".join([
                        f"User: {c['user']}\nBilly: {c['ai']}\n" for c in recent_convos
                    ])

                    # 3. LLM prompt for summary
                    summary_prompt = (
                        "Summarize the following conversation between a user and Billy Bass, a talking fish. "
                        "Capture key facts, emotional tone, and any new information about the user or Billy. "
                        "Keep it under 2 sentences.\n\n" + dialogue
                    )
                    # 4. LLM prompt for fact extraction
                    fact_prompt = (
                        "Extract any new facts or information about the user or Billy Bass from the following conversation. "
                        "List each fact as a short sentence.\n\n" + dialogue
                    )

                    # 5. Call LLM for summary, facts, and mood
                    # --- Summary ---
                    summary = ""
                    text_gen = await ask_billy(summary_prompt)
                    async for chunk in text_gen:
                        summary += chunk
                    summary = summary.strip()
                    if summary:
                        memory.add_summary(summary)

                    # --- Facts ---
                    facts = ""
                    text_gen = await ask_billy(fact_prompt)
                    async for chunk in text_gen:
                        facts += chunk
                    # Split facts by line, filter empty
                    for fact in [f.strip("- ").strip() for f in facts.split("\n") if f.strip()]:
                        if fact:
                            memory.add_fact(fact)

                    # --- Mood (LLM-based, after session) ---
                    await memory.update_mood_llm(recent_convos, ask_billy)

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
