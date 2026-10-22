---
id: "risograph"
axis: "visual"
title: "Risograph"
summary: "Two-ink print look: flat colour blocks, halftone fields, small misregistration and paper grain; stamped-in, punchy."
aliases: ["riso", "riso zine", "two-ink print", "zine"]
sources: ["https://explain.film/explainer-video-styles/risograph", "https://ideatomotion.com/looks", "https://www.creatoros.ca/blog/motion-style-atlas/"]
best_for: ["short", "ad", "launch-announcement", "hook-one-idea"]
formats: ["wide", "tall"]
pairs_with: {"editing": "jump-cut-punch", "content": "hook-one-idea"}
preview: "native"
build: "native"
palette_roles: {"paper": "bg", "ink1": "accent", "ink2": "accent2", "black": "ink", "grain": "faint", "edge": "line"}
---

## Look
- Field: paper in `bg` with fine grain. Two inks only: `accent` and `accent2`, plus `ink` for text. Where the two inks overlap they multiply to a darker third tone.
- Print flaws: each ink layer is offset 3-5 px from the other (misregistration). Edges are rough, with small speckle holes.
- Halftone: dot fields in one ink for shade and gradients (6-10 px dots). No smooth gradients.
- Type: heavy `head` font 90-150 px, tightly set, in one ink with the other ink offset behind it. Small `mono` labels 14-18 px.

## Behaviour
- Entrances: elements stamp in. Scale from 1.08 to 1.0 with `P.ease.crashIn` (330 ms) and the second ink layer arrives 2 frames later, off by 4 px.
- Text: whole words stamp, one per beat, 0.3-0.4 s apart. No letter-by-letter typing.
- Halftone dots grow from 0 to full size in 300 ms (`P.ease.softLand`) in a stagger of 20 ms per row.
- Transitions: a block of solid ink slams across in 230 ms (`P.ease.whip`) and reveals the next scene. Or a hard cut with a 2-frame ink flash.
- Ambient: grain shifts every 2 frames; no other motion. Camera: locked.
- Pacing: 2-4 s holds, about 15-20 changes per minute. Sound: paper stamps, roller thumps, short snare hits.

## Do
- Use only two inks and keep one for the hero.
- Keep misregistration small and the same direction.
- Let flat shapes and dots carry the picture.

## Don't
- No smooth gradients or soft shadows.
- No third bright colour.
- No slow drift or glow.
- No letter-perfect alignment of the two ink layers.

## Build notes
Native: stack two copies of each shape with `mix-blend-mode: multiply`, one offset by 4 px. Halftone with `radial-gradient` dot patterns and `mask-image`. Grain with a small SVG `feTurbulence` overlay at 8% opacity. Tall format: stack words in a column.
