"""Looks: brand-neutral visual, editing and content cards, per-brand picks and the style board (looks/CONTEXT.md)."""
from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path

from studio.workspace import WorkspaceError, _frontmatter, _record

AXES = ("visual", "editing", "content")
SECTIONS = ("## Look", "## Behaviour", "## Do", "## Don't", "## Build notes")
SHORTLIST_MAX = 5
_REQUIRED = {"id", "axis", "title", "summary", "aliases", "sources", "best_for", "formats", "pairs_with", "preview", "build"}
_ALLOWED = _REQUIRED | {"palette_roles"}
_TOKENS = {"bg", "surface", "raised", "ink", "dim", "faint", "line", "accent", "accent2", "green", "danger"} | {f"r{i}" for i in range(8)}
_HARD_COLOUR = re.compile(r"(?<![\w&-])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b|\b(?:rgba?|hsla?|oklch)\(", re.I)
_PREFS_FIELDS = {"default", "shortlist", "rules"}
AI_JOB = "looks-ai"


def load_cards(root) -> dict[str, dict[str, dict]]:
    """Every card by axis and id: {"meta", "body", "dir"}. Raises on a malformed card."""
    cards: dict[str, dict[str, dict]] = {axis: {} for axis in AXES}
    for axis in AXES:
        for path in sorted((Path(root) / "looks" / axis).glob("*/look.md")):
            try:
                meta, body = _frontmatter(path.read_text(encoding="utf-8"), _REQUIRED, _ALLOWED)
            except WorkspaceError as error:
                raise WorkspaceError("invalid", f"{path.parent.name}: {error}") from None
            cards[axis][path.parent.name] = {"meta": meta, "body": body, "dir": path.parent}
    return cards


def card_problems(root) -> list[str]:
    try:
        cards = load_cards(root)
    except WorkspaceError as error:
        return [str(error)]
    problems = []
    for axis, items in cards.items():
        for ident, card in items.items():
            meta, where = card["meta"], f"{axis}/{ident}"
            if meta["id"] != ident or meta["axis"] != axis:
                problems.append(f"{where}: id and axis must match the folder")
            if meta["preview"] not in ("native", "ai") or meta["build"] not in ("native", "library", "ai"):
                problems.append(f"{where}: preview is native|ai, build is native|library|ai")
            if not set(meta["formats"]) or not set(meta["formats"]) <= {"wide", "tall"}:
                problems.append(f"{where}: formats must be wide and/or tall")
            for section in SECTIONS:
                if not re.search(rf"^{re.escape(section)}\s*$", card["body"], re.M):
                    problems.append(f"{where}: missing section {section}")
            preview = card["dir"] / "preview.html"
            if not preview.is_file():
                problems.append(f"{where}: preview.html is missing (an ai card still needs a native stand-in)")
            elif _HARD_COLOUR.search(re.sub(r"<!--.*?-->|/\*.*?\*/", "", preview.read_text(encoding="utf-8"), flags=re.S)):
                problems.append(f"{where}: preview.html hard-codes a colour; use the brand variables")
            if axis == "visual":
                pairs = meta["pairs_with"]
                if not isinstance(pairs, dict) or pairs.get("editing") not in cards["editing"] or pairs.get("content") not in cards["content"]:
                    problems.append(f"{where}: pairs_with needs an existing editing and content id")
                roles = meta.get("palette_roles")
                if not isinstance(roles, dict) or not roles or not set(roles.values()) <= _TOKENS:
                    problems.append(f"{where}: palette_roles must map roles to brand tokens ({', '.join(sorted(_TOKENS))})")
            elif not isinstance(meta["pairs_with"], list) or not set(meta["pairs_with"]) <= set(cards["visual"]):
                problems.append(f"{where}: pairs_with must list existing visual ids")
    return problems


def ids(value) -> list[str]:
    """One look id, a comma list, or a JSON list -> a list of ids; the first is the main look."""
    if isinstance(value, str):
        return [part.strip() for part in value.replace("+", ",").split(",") if part.strip()]
    if isinstance(value, list) and all(isinstance(v, str) and v for v in value):
        return list(value)
    return []


