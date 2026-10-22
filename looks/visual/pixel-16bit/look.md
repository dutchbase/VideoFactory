---
id: "pixel-16bit"
axis: "visual"
title: "Pixel 16-bit"
summary: "Chunky pixel art with a limited palette, a console-game HUD and stepped motion, like a 16-bit adventure."
aliases: ["pixel art", "8-bit", "retro game", "16-bit odyssey"]
sources: ["https://explain.film/explainer-video-styles", "https://www.creatoros.ca/blog/motion-style-atlas/"]
best_for: ["course", "tutorial", "listicle", "short", "explainer"]
formats: ["wide", "tall"]
pairs_with: {"editing": "stepped-boil", "content": "tutorial"}
preview: "native"
build: "native"
palette_roles: {"sky": "bg", "ground": "surface", "block": "raised", "hero": "accent", "coin": "r4", "enemy": "danger", "grass": "green", "hud": "ink", "line": "line"}
---

## Look
- Grid: the whole frame is built on a 8 px (or 10 px) pixel grid. Every edge is axis-aligned and stepped. No anti-aliasing, no rotation except 90°.
- Palette: 6–10 flat tones from the brand: `accent`, `accent2`, `green`, `danger`, a ramp tone and `ink`. No gradients; depth uses 2–3 tone dithering.
- World: a flat sky (`bg`), a tiled ground strip in `surface` and `green`, blocky clouds or hills, platforms from `raised` blocks with a 1-pixel `line` edge.
- HUD: top bar with "SCORE", "LEVEL" and a progress bar in `mono`, hearts or coins as pixel icons.
- Characters: sprites of 16–32 px scaled up 4–6×, with a 1-pixel `bg` outline.
- Type: brand `mono` (or `head` if blocky) in caps, 24–72 px, with a hard 4 px offset shadow. Dialogue boxes have a thick `ink` border and typewriter text.

## Behaviour
- Frame rate: all motion steps at 8–12 fps and snaps to the pixel grid. Positions round to the nearest 8 px.
- Entrances: sprites hop in along a 3-step arc, or blocks drop from above and land with a 2-frame squash. Use `P.ease.linear` sampled in steps of 100 ms; never smooth springs.
- Text: dialogue and headings type in one character per 50 ms with a tick. A blinking cursor box (400 ms on, 400 ms off).
- Ambient: clouds scroll left at 12 px/s in 8 px steps; a coin spins in a 4-frame loop every 400 ms; the HUD score ticks up.
- Exits: pieces blink 3 times (80 ms each) and vanish, or fall off the bottom in 4 steps.
- Transitions: a pixel dissolve (blocks of 40 px flip over 500 ms), an iris circle closing in 8 steps, or a horizontal screen slide in 160 px steps.
- Camera: side-scroll in 8 px steps. No smooth zoom.
- Pacing: 2–4 s holds, about 15–20 changes per minute. One "level" per step of the topic.
- Sound: chiptune square-wave bed, coin blips, jump bleeps, a fanfare on completion.

## Do
- Show progress as a level number or a progress bar.
- Keep the same pixel size across the whole frame.
- Use a dialogue box for the voice's key sentence.
- Use blocky, readable caps for headlines.

## Don't
- No smooth curves, blur, glow or gradients.
- No mixed pixel sizes.
- No smooth easing between positions.
- No long paragraphs in dialogue boxes.

## Build notes
Native CSS: draw sprites with `box-shadow` pixel lists, or SVG `<rect>` at 8 px steps; set `image-rendering: pixelated` for any scaled bitmap. Step motion by rounding `P.prog` values to 1/10 s and to 8 px. Typewriter text uses `P.prog` mapped to the character count. Works in both formats.
