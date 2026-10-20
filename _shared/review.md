# Checks and review

A video is ready for you when the checks read zero, the look checks are done and a separate judge has scored it. The checks do not approve a video. You do, in the video's `REVIEW.md`. Motion rules: `motion.md`. Sound: `sound.md`.

Library parts: when you approve a video, every `fx:` part it uses with status `draft` (see `04_scene/assets/library.md`) becomes `approved`. Set `status: "approved"` in its `library/fx/<category>/<id>/block.md` and run `lib index`. Write `fx approved: <id>` in `REVIEW.md`.
For the Studio handoff and current-fingerprint approval, follow `dashboard-review.md`. Keep the independent judge's dated scores and three worst problems in `05_render/frame-critic.md` so render readiness can verify the evidence.

## 1. Scene check (must read 0)
`anim.py check <slug>` seeks through the whole scene and writes `05_render/check.md`. `render` runs it first and stops on any non-zero counter (`--skip-check` overrides; a `--start/--end` test cut skips it).

| Counter | Means | Fix |
|---|---|---|
| page errors | the scene threw a JavaScript error | read the message in `check.md`, fix `scene.js` |
| cue warnings | `scene.js` asks for a cue id that `cues.json` does not have | fix the id, or add the cue and run `cues` |
| clock use | `Math.random`, `Date.now`, `setTimeout` ... in `scene.js` | use `P.rand(seed)` and `t`; everything is a function of time |
| nondeterministic frames | the same time drew two different pictures | find the state that survives between frames; draw from `t` only |
| text cut off | a string is partly outside the frame | move it in; keep 60 px from the edge |
| text overlaps | two strings overlap for 0.5 s or more | move one, or cut instead of cross-fading text over text |
| text too short to read | a string left before `max(0.7, 0.25 + chars / 17)` s | hold it longer or show less text |
| invented labels | a zero-padded chapter counter (`02 / 05`, `01 — THE WAIT`, `FILM 01`), a timecode (`00:01:24`), a version stamp, BPM/FPS or a frame size on screen (both engines). Scores, dates, clocks, countdowns and `CHAPTER 3` pass | remove it: the viewer does not need production metadata (`plan-check.md` S2); a real exception goes in `CHECK_IGNORE` |
| sound design missing | (brands with a quality bar) no `music:` bed, no `[sfx:]`, no `04_scene/assets/sound.md` or no licence in it (each counts 1) | do the sound-design pass (`sound.md`) |
| sound effect unknown | an `[sfx:]` name that is not built in, a malformed token, or a `file:` effect missing from `04_scene/assets/` and `library/sfx/` (every brand; render also stops) | fix the name (`sound.md`, Effects) or add the file |
| sound effect unlicensed | a `file:` effect without a line in `04_scene/assets/sound.md` that names the file, its source URL and its licence (every brand) | add the line (`sound.md`) |
| too few beats | (brands with a quality bar) no cue in the first 2 s, a gap over 5 s between cues, or a final hold over 6 s | follow the brief's scene list; add a cue and a visual change |
| brand missing | `brands/<id>/tokens.js` for the brand in `project.json` does not exist | fix the brand id, or add the brand (`brands/CONTEXT.md`) |
| brand font unlicensed | a `font`/`head` family has no `FONT-SOURCES.json` record or no local `@font-face` | add the font under `_runtime/fonts/` with its licence, or pick a licensed one |
| brand contrast | `ramp` is not 8 colours, or `ramp[0]` on `ramp[6]` reads under 4.5 | darken or lighten the ramp |
| brand grads | `grads` does not hold 5 colour pairs | fix `grads` in `tokens.js` |
| lint errors | (hyperframes) `hyperframes lint` found errors or warnings in `index.html` | read the lines in `check.md`, fix `index.html` |
| composition errors | (hyperframes) a `data-composition-src` file is missing, lies outside `04_scene/`, or mounts itself in a loop | fix the path in `index.html` or the composition |
| video vs voice length | (hyperframes) the MP4 and the voice differ by more than the limit | make the composition as long as the voice (root `data-duration`) |
| no visual layer | (hyperframes) the scene is text only: no library block, image, video, svg or canvas | add a block (`lib find`), a screen, stock or an illustration; a text video only when you want one (`"allow": ["text-only"]` in `project.json`) |
| n/a (hyperframes) | a canvas-only counter on a hyperframes video | nothing; it is not measured there |

