---
id: "<id>"
title: "<Title>"
description: "<One sentence: what the part puts on screen and when you use it.>"
tags: ["<word>", "<synonym>", "<related word>"]
kind: "fx"
engine: "both"
status: "draft"
files: ["<id>.js", "<id>.css"]
depends: ["core"]
api: ["FX.<camelId>(H, el, {at, ...}): <what it does>"]
preview_at: 1.5
source: {"site": "<source>", "name": "<upstream name>", "repo": "<repo URL>", "sha": "<commit>", "file": "<path in the repo>", "license": "MIT"}
---

# <id>

What it shows, the options, and one usage example for each engine:

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.<camelId>(H, document.querySelector('#title'), { at: H.at('hook+0.2') });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.<camelId>(H, document.querySelector('#title'), { at: cue('hook') + 0.2 });
```

Rewritten for VideoFactory from <upstream name> (<source>, MIT). No upstream code is copied.
