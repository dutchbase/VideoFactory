---
id: "blinds"
title: "Blinds"
description: "Slats open one after the other, each sweeping sideways or down, and show the next full-frame shot; use it for a rhythmic, graphic scene change (cut K5 variant)."
tags: ["transition", "blinds", "slats", "stripes", "reveal", "cut", "scene", "stagger", "mask"]
kind: "fx"
engine: "both"
status: "draft"
files: ["blinds.js", "blinds.css"]
depends: ["core"]
api: ["FX.blinds(H, from, to, {at, dur = 0.6, slats = 8, orientation = 'horizontal'|'vertical', stagger = 0.5, alternate = false, soft = 0.12}): from is shot A, to is shot B, both full-frame on one stage; the slats open from `at` to `at + dur`", "slats is 2-48; horizontal slats stack top to bottom and sweep sideways, vertical slats stand side by side and sweep down; stagger is the share of dur that the start of the last slat is late; alternate turns every second slat the other way; soft is the soft edge as a share of the sweep", "returns {end, slats}"]
preview_at: 1.5
source: {"site": "remotionui", "name": "transition-blinds", "repo": "https://github.com/riaz37/remotion-ui", "sha": "b7e0e6becc3d22b8b03dfef72c064f72ff9fad1f", "file": "apps/web/registry/bases/default/primitives/transition-blinds.tsx", "license": "MIT"}
---

# blinds

A K5 cut (`_shared/transitions.md`) made of slats: each slat of shot B opens with a soft edge, and the slats start one after the other (`stagger`). Every slat ends together at `at + dur`, so no stripe stays. Above about 24 slats it stops reading as slats at 1080p. Length 0.6 s; start it 0.1-0.2 s before the voice phrase ends.

The part sets the visibility of both shots: B is hidden before `at`, A is hidden after `at + dur`. Give the shots no `data-cue`. Both shots must be full-frame, positioned elements in the same parent, A first. The part sets inline `z-index` 1 and 2 on A and B. The slats show B itself, so B's own ground shows first.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.blinds(H, document.querySelector('.shot-a'), document.querySelector('.shot-b'), { at: H.at('point-0.2'), slats: 10 });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.blinds(H, document.querySelector('.shot-a'), document.querySelector('.shot-b'), { at: cue('point') - 0.2, orientation: 'vertical', alternate: true });
```

Rewritten for VideoFactory from RemotionUI `TransitionBlinds` (MIT). No upstream code is copied.