def prefs_path(root, brand) -> Path:
    return Path(root) / "brands" / brand / "looks" / "prefs.md"


def load_prefs(root, brand) -> dict:
    path = prefs_path(root, brand)
    prefs = {"default": {}, "shortlist": [], "rules": {}}
    if path.is_file():
        meta, _ = _frontmatter(path.read_text(encoding="utf-8"), set(), _PREFS_FIELDS)
        prefs.update(meta)
    return prefs


def prefs_problems(root, brand, cards=None) -> list[str]:
    cards = cards or load_cards(root)
    try:
        prefs = load_prefs(root, brand)
    except WorkspaceError as error:
        return [f"{brand} prefs: {error}"]
    problems = []

    def pick(where, value):
        if not isinstance(value, dict) or not set(value) <= set(AXES):
            problems.append(f"{brand} prefs {where}: use visual, editing and content keys")
            return
        for axis, raw in value.items():
            if not ids(raw):
                problems.append(f"{brand} prefs {where}: {axis} needs a look id or a list of ids")
            problems.extend(f"{brand} prefs {where}: unknown {axis} look '{ident}'" for ident in ids(raw) if ident not in cards[axis])
    pick("default", prefs["default"])
    shortlist = prefs["shortlist"]
    if not isinstance(shortlist, list) or len(shortlist) > SHORTLIST_MAX:
        problems.append(f"{brand} prefs shortlist: at most {SHORTLIST_MAX} visual ids")
    else:
        problems.extend(f"{brand} prefs shortlist: unknown visual look '{i}'" for i in shortlist if i not in cards["visual"])
    if not isinstance(prefs["rules"], dict):
        problems.append(f"{brand} prefs rules: map a video type to looks")
    else:
        for key, value in prefs["rules"].items():
            pick(f"rule '{key}'", value)
    return problems


def resolve(root, brand, video_type=None, explicit=None) -> dict[str, tuple[list[str], str]]:
    """Per axis: (look ids, where they came from); the first id is the main look, the others serve named scenes.
    Order: explicit > type rule > brand default > the main visual look's pairs_with."""
    cards, prefs = load_cards(root), load_prefs(root, brand)
    rule = prefs["rules"].get(video_type, {}) if video_type else {}
    chosen: dict[str, tuple[list[str], str]] = {}
    for axis in AXES:
        for source, value in (("your choice", (explicit or {}).get(axis)), (f"rule for {video_type}", rule.get(axis)),
                              ("brand default", prefs["default"].get(axis))):
            picked = ids(value) if value else []
            if picked:
                unknown = [i for i in picked if i not in cards[axis]]
                if unknown:
                    raise WorkspaceError("invalid", f"unknown {axis} look '{unknown[0]}'")
                chosen[axis] = (picked, source)
                break
        else:
            chosen[axis] = ([], "none")
    if chosen["visual"][0]:
        main = chosen["visual"][0][0]
        for axis in ("editing", "content"):
            if not chosen[axis][0]:
                chosen[axis] = ([cards["visual"][main]["meta"]["pairs_with"][axis]], f"pairs with {main}")
    return chosen


def copy_into_video(root, dest: Path, chosen: dict) -> dict:
    """Freeze the chosen cards in <dest>/looks/<axis>-<id>.md (dest is the video's 04_scene/) and return the project.json value."""
    cards = load_cards(root)
    out = dest / "looks"
    picked = {axis: list(found) for axis, (found, _) in chosen.items() if found}
    for axis, found in picked.items():
        for ident in found:
            out.mkdir(parents=True, exist_ok=True)
            shutil.copy2(cards[axis][ident]["dir"] / "look.md", out / f"{axis}-{ident}.md")
    return picked


