# Modern kit: how to write a scene

The built-in look. A scene is one HTML page (`04_scene/index.html`) plus an optional `scene.js`.
Files: `_runtime/modern.css` (the look), `_runtime/modern.js` (helpers), `_runtime/player.js` (the clock, `P`).
Colours and fonts come from `brands/<id>/tokens.js`; never type a hex colour in a scene, use `var(--accent)` and friends.

## How time works
The voice drives everything. `03_cues/cues.js` holds the cue times. The player sets one time `t` per frame and
everything visible is a pure function of `t`, so preview, stills and render always match.
A **time** in any helper or attribute is one of:

| Write | Means |
|---|---|
| `hook` | start of cue `hook` |
| `hook+0.4` / `hook-0.2` | cue start plus or minus seconds |
| `@percent` | the moment the voice says the first word that starts with "percent" |
| `@percent>stat` | the first "percent" after cue `stat` starts |
| `2.5` | seconds from the start |

## Page skeleton (from `_templates/scene-modern-wide/`)
```html
<div id="stage" data-width="1920" data-height="1080">          <!-- tall: 1080 x 1920 -->
  <div class="vf-bg"><div class="vf-glow"></div><div class="vf-glow two"></div></div>
  <section class="vf-shot" data-cue="hook"> … </section>         <!-- one shot per idea -->
  <section class="vf-shot" data-cue="problem" data-until="fix"> … </section>
  <div class="vf-captions"><p></p></div>                          <!-- live captions from words.json -->
  <div class="vf-progress"></div>
</div>
```
- A `.vf-shot` with `data-cue` is visible while its cue is live (until the cue ends, or until cue `data-until` starts).
  A shot without `data-cue` is always visible.
- Shot layouts: default (left, stacked), `center`, `split` (two columns; stacks on tall).
- Scripts at the end of `<body>`, in this order: `cues/cues.js`, `brand/tokens.js`, `runtime/vendor/gsap.min.js`,
  `runtime/player.js`, `runtime/icons.js`, `runtime/modern.js`, then `scene.js`.
- Animated icons: `runtime/animicon.js` plus the icon wrappers (`assets/icons-animated/<set>/<name>.js`) load before `runtime/modern.js`.

## Entrances without code
Put attributes on any element inside a shot:

| Attribute | Effect |
|---|---|
| `data-in="rise"` | entrance at the shot's cue start. Kinds: `rise fade pop left right drop zoom blur wipe words chars` |
| `data-delay="0.4"` | seconds after the shot start |
| `data-at="@money"` | own time instead of the shot start (any time form above) |
| `data-stagger` / `data-stagger="0.2"` | animate the children one by one |
| `data-out="sink"` | exit that ends when the shot ends. Kinds: `fade sink shrink blur`. `data-out-at` sets a time |
| `data-count="87%"` | count up to the number (prefix and suffix kept) |
| `data-type` | typewriter with a caret |
| `data-draw` | draw SVG strokes |
| `data-grow` on `.vf-bars` | bars grow to their `--v` value |
| `data-icon="rocket"` on `<i>` | inline icon in the text colour (`python anim.py lib find <word>`) |
| `data-play="@bell"` on `<i data-icon="lucide-animated/bell">` | animated icon: plays at that time (any time form; empty = shot start). `data-loop="1"` repeats it, `data-gap`, `data-speed` tune it |
| `data-brand="name"` | text from the brand tokens |

One entrance moment per shot is usually enough. Animate what the voice says, when it says it.

## Building blocks (classes)
- Type: `vf-kicker` (mono label), `vf-hero`, `vf-title`, `vf-h2` (`<em>` = accent, `<i>` = second accent),
  `vf-sub`, `vf-small`, `vf-hand` (handwritten note), `vf-grad` (gradient text), `vf-hl` (marker highlight), `vf-strike`.
- Surfaces: `vf-card` (+ `hot`, `glass`) inside `vf-cards` (`style="--cols:2"`), `vf-chip` (+ `hot`, `ok`),
  `vf-tile` (+ `two`) for an icon in a rounded square.
