# Motion rules

How things move in every scene. Helpers are in `_runtime/player.js` (global `P`); the Modern kit builds on them (`modern.md`). Checks and the review loop: `review.md`. Sound: `sound.md`.

## Doctrine (explainers)
- The voice is the clock. Show a thing when the voice says it. Cue the meaning word, usually the verb.
- Text that must be read starts 0.02–0.06 s before its word. Hits land on the word.
- One change per spoken beat, 0.4–1.2 s apart. At most two cues on one word.
- Smooth beats bouncy. `P.ease.enter` is the default. `pop` and bounce only for a playful moment.
- No slow drift or "breathing" to fill a hold. Still is better than aimless motion.
- Something new on screen every 3–8 s. After 7–8 s of dense motion, rest for 1 s. A brand can set a stricter bar: a hook in the first 1–2 s and a change every 3–5 s (`review.md`).

## Eases
| Name | Curve | Use | Time |
|---|---|---|---|
| `P.ease.enter` | (0.16, 1, 0.3, 1) | things that arrive | 300–500 ms for small things; panels and cards: see Durations |
| `P.ease.exit` | (0.7, 0, 0.84, 0) | things that leave | 200–300 ms (60–70% of the entrance) |
| `P.ease.move` | (0.65, 0, 0.35, 1) | moves across the screen | 300–400 ms |
| `P.ease.pop` | (0.34, 1.56, 0.64, 1) | one branded accent | 300–400 ms |
| `P.ease.linear` | — | continuous motion only (progress bar, scroll) | — |
| `P.ease.crashIn` | measured, overshoots about 18 % | one slam that hits and passes its mark | about 330 ms |
| `P.ease.whip` | measured power-out 2.52 | a hard decelerating big move | about 230 ms |
| `P.ease.softLand` | measured expo-out | a firm landing for text and panels | about 400 ms |
| `P.ease.accelExit` | measured power-in 2.6 | a leave that accelerates into a cut | about 430 ms |

`P.ease.enter` stays the default. The four measured eases come from films made by people (motionmaxxing, Apache-2.0). In HyperFrames the same curves are `ease: Eases.whip` (`hyperframes.md`).

Use them through `P.prog('cue', { dur: 0.4, ease: P.ease.enter })`. Any CSS curve: `P.bezier(x1, y1, x2, y2)`.

## Durations
| Kind | Time |
|---|---|
| micro (icon, tick) | 120–240 ms |
| small (label, chip) | 320–480 ms |
| panel, card | 560–880 ms |
| scene change | 800–1200 ms |
| camera move | 1.6–3.6 s |
| number count-up | 600–1200 ms |

Longer travel needs more time: 50 px ×0.8, 100 px ×1.0, 200 px ×1.3, 400 px ×1.6, full screen ×1.8–2.0. When in doubt, make it 20% shorter.

## Springs
`P.spring({ dur, bounce })(seconds)` goes 0 → 1. `P.track([[t0, v0], [t1, v1], ...], { dur, bounce })` springs to each new value at its time, so a target can change many times.

| Preset | Options |
|---|---|
| settle (default) | `{ dur: 0.5, bounce: 0 }` |
| snap | `{ dur: 0.35, bounce: 0.1 }` |
| pop | `{ dur: 0.4, bounce: 0.25 }` |
| heavy | `{ dur: 0.9, bounce: 0.05 }` |

- Overshoot budget, as `bounce`: errors 0 (none); interface 0.1–0.4 (0.2% to about 10%); a celebration up to 0.6 (about 25%). For reference: 0.25 gives about 3%, 0.5 about 16%.
- Entrances start at scale 0.90–0.97, never at 0.

## Stagger
- List items 40–80 ms apart, grid items 20–40 ms. Total at most 800 ms: `total = (n − 1) × offset + item`.
- A narrated word reveal: 0.3–0.4 s per word (0.5–0.6 s for drama).
- Add ±1 frame of jitter with `P.rand(seed)`. Never `Math.random`.

## Reading time
- On-screen text stays at least `max(0.7 s, 0.25 s + characters / 17)`. `anim.py check` counts every string that does not.
- A hero line that must work without sound: `0.3 s × words + 1.5 s`. The final call to action: 4–6 s.
- Do not ask the viewer to read text that moves fast.

