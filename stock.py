"""Stock video, photos and music from Pexels, Pixabay, Unsplash and Openverse (CC0 music, no key). Downloads go to library/cache/stock/ (git-ignored)."""
import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import quote

from studio.project_paths import resolve_project
import libcore as C

CACHE = C.ROOT / "library" / "cache"
CACHE_TTL = 24 * 3600  # Pixabay requires search results to be cached for 24 hours
KEYS = {"pexels": "PEXELS_API_KEY", "pixabay": "PIXABAY_API_KEY", "unsplash": "UNSPLASH_ACCESS_KEY"}
PROVIDERS = tuple(KEYS)
LICENSE = {"pexels": "Pexels", "pixabay": "Pixabay", "unsplash": "Unsplash", "openverse": "CC0-1.0"}
MIN_TRACK_S = 30  # shorter results are sound effects, not a music bed


def pick_video_file(files: list[dict], min_w: int = 1080, max_w: int = 1920) -> dict:
    """Smallest file that is at least min_w wide and at most max_w; else the largest below min_w; else the smallest above max_w."""
    ok = sorted((f for f in files if min_w <= f["width"] <= max_w), key=lambda f: f["width"])
    if ok:
        return ok[0]
    below = sorted((f for f in files if f["width"] < min_w), key=lambda f: -f["width"])
    if below:
        return below[0]
    return sorted(files, key=lambda f: f["width"])[0]


def _get_json(url: str, headers: dict, fetch) -> dict:
    f = CACHE / "search" / (hashlib.sha256(url.encode()).hexdigest()[:24] + ".json")
    if f.exists() and time.time() - f.stat().st_mtime < CACHE_TTL:
        return json.loads(f.read_text(encoding="utf-8"))
    raw = C.http_get(url, headers, fetch)
    data = json.loads(raw)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(data), encoding="utf-8")
    return data


def _item(provider, kind, id, **kw) -> dict:
    d = {"ref": f"stock:{provider}/{kind}/{id}", "provider": provider, "kind": kind, "id": str(id), "title": "", "width": 0,
         "height": 0, "duration": 0, "thumb": "", "page_url": "", "author": "", "download_url": "", "license": LICENSE[provider]}
    d.update(kw)
    return d


def _pexels(q, kind, orient, limit, key, fetch):
    h = {"Authorization": key}
    if kind == "video":
        data = _get_json(f"https://api.pexels.com/v1/videos/search?query={quote(q)}&orientation={orient}&per_page={limit}", h, fetch)
        out = []
        for v in data.get("videos", []):
            files = [{"width": f["width"], "height": f["height"], "url": f["link"]}
                     for f in v.get("video_files", []) if f.get("file_type", "video/mp4") == "video/mp4" and f.get("width")]
            if not files:
                continue
            best = pick_video_file(files)
            out.append(_item("pexels", "video", v["id"], width=best["width"], height=best["height"], duration=v.get("duration", 0),
                             thumb=v.get("image", ""), page_url=v.get("url", ""), author=v.get("user", {}).get("name", ""),
                             download_url=best["url"], title=q))
        return out
    data = _get_json(f"https://api.pexels.com/v1/search?query={quote(q)}&orientation={orient}&per_page={limit}", h, fetch)
    return [_item("pexels", "photo", p["id"], title=p.get("alt", "") or q, width=p["width"], height=p["height"],
                  thumb=p["src"].get("tiny", ""), page_url=p.get("url", ""), author=p.get("photographer", ""),
                  download_url=p["src"].get("large2x") or p["src"]["original"]) for p in data.get("photos", [])]


