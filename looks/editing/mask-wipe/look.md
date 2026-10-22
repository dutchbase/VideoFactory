---
id: "mask-wipe"
axis: "editing"
title: "Mask and wipe reveals"
summary: "Hard-edged masks reveal text line by line and solid blocks wipe across the frame on the beat; precise and graphic."
aliases: ["block wipe", "swiss kinetic cut", "mask reveal"]
sources: ["https://ideatomotion.com/looks", "https://explain.film/explainer-video-styles/swiss-modernist"]
best_for: ["explain-mechanism", "listicle", "launch-announcement", "explainer", "short"]
formats: ["wide", "tall"]
pairs_with: ["swiss-modernist", "brutalist-bold", "kinetic-typography", "minimalist-premium"]
preview: "native"
build: "native"
---

## Look
The edit is visible as geometry: rectangles of solid colour (`accent`, `ink` or `bg`) that cover and uncover the frame. Text never fades; it is cut out of a mask.

## Behaviour
- Text: each line sits in an `overflow: hidden` box and slides up from 100% to 0% with `P.ease.softLand` (400 ms), 80 ms between lines. Exits slide the other way with `P.ease.accelExit` (260 ms).
- Scene change: a solid block enters from one edge with `P.ease.whip` (230 ms), covers the frame for 2–4 frames, and leaves from the opposite edge to reveal the next scene. Direction follows the reading direction (left to right, top to bottom for steps).
- Variants: a split wipe (two blocks from opposite edges meet in the centre), or a field inversion (bg ↔ ink) exactly on the cut.
- Rhythm: cut on the stressed word of the voice. Every wipe lands on a beat; never two wipes within 1.5 s.
- Camera: locked. No zoom, no blur, no dissolve.
- Pacing: 3–5 s per idea, 12–20 changes per minute.
- Sound: one short swish per wipe, a click on each text line.

## Do
- Use the same wipe direction for the same kind of step.
- Keep the wipe colour from the brand palette, one per video.
- Hold the revealed text still until the next beat.

## Don't
- No cross-dissolves or soft fades.
- No bounce or overshoot on masks.
- No diagonal or rotated wipes unless the visual look asks for 45° steps.

## Build notes
Modern kit: `clip-path: inset()` or `overflow: hidden` wrappers driven by `P.prog`. Block wipes are one absolutely positioned div per cut on the top layer. See `_shared/transitions.md` for cut timing.
