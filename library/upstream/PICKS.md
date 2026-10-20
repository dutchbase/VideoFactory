# Picks: the components we rewrite first

50 picks in 5 batches, plus 12 reserves. Edit surface: change `[x]` to `[ ]` to drop a pick, or `[ ]` to `[x]` to add a reserve. The port run reads only the `[x]` lines.

How they were chosen: the same effect exists on two or more sites, or the site marks it as featured; it fits an explainer (text, entrances, cuts, data, interface); no existing helper does it already (`covered` in `<source>.json`); difficulty easy or medium; it follows `_shared/motion.md` (no particle bursts, no glow on interface chrome) and `_shared/transitions.md` (one-frame cuts, no cross-fades).

Each line: the upstream ref, the fx id it becomes, category and difficulty, what it does, and where else the same effect exists.

## Batch 1. Text

- [x] `upstream:remotionui/matrix-decode` → `fx:matrix-decode` (text, easy). Scrambled glyphs resolve left to right into the word. The AI and tech beat. Also in: onda.
- [x] `upstream:remotionui/tracking-in` → `fx:tracking-in` (text, easy). Letters close in from wide spacing. A calm title entrance. Also in: onda.
- [x] `upstream:remotionui/masked-slide-reveal` → `fx:masked-slide-reveal` (text, easy). Words rise through a line mask. Editorial headline (mask needs bottom padding for descenders).
- [x] `upstream:remotionui/stroke-to-fill-text` → `fx:stroke-to-fill-text` (text, easy). An outline word fills solid. One big statement word.
- [x] `upstream:remotionui/strikethrough-replace` → `fx:strikethrough-replace` (text, easy). Strike out one phrase, put the right one in its place. The "not X, but Y" beat (K10).
- [x] `upstream:remotionui/slot-roll` → `fx:slot-roll` (text, easy). Characters roll like a slot reel and land. Numbers and names that tick through. Also in: onda.
- [x] `upstream:onda/shimmer-sweep` → `fx:shimmer-sweep` (text, easy). One band of light passes over a key word. Also in: remotionui.
- [x] `upstream:onda/rgb-glitch-text` → `fx:rgb-glitch-text` (text, easy). Red and cyan copies split off and snap back. A short tech or error moment. Also in: remotionui.
- [x] `upstream:remotionui/marker-highlight` → `fx:marker-highlight` (text, medium). A highlighter stroke sweeps word by word. Modern has a static `vf-hl`; this one moves and works in HyperFrames too. Also in: onda.
- [x] `upstream:onda/underline` → `fx:underline` (text, easy). A drawn underline under the key words.
- [x] `upstream:onda/marquee` → `fx:marquee` (text, easy). A seamless ticker band of words (no logos). Also in: remotionui.
- [x] `upstream:remotionui/handwriting-text` → `fx:handwriting-text` (text, easy). A handwritten note draws on, stroke by stroke.

## Batch 2. Entrances and emphasis

- [x] `upstream:remotionui/spring-in` → `fx:spring-in` (entrances, easy). Scale and rise on a spring with snappy, smooth and bouncy presets.
- [x] `upstream:onda/rotate-in` → `fx:rotate-in` (entrances, easy). Text settles from a slight rotation on a calm spring. Also in: remotionui.
- [x] `upstream:remotionui/skew-in` → `fx:skew-in` (entrances, easy). Skew plus slide. Editorial feel for labels and lists.
- [x] `upstream:onda/mask-reveal` → `fx:mask-reveal` (entrances, easy). Text is uncovered by a mask that moves away.
- [x] `upstream:remotionui/shake-emphasis` → `fx:shake-emphasis` (entrances, easy). A short impact shake. The "this is wrong" beat.
- [x] `upstream:remotionui/orbit-motion` → `fx:orbit-motion` (entrances, easy). Items circle a centre. Ecosystems, "everything around X".
- [x] `upstream:remotionui/motion-trail` → `fx:motion-trail` (entrances, easy). Echoes behind a fast object. A carrier for match cuts (K2).

## Batch 3. Cuts (only the kinds `_shared/transitions.md` allows; no cross-fades)

- [x] `upstream:onda/wipe` → `fx:wipe` (transitions, easy). Soft-edged wipe in B's ground colour (K5). Also in: remotionui.
- [x] `upstream:remotionui/transition-circle-reveal` → `fx:circle-reveal` (transitions, easy). A circle opens from a point, for example a pressed button (K5). Also in: onda iris.
- [x] `upstream:remotionui/transition-whip-pan` → `fx:whip-pan` (transitions, easy). Fast pan with motion blur and a content change inside the move (K7).
- [x] `upstream:remotionui/zoom-through` → `fx:zoom-through` (transitions, easy). Blur-matched zoom into the next scene (K4). Also in: onda zoom.
- [x] `upstream:onda/device-pullback` → `fx:device-pullback` (transitions, easy). Full-screen UI pulls back into its device (K6).
- [x] `upstream:onda/expand-morph` → `fx:expand-morph` (transitions, easy). A small card grows into the next scene (K3 container replacement).
- [x] `upstream:remotionui/transition-blinds` → `fx:blinds` (transitions, easy). Slats sweep open in a stagger (K5 variant).
- [x] `upstream:onda/grid-pixelate` → `fx:grid-pixelate` (transitions, easy). The scene breaks into cells that flip in a seeded order (K5 variant). Also in: remotionui.

## Batch 4. Data

