---
voice_id: JBFqnCBsd6RMkjVDRZzb
model: eleven_v4
stability: natural
similarity_boost: 0.75
format: mp3_44100_128
---
# VideoFactory voice settings

Two ways to get a voice. Both make the same video.

1. **Free: record it yourself.** Read `01_voice/script.md` aloud and save the file in `01_voice/`
   (`voice.wav`, `.m4a` or `.mp3`). Any phone or laptop microphone works in a quiet room.
2. **Paid: ElevenLabs.** `python anim.py speak <slug>` uses the settings above. The key goes in the local `.env`
   (`ELEVENLABS_API_KEY=...`), never in a file you commit. Check your key and model first:
   `python anim.py speak <slug> --check`.

The voice above is "George", one of the default voices every ElevenLabs account has.
To change it, copy a voice id from the ElevenLabs voice library into `voice_id`.
If your plan does not have `eleven_v4`, `--check` lists the models you can use; put one in `model`.

Each video freezes these settings in its own `settings.json` when it is created, so a change here only affects new videos.
How to write a script for a voice, review it and listen to the result: `../../_shared/voice.md`.
