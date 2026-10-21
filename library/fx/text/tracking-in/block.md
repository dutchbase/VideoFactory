---
id: "tracking-in"
title: "Tracking in"
description: "Wide letter-spacing collapses to normal while the line sharpens out of a light blur on a calm spring; use it for a title that lands."
tags: ["tracking", "letter-spacing", "text", "title", "entrance", "spring", "blur", "reveal", "snap"]
kind: "fx"
engine: "both"
status: "approved"
files: ["tracking-in.js", "tracking-in.css"]
depends: ["core"]
api: ["FX.trackingIn(H, el, {at, dur = 0.8, from = 0.28, blur = 6, bounce = 0}): el appears at `at`; `from` is the start spacing in em", "returns {el, end}"]
preview_at: 1.2
twins: ["onda/tracking-in"]
source: {"site": "remotionui", "name": "tracking-in", "repo": "https://github.com/riaz37/remotion-ui", "sha": "b7e0e6becc3d22b8b03dfef72c064f72ff9fad1f", "file": "apps/web/registry/bases/default/primitives/tracking-in.tsx", "license": "MIT"}
---

# tracking-in

The letters start `from` em apart and a little blurred, then close up on a spring with no overshoot (set `bounce` above 0 for a snap). Opacity comes in over the first 60 % of `dur`. Keep the line on one line and make sure it still fits the frame at its widest spacing.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.trackingIn(H, document.querySelector('#title'), { at: H.at('hook+0.2') });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.trackingIn(H, document.querySelector('#title'), { at: cue('hook') + 0.2, from: 0.4 });
```

Rewritten for VideoFactory from RemotionUI `tracking-in` (MIT). No upstream code is copied.
