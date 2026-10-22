---
id: "data-story"
axis: "content"
title: "Data story"
summary: "Takes one dataset and leads the viewer to one clear finding."
aliases: ["data viz story", "chart story", "numbers story"]
sources: ["https://yansmedia.com/blog/explainer-video-structure", "https://fliki.ai/blog/explainer-video-script-template", "https://adwave.com/resources/explainer-video-styles"]
best_for: ["explainer", "short", "course"]
formats: ["wide", "tall"]
pairs_with: ["data-journalism", "swiss-modernist", "newsdesk", "nightlab", "graphpaper", "minimalist-premium", "isotype-pictograms", "tech-glow"]
preview: "native"
build: "native"
---

## Look
Takes one dataset and leads the viewer to one clear finding. One clean chart, one highlighted point, one sentence title.

## Behaviour
- Structure (percent of runtime): 1) hook: the finding as a question or number 0–10%, 2) context: what is measured, source, period 10–22%, 3) build the chart in layers: axes, then one series, then the comparison 22–65%, 4) the finding: highlight the one point, 65–85%, 5) so what, and caveat 85–100%.
- Axes draw first (`P.ease.linear`, 600 ms). The data line or bars draw on the voice word, bars grow from baseline (`P.ease.softLand`, 600 ms, 40–60 ms stagger).
- Grey out everything except the series that matters (to 35%); the key point gets the accent, a ring (`P.spring` pop) and a number count-up (900 ms).
- One chart per scene. One message per chart. Annotation enters 0.4 s after the highlight and stays.
- Scene length: 10–20 s. Changes per minute: 6–9. Wide 45–120 s, tall 20–45 s with one chart.
- Sound: quiet; one low tone under the count-up, a tick at the finding.

## Do
- Write the finding as a sentence in the chart title.
- Show source and period in small text.
- Start the y axis at zero for bars.

## Don't
- No dual axes.
- No more than three series.
- No chart that the voice does not explain.

## Build notes
Stage 03 cues: axes, series, highlight, annotation. Use the Modern kit chart helpers or plain SVG. Number count-up is a prog on the text.
