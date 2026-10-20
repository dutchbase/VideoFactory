# Precedent library

What human motion designers did at a given kind of beat, as short rules: 716 rows in `moments.jsonl`.
Vendored from tejashmakwana/motionmaxxing (Apache-2.0, `licenses/motionmaxxing-Apache-2.0.txt`). Stdlib Python, no network, read-only.

- `PR-Xnn` (156): designer rules as WHEN / DO / BECAUSE, with frame and pixel numbers.
- `PM###` (53): study moments: role, mechanic and why it works.
- `PL####` (507): rules decoded from human-made reference films (film ids are opaque).

The rows come from short brand and product films, and the author marks them unverified. Rank: `_shared/motion.md`, `_shared/transitions.md`, the brand files and your own decisions always win over a precedent row. Take the rule and the why, not the technique name.

## Use it at the brief

One query per beat of the scene list. Beats: `hook`, `turn`, `proof`, `cta`. Contents: `ui`, `type`, `logo`, `number`, `3d`.

```
.venv/bin/python -I tools/precedent/precedent.py query --beat hook --content ui --k 5
.venv/bin/python -I tools/precedent/precedent.py query --beat proof --text "selection becomes result"
.venv/bin/python -I tools/precedent/precedent.py show PR-A02
.venv/bin/python -I tools/precedent/precedent.py rules --beat cta
.venv/bin/python -I tools/precedent/precedent.py stats
```

Adopt at most one rule per scene and write its id in that scene's line of the brief (for example `PR-A02: cause lands first, effect 1-2 f later`).
