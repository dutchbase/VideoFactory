---
id: "audio-led-cuts"
axis: "editing"
title: "Audio-led cuts"
summary: "J-cut and L-cut: the sound leads or trails the picture; calm, documentary pacing."
aliases: ["J-cut", "L-cut", "split edit"]
sources: ["https://ideatomotion.com/looks", "https://www.creatoros.ca/blog/motion-style-atlas/", "https://explain.film/explainer-video-styles"]
best_for: ["founder-story", "timeline", "explain-mechanism", "founder story", "explainer"]
formats: ["wide", "tall"]
pairs_with: ["archival-documentary", "cinematic-papercut", "watercolor", "minimalist-premium", "broadsheet"]
preview: "native"
build: "native"
---

## Look
The ear and the eye do not change at the same time. The voice of the next scene starts before its picture (J-cut), or the old voice runs on over the new picture (L-cut). The edit feels smooth and human.

## Behaviour
- J-cut: the next voice phrase or room tone starts 0.4-0.8 s before the picture changes. The cut waits for the stressed word.
- L-cut: the picture changes at the end of the phrase; the old voice and its music tail run 0.4-0.8 s over the new picture.
- Picture cut: a hard cut (K1) or a short 400 ms dissolve with `P.ease.move`. Use dissolves only when the time jumps.
- Entrance: elements fade up with `P.ease.enter` over 500-700 ms, a little after the voice names them.
- Exit: 300 ms with `P.ease.exit`.
- Camera: a slow 3-5% push over 5 s, `P.ease.linear`, or locked.
- Rhythm: alternate J and L. Never cut picture and sound on the same frame except for the first and last cut.
- Pacing: 5-9 s per scene, 7-12 cuts per minute.
- Sound: room tone or music bed runs through every cut; the voice never stops mid-word at a cut. Fade the bed 100 ms either side of the voice.

## Do
- Mark an audio track line under the picture track in the brief.
- Let the new sound say what the new picture will show.
- Hold silence for 0.3 s before a key line.

## Don't
- No picture and sound change on one frame.
- No fast cuts.
- No music stop at the cut.

## Build notes
Modern kit: picture cues are `P.past('cutN')`; audio offset lives in `audio.json`/sound plan (`_shared/sound.md`). Write each cut as `picture_t` and `audio_t` with a signed gap in the brief.