## Camera
- The cause of a move is on screen 10–14 frames (about 0.4 s) before the camera moves.
- One camera move per beat. Never zoom in and straight back out.
- Scale with `P.zoom(a, b, p)`: equal steps feel equal. For a captured page, zoom a large still image, not the live page.

## Path travel
- Prepare a fixed SVG route during scene setup: `const route = P.path('M20 90 Q160 10 300 90')`. In a frame, use `route(P.prog('travel', { dur: 1 }))` for `{ x, y, angle }` in scene units and radians. Progress clamps to the path ends. Invalid or zero-length paths throw during setup. Use the angle to turn an object along its travel.

## Cuts
- **Zoom-through:** the old shot scales 1 → 1.2 and blurs 0 → 10 px with `exit` over 0.2 s. Hard cut. The new shot goes 0.75 → 1 and blur 10 → 0 with `enter` over 0.5 s. Full-frame surfaces: 18–20 px blur.
- Match the speed across a cut: what moves out fast comes in fast.
- Every cut has a reason you can say out loud.
- Never exit, show a gap, then enter. Overlap or cut.
- More cuts (K1–K10) and endings (E1–E5): `transitions.md`.

## Type
- Wide (1920×1080): headline ≥ 60 px, body ≥ 20 px. Tall (1080×1920): headline ≥ 90 px, body ≥ 32 px.
- Strong weight contrast (300 against 800). Display tracking −0.03 em.
- Tabular figures for counters. Fonts: `brand.md`.

## Safe areas
- Wide: at least 60 px from every edge (about 5%). The Modern kit keeps more (`modern.md`, Formats and safe areas).
- Tall: text inside x 60–1020 and y 250–1500. The platform's buttons and captions cover the rest.
- Check it at phone size (`review.md`).

## Colour
- One primary and one accent from `brand.md`. Colour carries a meaning; do not decorate with it.
- Lift the blacks: never pure `#000`.
- Grain changes 12 times a second, not every frame.

## Motion blur
`anim.py render <slug> --blur 4`: only for big, fast moves. Never for text that must be read.

## Banned defaults

- Essential labels whose contrast depends on an animated bar reaching them: keep a contrasting text plane throughout the reveal.
- Ink copy over an ink shadow: give essential labels a clear brand-paper plane and enough projected clearance from all object faces.
- Counting tiny camera-angle changes as visible motion: verify the actual MP4; land or reveal a substantial object surface when the frame still reads as static.
- a centred title on a gradient
- everything fading in
- glow on interface chrome
- particle bursts
- invented labels: eyebrows, `01 / 02 / 03`, version stamps, timecode HUDs (`check`: invented labels)
- text within 60 px of the frame edge
- an empty or black frame 0
- text over text for longer than a cross-fade (`check`: text overlaps)
- a text-only video: kinetic type as the only visual layer. Every video carries at least one screen (real or rebuilt), illustration, stock shot or library block (`check`: no visual layer). Only when you want a text video: `"allow": ["text-only"]` in `project.json`, noted in `REVIEW.md`
- a still stretch over 3 s (`render` fails on it; `"allow": ["still"]` only when you want it)
- a line mask that cuts off a descender (g, j, p, q, y): give the mask bottom padding (it happens at line-height 1)

This list grows. When a problem shows up twice, add it here (`review.md`, steering rule). The ranked slop signs the judge looks for: `plan-check.md` part B.

## Sources
Re-expressed and adapted, with thanks: cth9191/animate, howseen-ai/claude-motion-design, whaleyxbt/claude-motion, AbubakrChan/product-launch-motion, Barty-Bart/motion-graphics, iart-ai/motion-design-skills, LottieFiles/motion-design-skill, nateherkai/hyperframes-student-kit (all MIT); heygen-com/hyperframes skills (Apache-2.0); tejashmakwana/motionmaxxing (Apache-2.0: plan check, slop signs, cuts and endings, measured eases); motiondivision/motion (MIT, spring maths). Ideas only, no text copied: t3knobox/klik-anim-skill-creation and remotion-dev/skills (no licence). Code notices: `THIRD-PARTY-NOTICES.md`.
