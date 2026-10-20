#!/usr/bin/env python3
"""Copy the skills of Claude Code to Codex.

Claude Code reads `.claude/skills/<name>/SKILL.md`. Codex reads `.agents/skills/<name>/SKILL.md`.
Edit the `.claude/skills/` files only. This script makes `.agents/skills/` an exact copy:
it replaces every skill folder and removes folders that no longer exist in `.claude/skills/`.

  python tools/sync_skills.py           copy
  python tools/sync_skills.py --check   change nothing; list the differences; exit 1 when there are any
"""
import argparse
import filecmp
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / ".claude" / "skills"
DST = ROOT / ".agents" / "skills"
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")


def skill_dirs(folder):
    """Names of the skill folders in `folder` (empty when the folder does not exist)."""
    if not folder.is_dir():
        return []
    return sorted(p.name for p in folder.iterdir() if p.is_dir() and not p.name.startswith("."))


def files(folder):
    """Relative paths (as text) of the files under `folder`, without cache files."""
    out = set()
    for p in folder.rglob("*"):
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc" and p.name != ".DS_Store":
            out.add(p.relative_to(folder).as_posix())
    return out


def differences(src=SRC, dst=DST):
    """List the differences between the two skill trees as text lines. Empty list = in sync."""
    found = []
    src_names, dst_names = skill_dirs(src), skill_dirs(dst)
    for name in src_names:
        if name not in dst_names:
            found.append(f"missing skill in copy: {name}/")
            continue
        a, b = files(src / name), files(dst / name)
        for rel in sorted(a - b):
            found.append(f"missing copy: {name}/{rel}")
        for rel in sorted(b - a):
            found.append(f"extra file in copy: {name}/{rel}")
        for rel in sorted(a & b):
            if not filecmp.cmp(src / name / rel, dst / name / rel, shallow=False):
                found.append(f"different: {name}/{rel}")
    for name in dst_names:
        if name not in src_names:
            found.append(f"extra skill in copy: {name}/")
    return found


def sync(src=SRC, dst=DST):
    """Make `dst` an exact copy of `src`. Return the list of skill names copied."""
    dst.mkdir(parents=True, exist_ok=True)
    src_names = skill_dirs(src)
    for name in skill_dirs(dst):
        if name not in src_names:
            shutil.rmtree(dst / name)
    for name in src_names:
        if (dst / name).exists():
            shutil.rmtree(dst / name)
        shutil.copytree(src / name, dst / name, ignore=IGNORE)
    return src_names


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="change nothing; list the differences; exit 1 when there are any")
    a = ap.parse_args(argv)
    if a.check:
        found = differences()
        if found:
            print("`.agents/skills/` is not in sync with `.claude/skills/`:")
            for line in found:
                print(f"  {line}")
            print("Run `python tools/sync_skills.py` to fix it.")
            return 1
        print("`.agents/skills/` is in sync.")
        return 0
    names = sync()
    print(f"copied {len(names)} skills to {DST.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