- Data: `vf-stat` (`<b>` number + `<span>` label), `vf-bars` with `vf-bar` rows (`style="--v:.7"`).
- Sequences: `vf-list` (`<li>` with an icon), `vf-steps` with `vf-step` (+ `on`), `vf-quote` + `<cite>`.
- Screens: `vf-browser` (`.top` with three `<i>` dots, `.url`, then `<img src="assets/x.png">`), `vf-code` (`<pre>`,
  spans `.k .s .c .n`), `vf-term`, `vf-phone`.
- Layout: `vf-row`, `vf-col`. Brand: `vf-logo` (`<img src="brand/logo/mark.svg">`).
- Background: `vf-bg` with one or two `vf-glow`. Add `grid` or `dots` only when the lines do a job (a chart, a map); as decoration they are slop sign S10 in `_shared/plan-check.md`.

## scene.js: timed parts in code
```js
const tl = P.timeline();                                  // a paused GSAP timeline on the scene clock
Modern.in(tl, '#card', 'problem+0.2', 'pop');              // entrance (kinds as data-in)
Modern.out(tl, '#card', 'fix-0.4', 'sink');                // exit
tl.to('#arrow', { rotate: 90, duration: 0.6, ease: P.ease.move }, Modern.at('turn'));   // any GSAP tween
Modern.count('#stat b', '@percent', 87, { suffix: '%' });  // count up
Modern.type('#prompt', 'demo+0.5', { cps: 30 });           // typewriter
Modern.draw('#path', 'map', { dur: 1.4 });                 // draw an SVG
Modern.push('#hero', 'hook');                              // slow camera push over the cue
Modern.clip('#screen', 'signup', 'demo');                  // play a clip: anim.py record, or use with stock: / motion:
Modern.clip('#screen', 'signup', 'demo', { from: 1.2, speed: 1.4 }); // skip 1.2 s of empty intro, play faster
P.onFrame((t) => { el.style.opacity = P.fade('aside'); }); // anything else: a pure function of t
```
- Eases: `P.ease.enter` (fast in, soft landing), `exit`, `move`, `pop`, `out`, `inOut`, `outExpo`, `back`, `sine`,
  and the measured `crashIn`, `whip`, `softLand`, `accelExit`. `P.spring({dur, bounce})` for springs.
- Cue maths: `P.cue(id)`, `P.prog(id, {dur, delay})`, `P.fade(id)`, `P.live(id)`, `P.past(id)`, `P.pick({id: value})`.
- Never use `setTimeout`, `setInterval`, `Date.now()` or `Math.random()`: the render jumps between frames.
  Use `t`, cue times and `P.rand(seed)`.
- GSAP callbacks (`onComplete`, `onUpdate`) do not fire while the clock jumps. Put per-frame code in `P.onFrame`.

## Pictures and other assets
- `python anim.py use <slug> <ref>` copies a library item into `04_scene/assets/`; then `<img src="assets/…">`.
- Screenshots: `python anim.py grab <slug> <url> <name>`; recordings: `python anim.py record …` (see `_shared/capture.md`).
- Motion-pack and stock video clips: `python anim.py use <slug> motion:<brand>/<ID> --as <name>` or `stock:...`, then `Modern.clip` (`_shared/library.md`).
- Every image must load. A missing file stops the render with a clear error.

## Formats and safe areas
- Wide 1920 x 1080: content padding 120 px top and bottom, 160 px left and right. Captions sit 64 px above the bottom.
- Tall 1080 x 1920: 240 px top and bottom for platform buttons, 90 px left and right, captions 420 px above the bottom.
- Text sizes switch automatically with the format. Keep at most about 12 words on screen per shot.

## Check your scene
`python anim.py preview <slug>` (live, scrub with the bar), `python anim.py stills <slug>` (one picture per cue),
`python anim.py check <slug>` (text off screen, overlaps, missing cues). Fix every finding before `render`.
