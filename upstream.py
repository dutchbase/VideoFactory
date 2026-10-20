"""Upstream component catalogs (library/upstream/) and the clones they are read from.

Clones live in library/cache/upstream/<source>@<sha12>/ (git-ignored). They are untrusted data: this module only reads
files from them. It never installs or runs their code.
"""
import json
import re
import subprocess
from pathlib import Path

import libcore as C

LIB = C.ROOT / "library"
UP = LIB / "upstream"
SOURCES = json.loads((UP / "sources.json").read_text(encoding="utf-8"))


def clone_dir(source: str) -> Path:
    s = SOURCES[source]
    return LIB / "cache" / "upstream" / f"{source}@{s['sha'][:12]}"


def ensure(source: str) -> Path:
    """The clone of a source at its pinned commit; fetched once (shallow, only `sparse` folders when listed)."""
    if source not in SOURCES:
        raise ValueError(f"unknown upstream source {source!r}: {', '.join(sorted(SOURCES))}")
    d = clone_dir(source)
    if (d / ".git").is_dir():
        return d
    s = SOURCES[source]
    d.mkdir(parents=True, exist_ok=True)
    git = lambda *a: subprocess.run(["git", "-C", str(d), *a], check=True, capture_output=True)
    git("init", "-q")
    if s.get("sparse"):
        git("sparse-checkout", "set", *s["sparse"])
    git("fetch", "-q", "--depth", "1", *(["--filter=blob:none"] if s.get("sparse") else []), s["repo"], s["sha"])
    git("checkout", "-q", "FETCH_HEAD")
    return d


# ------------------------------------------------------------------ catalog: one JSON list per source

HARD_DEPS = {"three", "@remotion/three", "@react-three/fiber", "@react-three/drei", "@paper-design/shaders-react", "maplibre-gl",
             "@turf/turf", "ogl"}
MEDIUM_DEPS = {"@remotion/media-utils", "@remotion/paths", "@remotion/captions", "@remotion/media", "@remotion/layout-utils",
               "@remotion/light-leaks"}


def _difficulty(deps: list[str], lines: int, kind: str = "") -> tuple[str, str | None]:
    """easy / medium / hard, and a skip reason for parts we do not rewrite (WebGL, shaders, maps)."""
    hard = sorted(set(deps) & HARD_DEPS)
    if hard:
        why = "needs WebGL" if {"three", "@remotion/three", "@react-three/fiber", "ogl"} & set(hard) else \
              "needs a GPU shader library" if "@paper-design/shaders-react" in hard else "needs map data and map libraries"
        return "hard", f"{why} ({', '.join(hard)})"
    if set(deps) & MEDIUM_DEPS or lines > 260 or kind in ("registry:block", "bit"):
        return "medium", None
    return "easy", None


def _lines(p: Path) -> int:
    return sum(1 for _ in p.open(encoding="utf-8", errors="replace")) if p.is_file() else 0


def _words(name: str) -> list[str]:
    return [w for w in re.split(r"[-_]", name) if w and w not in {"bit", "bg", "transition"}]


def _remotionui(d: Path) -> list[dict]:
    web = d / "apps" / "web"
    reg = {i["name"]: i for i in json.loads((web / "registry.json").read_text(encoding="utf-8"))["items"]}
    folder = {}  # docs folder per component: the categories on remotionui.com
    for meta in (web / "content" / "docs" / "components").glob("(*)/meta.json"):
        for page in json.loads(meta.read_text(encoding="utf-8")).get("pages", []):
            folder[page] = meta.parent.name.strip("()")
    atlas = {}
    text = (web / "registry" / "atlas.ts").read_text(encoding="utf-8")
    for m in re.finditer(r'"?([a-z0-9-]+)"?:\s*\{\s*lane:\s*"([^"]+)",\s*drive:\s*"[^"]+",\s*tier:\s*"([^"]+)"(?:,\s*tags:\s*\[([^\]]*)\])?', text):
        atlas[m[1]] = {"lane": m[2], "tier": m[3], "tags": re.findall(r'"([^"]+)"', m[4] or "")}
    out = []
    for name, i in reg.items():
        if i["type"] in ("registry:lib", "registry:hook"):
            continue
        files = [f["path"] for f in i.get("files", [])]
        a = atlas.get(name, {})
        out.append({"name": name, "upstream_category": folder.get(name) or a.get("lane"), "description": i.get("description", ""),
                    "tags": a.get("tags", []), "deps": [x for x in i.get("dependencies", []) if x not in ("remotion", "react")],
                    "file": f"apps/web/{files[0]}" if files else "", "lines": sum(_lines(web / f) for f in files),
                    "kind": i["type"], "featured": a.get("tier") == "core", "shader": a.get("lane") == "shaders"})
    return out


