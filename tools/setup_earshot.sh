#!/usr/bin/env bash
# Installs earshot (https://github.com/Leonxlnx/earshot, MIT) into the gitignored tools/earshot/ with its own venv.
# Idempotent. First run downloads ~1.4 GB of models. Used by `anim.py listen` and the earshot MCP server.
set -euo pipefail

EARSHOT_REF=108763c62648c78dbac14f5bebcd3c61ac7931cd
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/tools/earshot"

[ -d "$DEST/.git" ] || git clone https://github.com/Leonxlnx/earshot "$DEST"
git -C "$DEST" checkout --quiet "$EARSHOT_REF"

# the project venv's base interpreter (3.12) is known to take torch
[ -x "$DEST/.venv/bin/python" ] || "$ROOT/.venv/bin/python" -m venv "$DEST/.venv"
PY="$DEST/.venv/bin/python"

"$PY" -c "import torch" 2>/dev/null || "$PY" -m pip install torch --index-url https://download.pytorch.org/whl/cpu
"$PY" -m pip install -e "$DEST[mcp]"
EARSHOT_THREADS="${EARSHOT_THREADS:-3}" "$PY" -m earshot doctor --load
