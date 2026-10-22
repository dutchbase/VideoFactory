---
id: "layered-papercut"
axis: "visual"
title: "Layered papercut"
summary: "A shadow box of stacked paper layers in brand tones with soft light; each layer sits at its own depth and moves a little differently."
aliases: ["papercut", "paper layers", "shadow box"]
sources: ["https://explain.film/explainer-video-styles/papercut", "https://www.creatoros.ca/blog/motion-style-atlas/"]
best_for: ["founder-story", "hook-one-idea", "explainer", "short", "ad"]
formats: ["wide", "tall"]
pairs_with: {"editing": "canvas-pan", "content": "founder-story"}
preview: "ai"
build: "ai"
palette_roles: {"back": "bg", "layer1": "r2", "layer2": "r3", "layer3": "accent", "layer4": "accent2", "front": "r5", "ink": "ink"}
---

## Look
- Field: 4-6 flat paper layers, each a wavy or hill-shaped cut-out, stacked from back (dark ramp tone) to front (light or accent tone).
- Depth: each layer casts a soft inner shadow on the one below it (blur 20-40 px, 25-35% black from `bg`). A soft light comes from the top left.
- Edges: smooth hand-cut curves, no outlines. A faint paper fibre texture on every layer.
- Subjects: a simple paper silhouette (a house, a tree, a person) on the middle layer.
- Type: `head` font on a paper strip or cut into a layer, 80-140 px, one line or two.

## Behaviour
- Entrances: each layer rises from below the frame in turn, back to front, 80 ms stagger, 700 ms each, `P.ease.softLand`.
- Parallax: layers shift by depth. Back layer moves 10 px, front layer 60 px, over 3 s with `P.ease.move`. This is the camera.
- Camera: a slow lateral drift or a push of 1.0 to 1.08 over each hold, `P.ease.linear`. No shake.
- Text: the title strip slides up 40 px and fades in over 500 ms with `P.ease.enter`.
- Transition: layers drop away front to back (`P.ease.accelExit`, 430 ms) and the next scene's layers rise.
- Pacing: 4-6 s holds, about 8-12 changes per minute. The scene stays calm.
- Ambient: tiny paper float, 2-4 px, 6 s loop on the nearest layer, `P.ease.move`.
- Sound: soft paper rustle on each rise, a low warm pad underneath.

## Do
- Keep layers in a strict colour order from dark far to light near.
- Make shadows soft and consistent from one light.
- Leave one clear space on the middle layer for the subject or the title.

## Don't
- No hard black outlines, glossy shine or neon.
- No flat scene without shadow between layers.
- No fast whip moves.
- No more than one title per frame.

## Build notes
`preview: "ai"`: the real still comes from an AI image batch (`image-generation.md`) using the brand ramp. The native `preview.html` is a stand-in with CSS `clip-path` waves and `filter: drop-shadow`. A native build is possible with SVG layers and parallax in `P`; use AI images for detailed subjects.
