---
id: "transit-map"
axis: "visual"
title: "Transit map"
summary: "Process shown as a metro map: thick coloured lines at 45 and 90 degrees, round station dots and clear labels."
aliases: ["metro map", "subway diagram", "Beck map"]
sources: ["https://www.creatoros.ca/blog/motion-style-atlas/", "https://explain.film/explainer-video-styles", "https://en.wikipedia.org/wiki/Harry_Beck"]
best_for: ["timeline", "tutorial", "explain-mechanism", "explainer", "course"]
formats: ["wide", "tall"]
pairs_with: {"editing": "canvas-pan", "content": "timeline"}
preview: "native"
build: "native"
palette_roles: {"paper": "bg", "ink": "ink", "line1": "accent", "line2": "accent2", "line3": "green", "line4": "r4", "station": "surface", "label": "dim", "rule": "line"}
---

## Look
- Field: flat light or dark paper (`bg`). No texture, no shadow, no gradient.
- Lines: 14–18 px thick, round caps, only horizontal, vertical and 45° runs with rounded corners (radius 40 px). Each line has one colour: `accent`, `accent2`, `green`, `r4`.
- Stations: white-fill dots with a 6 px ink ring. An interchange is a larger ring that two lines share. The current station is filled with `accent`.
- Type: `head` bold 30–40 px for station names, set horizontal or at 45°. A `mono` small caps legend (14–16 px) lists the lines. One title in `head` 72–96 px, top left.

## Behaviour
- Entrances: a line draws from its start station to the end with a stroke-dash reveal, 900 ms, `P.ease.move`. A station dot pops in 120 ms after the line passes it, 240 ms, `P.spring` `pop`.
- Text: a station label fades and slides 12 px from its side, 260 ms, `P.ease.enter`. Labels follow the line draw, 90 ms stagger.
- Transitions: the camera follows the active line to the next station (see camera). A line that is done dims to 35% opacity in 300 ms, `P.ease.exit`.
- Camera: slow pan and 1.0 to 1.15 zoom that keeps the current station at the frame centre. Moves take 700 ms with `P.ease.move`. No rotation.
- Pacing: one station per beat, 2–3.5 s hold, about 18 changes per minute. Hold 1 s on the full map at the end.
- Ambient: a small marker dot travels along the active line at 120 px per second, `P.ease.linear`, in a loop.
- Sound: a soft rail "ding" on each station, a low whoosh on each line draw.

## Do
- Keep at most 4 lines and 10 stations on screen.
- Use one line colour for one topic every time.
- Name every station with 1–3 words.
- Keep the map readable at phone size: labels at least 28 px.

## Don't
- No curves other than corner rounding. No diagonal angles other than 45°.
- No map of real places or real transit logos.
- No bounce on lines. Only dots may pop.
- No label that crosses a line.

## Build notes
Inline SVG paths with `stroke-linecap: round` and `stroke-dasharray` driven by `P.prog`. Compute path length once. Put the whole map in one `<g>` and move that group for the camera. Works in tall: lay the main line vertically and put labels to the right.
