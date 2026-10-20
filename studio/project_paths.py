"""Safe identities for brand-scoped video projects."""
from __future__ import annotations
import json
import hashlib
import re
from pathlib import Path

class ProjectPathError(ValueError):
    pass

def _part(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-z0-9_][a-z0-9_-]*", value):
        raise ProjectPathError("invalid project identity")
    return value

def project_brand(path: Path) -> str:
    try:
        brand = json.loads((Path(path) / "project.json").read_text())["brand"]
    except (OSError, ValueError, KeyError) as e:
        raise ProjectPathError(f"project has no valid brand: {path}") from e
    return _part(brand)

def project_id(root: Path, path: Path) -> str:
    root, path = Path(root).resolve(), Path(path).resolve()
    try:
        parts = path.relative_to(root / "videos").parts
    except ValueError as e:
        raise ProjectPathError("project is outside videos") from e
    if len(parts) not in (1, 2):
        raise ProjectPathError("invalid project path")
    brand = project_brand(path)
    if len(parts) == 2 and parts[0] != brand:
        raise ProjectPathError(f"project brand differs from folder: {path}")
    return f"{brand}/{_part(parts[-1])}"

def iter_projects(root: Path):
    base = Path(root) / "videos"
    if not base.exists():
        return
    for child in sorted(base.iterdir()):
        if not child.is_dir():
            continue
        if child.is_symlink():
            raise ProjectPathError("project folders cannot be symbolic links")
        if (child / "project.json").is_file():
            project_id(root, child)
            yield child
        else:
            for path in sorted(child.iterdir()):
                if path.is_symlink():
                    raise ProjectPathError("project folders cannot be symbolic links")
                if path.is_dir() and (path / "project.json").is_file():
                    project_id(root, path)
                    yield path

def resolve_project(root: Path, video_id: str) -> Path:
    parts = video_id.split("/") if isinstance(video_id, str) else []
    if len(parts) not in (1, 2):
        raise ProjectPathError("use brand/slug or a unique slug")
    for part in parts:
        _part(part)
    matches = []
    for path in iter_projects(root):
        identity = project_id(root, path)
        if identity == video_id or (len(parts) == 1 and path.name == video_id):
            matches.append(path)
    if len(matches) != 1:
        raise ProjectPathError(f"{'ambiguous' if matches else 'unknown'} video '{video_id}'; use brand/slug")
    return matches[0]

def settings_snapshot(root: Path, path: Path, settings=None) -> dict:
    """Write once. Later brand edits cannot change an existing video voice."""
    target = Path(path) / "settings.json"
    brand = project_brand(path)
    if target.exists():
        value = json.loads(target.read_text())
        if not isinstance(value, dict) or value.get("brand") != brand:
            raise ProjectPathError("settings brand differs from project")
        return value
    voice = Path(root) / "brands" / brand / "voice.md"
    text = voice.read_text() if voice.is_file() else ""
    match = re.match(r"---\r?\n(.*?)\r?\n---", text, re.S)
    config = dict(re.findall(r"^(\w+):\s*(.+?)\s*$", match.group(1), re.M)) if match else {}
    metadata = json.loads((Path(path) / "project.json").read_text())
    sources = {}
    for name in ("voice.md", "brand.md", "tokens.js"):
        source = Path(root) / "brands" / brand / name
        if source.is_file():
            raw = source.read_bytes()
            sources[name] = {"sha256": hashlib.sha256(raw).hexdigest(), "content": raw.decode("utf-8")}
    value = {"brand": brand, "voice": config, "language": metadata.get("language"),
             "format": metadata.get("format"), "engine": metadata.get("engine"),
             "brand_sources": sources, **(settings or {})}
    if value["brand"] != brand:
        raise ProjectPathError("settings brand differs from project")
    with target.open("x") as out:
        out.write(json.dumps(value, indent=2) + "\n")
    return value