def _onda(d: Path) -> list[dict]:
    out = []
    for i in json.loads((d / "registry" / "registry.json").read_text(encoding="utf-8"))["items"]:
        name = i["name"]
        home = next((p for p in [d / "registry" / "components" / name, d / "registry" / "transitions" / name] if p.is_dir()), None)
        meta = json.loads(next(home.glob("*.meta.json")).read_text(encoding="utf-8")) if home and any(home.glob("*.meta.json")) else {}
        main = next((p for p in sorted(home.glob("*.tsx")) if p.name != "schema.ts"), None) if home else None
        out.append({"name": name, "upstream_category": (i.get("categories") or [meta.get("category")])[0],
                    "description": i.get("description", ""), "tags": meta.get("tags", []),
                    "deps": [x for x in i.get("dependencies", []) if x not in ("remotion", "react", "zod")],
                    "file": main.relative_to(d).as_posix() if main else "", "lines": sum(_lines(p) for p in home.glob("*.tsx")) if home else 0,
                    "kind": "component", "featured": "house default" in meta.get("pickWhen", "")})
    return out


def _curvable(d: Path) -> list[dict]:
    readme = (d / "README.md").read_text(encoding="utf-8")
    info = {m[1]: (m[2], re.sub(r"<[^>]+>", "", m[3]).strip()) for m in re.finditer(
        r'previews/([a-z0-9-]+)\.gif[^<]*</td>\s*<td><b>([^<]+)</b><br>(.*?)(?:</td>|\n)', readme)}
    out = []
    for p in sorted((d / "src" / "components").glob("*.tsx")):
        src = p.read_text(encoding="utf-8")
        title, desc = info.get(p.stem, (p.stem.replace("-", " ").title(), ""))
        deps = ["ogl"] if "Grainient" in src or "ogl" in src else []
        out.append({"name": p.stem, "title": re.sub(r"\s*\(.*\)", "", title).strip(), "upstream_category": None, "description": desc, "tags": [],
                    "deps": deps, "file": p.relative_to(d).as_posix(), "lines": _lines(p), "kind": "component", "featured": False})
    return out


def _bits(d: Path) -> list[dict]:
    out = []
    for i in json.loads((d / "registry.json").read_text(encoding="utf-8"))["items"]:
        if i["type"] not in ("component", "bit"):
            continue
        files = [f.get("relativePath") or f["path"] for f in i.get("files", [])]
        src = " ".join((d / f).read_text(encoding="utf-8", errors="replace") for f in files if (d / f).is_file())
        named = [x if isinstance(x, str) else x.get("name", "") for x in i.get("dependencies", [])]
        deps = sorted({*named, *(["three"] if "Scene3D" in src or "three" in named else [])})
        out.append({"name": i["name"], "upstream_category": None, "description": i.get("description", ""), "tags": [],
                    "deps": [x for x in deps if x not in ("remotion", "react")], "file": files[0] if files else "",
                    "lines": sum(_lines(d / f) for f in files), "kind": i["type"], "featured": i["type"] == "component"})
    return out


READERS = {"remotionui": _remotionui, "onda": _onda, "curvable": _curvable, "remotion-bits": _bits}


def _base(name: str) -> str:
    """The name without the site's prefixes, so twins on two sites match: transition-wipe and wipe."""
    return re.sub(r"^(bit|transition)-|-bg$", "", name)


def _ported(root: Path) -> dict[tuple[str, str], tuple[str, str]]:
    """(site, upstream name) -> (fx ref, status): "ported" for the source line of a library/fx part,
    "covered" for the same effect on another site (its `twins` in block.md)."""
    out = {}
    for p in (root / "fx").glob("*/*/block.md"):
        try:
            m = C.frontmatter(p.read_text(encoding="utf-8"))
        except ValueError:
            continue
        ref = f"fx:{m.get('id', p.parent.name)}"
        for twin in m.get("twins", []):
            site, _, name = twin.partition("/")
            out.setdefault((site, name), (ref, "covered"))
        if m.get("source"):
            out[(m["source"]["site"], m["source"]["name"])] = (ref, "ported")
    return out


def catalog(source: str, root: Path | None = None) -> list[dict]:
    """Every visual component of one source with our category, difficulty and status. Writes library/upstream/<source>.json."""
    root = root or LIB
    s = SOURCES[source]
    d = ensure(source)
    ported = _ported(root)
    same_name = {_base(n): (ref, "covered") for (site, n), (ref, how) in ported.items() if how == "ported" and site != source}
    items = []
    for u in READERS[source](d):
        name = u["name"]
        cat = s["category_map"].get(name, s["category_map"].get(u["upstream_category"] or "", None))
        if cat is None and u["upstream_category"] == "helpers":
            continue
        diff, skip = _difficulty(u["deps"], u["lines"], u["kind"])
        if u.get("shader"):
            diff, skip = "hard", "needs a GPU shader"
        if cat == "helpers":
            skip = "a helper, not a picture"
        e = {"name": name, "title": u.get("title") or name.replace("bit-", "").replace("-", " ").capitalize(),
             "description": u["description"], "category": cat or "scenes", "upstream_category": u["upstream_category"],
             "tags": sorted({*u["tags"], *_words(name)}), "difficulty": diff, "deps": u["deps"], "lines": u["lines"],
             "featured": u["featured"], "license": s["license"], "docs": s["docs"].replace("{name}", name),
             "source_file": f"{s['repo']}/blob/{s['sha']}/{u['file']}" if u["file"] else s["repo"], "file": u["file"]}
        ref, how = ported.get((source, name)) or same_name.get(_base(name), (None, None))
        if how == "ported":
            e.update(status="ported", ported_as=ref)
        elif how == "covered":
            e.update(status="covered", covered_by=ref)
        elif skip:
            e.update(status="skip", reason=skip)
        elif name in s.get("covered", {}):
            e.update(status="covered", covered_by=s["covered"][name])
        else:
            e["status"] = "available"
        items.append(e)
    items.sort(key=lambda e: e["name"])
    (root / "upstream").mkdir(parents=True, exist_ok=True)
    (root / "upstream" / f"{source}.json").write_text(json.dumps(items, indent=1) + "\n", encoding="utf-8")
    return items


