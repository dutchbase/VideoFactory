---
id: "terminal"
axis: "visual"
title: "Terminal"
summary: "A glowing command-line screen: monospace text, a blinking cursor and typed commands in one bright phosphor colour."
aliases: ["phosphor terminal", "terminal green", "hacker screen", "command line"]
sources: ["https://www.creatoros.ca/blog/motion-style-atlas/", "https://ideatomotion.com/looks"]
best_for: ["tutorial", "product-tour", "explain-mechanism", "course", "explainer"]
formats: ["wide", "tall"]
pairs_with: {"editing": "word-stagger", "content": "tutorial"}
preview: "native"
build: "native"
palette_roles: {"screen": "bg", "phosphor": "accent", "dim-text": "dim", "bright": "ink", "warn": "danger", "ok": "green", "rule": "line"}
---

## Look
- Screen: a very dark `bg` with a faint inner vignette and a thin `line` window frame. Optional scanlines: 1 px lines at 6% opacity every 3 px.
- Text: all text in the brand `mono`, 26–40 px, in `accent` (the phosphor colour), with a soft glow (text-shadow 0 0 8 px at 50%). Prompts use `dim`, success lines use `green`, errors use `danger`.
- Layout: a left-aligned text block with 1.5 line height, a prompt symbol (`$` or `>`), a title bar with three dots, and optional ASCII boxes and progress bars made of block characters.
- Headline: one large line, 64–96 px `mono` in `ink` with the glow. Everything else stays small and dim.
- No photos, no icons; use characters (`[ok]`, `->`, `###`) instead.

## Behaviour
- Entrances: text types in at 25–40 ms per character with `P.ease.linear`; the command line types, then output lines appear all at once 200 ms after the "Enter" press. Key ticks land on every 2nd character.
- Cursor: a solid block that blinks 500 ms on and 500 ms off, the only ambient loop. It sits at the end of the active line.
- Progress: bars fill in block characters in steps of 5%, `P.ease.linear`, 1–2 s per bar.
- Exits: lines scroll up one line per 120 ms as new lines arrive, or the screen clears in one frame. Old lines dim to `faint`.
- Emphasis: the key word flips to inverted colours (`bg` text on `accent` block) for 600 ms.
- Transitions: a hard cut with a 2-frame flicker, a clear-screen then retype, or a 6-line scroll. Never a fade.
- Camera: locked. A 2% slow push-in is allowed on long outputs. No shake.
- Pacing: 2–5 s per command, about 12–16 changes per minute; wait 0.5 s after each Enter before output.
- Sound: soft mechanical key clicks, a low hum and a short beep on success or error.

## Do
- Show real-looking, short commands and results.
- Keep one phosphor colour for 90% of the text.
- Type the command in time with the voice.
- Use the inverted block to point at one word.

## Don't
- No smooth fades, springs or bounce.
- No second colour except `green` and `danger` for status.
- No walls of text; at most 8 lines on screen.
- No proportional fonts in the terminal.

## Build notes
Native CSS: a `mono` text block, characters revealed with `P.prog` mapped to a character count, a blinking `::after` cursor stepped by time. Glow with `text-shadow`; scanlines with a `repeating-linear-gradient` overlay. Use `white-space: pre` for ASCII. In tall format, drop the font to 28 px and wrap the output to 34 columns. Works in both formats.
