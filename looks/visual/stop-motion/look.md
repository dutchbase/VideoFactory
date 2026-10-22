---
id: "stop-motion"
axis: "visual"
title: "Stop motion"
summary: "Paper and object animation shot on twos at 12 fps with handmade jitter, visible texture and slightly uneven movement."
aliases: ["paper stop motion", "handmade animation", "12 fps cut-out"]
sources: ["https://explain.film/explainer-video-styles/claymation", "https://explain.film/explainer-video-styles/papercut", "https://www.creatoros.ca/blog/motion-style-atlas/"]
best_for: ["hook-one-idea", "explain-mechanism", "short", "explainer", "ad"]
formats: ["wide", "tall"]
pairs_with: {"editing": "stepped-boil", "content": "explain-mechanism"}
preview: "ai"
build: "ai"
palette_roles: {"table": "bg", "paper": "surface", "paper2": "raised", "cut1": "accent", "cut2": "accent2", "ink": "ink", "edge": "line"}
---

## Look
- Field: a flat tabletop (`bg`) seen from above, with paper cut-outs in `surface`, `accent`, `accent2` and `r4`. Paper fibre grain on every piece.
- Pieces: hand-cut shapes with slightly uneven edges, a thin lighter edge and a short hard shadow (4-8 px, offset down right).
- Props: torn paper, tape strips, pins, string, small blocks. Objects look real and physical.
- Type: letters cut from paper, `head` font, 90-140 px, each letter slightly rotated (up to 3 degrees) and offset.
- Light: even top light with a gentle vignette. Small exposure flicker between frames.

## Behaviour
- Frame rate: motion runs on twos (12 fps). Quantise all movement to 12 steps per second. No smooth interpolation.
- Jitter: each piece shifts 1-2 px and rotates up to 0.5 degrees every frame, seeded with `P.rand`. This is the boil.
- Entrances: pieces step in from the edge in 5-8 held positions over 0.5 s, `P.ease.move` sampled at 12 fps. They overshoot a little, like a hand.
- Text: letters pop in one by one, 83 ms (one step) apart, with a 2-step wobble.
- Transitions: a hand-like paper slide or a flip of 3-4 steps, 330 ms. Jump cut is fine.
- Camera: locked top-down. A rare 2-4 step push-in.
- Pacing: a change every 1.5-3 s, holds of 2-4 s, about 20-28 changes per minute.
- Ambient: constant line boil and light flicker at 12 fps. Sound: wooden taps, paper scratches and clicks on each step, light acoustic bed.

## Do
- Quantise to 12 fps for everything, including text and shadows.
- Add small mistakes: uneven spacing, tilted pieces.
- Show texture and shadow on every piece.

## Don't
- No smooth 60 fps easing, glow or gradients.
- No perfect geometry or clean vector edges.
- No camera moves that glide.
- No more than 6 pieces moving at once.

## Build notes
`preview: "ai"`: the real still comes from an AI image batch in the brand colours (`image-generation.md`). The native stand-in uses SVG shapes with offset shadows. For the build, sample time with `Math.floor(t * 12) / 12` and add `P.rand`-seeded jitter per frame. Photograph-style pieces need AI or library images.
