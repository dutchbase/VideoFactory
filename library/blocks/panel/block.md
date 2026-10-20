---
id: "panel"
title: "Full-screen panel (transition)"
description: "Accent panel that slides in from the right over everything with big lines, then leaves to the left; a hard transition to a new part."
tags: ["panel", "transition", "wipe", "turn", "heading", "statement", "full screen"]
kind: "block"
category: "interface"
engine: "hyperframes"
files: ["panel.js", "panel.css"]
depends: ["core"]
api: ["const p = Blocks.panel(H, rootEl, {lines: [...], wordIdx: [...]})", "p.enter(at), p.exit(at)"]
preview_at: 1.6
---

# panel

Use it with the stage as root. `wordIdx` snaps each line on its spoken word; without it the lines follow 0.3 s apart.

See `demo.html` for a working example.
