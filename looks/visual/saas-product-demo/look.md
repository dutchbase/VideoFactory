---
id: "saas-product-demo"
axis: "visual"
title: "SaaS product demo"
summary: "Clean app windows, cards and charts with a moving cursor and smooth zooms into the one feature that matters."
aliases: ["product ui", "app demo", "interface explainer"]
sources: ["https://explain.film/explainer-video-styles/product-ui", "https://ideatomotion.com/looks"]
best_for: ["product-tour", "tutorial", "launch-announcement", "onboarding", "ad"]
formats: ["wide", "tall"]
pairs_with: {"editing": "zoom-through", "content": "product-tour"}
preview: "native"
build: "native"
palette_roles: {"canvas": "bg", "window": "surface", "card": "raised", "ink": "ink", "muted": "dim", "line": "line", "primary": "accent", "ok": "green"}
---

## Look
- Field: a soft background (`bg`, or a quiet two-tone gradient from `r1` to `bg`). The app window floats on it with a large soft shadow.
- Window: a rounded frame (radius 14-18 px) in `surface` with a top bar of three dots, a sidebar and a content area of cards in `raised`.
- Data: simple abstract UI. Text as grey bars, a bar or line chart in `accent`, a toggle, a table row, a green `ok` tick. Real words only in headings and buttons.
- Cursor: a clear arrow in `ink` with a small click ring in `accent`.
- Type: `head` for a caption at 56-80 px above or beside the window, `mono` for small labels at 14-16 px.

## Behaviour
- Entrance: the window rises 40 px and scales from 0.95 to 1.0 in 700 ms with `P.ease.softLand`. Inner cards follow with a 60 ms stagger, `P.ease.enter`.
- Cursor: it travels in a curved path to the target in 600-900 ms with `P.ease.move`. A click is a 200 ms ring pulse and a 4% button press.
- Zoom: the camera scales to the feature, 1.0 to 1.8 in 1.2 s with `P.ease.move`, and the rest of the window dims to 40%.
- UI change: a toggle slides 250 ms with `P.spring` snap. A chart grows in 600 ms with `P.ease.enter`. A toast drops in 400 ms with `P.ease.softLand`.
- Text: the caption fades up 16 px in 400 ms, `P.ease.enter`.
- Transition: zoom out in 900 ms, then slide to the next window.
- Pacing: one action per beat, 0.6-1.2 s apart, holds of 2-4 s, about 15-22 changes per minute.
- Ambient: none. Sound: soft mouse click, a gentle tick on toggles, a light chime on success.

## Do
- Show one feature per scene and zoom to it.
- Move the cursor before the thing changes.
- Keep real words short and use bars for filler text.

## Don't
- No real screenshots with tiny unreadable text.
- No bounce on windows.
- No more than one highlight colour besides `accent`.
- No cursor that jumps without travel.

## Build notes
Modern kit: HTML/CSS windows, cursor as an absolutely positioned SVG moved with `P.prog` along a bezier. Zoom is a `transform: scale` on a wrapper with a matching `transform-origin`. For real UI, use a capture (`capture.md`) and place it inside the window frame. Tall format: crop to the feature and zoom earlier.