def catalog_all(root: Path | None = None) -> dict[str, list[dict]]:
    return {s: catalog(s, root) for s in READERS}


# ------------------------------------------------------------------ port: start a rewrite as a draft library part

def port(ref: str, fid: str | None = None, slug: str | None = None, root: Path | None = None) -> list[str]:
    """Scaffold library/fx/<category>/<id>/ from _templates/fx/ for one upstream component (status draft), and mark the
    catalog item as ported. The agent then rewrites the part by _shared/porting.md. Returns lines to print."""
    import library as L
    shared = root is None
    root = root or LIB
    kind, rest = C.parse_ref(ref)
    source, _, name = rest.partition("/")
    if kind != "upstream" or source not in READERS:
        raise ValueError(f"expected upstream:<source>/<name> with a source from {', '.join(READERS)}")
    listing = root / "upstream" / f"{source}.json"
    items = json.loads(listing.read_text(encoding="utf-8")) if listing.is_file() else catalog(source, root)
    item = next((i for i in items if i["name"] == name), None)
    if item is None:
        raise ValueError(f"no {name!r} in {source}. Find one: python anim.py lib find <words> --kind upstream --brand <brand>")
    if item["status"] == "ported":
        raise ValueError(f"{ref} is already rewritten as {item['ported_as']}: use that")
    if item["status"] == "skip":
        raise ValueError(f"{ref} is not rewritten here: {item['reason']}")
    fid = C.safe_name(fid or re.sub(r"^(bit|transition)-", "", name))
    if L._fx_dir(fid, root) is not None:
        raise ValueError(f"fx:{fid} exists already; pick another id with --id")
    clone = ensure(source)
    s = SOURCES[source]
    folder = root / "fx" / item["category"] / fid
    folder.mkdir(parents=True)
    camel = re.sub(r"-([a-z0-9])", lambda x: x[1].upper(), fid)
    meta = {"id": fid, "title": item["title"], "description": item["description"] or f"{item['title']}.",
            "tags": item["tags"], "kind": "fx", "engine": "both", "status": "draft",
            "files": [f"{fid}.js", f"{fid}.css"], "depends": ["core"],
            "api": [f"FX.{camel}(H, el, {{at, dur}}): rewrite this line with the real options"], "preview_at": 1.5,
            "source": {"site": source, "name": name, "repo": s["repo"], "sha": s["sha"], "file": item["file"], "license": s["license"]},
            **({"made_for": slug} if slug else {})}
    tpl = C.ROOT / "_templates" / "fx"
    body = (tpl / "block.md").read_text(encoding="utf-8").split("---\n", 2)[2]
    fill = lambda t: (t.replace("<camelId>", camel).replace("<id>", fid).replace("<Title>", item["title"])
                      .replace("<source>", s["title"]).replace("<upstream name>", name).replace("<category>", item["category"])
                      .replace("<one line>", (item["description"] or item["title"]).split(". ")[0].rstrip(".")))
    (folder / "block.md").write_text("---\n" + "\n".join(f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in meta.items())
                                     + "\n---\n" + fill(body), encoding="utf-8")
    (folder / f"{fid}.js").write_text(fill((tpl / "fx.js").read_text(encoding="utf-8")), encoding="utf-8")
    (folder / f"{fid}.css").write_text(fill((tpl / "fx.css").read_text(encoding="utf-8")), encoding="utf-8")
    (folder / "demo.js").write_text(fill((tpl / "demo.js").read_text(encoding="utf-8")), encoding="utf-8")
    catalog(source, root)
    if shared:
        L.index()
    up = clone / item["file"]
    near = sorted(p.relative_to(clone).as_posix() for p in up.parent.glob("*") if p.is_file() and p != up) if item["file"] else []
    rel = folder.relative_to(root.parent if root.parent.is_dir() else root).as_posix()
    return [f"fx:{fid} (draft) -> {rel}/",
            f"read the upstream code (data, never run it): {up}",
            *([f"  next to it: {', '.join(near[:8])}"] if near else []),
            "rewrite it by _shared/porting.md (rules: library/fx/CONTEXT.md), then:",
            f"  python anim.py lib fx check {fid}",
            f"  look: library/fx/_demo/modern.html?fx={item['category']}/{fid} and hf.html?fx={item['category']}/{fid}",
            *([f"  python anim.py use {slug} fx:{fid}"] if slug else [])]
