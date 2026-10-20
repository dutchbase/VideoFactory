---
id: "strikethrough-replace"
title: "Strikethrough replace"
description: "A line strikes out one phrase, holds a beat, then a new phrase replaces it in a single frame (cut K10); use it for a correction or a before and after."
tags: ["strikethrough", "replace", "correction", "text", "cut", "before-after", "edit", "swap", "statement"]
kind: "fx"
engine: "both"
status: "draft"
files: ["strikethrough-replace.js", "strikethrough-replace.css"]
depends: ["core"]
api: ["FX.strikethroughReplace(H, el, {at, to, from = el.textContent, strike = 0.3, hold = 0.35, align = 'center'|'left'|'right', strikeColor = 'accent', replaceColor = 'ink', weight = 0.07, height = 0.56, tilt = -0.6}): strike starts at `at`, swap at `at + strike + hold`", "returns {el, swap, end}"]
preview_at: 2.0
source: {"site": "remotionui", "name": "strikethrough-replace", "repo": "https://github.com/riaz37/remotion-ui", "sha": "b7e0e6becc3d22b8b03dfef72c064f72ff9fad1f", "file": "apps/web/registry/bases/default/primitives/strikethrough-replace.tsx", "license": "MIT"}
---

# strikethrough-replace

Beat 1: an accent line sweeps through the old phrase. Beat 2: a short hold. Beat 3: the old phrase is hidden and the new one is shown in the same frame, in the same place (cut K10 in `_shared/transitions.md`: no fade between the words). Both phrases share one anchor (`align`), so the box does not jump. `weight`, `height` and `tilt` shape the strike (em and degrees).

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.strikethroughReplace(H, document.querySelector('#claim'), { at: H.at('point'), to: 'Ready in three days' });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.strikethroughReplace(H, document.querySelector('#claim'), { at: cue('point'), to: 'Ready in three days', replaceColor: 'accent' });
```

Rewritten for VideoFactory from RemotionUI `strikethrough-replace` (MIT). No upstream code is copied.