def _pixabay(q, kind, orient, limit, key, fetch):
    limit = max(3, limit)
    if kind == "video":
        data = _get_json(f"https://pixabay.com/api/videos/?key={key}&q={quote(q)}&per_page={min(200, limit * 3)}", {}, fetch)
        out = []
        for v in data.get("hits", []):
            files = [{"width": s["width"], "height": s["height"], "url": s["url"], "thumb": s.get("thumbnail", "")}
                     for s in v.get("videos", {}).values() if s.get("url") and s.get("width")]
            if not files:
                continue
            best = pick_video_file(files)
            if (best["height"] > best["width"]) != (orient == "portrait"):  # the API has no orientation filter for video
                continue
            out.append(_item("pixabay", "video", v["id"], width=best["width"], height=best["height"], duration=v.get("duration", 0),
                             thumb=best["thumb"], page_url=v.get("pageURL", ""), author=v.get("user", ""), download_url=best["url"], title=q))
        return out[:limit]
    o = "vertical" if orient == "portrait" else "horizontal"
    data = _get_json(f"https://pixabay.com/api/?key={key}&q={quote(q)}&image_type=photo&orientation={o}&per_page={limit}", {}, fetch)
    return [_item("pixabay", "photo", p["id"], title=p.get("tags", "") or q, width=p["imageWidth"], height=p["imageHeight"],
                  thumb=p.get("previewURL", ""), page_url=p.get("pageURL", ""), author=p.get("user", ""),
                  download_url=p.get("fullHDURL") or p["largeImageURL"]) for p in data.get("hits", [])]


def _unsplash(q, kind, orient, limit, key, fetch):
    if kind != "photo":
        raise ValueError("Unsplash has photos only. Use --type photo, or pick pexels or pixabay for video.")
    o = orient if orient in ("landscape", "portrait") else "squarish"
    data = _get_json(f"https://api.unsplash.com/search/photos?query={quote(q)}&orientation={o}&per_page={min(30, limit)}",
                     {"Authorization": f"Client-ID {key}"}, fetch)
    out = []
    for p in data.get("results", []):
        d = _item("unsplash", "photo", p["id"], title=p.get("alt_description") or q, width=p["width"], height=p["height"],
                  thumb=p["urls"].get("thumb", ""), page_url=p.get("links", {}).get("html", ""), author=p.get("user", {}).get("name", ""),
                  download_url=p["urls"]["raw"] + ("&" if "?" in p["urls"]["raw"] else "?") + "w=2400&fit=max&q=85&fm=jpg")
        d["download_location"] = p.get("links", {}).get("download_location", "")
        out.append(d)
    return out


def _openverse(q, kind, orient, limit, key, fetch):
    """CC0 audio only. Openverse's CC0 audio is Freesound previews (128 kbps mp3). It has no key."""
    if kind != "audio":
        raise ValueError("Openverse is used for audio only. Use --type audio.")
    data = _get_json(f"https://api.openverse.org/v1/audio/?q={quote(q)}&license=cc0&page_size=20", {}, fetch)
    out = []
    for a in data.get("results", []):
        if a.get("license") != "cc0" or not a.get("url") or (a.get("duration") or 0) < MIN_TRACK_S * 1000:
            continue
        out.append(_item("openverse", "audio", a["id"], title=a.get("title", "") or q, duration=round(a["duration"] / 1000),
                         page_url=a.get("foreign_landing_url", ""), author=a.get("creator", "") or "", download_url=a["url"]))
    return out[:limit]


_SEARCH = {"pexels": _pexels, "pixabay": _pixabay, "unsplash": _unsplash, "openverse": _openverse}


def search(provider: str, query: str, kind: str = "video", orientation: str = "landscape", limit: int = 12,
           fetch=None, env_file: Path | None = None) -> list[dict]:
    if provider not in _SEARCH:
        raise ValueError(f"unknown provider {provider!r}: {', '.join(_SEARCH)}")
    if kind not in ("video", "photo", "audio"):
        raise ValueError("--type is video, photo or audio")
    if (kind == "audio") != (provider == "openverse"):
        raise ValueError("audio comes from openverse only: python anim.py stock search openverse \"calm piano\" --type audio")
    if orientation not in ("landscape", "portrait"):
        raise ValueError("--orientation is landscape or portrait")
    if provider == "unsplash" and kind == "video":
        _unsplash(query, kind, orientation, limit, "", fetch)  # raises the plain error before asking for a key
    key = C.env_key(KEYS[provider], env_file=env_file) if provider in KEYS else ""
    items = _SEARCH[provider](query, kind, orientation, limit, key, fetch)
    found = CACHE / "found"
    found.mkdir(parents=True, exist_ok=True)
    for it in items:  # so `stock get <ref>` and `use` can find the item again
        (found / f"{it['provider']}-{it['kind']}-{_stem(it['id'])}.json").write_text(json.dumps(it), encoding="utf-8")
    return items


