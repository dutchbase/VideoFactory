---
id: "motion-trail"
title: "Motion trail"
description: "An element flies in from the side and leaves a trail of fading, blurred echoes behind it; use it for a fast, energetic arrival."
tags: ["trail", "echo", "motion blur", "fly in", "entrance", "speed", "ghost", "slide", "afterimage"]
kind: "fx"
engine: "both"
status: "approved"
files: ["motion-trail.js", "motion-trail.css"]
depends: ["core"]
api: ["FX.motionTrail(H, el, {at, dur = 0.9, x = -520, y = 0, count = 5, gap = 0.06, opacity = 0.45, falloff = 1.6, scale = 0.82, blur = 4, ease = 'power3.out', color: null}): el flies in from (x, y) px away at `at`", "returns {el, echoes, end}"]
preview_at: 1.5
source: {"site": "remotionui", "name": "motion-trail", "repo": "https://github.com/riaz37/remotion-ui", "sha": "b7e0e6becc3d22b8b03dfef72c064f72ff9fad1f", "file": "apps/web/registry/bases/default/primitives/motion-trail.tsx", "license": "MIT"}
---

# motion-trail

`el` moves from `x`, `y` px away to its own place. `count` copies of it follow the same move, each `gap` seconds later, smaller (`scale`), blurrier (`blur`) and fainter (`opacity`, `falloff`) the older they are. The copies are placed behind `el` and fade out as the move ends. `el` needs a position and a size in its parent (for example absolute). `color` is an optional brand colour role for the text of the copies.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.motionTrail(H, document.querySelector('#card'), { at: H.at('hook+0.2'), x: -900 });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.motionTrail(H, document.querySelector('#card'), { at: cue('hook') + 0.2, x: 900, count: 6 });
```

Rewritten for VideoFactory from RemotionUI `MotionTrail` (MIT). No upstream code is copied.