- [x] `upstream:onda/progress-bar` → `fx:progress-bar` (data, easy). A pill bar fills to a value. Also in: remotionui.
- [x] `upstream:onda/pie-reveal` → `fx:pie-reveal` (data, easy). A ring fills to a percent. "73 % of people ..."
- [x] `upstream:remotionui/donut-chart` → `fx:donut-chart` (data, medium). Several segments with labels.
- [x] `upstream:remotionui/comparison-bars` → `fx:comparison-bars` (data, easy). Before and after, with the change called out.
- [x] `upstream:remotionui/funnel-chart` → `fx:funnel-chart` (data, easy). Stages that narrow, with drop-off numbers.
- [x] `upstream:remotionui/gauge-dial` → `fx:gauge-dial` (data, easy). A needle sweeps to the target.
- [x] `upstream:onda/line-chart` → `fx:line-chart` (data, easy). A line draws left to right, with points. Also in: remotionui.
- [x] `upstream:onda/timeline` → `fx:timeline` (data, medium). Dates or steps appear along a line. Also in: remotionui timeline-steps.
- [x] `upstream:remotionui/sparkline-row` → `fx:sparkline-row` (data, easy). Small trend lines that read at a small size.

## Batch 5. Backgrounds, shapes, camera, interface, scenes

- [x] `upstream:onda/mesh-gradient` → `fx:mesh-gradient` (backgrounds, easy). Soft colour blobs drift slowly (never under a centred title: banned default). Also in: remotionui.
- [x] `upstream:onda/dynamic-grid` → `fx:dynamic-grid` (backgrounds, easy). A technical grid that drifts. Also in: remotionui.
- [x] `upstream:remotionui/animated-noise-grain` → `fx:animated-noise-grain` (backgrounds, easy). Film grain over the whole frame. Also in: onda grain-overlay.
- [x] `upstream:remotionui/arrow-annotate` → `fx:arrow-annotate` (shapes, easy). A hand-drawn arrow points at a target.
- [x] `upstream:onda/callout` → `fx:callout` (shapes, medium). A box and a label point at one part of a screen. Also in: onda bounding-box.
- [x] `upstream:remotionui/svg-mask-reveal` → `fx:svg-mask-reveal` (shapes, easy). Any SVG shape opens as a reveal mask.
- [x] `upstream:remotionui/connector-lines` → `fx:connector-lines` (shapes, easy). Lines draw between boxes. Flows and systems. Also in: onda node-graph.
- [x] `upstream:onda/ken-burns` → `fx:ken-burns` (cinematic, easy). Slow zoom and pan over a photo.
- [x] `upstream:onda/camera-shake` → `fx:camera-shake` (cinematic, easy). A short camera shake on impact.
- [x] `upstream:onda/spotlight` → `fx:spotlight` (cinematic, easy). Everything dims except one area of a screen. Also in: remotionui callout-spotlight.
- [x] `upstream:onda/terminal` → `fx:terminal` (interface, easy). Commands type out in a terminal and print their result. Also in: remotion-bits, remotionui.
- [x] `upstream:onda/code-block` → `fx:code-block` (interface, easy). Code appears line by line with highlighting in brand colours. Also in: remotion-bits.
- [x] `upstream:remotionui/notification-stack` → `fx:notification-stack` (interface, medium). Notifications stack up on a screen.
- [x] `upstream:onda/stat-card` → `fx:stat-card` (scenes, easy). A big number counts up above its label. Also in: remotionui.

## Reserves

- [ ] `upstream:remotionui/neon-flicker-text` → `fx:neon-flicker-text` (text, easy). Neon flicker then settle.
- [ ] `upstream:curvable/curvable-types` → `fx:curvable-types` (text, easy). First word zooms in big and blurred.
- [ ] `upstream:remotionui/parallax-layers` → `fx:parallax-layers` (entrances, easy). Layers move at different depths.
- [ ] `upstream:remotionui/squash-stretch` → `fx:squash-stretch` (entrances, easy). Playful landing of an object.
- [ ] `upstream:onda/clock-wipe` → `fx:clock-wipe` (transitions, easy). Clock-hand wipe.
- [ ] `upstream:onda/glass-wipe` → `fx:glass-wipe` (transitions, easy). Wipe behind a frosted-glass edge.
- [ ] `upstream:remotionui/bar-chart-race` → `fx:bar-chart-race` (data, easy). Ranked bars reorder over time.
- [ ] `upstream:remotionui/heatmap-grid` → `fx:heatmap-grid` (data, easy). Cells fill by intensity.
- [ ] `upstream:remotionui/topographic-lines-bg` → `fx:topographic-lines-bg` (backgrounds, easy). Contour lines drift.
- [ ] `upstream:onda/lower-third` → `fx:lower-third` (scenes, easy). Name and role bar.
- [ ] `upstream:onda/progress-steps` → `fx:progress-steps` (interface, easy). Step 1, 2, 3 indicator.
- [ ] `upstream:remotion-bits/staggered-motion` → `fx:staggered-motion` (entrances, easy). Stagger with transforms (data-stagger covers most).

## Left out on purpose

- Cross-fades and dips (`onda/cross-fade`, `onda/dip-to-color`, `onda/blur`, `onda/morph`, `remotionui/transition-fade`): `_shared/transitions.md` allows no cross-fade between scenes.
- Confetti and particle bursts (`onda/confetti`, `remotionui/confetti-burst`): banned default in `_shared/motion.md`.
- `remotionui/glow-pulse`: glow on interface chrome is a banned default.
- Fading word rotators (`onda/word-rotate`, `onda/text-fade-replace`): K10 replaces words in one frame; `slot-roll` and `strikethrough-replace` do it right.
- WebGL, shaders, maps and 3D: status `skip` in the catalog.
