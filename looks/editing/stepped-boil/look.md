---
id: "stepped-boil"
axis: "editing"
title: "Stepped boil"
summary: "Stepped 8-12 fps motion with line boil; handmade, a little wobbly."
aliases: ["boil", "limited animation", "on twos and threes"]
sources: ["https://ideatomotion.com/looks", "https://www.creatoros.ca/blog/motion-style-atlas/", "https://explain.film/explainer-video-styles"]
best_for: ["explain-mechanism", "tutorial", "founder-story", "explainer", "course"]
formats: ["wide", "tall"]
pairs_with: ["napkin-sketch", "chalkboard", "stop-motion", "risograph", "claymation"]
preview: "native"
build: "native"
---

## Look
Motion looks hand-drawn. Everything updates at 8-12 frames per second, not 30, and every line jitters a little each step. The result feels crafted, like paper cut-outs or pencil frames.

## Behaviour
- Stepping: hold each pose for 3 frames at 30 fps (10 fps). Use 4 frames (7.5 fps) for slow items and 2.5-3 frames for fast ones. Positions snap, they do not glide.
- Easing: ease in steps. Compute `P.ease.enter` then quantise time: `t = floor(t * 10) / 10`.
- Boil: every line and shape gets 1-2 px of offset and 0.5 degree of rotation from `P.rand(seed + step)` each step. Loop 3 different offsets for a 0.3 s cycle.
- Entrance: pop from scale 0.8 to 1.0 in 4 steps (400 ms), no spring.
- Exit: 3 steps, 300 ms, shrink and jitter out.
- Scene change: a hard cut on a step (K1). A paper-slide wipe of 4 steps is allowed.
- Rhythm: a change on each spoken beat. Items arrive 2 steps apart.
- Pacing: 3-5 s per idea, 12-20 changes per minute.
- Camera: locked or a 3-step stepped nudge.
- Ambient: the boil runs everywhere all the time; it is the texture.
- Sound: pencil scratch on lines, paper rustle on cuts, no polished whooshes.

## Do
- Keep the boil small (under 2 px).
- Quantise every tween, also colour and opacity.
- Use the same step rate for the whole video.

## Don't
- No smooth 30 fps tween.
- No blur or glow.
- No boil on text that must be read at small size; use 1 px.

## Build notes
Modern kit: a helper `step(t) = Math.floor(t * 10) / 10` applied before `P.prog`. Boil with SVG `feTurbulence` plus `feDisplacementMap` and a `seed` that changes each step, or by CSS `translate` from `P.rand`. Keep it cheap for stills.
