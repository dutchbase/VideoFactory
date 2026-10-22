---
id: "claymation"
axis: "visual"
title: "Claymation"
summary: "Hand-moulded clay figures and props with fingerprints and soft studio light, animated on twos like real stop-motion."
aliases: ["clay animation", "plasticine", "clay stop-motion"]
sources: ["https://explain.film/explainer-video-styles", "https://www.creatoros.ca/blog/motion-style-atlas/"]
best_for: ["founder-story", "hook-one-idea", "myth-vs-fact", "short", "explainer"]
formats: ["wide", "tall"]
pairs_with: {"editing": "stepped-boil", "content": "hook-one-idea"}
preview: "ai"
build: "ai"
palette_roles: {"table": "bg", "clay-a": "accent", "clay-b": "accent2", "clay-c": "r4", "clay-d": "green", "shadow": "faint", "text": "ink"}
---

## Look
- Field: a soft tabletop in `bg` with a gentle light fall-off. A paper or felt backdrop, no hard horizon.
- Clay: chunky rounded shapes in `accent`, `accent2` and two ramp tones. Matte, slightly lumpy surfaces with visible thumb prints, seams and tool marks. Slight colour variation inside one piece.
- Light: one warm key light from the upper left, a soft contact shadow under each piece. Shallow depth of field: back props blur 2–4 px.
- Characters: simple blob bodies, bead eyes, rolled-clay limbs. Props are 3–6 simple shapes only.
- Type: brand `head` in heavy weight, shown as chunky letters in `ink` or as clay letters (AI image). Short, 2–4 words.

## Behaviour
- Frame rate: all motion runs on twos (12 fps look). Hold each pose for 2 frames at 24 fps (83 ms).
- Entrances: pieces pop up from the table with a squash (scale y 0.85 for 2 frames), then stretch (1.08 for 2 frames), then rest. Use `P.spring` snap (`{ dur: 0.35, bounce: 0.1 }`) sampled on twos.
- Exits: a piece squishes flat in 3 frames and slides out, or is pulled off screen by a clay hand. About 250 ms.
- Jitter: add a 1–2 px random wobble and a 0.5° rotation jitter every 2 frames to every piece (`P.rand(seed)`). This is the ambient "boil".
- Transitions: a clay ball rolls across and grows to fill the frame (500 ms, `P.ease.move`), or a hard cut on the beat.
- Camera: locked, with a slow 3% push over a hold. Handheld micro shake of 1 px is allowed.
- Pacing: 3–5 s holds, about 10–14 changes per minute.
- Sound: wet squelches, soft thumps, a plinky xylophone or ukulele bed.

## Do
- Show one clear action per shot.
- Keep a few visible imperfections on every piece.
- Hold a pose for 2 frames before the next one.
- Keep shadows soft and short.

## Don't
- No sharp vector edges or perfect gradients.
- No smooth interpolation at 60 fps.
- No more than five pieces per shot.
- No glossy plastic highlights (that is `soft-3d-clay`).

## Build notes
`preview: "ai"`: real clay needs AI images (`_shared/image-generation.md`). Generate props and characters on a clean tabletop, then animate the stills in the Modern kit with stepped transforms (`P.prog` rounded to 1/12 s) and a seeded jitter. The native `preview.html` is a CSS stand-in: radial-gradient blobs with soft shadows. Works in both formats.
