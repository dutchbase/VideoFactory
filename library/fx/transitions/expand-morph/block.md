---
id: "expand-morph"
title: "Expand morph"
description: "A rounded card of the next shot grows from a small origin rect to the full frame while the old shot leans back; use it when a box, input or list becomes its result (cut K3)."
tags: ["transition", "expand", "morph", "card", "container", "cut", "scene", "shared element", "modal"]
kind: "fx"
engine: "both"
status: "draft"
files: ["expand-morph.js", "expand-morph.css"]
depends: ["core"]
api: ["FX.expandMorph(H, from, to, {at, lead = 0.14, dur = 0.8, shrink = 0.09, origin = [0.36, 0.34, 0.28, 0.32], radius = 28}): from is shot A, to is shot B, both full-frame on one stage; A leans back from `at`, the card starts at `at + lead` and is full at `at + lead + dur`", "lead is the length of A's anticipation in s; shrink is how much A shrinks (K3: about 0.09); origin is the start rect of the card as [x, y, width, height] shares of the frame; radius is the corner radius in px at the start (it goes to 0)", "returns {shadow, cut, end}: the shadow element, the time the card starts and the end time"]
preview_at: 1.5
source: {"site": "onda", "name": "expand-morph", "repo": "https://github.com/degueba/onda", "sha": "3c814051269597b31fee1603bef7ccfb93d091b6", "file": "registry/transitions/expand-morph/expandMorph.tsx", "license": "MIT"}
---

# expand-morph

Cut K3 (`_shared/transitions.md`). A shrinks about 9 % over 0.14 s with the biggest step last. Then a card with shot B inside replaces the container at the `origin` rect, and grows to the full frame in 0.8 s on one calm curve (position, size and corner radius together, no overshoot). B keeps its shape inside the card and scales with it, so it reads as one thing growing. Put `origin` over the box in A that becomes the result.

The part sets the visibility of both shots. Give the shots no `data-cue`. Both shots must be full-frame, positioned elements in the same parent, A first. The part sets `scale`, `x`, `y` and `clip-path` on B with GSAP, adds a shadow element, and sets inline `z-index` 1, 2 and 3 on A, the shadow and B. Start B's hero at `cut`.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.expandMorph(H, document.querySelector('.shot-a'), document.querySelector('.shot-b'), { at: H.at('result-0.14'), origin: [0.3, 0.4, 0.4, 0.2] });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.expandMorph(H, document.querySelector('.shot-a'), document.querySelector('.shot-b'), { at: cue('result') - 0.14, radius: 40 });
```

Rewritten for VideoFactory from Onda `ExpandMorph` (MIT). No upstream code is copied.
