"""Write library/icons/lucide/TAGS.json: search tags and groups (categories) for every Lucide icon.

The data comes from the Lucide repository (icons/<name>.json, ISC) at the commit pinned in library/upstream/sources.json.
`lib index` reads TAGS.json, so `lib find` matches an icon by meaning, not only by file name. Generated: never edit.

    .venv/bin/python tools/icon_meta.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import upstream  # noqa: E402

OUT = ROOT / "library" / "icons" / "lucide" / "TAGS.json"


def lucide_tags() -> dict[str, dict]:
    src = upstream.ensure("lucide") / "icons"
    out = {}
    for f in sorted(src.glob("*.json")):
        m = json.loads(f.read_text(encoding="utf-8"))
        out[f.stem] = {"tags": m.get("tags", []), "groups": m.get("categories", [])}
    return out


def build() -> int:
    tags = lucide_tags()
    OUT.write_text(json.dumps(tags, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8")
    return len(tags)


if __name__ == "__main__":
    print(f"{build()} icons -> {OUT.relative_to(ROOT)}")
