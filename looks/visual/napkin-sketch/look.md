---
id: "napkin-sketch"
axis: "visual"
title: "Napkin sketch"
summary: "A quick marker sketch on a paper napkin: loose boxes, arrows and doodles for a pitch told in one minute."
aliases: ["napkin pitch", "marker sketch", "ballpoint notebook"]
sources: ["https://www.creatoros.ca/blog/motion-style-atlas/", "https://explain.film/explainer-video-styles"]
best_for: ["founder-story", "explain-mechanism", "hook-one-idea", "founder story", "short"]
formats: ["wide", "tall"]
pairs_with: {"editing": "stepped-boil", "content": "hook-one-idea"}
preview: "native"
build: "native"
palette_roles: {"paper": "bg", "ink": "ink", "note": "accent", "fold": "line", "ring": "faint", "table": "surface"}
---

## Look
- Field: `bg` paper with faint quarter-fold creases in `line` and one coffee ring in `faint` at 20%. A soft edge frame in `surface` suggests a table.
- Marks: one dark marker in `ink`, 4-6 px, round and uneven. Circles do not close. `accent` for one underline or star per frame.
- Type: `hand` font if available, else `head`, 56-80 px. Labels 28-36 px. Handwriting, not caps lock.
- Content: stick people, boxes, arrows, dollar signs and clouds. No fills, only outline and a few hatch lines.

## Behaviour
- Drawing: strokes reveal along their path in 400-800 ms, `P.ease.linear`, with a 3 px wobble. Text types in at 12-16 characters per second.
- Boil: finished drawings jitter between 2 line variants every 160 ms (3 fps style).
- Emphasis: an `accent` circle draws around the key word in 350 ms.
- Transitions: the napkin slides left 120 px and fades in 400 ms (`P.ease.move`), and a new fold of paper appears. Crossed-out ideas get a quick scribble in 200 ms.
- Camera: locked, or a 3% push over 5 s. Pacing: 3-5 s holds, about 12-15 changes per minute.
- Sound: marker squeak on strokes, a soft pen tap on dots.

## Do
- Draw only what the voice says.
- Leave a lot of blank napkin.
- Make every shape slightly wrong on purpose.

## Don't
- No clean geometry or perfect circles.
- No gradients, glow or shadows beyond the table edge.
- No more than one accent mark per frame.
- No more than 8 words of text per frame.

## Build notes
Native: SVG paths with `feTurbulence` wobble, `stroke-dasharray` reveals, two stroke variants swapped by `P.prog` steps for the boil. Fold lines are 1 px gradients in `line`. Tall format: sketch fills the full height.
