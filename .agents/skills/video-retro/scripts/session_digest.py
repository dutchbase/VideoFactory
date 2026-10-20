#!/usr/bin/env python3
"""Condense a Claude Code session transcript into a retro digest.

A video session transcript is tens of MB, and most of it is tool output,
task notifications and subagent reports. This keeps what a retro needs:
the user's own messages (with the agent text just before each one),
judge/subagent verdicts, tool errors, repeated commands, anim.py usage
and the files the session already changed.

  session_digest.py --list [--limit N]          recent sessions of this project
  session_digest.py SESSION [--out FILE]        digest of one session
     SESSION = session id, id prefix, path to .jsonl, or "current"
     (the newest transcript, i.e. the session running this command)
"""
import argparse
import collections
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

NOISE_PREFIXES = (
    "<task-notification", "<system-reminder", "<local-command",
    "<command-name>/model", "<command-name>/clear", "<command-name>/compact",
    "Base directory for this skill", "Another Claude session sent a message",
    "This session is being continued", "Caveat:",
)
SLUG_RE = re.compile(r"videos/([a-z0-9][a-z0-9-]{2,})")
BASH_WRITE_RE = re.compile(r"(?:sed -i\S*\s+(?:'[^']*'|\"[^\"]*\"|\S+)\s+|>>?\s*|tee\s+(?:-a\s+)?)([\w./-]+\.(?:md|js|json|py|html|css|txt))")
ANIM_RE = re.compile(r"anim\.py\s+([a-z][\w-]*)(?:\s+([a-z0-9][a-z0-9-]{2,}))?")


def project_dir(cwd):
    return Path.home() / ".claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", cwd)


def resolve(arg, pdir):
    p = Path(arg)
    if p.suffix == ".jsonl" and p.exists():
        return p
    files = sorted(pdir.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)
    if arg == "current":
        return files[0]
    hits = [f for f in files if f.stem.startswith(arg)]
    if len(hits) == 1:
        return hits[0]
    sys.exit(f"no unique session for {arg!r} in {pdir} ({len(hits)} matches)")


def records(path):
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def blocks(rec):
    c = rec.get("message", {}).get("content")
    if isinstance(c, str):
        return [{"type": "text", "text": c}]
    return c if isinstance(c, list) else []


def text_of(rec):
    return "\n".join(b.get("text", "") for b in blocks(rec) if b.get("type") == "text").strip()


def is_human(rec):
    """True for a message the user typed (not tool results, hooks or relays)."""
    if rec.get("type") != "user" or rec.get("isSidechain") or rec.get("isMeta") or rec.get("isCompactSummary"):
        return False
    origin = rec.get("origin")
    if origin is not None:
        return origin.get("kind") == "human"
    bl = blocks(rec)
    if any(b.get("type") == "tool_result" for b in bl):
        return False
    t = text_of(rec)
    has_image = any(b.get("type") == "image" for b in bl)
    return (bool(t) or has_image) and not t.startswith(NOISE_PREFIXES)


def clip(s, n, tail=False):
    s = re.sub(r"\s+", " ", s or "").strip()
    if len(s) <= n:
        return s
    return "…" + s[-n:] if tail else s[:n] + "…"


