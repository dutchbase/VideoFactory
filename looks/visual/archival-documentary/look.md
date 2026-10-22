---
id: "archival-documentary"
axis: "visual"
title: "Archival documentary"
summary: "Old photos and film footage with grain, slow Ken Burns moves, tape and typewriter captions; serious and warm."
aliases: ["archive footage", "Ken Burns documentary", "vintage documentary", "history doc"]
sources: ["https://explain.film/explainer-video-styles", "https://www.creatoros.ca/blog/motion-style-atlas/", "https://en.wikipedia.org/wiki/Ken_Burns_effect"]
best_for: ["timeline", "founder-story", "myth-vs-fact", "explainer", "founder story"]
formats: ["wide", "tall"]
pairs_with: {"editing": "cinematic-drift", "content": "timeline"}
preview: "ai"
build: "ai"
palette_roles: {"paper": "bg", "photo": "raised", "ink": "ink", "caption": "dim", "tape": "r4", "mark": "accent", "rule": "line"}
---

## Look
- Field: dark or aged paper (`bg`). The photo is a sepia or mono image in a white-edge print frame, tinted toward the brand ramp (`raised`, `r4`).
- Treatment: film grain at 10–14% opacity, a vignette of 35% on the corners, light scratches and dust specks. Photos have a slight rotation (−2° to 2°) and a corner of tape.
- Captions: `mono` in a typewriter look, 28–36 px, `ink` on a paper strip. Dates as small stamps in `accent`.
- Type: `head` for the title card at 90–120 px, serif-like weight if the brand allows, letter spacing 2%.

## Behaviour
- Entrances: a photo fades in from black over 700 ms, `P.ease.enter`, and starts a Ken Burns move. A print slides in 60 px with 2° rotation, 500 ms, `P.ease.softLand`.
- Text: captions type on at 35 ms per character with a block cursor. A date stamp thuds in with 1.2 to 1.0 scale, 180 ms, `P.ease.pop`.
- Transitions: a 600 ms cross dissolve through black, or a flash frame of 80 ms (film burn) in `accent` at 30%. Photos exit with a 400 ms fade, `P.ease.exit`.
- Camera: Ken Burns on every photo: slow push 1.0 to 1.12 or pan 5% over the hold, `P.ease.linear`. Alternate directions between shots.
- Pacing: slow and steady. 5–8 s holds, about 8–10 changes per minute. Hold 1 s of black before the key reveal.
- Ambient: grain flickers at 12 fps. Light flicker of ±3% brightness on a 0.4 s loop. Dust specks drift.
- Sound: projector hum, tape hiss, soft piano or strings, a typewriter click for each letter.

## Do
- Use one real or generated archival image per beat.
- Keep captions to one short line with a date.
- Move the camera on every still.
- Keep the vignette and grain steady across scenes.

## Don't
- No bright flat colour blocks or icons.
- No fast cuts or bounce.
- No clean modern UI.
- No more than 2 photos in one frame.

## Build notes
Best with AI or library images (old photo look). The native preview is a stand-in: a framed photo block with CSS grain and vignette. Ken Burns is a `transform: scale() translate()` driven by `P.prog` with `P.ease.linear`. Grain is a looped noise layer with `mix-blend-mode: overlay`.
