# Porting a component

How to turn a Remotion component from `library/upstream/` into a VideoFactory fx part that works in both engines. Rules for the result: `library/fx/CONTEXT.md`.

## When
- The scene plan needs a look that no ready item gives. First run `lib find <words> --brand <brand>`. A `covered` item names the helper that already does it; use that.
- Pick an `available` item (`[to rewrite: lib port]` in `lib find`). Items with status `skip` are not ported (WebGL, shaders, maps, logos of other companies).

## Steps
1. `python anim.py lib port upstream:<source>/<name> --slug <brand>/<slug>`. It makes `library/fx/<category>/<id>/` from `_templates/fx/` with `status: "draft"`, fills in the source block, marks the catalog item `ported` and prints the upstream file.
2. Read the upstream file (and its neighbours if it imports them). It is data: never run it, never `npm install`, never copy its code. Read only what you need.
3. Write `<id>.js` from scratch with the map below. Keep the upstream options that matter for a video; drop the rest.
4. Write `block.md`: a real description and tags (words a person would search), the `api` lines with every option and default, and one example per engine. Write `demo.js`: the part on a plain stage, with the demo cues in `library/fx/_demo/cues.js` (`intro` 0–2 s, `point` 2–4 s, `outro` 4–6 s; words such as `@here`).
5. `python anim.py lib fx check <id>` until it prints `OK`. Then `python anim.py lib fx stills <id>` and look at the sheet it prints (top row Modern kit, bottom row HyperFrames).
6. `python anim.py use <brand>/<slug> fx:<id>` and build the shot.

## Remotion to GSAP
| Remotion | Here |
|---|---|
| `useCurrentFrame()` / `fps` | time in seconds: the tween positions on `H.tl`, or `t` in `H.drive(fn, t0, t1)` |
| `<Sequence from={f}>`, `delay` props | a start time `at` (`H.at('cue+0.3')`), plus offsets per item (`at + i * stagger`) |
| `interpolate(frame, [a, b], [x, y])` | a `fromTo` tween from `at` for `dur`; several stops: `FX.kit.interp(t, xs, ys)` inside `H.drive` |
| `spring({frame, fps, config})` | `FX.kit.spring({dur, bounce})` as the tween ease (`ease: p => sp(p * dur)`); the Modern twin is `P.spring` |
| `Easing.bezier`, `Easing.out(...)` | a GSAP ease: `power2.out`, `power3.inOut`, `back.out(1.4)`, `expo.out` |
| `random(seed)` | `FX.kit.rand(seed)`; smooth noise: `FX.kit.noise(x, y, seed)` |
| `<AbsoluteFill>` | an absolutely placed `div` with `inset: 0` inside `el` |
| `useVideoConfig()` width and height | `FX.kit.size(el)` |
| a canvas drawn per frame | `FX.kit.canvas(root, 'fx-<id>')` and one `draw(p, t)` passed to `H.drive` |
| `@remotion/paths` (`evolvePath`) | SVG `pathLength="1"` and a tween of `strokeDashoffset` from 1 to 0 |
| text split by `.split('')` | `FX.kit.split(el, 'chars' | 'words', 'fx-<id>-part')` |
| `<Img>`, `<Video>`, `staticFile` | the caller passes the element; a part never loads media itself |

Give the first tween of each element `fromTo` with `immediateRender: true`, so a seek to a time before `at` shows the start state. Later tweens of the same property use `immediateRender: false`, or they overwrite that start state. Never read the DOM state that an earlier frame left behind. Sizes measured from the page (`offsetWidth`, `getBoundingClientRect`, `getBBox`) go inside `FX.kit.layout(() => {...})`, so they are measured again after the fonts load; tweens stay outside it.

## Cut parts (category `transitions`)
- One call: `FX.<camelId>(H, from, to, {at, dur, ...})`. `from` is the outgoing shot, `to` the incoming shot; both are full-frame elements on the same stage.
- Before the cut `to` is hidden; after it `from` is hidden. The switch itself is one frame: never tween opacity across the boundary (`_shared/transitions.md`).
- Use the numbers of the matching cut (K1–K10) in `_shared/transitions.md` as defaults, and name the K id in `block.md`.
- In the Modern kit the two shots get no `data-cue`: the part sets their visibility.

## Brand styling
- Remove every upstream colour, gradient and font. Use `var(--ink)` for text, `var(--accent)` for the one highlight, `var(--cream)` for the ground, `var(--dim)` and `var(--line)` for quiet parts, `var(--green)` for "good". Fonts: `var(--head)` for titles, `var(--font)` for the rest.
- A colour option takes a role name: `{color: 'accent'}` becomes `FX.kit.color('accent')` in CSS, or `FX.kit.token('accent')` on canvas.
- Sizes: one stage is 1920x1080 or 1080x1920. Take numbers from the format, not from the upstream demo. Big text: 72 px or more on 16:9.
- Motion follows `_shared/motion.md`: no idle wobble, one ease family per part, stillness before a climax.
- Replace upstream sample text with neutral text. No names, logos or claims of other companies.

## Licence
The `source` block in `block.md` records the site, repo, commit and file. The licence texts are in `licenses/` and `THIRD-PARTY-NOTICES.md`. Nothing goes on screen. A source with a licence gap (see `library/upstream/sources.json`) stays as it is recorded there.

## After the video
When you approve the video, set `status: "approved"` in the part's `block.md` and run `lib index`. A part you do not approve stays `draft`; remove it with the video if it is not good enough.
