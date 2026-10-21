---
id: "handwriting-text"
title: "Handwriting text"
description: "Writes a line of text on letter by letter, left to right, with a pen dot on the wet edge and an optional hand-drawn underline; use it for a personal note, a title or a signature feel."
tags: ["handwriting", "write on", "pen", "script", "signature", "text", "reveal", "underline", "draw"]
kind: "fx"
engine: "both"
status: "approved"
files: ["handwriting-text.js", "handwriting-text.css"]
depends: ["core"]
api: ["FX.handwritingText(H, el, {at, perChar = 0.07, dur = chars * perChar, wobble = 1.4, pen = 0.1, penColor: 'accent', seed = 1, underline = false, lineColor: 'accent', lineDur = 0.5}): the text of el is written on from `at`; pen is the dot size in em (0 hides it)", "returns {el, parts, end}: end is the time the last stroke ends"]
preview_at: 1.5
source: {"site": "remotionui", "name": "handwriting-text", "repo": "https://github.com/riaz37/remotion-ui", "sha": "b7e0e6becc3d22b8b03dfef72c064f72ff9fad1f", "file": "apps/web/registry/bases/default/primitives/handwriting-text.tsx", "license": "MIT"}
---

# handwriting-text

The text of `el` is revealed one letter after another, left to right, in italic `var(--head)`. A small dot (the pen) rides the wet edge of each letter. Each letter gets a small seeded tilt and baseline drift (`wobble`, in degrees; 0 is machine-even; another `seed` gives another hand). With `underline: true` an SVG stroke (`pathLength` 1, drawn by its dash offset) is drawn under the line after the last letter. A text has no stroke order, so this is a left-to-right write-on, not a trace of real outlines.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.handwritingText(H, document.querySelector('#note'), { at: H.at('hook+0.2'), underline: true });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.handwritingText(H, document.querySelector('#note'), { at: cue('hook') + 0.2, perChar: 0.05 });
```

Rewritten for VideoFactory from RemotionUI `HandwritingText` (MIT). No upstream code is copied.
