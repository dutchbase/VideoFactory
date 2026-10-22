---
id: "tech-glow"
axis: "visual"
title: "Tech glow"
summary: "Dark field with a perspective grid, neon glass cards and drifting particles; futuristic, fast and high-contrast."
aliases: ["tech explainer", "neon glass", "cyber grid"]
sources: ["https://www.creatoros.ca/blog/motion-style-atlas/", "https://ideatomotion.com/looks"]
best_for: ["product-tour", "launch-announcement", "ad", "explainer", "short"]
formats: ["wide", "tall"]
pairs_with: {"editing": "zoom-through", "content": "launch-announcement"}
preview: "native"
build: "native"
palette_roles: {"void": "bg", "glass": "surface", "rim": "line", "neon": "accent", "neon2": "accent2", "ink": "ink", "dim": "dim"}
---

## Look
- Field: deep `bg`, with a perspective floor grid in `line` and a horizon glow in `accent` at 25%.
- Cards: translucent `surface` panels (60% opacity, 12 px blur) with a 1.5 px rim in `accent` or `accent2` and a soft outer glow.
- Particles: 20-40 small dots and streaks in `accent` and `ink` drifting upward.
- Type: `head` bold 72-110 px in `ink` with a faint `accent` glow; `mono` 14-18 px for data labels. Numbers glow brighter.

## Behaviour
- Grid: the floor grid scrolls toward the camera at 120 px/s (`P.ease.linear`), always on.
- Cards: fly in from depth, scale 0.9 to 1 and 60 px up, 560 ms with `P.ease.enter`, 70 ms stagger. The rim draws around the edge in 400 ms.
- Text: headline reveals by a left-to-right light sweep in 500 ms (`P.ease.softLand`); numbers count up in 800 ms.
- Camera: slow dolly forward, 6% scale over a hold; on a cut the camera pushes through a card in 700 ms (`P.ease.whip`).
- Transitions: a glow flash (accent at 30%, 120 ms) and a push-through into the next scene. Exit: cards fade and sink 30 px in 250 ms (`P.ease.exit`).
- Pacing: 2.5-4 s holds, about 16-22 changes per minute. Rest 1 s after a flash.
- Ambient: particles drift up at 20-60 px/s; a rim pulse every 3 s at 8%.
- Sound: low synth pulse, glassy tick on each card, riser before a flash.

## Do
- Keep one hero card larger than the others.
- Use glow only on `accent` elements and numbers.
- Keep text on cards at contrast 4.5:1 or higher.

## Don't
- No more than two glow colours.
- No rainbow gradients, no lens flares.
- No glow on body text.
- No particle count above 40.

## Build notes
Native: CSS `perspective` and `rotateX(65deg)` for the floor, `backdrop-filter: blur`, `box-shadow` for glow, canvas or absolutely placed dots for particles driven by `P.rand`. In tall, stack cards in one column.
