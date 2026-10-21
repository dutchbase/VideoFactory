---
name: vf-voice
description: Record or generate the voice for a video (stage 01, audio). Use when the user says "voice", "record", "ElevenLabs", "narration audio", "speak".
---
# /vf-voice — record or make the voice

Talk: `_shared/talk.md`. Steps: `_shared/guide.md`.
Before production, follow `_shared/permissions.md`. Pause for review only when the active permission requires it. Ask separately before each paid request.
Read: `_shared/voice.md`, `brands/<brand>/voice.md`, `stages/01_voice/CONTEXT.md`.
Video id: `<brand>/<slug>`. If the user gave none, run `python anim.py status` and ask which video.

1. Check that the current script is ready. Pause for script review only when this session permission requires it.
2. Ask one question. Suggest "record yourself (free)". The other choice: "ElevenLabs (paid, needs a key in `.env`)".
3. Record yourself: tell the user to read the current script aloud and save the file as `voice.wav` or `voice.mp3`
   in `videos/<id>/01_voice/`. Wait for "done". Check the file exists. Print its length:
   `ffprobe -v error -show_entries format=duration -of csv=p=0 <file>`.
4. ElevenLabs:
   - `python anim.py speak <id> --check` and `--dry-run` do not spend credits. Use them to check setup and show the chunks.
   - Do not use direct `speak` for paid generation. Start a managed run as described in `_shared/autonomous-runs.md`.
     When it stops for a quote, show the exact request and maximum cost. Get approval, record the quote with
     `run-quote`, approve that quote with `run-approve`, then resume the run. A retry needs a new quote and approval.
   - The managed run must use the current script fingerprint. Keep the quote and approval with that exact request.
5. Tell the user to listen to the whole file. Name the file. Say what to check: meaning, names, numbers, pace.
6. ElevenLabs only: when the managed run records the takes, mark the first take ready:
   `python anim.py review <id> voice-test --ready --expected <fingerprint>`. Use the Studio review when this session permission requires human review.
   Then mark the full voice ready the same way (gate `voice`).

Gate: pause for voice review when this session permission requires it. Ensure the required listening checks are complete.
Next: `/vf-transcript`.
