---
name: vf-script
description: Write and revise the script text for a video (stage 01, text). Use when the user says "script", "write the text", "narration", "voice-over text", "draft".
---
# /vf-script — write the script

Talk: `_shared/talk.md`. Steps: `_shared/guide.md`.
Read: `stages/01_voice/CONTEXT.md`, `_shared/script-production.md`, `_shared/tone.md`, `_shared/voice.md`,
`brands/<brand>/brand.md`, `brands/<brand>/voice.md`, `videos/<id>/01_voice/brief.md`,
and `videos/<id>/00_research/research.md` if it exists.
Video id: `<brand>/<slug>`. If the user gave none, run `python anim.py status` and ask which video.

1. Check that the user confirmed the brief. If not, go to `/vf-new-video` step 3.
2. Follow `_shared/script-production.md`: three different opening angles, choose one with a reason, then draft.
   Write the spoken words in `videos/<id>/01_voice/script.md`. Use facts from the brief and the research only.
3. Critique your draft against the contract and revise at most two times.
4. Show the script. Give the word count and the estimated length. Name the one line you are least sure about.
5. Change the text until the user approves it.
6. If the voice will come from ElevenLabs, run `python anim.py speak <id> --dry-run`.
   It costs nothing. Show the chunks and the fingerprint.

Gate: the user approves the script text.
Next: `/vf-voice`.
