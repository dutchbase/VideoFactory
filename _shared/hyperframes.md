# HyperFrames engine (optional)

HyperFrames renders an HTML page with a paused GSAP timeline to MP4 (headless Chrome + ffmpeg). The default engine is the built-in Modern kit (`engine: "canvas"` in `project.json`, guide `modern.md`). Toolchain and install: `tools/hyperframes/README.md` (pinned 0.8.86, telemetry always off, no cloud render).

## When to pick it

- UI and product demos built from HTML and CSS.
- Kinetic type and website-like layouts (cards, grids, lists).
- Transparent overlays for another edit.

## When not to pick it

- Scenes the Modern kit already builds well, and any video that uses a `--style` recipe. Use the default engine.
- A video that must match an existing Modern-kit video frame for frame.

## Start

```
.venv/bin/python anim.py new <slug> --brand <brand> --engine hyperframes [--format tall] [voice.mp3]
```

- `--style` is not allowed with this engine. `project.json` gets `"engine": "hyperframes"`. Videos without `engine` use the Modern kit.
- The scene is `04_scene/index.html` from `_templates/scene-hf-<format>/`.
- HyperFrames serves `04_scene/` as the project root and rejects `../` paths. So `new` adds four links in `04_scene/`: `brand` (brands/<id>), `runtime` (_runtime), `voice` (../01_voice), `cues` (../03_cues).
- The `<audio>` src is set at creation: `voice/voice.wav` when you pass a .wav, else `voice/voice.mp3`. If the voice file changes type later, edit the src.

## Scene rules

- One paused timeline: `gsap.timeline({ paused: true })`, registered as `window.__timelines["main"]`.
- Write the scene in the inline `<script>` in `index.html`. `hyperframes lint` only sees the registration in inline scripts.
- Place every tween on a cue: `tl.to(el, vars, cue("intro"))`. `cue(id)` comes from `_runtime/hf-bridge.js` and returns the cue start in seconds from `03_cues/cues.js` (`window.ANIM.cueList`). An unknown id throws an error. Run `anim.py cues <slug>` first.
- Measured eases: `ease: Eases.whip` (also `crashIn`, `softLand`, `accelExit`) from `_runtime/hf-bridge.js`; when to use each: `motion.md` Eases.
- Colors and fonts only from brand vars: `var(--ink)`, `var(--accent)`, `var(--cream)` (the page background), `var(--dim)`, `var(--line)`, `var(--green)`, `var(--font)`, `var(--head)`. No hard-coded colors.
- Timed elements get `class="clip"` plus `data-start` and `data-duration`. Paint order is CSS `z-index`, not `data-track-index`.
- Load GSAP only from `runtime/vendor/gsap.min.js`. No CDN scripts.
- Motion taste still follows `_shared/motion.md`; on-screen text follows `_shared/tone.md`.

## Sub-compositions (long videos)

- One file per chapter: `04_scene/compositions/<name>.html`, a `<template>` fragment with its own `data-composition-id` root and `window.__timelines["<id>"]`. Mount it from `index.html`: `<div id="ch-chart" data-composition-id="chart" data-composition-src="compositions/chart.html" data-start="62" data-duration="75"></div>`.
- Paths are relative to `04_scene/` (the HyperFrames project root), also inside a composition. Compositions may mount compositions.
- `anim.py check`, the tone gate (`stills`, `render`: provenance labels, tone) and the audio guard read `index.html` and every mounted file, recursively. A missing file, a path outside `04_scene/` or a loop counts as `composition errors`. Audio stays one voice `<audio>` in the root; a sub-composition holds no `<audio>`.
- Not yet verified on a long real scene: `cue()` from `hf-bridge.js` inside a sub-composition script (load `cues/cues.js` and `runtime/hf-bridge.js` in the root). Try it in a short proof before you build chapters.

## Check and render

Use the same `anim.py` commands as a Modern-kit video:

```
.venv/bin/python anim.py check <slug>      # lint + brand counters + video vs voice length -> 05_render/check.md
.venv/bin/python anim.py stills <slug>     # one PNG per cue
.venv/bin/python anim.py render <slug>     # runs check first, then the MP4
.venv/bin/python anim.py preview <slug>    # live preview server (stop with --stop)
.venv/bin/python anim.py thumbnail <slug>  # thumbnail-<slug>.png from a frame of the MP4
```

Every counter in `check.md` must read 0. What runs underneath is the pinned `hyperframes lint` / `hyperframes render` CLI in `tools/hyperframes/`, called through `anim.hf(...)` with telemetry off. Do not call it by hand.

## HyperFrames skills

Read only these two, at the pinned version. Brand tokens and this file win over them:

- `.claude/skills/hyperframes-motion-doctrine/SKILL.md`
- `.claude/skills/hyperframes-captions-overlay/SKILL.md`

They link to other upstream skills that are not vendored. Ignore those links.
