---
id: "canvas-pan"
axis: "editing"
title: "Canvas pan"
summary: "One big infinite canvas; the camera pans and zooms between areas, whiteboard style."
aliases: ["infinite canvas", "prezi style", "camera over a board"]
sources: ["https://ideatomotion.com/looks", "https://www.creatoros.ca/blog/motion-style-atlas/", "https://explain.film/explainer-video-styles"]
best_for: ["timeline", "explain-mechanism", "tutorial", "explainer", "course"]
formats: ["wide", "tall"]
pairs_with: ["whiteboard", "blueprint", "graphpaper", "napkin-sketch", "sticky-note-wall"]
preview: "native"
build: "native"
---

## Look
There are no scenes. The whole story is laid out on one large board and the camera moves from area to area. Each area is a topic; the route shows the order.

## Behaviour
- Layout: the canvas is about 4x the frame width and 3x the height. Each topic is a cluster about one frame wide, placed on the reading route.
- Camera move: 1.2-2.0 s between clusters with `P.ease.move`. Longer travel needs more time (`_shared/motion.md` Durations). Zoom out 0.6x at mid-move and zoom in again at the end.
- Arrive: the camera settles with `P.ease.softLand`. Content in the new cluster draws in 150 ms after the camera stops, `P.ease.enter` 400 ms, 80 ms between items.
- Overview: once, near the end, zoom out to 0.3x with `P.ease.move` (2.4 s) to show the whole board.
- Connectors: lines draw between clusters with `P.ease.linear` at the camera speed.
- Rhythm: the move starts on the last word of the phrase and lands on the first word of the next.
- Pacing: 4-8 s per cluster, 8-14 camera moves per minute. Max 2 s of travel.
- Ambient: none. Earlier clusters stay visible at 60% opacity for context.
- Sound: a soft slide on each move, a pen tick on each draw.

## Do
- Plan the board route as a path, left to right then down.
- Keep cluster size equal.
- End on the overview.

## Don't
- No zoom beyond 2.5x.
- No diagonal moves that cross other clusters at speed.
- No cut between clusters.

## Build notes
Modern kit: put every cluster in one `.canvas` wrapper and drive its `transform: translate() scale()` with `P.track` between cluster poses. Pre-compute the poses in `scene.js`.
