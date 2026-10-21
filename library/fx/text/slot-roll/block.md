---
id: "slot-roll"
title: "Slot roll"
description: "Each character spins through a reel of glyphs and lands on the new character, column by column; use it for a number or a code that changes."
tags: ["slot", "roll", "counter", "number", "text", "reel", "change", "odometer", "digits"]
kind: "fx"
engine: "both"
status: "approved"
files: ["slot-roll.js", "slot-roll.css"]
depends: ["core"]
api: ["FX.slotRoll(H, el, {at, from = el.textContent, to = from, dur = 1.0, stagger = 0.08, spins = 2, cell = 0.64, glyphs = digits (or letters and digits), color = 'ink'}): the roll runs from `at` to `at + dur`", "returns {el, cells, end}"]
preview_at: 1.0
twins: ["onda/slot-machine-roll"]
source: {"site": "remotionui", "name": "slot-roll", "repo": "https://github.com/riaz37/remotion-ui", "sha": "b7e0e6becc3d22b8b03dfef72c064f72ff9fad1f", "file": "apps/web/registry/bases/default/primitives/slot-roll.tsx", "license": "MIT"}
---

# slot-roll

The old text shows until `at`. Then every column cycles through the glyph pool and slows down to its new character; the columns land left to right, `stagger` seconds apart. The text changes character by character with no fade (cut K10). Columns have a fixed width of `cell` em, so the line keeps its width. A shorter text is padded on the left.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.slotRoll(H, document.querySelector('#count'), { at: H.at('point'), from: '0420', to: '9187' });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.slotRoll(H, document.querySelector('#count'), { at: cue('point'), from: '0420', to: '9187', dur: 1.2 });
```

Rewritten for VideoFactory from RemotionUI `slot-roll` (MIT). No upstream code is copied.
