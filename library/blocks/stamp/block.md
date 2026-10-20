---
id: "stamp"
title: "Stamp with shake"
description: "Tilted stamp that lands on the picture with a bang and a short shake of the screen under it; for the turning point or a verdict."
tags: ["stamp", "impact", "slam", "shake", "verdict", "label", "emphasis"]
kind: "block"
category: "shapes"
engine: "hyperframes"
files: ["stamp.js", "stamp.css"]
depends: ["core"]
api: ["const s = Blocks.stamp(H, rootEl, {text, x, y, rotation, shake: elementToShake})", "s.slam(at): lands on `at`", "s.clear(at)"]
preview_at: 1.5
---

# stamp

Put the `stamp` sound effect on the same cue as `slam`.

See `demo.html` for a working example.
