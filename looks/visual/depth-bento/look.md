---
id: "depth-bento"
axis: "visual"
title: "Depth bento"
summary: "A bento grid of rounded glass cards tilted in 3D with depth of field; each card holds one fact and the camera tours the grid."
aliases: ["bento grid", "3D bento", "glass bento"]
sources: ["https://ideatomotion.com/looks", "https://www.creatoros.ca/blog/motion-style-atlas/"]
best_for: ["product-tour", "listicle", "launch-announcement", "explainer", "ad"]
formats: ["wide", "tall"]
pairs_with: {"editing": "canvas-pan", "content": "product-tour"}
preview: "native"
build: "native"
palette_roles: {"field": "bg", "card": "surface", "raised": "raised", "rim": "line", "hot": "accent", "alt": "accent2", "ink": "ink", "dim": "dim"}
---

## Look
- Field: `bg` with a blurred pool of `accent` at 15% behind the grid.
- Grid: 5-8 rounded cards (radius 28-36 px, 16 px gap) in different spans, in `surface` and `raised`, with a 1 px `line` rim and a soft shadow. The whole grid tilts: rotateX 12 degrees, rotateY -10 degrees.
- Cards: one fact each. A big number or icon in `accent`, a `mono` label, a short line of text. One hero card in `accent` fill.
- Depth: cards at the back get 3 px blur and 70% opacity; the focus card is sharp and lifts 40 px.
- Type: `head` bold 56-110 px for numbers, `font` 22-26 px for text.

## Behaviour
- Entrances: cards rise from 80 px lower with scale 0.92, in a wave from the top left, 70 ms stagger, 600 ms each (`P.ease.enter`).
- Focus: the camera moves to a card in 1.2 s (`P.ease.move`): the grid slides and tilts, the target lifts 40 px and sharpens, others blur to 3 px.
- Content: inside a focused card the number counts up in 800 ms and its label fades in 150 ms later.
- Transitions: the grid flattens to rotate 0 and scales out in 800 ms (`P.ease.move`) as the next grid slides in.
- Exit: cards sink and fade in 300 ms (`P.ease.exit`), 40 ms stagger, bottom first.
- Pacing: 3-5 s per focused card, about 12-18 changes per minute. Open and close with a full-grid wide shot of 2 s.
- Ambient: the grid sways 1 degree in rotateY over 8 s (`P.ease.move`); the hero card rim pulses once every 4 s.
- Sound: soft glassy click per card, low whoosh on camera moves.

## Do
- Fill the grid with different spans; no two cards the same size next to each other.
- Give every card one fact and nothing else.
- Keep the focus card the only sharp one.

## Don't
- No more than 8 cards.
- No tilt above 15 degrees; text must stay readable.
- No bounce.
- No text under 20 px.

## Build notes
CSS 3D: a parent with `perspective: 1400px` and `transform-style: preserve-3d`; cards use `translateZ` and `filter: blur()`. Drive camera moves with `P.prog` on the parent transform. In tall, use a 2-column grid with 4-6 cards.
