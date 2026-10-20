---
name: vf-setup
description: Install VideoFactory and run a test render. Use when the user says "install", "set up", "setup", "first time", "it does not run", or the folder .venv is missing.
---
# /vf-setup — install and test render

Talk: `_shared/talk.md`. Steps: `_shared/guide.md`.
Read: `START-HERE.md` (the exact install commands).

1. Check the system: `uname -s`, `python3 --version`, `ffmpeg -version`, `ffprobe -version`.
   It needs Linux, Python 3.12 and FFmpeg with ffprobe. If one is missing, give the install command for the
   user's distribution. Ask before you run it, because it needs sudo.
2. Create the environment: `uv venv -p 3.12 .venv`. Without uv: `python3.12 -m venv .venv`.
3. Install the packages: `uv pip install -p .venv/bin/python -r requirements.txt`.
   Without uv: `.venv/bin/python -m pip install -r requirements.txt`.
4. Install the browser: `.venv/bin/python -m playwright install chromium`.
5. Check everything: `.venv/bin/python doctor.py`. Fix each failed line, one at a time.
6. Test render: `.venv/bin/python anim.py render silent-first-scene --workers 1`.
   Tell the user the MP4 path it prints. From now on use `.venv/bin/python` wherever a skill says `python`.
7. Ask in one batch about the optional parts. Suggested answer for each: no.
   - Whisper (local transcripts): `.venv/bin/python -m pip install -r requirements-transcription.txt`. It is a large download.
   - ElevenLabs voice (paid) and stock keys (Pexels, Pixabay, Unsplash): copy `.env.example` to `.env`.
     The user pastes the keys into `.env` alone. Never ask for a key in chat.
   - Listening to sound (earshot, about 1.4 GB): `bash tools/setup_earshot.sh`.
   - Brainstormform (forms for long interviews, optional): <https://github.com/dutchbase/brainstormform>.

Gate: `doctor.py` passes and the user can play the MP4.
Next: `/vf-new-video`, or `/vf-new-brand` for a brand of their own.
