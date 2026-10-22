---
id: "brutalist-bold"
axis: "visual"
title: "Brutalist bold"
summary: "Raw grid, huge type, thick hard borders and flat blocks; loud, blunt and unpolished on purpose."
aliases: ["neo-brutalism", "brutalist web", "raw grid"]
sources: ["https://ideatomotion.com/looks", "https://explain.film/explainer-video-styles", "https://www.creatoros.ca/blog/motion-style-atlas/"]
best_for: ["launch-announcement", "myth-vs-fact", "hook-one-idea", "ad", "short"]
formats: ["wide", "tall"]
pairs_with: {"editing": "jump-cut-punch", "content": "hook-one-idea"}
preview: "native"
build: "native"
palette_roles: {"paper": "bg", "ink": "ink", "block1": "accent", "block2": "accent2", "block3": "r4", "frame": "line", "card": "surface"}
---

## Look
- Field: flat `bg` split by a visible grid of 6–8 px `ink` borders into hard cells. Cells are filled with solid `accent`, `accent2`, `r4` or `surface`.
- Cards: rectangles with 6 px `ink` border and a hard offset shadow (12 px right, 12 px down, solid `ink`, no blur). Corner radius 0.
- Type: `head` in its heaviest weight, uppercase, 160–300 px, tight leading (0.85), cropped by the frame edge on purpose. A `mono` label at 18–22 px in a bordered tag.
- No gradient, no glass, no soft shadow. Raw, a bit ugly, on purpose.

## Behaviour
- Entrances: blocks slam in from the nearest edge with `P.ease.crashIn`, 220 ms, with no overshoot. Cards stack with a 60 ms stagger. The hard shadow snaps in 80 ms after the card.
- Text: headlines cut in whole, no fade. Each word replaces the last in a hard cut every 180–260 ms. A key word flips its cell to `accent` on the hit.
- Transitions: grid cells flip colour in a checker sweep (30 ms stagger, 120 ms each) or the whole frame hard-cuts. Exit with `P.ease.accelExit`, 180 ms.
- Camera: locked, with a 12 px shake on the hit (2 frames), then still. No drift.
- Pacing: fast. 1.2–2.5 s holds, about 25–30 changes per minute. One 0.5 s silent beat before the key line.
- Ambient: a ticker band of mono text scrolls at 160 px per second, `P.ease.linear`. Nothing else moves.
- Sound: hard thumps and clacks on each slam; sparse bass or a drum loop, with silence on the key line.

## Do
- Crop type on the frame edge. Let one word fill the frame.
- Keep borders the same thickness everywhere (6 px).
- Use two high-contrast colours per frame.
- Align every cell to the same grid.

## Don't
- No rounded corners, blur or soft shadow.
- No easing that floats. Snap or slam only.
- No more than 6 words on screen.
- No small light-weight type.

## Build notes
Native CSS: `border: 6px solid var(--ink)`, `box-shadow: 12px 12px 0 var(--ink)`, CSS grid for cells. Use `P.prog` with `P.ease.crashIn`. For the shake, offset the frame by ±12 px for 2 frames. In tall, stack cells in 2 columns.
