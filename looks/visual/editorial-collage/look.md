---
id: "editorial-collage"
axis: "visual"
title: "Editorial collage"
summary: "Cut-out shapes, torn paper edges and serif headlines layered like a magazine spread; human, curated and slightly rough."
aliases: ["paper collage", "magazine collage", "cut and paste"]
sources: ["https://explain.film/explainer-video-styles/editorial-collage", "https://www.creatoros.ca/blog/motion-style-atlas/"]
best_for: ["founder story", "launch-announcement", "hook-one-idea", "ad", "short"]
formats: ["wide", "tall"]
pairs_with: {"editing": "stepped-boil", "content": "founder-story"}
preview: "native"
build: "library"
palette_roles: {"paper": "bg", "card": "surface", "ink": "ink", "cut1": "accent", "cut2": "accent2", "cut3": "r4", "tape": "r6", "line": "line"}
---

## Look
- Field: warm `bg` paper with a faint grain. Layers of cut shapes in `accent`, `accent2` and ramp tones, each with a hard 3 px offset shadow in `ink` at 18%.
- Cut-outs: subjects (people, objects) as photo or illustration cut-outs with a white border. Edges are slightly rough, polygons not circles.
- Details: torn paper strips, tape pieces, halftone dots, a hand-drawn circle or arrow in `accent`.
- Type: a high-contrast `serif` fallback after `head` for the headline at 110-170 px, mixed with cut-out letter blocks. Small `mono` captions.
- Every layer rotates a little: -4 to +4 degrees.

## Behaviour
- Entrances: pieces slap on from the side with `P.ease.crashIn` (330 ms), rotate to rest angle, 90 ms stagger. A tape piece lands 120 ms after its card.
- Boil: the whole collage steps its rotation and offset by 1-2 px at 8 fps, so it feels cut by hand.
- Headline: words appear one cut-out block at a time, 180-260 ms per word, snapped (no easing between frames, 2-frame hold).
- Transitions: a torn paper strip sweeps across in 450 ms (`P.ease.whip`) and the next board is already under it.
- Camera: locked, with one 3% push over a 4 s hold (`P.ease.linear`).
- Pacing: 2-4 s holds, about 16-22 changes per minute. Build up 3-6 layers then cut.
- Ambient: boil only. No smooth drift.
- Sound: paper rustle and scissor snip on entrance, soft thump on tape.

## Do
- Stack in clear depth: back field, mid cut-outs, front type.
- Reuse the same 3-4 paper textures all video long.
- Let one layer hold the key word in `accent`.

## Don't
- No glossy gradients, glass or glow.
- No perfect geometry or clean vector circles.
- No smooth bouncy springs. Motion is snappy or stepped.
- No more than 2 type styles.

## Build notes
Needs cut-out PNGs from `library/` or AI images (`_shared/library.md`). Shapes and tape are CSS `clip-path` polygons. Boil is `P.rand(seed)` jitter on a stepped clock (every 125 ms). Works in tall with a stacked layout.
