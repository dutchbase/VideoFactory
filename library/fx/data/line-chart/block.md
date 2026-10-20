---
id: "line-chart"
title: "Line chart"
description: "A line draws on left to right over a soft area with dots that pop as the line reaches them and the last value shown at its end; use it for one trend over time."
tags: ["line", "chart", "trend", "graph", "data", "growth", "series", "timeline", "area"]
kind: "fx"
engine: "both"
status: "draft"
files: ["line-chart.js", "line-chart.css"]
depends: ["core"]
api: ["FX.lineChart(H, el, {at, dur = 2.0, values: [numbers] (7 sample values), labels: null|[text per point], labelEvery = 1, unit = '', decimals = 0, zero = false, fill = true, showDots = true, strokeWidth = 8, width = 1500, height = 560, valueGutter = 200, color: 'accent'}): builds the chart inside el; the line draws over `dur` seconds from `at`", "returns {el, root, last}"]
preview_at: 1.5
twins: ["remotionui/line-chart-draw"]
source: {"site": "onda", "name": "line-chart", "repo": "https://github.com/degueba/onda", "sha": "3c814051269597b31fee1603bef7ccfb93d091b6", "file": "registry/components/line-chart/LineChart.tsx", "license": "MIT"}
---

# line-chart

The line and the soft area are cut at the head position each frame, so a seek always shows the same picture. The y range runs from the lowest to the highest value (`zero: true` starts at 0 or lower). Dots pop as the head reaches them; the last dot is larger. The last value (64 px) fades in at the end of the line in a gutter on the right, and the optional `labels` (32 px) sit under the chart, both on the ground. Use 3 to 12 points; with more, set `labelEvery`.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.lineChart(H, document.querySelector('#trend'), { at: H.at('growth+0.2'), values: [12, 18, 15, 24, 31], labels: ['Q1', 'Q2', 'Q3', 'Q4', 'Q5'] });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.lineChart(H, document.querySelector('#trend'), { at: cue('growth') + 0.2, values: [12, 18, 15, 24, 31], unit: 'k', color: 'green' });
```

Rewritten for VideoFactory from Onda `LineChart` (MIT). No upstream code is copied.
