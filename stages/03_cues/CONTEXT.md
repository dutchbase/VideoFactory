# 03 Storyboard

Read the checked transcript, the brief and the brand files. Write `cues.md` with headings like these:

```
## intro "a phrase from transcript"
Show the input.
## intro.change "another exact phrase"
Highlight the change.
```

Or use `@0:04` for an explicit time. This is useful in silent work. Parent ids are sections. Dotted ids are beats. Parents stay active through their sub-cues.

Timing rules (cue the meaning word, one change per beat, reading time): `_shared/motion.md`. Effect and music lines (`[sfx: pop]`, `[sfx: file:door.wav 0.6]`, `music:`): `_shared/sound.md`. `cues` warns about an unknown effect name or a missing effect file. `check` counts it and `render` stops.

Run `python anim.py cues <slug>`. It reads `words.json` and writes `cues.json` and `cues.js`. Do not edit those generated files. Recompile after you edit `cues.md`. In `cues.md`, note which shots are captures, redraws or illustrations. That note never appears on screen (`_shared/tone.md`). You review the storyboard before scene work.

A brand can set a quality bar: a cue in the first 2 seconds, a new cue at most every 5 seconds, `[sfx: ...]` on cuts and reveals, and a `music:` bed. For such a brand `anim.py check` counts `too few beats` and `sound design missing` (`_shared/review.md`).

Handoff: mark the current `cues` gate ready and open its exact Studio review link (`_shared/dashboard-review.md`).

Guided command: `/vf-cues`. Next: `/vf-scene`.
