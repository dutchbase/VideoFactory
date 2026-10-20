---
id: "chat"
title: "Chat screen (rebuilt, no logo)"
description: "Rebuilt chat screen with an empty state, typing in the input field, sending, a streaming answer, strike-through and highlight; variants dark (ChatGPT-like), light (Claude-like) and mobile."
tags: ["chat", "chat screen", "chatgpt", "claude", "conversation", "prompt", "input", "typing", "answer", "stream", "send", "app", "screen", "dark", "light", "mobile", "strike", "highlight"]
kind: "block"
category: "interface"
engine: "hyperframes"
files: ["chat.js", "chat.css"]
depends: ["core"]
api: ["const c = Blocks.chat(H, rootEl, {variant: 'dark'|'light'|'mobile', title, hello, placeholder, frame})", "c.center(at) / c.dock(at): input in the middle (empty chat) or at the bottom", "c.showHello(at) / c.hideHello(at)", "c.typeInto(text, t0, t1, {hot, block, struck}) -> seg; c.quote(text, at); c.strike(seg|el, at); c.untype(seg, t0, t1); c.clearInput(at)", "c.sendTo(at, text, {struck, chips}) -> {el, struck}: input clears, message flies up; c.bubble(text, at, opts)", "c.answer(text, t0, t1) -> spans (thinking dot, then words stream); c.highlight(spans, at); c.clearMessages(at)", "c.el, c.input, c.msgs, c.send: elements, e.g. to put a cursor click on c.send"]
preview_at: 3.4
---

# chat

The root is a positioned box (about 920 x 810 px); the chat fills it. Put a camera (`scale` on a wrapper) around it yourself. A rebuilt screen is labelled in the caption ("Chat screen rebuilt").

See `demo.html` for a working example.