def ai_image(root, brand, ident) -> Path | None:
    """The newest registered AI preview for one look, from the image job images/<brand>/looks-ai/."""
    found = []
    for path in (Path(root) / ".studio" / "generations").glob(f"look-{ident}*.json"):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if record.get("subject_id") == f"{brand}/{AI_JOB}" and record.get("state") == "completed" and record.get("outputs"):
            found.append((record.get("created_at", ""), Path(root) / record["outputs"][0]["path"]))
    found = [f for f in found if f[1].is_file()]
    return max(found)[1] if found else None


def _inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)


def body_html(body: str) -> str:
    """The card body as small HTML: ## headings, - lists and paragraphs."""
    out, items, para = [], [], []

    def flush():
        if items:
            out.append("<ul>" + "".join(f"<li>{_inline(i)}</li>" for i in items) + "</ul>"); items.clear()
        if para:
            out.append(f"<p>{_inline(' '.join(para))}</p>"); para.clear()
    for line in body.splitlines():
        line = line.rstrip()
        if line.startswith("## "):
            flush(); out.append(f"<h3>{_inline(line[3:])}</h3>")
        elif line.lstrip().startswith(("- ", "* ")):
            if para: flush()
            items.append(line.lstrip()[2:])
        elif not line.strip():
            flush()
        elif items:
            items[-1] += " " + line.strip()
        else:
            para.append(line.strip())
    flush()
    return "".join(out)