def _stem(id) -> str:
    """A file name for a provider id. Unsplash ids are case-sensitive and may start with '-': keep the case, guard the start."""
    s = str(id).strip()
    if not re.fullmatch(r"[A-Za-z0-9_-][A-Za-z0-9._-]*", s) or ".." in s:
        raise ValueError(f"bad stock id {s!r}")
    return "_" + s if s.startswith("-") else s


def _paths(provider: str, kind: str, id: str) -> tuple[Path, Path]:
    base = CACHE / "stock" / C.safe_name(provider)
    stem = _stem(id)
    return base / f"{stem}.{ {'video': 'mp4', 'audio': 'mp3'}.get(kind, 'jpg') }", base / f"{stem}.json"


def download(item: dict, fetch=None, env_file: Path | None = None) -> Path:
    """Download one search result into the cache. Idempotent. Writes a sidecar .json with the item."""
    media, side = _paths(item["provider"], item["kind"], item["id"])
    if media.exists():
        return media
    if item["provider"] == "unsplash" and item.get("download_location"):  # Unsplash asks apps to report each download
        key = C.env_key(KEYS["unsplash"], env_file=env_file)
        C.http_get(item["download_location"], {"Authorization": f"Client-ID {key}"}, fetch)
    data = C.http_get(item["download_url"], {}, fetch)
    media.parent.mkdir(parents=True, exist_ok=True)
    tmp = media.with_suffix(media.suffix + ".part")
    tmp.write_bytes(data)
    tmp.replace(media)
    side.write_text(json.dumps(item, indent=1), encoding="utf-8")
    return media


def load_item(ref: str) -> dict:
    """The item for a ref like stock:pexels/video/123, from a download or from an earlier search."""
    kind, rest = C.parse_ref(ref)
    parts = rest.split("/")
    if kind != "stock" or len(parts) != 3:
        raise ValueError(f"bad stock ref {ref!r}: expected stock:provider/video|photo|audio/id")
    _, side = _paths(parts[0], parts[1], parts[2])
    found = CACHE / "found" / f"{C.safe_name(parts[0])}-{parts[1]}-{_stem(parts[2])}.json"
    for f in (side, found):
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8"))
    raise ValueError(f"unknown {ref}. Find it first: python anim.py stock search {parts[0]} \"...\" --type {parts[1]}")


def run(a) -> None:
    """CLI entry for `anim.py stock ...`."""
    import library
    if a.act == "search":
        orient = a.orientation or (library.video_orientation(resolve_project(C.ROOT, a.slug)) if a.slug else "landscape")
        names = ["openverse"] if a.type == "audio" else list(PROVIDERS) if a.provider == "all" else [a.provider]
        n = 0
        for p in names:
            if a.provider == "all" and p == "unsplash" and a.type == "video":
                continue
            try:
                items = search(p, a.query, a.type, orient, a.limit)
            except (C.KeyMissing, C.NetError) as e:
                if a.provider != "all":
                    raise
                print(f"  {p}: skipped ({e})")
                continue
            for it in items:
                n += 1
                dur = f"{it['duration']}s" if it["duration"] else "-"
                size = "audio" if it["kind"] == "audio" else f"{it['width']}x{it['height']}"
                print(f"{it['ref']:<44} {size:<10} {dur:<5} {it['author'][:22]:<22} {it['title'][:40]}")
        print(f"{n} results ({a.type}, {orient}). Next: python anim.py stock get <ref>  or  python anim.py use <slug> <ref>")
    elif a.act == "get":
        for ref in a.refs:
            print(f"{ref} -> {download(load_item(ref)).relative_to(C.ROOT)}")
