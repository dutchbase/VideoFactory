---
id: "blueprint"
axis: "visual"
title: "Blueprint"
summary: "Thin technical line drawings on a dark grid field with dimension marks and mono labels; precise, engineered and calm."
aliases: ["technical drawing", "engineering schematic", "blueprint explainer"]
sources: ["https://explain.film/explainer-video-styles/blueprint", "https://ideatomotion.com/looks"]
best_for: ["explain-mechanism", "product-tour", "tutorial", "explainer", "course"]
formats: ["wide", "tall"]
pairs_with: {"editing": "scroll-build", "content": "explain-mechanism"}
preview: "native"
build: "native"
palette_roles: {"paper": "bg", "grid": "line", "stroke": "ink", "label": "dim", "mark": "accent", "fill": "surface"}
---

## Look
- Field: flat `bg` with a fine grid (24 px minor, 120 px major) in `line` at low opacity. No gradient, no photo.
- Lines: 2 px strokes in `ink`, no fills except a faint `surface` wash. One `accent` stroke marks the part that matters.
- Marks: dimension lines with end ticks, corner crop marks, leader lines with a small dot, a title block at the bottom right.
- Type: `mono` 14-18 px, uppercase, wide tracking, for labels and part numbers ("A-01"). One `head` headline, 72-96 px, flush left.

## Behaviour
- Drawing: every shape draws itself with a stroke-dashoffset run, 700-1200 ms, `P.ease.move`. Longer paths take the longer time.
- Labels: a leader line draws out in 300 ms (`P.ease.enter`), then the mono label types in at 40 ms per character.
- Dimension lines draw from the centre to both ends in 400 ms, ticks pop in last with `P.ease.softLand`.
- Highlight: the key part switches its stroke to `accent` and a faint `accent` wash fades in over 400 ms.
- Transitions: the drawing erases back along its path in 350 ms (`P.ease.exit`). The grid stays and the next drawing starts 200 ms later.
- Camera: locked, or one slow zoom of 4% over the hold with `P.ease.linear`. Zoom-in on a detail takes 1.6 s (`P.ease.move`).
- Pacing: one part or one step per beat, 3-5 s holds, about 12-16 changes per minute.
- Ambient: a thin scan line crosses the grid once every 8 s at 6% opacity. Nothing else moves.
- Sound: pen scratch under each draw, soft tick on each label, low hum bed.

## Do
- Draw first, label second. Keep labels short (1-3 words).
- Use the same line weight in the whole video.
- Keep 30% of the frame empty grid.
- Number steps in the title block.

## Don't
- No filled colour shapes, gradients, glow or shadows.
- No bounce or overshoot (`bounce` stays 0).
- No more than one `accent` part per frame.
- No hand-drawn wobble. Lines stay straight and exact.

## Build notes
Inline SVG with `pathLength="1"` and `stroke-dasharray: 1; stroke-dashoffset` driven by `P.prog`. The grid is a repeating CSS gradient. Works in tall: stack the drawing above the title block and use 16 px labels.
