---
id: "match-cut-morph"
axis: "editing"
title: "Match cut and morph"
summary: "Shape and position match cuts and morphs between scenes; one form turns into the next."
aliases: ["shape match", "graphic match", "morph transition"]
sources: ["https://ideatomotion.com/looks", "https://www.creatoros.ca/blog/motion-style-atlas/", "https://explain.film/explainer-video-styles"]
best_for: ["explain-mechanism", "before-after", "timeline", "explainer", "hook-one-idea"]
formats: ["wide", "tall"]
pairs_with: ["flat-vector", "isotype-pictograms", "minimalist-premium", "manim-math", "kinetic-typography"]
preview: "native"
build: "native"
---

## Look
Every scene ends on a shape and the next scene starts on the same shape in the same place. A circle becomes a clock, a bar becomes a door. The carried form is the story link.

## Behaviour
- Pair: plan each cut as a pair (K2 in `_shared/transitions.md`). Name the carried object. Its position is within 0.02 of the frame, size within 5%, same colour.
- Morph: the shape changes form over 400-600 ms with `P.ease.move`. Corner radius, width and height tween together; no cross-fade.
- Hard match cut: A's last frame and B's first frame show the same shape. B then changes around it with `P.ease.enter` (400 ms), 80 ms between items.
- Scale: the carried shape may grow 1.0 to 3.0 over 500 ms with `P.ease.whip` and fill the screen as B's ground.
- Other items: leave with `P.ease.exit` (240 ms) 100 ms before the morph starts, so only the shape is left.
- Rhythm: the morph starts on the verb of the phrase and ends on the noun.
- Pacing: 4-6 s per scene, 10-15 morphs per minute.
- Camera: locked.
- Sound: a rising whoosh across the morph, a soft click when the shape locks.

## Do
- Choose simple geometry: circle, rounded square, bar, line.
- Keep the colour constant on the carried shape.
- Hold B's new content 0.3 s after the morph.

## Don't
- No carried shape that changes colour and size together.
- No decorative morph without a story link.
- No fade between scenes.

## Build notes
Modern kit: one SVG or div per carried shape in a persistent top layer; tween `width`, `height`, `border-radius`, `x`, `y` with `P.prog`. Do not rebuild the shape in B. See K2 and K3.
