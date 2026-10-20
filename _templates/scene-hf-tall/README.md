# HyperFrames scene (tall)

Optional engine. Read `_shared/hyperframes.md` first.

`anim.py new <slug> --brand <id> --engine hyperframes --format tall` copies this folder to `04_scene/`, fills `{{BRAND}}` and `{{VOICE}}`, and adds four links inside `04_scene/`:

- `brand` -> `brands/<id>/` (tokens.js)
- `runtime` -> `_runtime/` (fonts, vendored GSAP, hf-bridge.js)
- `voice` -> `../01_voice/`
- `cues` -> `../03_cues/`

HyperFrames serves `04_scene/` as the project root and rejects `../` paths, so the links keep every path inside it.

Write the scene in the inline `<script>` of `index.html`. Check: `tools/hyperframes/node_modules/.bin/hyperframes lint videos/<brand>/<slug>/04_scene`.
