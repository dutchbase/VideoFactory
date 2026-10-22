---
id: "minimalist-premium"
axis: "visual"
title: "Minimalist premium"
summary: "A light, quiet frame with a lot of white space, one object and refined type; slow and calm, the light opposite of keynote-black."
aliases: ["quiet luxury", "light minimal", "white space"]
sources: ["https://ideatomotion.com/looks", "https://www.creatoros.ca/blog/motion-style-atlas/"]
best_for: ["hook-one-idea", "launch-announcement", "product-tour", "ad", "founder story"]
formats: ["wide", "tall"]
pairs_with: {"editing": "cinematic-drift", "content": "hook-one-idea"}
preview: "native"
build: "native"
palette_roles: {"paper": "bg", "ink": "ink", "quiet": "dim", "hair": "line", "accent": "accent", "object": "surface"}
---

## Look
- Field: a light, plain `bg`. In a dark brand, use the lightest ramp tone (`r6`) as the field and `bg` as the ink. No texture.
- Space: at least 60% of the frame is empty. One object sits slightly off centre on a thirds line.
- Object: a single soft form (a sphere, a card, a device outline) in `surface` with a very soft shadow (blur 60 px, 10% opacity). Max one `accent` detail.
- Type: refined `head` in a light weight, 56-96 px, wide tracking (+2%), at most 6 words. A small `mono` caption at 14-16 px in `faint`.
- Lines: 1 px hairlines in `line`. No boxes, icons or badges.

## Behaviour
- Entrances: the object fades in with a 24 px rise over 900 ms using `P.ease.softLand`. Text follows 300 ms later with a 12 px rise over 700 ms, `P.ease.enter`.
- Text: whole lines, never word by word. Fade only (opacity), no mask or slide.
- Camera: a very slow push, scale 1.0 to 1.05 over the full hold, `P.ease.linear`. Or no move at all.
- Transition: crossfade, 900-1200 ms, `P.ease.move`. Or hold the empty field for 400 ms, then fade the next object in.
- Exits: fade out 500 ms with `P.ease.exit`.
- Pacing: 5-8 s holds, about 6-9 changes per minute. One idea per frame.
- Ambient: none. Sound: a soft piano or air pad, one low note on each reveal, no hits.

## Do
- Keep exactly one object and one line of text.
- Use only `ink`, `dim` and one `accent` detail.
- Let a frame rest for a full second before the next change.

## Don't
- No gradients, glow, glass, bounce or overshoot.
- No dark field (use keynote-black for dark).
- No second object, no icons, no decoration.
- No fast cuts or whip moves.

## Build notes
Pure CSS: absolute layout, `opacity` and `transform` animation with `P.prog`. Use a thirds grid (426 px, 853 px) for the object. For tall format, put the object in the upper third and the text in the lower third.
