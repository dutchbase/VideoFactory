---
id: "wipe"
title: "Wipe"
description: "A soft-edged wipe from one full-frame shot to the next, painted in the next shot's ground colour; use it between two busy scenes (cut K5)."
tags: ["transition", "wipe", "cut", "scene", "edge", "directional", "reveal", "soft", "ground"]
kind: "fx"
engine: "both"
status: "approved"
files: ["wipe.js", "wipe.css"]
depends: ["core"]
api: ["FX.wipe(H, from, to, {at, dur = 0.58, dir = 'right'|'left'|'up'|'down', soft = 0.36, lag = 0.28, ground = null|role|false}): from is shot A, to is shot B, both full-frame on one stage; the wipe runs from `at` to `at + dur`", "dir is the way the edge travels; soft is the soft edge as a share of the axis (K5: 0.31-0.42); ground is a colour role for the strip (default: the background B already has, false = no strip); lag is how far B trails the strip (share of dur)", "returns {panel, end}: the strip element and the end time"]
preview_at: 1.5
twins: ["remotionui/transition-wipe", "remotionui/directional-wipe"]
source: {"site": "onda", "name": "wipe", "repo": "https://github.com/degueba/onda", "sha": "3c814051269597b31fee1603bef7ccfb93d091b6", "file": "registry/transitions/wipe/wipe.tsx", "license": "MIT"}
---

# wipe

Cut K5 (`_shared/transitions.md`): a wipe that starts in shot A and ends in shot B. A strip in B's ground colour crosses A with a soft edge (0.36 of the axis); B follows behind it, so A's content never mixes with B's. Length 0.58 s. Start it 0.1-0.2 s before the voice phrase ends; start B's hero 0.1 s before `at + dur`.

The part sets the visibility of both shots: B is hidden before `at`, A is hidden after `at + dur`. Give the shots no `data-cue`. Both shots must be full-frame, positioned elements in the same parent, A first. The part sets inline `z-index` 1, 2 and 3 on A, the strip and B.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.wipe(H, document.querySelector('.shot-a'), document.querySelector('.shot-b'), { at: H.at('point-0.2'), dir: 'right' });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.wipe(H, document.querySelector('.shot-a'), document.querySelector('.shot-b'), { at: cue('point') - 0.2, ground: 'cream' });
```

Rewritten for VideoFactory from Onda `wipe` (MIT). No upstream code is copied.
