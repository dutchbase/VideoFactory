---
id: "notification-stack"
title: "Notification stack"
description: "Generic toast notifications slide in, stack in a corner and dismiss themselves while the others close the gap; use it for alerts or activity."
tags: ["notification", "toast", "stack", "alert", "popup", "message", "ui", "dismiss", "badge", "inbox"]
kind: "fx"
engine: "both"
status: "draft"
files: ["notification-stack.js", "notification-stack.css"]
depends: ["core"]
api: ["FX.notificationStack(H, root, {at, toasts: [{title, body, meta, tone: 'info'|'success'|'warn'|'error', at, hold}], align = 'top-right'|'top-left'|'bottom-right'|'bottom-left', stagger = 0.7, life = 2.2, progress = true, width = 640, margin = 60, gap = 20}): a stack in the corner of root", "returns {el, toasts, end}"]
preview_at: 1.5
source: {"site": "remotionui", "name": "notification-stack", "repo": "https://github.com/riaz37/remotion-ui", "sha": "b7e0e6becc3d22b8b03dfef72c064f72ff9fad1f", "file": "apps/web/registry/bases/default/scenes/notification-stack/index.tsx", "license": "MIT"}
---

# notification-stack

Each toast slides in from the side on a calm spring and leaves after `life` seconds (or its own `hold`). Its arrival is `at + i * stagger`, or `at + toast.at`. When one leaves, the toasts below it move up into the gap. A thin line along the bottom of each toast drains over its life (`progress: false` turns it off). Tones use only brand colours: `success` green, `warn` and `error` accent with a different glyph, `info` ink. A toast with a `body` is taller. No logos or app names.

```js
// Modern kit (scene.js)
const H = Blocks.core(P.timeline());
FX.notificationStack(H, document.getElementById('stage'), { at: H.at('alerts'), toasts: [{ title: 'Saved', body: 'All files', tone: 'success' }] });
// HyperFrames (inline script in index.html)
const H = Blocks.core(tl);
FX.notificationStack(H, document.querySelector('[data-composition-id="main"]'), { at: cue('alerts'), align: 'bottom-left', toasts: [{ title: 'New message' }] });
```

Rewritten for VideoFactory from RemotionUI `NotificationStack` (MIT). No upstream code is copied.
