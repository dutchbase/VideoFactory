---
id: "underline"
title: "Underline"
description: "The text snaps in, then an accent line draws under it after a short beat; a two-step emphasis for one key phrase."
tags: ["underline", "emphasis", "line", "draw", "text", "accent", "key phrase", "title"]
kind: "fx"
engine: "both"
status: "approved"
files: ["underline.js", "underline.css"]
depends: ["core"]
api: ["FX.underline(H, el, {at, dur = 0.25, lineDelay = 0.3, lineDur = 0.5, rise = 24, lineColor = 'accent', thickness = 0.08, offset = 0.04, text = el.textContent}): text at `at`, line from `at + lineDelay`", "returns {el, text, line, end}"]
preview_at: 1.5
source: {"site": "onda", "name": "underline", "repo": "https://github.com/degueba/onda", "sha": "3c814051269597b31fee1603bef7ccfb93d091b6", "file": "registry/components/underline/Underline.tsx", "license": "MIT"}
---

# underline

Step 1: the text snaps up `rise` px with a power4 ease. Step 2: after `lineDelay` the line draws from left to right. `thickness` and `offset` are in em, so the line sits under the descenders at any font size. Use the accent colour for the line only once per scene.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.underline(H, document.querySelector('#phrase'), { at: H.at('point') });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.underline(H, document.querySelector('#phrase'), { at: cue('point'), lineColor: 'green' });
```

Rewritten for VideoFactory from Onda `Underline` (MIT). No upstream code is copied.