def hhmm(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone().strftime("%m-%d %H:%M")
    except Exception:
        return "?"


def tool_summary(name, inp):
    if name == "Bash":
        return inp.get("command", "")
    for k in ("file_path", "path", "pattern", "url", "query", "prompt", "description"):
        if k in inp:
            return f"{k}={inp[k]}"
    return json.dumps(inp)[:200]


def session_meta(path):
    title = ai = None
    typed = 0
    slugs = collections.Counter()
    first = last = None
    for r in records(path):
        t = r.get("type")
        if t == "custom-title":
            title = r.get("customTitle")
        elif t == "ai-title":
            ai = r.get("aiTitle")
        ts = r.get("timestamp")
        if ts:
            first = first or ts
            last = ts
        if is_human(r):
            typed += 1
        if t == "assistant":
            for b in blocks(r):
                if b.get("type") == "tool_use":
                    slugs.update(SLUG_RE.findall(json.dumps(b.get("input", {}))))
    return title or ai or "-", typed, slugs, first, last


def cmd_list(pdir, limit):
    files = sorted(pdir.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)[:limit]
    print(f"Sessions in {pdir} (newest first; the first one is normally the running session)\n")
    for i, f in enumerate(files):
        title, typed, slugs, first, last = session_meta(f)
        top = ", ".join(f"{s}×{n}" for s, n in slugs.most_common(4)) or "-"
        mark = "  <- current" if i == 0 else ""
        print(f"{f.stem}  {f.stat().st_size / 1e6:6.1f} MB  {hhmm(first or '')} → {hhmm(last or '')}  "
              f"user msgs {typed:3d}  \"{title}\"{mark}\n    videos: {top}")


def subagent_list(path):
    """Type and task of each subagent the session started (reports arrive as hand-backs)."""
    out = []
    sdir = path.with_suffix("") / "subagents"
    for meta in sorted(sdir.glob("*.meta.json")) if sdir.exists() else []:
        try:
            m = json.loads(meta.read_text())
        except Exception:
            m = {}
        out.append(f"{m.get('agentType') or 'agent'}: {m.get('description') or meta.stem}")
    return out


def digest(path, ctx, handback):
    title, _, slugs, first, last = session_meta(path)
    tools = {}                      # tool_use_id -> (name, summary)
    last_agent_text = ""
    user_msgs, errors, handbacks = [], [], []
    bash = collections.Counter()
    anim = collections.Counter()
    edited = collections.Counter()
    compactions = 0
    interrupts = 0

    for r in records(path):
        if r.get("isSidechain"):
            continue
        t = r.get("type")
        if r.get("isCompactSummary"):
            compactions += 1
            continue
        if t == "assistant":
            for b in blocks(r):
                if b.get("type") == "text" and b.get("text", "").strip():
                    last_agent_text = b["text"]
                elif b.get("type") == "tool_use":
                    name, inp = b.get("name", "?"), b.get("input", {}) or {}
                    summ = tool_summary(name, inp)
                    tools[b.get("id")] = (name, summ)
                    if name == "Bash":
                        cmd = inp.get("command", "").strip()
                        bash[cmd] += 1
                        for sub, slug in ANIM_RE.findall(cmd):
                            anim[f"{sub} {slug}".strip()] += 1
                        for f in BASH_WRITE_RE.findall(cmd):
                            if not f.startswith("/dev/"):
                                edited[f + "  (bash)"] += 1
                    if name in ("Edit", "Write", "NotebookEdit", "MultiEdit") and inp.get("file_path"):
                        edited[inp["file_path"]] += 1
        elif t == "user":
            origin = r.get("origin") or {}
            if origin.get("kind") == "peer" and origin.get("body"):
                body = origin["body"].split("The report follows:", 1)[-1]
                handbacks.append((hhmm(r.get("timestamp", "")), origin.get("name") or origin.get("from"), clip(body, handback)))
                continue
            for b in blocks(r):
                if b.get("type") == "tool_result" and not b.get("is_error") and tools.get(b.get("tool_use_id"), ("",))[0] in ("Agent", "Task"):
                    c = b.get("content")
                    if isinstance(c, list):
                        c = " ".join(x.get("text", "") for x in c if isinstance(x, dict))
                    if c and "agentId" not in str(c)[:200] and "running in the background" not in str(c):
                        handbacks.append((hhmm(r.get("timestamp", "")), tools[b["tool_use_id"]][1][:60], clip(str(c), handback)))
                if b.get("type") == "tool_result" and b.get("is_error"):
                    name, summ = tools.get(b.get("tool_use_id"), ("?", ""))
                    c = b.get("content")
                    if isinstance(c, list):
                        c = " ".join(x.get("text", "") for x in c if isinstance(x, dict))
                    errors.append((hhmm(r.get("timestamp", "")), name, clip(summ, 140), clip(str(c), 220)))
                if b.get("type") == "text" and "[Request interrupted by user" in b.get("text", ""):
                    interrupts += 1
                    user_msgs.append((hhmm(r.get("timestamp", "")), "⟂ user interrupted the agent", clip(last_agent_text, ctx, tail=True)))
            if is_human(r):
                msg = text_of(r)
                if any(b.get("type") == "image" for b in blocks(r)):
                    msg = (msg + " [image attached]").strip()
                if "<command-name>" in msg:
                    m = re.search(r"<command-name>(.*?)</command-name>.*?<command-args>(.*?)</command-args>", msg, re.S)
                    msg = f"[ran {m.group(1)}] {m.group(2).strip()}" if m else msg
                user_msgs.append((hhmm(r.get("timestamp", "")), msg, clip(last_agent_text, ctx, tail=True)))

    w = []
    w.append(f"# Session digest: {title}")
    w.append(f"- transcript: {path}")
    w.append(f"- span: {first} → {last}")
    w.append(f"- compactions: {compactions}, user interrupts: {interrupts}, tool errors: {len(errors)}")
    w.append("- videos touched: " + (", ".join(f"{s}×{n}" for s, n in slugs.most_common()) or "none"))

    w.append(f"\n## User messages ({len(user_msgs)})")
    w.append("Each item: time, what the user said, then the tail of the agent's last text before it (context).")
    for i, (ts, msg, before) in enumerate(user_msgs, 1):
        w.append(f"\n{i}. [{ts}] USER: {msg.strip()}")
        if before:
            w.append(f"   agent before: {before}")

    if handbacks:
        w.append(f"\n## Subagent / judge hand-backs ({len(handbacks)})")
        for ts, name, body in handbacks:
            w.append(f"- [{ts}] {name}: {body}")
    subs = subagent_list(path)
    if subs:
        w.append(f"\n## Subagents started ({len(subs)})")
        w.append("; ".join(subs))

    w.append(f"\n## Tool errors ({len(errors)})")
    for ts, name, summ, err in errors:
        w.append(f"- [{ts}] {name}: `{summ}` → {err}")

    rep = [(c, n) for c, n in bash.most_common() if n >= 3]
    w.append(f"\n## Bash commands run 3+ times ({len(rep)})")
    for c, n in rep[:25]:
        w.append(f"- ×{n} `{clip(c, 160)}`")

    w.append("\n## anim.py usage (subcommand slug: count)")
    w.append(", ".join(f"{k}×{n}" for k, n in sorted(anim.items())) or "none")

    w.append(f"\n## Files the session edited ({len(edited)})")
    w.append("Edit/Write calls plus a best guess from shell redirects; most edits run through scripts, so git is the real record.")
    for f, n in sorted(edited.items()):
        w.append(f"- {f} ×{n}")
    return "\n".join(w) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("session", nargs="?", help='session id/prefix, .jsonl path, or "current"')
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--limit", type=int, default=12)
    ap.add_argument("--cwd", default=os.getcwd(), help="project root (default: cwd)")
    ap.add_argument("--context", type=int, default=400, help="chars of agent text kept before each user message")
    ap.add_argument("--handback", type=int, default=900, help="chars kept per subagent report")
    ap.add_argument("--out", help="write the digest here instead of stdout")
    a = ap.parse_args()
    pdir = project_dir(a.cwd)
    if a.list or not a.session:
        return cmd_list(pdir, a.limit)
    text = digest(resolve(a.session, pdir), a.context, a.handback)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"wrote {a.out} ({len(text) // 1024} KB)")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
