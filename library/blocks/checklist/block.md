---
id: "checklist"
title: "Checklist (ticks)"
description: "Row of accent labels with a check mark that appear one by one; shows that requirements or steps are met."
tags: ["checklist", "check", "tick", "ticks", "requirements", "done", "passed", "labels"]
kind: "block"
category: "interface"
engine: "hyperframes"
files: ["checklist.js", "checklist.css"]
depends: ["core"]
api: ["const v = Blocks.checklist(H, rootEl, {items: [...]})", "v.show(at[, step])"]
preview_at: 1.5
---

# checklist

Only tick what was really checked (for example counted words of a real answer).

See `demo.html` for a working example.
