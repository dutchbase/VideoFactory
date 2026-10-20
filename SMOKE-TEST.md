# Setup check

Run this after setup (`START-HERE.md`) to prove the install works. Write down the date and your versions when it passes.

1. `.venv/bin/python doctor.py` passes. FFmpeg and ffprobe are found.
2. `.venv/bin/python anim.py stills silent-first-scene` writes one picture for each cue.
3. `.venv/bin/python anim.py render silent-first-scene --workers 1` writes an eight-second MP4 (240 frames) in `tests/fixtures/silent-first-scene/05_render/`. Set `ANIM_OFFLINE=1` before steps 2 and 3 to prove they need no network.

Last recorded run: none yet. Add the date, your OS, the Python version and the Playwright version (`requirements.txt` pins it).

Not covered by this check: ElevenLabs, Whisper, the capture commands and Python 3.14 (the pinned numpy has no wheel). See `LIMITATIONS.md`.
