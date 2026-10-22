---
id: "keynote-black"
axis: "visual"
title: "Keynote black"
summary: "Near-black field with one softly lit object and large type that blurs into focus; quiet, expensive and confident."
aliases: ["keynote", "product launch black", "dark stage"]
sources: ["https://ideatomotion.com/looks", "https://explain.film/explainer-video-styles"]
best_for: ["launch-announcement", "hook-one-idea", "product-tour", "ad", "short"]
formats: ["wide", "tall"]
pairs_with: {"editing": "cinematic-drift", "content": "launch-announcement"}
preview: "native"
build: "native"
palette_roles: {"stage": "bg", "object": "raised", "rim": "accent", "ink": "ink", "dim": "dim", "glow": "accent2"}
---

## Look
- Field: the darkest brand tone (`bg`), with a faint vignette. If the brand is light, flip to its darkest ramp tone for the field.
- Hero: one object (device, shape, number) centred or at the rule of thirds, lit from one side. Rim light in `accent`, a soft pool of light on the floor in `accent2` at 20%.
- Type: `head` medium or semibold, 64-120 px, centred, `ink`; one line of `dim` support text at 28 px. Max 6 words.
- Space: at least 55% of the frame stays dark and empty.

## Behaviour
- Type entrances: each line blurs in, from blur 18 px, opacity 0 and 12 px low to sharp in 700 ms (`P.ease.enter`). Lines 180 ms apart.
- Object: fades up out of darkness over 900 ms, light sweeps across it from left to right in 1.4 s (`P.ease.move`).
- Camera: very slow push-in, 4% over the whole hold (`P.ease.linear`), 4-7 s.
- Transitions: dip to black for 300 ms (`P.ease.exit` out, `P.ease.enter` in), or the object morphs into the next in 800 ms.
- Exit: text blurs out to 12 px and fades in 400 ms (`P.ease.exit`).
- Pacing: one idea, 4-7 s holds, about 8-12 changes per minute. Silence between beats is part of the look.
- Ambient: the light sweep repeats every 6 s at 10% strength. Nothing else moves.
- Sound: deep sub hit on the title, quiet air bed, soft click on text.

## Do
- Show one thing at a time.
- Let the dark breathe; add no filler.
- Keep the lit side consistent across scenes.

## Don't
- No second object, no grid, no icons, no cards.
- No bounce, pop or fast motion.
- No bright full-screen colour fields.
- No body text above 6 words.

## Build notes
CSS `filter: blur()` animated with `P.prog`, radial gradients for light pools, `mix-blend-mode: screen` for the sweep. The hero object is an SVG, a library part or an AI image. Same layout works in tall with larger type.
