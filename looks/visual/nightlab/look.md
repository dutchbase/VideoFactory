---
id: "nightlab"
axis: "visual"
title: "Nightlab"
summary: "Neon outlines and one teal-style light on a dotted grid, with glowing packets drifting through the diagram."
aliases: ["neon lab", "night diagram", "glow grid"]
sources: ["https://ideatomotion.com/looks", "https://www.creatoros.ca/blog/motion-style-atlas/"]
best_for: ["explain-mechanism", "launch-announcement", "explainer", "short"]
formats: ["wide", "tall"]
pairs_with: {"editing": "cinematic-drift", "content": "explain-mechanism"}
preview: "native"
build: "native"
palette_roles: {"field": "bg", "panel": "surface", "neon": "accent", "neon2": "accent2", "dots": "line", "text": "ink"}
---

## Look
- Field: very dark `bg` with a dotted grid in `line` (2 px dots, 32 px apart). One soft radial light from the top in `accent` at 12-16% strength.
- Panels: `surface` fills with 1.5 px `accent` outlines and a soft outer glow (`box-shadow`, 18-30 px blur, `accent` at 35%).
- Packets: small bright dots in `accent2` with a glow trail.
- Type: `head` font, 52-68 px, `ink`. Labels in `mono` 16 px in `dim`. Glow only on the key word.

## Behaviour
- Entrances: panel outlines draw around their rectangle in 500 ms (`P.ease.enter`) and the fill fades in 200 ms later. Glow ramps from 0 to full over 400 ms.
- Wires: neon lines draw with `stroke-dashoffset`, 600 ms, `P.ease.linear`. Packets then travel along them in 900-1400 ms with `P.ease.move`, leaving a 120 px fading trail.
- Text: headline fades up 16 px, 360 ms, `P.ease.softLand`. Key word brightens its glow once.
- Camera: slow drift. Scale 1.00 to 1.04 and 12 px sideways over the whole scene, `P.ease.linear`. Dots move at half speed for parallax.
- Transitions: glow dims to 0 in 240 ms (`P.ease.exit`) and the next scene lights up. No hard wipes.
- Pacing: unhurried. 4-7 s holds, about 8-10 changes per minute.
- Ambient: dots twinkle at 8% opacity change, 3 s loop. Sound: low synth pad, soft electric hum, a glassy ping per packet.

## Do
- Keep one light source only.
- Let glow carry importance; only the active item glows fully.
- Keep text small and sharp against the dark.

## Don't
- No bounce or springy pops.
- No more than two glow colours.
- No glow on body text.
- No bright fills; neon is outline and line.

## Build notes
Native: CSS `box-shadow` and `filter: drop-shadow` for glow, `radial-gradient` for the light and the dot grid, SVG paths for wires. Keep blur small for render speed. On a light brand, dark panels still come from `surface`; check contrast.
