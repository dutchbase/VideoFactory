---
id: "halftone-pop"
axis: "visual"
title: "Halftone pop"
summary: "A comic-book panel look with thick black outlines, Ben-Day dots, bold lettering and flat colour captions."
aliases: ["pop comic", "comic panel", "lichtenstein", "ben-day"]
sources: ["https://explain.film/explainer-video-styles/comic-book", "https://www.creatoros.ca/blog/motion-style-atlas/"]
best_for: ["short", "ad", "myth-vs-fact", "launch-announcement"]
formats: ["wide", "tall"]
pairs_with: {"editing": "jump-cut-punch", "content": "myth-vs-fact"}
preview: "native"
build: "native"
palette_roles: {"paper": "bg", "dots": "accent2", "outline": "ink", "caption": "r4", "hot": "accent", "sound": "danger"}
---

## Look
- Panel: a rectangular panel with a 10-14 px `ink` border that tapers at the corners, on a paper gutter in `bg`.
- Dots: a Ben-Day dot field (12 px dots, 18 px pitch) in `accent2` as shade, with a second dot field in `accent` on the shadow side.
- Captions: flat boxes in `r4` with a 4 px `ink` border and a hard 6 px offset shadow. Burst shapes in `accent` with a jagged edge for emphasis.
- Type: bold `head` font in caps, 80-140 px, with an `ink` outline. Short words such as 'POW' and 'WHY?' in a burst.

## Behaviour
- Entrances: panels slam in from off-screen, 320 ms, `P.ease.crashIn`. Captions pop with `P.spring` pop (400 ms). Bursts scale 0.8 to 1.0 and rotate -4 degrees in 280 ms.
- Dots: the dot field wipes in as a diagonal band over 400 ms (`P.ease.whip`).
- Shake: on a hit word, the panel shakes 6 px for 160 ms (4 frames).
- Transitions: next panel replaces the current with a hard cut or a quick page-slide of 230 ms (`P.ease.whip`). Panels may split into two in 300 ms.
- Camera: locked inside a panel; zoom between panels as a cut.
- Pacing: 2-3.5 s holds, about 16-22 changes per minute. Sound: comic hits, whooshes, a short stinger on each new panel.

## Do
- Show one idea per panel with one caption.
- Keep outlines thick and the colours flat.
- Use the burst for the single most important word.

## Don't
- No soft gradients, glow or blur.
- No more than three flat colours plus `ink`.
- No small text; captions stay large.
- No smooth ease-out drifting; hits are hard.

## Build notes
Native: CSS borders, `radial-gradient` for dots with `mask-image`, SVG `polygon` for bursts, `box-shadow` with zero blur for caption shadows. Tall format: stack 2 panels vertically.
