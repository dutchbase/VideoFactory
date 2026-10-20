---
id: "phone"
title: "Phone frame"
description: "Phone with an ink-coloured body, notch and hard shadow; the screen is the place for another block, such as the chat screen in the mobile variant."
tags: ["phone", "mobile", "smartphone", "app", "frame", "device", "screen"]
kind: "block"
category: "interface"
engine: "hyperframes"
files: ["phone.js", "phone.css"]
depends: ["core"]
api: ["const t = Blocks.phone(H, rootEl)", "t.screen: the box to give to another block (e.g. Blocks.chat(H, t.screen, {variant: 'mobile', frame: false}))", "t.el: the phone, e.g. for a camera move"]
preview_at: 3.0
---

# phone

The phone fills its root (about 600 x 1240 px).

See `demo.html` for a working example.
