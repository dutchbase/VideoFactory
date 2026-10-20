# 05 Export and review

After preview approval, `python anim.py render <slug>` writes an H.264/AAC MP4. The render starts at once; there is no queue or time window. To test a segment use `--start 0 --end 5 --workers 1`. `--phone` also writes a smaller copy. Check its real size and readability.

Make the thumbnail before the final render. `04_scene/thumbnail.*` are scene and audio inputs, so adding them afterwards makes the scene check and the audio check stale. The same holds for edits to `anim.py`. Edit `thumbnail.js`, then run `python anim.py thumbnail <slug>`. `python anim.py chapters <slug>` prints the top-level cue times as chapter lines. Write `DESCRIPTION.md` with accurate sources and the disclosures your platform needs.

Render runs the check first, masters the audio (`_shared/sound.md`) and writes `check-video.md`. Run the phone test and the `frame-critic` judge (`_shared/review.md`) before you watch.

Each export also writes `<slug>.render.json` with the Chromium version, connection, frame size, FPS, worker count, frame count and elapsed time. Browser-per-worker rendering is the default. A benchmark of isolated 1920x1080 capture found identical frames but a slower shared-browser median at four workers (4.013 s against 3.252 s). Re-run `tests/benchmark_render_browser.py` in a clean environment before you change that design.

Watch the MP4 with sound. Check the first and last frames, captions, layout and timing. Export success is not content approval. This package does not upload, schedule or publish.

Before the render review, save phone frames under `05_render/phone/` and an independent judge record at `05_render/frame-critic.md`. The record holds the reviewer, the date, scores for hook, 360 px readability, motion, variety, composition, accuracy and sound sync, and the three worst problems (or an explicit "none"). Studio can request `review-checks` agent work when these are missing. Then mark the `render` gate ready and open its exact Studio review link (`_shared/dashboard-review.md`). You watch the current export before you approve.

Audio input and balance follow `_shared/sound.md`. Effects need separate voice and effects tracks and corrected word timings. Render limits the summed effects and checks the written stem before it replaces the export. Each export writes `check-audio.md`. The Studio render review requires a current passing report (or an explicit no-effects result). Listen on headphones and on a phone speaker before you approve. A manual premix, or extra HyperFrames audio, cannot bypass this gate.

For a brand with a quality bar, render runs the check, so a missing sound-design pass (`sound design missing`) or sparse cues (`too few beats`) stops it. Copy the music and effect credits from `04_scene/assets/sound.md` into `DESCRIPTION.md`.

Managed runs may render when ready under their saved settings. They still need current checks and independent review evidence before completion. Managed review requires seven scores of at least 8, current artifact hashes, evidence from the actual rendered audio and no blocking issue. After three unsuccessful repair rounds, or when evidence is missing, the run needs attention (`_shared/autonomous-runs.md`).

Guided command: `/vf-render`.
