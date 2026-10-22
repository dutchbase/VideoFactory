---
id: "graphpaper"
axis: "visual"
title: "Graphpaper"
summary: "Dot-grid paper with ink strokes, hard offset shadows, one blue accent and a highlighter mark on the headline."
aliases: ["dot grid notebook", "tutorial paper", "docs style"]
sources: ["https://ideatomotion.com/looks", "https://www.creatoros.ca/blog/motion-style-atlas/"]
best_for: ["tutorial", "explain-mechanism", "onboarding", "course"]
formats: ["wide", "tall"]
pairs_with: {"editing": "stepped-boil", "content": "tutorial"}
preview: "native"
build: "native"
palette_roles: {"paper": "bg", "ink": "ink", "dots": "line", "accent": "accent", "highlighter": "r4", "card": "surface"}
---

## Look
- Field: light `bg` with a dot grid in `line` (2 px dots, 28 px apart).
- Cards: `surface` boxes with a 2-3 px `ink` border and a hard shadow offset 8 px down-right in `ink` (no blur).
- Accent: `accent` for strokes, arrows and checkmarks. A highlighter bar in `r4` (at 70%) sits behind the key words of the headline.
- Type: `head` font 54-72 px for headlines, `mono` 16-20 px for step numbers and code-like labels. Arrows are hand-drawn style with a round cap.

## Behaviour
- Entrances: the highlighter wipes left to right behind the headline in 360 ms (`P.ease.softLand`) after the text lands. Cards drop in from 24 px above with `P.ease.softLand` (400 ms) and their shadow snaps on 80 ms later.
- Strokes: arrows and underlines draw along their path in 400-600 ms, `P.ease.linear`.
- Steps: numbered cards arrive one per beat, 0.8-1.2 s apart. A check mark scales in with `P.spring` snap when the step is done.
- Camera: locked. Transitions: the page flips up 40 px and fades (500 ms, `P.ease.move`) or cards slide off the right edge in 240 ms (`P.ease.accelExit`).
- Pacing: 3-5 s holds, about 12-16 changes per minute.
- Ambient: none. Sound: pencil scratch on strokes, soft paper tap per card.

## Do
- Build the diagram piece by piece in teaching order.
- Highlight only the one phrase that matters.
- Keep shadows hard and the same direction.

## Don't
- No blurred or soft shadows.
- No gradients or glass.
- No more than one highlighter bar on screen.
- No more than one accent colour besides `ink`.

## Build notes
Native: CSS borders and `box-shadow: 8px 8px 0 var(--ink)`, `radial-gradient` dots, SVG for arrows with `stroke-dasharray`. Highlighter is a `clip-path` or scaleX bar behind text. Tall format: one card per screen.
