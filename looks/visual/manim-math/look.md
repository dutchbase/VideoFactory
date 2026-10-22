---
id: "manim-math"
axis: "visual"
title: "Manim math"
summary: "Maths-lecture look: a dark board, thin axes, drawn curves and equations that write on and morph into each other."
aliases: ["3blue1brown style", "manim", "math animation", "equation explainer"]
sources: ["https://www.creatoros.ca/blog/motion-style-atlas/", "https://explain.film/explainer-video-styles"]
best_for: ["explain-mechanism", "data-story", "tutorial", "course", "explainer"]
formats: ["wide", "tall"]
pairs_with: {"editing": "match-cut-morph", "content": "explain-mechanism"}
preview: "native"
build: "native"
palette_roles: {"board": "bg", "curve-a": "accent", "curve-b": "accent2", "highlight": "r4", "good": "green", "axis": "dim", "grid": "line", "text": "ink"}
---

## Look
- Board: a near-black `bg`, flat and clean. A faint coordinate grid in `line` (1 px, 50% opacity) with brighter axes in `dim` and small tick marks.
- Strokes: thin vector lines (3–4 px) with round caps. Curves in `accent`, secondary curves in `accent2`, highlights in `r4`, "correct" states in `green`.
- Fills: shapes use a 20–30% tint of their stroke colour.
- Type: equations and labels in a `serif` stack after the brand font var, in `ink`, 44–72 px. Parts of an equation are tinted to match the object they describe. Plain words use the brand `font`.
- Layout: the graph or object sits at 55–65% of the frame; the equation sits top or side. Lots of empty board.

## Behaviour
- Entrances: strokes draw on along their path (stroke-dashoffset) in 800–1400 ms with `P.ease.move`. Equations write on left to right in 600–900 ms. Fills fade in 300 ms after the stroke ends.
- Transforms: one object morphs into another over 800–1000 ms with `P.ease.move`: curve to curve, term to term. Matching parts slide to their new spots instead of cutting.
- Emphasis: a highlight box or a colour flash (to `r4`, 400 ms in, 400 ms out) points at one term. A traced dot moves along a curve with `P.ease.linear` while a value counts up.
- Exits: objects un-draw in reverse in 400 ms with `P.ease.exit`, or fade 250 ms.
- Camera: the whole board pans or zooms by 1.2–2× over 1.6–2.4 s with `P.ease.move` to focus on a region; axes rescale with it.
- Ambient: none. Stillness lets the viewer read.
- Pacing: 4–8 s holds, about 8–12 changes per minute. Build one idea over several beats, never all at once.
- Sound: soft piano or ambient pad, subtle pen-stroke whispers; mostly voice.

## Do
- Colour-match the words in the voice, the terms in the equation and the part of the graph.
- Draw the object before you name it.
- Morph rather than replace.
- Keep the board mostly empty.

## Don't
- No bounce, shake or flashy transitions.
- No more than three stroke colours at once.
- No 3D shadows, glow or textures.
- No dense formulas; four terms at most.

## Build notes
Native SVG: `<path>` with stroke-dasharray for draw-on, driven by `P.prog` and `P.ease.move`; morphs by interpolating path points of equal count. Equations as styled text spans (no TeX engine needed for short formulas). Axes and grid are static SVG. Works in both formats; in tall, put the equation on top and the graph below.
