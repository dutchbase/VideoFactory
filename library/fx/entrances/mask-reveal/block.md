---
id: "mask-reveal"
title: "Mask reveal"
description: "Text is uncovered by a mask that slides away with a hard, sharp edge and no fade; use it for a title that should arrive with authority."
tags: ["mask", "reveal", "wipe", "clip", "entrance", "text", "title", "hard edge", "uncover"]
kind: "fx"
engine: "both"
status: "draft"
files: ["mask-reveal.js", "mask-reveal.css"]
depends: ["core"]
api: ["FX.maskReveal(H, el, {at, dur = 0.7, direction: 'left'|'right'|'top'|'bottom' = 'left'}): el is uncovered from `at`", "returns {el, at, dur}"]
preview_at: 1.5
source: {"site": "onda", "name": "mask-reveal", "repo": "https://github.com/degueba/onda", "sha": "3c814051269597b31fee1603bef7ccfb93d091b6", "file": "registry/components/mask-reveal/MaskReveal.tsx", "license": "MIT"}
---

# mask-reveal

A `clip-path` inset on `el` shrinks from fully covered to fully open on a calm spring. There is no opacity fade: the moving edge is the effect. `direction` names the side the text comes in from. The element is clipped by 10% less than its box on the open sides, so glyph tails stay whole.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.maskReveal(H, document.querySelector('#title'), { at: H.at('hook+0.2'), direction: 'bottom' });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.maskReveal(H, document.querySelector('#title'), { at: cue('hook') + 0.2, direction: 'left' });
```

Rewritten for VideoFactory from Onda `MaskReveal` (MIT). No upstream code is copied.