Info lines are not failures. "music: none (warning)" means `cues.md` has no `music:` line; every video gets a bed unless you ask otherwise (`sound.md`). "Brief overlaps" are cross-fades shorter than 0.5 s. "Unmapped text" was drawn on an offscreen canvas, which the check cannot place; look at the stills for those.

A deliberate exception: `window.CHECK_IGNORE = ['exact string']` in `scene.js`, with a comment that says why and one line in `REVIEW.md`.

## 2. Video check (after render)
`render` writes `05_render/check-video.md`.
- One-frame flashes must be 0 (render stops). A flash is one frame that differs from both neighbours.
- Flat frames must be 0 (render stops): a run of more than 3 frames of one flat field (black, cream, any solid colour), frame 0 included. `--skip-check` only when it is on purpose.
- Dead stretches (over 3 s without visible change) stop the render: add motion. Only when you want it: `"allow": ["still"]` in `project.json`, noted in `REVIEW.md`.
- Format: h264, yuv420p, bt709, AAC. Loudness: against the target in `sound.md`.

## 3. Look checks
- Stills 0.3 s after each cue, so motion has settled: `anim.py stills <slug> --hold 0.3`. To step through a transition: `--at 3,3.1,3.2,3.3`. `--at` replaces the stills folder, so run plain `stills` again afterwards.
- Judge size and spacing on full-size stills, not on the contact sheet.
- Phone test: `mkdir -p videos/<brand>/<slug>/05_render/phone && ffmpeg -i videos/<brand>/<slug>/05_render/<slug>.mp4 -vf fps=1,scale=360:-2 videos/<brand>/<slug>/05_render/phone/%03d.png`. Read every word at 360 px wide.
- Three passes over the MP4: sync (sound on), motion (sound off), reading (pause on every text).
- Sound pass: `anim.py listen <slug>`, then compare the hits in `05_render/listen.md` with the cue times; a hit that trails its picture is fixed per `sound.md`. Evidence only: not a counter, it does not block render.
- Distraction test: after one watch, write down the on-screen words from memory. If you remember the motion but not the words, the motion is too loud.

## 4. Judge (the builder does not judge)
Run the `frame-critic` agent (`.claude/agents/frame-critic.md`) after stills or a render. It scores hook, readability at 360 px, motion, variety, composition, accuracy and sound sync from 1 to 10, and names the three worst problems.
- Fix those three, make new stills, run the judge again.
- Stop when every score is 8 or more, or after 3 rounds. If any score is still below 8, save `needs-attention`; do not mark the run complete.
- Never report a fix that you did not render again and look at.

## 5. Loop
Paste this to let the agent work until the scene check is clean:

```
/goal `.venv/bin/python anim.py check <slug>` reads 0 on every counter. Each round, fix the worst counter and run check again. Abort if a round fixes nothing. Stop after 5 rounds.
```

## 6. Steering rule
Capture a clear failure on its first occurrence in the run findings. Keep an uncertain observation separate. When a failure can be detected automatically, add a regression check. Add a line to "Banned defaults" in `motion.md`, or a counter to `check.py`. Brand rules and permissions need your approval. Then write `rule added: ...` in the video's `REVIEW.md`.

Managed-run evidence uses the structured contract in `.claude/agents/frame-critic.md`. Scores alone are insufficient: bind the report to current artifacts and include an actual audio review. Load verified lessons before each stage and save findings, including an explicit no-new-lesson result, afterwards.
