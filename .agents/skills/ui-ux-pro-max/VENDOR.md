# Vendor record: UI UX Pro Max

- Source: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
- Commit: 026b6e172c47fa09246b89b6e1d414b8e15f1057 (cloned 2026-10-12)
- Licence: MIT, see `licenses/ui-ux-pro-max-MIT.txt`
- Copied from `.claude/skills/ui-ux-pro-max/` upstream: `SKILL.md`, `data/`, `scripts/`, `references/`.
- Left out: `scripts/tests/` (upstream tests).
- Changed: one note added at the top of `SKILL.md`. Nothing else is edited.
- Reviewed: scripts use only the Python standard library. No network, no subprocess.
  `urllib.parse` is used for string parsing only.
- Run: `python -E -s -B .claude/skills/ui-ux-pro-max/scripts/search.py "<query>" --domain <domain>`.
  Do not use `-I`: search.py imports `core` from its own folder.
- Do not use `--persist` (it writes `design-system/`, which is gitignored) or the `uipro` npm CLI.
- SKILL.md keeps upstream `${CLAUDE_PLUGIN_ROOT}/.claude/skills/ui-ux-pro-max/...` paths. `CLAUDE_PLUGIN_ROOT` is unset in this repo, so those paths do not resolve. Known divergence: the top note in SKILL.md says to ignore the prefix and run from the repo root. Upstream paths are not mass-edited.
- To update: clone to a scratch folder, read the diff, replace the folders, change the commit here.
