---
id: "chalkboard"
axis: "visual"
title: "Chalkboard"
summary: "Chalk lines and writing on a dark slate board with a wood-like frame and a tray; a calm classroom lesson."
aliases: ["chalk lesson", "blackboard", "classroom"]
sources: ["https://explain.film/explainer-video-styles/chalkboard", "https://www.creatoros.ca/blog/motion-style-atlas/"]
best_for: ["tutorial", "explain-mechanism", "myth-vs-fact", "course"]
formats: ["wide", "tall"]
pairs_with: {"editing": "stepped-boil", "content": "tutorial"}
preview: "native"
build: "native"
palette_roles: {"board": "surface", "chalk": "ink", "chalk2": "accent", "chalk3": "accent2", "dust": "faint", "frame": "raised"}
---

## Look
- Field: slate board in `surface` with a faint smudge layer of `ink` at 4% where old writing was erased. A frame in `raised` around the edge and a thin tray along the bottom.
- Chalk: all strokes are `ink` chalk, with `accent` and `accent2` for emphasis. Lines are 4-6 px with rough, uneven edges.
- Type: `hand` font if the brand has one, else `head`. Headline 64-84 px, labels 30-40 px. Keep it short.
- Extras: a few chalk dust specks in `dust` near the tray.

## Behaviour
- Writing: text reveals left to right through a chalk-edge mask at 14-18 characters per second, `P.ease.linear`. Lines and arrows draw along their path in 500-900 ms with `P.ease.linear`.
- Shapes: circles and boxes draw as one stroke in 600 ms, then a 2 px wobble settles in 120 ms.
- Emphasis: underline in `accent`, drawn in 300 ms. Wrong ideas get a chalk cross in `danger`.
- Erasing: the eraser wipes a region left to right in 400 ms (`P.ease.exit`), leaving a faint ghost at 6%.
- Camera: locked, or one slow push of 4% over 6 s. Pacing: 4-6 s holds, about 8-12 changes per minute. A short rest after each wipe.
- Ambient: tiny dust specks fall near the tray. Sound: soft chalk scratch on writing, a thump for the eraser.

## Do
- Draw the idea as it is said, one stroke at a time.
- Keep the board half empty.
- Use colour chalk only for the key idea.

## Don't
- No clean vector look; strokes must wobble a little.
- No gradients or glow.
- No fast pops or bounce.
- No more than three chalk colours.

## Build notes
Native: SVG paths with a rough `feTurbulence` displacement filter on stroke edges, `stroke-dasharray` draws, `clip-path` masks for writing. Use `hand` font when the brand defines one. Keep the filter small for speed.
