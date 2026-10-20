---
name: vf-voice
description: Record or generate the voice for a video (stage 01, audio). Use when the user says "voice", "record", "ElevenLabs", "narration audio", "speak".
---
# /vf-voice — record or make the voice

Talk: `_shared/talk.md`. Steps: `_shared/guide.md`.
Read: `_shared/voice.md`, `brands/<brand>/voice.md`, `stages/01_voice/CONTEXT.md`.
Video id: `<brand>/<slug>`. If the user gave none, run `python anim.py status` and ask which video.

1. Check that the user approved the script. If not, go to `/vf-script`.
2. Ask one question. Suggest "record yourself (free)". The other choice: "ElevenLabs (paid, needs a key in `.env`)".
3. Record yourself: tell the user to read the approved script aloud and save the file as `voice.wav` or `voice.mp3`
   in `videos/<id>/01_voice/`. Wait for "done". Check the file exists. Print its length:
   `ffprobe -v error -show_entries format=duration -of csv=p=0 <file>`.
4. ElevenLabs:
   - `python anim.py speak <id> --check` is free. It checks the key, the model and the voice. Fix any problem first.
   - `python anim.py speak <id> --dry-run` is free. Show the chunks.
   - Paid voice needs a recorded script approval. Run `python anim.py review <id> script` to get the fingerprint,
     then `python anim.py review <id> script --ready --expected <fingerprint>`.
   - Start the Studio (`python anim.py studio`, keep it running) and give the user the review link from that output.
     The user reads the script there and presses Approve. The agent never approves.
   - Say the cost in plain words: it uses credits from the user's ElevenLabs plan, by the number of characters.
     Ask for a clear yes. Then run `python anim.py speak <id> --confirm-script <fingerprint>`.
     To redo one part, add `--chunk <n>`. Stop the Studio when done.
5. Tell the user to listen to the whole file. Name the file. Say what to check: meaning, names, numbers, pace.
6. ElevenLabs only: `speak` records the takes for review. Mark the first take ready:
   `python anim.py review <id> voice-test --ready --expected <fingerprint>`. The user approves it in the Studio.
   Then mark the full voice ready the same way (gate `voice`). The user approves it in the Studio.

Gate: the user listens to the voice and approves it.
Next: `/vf-transcript`.
