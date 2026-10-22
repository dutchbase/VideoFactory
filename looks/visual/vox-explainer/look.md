---
id: "vox-explainer"
axis: "visual"
title: "Vox explainer"
summary: "Editorial explainer collage: cut-out photos on paper, highlighter marks, map zooms, clippings, bold captions and simple charts."
aliases: ["vox style", "editorial explainer", "news explainer"]
sources: ["https://explain.film/explainer-video-styles/editorial-collage", "https://ideatomotion.com/looks", "https://www.creatoros.ca/blog/motion-style-atlas/"]
best_for: ["data-story", "timeline", "myth-vs-fact", "explainer", "short"]
formats: ["wide", "tall"]
pairs_with: {"editing": "scroll-build", "content": "data-story"}
preview: "native"
build: "library"
palette_roles: {"paper": "bg", "card": "surface", "ink": "ink", "marker": "accent", "mark2": "accent2", "rule": "line", "cutout": "raised"}
---

## Look
- Field: warm paper (`bg`) with a faint grain. Cut-out subjects sit on it with a thick white edge and a soft drop shadow, like paper cut with scissors.
- Marks: a highlighter bar in `accent2` behind key words, a hand circle or arrow in `accent`, and torn-paper strips in `surface`.
- Props: newspaper clippings (headline in `head`, body as grey lines), a simple map, a flat bar or line chart in two brand colours.
- Type: bold `head` captions, 64-110 px, left-aligned, in a white or `ink` label block. Small `mono` source tags at 14-16 px ("SOURCE: ...").
- Photos are library or stock images, cut out. If a photo is missing, use a flat silhouette in `raised`.

## Behaviour
- Entrances: cut-outs slide in 40-80 px with a slight tilt (2-4 degrees) using `P.ease.softLand` (400 ms). Clippings drop in with `P.ease.crashIn` (330 ms) and settle.
- Highlighter: a bar wipes left to right behind the key word in 350 ms with `P.ease.move`, starting 0.04 s before the spoken word.
- Map zoom: scale the map 1.0 to 2.4 on the place, `P.ease.move`, 1.6 s. Drop a pin with `P.spring` pop.
- Charts: bars grow from the base in 500 ms, 60 ms stagger, `P.ease.enter`. A number counts up in 800 ms.
- Exits: `P.ease.exit` 250 ms, items slide down and out. Scene change is a paper-slide wipe, 800 ms.
- Camera: slow push on the whole collage, scale 1.0 to 1.04 over the hold, `P.ease.linear`. No shake.
- Pacing: one new object every 1.5-3 s, holds of 3-5 s, about 18-24 changes per minute.
- Ambient: faint paper grain only. Sound: soft paper swish on each cut-out, a pen scratch on the highlighter, a low thud on the clipping.

## Do
- Put one fact on each frame and mark the key words with the highlighter.
- Show the source on any number.
- Layer 3-6 objects with different depth and tilt.
- Use the map zoom to open each new place or topic.

## Don't
- No glossy gradients, glow or glass.
- No more than two marker colours per frame.
- No text on top of a busy photo without a label block.
- No bounce on charts.

## Build notes
Modern kit: CSS cut-out with `filter: drop-shadow` and a white border, `clip-path` for torn edges, `mix-blend-mode: multiply` for the highlighter. Photos come from `library/` (`library.md`). Charts use the data-journalism helpers. Tall format: stack caption above one big cut-out.
