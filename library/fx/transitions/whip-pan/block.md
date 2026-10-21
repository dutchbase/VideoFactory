---
id: "whip-pan"
title: "Whip pan"
description: "Both full-frame shots slide along one axis in about eight frames with a motion blur that follows the speed; use it to move between two parts of one screen or two screens on one ground (cut K7)."
tags: ["transition", "whip", "pan", "slide", "motion blur", "cut", "scene", "fast", "camera"]
kind: "fx"
engine: "both"
status: "approved"
files: ["whip-pan.js", "whip-pan.css"]
depends: ["core"]
api: ["FX.whipPan(H, from, to, {at, dur = 8/30, dir = 'left'|'right'|'up'|'down', blur = 20, punch = 2.2, travel = 1}): from is shot A, to is shot B, both full-frame on one stage; the pan runs from `at` to `at + dur`", "dir is the way the content moves (left = B arrives from the right); blur is the peak blur in px at the fastest point; punch (1-4) is how hard the move is squeezed into a few frames; travel is the share of the frame each shot moves (1 = edge to edge)", "returns {end}"]
preview_at: 1.5
source: {"site": "remotionui", "name": "transition-whip-pan", "repo": "https://github.com/riaz37/remotion-ui", "sha": "b7e0e6becc3d22b8b03dfef72c064f72ff9fad1f", "file": "apps/web/registry/bases/default/primitives/transition-whip-pan.tsx", "license": "MIT"}
---

# whip-pan

Cut K7 (`_shared/transitions.md`): A leaves and B arrives inside one fast move of about 8 frames at 30 fps. The speed peaks early (the move is mostly done in its first half), and a CSS blur (`blur` px at the peak, 0 at both ends) follows the speed, so B lands sharp. Never use it on text that must be read mid-move. For a whole-frame change with no camera feel, use a K5 cut instead.

The part sets the visibility of both shots: B is hidden before `at`, A is hidden after `at + dur`. Give the shots no `data-cue`. Both shots must be full-frame, positioned elements in the same parent, A first; the part sets `x`, `y` and `filter` on them with GSAP and inline `z-index` 1 and 2. Keep one object the same size on both sides of the cut as the anchor. Put the stage in `overflow: hidden`.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.whipPan(H, document.querySelector('.shot-a'), document.querySelector('.shot-b'), { at: H.at('point-0.15'), dir: 'left' });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.whipPan(H, document.querySelector('.shot-a'), document.querySelector('.shot-b'), { at: cue('point') - 0.15, dir: 'up', blur: 28 });
```

Rewritten for VideoFactory from RemotionUI `TransitionWhipPan` (MIT). No upstream code is copied.
