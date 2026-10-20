---
id: "sparkline-row"
title: "Sparkline row"
description: "A stack of rows, each with a label, a small trend line that draws on, a counting headline value and a change figure; use it for a quick read of several metrics at once."
tags: ["sparkline", "trend", "metrics", "kpi", "row", "chart", "dashboard", "data", "delta"]
kind: "fx"
engine: "both"
status: "draft"
files: ["sparkline-row.js", "sparkline-row.css"]
depends: ["core"]
api: ["FX.sparklineRow(H, el, {at, dur = 1.2, rows: [{label, values: [numbers], value?, delta?, unit?, color?}] (3 sample rows), stagger = 0.35, unit = '', decimals = 0, showArea = true, width = 1600, rowHeight = 150, sparkWidth = 560, labelWidth = 340, deltaWidth = 200, color: 'accent', upColor: 'green', downColor: 'accent'}): builds the rows inside el; each line draws over `dur` seconds, row i starts `i * stagger` after `at`", "returns {el, root, rows}"]
preview_at: 1.5
source: {"site": "remotionui", "name": "sparkline-row", "repo": "https://github.com/riaz37/remotion-ui", "sha": "b7e0e6becc3d22b8b03dfef72c064f72ff9fad1f", "file": "apps/web/registry/bases/default/primitives/sparkline-row.tsx", "license": "MIT"}
---

# sparkline-row

Each row has its label (44 px), a trend line with a soft area and a round tip that follows the head of the line, a headline value (72 px) and a change figure (44 px). Label, value and change sit in their own columns on the ground, so they stay readable while a line draws. The headline counts up to `value` (default: the last point of `values`); it is set from the time and rounded to `decimals`. The change is green, or `downColor` when the text starts with a minus. Each line scales to its own range. Use 2 to 5 rows.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.sparklineRow(H, document.querySelector('#metrics'), { at: H.at('kpi+0.2'),
  rows: [{ label: 'Visits', values: [12, 14, 13, 18, 22], delta: '+18%' }, { label: 'Signups', values: [8, 9, 12, 10, 14], delta: '+12%' }] });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.sparklineRow(H, document.querySelector('#metrics'), { at: cue('kpi') + 0.2, unit: 'k',
  rows: [{ label: 'Visits', values: [12, 14, 13, 18, 22], delta: '+18%' }] });
```

Rewritten for VideoFactory from RemotionUI `SparklineRow` (MIT). No upstream code is copied.
