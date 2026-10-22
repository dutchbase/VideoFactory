---
id: "timeline"
axis: "content"
title: "Timeline"
summary: "Shows how something changed over time along one line, with a few key dates."
aliases: ["history", "evolution", "roadmap", "journey"]
sources: ["https://yansmedia.com/blog/explainer-video-structure", "https://adwave.com/resources/explainer-video-styles", "https://pexo.ai/blog/types-of-explainer-videos-0995"]
best_for: ["explainer", "course", "founder story"]
formats: ["wide", "tall"]
pairs_with: ["transit-map", "archival-documentary", "swiss-modernist", "data-journalism", "mid-century-cartoon", "blueprint", "isotype-pictograms", "minimalist-premium"]
preview: "native"
build: "native"
---

## Look
Shows how something changed over time along one line, with a few key dates. One line crosses the frame with dated dots.

## Behaviour
- Structure (percent of runtime): 1) hook: the start and the end state, one line 0–10%, 2) the line draws, with 4–7 milestones 10–82%, 3) turning point gets the longest hold 50–70%, 4) what it means now / what comes next 82–95%, 5) recap and call to action 95–100%.
- The line draws left to right (wide) or top to bottom (tall) on `P.ease.linear` at a steady pace, tied to the voice, never faster than the words. Camera follows the line head by `canvas-pan` style moves of 1.6–2.4 s (`P.ease.move`).
- Each milestone: dot pops on the line (`P.spring` pop, 400 ms) on the date word; year in mono text enters (`P.ease.enter`, 350 ms); label card slides 24 px from the line (`P.ease.softLand`, 400 ms).
- Past milestones stay at 60%. The current one is at 100% with the accent ring.
- Milestone length: 6–12 s. Changes per minute: 6–10. Wide 60–180 s, tall 30–60 s with maximum 5 milestones.
- Equal time spacing on screen unless the gaps matter; then scale the gap and say so. Sound: soft tick at each dot.

## Do
- Show the year or step number on every milestone.
- Keep milestones to 4–7.
- End on the full line plus the present.

## Don't
- No milestone without a date or order.
- No uneven spacing with no reason.
- No side story between two dots.

## Build notes
Stage 03 cues: line progress (one long prog), dot, year, label per milestone. Line is an SVG path with dash offset. Camera is a translate on the scene root.
