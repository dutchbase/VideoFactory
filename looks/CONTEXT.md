# Looks: visual, editing and content styles

A look is a brand-neutral card that tells the scene builder how a video should look, move or be shaped. Every look works with every brand: colours and fonts always come from the brand's `tokens.js`. Looks are a light layer on top of the Modern kit. They are not style recipes (`styles/`) and they need no sample render.

## Three axes
| Axis | Question it answers | Folder | Preview image |
|---|---|---|---|
| visual | How does it look? (palette roles, shapes, texture, type) | `looks/visual/<id>/` | one still frame |
| editing | How does it move and cut? (entrances, transitions, camera, pacing) | `looks/editing/<id>/` | a 3-panel filmstrip |
| content | What does the video do? (explain, compare, list, demo …) | `looks/content/<id>/` | a layout wireframe |

One video can mix looks. Per axis it holds a list: the first id is the main look, the others serve named scenes (for example a Swiss-modernist video with one data-journalism chart scene, or a listicle with one compare segment). Each visual card names the editing and content looks it pairs with by default (`pairs_with`).

## Mixing looks in one video
- The main look carries the opening, the end card and every scene that names no look.
- The brief's scene list names the look of each other scene (`look: visual/data-journalism`). The scene builder follows that card's `## Behaviour` inside the scene.
- Keep it coherent: brand tokens stay the same in every look. At most three visual looks per video; switch looks only at a scene change, with a cut from the main editing look.
- Content looks shape the order of beats. A second content look covers one segment, then the main structure continues.

## Card: `look.md`
Frontmatter is one `key: <JSON value>` per line (same rule as `styles/*/style.md`).
| Field | Value |
|---|---|
| `id` | folder name, lowercase with hyphens |
| `axis` | `"visual"`, `"editing"` or `"content"` |
| `title`, `summary` | name and one sentence |
| `aliases` | other names people use, e.g. `["vox style"]` |
| `sources` | research URLs |
| `best_for` | content look ids and video types from `_shared/audience.md` |
| `formats` | `["wide","tall"]` or one of them |
| `pairs_with` | visual: `{"editing": id, "content": id}`; editing/content: list of visual ids |
| `preview` | `"native"` (code-drawn `preview.html`) or `"ai"` (AI still, see Board) |
| `build` | `"native"` (CSS/SVG in the Modern kit), `"library"` (needs `library/` parts) or `"ai"` (needs AI images) |
| `palette_roles` | visual only: style role → brand token, e.g. `{"paper": "bg", "ink": "ink", "hot": "accent"}` |

Body sections, all required: `## Look`, `## Behaviour`, `## Do`, `## Don't`, `## Build notes`.
`## Behaviour` is binding for stage 04. It states entrances, exits, transitions, camera, pacing (hold times, changes per minute) and easing in the names of `_shared/motion.md`, plus ambient loops and sound feel.

## Preview: `preview.html`
A 1280×720 still. It loads `../../_runtime/preview.css` and `../../_runtime/preview.js`, which turn the brand tokens into CSS variables (`--bg --surface --raised --ink --dim --faint --line --accent --accent2 --r0..--r7 --g0a/--g0b --font --head --mono --hand`). Never write a hex, `rgb()` or font name in a preview. Derive tints with `color-mix()`. Generic families (`serif`, `monospace`) are allowed only as texture next to a brand font. Start from `_templates/look/`.

## Board (per brand)
`python anim.py looks board --brand <id>` (or `--all`) screenshots every native preview with that brand's tokens into `brands/<id>/looks/previews/` and writes `brands/<id>/looks/board.html`: images only, grouped by axis, with the default and shortlist marked. Click an image to read the look's card. Run it when a brand is added, when a brand's tokens change, and with `--all` when a look is added.
AI previews: one image job per brand, `images/<brand>/looks-ai/`, with one `image-picture` batch per look whose id starts with `look-<look-id>` (`_shared/image-generation.md`). A person approves every batch. The board shows a registered image, or a "needs AI image" tile.

## Picks (per brand): `brands/<id>/looks/prefs.md`
Frontmatter, same JSON-line rule:
- `default`: `{"visual": id, "editing": id, "content": id}`; a value may be a list, main look first
- `shortlist`: up to 5 visual ids
- `rules`: video type or content id → `{"visual": id or [ids], "editing": …, "content": …}` (any subset)
CLI: join several ids with `+`, e.g. `looks prefs --brand vai --rule course:visual=whiteboard+data-journalism`.
When the user says "always use X", "put X on the shortlist" or "use X for courses", edit this file, then run `python anim.py looks check --brand <id>`.

Resolution for a new video, per axis: the user's explicit choice > the rule for the video type > the brand default > the visual card's `pairs_with` > none (plain Modern). `python anim.py looks pick --brand <id> --type <type>` prints the result and its source. `anim.py new --type <type>` (or `--visual/--editing/--content`) writes `looks` into `project.json` and copies every chosen card into `videos/<brand>/<slug>/04_scene/looks/<axis>-<id>.md`. `--visual a,b` gives several looks. The copy is frozen: later card edits do not change the video.

`python anim.py looks open --brand <id>` opens the board in the default browser (`--look visual-<id>` opens one look's explanation). Every image on the board opens a window with the full card.

## Human check
Look at the board for each new brand. Pick a default and a shortlist. A look is direction for the builder, never an approval of a scene.
