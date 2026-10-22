---
id: "jump-cut-punch"
axis: "editing"
title: "Jump cut punch"
summary: "Social style: punch-in zooms, jump cuts, popping captions and a pattern interrupt every 1-3 seconds."
aliases: ["talking-head edit", "short-form edit", "punch-in"]
sources: ["https://ideatomotion.com/looks", "https://www.creatoros.ca/blog/motion-style-atlas/", "https://explain.film/explainer-video-styles"]
best_for: ["hook-one-idea", "listicle", "myth-vs-fact", "short", "ad"]
formats: ["wide", "tall"]
pairs_with: ["high-end-social", "brutalist-bold", "kinetic-typography", "halftone-pop", "tech-glow"]
preview: "native"
build: "native"
---

## Look
The edit is fast and a little rough. The same frame is cut tighter and wider again and again. Captions pop on every few words. Something changes every 1-3 seconds so the eye never rests.

## Behaviour
- Jump cut: remove the pause between phrases. Cut on the first frame of the next phrase. One frame, no transition.
- Punch-in: alternate scale 1.0 and 1.12-1.25 between cuts, in one frame (K8 in `_shared/transitions.md`). Never tween it.
- Caption pop: 2-4 words at a time, scale 0.9 to 1.0 with `P.spring` pop (`{dur: 0.4, bounce: 0.25}`), 160-240 ms. The key word turns `accent` and is 15% larger.
- Pattern interrupt: every 1-3 s change one thing: scale, a sticker or emoji pop, a colour field flip (bg to accent), a screen shake of 6 px for 120 ms, or an inserted b-roll tile.
- Hook: the first 1.5 s shows the claim in large words and a punch-in.
- Exit: 100 ms with `P.ease.accelExit`.
- Pacing: 20-40 cuts or interrupts per minute. A hold over 3 s fails.
- Format: tall 9:16 first; keep captions in the middle third.
- Sound: a pop or whoosh on each interrupt, a bass hit on a key word, music at 85-120 BPM.

## Do
- Vary the interrupt: never the same one twice in a row.
- Time each caption to its spoken word within 2 frames.
- Keep captions to 2 lines, 4 words per line.

## Don't
- No slow pans or fades.
- No caption that stays after its words end.
- No interrupt that covers the speaker's key word.

## Build notes
Modern kit: toggle `scale` with `P.past('cutN')` for punch-ins. Captions are one absolutely positioned div per group; show the group with `P.prog` and a spring. Shake with `P.rand(seed)` offsets.
