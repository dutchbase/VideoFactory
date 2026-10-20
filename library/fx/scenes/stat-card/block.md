---
id: "stat-card"
title: "Stat card"
description: "A big number counts up above its label, and an accent rule draws under both; use it for a hero stat, a milestone or a result."
tags: ["stat", "number", "count up", "kpi", "metric", "milestone", "label", "scene", "data"]
kind: "fx"
engine: "both"
status: "draft"
files: ["stat-card.js", "stat-card.css"]
depends: ["core"]
api: ["FX.statCard(H, el, {at, value = 100, label = '', prefix = '', suffix = '', decimals = 0, locale: 'en'|'nl' = 'en', separator = true, dur = 1.2, numberSize = 240, labelSize = 72, color: null, ruleColor: 'accent', rule = true}): builds the card in el, which needs a size", "returns {el, num, label, end}"]
preview_at: 1.5
twins: ["remotionui/stat-card"]
source: {"site": "onda", "name": "stat-card", "repo": "https://github.com/degueba/onda", "sha": "3c814051269597b31fee1603bef7ccfb93d091b6", "file": "registry/components/stat-card/StatCard.tsx", "license": "MIT"}
---

# stat-card

The number counts from 0 to `value` on a calm spring over `dur` seconds (the number is a function of time, so a seek always shows the same digits). The label comes in word by word a beat before the count settles, and the rule draws last. `locale: 'nl'` writes 12.480,5 instead of 12,480.5. `prefix` and `suffix` go around the number (for example `'%'`). The card is centred in `el`; any text in `el` is replaced. Keep the label short.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.statCard(H, document.querySelector('#stat'), { at: H.at('hook+0.2'), value: 1200, label: 'videos made' });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.statCard(H, document.querySelector('#stat'), { at: cue('hook') + 0.2, value: 98, suffix: '%', label: 'on time' });
```

Rewritten for VideoFactory from Onda `StatCard` (MIT). No upstream code is copied.
