# Cuts and endings

How one scene hands over to the next, and how a video ends. The basic cut rules and the zoom-through numbers are in `motion.md` (Cuts); this file adds the other cuts. Positions are fractions of the frame (W = width, H = height). Frames (f) are at 30 fps. Brand values, such as the end-card length and the call to action, come from `brands/<id>/brand.md` and the brief.

## Anatomy of a good cut

1. A speeds up into the cut: the last 3–8 f of the exit have the biggest steps (`P.ease.accelExit`, `P.ease.exit`).
2. The cut is one frame. No cross-fade between scenes.
3. B's first frame is already moving or already built. It does not start from rest.
4. B continues A's direction and speed (`motion.md`: match the speed across a cut).

Plan each cut as a pair: write A's last 6 f and B's first 6 f together (object, position within 0.02, scale, colour, blur, ground, speed). Name one thing that is the same on both sides; record it in the brief's scene list as the cut id plus the carried thing.

In a Modern-kit scene a cut is a switch at a cue: a shot with `data-cue`, or `if (P.past('b'))` in `scene.js`. In HyperFrames it is a `tl.set(el, { autoAlpha: 0 }, cue('b'))` next to the first tween of B. Never tween opacity across a scene boundary.

## Cuts

| Id | Cut | Use it when | How |
|---|---|---|---|
| K1 | Hard cut on motion | any scene boundary, the default | Cut on A's fastest frame, never on a settled one. B starts mid-move. |
| K2 | Carried-object match cut | two scenes must read as one take | The same object (dot, card, cursor, headline, ground colour) sits at the same place, within 0.02, with the same speed on both sides. |
| K3 | Container replacement | A ends on an input or list and the result is a box | A's container shrinks about 9 % with the biggest step last, then the new container replaces it at full size in one frame. |
| K4 | Blur-matched cut (zoom-through) | the video already uses blur | Numbers in `motion.md` Cuts. B starts at equal or more blur than A ended with. |
| K5 | Wipe that starts in A and ends in B | both scenes are full of content | Start the wipe 0.1–0.2 s before the voice phrase ends; finish it in B's first 3 f; paint it in B's ground colour with a soft edge of 0.31–0.42 of the wiped axis; 0.56–0.6 s long. B's hero starts 0.1 s before the wipe is done. |
| K6 | Pull-back reveal | "this is inside the real product" is the beat | Show one fragment at about 3x; pull back slowly, then snap the last part in one frame (scale ratio about 0.56). |
| K7 | Whip pan with a content change | moving between two parts of one screen or two screens on one ground | About 8 f, peak speed near a quarter of the move, peak about 13 % W per frame. Old content leaves and new content arrives inside the move. One object keeps its size as the anchor. |
| K8 | Scale cut | the change of distance is the edit, not a camera move | Change scale in one frame, with a content change in the same frame. The background keeps its own scale. A zoom tween says "camera"; a one-frame jump says "a new distance". |
| K9 | Occlusion | the new scene sits on top of the old one | A surface rises over the old content: about 60 % of the travel in the first 0.13 s, no overshoot, nothing fades. |
| K10 | Hard word replacement | one statement replaces the next, a name changes, rows tick through | Replace the text in one frame with a fixed anchor (left edge, centre or carrier dot). No fade between words. |

## Choose a cut

| Beat change | Cut |
|---|---|
| a new point, same world | K1 or K10 |
| the same object, new context | K2 |
| a question or input becomes its answer | K3 |
| a detail becomes the whole screen | K6 or K8 |
| one screen area to another | K7 |
| a busy scene to another busy scene | K5 or K9 |

## Endings

The ending is the last beat of the story, not a web footer. Its length is a brand setting (see `motion.md`, Reading time).

| Id | Ending | Use it when | How |
|---|---|---|---|
| E1 | Button click, cut before release | the viewer's next action is a click on the product's own control | The button arrives already moving; the cursor arrives large (up to 5x) and settles; the click is one frame (button about +2 %, cursor about −13 %); then everything shrinks to about 0.75 and you cut at top speed. Never show the release. |
| E2 | Typed prompt, cut before send | the action is "type what you want" | A centred input bar about 0.71 W x 0.13 H; type the request with a human rhythm; the caret does not blink; the cursor parks on send without a press. |
| E3 | Logo built from parts | the mark is simple geometry | Build it in a few steps over about 7 f; then it keeps moving (a slow shrink). Only when it is the idea: it is a common default (`plan-check.md`). |
| E4 | Call-to-action words focusing in place | a calm ending | Fade only the last phrase; the mark arrives large and shrinks about its centre; the words come into focus where they stand. |
| E5 | Dive into the product | the logo or a part of it can become a container | Scale up at a constant rate (x1.5–2 per 2 f) into one feature that becomes the input or screen of the next shot. |

Ending rules:
- The logo or call to action arrives by a cause on screen or on a spoken word. The reveal is complete about 0.16 s before the voice says the name.
- A final mark starts large (1.5–3.75x) and comes down. Never from zero, never a plain fade up.
- A long hold changes by purpose (a last element lands, a contraction into the end), never by idle drift (`motion.md` Doctrine). A still stretch over 3 s fails the video check (`review.md`).
- Do not fade the end card out by default. End mid-motion or on a hard cut.
- One tagline at most. No "logo + tagline + button + URL" stack (`plan-check.md` A11).
- Scenes near the end get shorter, then the last one stays: the ending is smaller than the climax.

Source: re-expressed from tejashmakwana/motionmaxxing `references/transitions.md` and `references/close.md` (Apache-2.0); no text copied.
