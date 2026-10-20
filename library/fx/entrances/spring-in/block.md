---
id: "spring-in"
title: "Spring in"
description: "An element scales up a little and rises into place on a spring, with snappy, smooth and bouncy presets; use it for a card, a label or any block that arrives."
tags: ["spring", "entrance", "scale", "rise", "snappy", "bouncy", "smooth", "card", "pop in"]
kind: "fx"
engine: "both"
status: "draft"
files: ["spring-in.js", "spring-in.css"]
depends: ["core"]
api: ["FX.springIn(H, el, {at, config: 'snappy'|'smooth'|'bouncy' = 'snappy', from = 0.88, travel = 24, direction: 'up'|'down'|'left'|'right' = 'up', origin = '50% 50%', dur = by preset, bounce = by preset}): el appears at `at`", "returns {el, at, dur}"]
preview_at: 1.5
source: {"site": "remotionui", "name": "spring-in", "repo": "https://github.com/riaz37/remotion-ui", "sha": "b7e0e6becc3d22b8b03dfef72c064f72ff9fad1f", "file": "apps/web/registry/bases/default/primitives/spring-in.tsx", "license": "MIT"}
---

# spring-in

Scale (from `from` to 1), a short travel of `travel` px and a fade run together on one spring. `snappy` settles in 0.4 s with a small overshoot, `smooth` in 0.65 s with none, `bouncy` in 0.8 s with a clear overshoot (keep it for a playful moment). `direction` names the side the element comes from. `dur` and `bounce` override the preset.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.springIn(H, document.querySelector('#card'), { at: H.at('hook+0.2'), config: 'smooth' });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.springIn(H, document.querySelector('#card'), { at: cue('hook') + 0.2, config: 'bouncy', from: 0.7 });
```

Rewritten for VideoFactory from RemotionUI `SpringIn` (MIT). No upstream code is copied.
