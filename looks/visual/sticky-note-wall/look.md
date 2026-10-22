---
id: "sticky-note-wall"
axis: "visual"
title: "Sticky-note wall"
summary: "A cork board of tilted paper notes, pins and red yarn, like a detective or planning wall."
aliases: ["cork board", "corkboard", "pin board", "detective wall"]
sources: ["https://www.creatoros.ca/blog/motion-style-atlas/", "https://explain.film/explainer-video-styles"]
best_for: ["problem-agitate-solve", "listicle", "explain-mechanism", "tutorial", "explainer", "course"]
formats: ["wide", "tall"]
pairs_with: {"editing": "canvas-pan", "content": "problem-agitate-solve"}
preview: "native"
build: "native"
palette_roles: {"board": "bg", "dots": "faint", "note1": "r4", "note2": "accent2", "note3": "green", "note4": "surface", "pin": "accent", "yarn": "danger", "ink": "ink", "shadow": "line"}
---

## Look
- Field: a flat corkboard in `bg` with a fine speckle texture (`faint` dots at 8% opacity). No photo of cork.
- Notes: square or wide paper notes in `r4`, `accent2`, `green` and `surface`, rotated −4° to 4°, with a soft shadow (4 px down, 10 px blur, 25% `ink`). Each note has a folded top edge and one round pin in `accent`.
- Yarn: 3 px `danger` lines that run pin to pin in straight sagging curves. They join related notes.
- Type: `hand` face at 36–48 px on notes, ink colour, 3 lines maximum. A `head` bold 80 px title on a wide white note at the top.

## Behaviour
- Entrances: a note drops from 40 px above, scales 1.1 to 1.0 and rotates into its tilt in 380 ms with `P.spring` `settle`. Its pin pushes in 120 ms later with a 4 px scale hit, `P.ease.pop`.
- Text: handwriting reveals left to right through a mask, 25 ms per letter. The title types in one line at 40 ms per letter.
- Transitions: yarn draws from one pin to the next in 450 ms, `P.ease.move`, with a gentle sag. To change topic, the old notes fall 80 px and fade in 300 ms (`P.ease.accelExit`) and new ones drop in.
- Camera: pans across the board between clusters, 800 ms, `P.ease.move`, with a 1.0 to 1.2 zoom on the active note. Light 0.5° tilt during the move.
- Pacing: 2.5–4 s holds, about 15 changes per minute. Add at most 1 note per beat.
- Ambient: the yarn and loose notes sway ±0.6° on a 4 s loop, `P.ease.linear`.
- Sound: paper slaps and soft pin clicks; a string pluck for each yarn line; light acoustic bed.

## Do
- Keep 5–8 notes on screen with different tilts.
- Put the main note in the centre and slightly larger.
- Use yarn only to show a real link.
- Keep note text to 6 words.

## Don't
- No perfect alignment. Notes must look hand placed.
- No tilt above 5°. No notes that overlap the main text.
- No more than 3 yarn lines crossing in one frame.
- No glossy or 3D paper.

## Build notes
Native CSS: absolutely placed notes with `transform: rotate()` and `box-shadow`. Yarn is SVG `<path>` quadratic curves with `stroke-dasharray` for the draw. Move the whole board group for the camera. In tall, use a 2-column cluster.
