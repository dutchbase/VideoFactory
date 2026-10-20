# Described materials

Each `library/materials/<id>/material.md` owns one title, description, kind, source and rights statement. An optional original upload sits beside it. Start from `_templates/material/material.md`. `source` is `upload`, an HTTP(S) reference, or an allowed workspace-relative file path. Links are references only; the server does not fetch websites.

`videos/<brand>/<slug>/materials.md` and `styles/<id>/materials.md` list stable material IDs. The catalog record stays in one place. Existing per-video assets and generated `library/INDEX.json` stay where they are. Unknown rights remain visible for research/reference but cannot be copied into production with `anim.py use` until permission is clarified. You check attribution, the licence or the rights holder's permission, and the actual bytes before use.
