---
id: "matrix-decode"
title: "Matrix decode"
description: "Random glyphs resolve from left to right into the real text, with one accent character on the decode front; use it for a data, code or reveal moment."
tags: ["decode", "matrix", "scramble", "text", "reveal", "glyphs", "hacker", "typing", "resolve"]
kind: "fx"
engine: "both"
status: "approved"
files: ["matrix-decode.js", "matrix-decode.css"]
depends: ["core"]
api: ["FX.matrixDecode(H, el, {at, dur = 1.0, rate = 24, jitter = 2, glyphs = letters and digits, seed = 'matrix-decode', color = 'ink', hotColor = 'accent', scrambleColor = 'dim', text = el.textContent}): the text appears at `at` as a scramble and is clean at `at + dur`", "returns {el, parts, end}"]
preview_at: 1.0
twins: ["onda/matrix-decode"]
source: {"site": "remotionui", "name": "matrix-decode", "repo": "https://github.com/riaz37/remotion-ui", "sha": "b7e0e6becc3d22b8b03dfef72c064f72ff9fad1f", "file": "apps/web/registry/bases/default/primitives/matrix-decode.tsx", "license": "MIT"}
---

# matrix-decode

The line shows as scrambled glyphs and resolves one character at a time from left to right. A seeded jitter (`jitter` characters) makes some characters lock early or late. Each character keeps the width of its real glyph, so the line does not change width. The character on the decode front uses `hotColor`; the other unresolved ones use `scrambleColor`. `rate` is the number of glyph changes per second. Give the element a font size and keep it on one line.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.matrixDecode(H, document.querySelector('#title'), { at: H.at('hook+0.2'), dur: 1.2 });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.matrixDecode(H, document.querySelector('#title'), { at: cue('hook') + 0.2, dur: 1.2 });
```

Rewritten for VideoFactory from RemotionUI `matrix-decode` (MIT). No upstream code is copied.
