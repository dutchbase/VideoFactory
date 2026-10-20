"""Prompt workshops and human review state for style and character records."""

from __future__ import annotations

import hashlib
import json
import functools
import math
import re
import shutil
import uuid
from pathlib import Path
from urllib.parse import urlsplit
from PIL import Image

from studio import workspace as ws

_GATES = {"style": ("brief", "materials", "sample"),
          "character": ("brief", "design", "identity")}
_HEADING = "## Studio creative review events"
_TEMPLATES = Path(__file__).resolve().parents[1] / "_templates"
_FORM_FIELDS = {"sessionId", "submittedAt", "durationMs", "notes", "skipped", "unanswered", "hidden"}
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
_RIG_VIEWS = ("front", "three-quarter-right")
_RIG_EVIDENCE = ("neutral", "blink", "mouth_contact_sheet", "head_movement", "elbows_bent", "hands_crossing_torso")
_RIG_MOUTHS = frozenset("ABCDEFGHX")


def _folder(root, subject_type, ident):
    if subject_type not in _GATES:
        raise ws.WorkspaceError("invalid", "Creative subject must be style or character.")
    path = ws.safe_path(root, f"{'styles' if subject_type == 'style' else 'characters'}/{ws._id(ident)}")
    if not path.is_dir():
        raise ws.WorkspaceError("missing", "Creative subject does not exist.")
    return path


def _gate(subject_type, gate):
    if gate in _GATES[subject_type]:
        return gate
    if subject_type == "character" and re.fullmatch(r"rig:[a-z0-9][a-z0-9-]*", gate or ""):
        return gate
    if subject_type == "character" and re.fullmatch(r"animation:[a-z0-9][a-z0-9-]*:[a-z0-9][a-z0-9-]*", gate or ""):
        return gate
    raise ws.WorkspaceError("invalid", "Unknown creative review gate.")


