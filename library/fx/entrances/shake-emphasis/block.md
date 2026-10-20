---
id: "shake-emphasis"
title: "Shake emphasis"
description: "A short impact shake that dies away, with a small squash on the hit; use it on a word or card on the beat the voice stresses."
tags: ["shake", "impact", "emphasis", "hit", "punch", "jolt", "beat", "stress", "vibrate"]
kind: "fx"
engine: "both"
status: "draft"
files: ["shake-emphasis.js", "shake-emphasis.css"]
depends: ["core"]
api: ["FX.shakeEmphasis(H, el, {at, dur = 0.6, intensity = 14, rotation = 1.4, punch = 0.05, frequency = 22, axis: 'both'|'x'|'y' = 'both', decay = 2.2, repeat = 1, every = dur + 0.6, seed = 1}): el shakes from `at`", "returns {el, at, end}"]
preview_at: 1.5
source: {"site": "remotionui", "name": "shake-emphasis", "repo": "https://github.com/riaz37/remotion-ui", "sha": "b7e0e6becc3d22b8b03dfef72c064f72ff9fad1f", "file": "apps/web/registry/bases/default/primitives/shake-emphasis.tsx", "license": "MIT"}
---

# shake-emphasis

Smooth seeded noise moves `el` by up to `intensity` px and turns it by up to `rotation` degrees. The strength falls with `decay` over `dur` seconds. `repeat` shakes again every `every` seconds. The part writes the CSS `translate`, `rotate` and `scale` properties, so it works on an element that GSAP also moves. Use it once or twice in a video, not on every line.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.shakeEmphasis(H, document.querySelector('#word'), { at: H.at('hook+0.2') });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.shakeEmphasis(H, document.querySelector('#word'), { at: cue('hit') + 0.1, intensity: 20 });
```

Rewritten for VideoFactory from RemotionUI `ShakeEmphasis` (MIT). No upstream code is copied.
