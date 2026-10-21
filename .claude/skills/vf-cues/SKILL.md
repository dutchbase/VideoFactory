---
name: vf-cues
description: Write the cue sheet, the moments when the picture changes (stage 03). Use when the user says "cues", "cue sheet", "timing", "storyboard", "stage 3".
---
# /vf-cues — the moments of the picture

Talk: `_shared/talk.md`. Steps: `_shared/guide.md`.
Before production, follow `_shared/permissions.md`. Pause for review only when the active permission requires it. Ask separately before each paid request.
Read: `stages/03_cues/CONTEXT.md`, `_shared/sound.md`, `_shared/motion.md`,
`videos/<id>/02_transcript/transcript.md`, `videos/<id>/01_voice/brief.md`.
Video id: `<brand>/<slug>`. If the user gave none, run `python anim.py status` and ask which video.

1. Check that `videos/<id>/02_transcript/words.json` exists. Pause for transcript review only when this session permission requires it.
2. Write `videos/<id>/03_cues/cues.md`: one cue for each idea. Anchor each cue on an exact phrase from the transcript.
   Format: `## intro "exact phrase"`. Use `## intro.change "phrase"` for a beat inside a cue, or `@0:04` for a fixed time.
   Put the sound on the cue: `[sfx: pop]` for an effect, and a `music:` line for the music.
   `_shared/motion.md` has the timing rules. `_shared/sound.md` has the effect names. Use only those names.
3. Run `python anim.py cues <id>`. If it warns that a phrase is not found, copy the phrase from the transcript and run again.
   Never edit `cues.json` or `cues.js`: the command makes them.
4. Show the cue table with the times. For each cue give: id, time, phrase, what changes on screen.
5. Revise the cues until they are ready. Pause for human review only when this session permission requires it.

Gate: pause for human review when this session permission requires it.
Next: `/vf-scene`.
