---
id: "soft-3d-clay"
axis: "visual"
title: "Soft 3D clay"
summary: "Rounded, matte 3D props with pastel colour and soft light that float and bob; friendly, tactile and calm."
aliases: ["clay 3d", "soft 3d", "inflated 3d", "claymorphism"]
sources: ["https://www.creatoros.ca/blog/motion-style-atlas/", "https://explain.film/explainer-video-styles"]
best_for: ["onboarding", "product-tour", "hook-one-idea", "explainer", "short"]
formats: ["wide", "tall"]
pairs_with: {"editing": "cinematic-drift", "content": "product-tour"}
preview: "ai"
build: "ai"
palette_roles: {"field": "bg", "prop-a": "accent", "prop-b": "accent2", "prop-c": "r4", "prop-d": "green", "shadow": "faint", "text": "ink"}
---

## Look
- Field: a smooth `bg` backdrop with a very soft vertical gradient and a faint floor shadow. No horizon line.
- Props: pillowy shapes (spheres, rounded cubes, capsules, tori) with big radii. Matte surface, a soft highlight on the top-left, a soft inner shade on the bottom-right. Colours are the brand tones lightened toward pastel.
- Light: one large soft key light and a gentle ambient fill. Shadows are wide, blurry and tinted by the object colour.
- Icons and UI are built as 3D props: a chat bubble is an inflated pill, a chart is rounded bars.
- Type: brand `head` in semibold to heavy, 48–84 px, sentence case, `ink` colour, rounded feel.

## Behaviour
- Entrances: props scale from 0.9 and rise 30 px with `P.spring` pop (`{ dur: 0.4, bounce: 0.25 }`), with a small squash on landing (scale y 0.94 for 120 ms). Stagger 60–80 ms.
- Ambient: every prop bobs 6–10 px vertically on a 3–4 s sine loop, each with a different phase. Slow 4–8° rotation sway. This is the main ambient motion.
- Exits: props shrink to 0.9 and fade in 240 ms with `P.ease.exit`, or float up and out.
- Transitions: a big round prop grows to fill the frame (600 ms `P.ease.move`) and becomes the next background colour. Or a soft cross-dissolve of 400 ms.
- Camera: a slow orbit or push-in of 3–5% over 4 s with `P.ease.move`. Depth of field softens far props.
- Pacing: 3–6 s holds, about 10–12 changes per minute.
- Sound: soft bubbly pops, marimba and warm synth pad.

## Do
- Keep three to five props per shot with one clear hero prop.
- Use pastel tints of the brand tones, not new colours.
- Round every edge.
- Leave generous space around the hero.

## Don't
- No hard edges, outlines or flat vector shapes.
- No glossy chrome or harsh reflections.
- No dark, gritty scenes.
- No dense text; one short line per shot.

## Build notes
`preview: "ai"`: true soft 3D needs AI images or 3D renders (`_shared/image-generation.md`). Generate each hero prop on a plain background, cut it out and animate in the Modern kit with bobs, springs and soft shadows. The native `preview.html` is a CSS stand-in using radial gradients and blurred shadows. Works in both formats.