def board_html(root, brand, cards, prefs, images: dict[tuple[str, str], Path]) -> str:
    """A static board grouped by axis; default, shortlist and rules marked. A click opens the look's explanation."""
    base = (Path(root) / "brands" / brand / "looks").resolve()
    default, shortlist = prefs.get("default", {}), prefs.get("shortlist", [])
    rules = {}
    for key, value in prefs.get("rules", {}).items():
        for axis, raw in value.items():
            for ident in ids(raw):
                rules.setdefault((axis, ident), []).append(key)
    data, sections = {}, []
    for axis, title in zip(AXES, ("Visual styles: how it looks", "Editing styles: how it moves and cuts", "Content styles: what the video does")):
        tiles = []
        for ident, card in sorted(cards[axis].items(), key=lambda kv: kv[1]["meta"]["title"].lower()):
            meta, key = card["meta"], f"{axis}-{ident}"
            tags = []
            if ident in ids(default.get(axis)):
                tags.append('<b class="t def">default</b>')
            if axis == "visual" and ident in shortlist:
                tags.append(f'<b class="t sl">shortlist {shortlist.index(ident) + 1}</b>')
            tags += [f'<b class="t ru">{html.escape(k)}</b>' for k in rules.get((axis, ident), [])]
            img = images.get((axis, ident))
            src = (img.resolve().relative_to(base).as_posix() if img.resolve().is_relative_to(base) else img.resolve().as_uri()) if img else ""
            pic = f'<img loading="lazy" src="{html.escape(src)}" alt="">' if img else '<div class="missing">needs AI image</div>'
            pairs = meta["pairs_with"]
            data[key] = {"axis": axis, "id": ident, "title": meta["title"], "summary": meta["summary"], "src": src,
                         "aliases": meta["aliases"], "best_for": meta["best_for"], "formats": meta["formats"],
                         "pairs": ([f"editing-{pairs['editing']}", f"content-{pairs['content']}"] if axis == "visual"
                                   else [f"visual-{v}" for v in pairs]),
                         "sources": meta["sources"], "tags": "".join(tags),
                         "ai": meta["preview"] == "ai" and not (img and "/generated/" in img.as_posix()),
                         "body": body_html(card["body"])}
            tiles.append(f'<button class="tile" data-key="{key}" aria-label="{html.escape(meta["title"])}">{pic}'
                         f'<span class="cap"><span>{html.escape(meta["title"])}</span><code>{ident}</code>{"".join(tags)}</span></button>')
        sections.append(f'<h2>{title} <small>{len(tiles)}</small></h2><div class="grid">{"".join(tiles)}</div>')
    name = html.escape(brand)
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name} looks</title>
<style>
:root {{ --bg:#f6f6f4; --ink:#16171a; --dim:#6b6e76; --card:#fff; --line:#e3e3df; --def:#1f7a4d; --sl:#2d5bd7; --ru:#8a5a00; --shade:rgba(10,10,12,.55); }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#121316; --ink:#eceef2; --dim:#9aa0ab; --card:#1b1d22; --line:#2a2d34; --def:#4cc38a; --sl:#7aa2ff; --ru:#e0b050; --shade:rgba(0,0,0,.7); }} }}
* {{ box-sizing:border-box; }} body {{ margin:0; padding:24px 16px 64px; background:var(--bg); color:var(--ink); font:15px/1.45 system-ui,sans-serif; }}
main {{ max-width:1400px; margin:0 auto; }} h1 {{ font-size:26px; margin:0 0 4px; }} p.lead {{ color:var(--dim); margin:0 0 24px; }}
h2 {{ font-size:18px; margin:36px 0 12px; }} h2 small {{ color:var(--dim); font-weight:400; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:16px; }}
.tile {{ all:unset; cursor:pointer; display:block; background:var(--card); border:1px solid var(--line); border-radius:10px; overflow:hidden; transition:transform .15s, box-shadow .15s; }}
.tile:hover {{ transform:translateY(-2px); box-shadow:0 8px 24px var(--shade); }} .tile:focus-visible {{ outline:3px solid var(--sl); outline-offset:2px; }}
.tile img, .missing {{ display:block; width:100%; aspect-ratio:16/9; object-fit:cover; }}
.missing {{ display:grid; place-items:center; color:var(--dim); background:repeating-linear-gradient(45deg,transparent 0 10px,var(--line) 10px 11px); }}
.cap {{ display:flex; flex-wrap:wrap; gap:6px; align-items:center; padding:10px 12px; }} .cap > span {{ font-weight:600; margin-right:auto; }}
code {{ color:var(--dim); font-size:12px; }} .t {{ font-size:11px; font-weight:600; padding:2px 7px; border-radius:99px; border:1px solid currentColor; white-space:nowrap; }}
.def {{ color:var(--def); }} .sl {{ color:var(--sl); }} .ru {{ color:var(--ru); }}
dialog {{ width:min(960px,100%); max-height:calc(100dvh - 32px); padding:0; border:1px solid var(--line); border-radius:14px; background:var(--card); color:var(--ink); }}
dialog::backdrop {{ background:var(--shade); }}
.m-img {{ display:block; width:100%; aspect-ratio:16/9; object-fit:cover; background:var(--bg); }}
.m-body {{ padding:20px 24px 28px; }} .m-top {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; }}
.m-top h2 {{ margin:0 auto 0 0; font-size:24px; }} .m-sum {{ font-size:17px; margin:10px 0 14px; }}
.m-meta {{ display:grid; grid-template-columns:max-content 1fr; gap:6px 14px; font-size:14px; padding:12px 0; border-block:1px solid var(--line); }}
.m-meta dt {{ color:var(--dim); }} .m-meta dd {{ margin:0; }}
.m-meta a {{ color:var(--sl); cursor:pointer; text-decoration:underline; margin-right:10px; }}
.m-text h3 {{ font-size:16px; margin:20px 0 6px; }} .m-text ul {{ margin:0; padding-left:20px; }} .m-text li {{ margin:4px 0; }}
.m-text code {{ font-size:13px; }} .m-note {{ color:var(--ru); font-size:13px; margin-top:8px; }}
.m-nav {{ position:sticky; top:0; display:flex; justify-content:flex-end; gap:6px; padding:8px; background:var(--card); border-bottom:1px solid var(--line); z-index:1; }}
.m-nav button {{ font:inherit; font-size:14px; padding:6px 12px; border-radius:8px; border:1px solid var(--line); background:var(--bg); color:var(--ink); cursor:pointer; }}
.m-src a {{ color:var(--dim); font-size:13px; word-break:break-all; display:block; }}
</style></head><body><main>
<h1>{name}: video looks</h1>
<p class="lead">Every look in this brand's colours and fonts. Click a look for its explanation. Tell the agent the id to use, to set as default, to put on the shortlist (max {SHORTLIST_MAX}), or to use for a video type.</p>
{"".join(sections)}
</main>
<dialog id="look"><div class="m-nav"><button data-go="-1" aria-label="Previous look">&larr;</button><button data-go="1" aria-label="Next look">&rarr;</button><button data-close aria-label="Close">Close</button></div>
<img class="m-img" alt=""><div class="m-body"><div class="m-top"><h2></h2><code class="m-id"></code><span class="m-tags"></span></div>
<p class="m-sum"></p><p class="m-note" hidden>This image is a code-drawn stand-in. An AI image can replace it after you approve it.</p>
<dl class="m-meta"></dl><div class="m-text"></div><div class="m-src"></div></div></dialog>
<script>
const LOOKS = {payload};
const keys = [...document.querySelectorAll('.tile')].map(t => t.dataset.key);
const dlg = document.getElementById('look'), q = s => dlg.querySelector(s);
let current = null;
const esc = s => String(s).replace(/[&<>"]/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}})[c]);
const link = k => LOOKS[k] ? `<a data-key="${{k}}">${{esc(LOOKS[k].title)}}</a>` : '';
function show(key) {{
  const L = LOOKS[key]; if (!L) return; current = key;
  const img = q('.m-img'); img.hidden = !L.src; if (L.src) img.src = L.src;
  q('h2').textContent = L.title; q('.m-id').textContent = L.axis + ' / ' + L.id; q('.m-tags').innerHTML = L.tags;
  q('.m-sum').textContent = L.summary; q('.m-note').hidden = !L.ai;
  const rows = [['Also called', esc(L.aliases.join(', '))], ['Best for', esc(L.best_for.join(', '))], ['Formats', esc(L.formats.join(', '))],
                [L.axis === 'visual' ? 'Pairs with' : 'Fits visual looks', L.pairs.map(link).join('')]];
  q('.m-meta').innerHTML = rows.filter(r => r[1]).map(r => `<dt>${{r[0]}}</dt><dd>${{r[1]}}</dd>`).join('');
  q('.m-text').innerHTML = L.body;
  q('.m-src').innerHTML = L.sources.length ? '<h3>Sources</h3>' + L.sources.map(u => `<a href="${{esc(u)}}" target="_blank" rel="noopener">${{esc(u)}}</a>`).join('') : '';
  dlg.scrollTop = 0; if (!dlg.open) dlg.showModal();
  history.replaceState(null, '', '#' + key);
}}
document.addEventListener('click', e => {{
  const t = e.target.closest('[data-key]'); if (t) {{ e.preventDefault(); show(t.dataset.key); return; }}
  if (e.target.closest('[data-close]') || e.target === dlg) dlg.close();
  const go = e.target.closest('[data-go]'); if (go) show(keys[(keys.indexOf(current) + +go.dataset.go + keys.length) % keys.length]);
}});
document.addEventListener('keydown', e => {{
  if (!dlg.open) return;
  if (e.key === 'ArrowRight') show(keys[(keys.indexOf(current) + 1) % keys.length]);
  if (e.key === 'ArrowLeft') show(keys[(keys.indexOf(current) - 1 + keys.length) % keys.length]);
}});
dlg.addEventListener('close', () => history.replaceState(null, '', location.pathname));
const fromHash = () => {{ if (LOOKS[location.hash.slice(1)]) show(location.hash.slice(1)); }};
addEventListener('hashchange', fromHash); fromHash();
</script></body></html>
"""


def write_prefs(root, brand, prefs: dict) -> Path:
    path = prefs_path(root, brand)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = ("\n# Look picks\n\nEdit with the agent or by hand, then run `python anim.py looks check --brand " + brand + "`.\n"
            "Rules map a video type (`_shared/audience.md`) or a content look id to looks. Order: looks/CONTEXT.md.\n")
    path.write_text(_record({k: prefs.get(k, {} if k != "shortlist" else []) for k in ("default", "shortlist", "rules")}, body), encoding="utf-8")
    return path
