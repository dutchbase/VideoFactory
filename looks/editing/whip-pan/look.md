---
id: "whip-pan"
axis: "editing"
title: "Whip pan"
summary: "Fast blurred pans that hide the cut; the camera swings and lands on the next scene."
aliases: ["swish pan", "blur pan", "camera whip"]
sources: ["https://ideatomotion.com/looks", "https://www.creatoros.ca/blog/motion-style-atlas/", "https://explain.film/explainer-video-styles"]
best_for: ["product-tour", "tutorial", "launch-announcement", "ad", "explainer"]
formats: ["wide", "tall"]
pairs_with: ["saas-product-demo", "tech-glow", "depth-bento", "high-end-social", "isometric-3d"]
preview: "native"
build: "native"
---

## Look
Each scene change is a quick sideways swing. Content smears into horizontal blur, the cut hides in the middle of the smear, and the new scene decelerates into place.

## Behaviour
- Pan: about 8 frames (270 ms), peak speed near a quarter of the move, peak about 13% of W per frame (K7 in `_shared/transitions.md`).
- Out: A moves left 60% of W with `P.ease.accelExit` (130 ms) and blurs to 24 px horizontal.
- Cut: one frame at peak blur. Swap content here (`tl.set` or `P.past`). Never tween opacity.
- In: B moves in from the right with `P.ease.whip` (230 ms) and sharpens from 24 px to 0.
- Anchor: one object (logo, cursor, card) keeps its size and screen position across the pan so the eye follows it.
- Direction: forward steps pan left, going back pans right. Up-and-down pans only for a change of level.
- Rhythm: start the pan 0.1 s before the next phrase. One whip per idea, never two within 2 s.
- Pacing: 3-5 s per scene, 12-20 pans per minute. Between pans the camera is locked.
- Sound: a short air swish at pan peak, a soft thud on landing.

## Do
- Put a motion-blur streak on every moving element during the pan.
- Land on a composed frame with a clear focus.
- Keep the pan direction consistent.

## Don't
- No slow pans.
- No pan over text that must be read.
- No bounce on landing.

## Build notes
Modern kit: shift the scene wrapper with `translateX` and `filter: blur(Npx)` from `P.prog`. Blur horizontal only if you add an SVG `feGaussianBlur stdDeviation="24 0"`. Cut at the peak with `P.past('cutN')`.
