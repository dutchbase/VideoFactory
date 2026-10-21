---
id: "donut-chart"
title: "Donut chart"
description: "A multi-segment donut whose slices sweep on clockwise one after another while the total counts in the hole and a legend lists each part; use it to show how a whole splits."
tags: ["donut", "pie", "chart", "segments", "share", "legend", "data", "total", "split"]
kind: "fx"
engine: "both"
status: "approved"
files: ["donut-chart.js", "donut-chart.css"]
depends: ["core"]
api: ["FX.donutChart(H, el, {at, dur = 1.8, segments: [{label, value, color?}] (4 sample parts), totalLabel = '', unit = '', decimals = 0, size = 520, thickness = 64, gap = 8, width = 1200, trackColor: 'line'}): builds the ring and the legend inside el; the sweep runs `dur` seconds from `at`", "returns {el, root, total, legend}"]
preview_at: 1.5
source: {"site": "remotionui", "name": "donut-chart", "repo": "https://github.com/riaz37/remotion-ui", "sha": "b7e0e6becc3d22b8b03dfef72c064f72ff9fad1f", "file": "apps/web/registry/bases/default/primitives/donut-chart.tsx", "license": "MIT"}
---

# donut-chart

One sweep runs clockwise from 12 o'clock; each segment fills as the sweep passes it, and its legend row and value count in at the same time. Segment colours are brand role names (`color: 'green'`); without one the order is accent, green, ink, dim. The total (96 px) sits in the hole and the legend (44 px names, 52 px values) sits beside the ring, so no label depends on the arc. All numbers are set from the time and rounded to `decimals`. Keep to 2 to 5 segments.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.donutChart(H, document.querySelector('#split'), { at: H.at('split+0.2'),
  segments: [{ label: 'Design', value: 420 }, { label: 'Build', value: 310 }, { label: 'Test', value: 180 }] });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.donutChart(H, document.querySelector('#split'), { at: cue('split') + 0.2, totalLabel: 'Total',
  segments: [{ label: 'Design', value: 420 }, { label: 'Build', value: 310, color: 'green' }] });
```

Rewritten for VideoFactory from RemotionUI `DonutChart` (MIT). No upstream code is copied.
