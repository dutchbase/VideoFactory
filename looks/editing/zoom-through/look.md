---
id: "zoom-through"
axis: "editing"
title: "Zoom through"
summary: "One continuous shot: the camera zooms into a detail and that detail becomes the next scene."
aliases: ["infinite zoom", "fractal zoom", "dive in"]
sources: ["https://ideatomotion.com/looks", "https://www.creatoros.ca/blog/motion-style-atlas/", "https://explain.film/explainer-video-styles"]
best_for: ["explain-mechanism", "product-tour", "timeline", "explainer", "launch-announcement"]
formats: ["wide", "tall"]
pairs_with: ["isometric-3d", "depth-bento", "flat-vector", "tech-glow", "blueprint"]
preview: "native"
build: "native"
---

## Look
There is no cut. Each scene holds a small window, button or dot. The camera dives into it and what was tiny becomes the full next scene. The whole video feels like one long fall inwards.

## Behaviour
- Dive: scale the whole scene about the target point from 1.0 to 8-12x over 600-900 ms with an exponential rate (x1.5-2 per 2 frames, E5 in `_shared/transitions.md`). Use `P.ease.accelExit`.
- Blur: ramp 0 to 20 px during the last 40% of the dive (K4). B starts at equal or more blur and sharpens to 0 in 400 ms with `P.ease.softLand`.
- Handover: the target element in A becomes B's ground. Its colour and position (within 0.02) are the same at the swap frame. Swap in one frame at peak blur.
- B starts large: B's content scales from 0.1x to 1.0x during the same dive so it looks like it was always inside.
- Hold: after landing, B holds 2-4 s with a locked camera. Only B's own elements move.
- Rhythm: start the dive on the verb of the last phrase; land on the first word of the next.
- Pacing: 5-8 s per level, 7-12 dives per minute. Max 5 levels in a row, then pull out once.
- Camera: the dive is the only move. No pans.
- Sound: a rising tone under the dive, a soft thud on landing.

## Do
- Draw a small, clear target in every scene.
- Keep colours one step apart so the nesting reads.
- Pull out once at the end to show the whole chain.

## Don't
- No fade-through.
- No dive without a visible target.
- No second camera move during a dive.

## Build notes
Modern kit: group all scenes in one `.world` and scale it about the target's `transform-origin`. Nest B at 0.1x inside A's target in the markup. Use `P.prog` with `P.ease.accelExit`. See `_shared/motion.md` Cuts for zoom-through numbers.
