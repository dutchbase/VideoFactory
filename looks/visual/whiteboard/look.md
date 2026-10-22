---
id: "whiteboard"
axis: "visual"
title: "Whiteboard"
summary: "Marker sketches on a clean light board: strokes draw themselves, hand lettering and pastel fills explain an idea step by step."
aliases: ["whiteboard animation", "sketchpad", "doodle explainer"]
sources: ["https://explain.film/explainer-video-styles/whiteboard-animation", "https://ideatomotion.com/looks"]
best_for: ["explain-mechanism", "tutorial", "problem-agitate-solve", "explainer", "course"]
formats: ["wide", "tall"]
pairs_with: {"editing": "stepped-boil", "content": "explain-mechanism"}
preview: "native"
build: "native"
palette_roles: {"board": "bg", "ink": "ink", "pen": "accent", "pen2": "accent2", "fill": "surface", "line": "line"}
---

## Look
- Field: a light board (`bg`) with no texture. In a dark brand, use `ink` strokes on the dark board; keep the same rules.
- Strokes: 4-6 px marker lines in `ink`, round caps, slightly wobbly. Key items in `accent` and `accent2`.
- Fills: flat pastel blocks (`surface`, tints of `accent`) that sit a few px off the outline, like a missed fill.
- Type: `hand` font for labels at 40-64 px, `head` only for the one title. Underlines and arrows are drawn, not typed.
- Objects are simple doodles: boxes, stick people, circles, arrows, a lightbulb. Max 6 items on the board.

## Behaviour
- Draw-on: every stroke reveals along its path with stroke-dashoffset, `P.ease.move`, 500-900 ms by length. Long lines run up to 1.2 s.
- Text: handwriting reveals left to right through a mask, 40 ms per letter, `P.ease.linear`.
- Fills: a pastel fill wipes in after its outline, 300 ms, `P.ease.enter`.
- Arrows: draw 400 ms, then the head pops with `P.spring` snap.
- Erase: old items wipe out left to right in 300 ms with `P.ease.exit`, or the board scrolls up 1.0 s with `P.ease.move`.
- Camera: locked. For a big board, pan 1.6 s with `P.ease.move` to the next area.
- Pacing: one new sketch every 2-4 s, holds of 2-3 s after a draw, about 15-20 changes per minute.
- Ambient: a 2-frame line boil at 8 fps on strokes (1 px jitter) if the brand allows. Sound: marker squeak under each draw, soft tap on arrow heads.

## Do
- Draw in the order the voice says things.
- Keep one idea per board and clear it before the next.
- Use `accent` only for the point of the frame.

## Don't
- No photos, gradients, shadows or glass.
- No perfect geometry: keep a small wobble.
- No more than 6 items or 2 pen colours at once.
- No fade-in for drawn items; always draw them.

## Build notes
Inline SVG paths with `pathLength=1` and `stroke-dasharray: 1` animated by `P.prog`. Handwriting uses `hand` with a `clip-path` wipe. The 8 fps boil is an optional SVG turbulence filter stepped by frame. Works in tall: use one column of steps.
