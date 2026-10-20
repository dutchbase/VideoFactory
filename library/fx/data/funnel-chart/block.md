---
id: "funnel-chart"
title: "Funnel chart"
description: "Stage bands wipe in from the top and narrow toward the bottom, with counting numbers and the drop-off percent between bands; use it for a conversion or a step-by-step loss."
tags: ["funnel", "chart", "stages", "conversion", "drop-off", "data", "pipeline", "steps", "narrowing"]
kind: "fx"
engine: "both"
status: "draft"
files: ["funnel-chart.js", "funnel-chart.css"]
depends: ["core"]
api: ["FX.funnelChart(H, el, {at, dur = 0.8, stages: [{label, value}] (4 sample stages), stagger = 0.45, unit = '', decimals = 0, showDropoff = true, tailOpacity = 0.45, width = 1600, bandHeight = 120, gap = 64, labelWidth = 560, color: 'accent', dropColor: 'accent'}): builds the funnel inside el; band i wipes over `dur` seconds, starting `i * stagger` after `at`", "returns {el, root, items}"]
preview_at: 1.5
source: {"site": "remotionui", "name": "funnel-chart", "repo": "https://github.com/riaz37/remotion-ui", "sha": "b7e0e6becc3d22b8b03dfef72c064f72ff9fad1f", "file": "apps/web/registry/bases/default/primitives/funnel-chart.tsx", "license": "MIT"}
---

# funnel-chart

Each band is a trapezoid from its own width down to the width of the next stage, so the taper shows the loss. The last band is a rectangle. Widths follow the values (the first stage is full width). Names (36 px) and numbers (64 px) sit in a left column on the ground; the drop-off percent (36 px) sits in the gap between two bands. No label lies on a band. Bands fade from full `color` to `tailOpacity`. The height of `el` content is `stages * bandHeight + (stages - 1) * gap`; use 3 to 5 stages. Numbers are set from the time and rounded to `decimals`.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.funnelChart(H, document.querySelector('#funnel'), { at: H.at('loss+0.2'),
  stages: [{ label: 'Visits', value: 12000 }, { label: 'Signups', value: 4800 }, { label: 'Customers', value: 640 }] });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.funnelChart(H, document.querySelector('#funnel'), { at: cue('loss') + 0.2, stagger: 0.6,
  stages: [{ label: 'Visits', value: 12000 }, { label: 'Customers', value: 640 }] });
```

Rewritten for VideoFactory from RemotionUI `FunnelChart` (MIT). No upstream code is copied.
