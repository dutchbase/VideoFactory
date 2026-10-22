---
id: "flat-vector"
axis: "visual"
title: "Flat vector"
summary: "Bold flat illustration with simple shapes, thick tidy outlines and bright brand colours; friendly, clear and quick to read."
aliases: ["flat design", "bold flat illustration", "flat vector science"]
sources: ["https://explain.film/explainer-video-styles/flat-vector", "https://www.creatoros.ca/blog/motion-style-atlas/"]
best_for: ["explain-mechanism", "listicle", "onboarding", "explainer", "course"]
formats: ["wide", "tall"]
pairs_with: {"editing": "beat-snap", "content": "listicle"}
preview: "native"
build: "native"
palette_roles: {"field": "bg", "shape1": "accent", "shape2": "accent2", "shape3": "r4", "shape4": "r6", "skin": "r7", "outline": "ink", "card": "surface"}
---

## Look
- Field: flat `bg`, sometimes one large soft circle in a ramp tone behind the subject.
- Shapes: circles, rounded rectangles, simple characters and objects. Fills in `accent`, `accent2` and ramp tones. One flat shade per shape, optional second shade for a fold.
- Outline: none, or a uniform 4 px `ink` outline on all shapes (pick one per video).
- Characters: round heads, no facial detail beyond eyes and a mouth line, limbs as thick rounded bars.
- Type: `head` bold 64-96 px headline, `font` 28 px body. Numbered badges in circles.

## Behaviour
- Entrances: shapes pop in from scale 0.9 with `P.spring` snap (`{ dur: 0.35, bounce: 0.1 }`), 60 ms stagger, or slide 80 px with `P.ease.enter` (400 ms).
- Lists: items enter one per beat, number badge first (240 ms), text 80 ms later.
- Characters: one loop per action (wave, point, walk), 600-1000 ms, `P.ease.move`. Limbs rotate around joints.
- Transitions: a circle wipe in `accent` grows from the focus point in 600 ms (`P.ease.move`), or a slide push of 800 ms.
- Camera: locked, or a slow push of 5% over a 5 s hold (`P.ease.linear`).
- Pacing: 3-5 s holds, about 14-20 changes per minute.
- Ambient: objects with life loop gently (a gear turns 360 degrees in 6 s, a cloud drifts 40 px in 8 s).
- Sound: soft pops and plucks, bright light bed.

## Do
- Reduce each idea to one icon-like scene.
- Reuse the same 4 shape colours all video.
- Keep outlines the same width everywhere.

## Don't
- No gradients, shadows, textures or 3D.
- No detailed faces or realistic proportions.
- No more than 6 objects in a scene.
- No mixed outline and no-outline shapes.

## Build notes
Inline SVG groups with `transform-origin` set for joints; animate with `P.prog` and `P.spring`. Reusable pieces can live in `library/` as SVG parts. Works in tall: scene on top, text below.
