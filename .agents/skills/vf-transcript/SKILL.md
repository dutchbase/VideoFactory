---
name: vf-transcript
description: Turn the voice into words with times (stage 02). Use when the user says "transcript", "transcribe", "Whisper", "word timing", "stage 2".
---
# /vf-transcript — words with times

Talk: `_shared/talk.md`. Steps: `_shared/guide.md`.
Before production, follow `_shared/permissions.md`. Pause for review only when the active permission requires it. Ask separately before each paid request.
Read: `stages/02_transcript/CONTEXT.md`, `videos/<id>/01_voice/script.md`.
Video id: `<brand>/<slug>`. If the user gave none, run `python anim.py status` and ask which video.

1. Check that a voice file exists in `videos/<id>/01_voice/`. Pause for voice review only when this session permission requires it.
2. Check Whisper: `.venv/bin/python -c "import whisper"`. If it fails, say Whisper is missing.
   Ask before you install it: `.venv/bin/python -m pip install -r requirements-transcription.txt`.
   It is a large download. The first run also downloads model files.
3. Ask for the spoken language code. Suggest `en`.
   Run `python anim.py transcribe <id> --language <code>`. This can take minutes on a CPU.
   For a faster, rougher result: add `--model base --no-verify`.
4. Show `videos/<id>/02_transcript/transcript.md`. Compare it with the script and the audio.
   List the words that differ, and every name and number.
5. Fix wrong words with the user. Change only the `text` of a word in `videos/<id>/02_transcript/words.json`
   and in `videos/<id>/02_transcript/transcript.md`. Do not change `start` or `end`. Do not run `--force` after a hand fix: it overwrites the fix.

Gate: the words match the script and the audio.
Next: `/vf-cues`.
