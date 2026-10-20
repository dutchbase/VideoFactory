---
name: vf-scene
description: Build the animated scene (stage 04). Use when the user says "scene", "animation", "build the visuals", "stills", "preview", "stage 4".
---
# /vf-scene — build the animation

Talk: `_shared/talk.md`. Steps: `_shared/guide.md`.
Read: `stages/04_scene/CONTEXT.md`, `_shared/modern.md`, `_shared/motion.md`, `brands/<brand>/brand.md`,
`brands/<brand>/tokens.js`, `videos/<id>/03_cues/cues.md`.
What the library holds, by category: `library/CATALOG.md` (read it before the shot plan). Icons, graphics and stock clips: `_shared/library.md`.
A look the library does not have: `_shared/porting.md` (the new part joins the library as a draft). Screenshots of web pages: `_shared/capture.md`.
Video id: `<brand>/<slug>`. If the user gave none, run `python anim.py status` and ask which video.

1. Check that the cues are compiled and the user approved them.
2. Plan one shot for each cue. Show a table: cue, what the viewer sees, the motion, the library part (`fx:`, `block:`, `motion:`, `animicon:`, `lottie:`, or `upstream:` to rewrite). Ask "Build this?" and wait.
3. Write `videos/<id>/04_scene/index.html` and `videos/<id>/04_scene/scene.js` with the Modern kit, as
   `_shared/modern.md` says. Take colours and fonts from the brand tokens. Remove the `TEMPLATE` marker from `scene.js`.
   Follow the sound pass that `stages/04_scene/CONTEXT.md` names.
4. Run `python anim.py stills <id>`, then `python anim.py check <id>`.
   Fix every finding and run both again. Every counter must read 0.
5. Show the contact sheet: the path that `stills` prints. Say what to look at: text size, empty areas, the order of events.
6. Run the `frame-critic` judge on the fresh stills (`_shared/review.md`, the judge section). Fix what it names.
7. For a live review run `python anim.py preview <id>`. Tell the user to open the address it prints.
   Stop the preview when the user is done.

Gate: the user approves the stills and the preview.
Next: `/vf-render`.
