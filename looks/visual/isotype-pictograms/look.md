---
id: "isotype-pictograms"
axis: "visual"
title: "ISOTYPE pictograms"
summary: "Data as rows of simple identical icons, one icon for a fixed number of units, in Otto Neurath's ISOTYPE style."
aliases: ["Isotype", "Neurath pictograms", "pictogram chart", "icon counts"]
sources: ["https://www.creatoros.ca/blog/motion-style-atlas/", "https://explain.film/explainer-video-styles", "https://en.wikipedia.org/wiki/Isotype_(picture_language)"]
best_for: ["data-story", "compare", "listicle", "explainer", "course"]
formats: ["wide", "tall"]
pairs_with: {"editing": "stepped-boil", "content": "data-story"}
preview: "native"
build: "native"
palette_roles: {"paper": "bg", "ink": "ink", "icon": "accent", "icon2": "accent2", "row": "surface", "rule": "line", "note": "dim"}
---

## Look
- Field: warm flat paper (`bg`). Rows sit on thin `line` rules. No gradients, no shadows.
- Icons: one simple solid silhouette per topic (person, house, coin, box). Same size, same spacing, one colour per row: `accent` or `accent2`. Half a unit is a half-cut icon.
- Rule of ISOTYPE: more is more icons, never a bigger icon. One icon stands for one fixed number, for example 1 icon = 10 people.
- Type: `head` bold 40–56 px for the row label and the big number, `mono` 14–16 px for the key ("1 icon = 10"). Left aligned, in a column at the left.

## Behaviour
- Entrances: icons appear one by one left to right in each row, 70 ms stagger, 220 ms each, `P.spring` `snap`, scale from 0.6 to 1. Rows start 300 ms after each other, top to bottom.
- Text: the row label slides 16 px from the left, 280 ms, `P.ease.enter`. The count number ticks up in step with the icons.
- Transitions: to compare, the rows clear to the left with a 40 ms stagger, 260 ms, `P.ease.accelExit`. New rows enter from the right.
- Camera: locked. At most a 1.0 to 1.06 push in on the winning row, 600 ms, `P.ease.softLand`.
- Pacing: 1 row group per beat, 3–5 s holds, about 12–15 changes per minute. Hold 1.2 s after the last icon lands.
- Ambient: none. The winning row icons may nod 4 px up in turn, 1.6 s loop, `P.ease.linear`.
- Sound: a light wood tick for each icon, a soft chime for the final count.

## Do
- Keep at most 4 rows and 12 icons per row.
- Show the key on screen in every frame with icons.
- Use the same icon shape for the same topic in all frames.
- Say the total number in the voice and in a big number.

## Don't
- No scaled icons to show size. No 3D icons.
- No pie charts, no axes with ticks.
- No detailed or outlined icons. Silhouettes only.
- No more than two row colours.

## Build notes
Define each icon once as an SVG `<symbol>` and `<use>` it in a CSS grid. A half icon uses a `clip-path` of 50% width. Stagger with `P.prog` per index. In tall, make rows 6 icons wide and stack them.
