---
id: "cursor"
title: "Cursor with click"
description: "Big mouse cursor that moves to a button and clicks, with a click ring; the click starts the next step."
tags: ["cursor", "mouse", "click", "button", "pointer", "point"]
kind: "block"
category: "interface"
engine: "hyperframes"
files: ["cursor.js", "cursor.css"]
depends: ["core"]
api: ["const k = Blocks.cursor(H, rootEl)", "k.move(x, y, at[, dur]): eased move from the last spot (enters from the lower right)", "k.click(x, y, at): squash plus ring on `at`", "k.leave(at[, dur])"]
preview_at: 1.2
---

# cursor

Coordinates are px inside the root; the tip of the arrow is the point. Put it in the same wrapper as the screen, so a camera moves both.

See `demo.html` for a working example.
