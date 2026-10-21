---
id: "camera-shake"
title: "Camera shake"
description: "One short shake of the whole scene that fades to rest by itself; use it for an impact, a hit or a slam, not as idle motion."
tags: ["camera", "shake", "impact", "hit", "slam", "rumble", "shock", "handheld", "cinematic", "seeded"]
kind: "fx"
engine: "both"
status: "approved"
files: ["camera-shake.js", "camera-shake.css"]
depends: ["core"]
api: ["FX.cameraShake(H, el, {at, dur = 0.6, intensity = 14, rotate = 0.5, rate = 20, decay = 2, seed = 1}): el shakes from `at` for `dur` seconds and then sits still", "returns {el, at, end}"]
preview_at: 1.5
source: {"site": "onda", "name": "camera-shake", "repo": "https://github.com/degueba/onda", "sha": "3c814051269597b31fee1603bef7ccfb93d091b6", "file": "registry/components/camera-shake/CameraShake.tsx", "license": "MIT"}
---

# camera-shake

Pass one element that holds the scene (a wrapper div around everything that should shake, with no other transform tween of its own). The offset comes from seeded smooth noise: the same `seed` always gives the same shake, also when you seek back. `intensity` is the largest move in stage px, `rotate` the largest turn in degrees, `rate` how fast it jitters. `decay` shapes the fade: 1 is linear, 2 (default) fades faster. The shake starts with a hit and ends at exactly zero; before and after it the element has no transform. Use it once per impact.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.cameraShake(H, document.getElementById('world'), { at: H.at('slam'), dur: 0.6, intensity: 18 });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.cameraShake(H, document.querySelector('.world'), { at: cue('slam'), seed: 4 });
```

Rewritten for VideoFactory from Onda `CameraShake` (MIT). No upstream code is copied.
