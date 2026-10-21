---
id: "rotate-in"
title: "Rotate in"
description: "Text settles from a slight tilt (default -8 degrees) to straight while it fades in, on a calm spring with no overshoot; use it for a title or a line."
tags: ["rotate", "tilt", "entrance", "text", "title", "spring", "calm", "fade", "settle"]
kind: "fx"
engine: "both"
status: "approved"
files: ["rotate-in.js", "rotate-in.css"]
depends: ["core"]
api: ["FX.rotateIn(H, el, {at, dur = 0.7, angle = -8, origin = '50% 50%', by: null|'words'|'chars', stagger = 0.08}): el appears at `at`; angle is clamped to -12..12", "returns {el, parts}"]
preview_at: 1.5
twins: ["remotionui/rotate-in"]
source: {"site": "onda", "name": "rotate-in", "repo": "https://github.com/degueba/onda", "sha": "3c814051269597b31fee1603bef7ccfb93d091b6", "file": "registry/components/rotate-in/RotateIn.tsx", "license": "MIT"}
---

# rotate-in

The text turns from `angle` degrees to 0 and fades in on one spring. The calm range is -12 to 12 degrees; a larger value is clamped. `origin` is the pivot (for example `'0% 100%'` for the bottom left corner). `by: 'words'` turns each word on its own, `stagger` seconds apart.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.rotateIn(H, document.querySelector('#title'), { at: H.at('hook+0.2') });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.rotateIn(H, document.querySelector('#title'), { at: cue('hook') + 0.2, by: 'words', angle: 10 });
```

Rewritten for VideoFactory from Onda `RotateIn` (MIT). No upstream code is copied.
