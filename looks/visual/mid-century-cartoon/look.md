---
id: "mid-century-cartoon"
axis: "visual"
title: "Mid-century cartoon"
summary: "UPA-style flat cartoon: simple angular shapes, offset colour blocks, limited palette and a retro 1950s feel."
aliases: ["UPA style", "retro cartoon", "1950s modern", "mid-century modern"]
sources: ["https://explain.film/explainer-video-styles", "https://en.wikipedia.org/wiki/United_Productions_of_America"]
best_for: ["listicle", "founder-story", "explainer", "ad", "short"]
formats: ["wide", "tall"]
pairs_with: {"editing": "stepped-boil", "content": "listicle"}
preview: "native"
build: "native"
palette_roles: {"paper": "bg", "ink": "ink", "c1": "accent", "c2": "accent2", "c3": "r4", "c4": "green", "block": "surface"}
---

## Look
- Field: flat off-white or muted tone (`bg`). Colour fields are big flat blocks (`surface`, `r4`) that sit slightly off the ink outline, so colour and line do not match (the "misregistered" print look).
- Shapes: boomerangs, kidney blobs, starbursts, atomic dots and long triangles. Characters are tall angular figures with dot eyes and no detail.
- Line: `ink` outline at 4–6 px, only on some shapes. Texture: a light halftone or paper speckle at 5% opacity.
- Type: `head` bold 90–140 px, slightly tilted (−3°). A `mono` caption at 18 px. Big numbered headers ("1.", "2.") for lists.

## Behaviour
- Entrances: shapes pop in on 2 fps "limited animation": hold each pose 3 frames at 24 fps, `P.spring` `pop` for 280 ms. Blocks slide in from off-screen with `P.ease.crashIn` (320 ms) and settle with a 6 px overshoot.
- Text: headlines drop in letter by letter, 40 ms stagger, 200 ms each, `P.ease.pop`. A list number stamps in first, then its text, 150 ms later.
- Transitions: a colour block wipes across (350 ms, `P.ease.whip`) or the shapes shrink to a dot and the next set grows out of it (400 ms, `P.ease.move`).
- Camera: locked, with a stepped 2-frame slide of the background (parallax of 20 px) on pans.
- Pacing: bouncy and quick. 2–3.5 s holds, about 20 changes per minute.
- Ambient: stepped "boil" on outlines, redrawn every 4 frames with a 1–2 px shift. Starbursts rotate in 15° steps every 0.5 s.
- Sound: pizzicato strings, xylophone hits and slide-whistles on moves; light jazz bed.

## Do
- Use a limited set of 4 colours and keep the outline shifted off the fill.
- Show each list item with its own number and one flat prop.
- Exaggerate with squash and stretch (1.15 max).
- Keep character faces to dots and one line.

## Don't
- No gradients, no glow, no realistic detail.
- No smooth 60 fps tweens on characters. Keep the stepped feel.
- No glossy or glass effects.
- No more than 5 shapes in a frame.

## Build notes
Native CSS and SVG. Offset fill and stroke by 6–10 px using two stacked layers. Use `steps()` timing or time quantised in `P.prog` to 12 fps for the limited feel. Halftone with a radial-gradient pattern at low opacity.
