# Design lookup (optional)

UI UX Pro Max is an offline search over style, colour, font and chart data. It is a source of ideas only.
Brand tokens in `brands/<id>/` always win. A video for an existing brand never needs it.

Vendored in `.claude/skills/ui-ux-pro-max/` (see its `VENDOR.md`). No network. Nothing to install.

## When to use it
- New brand: you need a first palette, font pair and style.
- New video style that no existing style covers.
- Chart scene: you need a chart type for the data.
- Mood that `brands/` and `styles/` do not cover.

## Command
```
.venv/bin/python -E -s -B .claude/skills/ui-ux-pro-max/scripts/search.py "<query>" --domain <domain> [-n 5] [--json]
.venv/bin/python -E -s -B .claude/skills/ui-ux-pro-max/scripts/search.py "<business and mood>" --design-system
```
Do not use `-I`: search.py imports files from its own folder.

## Domains to use
`style`, `color`, `typography`, `motion` (only as `--design-system --motion N`; do not use `--domain motion`), `chart`, `--design-system`.

## Domains to ignore
`--stack`, `ux`, `landing`, `react`, `web`, `product`, `icons`, `gsap`. They target web apps, not video.
Do not paste GSAP snippets from the data. All motion is a function of time (`_shared/motion.md`).
Never use `--persist` and never install `uipro` from npm.

## Flow for a new brand
1. Run `--design-system "<business>"`. Read the colours, fonts and style it suggests.
2. Copy `_templates/brand/` to `brands/<id>/` (steps in `brands/CONTEXT.md`).
3. Fill `tokens.js` and `brand.md` with the chosen values. Keep your own words in `brand.md`.
4. Fonts must be local: add them under `_runtime/fonts/`, with `OFL.txt`, `fonts.css` and `FONT-SOURCES.json`. A font name from a search is not enough.
5. Brand counters run inside a video's check. Make a test video first (`.venv/bin/python anim.py new brand-test --brand <id>`), then run `.venv/bin/python anim.py check <id>/brand-test`. Brand missing, font, contrast and gradient counters must read 0. Without a video: `.venv/bin/python -c "import check, pathlib; print(check.brand_counters(pathlib.Path('.'), '<id>'))"`.
6. Render stills. You approve them before you build scenes.

## Limits
- Motion values from a search must still pass `_shared/motion.md` (eases, springs, timing).
- Search results are suggestions. Never copy claims, prices or text from the data into a video.
- Results change when the vendored data changes. Record the choice in the brand's `brand.md`.
