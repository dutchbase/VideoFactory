---
id: "cinematic-papercut"
axis: "visual"
title: "Cinematic papercut"
summary: "Moody paper layers with dramatic light, shallow depth of field and a camera that dollies through the stack."
aliases: ["dark papercut", "paper diorama", "cinematic paper"]
sources: ["https://explain.film/explainer-video-styles/papercut", "https://www.creatoros.ca/blog/motion-style-atlas/"]
best_for: ["founder-story", "hook-one-idea", "ad", "short", "launch-announcement"]
formats: ["wide", "tall"]
pairs_with: {"editing": "cinematic-drift", "content": "founder-story"}
preview: "ai"
build: "ai"
palette_roles: {"far": "bg", "mid": "r1", "near": "r2", "glow": "accent2", "rim": "accent", "ink": "ink"}
---

## Look
- Field: a dark diorama. Paper layers from near-black far to mid tones near, with a single warm light source (`accent2`) low in the frame.
- Light: strong rim light on layer edges, long soft shadows, a light haze between layers (a 10-20% tint of the glow colour).
- Depth of field: the focus layer is sharp. Near and far layers blur 6-14 px. Dust specks drift in the beam.
- Contrast: the frame is 70% dark. One bright shape (moon, window, face) draws the eye.
- Type: `head`, 90-150 px, light `ink`, placed in a quiet dark area, wide tracking (+4%).

## Behaviour
- Camera: a dolly forward through the layers, scale and parallax from 1.0 to 1.15 over 4-6 s, `P.ease.move`. Near layers pass the lens and blur out.
- Focus pull: blur moves from the far layer to the subject over 1.2 s with `P.ease.softLand`.
- Entrances: layers settle in from 60 px lower, 900 ms, 100 ms stagger, `P.ease.softLand`. Light fades up in 1.5 s with `P.ease.enter`.
- Text: fades up with a 30 px rise, 700 ms, `P.ease.enter`, after the dolly slows.
- Transition: the camera passes through a near layer into the next scene (dark dip, 600 ms), `P.ease.accelExit` then `P.ease.enter`.
- Pacing: 5-8 s holds, about 6-10 changes per minute.
- Ambient: dust drift 8 px over 8 s, light flicker of 3% at 2 Hz.
- Sound: low drone, soft paper creaks, a deep boom on reveals.

## Do
- Keep one light source and one bright subject.
- Use blur to show depth, not to hide mistakes.
- Hold long on the reveal.

## Don't
- No flat bright fills or white backgrounds.
- No fast cuts and no bounce.
- No second light colour besides the rim.
- No dense text.

## Build notes
`preview: "ai"`: make the real still with AI images from the brand ramp (`image-generation.md`). Native stand-in uses SVG layers, a radial glow and `filter: blur`. Sample the dolly with scaled layers at different rates. Tall format: stack the layers vertically and dolly up.
