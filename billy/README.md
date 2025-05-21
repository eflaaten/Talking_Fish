# 🐟 Talking Fish (Billy Bass) – GPT-4o + ElevenLabs + Raspberry Pi 5

Bring your old Big Mouth Billy Bass back to life using AI and real-time text-to-speech!  
Billy listens, talks like an action movie hero, and flaps his mouth and tail while speaking.  
Powered by GPT-4o and ElevenLabs, running on Raspberry Pi 5.

---

## 🎬 What Billy Can Do

- 🖲️ Button press to activate
- 📸 Takes a photo when you press the button and again the moment you start speaking
- 🎤 Voice recognition with real-time Whisper transcription (always English)
- 🧠 GPT-4o (vision) for funny, Arnold-style responses that can comment on what Billy "sees"
- 🔊 ElevenLabs for real-time speech synthesis
- 🐟 GPIO-controlled mouth & tail movement while speaking
- 🧠 Remembers recent conversations and can store "core memories" (as decided by GPT-4o)

---

## 🍓 Requirements

- Raspberry Pi 5
- Python 3.11+
- An actual Billy Bass (or similar animatronic) wired to GPIO
- USB mic and speakers
- Camera module (compatible with Picamera2)
- ElevenLabs API key
- OpenAI API key

---

## 🧰 Installation

```bash
git clone https://github.com/yourname/talking-fish.git
cd talking-fish
python -m venv env
source env/bin/activate
pip install -r requirements.txt
```

---

## 🚀 Usage

1. Add your OpenAI and ElevenLabs API keys to a `.env` file in the project root:
   ```
   OPENAI_API_KEY=sk-...
   ELEVENLABS_API_KEY=...
   ELEVENLABS_VOICE_ID=...
   ```
2. Connect your Billy Bass hardware and camera to the Pi.
3. Run the main script:
   ```bash
   python main.py
   ```
4. Press the button to wake Billy. Speak to him and watch him respond with action-hero flair, commenting on what he "sees"!

---

## 🗂️ Project Structure

- `main.py` – Main event loop and logic
- `billy/audio.py` – Audio recording and Whisper transcription
- `billy/vision.py` – Camera integration and image capture
- `billy/gpt.py` – GPT-4o integration (vision + text)
- `billy/tts.py` – ElevenLabs TTS and mouth/tail animation
- `billy/hardware.py` – GPIO pin setup and helpers

- `captures/` – Folder for Billy's photos (auto-ignored by git)

---

## 📝 Features & Notes

- **Vision:** Billy takes a photo at button press and again when you start speaking, so he can comment on the latest scene.

- **Performance:** Optimized for low-latency; persistent camera, low-res images, and async event loop.
- **Audio:** Always transcribes as English for best results.
- **Git:** The `captures/` folder is ignored by git, so Billy's photos won't clutter your commits.

---

## 📖 License

MIT License
