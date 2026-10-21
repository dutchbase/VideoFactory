# Frame critic: what-is-videofactory

- Reviewer: frame-critic agent (not the builder)
- Date: 2026-10-21
- Brand: videofactory (frozen `settings.json` brand sources read)
- Judged: `05_render/what-is-videofactory.mp4` (215.36 s) through the 9 phone contact sheets `phone/sheet_01..09.png`, the stills sheets in `sheets/`, `check.md`, `check-video.md`, `check-audio.md`, `03_cues/cues.md`, `03_cues/cues.json`, and a few single phone frames (008, 032, 059, 073, 085, 096, 103, 124, 152, 157, 184, 196).
- Listening: NOT done. No listening tool is installed. Sound sync is judged from `check-audio.md` (effect times against word windows) and from the picture times only.

## Scores (1 to 10)

| Criterion | Score | Evidence |
|---|---|---|
| Hook | 8 | `phone/sheet_01` 0:00 shows the headline "An explainer video usually means"; the Editor / Timeline / Audio chips are in at 0:01; the strike and the orange "a lost weekend" land at 0:04-0:05 on the `error` hit (4.24 s). Frame 0 is a lone line on a near-empty frame, and the strike lands about 2 s later than the brief's "1 to 2 s". |
| 360 px readability | 8 | Headlines, bottom captions, terminals and cards read at 360 px (frames 032, 085, 096). Small stuff fails: hex codes at 1:12-1:16, the motion-pack clip at 2:30-2:32 (about 5 px text), the status header row at 3:13-3:15, and all text inside the Wikipedia and Studio screenshots (proof only). |
| Motion | 8 | Smooth, no bounce, no drift. Words reveal one by one (0:19 "What you need", 1:45 "/vf-script"). Weak spots are short gaps at chapter changes: 0:09 (faint folder card only), 1:45, and 2:50 (render panel almost empty). Brand motion "enter fast, land soft" is followed. |
| Variety | 8 | Something new every 1-4 s across 74 cues. Terminals, chips, grid, waves, stock photo, Wikipedia page, Studio pages, status table, stamps. Mild loss: 1:17-2:59 reuses one frame (orange "/vf-x" verb headline on top, card under, caption below). |
| Composition | 8 | Text sits inside the safe area; one focus per frame in most shots. Captions at about 90 % height stay clear of the edge. Top-heavy frames with an empty lower half: 1:12-1:16 (logo and swatches), 2:00-2:02. The headline and the caption repeat the same words at 0:00-0:05 and 0:10-0:18. |
| Accuracy | 8 | Real material is used: doctor rows (0:31), real status table (3:13-3:15), real Studio pages (2:01-2:04, 3:05-3:11), Wikipedia grab with a "Source: Wikipedia" chip (1:44), chapter times 0:19 / 1:09 / 2:14 / 2:50 equal the whoosh times in `check-audio.md`, brainstormform URL is in the repo README. Minor: counters 5 / 6 / 1 at 2:45 are not from a real run; "Unlock your productivity" and "Move the invoice..." (1:49-1:53) are authored although the brief says "Authored examples: none"; stage names differ between 0:17 ("Words") and 3:17 ("script"). |
| Sound sync | 7 | Not heard, so capped. `check-audio.md`: 40 effects, 253 windows, 0 violations, smallest distance 13.0 dB (needs 12), -14.4 LUFS, -1.1 dBTP. Effect times equal cue start times (for example stamp 85.72 s with the stamps on `phone/sheet_04` 1:26, chime 33.9 s with the test-video card at 0:34, error 4.24 s with the strike). Two offsets seen: the `chime` at 167.94 s fires on "every" while the last counter reaches 0 at about 2:48.5-2:49; the `riser` at 207.22 s starts at the moment the end-card logo lands (3:27), so its build peaks after the picture, not into it. "Listening review: pending" in `check-audio.md`. |

## Slop signs seen (plan-check part B)

- S3 (borderline, brand layout): 0:36-0:58 (`phone/sheet_02` and `sheet_03`): grid on the left, headline with a small sub-line on the right ("An advanced animation engine / HyperFrames", "Questions as a form in your browser / github.com/...").
- S6: 1:17-2:59 (`phone/sheet_04` to `sheet_07`): "/vf-x" verb headline on top, one card, caption at the same place, many times. The pipeline order and the brief explain it, but the frame formula repeats.
- S2 (borderline): 3:17-3:23 (`phone/sheet_09`): six-segment hairline under "One step. Then it stops." It carries meaning (the pipeline), so it is not an invented counter (`check` invented labels = 0).
- S15 (minor): `sheets/sheet_05.png` check.count 02:45.3 (counters 5 / 6 / 1); `phone/sheet_05` 1:49-1:53 (hype example copy).
- Not counted: bottom caption pinned all video (live captions are in the brief), two background glows (brand), mono caps chips "FREE CC0 FILES" and "FREE / OPEN SOURCE / MIT" (brand label style).
- S1, S4, S5, S7, S9, S10, S11, S12, S13, S14: none.

## Three worst problems

1. Tiny proof text in the motion-pack and status shots. File `04_scene/scene.js` (and `04_scene/motion/VID-01.dc.html`), cues `scene.motion` (2:30-2:33), `status` (3:13-3:15), `brand.new` (1:12-1:16). Fix: scale the motion-pack clip up to fill the card or crop to its key frame (the panel is mostly dark and empty), enlarge the status header row and hide the hex codes or double them. Rule: `motion.md` Type and Reading time; `review.md` phone test.
2. Two effects off their picture. File `03_cues/cues.md`: `check.zero` `[sfx: chime]` should land when the last counter reaches 0 (about 168.7 s, on "zero"), not on "every" at 167.94 s. `cta` `[sfx: riser]` should start about 1.5 s before 207.22 s so it ends on the logo (use the tail of `reveal`). Then listen to the new MP4 (or run `anim.py listen`). Rule: `motion.md` "hits land on the word", `sound.md`.
3. Empty gaps at chapter changes and one repeated frame formula. File `04_scene/scene.js`, cues `turn` to `what` (0:09), `script` (1:45), `render` (2:50). Fix: overlap the exit and the next entrance (zoom-through or cut) so no frame holds only a faint ghost card. Vary the frame for two or three of the 1:17-2:59 chapters (for example a centred object with the command inside it). Rule: `motion.md` Cuts "never exit, show a gap, then enter"; plan-check S6.

## Video message from the frames alone

VideoFactory turns a chat with an AI agent into a finished, branded explainer MP4: you need only Linux, Python, FFmpeg and Claude Code or Codex, everything else is optional, each `/vf` command does one step and waits for your clear yes, and the viewer should clone the repo and run `/vf-setup`. This matches the brief's outcome (every command, required vs optional, one conversation gives a branded MP4). The command `/vf-render` is only spoken and shown late (3:26 chips), not as its own terminal line.

## Verdict

Strong, clear, consistent explainer; six criteria score 8 or more. It is needs-attention only because sound sync is unheard (7): fix the chime and riser times, listen to the final MP4, then score again.
