---
id: "liquid-glass"
axis: "visual"
title: "Liquid glass"
summary: "Frosted translucent panels with bright rims floating over slow blurred brand-colour gradients; premium, calm and touchable."
aliases: ["glassmorphism", "frosted glass", "apple liquid glass"]
sources: ["https://explain.film/explainer-video-styles/liquid-glass", "https://www.creatoros.ca/blog/motion-style-atlas/"]
best_for: ["product-tour", "launch-announcement", "explain-mechanism", "ad", "explainer"]
formats: ["wide", "tall"]
pairs_with: {"editing": "cinematic-drift", "content": "product-tour"}
preview: "native"
build: "native"
palette_roles: {"field": "bg", "blob-a": "accent", "blob-b": "accent2", "glass": "ink", "rim": "ink", "text": "ink"}
---

## Look
- Field: the brand `bg`, with two or three large, heavily blurred blobs (blur 80–140 px) in `accent`, `accent2` and a ramp tone behind everything.
- Glass: panels, pills and buttons filled with 8–16% `ink` over a `backdrop-filter: blur(24–40px) saturate(1.4)`. Each has a 1 px rim of 30–50% `ink` that is brighter on the top-left edge, a soft inner glow and a long, faint shadow.
- Radius: generous and consistent (24–40 px panels, full pills). Depth comes from blur, light and shadow only, never from outlines.
- Type: the brand `font` in light to semibold, 40–72 px headlines, sentence case, plenty of tracking room. Thin line icons in `ink`.

## Behaviour
- Entrances: panels rise 24–40 px and fade in with `P.spring` settle (`{ dur: 0.6, bounce: 0 }`); scale starts at 0.96. Stagger panels 60–80 ms.
- Transforms: a panel stretches into the next panel size (morph width, height and radius together, 600–800 ms `P.ease.move`) instead of cutting. Panels slide over each other and the blur shows what is under them.
- Light: the rim highlight glides across a panel as it moves (a 200–400 ms sheen on landing). The background blobs drift very slowly (one full loop per 20–30 s) as the only ambient motion.
- Transitions: cross-dissolve through a full-frame frosted blur (300–500 ms), or a panel grows to fill the frame and becomes the next scene.
- Camera: almost locked; a slow 2–4% push-in over a shot is allowed.
- Pacing: calm, 4–7 s holds, about 8–12 changes per minute. "Nothing snaps."
- Sound: soft whooshes, glassy taps, warm pad or minimal piano.

## Do
- Keep two or three glass layers at most so the depth reads.
- Put the key number or word on the frontmost, brightest panel.
- Keep text contrast high: darken or lighten the area behind text.
- Use a lens moment (a round glass that magnifies one detail) once per video at most.

## Don't
- No hard cuts mid-idea, no bounce, no shake.
- No busy photo behind glass; the background stays soft colour.
- No thick borders, neon, or stacked drop shadows.
- Never put long paragraphs on glass.

## Build notes
Native in the Modern kit with `backdrop-filter`, `filter: blur()` blobs and layered `box-shadow`. Blur is heavy on render: keep at most four blurred elements per shot and render at the final size. Morphs use `P.prog` on width, height and border-radius. Works in both formats.
