---
id: "swiss-modernist"
axis: "visual"
title: "Swiss modernist"
summary: "Flat primary geometry on a strict grid with one huge flush-left grotesk headline; precise, calm and design-literate."
aliases: ["swiss kinetic", "international typographic style", "bauhaus explainer"]
sources: ["https://explain.film/explainer-video-styles/swiss-modernist", "https://ideatomotion.com/looks"]
best_for: ["explain-mechanism", "product-tour", "launch-announcement", "explainer", "course"]
formats: ["wide", "tall"]
pairs_with: {"editing": "mask-wipe", "content": "explain-mechanism"}
preview: "native"
build: "native"
palette_roles: {"field": "ink", "paper": "bg", "red": "accent", "blue": "accent2", "yellow": "r4", "rule": "line"}
---

## Look
- Field: off-white or near-black paper (`bg`) with flat solid shapes in three brand voices: `accent`, `accent2` and a light ramp tone (`ramp[4]`). No gradients, no shadows, no glow, no texture.
- Grid: a visible or implied 12-column grid with 48–64 px margins. Every edge sits on a column line. Circles, bars, quarter-arcs and triangles only.
- Type: the brand `head` font in its heaviest weight, very large (120–220 px wide, 140–260 px tall) and flush-left, tight leading (0.9) and tight tracking (−2%). A second level in small caps `mono` (14–18 px) for captions and index numbers ("01", "02").
- People and objects are reduced to geometry: a head is a circle, a body a bar.

## Behaviour
- Entrances: shapes slide in along grid lines from one edge with `P.ease.softLand` (400 ms) or scale from a corner, never from the centre. Rotations snap in 45° or 90° steps with `P.ease.move` (300–400 ms).
- Text: headlines reveal line by line through a rectangular mask, 80 ms stagger per line. Small captions fade in 120 ms after the headline lands.
- Transitions: hard block wipes in an accent colour, or the field inverts (paper ↔ ink) on the cut. Cuts land on the beat of the voice.
- Camera: locked. No drift, no parallax, no shake. "Nothing wobbles."
- Pacing: one idea per frame, 2.5–5 s holds, about 15–20 changes per minute. Rest still for a full second after a dense build.
- Ambient: none. Stillness is part of the look.
- Sound: dry clicks and soft ticks on each snap; minimal electronic or piano bed.

## Do
- Keep at most three shapes plus one headline on screen.
- Align everything to the grid; use index numbers to count steps.
- Let one colour block carry the key idea of each frame.
- Use big negative space on purpose (40–60% of the frame empty).

## Don't
- No bounce, overshoot or springy pops (`bounce` stays 0).
- No drop shadows, gradients, glass, icons with detail, or photos.
- No centred layouts and no more than two type sizes per frame.
- No diagonal text.

## Build notes
Pure CSS in the Modern kit: absolutely positioned blocks, `clip-path` masks for line reveals, `transform-origin` at corners. Use `P.prog` with `P.ease.softLand` and `P.ease.move`. Works in both formats: in tall, stack the headline above the geometry and use a 6-column grid.
