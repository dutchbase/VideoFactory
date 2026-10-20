# VideoFactory motion pack

89 animation assets for the VideoFactory brand: device frames, AI interfaces, kinetic type, transitions, overlays, counters, captions, players, backgrounds. Each asset is one page, `<ID>.dc.html`, 6 s loop at 30 fps, in 16:9, 9:16 and 1:1.

**Reads:** `manifest.json` (source of truth: id, name, section, type `scene|device|overlay|transition|background`, formats), `<ID>.dc.html`, `motion.css` (brand colours and fonts as `--vf-*` variables, defined once), `support.js` (generated runtime), `image-slot.js`.
**Does:** `tools/motion.py` serves the pack and renders clips. Time is driven by `window.smai.seek(t)`, never by a wall clock. Everything loads offline: React from `vendor/`, fonts from `_runtime/fonts/`.
**Writes:** `library/cache/motion/` (git-ignored): clips and `contact-sheet.png`.
**Human check:** watch the clip or the contact sheet. Sample text in assets (B2B-02, DAT-*, TYP-06, and so on) is placeholder: replace it with approved claims before you publish.

## Browse
```
.venv/bin/python tools/motion.py serve --brand videofactory
```
Open `http://127.0.0.1:8791/Index.dc.html`. Do not open the pages through `file://`.

## Render
Output goes to `library/cache/motion/` and is named `<ID>_<format with x>_<dur>s[_alpha].<ext>`.
```
.venv/bin/python tools/motion.py render --brand videofactory --id AIM-05 --format 9:16
.venv/bin/python tools/motion.py render --brand videofactory --id CAP-01 --format 9:16 --transparent   # .mov (ProRes 4444) + .webm (VP9 alpha)
.venv/bin/python tools/motion.py render --brand videofactory --id all --format all --jobs 3
.venv/bin/python tools/motion.py sheet --brand videofactory                                           # contact-sheet.png, frame at t=3.0
```
Options: `--dur 1-60` (longer than 6 s holds the end state and plays the exit at the end), `--fps`, `--no-out` (no exit), `--outDir`, `--img URL|FILE`.
Always render overlays (`type: overlay`) with `--transparent`.

## Page query parameters
`format`, `dur`, `out=0`, `clean=1`, `transparent=1`, `t`, `play=1`. API: `window.smai.ready/seek/duration/fps/play/pause/setAsset`.

## Image slots
`DEV-04`, `DEV-05`, `B2B-02` and `UTL-05` use `<image-slot>`. `--img <url or file>` swaps `image-slot.js` for a plain cover image while rendering. The files stay unchanged.

## Edit text and timing
Text is plain HTML. Typed text uses `data-text`. Timing uses CSS `animation-delay` in seconds and `data-start`. The loop is 6 s and the exit runs from 5.46 s to 6 s. To change a colour, edit the `--vf-*` variables in `motion.css`.

## Use in a video
In a Modern scene: `python anim.py use <slug> motion:videofactory/<ID> --as <name>` renders the clip in the video's format (cached) and makes frames in `04_scene/assets/<name>/`. Play it with `Modern.clip('#el', '<name>', '<cue>')`. Overlays need transparency, so use them in an editor or a HyperFrames scene (`_alpha.mov` / `.webm`). Do not embed the live HTML.

## Licence
The assets are own work, made with Claude Design, and released under the MIT licence of this repository. React 18.3.1 and ReactDOM 18.3.1 in `vendor/` are MIT licensed (see `vendor/LICENSE` and `vendor/SOURCES.json`). The fonts in `_runtime/fonts/` are under the SIL Open Font Licence (see the `OFL.txt` next to each font).
