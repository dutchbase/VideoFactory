---
id: "synthwave"
axis: "visual"
title: "Synthwave"
summary: "Neon retro-futurism: a striped sunset, a glowing perspective grid and chrome-bright type on a deep night sky."
aliases: ["outrun", "retrowave", "neon 80s", "vaporwave grid"]
sources: ["https://explain.film/explainer-video-styles", "https://www.creatoros.ca/blog/motion-style-atlas/"]
best_for: ["ad", "launch-announcement", "hook-one-idea", "short", "explainer"]
formats: ["wide", "tall"]
pairs_with: {"editing": "audio-led-cuts", "content": "launch-announcement"}
preview: "native"
build: "native"
palette_roles: {"sky": "bg", "sun-top": "accent", "sun-bottom": "accent2", "grid": "accent2", "glow": "accent", "text": "ink", "haze": "surface"}
---

## Look
- Sky: a deep `bg` gradient to a lighter `surface` haze at the horizon, with a few small `ink` stars.
- Sun: a large circle at the horizon, filled with a vertical gradient from `accent` (top) to `accent2` (bottom). Horizontal slits cut it from the lower half, widening toward the bottom.
- Floor: a perspective grid in thin `accent2` lines (2 px) that glows (blur 6–10 px, 60% opacity) and runs to a vanishing point at the horizon.
- Silhouettes: dark mountains or a city line at the horizon in `bg`, edged with a thin `accent` rim.
- Type: brand `head` in heavy weight, wide tracking, caps or italic-slanted, `ink` fill with an `accent` glow (text-shadow 0 0 24 px). 72–120 px.

## Behaviour
- Entrances: the sun rises from behind the horizon over 1.2 s with `P.ease.enter`; the grid draws from the horizon forward in 800 ms. Headline letters flicker on like neon: 2 quick flashes (60 ms on, 40 ms off) then steady, 40 ms stagger per letter.
- Ambient: the grid scrolls toward the camera at a steady 1 grid cell per 0.8 s (`P.ease.linear`), looped. The sun slits crawl down slowly. A scanline shimmer or 2 px chromatic offset on text pulses every 2–3 s.
- Exits: neon text cuts off with a 2-frame flicker and a 120 ms fade (`P.ease.exit`).
- Transitions: a horizontal scanline wipe in `accent` (300 ms `P.ease.whip`), a glitch cut on the beat, or a fast fly-forward along the grid.
- Camera: a low, forward-moving camera over the grid; keep the horizon at 55–62% of the height. A 2–3% drift upward is allowed.
- Pacing: cuts land on the music beat; 2–4 s holds, about 16–22 changes per minute.
- Sound: a driving 4/4 synth bass, gated snares, laser blips on text hits.

## Do
- Keep one glow colour family from `accent` to `accent2`.
- Put the headline over the sky, never over the grid lines.
- Cut on the beat.
- Keep the horizon line clear and strong.

## Don't
- No soft pastel or warm natural tones.
- No glow on more than three elements at once.
- No small body text on the grid.
- No slow, dreamy motion; the grid keeps moving.

## Build notes
Native CSS and SVG: the grid is a rotated `perspective` plane or an SVG with converging lines; scroll it with `background-position` on `P.ease.linear`. Glow uses `filter: blur()` copies or `text-shadow`; keep at most four blurred layers per shot. The sun slits are a `mask` of repeating gradients. Works in both formats; in tall, raise the sun and stack the headline above it.