@ws._read_once
def _files(folder, subject_type, gate):
    brief = [folder / "01_brief/prompt.md", folder / "01_brief/answers.json", folder / "01_brief/brief.md"] if subject_type == "style" else [folder / "01_design/prompt.md", folder / "01_design/answers.json", folder / "01_design/brief.md"]
    if gate == "brief":
        return brief if subject_type == "style" else brief + [folder / "character.md"]
    if subject_type == "style":
        if gate == "materials":
            files = [folder / "style.md", folder / "materials.md"]
            files += sorted(p for p in (folder / "02_assets").rglob("*") if p.is_file() and not p.name.startswith("."))
            root = folder.parents[1]
            for material_id in ws._read_links(folder / "materials.md"):
                material = ws.safe_path(root, f"library/materials/{material_id}")
                if material.is_dir():
                    files.extend(sorted(p for p in material.iterdir() if p.is_file()))
                    source = ws._material(root, material_id)["source"]
                    if source != "upload" and not source.startswith(("http:", "https:")):
                        files.append(ws.safe_path(root, source))
            references = ws._style(root, folder.name)["references"]
            files.extend(ws._style_reference_path(root, path) for path in references)
            return files
        return sorted(p for directory in (folder / "03_sample", folder / "template")
                      for p in directory.rglob("*") if p.is_file() and not p.name.startswith("."))
    if gate == "design":
        files = [folder / "01_design/candidates.json"] + sorted(p for p in (folder / "01_design/candidates").rglob("*") if p.is_file())
        if files[0].is_file():
            try:
                candidates = json.loads(files[0].read_text(encoding="utf-8"))
                if isinstance(candidates, list): files += [ws.safe_path(folder.parents[1], c["path"]) for c in candidates if isinstance(c, dict) and isinstance(c.get("path"), str)]
            except ValueError: pass
        return files
    if gate == "identity":
        files = [folder / "02_identity/reference-set.json"] + sorted(p for p in (folder / "02_identity").rglob("*") if p.is_file() and p.name != "reference-set.json")
        if files[0].is_file():
            try:
                references = json.loads(files[0].read_text(encoding="utf-8"))
                if isinstance(references, dict): files += [ws.safe_path(folder.parents[1], references[k]) for k in ("candidate_path", "sheet", "in_scene") if isinstance(references.get(k), str)]
            except ValueError: pass
        return files
    if gate.startswith("rig:"):
        variant = gate.split(":", 1)[1]
        pack = folder / "03_animation" / variant
        native = pack / "native-candidate" if (pack / "native-candidate/manifest.json").is_file() else pack / "native"
        return [pack / "variant.json", pack / "assets.json", pack / "rig.json"] + sorted(
            p for p in native.rglob("*") if p.is_file() and
            p.relative_to(native).parts[0] != "renders" and
            not any(part.startswith(".") for part in p.relative_to(native).parts))
    _, variant, action = gate.split(":")
    pack = folder / "03_animation" / variant
    if (pack / "native/manifest.json").is_file():
        from studio.native_pipeline import render_status
        files = []
        for view in _RIG_VIEWS:
            status = render_status(folder.parents[1], folder.name, variant, view, action, "neutral")
            clip = status.get("clip")
            if not clip: continue
            output = ws.safe_path(folder.parents[1], clip["path"])
            files += [output / "render.json", output / "preview.mp4"]
            try:
                rendered = json.loads((output / "render.json").read_text(encoding="utf-8"))
                frames = rendered["frames"]
                files += [output / "frames" / frames[index]["file"] for index in (0, len(frames) // 2, len(frames) - 1)]
            except (OSError, ValueError, TypeError, KeyError, IndexError): pass
        return list(dict.fromkeys(files))
    files = [pack / "assets.json", pack / "rig.json", pack / "motions.json", pack / "variant.json"]
    files += sorted(p for directory in (pack / "preview" / action, pack / "assets", pack / "frames" / action)
                    for p in directory.rglob("*") if p.is_file() and
                    not any(part.startswith(".") for part in p.relative_to(directory).parts))
    files += _referenced_artwork(folder.parents[1], pack, files[:4])
    return files


def _referenced_artwork(root, pack, manifests):
    def walk(value):
        if isinstance(value, str) and Path(value).suffix.lower() in _IMAGE_EXTENSIONS:
            if value.startswith("/") or "\\" in value:
                raise ws.WorkspaceError("invalid", "Animation artwork must use a public workspace path.")
            relative = value if value.split("/", 1)[0] in ws.SHELVES else (pack / value).relative_to(root).as_posix()
            yield ws.safe_path(root, relative)
        elif isinstance(value, dict):
            for child in value.values(): yield from walk(child)
        elif isinstance(value, list):
            for child in value: yield from walk(child)

    paths = []
    for manifest in manifests:
        if manifest.is_file():
            try: paths.extend(walk(json.loads(manifest.read_text(encoding="utf-8"))))
            except ValueError: pass
    return list(dict.fromkeys(paths))


def _validate_rig_evidence(native, registration):
    """Check review images against the current registered source revision.

    This only makes a rig eligible for a human review decision; it never
    marks the rig approved. All evidence remains part of the rig fingerprint.
    """
    evidence_path = native / "rig-review.json"
    try:
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("rig review evidence registry is missing or malformed") from exc
    if not isinstance(evidence, dict) or evidence.get("schema") != 1:
        raise ValueError("rig review evidence schema must be 1")
    if evidence.get("source_sha256") != ws._file_hash(native / "manifest.json"):
        raise ValueError("rig review evidence does not match the current native source")
    projects = registration.get("projects")
    controls = registration.get("controls")
    if not isinstance(projects, dict) or not set(_RIG_VIEWS) <= projects.keys():
        raise ValueError("native rig needs both registered views")
    mouth_controls = controls.get("mouth_shapes") if isinstance(controls, dict) else None
    if (not isinstance(mouth_controls, list) or len(mouth_controls) != len(_RIG_MOUTHS) or
            not all(isinstance(item, str) for item in mouth_controls) or set(mouth_controls) != _RIG_MOUTHS):
        raise ValueError("native rig needs A–H and closed mouth controls")
    views = evidence.get("views")
    if not isinstance(views, dict) or not set(_RIG_VIEWS) <= views.keys():
        raise ValueError("rig review evidence needs both views")
    seen_paths = set()
    for view in _RIG_VIEWS:
        record = views[view]
        mouth_states = record.get("mouth_states") if isinstance(record, dict) else None
        if (not isinstance(mouth_states, list) or len(mouth_states) != len(_RIG_MOUTHS) or
                not all(isinstance(item, str) for item in mouth_states) or set(mouth_states) != _RIG_MOUTHS):
            raise ValueError(f"{view} evidence needs A–H and closed mouth state metadata")
        images = record.get("images")
        if not isinstance(images, dict) or not set(_RIG_EVIDENCE) <= images.keys():
            raise ValueError(f"{view} is missing required rig review images")
        for role in _RIG_EVIDENCE:
            item = images[role]
            if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not isinstance(item.get("sha256"), str):
                raise ValueError(f"{view} {role} evidence is malformed")
            relative = Path(item["path"])
            if relative.is_absolute() or ".." in relative.parts or not relative.parts or any(part.startswith(".") for part in relative.parts) or "\\" in item["path"]:
                raise ValueError(f"{view} {role} evidence path is unsafe")
            path = (native / relative).resolve()
            try:
                path.relative_to(native.resolve())
            except ValueError as exc:
                raise ValueError(f"{view} {role} evidence escapes native folder") from exc
            if path in seen_paths:
                raise ValueError(f"{view} {role} evidence must be a distinct image")
            seen_paths.add(path)
            if not path.is_file() or path.suffix.lower() != ".png" or ws._file_hash(path) != item["sha256"]:
                raise ValueError(f"{view} {role} evidence image is missing or stale")
            try:
                with Image.open(path) as image:
                    image.load()
                    if image.mode not in {"RGB", "RGBA"} or min(image.size) < 128:
                        raise ValueError(f"{view} {role} evidence image is not a readable 128px RGB image")
            except OSError as exc:
                raise ValueError(f"{view} {role} evidence image cannot be decoded") from exc


def _answer_has_value(value):
    if isinstance(value, str): return bool(value.strip())
    if isinstance(value, bool): return True
    if isinstance(value, (int, float)): return math.isfinite(value)
    if isinstance(value, list): return any(_answer_has_value(item) for item in value)
    if isinstance(value, dict):
        if "type" in value and "value" in value:
            return isinstance(value["type"], str) and bool(value["type"]) and _answer_has_value(value["value"])
        return any(_answer_has_value(item) for item in value.values())
    return False


def _answers_complete(data):
    if not isinstance(data, dict): return False
    envelope = isinstance(data.get("answers"), dict) and (set(data) & _FORM_FIELDS or set(data) == {"answers"})
    if envelope and "sessionId" in data and not data.get("submittedAt"): return False
    values = data["answers"] if envelope else data
    return bool(values) and all(isinstance(key, str) and key.strip() and _answer_has_value(value) for key, value in values.items())


def _previous(subject_type, gate, folder):
    if gate == "brief": return None
    if subject_type == "style": return "brief" if gate == "materials" else "materials"
    if gate == "design": return "brief"
    if gate == "identity": return "design"
    if gate.startswith("rig:"): return "identity"
    variant = gate.split(":")[1]
    rig_gate = "rig:" + variant
    if (folder / "03_animation" / variant / "native/manifest.json").is_file():
        return rig_gate
    return "identity"


@ws._read_once
def creative_fingerprint(root, subject_type, id, gate):
    folder = _folder(root, subject_type, id)
    _gate(subject_type, gate)
    digest = hashlib.sha256()
    digest.update(f"{subject_type}/{id}/{gate}\n".encode())
    previous = _previous(subject_type, gate, folder)
    if previous:
        digest.update(creative_fingerprint(root, subject_type, id, previous).encode())
    files = _files(folder, subject_type, gate)
    if subject_type == "character" and gate.startswith("animation:") and not (folder / "03_animation" / gate.split(":")[1] / "native/manifest.json").is_file():
        from studio.character_motion import _source_revision
        _, variant, action = gate.split(":")
        digest.update(_source_revision(root, id, variant, action).encode())
        files = [path for path in files if f"/preview/{action}/" in path.as_posix() or f"/frames/{action}/" in path.as_posix()]
    for path in files:
        relative = path.relative_to(root).as_posix()
        (ws._style_reference_path if relative.startswith("_templates/") else ws.safe_path)(root, relative)
        digest.update(relative.encode() + b"\0")
        digest.update(ws._file_hash(path).encode() if path.is_file() else b"missing")
    return digest.hexdigest()


@ws._read_once
def _events(folder, subject_type):
    path = ws.safe_path(folder.parents[1], (folder / "REVIEW.md").relative_to(folder.parents[1]).as_posix())
    prose = path.read_text(encoding="utf-8") if path.is_file() else "# Creative reviews\n"
    if _HEADING not in prose:
        return prose, []
    head, tail = prose.split(_HEADING, 1)
    blocks = re.findall(r"```json\s*\n(.*?)\n```", tail, re.S)
    try:
        events = json.loads(blocks[0]) if len(blocks) == 1 else None
    except ValueError:
        events = None
    if not isinstance(events, list) or any(not isinstance(e, dict) or not {"gate", "kind", "fingerprint", "at"} <= e.keys() or
                                           e["kind"] not in {"ready", "decision"} or not isinstance(e["fingerprint"], str) or
                                           not isinstance(e["at"], str) for e in events):
        raise ws.WorkspaceError("invalid", "Creative review events are malformed.")
    for event in events:
        _gate(subject_type, event["gate"])
    return head.rstrip() + "\n", events


def _write_event(folder, subject_type, event):
    prose, events = _events(folder, subject_type)
    events = [*events, event]
    ws._atomic_write(folder / "REVIEW.md", (prose.rstrip() + "\n\n" + _HEADING + "\n\n```json\n" +
                                               json.dumps(events, ensure_ascii=False, indent=2) + "\n```\n").encode())


def _readiness(root, subject_type, id, gate):
    folder = _folder(root, subject_type, id)
    missing = []
    previous = _previous(subject_type, gate, folder)
    if previous and creative_review_state(root, subject_type, id, previous)["state"] != "approved":
        missing.append(f"current {previous} approval")
    files = _files(folder, subject_type, gate)
    if gate == "brief":
        if not files[0].is_file() or not files[0].read_text(encoding="utf-8").strip():
            missing.append("saved prompt")
        answers = files[1]
        try:
            data = json.loads(answers.read_text(encoding="utf-8"))
            if not _answers_complete(data):
                raise ValueError
        except (OSError, ValueError):
            missing.append("complete workshop answers")
        if not files[2].is_file() or not files[2].read_text(encoding="utf-8").strip() or "<!--" in files[2].read_text(encoding="utf-8"):
            missing.append("completed brief")
    elif gate == "materials":
        description = files[1].read_text(encoding="utf-8").split("## Linked materials", 1)[0] if files[1].is_file() else ""
        description = re.sub(r"(?m)^\s*#+\s*[^\n]+", "", description).strip()
        if len(description) < 20:
            missing.append("described materials")
    elif gate == "sample":
        from studio.references import sample_valid
        formats = ws._style(root, id)["supported_formats"]
        if not formats: missing.append("claimed style format")
        for fmt in formats:
            if not sample_valid(root, id, fmt):
                missing.append(f"{fmt} style sample")
    elif gate == "design":
        try:
            from studio.characters import _registered_candidates
            candidates = _registered_candidates(root, id)
            if sum(candidate["selected"] for candidate in candidates) != 1: raise ValueError
        except (OSError, ValueError, TypeError, KeyError, ws.WorkspaceError):
            missing.append("three readable candidate artworks and one selection")
    elif gate == "identity":
        try:
            from studio.characters import _registered_reference
            _registered_reference(root, id)
        except (OSError, ValueError, TypeError, KeyError, AttributeError, ws.WorkspaceError):
            missing.append("canonical candidate, constraints, sheet and in-scene references")
    elif gate.startswith("rig:"):
        from studio.native_character import NativeCharacterError, validate_native_registration
        from studio.characters import _registered_variant
        variant = gate.split(":", 1)[1]
        pack = folder / "03_animation" / variant
        native = pack / "native-candidate" if (pack / "native-candidate/manifest.json").is_file() else pack / "native"
        try:
            _registered_variant(root, id, variant)
            registration = validate_native_registration(native / "manifest.json")
            renderer = registration.get("capabilities", {}).get("renderer")
            if (not isinstance(renderer, dict) or renderer.get("name") != "Synfig" or
                    "1.4.5" not in str(renderer.get("version", "")) or
                    not renderer.get("pinned") or not renderer.get("png_target")):
                missing.append("pinned Synfig 1.4.5 with PNG output")
            try:
                _validate_rig_evidence(native, registration)
            except ValueError as exc:
                missing.append(str(exc))
        except (NativeCharacterError, OSError, TypeError, AttributeError, ws.WorkspaceError):
            missing.append("current validated native project and linked artwork")
    else:
        _, variant, action = gate.split(":")
        if (folder / "03_animation" / variant / "native/manifest.json").is_file():
            from studio.native_pipeline import render_status
            for view in _RIG_VIEWS:
                status = render_status(root, id, variant, view, action, "neutral")
                if not status["current"] or not status.get("clip"):
                    missing.append(f"current native {action} clip for {view}")
        else:
            try:
                from studio.character_motion import animation_export_valid, compile_character_pack, VIEWS
                data = compile_character_pack(root, id, variant, action=action)
                if not all(animation_export_valid(root, id, variant, action, view, manifest=data) for view in VIEWS):
                    missing.append("current rendered previews and frame exports for both views")
                else:
                    selections = [json.loads((folder / "03_animation" / variant / "frames" / action / view / "index.json").read_text(encoding="utf-8"))["prop"] for view in VIEWS]
                    if selections[0] != selections[1]:
                        missing.append("same selected prop in both views")
            except (OSError, ValueError, TypeError, KeyError, ws.WorkspaceError):
                missing.append("current registered character pack and action")
    return not missing, missing


def _native_request(function):
    """Share native render checks across one detail or review request."""
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        from studio.native_pipeline import request_cache
        with request_cache():
            return function(*args, **kwargs)
    return wrapper


@_native_request
@ws._read_once
def creative_review_state(root, subject_type, id, gate):
    folder = _folder(root, subject_type, id)
    _gate(subject_type, gate)
    fingerprint = creative_fingerprint(root, subject_type, id, gate)
    prose, events = _events(folder, subject_type)
    history = [e for e in events if e["gate"] == gate]
    current = [e for e in history if e["fingerprint"] == fingerprint]
    ready, missing = _readiness(root, subject_type, id, gate)
    state = "draft"
    if history and not current:
        state = "stale"
    elif current:
        latest = current[-1]
        state = latest.get("decision", "draft") if latest["kind"] == "decision" else "awaiting-review"
    if not ready and state in {"approved", "awaiting-review"}:
        state = "stale"
    return {"gate": gate, "state": state, "fingerprint": fingerprint, "revision": fingerprint,
            "ready": ready, "missing": missing, "history": history, "legacy": prose.strip(),
            "artifacts": [p.relative_to(root).as_posix() for p in _files(folder, subject_type, gate) if p.is_file()],
            "review_path": f"/api/creative/{subject_type}/{id}/reviews/{gate}"}


def review_summaries(root):
    def read():
        rows = []
        for subject_type, shelf in (("style", "styles"), ("character", "characters")):
            parent = ws.safe_path(root, shelf)
            if not parent.is_dir():
                continue
            for folder in sorted(parent.iterdir()):
                if not folder.is_dir() or folder.is_symlink() or not ws.ID.fullmatch(folder.name):
                    continue
                try:
                    events = _events(folder, subject_type)[1]
                    gates = list(dict.fromkeys(event["gate"] for event in events))
                    profile = ws.safe_path(root, f"{shelf}/{folder.name}/{subject_type}.md")
                    title = re.search(r'(?m)^title: (".*")$', profile.read_text(encoding="utf-8")) if profile.is_file() else None
                    rows.append({"type": subject_type, "id": folder.name, "title": json.loads(title[1]) if title else folder.name,
                                 "reviews": {gate: ws._review_summary(gate, events) for gate in gates}})
                except (ws.WorkspaceError, ValueError, UnicodeDecodeError) as exc:
                    rows.append({"type": subject_type, "id": folder.name, "error": str(exc), "reviews": {}})
        return rows
    return ws.readcache.cached(root, "creative-reviews", read)


@_native_request
@ws._read_once
def creative_detail(root, subject_type, id):
    folder = _folder(root, subject_type, id)
    workshop_path = ws.safe_path(root, (folder / "workshop.json").relative_to(root).as_posix())
    workshop = json.loads(workshop_path.read_text(encoding="utf-8")) if workshop_path.is_file() else {"state": "legacy", "form_url": None}
    gates = list(_GATES[subject_type])
    if subject_type == "character":
        animation = folder / "03_animation"
        prior_rigs = {event["gate"] for event in _events(folder, subject_type)[1] if event["gate"].startswith("rig:")}
        if animation.is_dir():
            for variant in sorted(animation.iterdir()):
                if variant.is_dir() and ws.ID.fullmatch(variant.name) and ((variant / "native/manifest.json").is_file() or
                        (variant / "native-candidate/manifest.json").is_file() or f"rig:{variant.name}" in prior_rigs):
                    gates.append(f"rig:{variant.name}")
                if variant.is_dir() and ws.ID.fullmatch(variant.name) and (variant / "motions.json").is_file():
                    try: actions = json.loads((variant / "motions.json").read_text(encoding="utf-8")).get("actions", {})
                    except (ValueError, AttributeError): actions = {}
                    if isinstance(actions, dict):
                        gates += [f"animation:{variant.name}:{action}" for action in actions if ws.ID.fullmatch(action)]
                active_manifest = variant / "native/manifest.json"
                if variant.is_dir() and ws.ID.fullmatch(variant.name) and active_manifest.is_file():
                    try:
                        bindings = json.loads(active_manifest.read_text(encoding="utf-8")).get("controls", {}).get("bindings", {})
                        gates += [f"animation:{variant.name}:{action}" for views in bindings.values() if isinstance(views, dict)
                                  for action in views if ws.ID.fullmatch(action)]
                    except (ValueError, AttributeError, TypeError): pass
        gates = list(dict.fromkeys(gates))
    reviews = {gate: creative_review_state(root, subject_type, id, gate) for gate in gates}
    revision = hashlib.sha256(("".join(reviews[g]["fingerprint"] for g in gates) + json.dumps(workshop, sort_keys=True)).encode()).hexdigest()
    return {"subject": {"type": subject_type, "id": id}, "path": folder.relative_to(root).as_posix(),
            "revision": revision, "workshop": workshop, "reviews": reviews}


def create_creative(root, subject_type, id, prompt, metadata):
    if subject_type not in _GATES or not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 20000 or not isinstance(metadata, dict):
        raise ws.WorkspaceError("invalid", "A style or character needs a prompt and metadata.")
    ws._id(id)
    title = metadata.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ws.WorkspaceError("invalid", "Creative title is required.")
    root = Path(root).resolve()
    if subject_type == "style":
        allowed = {"title", "base_kit", "family_id", "renderer", "supported_formats", "origin", "reference_videos", "references", "readiness",
                   "setting", "environment", "components", "captions", "voice_guidance", "motion_guidance", "visual_instructions"}
        if set(metadata) - allowed: raise ws.WorkspaceError("invalid", "Unknown style metadata.")
        ws.create_style(root, id, title, metadata.get("base_kit", "modern"), **{k: v for k, v in metadata.items() if k not in {"title", "base_kit"}})
    else:
        if set(metadata) - {"title", "description"}: raise ws.WorkspaceError("invalid", "Unknown character metadata.")
        folder = root / "characters" / id
        with ws.workspace_lock(root):
            if folder.exists(): raise ws.WorkspaceError("conflict", "Character ID already exists.")
            folder.mkdir(parents=True)
            profile = {"id": id, **metadata, "identity": "draft", "personality": "",
                       "appearance": {"hair": None, "eyes": None, "face": None, "proportions": None},
                       "clothing": "", "references": [], "voice": "", "relationships": []}
            ws._atomic_write(folder / "character.md", ws._record(profile,
                "\n## Identity\n\n## Personality\n\n## Appearance\n\n## Clothing\n\n## References\n\n## Voice\n\n## Relationships\n").encode())
            ws._atomic_write(folder / "materials.md", b"# Character materials\n")
    folder = _folder(root, subject_type, id)
    template = _TEMPLATES / ("style-factory" if subject_type == "style" else "character-factory")
    if template.is_dir(): shutil.copytree(template, folder, dirs_exist_ok=True)
    brief_dir = folder / ("01_brief" if subject_type == "style" else "01_design")
    ws._atomic_write(brief_dir / "prompt.md", (prompt.strip() + "\n").encode("utf-8"))
    ws._atomic_write(brief_dir / "answers.json", b"{}\n")
    ws._atomic_write(folder / "workshop.json", json.dumps({"state": "waiting-for-agent", "form_url": None}, indent=2).encode())
    from studio import jobs
    jobs.create_request(root, None, f"{subject_type}-discovery", f"Open Brainstormform for {subject_type} {id}; save complete answers and a brief. Prompt: {prompt.strip()}",
                        None, uuid.uuid4().hex, subject={"type": subject_type, "id": id},
                        input_revision=creative_fingerprint(root, subject_type, id, "brief"))
    return creative_detail(root, subject_type, id)


def save_workshop_answers(root, subject_type, id, answers, *, brief=None, form_url=None, expected_revision=None):
    folder = _folder(root, subject_type, id)
    if answers is not None:
        if not isinstance(answers, dict): raise ws.WorkspaceError("invalid", "Workshop answers must be a JSON object.")
        try: encoded_answers = (json.dumps(answers, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()
        except (TypeError, ValueError, OverflowError): raise ws.WorkspaceError("invalid", "Workshop answers must be valid JSON.") from None
        if len(encoded_answers) > ws.TEXT_LIMIT: raise ws.WorkspaceError("invalid", "Workshop answers exceed 2 MiB.")
    if brief is not None and (not isinstance(brief, str) or len(brief) > ws.TEXT_LIMIT):
        raise ws.WorkspaceError("invalid", "Invalid workshop brief.")
    if form_url is not None:
        if not isinstance(form_url, str):
            raise ws.WorkspaceError("invalid", "Form URL must be HTTP or HTTPS without credentials.")
        parsed = urlsplit(form_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
            raise ws.WorkspaceError("invalid", "Form URL must be HTTP or HTTPS without credentials.")
    with ws.workspace_lock(root):
        if expected_revision != creative_detail(root, subject_type, id)["revision"]:
            raise ws.WorkspaceError("conflict", "Creative inputs changed since you opened them.")
        brief_dir = folder / ("01_brief" if subject_type == "style" else "01_design")
        if answers is not None: ws._atomic_write(brief_dir / "answers.json", encoded_answers)
        if brief is not None: ws._atomic_write(brief_dir / "brief.md", (brief.strip() + "\n").encode())
        workshop = json.loads((folder / "workshop.json").read_text(encoding="utf-8"))
        if form_url is not None: workshop["form_url"] = form_url
        workshop["state"] = ("answers-saved" if _answers_complete(answers) else "answers-draft") if answers is not None else "form-open" if form_url else workshop["state"]
        ws._atomic_write(folder / "workshop.json", (json.dumps(workshop, ensure_ascii=False, indent=2) + "\n").encode())
    return creative_detail(root, subject_type, id)


def mark_creative_ready(root, subject_type, id, gate, expected_revision):
    folder = _folder(root, subject_type, id)
    with ws.workspace_lock(root):
        state = creative_review_state(root, subject_type, id, gate)
        if expected_revision != state["fingerprint"]: raise ws.WorkspaceError("conflict", "Review inputs changed since you opened them.")
        if not state["ready"]: raise ws.WorkspaceError("blocked", "Review is incomplete: " + ", ".join(state["missing"]))
        if state["state"] in {"awaiting-review", "approved", "changes-requested"}: return state
        _write_event(folder, subject_type, {"gate": gate, "kind": "ready", "decision": None, "reviewer": None, "note": "", "fingerprint": expected_revision, "at": ws._now()})
    return creative_review_state(root, subject_type, id, gate)


def decide_creative(root, subject_type, id, gate, decision, reviewer, note, expected_revision):
    folder = _folder(root, subject_type, id)
    if decision not in {"approved", "changes-requested"} or not isinstance(reviewer, str) or not reviewer.strip() or not isinstance(note, str):
        raise ws.WorkspaceError("invalid", "Provide a reviewer and an approval or changes-requested decision.")
    with ws.workspace_lock(root):
        state = creative_review_state(root, subject_type, id, gate)
        if expected_revision != state["fingerprint"]: raise ws.WorkspaceError("conflict", "Review inputs changed since you opened them.")
        if state["state"] not in {"awaiting-review", "approved", "changes-requested"} or not state["ready"]:
            raise ws.WorkspaceError("blocked", "Mark this complete revision ready before deciding.")
        if state["state"] == "approved" and decision == "approved": return state
        _write_event(folder, subject_type, {"gate": gate, "kind": "decision", "decision": decision, "reviewer": reviewer.strip(), "note": note, "fingerprint": expected_revision, "at": ws._now()})
    return creative_review_state(root, subject_type, id, gate)
