---
id: "tip"
title: "Numbered tip block"
description: "Accent block with a big number and a title that comes in word by word with the voice; enters from the right and leaves to the left."
tags: ["tip", "number", "step", "list", "title", "heading", "1 2 3"]
kind: "block"
category: "interface"
engine: "hyperframes"
files: ["tip.js", "tip.css"]
depends: ["core"]
api: ["const t = Blocks.tip(H, rootEl, {nr, words: [a, b] | title, sub: [a, b]})", "t.enter(at), t.exit(at)"]
preview_at: 3.0
---

# tip

`words: [a, b]` takes spoken words a..b-1 from ANIM.words; without a voice use `title`. The root sets the width and the top.

See `demo.html` for a working example.
