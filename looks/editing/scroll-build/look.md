---
id: "scroll-build"
axis: "editing"
title: "Scroll and build"
summary: "Locked camera; the story scrolls up the page and charts build in place, data-journalism style."
aliases: ["scrollytelling", "scrolly", "chart build"]
sources: ["https://ideatomotion.com/looks", "https://www.creatoros.ca/blog/motion-style-atlas/", "https://explain.film/explainer-video-styles"]
best_for: ["data-story", "timeline", "compare", "explainer", "course"]
formats: ["wide", "tall"]
pairs_with: ["data-journalism", "newsdesk", "broadsheet", "swiss-modernist", "editorial-collage"]
preview: "native"
build: "native"
---

## Look
The frame is a window onto a long page. Content scrolls up at a steady pace and each chart builds as it reaches the middle of the frame. The window never zooms or cuts.

## Behaviour
- Scroll: the page moves up by one block at a time, 500-700 ms with `P.ease.move`, then holds. A continuous creep of 8 px per second with `P.ease.linear` is allowed only between blocks.
- Focus: the block in the middle band stays at 100% opacity. Blocks outside fade to 35% over 300 ms.
- Chart build: bars grow from the baseline over 600-900 ms with `P.ease.enter`, 60 ms apart. Lines draw with `P.ease.linear` at 0.3 s per x-axis step. Numbers count up 600-1200 ms.
- Text: headings rise 12 px and fade up over 400 ms with `P.ease.enter`. Body text appears whole, not by word.
- Highlight: the key bar or point turns `accent` in 160 ms. Others drop to `dim`.
- Rhythm: scroll starts 0.1 s before the voice moves to the next point; the chart finishes building on the key number.
- Pacing: 5-8 s per block, 7-12 scrolls per minute.
- Camera: locked. No cuts, no zoom.
- Sound: a soft tick for each bar, a low tone on the highlight.

## Do
- Keep one chart per block.
- Label values directly on the marks.
- Keep the scroll direction up only.

## Don't
- No camera zoom.
- No 3D or spinning charts.
- No scroll faster than 700 ms per block.

## Build notes
Modern kit: one tall `.page` div translated by `P.track`. Charts are SVG; set bar heights from `P.prog` per bar with an offset. Highlights change fill through `color-mix`.
