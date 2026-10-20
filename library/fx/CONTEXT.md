# library/fx: animated parts for both engines

Text effects, entrances, backgrounds, charts and other parts that work in the Modern kit and in HyperFrames. Most are rewritten from the open-source component sites in `library/upstream/` (never copied). One folder per part: `fx/<category>/<id>/`; the category comes from `library/categories.json`.

**Reads:** `<category>/<id>/block.md` (frontmatter: id, title, description, tags, kind `fx`, engine `both`, status, files, depends, api, preview_at, source), `<id>.js`, `<id>.css`, `demo.js`. Shared helpers: `_kit/kit.js` (`FX.kit`). Timeline helpers: `library/blocks/core/core.js` (`H`).
**Does:**
- Find: `python anim.py lib find <words> --kind fx --brand <brand>`. Overview of all categories: `library/CATALOG.md`.
- Look: open `_demo/modern.html?fx=<category>/<id>` or `_demo/hf.html?fx=<category>/<id>` (both engines, same demo). `python anim.py lib gallery` writes `GALLERY.html`, grouped by category.
- Use: `python anim.py use <slug> fx:<id>` copies the part, the kit and `core` into `04_scene/fx/` and `04_scene/blocks/`, logs it, and prints the script lines and the `H` line for the video's engine.
- Add: `python anim.py lib port upstream:<source>/<name> [--slug <video>]` (`_shared/porting.md`).
**Writes:** nothing in videos by itself. `_demo/parts.js` and `GALLERY.html` are generated: never edit them.
**Human check:** you look at the demo in both engines. You approve a draft part together with the video it was made for.

## Rules for a part
- One call per part: `FX.<camelId>(H, el, {at, ...})`. `at` (and `from`/`to`) take any time `H.at` reads: seconds, `"cue+0.4"` or `"@word"`.
- Every motion is a tween on `H.tl`. Per-frame drawing (canvas, particles, noise) goes through `H.drive(fn, t0, t1)`; `fn(p, t)` redraws everything from `p` and `t` alone.
- The same time gives the same picture, also when seeked out of order. No `Math.random` (use `FX.kit.rand(seed)`), no `Date`, timers, `requestAnimationFrame`, `onUpdate`/`onComplete` or network loads.
- Colours and fonts only from the brand: CSS `var(--ink|--accent|--cream|--dim|--line|--green|--font|--head)`, on canvas `FX.kit.token('accent')`. Colour options take a role name (`'accent'`), never a hex value. Black or white with alpha for shadows is allowed.
- Measure the page (text width, a target's box) only inside `FX.kit.layout(place)` or a `H.drive` draw function: the scene script runs before the brand fonts load, and `layout` runs `place` again when they have loaded and once on the page `load` event. A box that never depends on fonts (a picture) may be measured once, with the comment `// fx: measure-once (<reason>)`.
- Class names start with `fx-`; no ids, so two copies work in one scene.
- Sizes in stage pixels (`FX.kit.size(root)`); keep text inside the safe areas of the format (`_shared/modern.md`).
- No logos, product names or screenshots of other companies (`_shared/tone.md`).
- `block.md` keeps the `source` block (site, name, repo, sha, file, licence). The licence must be on the allowlist (`libcore.ALLOWED`).

## Status
- `draft`: new, or made for one video. `use` says so. Usable, but not yet reviewed.
- `approved`: you approved a video that uses it, or you approved its batch in the gallery. Then set `status: "approved"` in `block.md` and run `lib index`.

## Check
`python anim.py lib fx check <id>` runs the rules above and the demo in both engines (three seeks, out of order, must match). Every problem must be gone before `use` in a video you approve. Tests: `tests/test_fx.py`, `tests/test_fx_browser.py`.
