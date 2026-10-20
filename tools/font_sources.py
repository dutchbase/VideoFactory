"""Rebuild FONT-SOURCES.json from the font folders in _runtime/fonts/.

Every font family lives in its own folder with its licence file (OFL.txt) and has an @font-face rule in
_runtime/fonts/fonts.css. `check` refuses a brand font that has no record here. Add a font, then run:

    .venv/bin/python tools/font_sources.py
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "_runtime" / "fonts"
OUT = ROOT / "FONT-SOURCES.json"


def build() -> list[dict]:
    css = (FONTS / "fonts.css").read_text(encoding="utf-8")
    family = {}  # folder name -> family name, from the @font-face rules
    for m in re.finditer(r"font-family:\s*'([^']+)'[^}]*?url\('([^/']+)/", css):
        family[m.group(2)] = m.group(1)
    rows = []
    for f in sorted(FONTS.glob("*/*")):
        if f.suffix.lower() not in {".ttf", ".otf", ".woff", ".woff2"}:
            continue
        folder = f.parent.name
        licence = next((p.name for p in f.parent.iterdir() if p.name.upper().startswith(("OFL", "LICENSE"))), None)
        if licence is None:
            raise SystemExit(f"{folder}: no OFL.txt or LICENSE file next to the font")
        rows.append({"family": family.get(folder, folder), "path": f.relative_to(ROOT).as_posix(),
                     "licence": "OFL-1.1" if licence.upper().startswith("OFL") else "see " + licence,
                     "licence_file": (f.parent / licence).relative_to(ROOT).as_posix(),
                     "source": f"https://github.com/google/fonts/tree/main/ofl/{folder}",
                     "sha256": hashlib.sha256(f.read_bytes()).hexdigest()})
    return rows


if __name__ == "__main__":
    rows = build()
    OUT.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(f"{len(rows)} font files -> {OUT.relative_to(ROOT)}")
