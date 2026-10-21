---
id: "comparison-bars"
title: "Comparison bars"
description: "Rows of two bars, a muted before and a coloured after, that grow in turn with counting numbers and a change chip; use it for a before/after or old/new comparison."
tags: ["bars", "comparison", "before", "after", "delta", "chart", "data", "change", "versus"]
kind: "fx"
engine: "both"
status: "approved"
files: ["comparison-bars.js", "comparison-bars.css"]
depends: ["core"]
api: ["FX.comparisonBars(H, el, {at, dur = 1.0, rows: [{label, before, after, delta?}] (3 sample rows), seriesLabels = ['Before', 'After'], stagger = 0.3, pairOffset = 0.18, unit = '', decimals = 0, showDelta = true, width = 1600, barHeight = 44, rowGap = 54, labelWidth = 340, valueWidth = 190, deltaWidth = 220, beforeColor: 'dim', afterColor: 'accent', upColor: 'green', downColor: 'accent'}): builds the legend and rows inside el; each bar grows over `dur` seconds, row i starts `i * stagger` after `at`", "returns {el, root, rows}"]
preview_at: 1.5
source: {"site": "remotionui", "name": "comparison-bars", "repo": "https://github.com/riaz37/remotion-ui", "sha": "b7e0e6becc3d22b8b03dfef72c064f72ff9fad1f", "file": "apps/web/registry/bases/default/primitives/comparison-bars.tsx", "license": "MIT"}
---

# comparison-bars

All bars share one scale (the largest value). Each row has its label (44 px) on the left, two bars, a column with the two numbers (36 px) and a change chip (56 px), all on the ground, so no label depends on a bar reaching it. The "after" bar trails the "before" bar by `pairOffset`; the chip fades in after both end. The chip is the percent change, or your own `delta` text; it is `upColor` when the value rose and `downColor` when it fell. Numbers are set from the time and rounded to `decimals`. Use 2 to 5 rows.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.comparisonBars(H, document.querySelector('#compare'), { at: H.at('result+0.2'),
  rows: [{ label: 'Speed', before: 40, after: 68 }, { label: 'Cost', before: 90, after: 60 }] });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.comparisonBars(H, document.querySelector('#compare'), { at: cue('result') + 0.2, seriesLabels: ['2024', '2025'],
  rows: [{ label: 'Speed', before: 40, after: 68 }] });
```

Rewritten for VideoFactory from RemotionUI `ComparisonBars` (MIT). No upstream code is copied.
