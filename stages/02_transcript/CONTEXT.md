# 02 Words and timing

Read `_shared/permissions.md` before production. Pause for human review when the active session permission requires it.

Install `requirements-transcription.txt` for local Whisper (`START-HERE.md`). Run it after the voice review: `python anim.py transcribe <slug>`. The first run may download model weights. A CPU works. Larger models need more memory and time.

The default model is `large-v3`. A second model may check flagged words. For a smaller, faster run use `--model base --no-verify`. Set the spoken language with `--language` (default `en`). Whisper reads `_shared/vocab.txt` as a hint for names and jargon: add your own names there. When a real script exists, `transcribe` respells words from it and keeps Whisper's timing. It reports the pace of each take (`_shared/voice.md`, Pace).

Compare suspicious words with the recording. Two models agreeing is not proof.

Output: `words.json` as `{voice, duration, model, words: [{text, start, end}]}`, plus `transcript.md`. Check names, missing or repeated words and timing. Edit `words.json`, not `transcript.md`. `--force` overwrites an existing `words.json`, including your edits to timing. Recompile the cues after a correction. The silent fixture has empty words and authored timestamps, not a transcript.

Handoff: when this session requires transcript review, mark the current gate ready and open its exact Studio review link (`_shared/dashboard-review.md`). A human decision covers the saved words and timings after comparing them with the audio. Otherwise continue to the next permitted stage.

Guided command: `/vf-transcript`. Next: `/vf-cues`.
