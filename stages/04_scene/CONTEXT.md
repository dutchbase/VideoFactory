# 04 Scene and preview

Read `_shared/permissions.md` before production. Pause for human review when the active session permission requires it.

Engine: `project.json` `engine` is `canvas` (the built-in Modern kit; a missing key means the same) or `hyperframes`. For hyperframes write `index.html` per `_shared/hyperframes.md`, not the Modern steps below. A long video may split its chapters into sub-compositions (`04_scene/compositions/*.html`, mounted with `data-composition-src`). `anim.py check`, the tone gate and the audio guard read those too. `check`, `stills` and `render` apply to both engines.

Looks: if `04_scene/looks/` exists, read its cards (`<axis>-<id>.md`) before the shot plan. They are frozen copies from `looks/`; `project.json` `looks` lists them per axis, main look first. Each scene uses the look its brief line names, else the main look. A card's `## Behaviour` is binding for motion, cuts and structure inside its scenes; `## Look` maps the palette roles onto the brand tokens. Mixing rules: `looks/CONTEXT.md`.

Read `_shared/modern.md`: how to write a scene in the Modern kit. Start from the files `anim.py new` copied into `04_scene/`. Colours and fonts come from the brand's `tokens.js`. Plan one shot per cue before you build.

Motion vocabulary (`P.ease.enter`, `P.spring`, `P.track`, `P.rand`) and banned defaults: `_shared/motion.md`. On-screen text follows `_shared/tone.md`. `stills` and `render` stop on tone problems. Keep provenance in the records (`assets/captures.md`, `assets/library.md`, `REVIEW.md`), never as an on-screen label.

Before you build, read the brief's plan check (`_shared/plan-check.md` part A). After the stills, the judge (`frame-critic`) reports the slop signs of part B. Cuts and endings: `_shared/transitions.md`.

Run `python anim.py check <slug>` until every counter reads 0. Then run `python anim.py stills <slug>` and do the look checks in `_shared/review.md`. Watch the live preview with `python anim.py preview <slug>`, or open Studio (`python anim.py studio`). Recompile the cues after a timing change.

Captures: `grab`, `login` and `record` show a real web page or app at any breakpoint (`_shared/capture.md`). `04_scene/assets/captures.md` lists every capture for the brief and for the `DESCRIPTION.md` sources. Redaction is best-effort: review captures before you share them.

Before the shot plan, read `library/CATALOG.md`: the ready parts (fx for both engines, blocks, motion clips, animated icons, Lottie) by category, and the components we can rewrite on demand (`_shared/porting.md`). Icons, graphics, Lottie and stock footage: `_shared/library.md`. Add them with `python anim.py use <slug> <ref>`. It logs the licence in `assets/library.md`.

Sound: pick the music bed and place effects on cuts and reveals (`_shared/sound.md`). Record each music and effect file with its source and licence in `04_scene/assets/sound.md`. Library sounds: `library/audio/INDEX.md`; `anim.py use <slug> audio:<id>` copies one and writes its licence line.

Handoff: after zero counters, stills and a moving preview, run the `frame-critic` judge on fresh stills. Fix until every score is 8 or higher. Judge before the gate, not only after a render. When this session requires scene review, mark the current gate ready and open its exact Studio review link (`_shared/dashboard-review.md`). Review the saved scene, the selected style snapshot and the referenced assets together. Otherwise continue to the next permitted stage.

Guided command: `/vf-scene`. Next: `/vf-render`.
