"""Character concepts and canonical identity records for the reviewed creative workflow."""

from __future__ import annotations

import json
import ctypes
import os
import re
import shutil
import uuid
from pathlib import Path

from PIL import Image

from studio import workspace as ws
from studio.creative import create_creative, creative_detail, creative_review_state
from studio.generation import generation_detail, prepare_generation

_VIEWS = ["front", "three-quarter-right"]
_APPEARANCE = {"hair", "eyes", "face", "proportions", "clothing"}


def _folder(root, ident):
    folder = ws.safe_path(root, f"characters/{ws._id(ident)}")
    if not folder.is_dir():
        raise ws.WorkspaceError("missing", "Character does not exist.")
    return folder


def _json(path):
    try:
        raw = path.read_bytes()
        if len(raw) > ws.TEXT_LIMIT:
            raise ValueError
        data = json.loads(raw)
        name = path.name
        if name == "candidates.json":
            keys = {"id", "path", "sha256", "generation_id", "provider", "selected", "material_id"}
            if (not isinstance(data, list) or len(data) != 3 or any(not isinstance(c, dict) or set(c) != keys or
                not all(isinstance(c[k], str) and 0 < len(c[k]) <= 2000 for k in keys - {"selected"}) or
                not isinstance(c["selected"], bool) or c["provider"] != "openai" or
                not re.fullmatch(r"[0-9a-f]{64}", c["sha256"]) for c in data)): raise ValueError
            if (len({c["id"] for c in data}) != 3 or len({c["generation_id"] for c in data}) != 1 or
                    len({c["path"] for c in data}) != 3 or len({c["sha256"] for c in data}) != 3 or
                    sum(c["selected"] for c in data) > 1): raise ValueError
        elif name == "reference-set.json":
            keys = {"candidate_id", "candidate_path", "candidate_sha256", "appearance", "views", "sheet", "sheet_sha256",
                    "in_scene", "in_scene_sha256", "material_ids", "generation_id", "design_revision"}
            if (not isinstance(data, dict) or set(data) != keys or data["views"] != _VIEWS or
                not isinstance(data["appearance"], dict) or set(data["appearance"]) != _APPEARANCE or
                any(not isinstance(v, str) or not v.strip() or len(v) > 2000 for v in data["appearance"].values()) or
                not isinstance(data["material_ids"], dict) or set(data["material_ids"]) != {"sheet", "in-scene"} or
                any(not isinstance(v, str) or not v or len(v) > 2000 for v in data["material_ids"].values()) or
                any(not isinstance(data[k], str) or not data[k] or len(data[k]) > 2000 for k in keys - {"appearance", "views", "material_ids"}) or
                any(not re.fullmatch(r"[0-9a-f]{64}", data[k]) for k in ("candidate_sha256", "sheet_sha256", "in_scene_sha256", "design_revision"))): raise ValueError
        elif name == "variant.json":
            keys = {"generation_id", "style_id", "views", "appearance", "monochrome_exception", "id", "identity_revision",
                    "reference_set_sha256", "reference_material_ids", "artwork"}
            art = data.get("artwork") if isinstance(data, dict) else None
            if (not isinstance(data, dict) or set(data) != keys or data["views"] != _VIEWS or
                not isinstance(data["appearance"], dict) or set(data["appearance"]) != _APPEARANCE or
                any(not isinstance(v, str) or not v.strip() or len(v) > 2000 for v in data["appearance"].values()) or
                not isinstance(data["monochrome_exception"], bool) or
                not isinstance(data["reference_material_ids"], dict) or set(data["reference_material_ids"]) != {"sheet", "in-scene"} or
                any(not isinstance(v, str) or not v or len(v) > 2000 for v in data["reference_material_ids"].values()) or
                not isinstance(art, dict) or set(art) != {"path", "sha256", "views"} or art["views"] != _VIEWS or
                not isinstance(art["path"], str) or not art["path"] or len(art["path"]) > 2000 or
                not isinstance(art["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", art["sha256"]) or
                any(not isinstance(data[k], str) or not data[k] or len(data[k]) > 2000 for k in keys - {"views", "appearance", "monochrome_exception", "reference_material_ids", "artwork"}) or
                any(not re.fullmatch(r"[0-9a-f]{64}", data[k]) for k in ("identity_revision", "reference_set_sha256"))): raise ValueError
        return data
    except (OSError, ValueError, UnicodeError, TypeError, KeyError):
        raise ws.WorkspaceError("invalid", f"Unreadable character record: {path.name}.") from None


def _art(root, relative, sha=None):
    path = ws.safe_path(root, relative)
    if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"} or not path.is_file():
        raise ws.WorkspaceError("invalid", "Character artwork must be a saved raster image.")
    try:
        with Image.open(path) as image: image.verify()
    except (OSError, ValueError):
        raise ws.WorkspaceError("invalid", "Character artwork is unreadable.") from None
    digest = ws._file_hash(path)
    if sha is not None and sha != digest:
        raise ws.WorkspaceError("conflict", "Character artwork changed.")
    return digest


def _profile(root, ident):
    path = _folder(root, ident) / "character.md"
    data, _ = ws._frontmatter(path.read_text(encoding="utf-8"), {"id", "title"},
        {"id", "title", "description", "identity", "personality", "appearance", "clothing", "references", "voice", "relationships"})
    if data["id"] != ident:
        raise ws.WorkspaceError("invalid", "Character profile ID does not match its folder.")
    return data


def _catalog_preview(root, ident, identity_state):
    folder = _folder(root, ident)
    choices = []
    try:
        reference = folder / "02_identity/reference-set.json"
        if reference.is_file():
            record = _json(reference)
            choices.extend((record[name], record[name + "_sha256"], kind, identity_state)
                           for name, kind in (("in_scene", "in-scene"), ("sheet", "sheet")))
    except ws.WorkspaceError:
        pass
    try:
        candidates = folder / "01_design/candidates.json"
        if candidates.is_file():
            records = _json(candidates)
            try: state = creative_review_state(root, "character", ident, "design")["state"]
            except ws.WorkspaceError: state = "stale"
            choices.extend((item["path"], item["sha256"], "concept", state)
                           for item in sorted(records, key=lambda item: not item["selected"]))
    except ws.WorkspaceError:
        pass
    for path, digest, kind, state in choices:
        if not path.startswith(f"characters/{ident}/generated/"):
            continue
        try:
            _art(root, path, digest)
            return {"path": path, "kind": kind, "state": state}
        except ws.WorkspaceError:
            continue
    return None


def list_characters(root):
    result = []
    shelf = Path(root) / "characters"
    if shelf.is_dir():
        for folder in sorted(shelf.iterdir()):
            if folder.is_dir() and not folder.is_symlink() and ws.ID.fullmatch(folder.name) and (folder / "character.md").is_file():
                try:
                    profile = _profile(root, folder.name)
                    try: state = creative_review_state(root, "character", folder.name, "identity")
                    except ws.WorkspaceError: state = {"state": "stale"}
                    try: brief_state = creative_review_state(root, "character", folder.name, "brief")["state"]
                    except ws.WorkspaceError: brief_state = "stale"
                    result.append({"id": folder.name, "title": profile["title"], "description": profile.get("description", ""),
                                   "origin": "character-workshop", "approved": state["state"] == "approved", "identity_state": state["state"],
                                   "brief_state": brief_state, "references": profile.get("references", []),
                                   "preview": _catalog_preview(root, folder.name, state["state"])})
                except (ws.WorkspaceError, OSError, ValueError):
                    result.append({"id": folder.name, "origin": "character-workshop", "approved": False, "error": "Unreadable character record"})
    return result


def create_character(root, id, prompt, metadata):
    if not isinstance(metadata, dict) or set(metadata) - {"title", "description"}:
        raise ws.WorkspaceError("invalid", "Unknown character metadata.")
    create_creative(root, "character", id, prompt, metadata)
    return character_detail(root, id)


def character_detail(root, id):
    detail = creative_detail(root, "character", id)
    folder = _folder(root, id)
    detail["profile"] = _profile(root, id)
    path = folder / "01_design/candidates.json"
    detail["candidates"] = _json(path) if path.is_file() else []
    detail["candidate_revision"] = ws._file_hash(path) if path.is_file() else None
    path = folder / "02_identity/reference-set.json"
    detail["reference_set"] = _json(path) if path.is_file() else None
    detail["reference_revision"] = ws._file_hash(path) if path.is_file() else None
    variants = folder / "03_animation"
    detail["variants"] = []
    if variants.is_dir():
        for path in sorted(variants.glob("*/variant.json")):
            variant = _json(path)
            actions = [review for gate, review in detail["reviews"].items() if gate.startswith(f"animation:{path.parent.name}:")]
            try:
                current = (detail["reviews"]["identity"]["state"] in {"approved", "accepted"} and
                           variant["identity_revision"] == detail["reviews"]["identity"]["fingerprint"] and
                           _registered_variant(root, id, path.parent.name))
            except (KeyError, ws.WorkspaceError):
                current = False
            variant["state"] = ("stale" if not current or any(action["state"] == "stale" for action in actions)
                                else "approved" if actions and all(action["state"] == "approved" for action in actions)
                                else "accepted" if actions and all(action["state"] in {"approved", "accepted"} for action in actions)
                                else "draft")
            variant["revision"] = ws._file_hash(path)
            detail["variants"].append(variant)
    return detail


def character_capabilities(root, id, variant):
    """Describe authored motion without treating a draft pack as a valid export."""
    from studio.character_motion import ACTIONS, VIEWS, _read, animation_export_valid, compile_character_pack

    pack = _folder(root, id) / "03_animation" / ws._id(variant)
    if not pack.is_dir():
        raise ws.WorkspaceError("missing", "Character variant does not exist.")
    authored = {"actions": [], "views": [], "expressions": []}
    supported = {"actions": [], "views": [], "expressions": []}
    error = None
    try:
        motions, assets, rig = (_read(pack / f"{name}.json") for name in ("motions", "assets", "rig"))
        actions = motions.get("actions", {}) if isinstance(motions, dict) else {}
        views = assets.get("views", {}) if isinstance(assets, dict) else {}
        rig_views = rig.get("views", {}) if isinstance(rig, dict) else {}
        if not all(isinstance(value, dict) for value in (actions, views, rig_views)):
            raise ValueError("Malformed character pack")
        authored["actions"] = sorted(set(actions) & ACTIONS)
        authored["views"] = [view for view in VIEWS if view in views]
        authored["expressions"] = sorted({name for view in rig_views.values() if isinstance(view, dict)
                                          and isinstance(view.get("expressions"), dict)
                                          for name in view["expressions"] if isinstance(name, str)})
        manifest = compile_character_pack(root, id, variant)
        supported["views"] = list(manifest["views"])
        supported["expressions"] = sorted(set.intersection(*(set(view["rig"]["expressions"])
                                                           for view in manifest["views"].values())))
        for name, action in manifest["actions"].items():
            review = creative_review_state(root, "character", id, f"animation:{variant}:{name}")
            exports = {view: animation_export_valid(root, id, variant, name, view) for view in VIEWS}
            supported["actions"].append({"id": name, "duration": action["duration"], "loop": action["loop"],
                                         "requires_prop": action["requires_prop"], "review": review["state"],
                                         "exports": exports})
    except (OSError, ValueError, TypeError, ws.WorkspaceError) as exc:
        error = str(exc)
        supported = {"actions": [], "views": [], "expressions": []}
    native = {"available": False, "registered": (pack / "native").is_dir(),
              "candidate": False, "source_matches": False,
              "review": "draft", "bindings": [], "error": None}
    native_path = pack / "native/manifest.json"
    native["candidate"] = (pack / "native-candidate/manifest.json").is_file()
    if native_path.is_file():
        from studio.native_pipeline import source_tree_hash
        native["source_matches"] = not native["candidate"] or source_tree_hash(pack / "native") == source_tree_hash(pack / "native-candidate")
    if native["candidate"]:
        native["review"] = creative_review_state(root, "character", id, f"rig:{variant}")["state"]
    if native["registered"]:
        from studio.native_character import NativeCharacterError, validate_native_registration
        from studio.native_pipeline import render_status
        try:
            registration = validate_native_registration(native_path)
            native["review"] = creative_review_state(root, "character", id, f"rig:{variant}")["state"]
            native["available"] = True
            for perspective, actions in registration.get("controls", {}).get("bindings", {}).items():
                if not isinstance(actions, dict): continue
                for motion, expressions in actions.items():
                    if not isinstance(expressions, dict): continue
                    for expression in expressions:
                        if all(ws.ID.fullmatch(value) for value in (perspective, motion, expression)):
                            native["bindings"].append({"view": perspective, "action": motion,
                                "expression": expression, "render": render_status(root, id, variant, perspective, motion, expression)})
        except (NativeCharacterError, OSError, ValueError, TypeError, ws.WorkspaceError) as exc:
            native["error"] = str(exc)
        # A broken or changed source must not hide the last validated native clip.
        known = {(row["view"], row["action"], row["expression"]) for row in native["bindings"]}
        renders = pack / "native/renders"
        if renders.is_dir():
            for pointer in renders.glob("*/*/*/current.json"):
                values = pointer.relative_to(renders).parts[:3]
                if values in known or not all(ws.ID.fullmatch(value) for value in values):
                    continue
                try:
                    status = render_status(root, id, variant, *values)
                except (NativeCharacterError, OSError, ValueError, TypeError, ws.WorkspaceError):
                    continue
                if status["clip"]:
                    native["bindings"].append({"view": values[0], "action": values[1],
                                               "expression": values[2], "render": status})
    return {"character_id": id, "variant_id": variant, "renderer": "native" if native["registered"] else "canvas", "authored": authored,
            "supported": supported, "native": native, "error": error}


def _exchange_native_dirs(left, right):
    libc = ctypes.CDLL(None, use_errno=True)
    if not hasattr(libc, "renameat2") or libc.renameat2(-100, os.fsencode(left), -100, os.fsencode(right), 2):
        raise ws.WorkspaceError("io", "Atomic native source replacement is unavailable.")


def register_native_candidate(root, id, variant, expected_variant_revision, expected_source_sha256,
                              replace_revision=None, confirm_replace=False):
    """Install a complete calibration candidate as draft rig source, without approval."""
    from studio.creative import _validate_rig_evidence
    from studio.native_character import NativeCharacterError, validate_native_registration

    root = Path(root).resolve()
    pack = _folder(root, id) / "03_animation" / ws._id(variant)
    candidate = pack / "calibration/native"
    active = pack / "native-candidate"
    manifest_path = candidate / "manifest.json"
    if (not re.fullmatch(r"[0-9a-f]{64}", expected_source_sha256 or "") or
            not re.fullmatch(r"[0-9a-f]{64}", expected_variant_revision or "")):
        raise ws.WorkspaceError("invalid", "Expected candidate and variant hashes are required.")
    with ws.workspace_lock(root):
        if ws._file_hash(pack / "variant.json") != expected_variant_revision:
            raise ws.WorkspaceError("conflict", "Variant changed before native source registration.")
        if not manifest_path.is_file() or ws._file_hash(manifest_path) != expected_source_sha256:
            raise ws.WorkspaceError("conflict", "Native candidate manifest changed or is missing.")
        replacing = active.exists()
        if replacing and (confirm_replace is not True or
                          replace_revision != ws._file_hash(active / "manifest.json")):
            raise ws.WorkspaceError("conflict", "Current native candidate hash and explicit replacement are required.")
        if not replacing and (replace_revision is not None or confirm_replace):
            raise ws.WorkspaceError("invalid", "No native candidate exists to replace.")
        if any(path.is_symlink() for path in candidate.rglob("*")):
            raise ws.WorkspaceError("invalid", "Native candidate cannot contain links.")
        if (candidate / "renders").exists():
            raise ws.WorkspaceError("invalid", "Rendered outputs do not belong in native candidate source.")
        try:
            registration = validate_native_registration(manifest_path)
            _validate_rig_evidence(candidate, registration)
            _registered_variant(root, id, variant)
        except (NativeCharacterError, ValueError, OSError) as exc:
            raise ws.WorkspaceError("blocked", f"Native candidate is incomplete: {exc}") from exc
        staging = pack / (".native-staging-" + uuid.uuid4().hex)
        old_candidate = False
        try:
            shutil.copytree(candidate, staging)
            validate_native_registration(staging / "manifest.json")
            _validate_rig_evidence(staging, registration)
            if ws._file_hash(manifest_path) != expected_source_sha256:
                raise ws.WorkspaceError("conflict", "Native candidate changed during registration.")
            if replacing:
                _exchange_native_dirs(active, staging)
                old_candidate = True
                history = pack / "native-history" / (replace_revision + "-" + uuid.uuid4().hex[:8])
                history.parent.mkdir(parents=True, exist_ok=True)
                staging.rename(history)
            else:
                staging.rename(active)
        finally:
            if staging.exists() and not old_candidate: shutil.rmtree(staging)
    return {"state": "draft", "source_sha256": expected_source_sha256,
            "review": f"/creative/character/{id}/review/rig:{variant}"}


def activate_native_candidate(root, id, variant, expected_fingerprint):
    """Copy exactly the approved candidate into the production source shelf."""
    from studio.native_character import validate_native_registration
    from studio.native_pipeline import source_tree_hash

    root = Path(root).resolve()
    pack = _folder(root, id) / "03_animation" / ws._id(variant)
    candidate = pack / "native-candidate"
    active = pack / "native"
    with ws.workspace_lock(root):
        gate = creative_review_state(root, "character", id, f"rig:{variant}")
        if gate["state"] not in {"approved", "accepted"} or gate["fingerprint"] != expected_fingerprint:
            raise ws.WorkspaceError("blocked", "The current native candidate needs rig approval.")
        if active.exists():
            if (active / "manifest.json").is_file() and source_tree_hash(active) == source_tree_hash(candidate):
                validate_native_registration(active / "manifest.json")
                return {"state": "active", "review": gate["state"], "fingerprint": gate["fingerprint"]}
        staging = pack / (".native-staging-" + uuid.uuid4().hex)
        try:
            shutil.copytree(candidate, staging)
            validate_native_registration(staging / "manifest.json")
            if ws._file_hash(candidate / "manifest.json") != ws._file_hash(staging / "manifest.json"):
                raise ws.WorkspaceError("conflict", "Candidate changed during activation.")
            if creative_review_state(root, "character", id, f"rig:{variant}")["fingerprint"] != expected_fingerprint:
                raise ws.WorkspaceError("conflict", "Reviewed native candidate changed during activation.")
            if active.exists():
                prior_renders = active / "renders"
                if prior_renders.exists():
                    if any(path.is_symlink() for path in prior_renders.rglob("*")):
                        raise ws.WorkspaceError("invalid", "Previous native render cache contains links.")
                    shutil.copytree(prior_renders, staging / "renders", copy_function=os.link)
                # Linux directory exchange keeps the old source available until the new source is fully installed.
                _exchange_native_dirs(active, staging)
            else:
                staging.rename(active)
        finally:
            if staging.exists(): shutil.rmtree(staging)
    return {"state": "active", "review": "approved", "fingerprint": expected_fingerprint}


def _material(root, ident, title, path):
    return ws.create_material(root, {"id": ident, "title": title, "description": "OpenAI generated character reference artwork",
                                     "kind": "image", "source": path, "rights": "OpenAI generated", "tags": ["character"]}, _lock_held=True)


def _batch_art(root, record, output):
    if not isinstance(output, dict) or not isinstance(output.get("path"), str) or not isinstance(output.get("sha256"), str) or not output["path"].startswith(record["output_dir"] + "/"):
        raise ws.WorkspaceError("invalid", "Artwork does not belong to its generation batch.")
    return _art(root, output["path"], output["sha256"])


def _verified_batch(root, id, purpose, generation_id, revision, artworks):
    record = generation_detail(root, generation_id)
    try:
        if (record["subject_type"] != "character" or record["subject_id"] != id or record["purpose"] != purpose or
                record["state"] != "completed" or record["provider"] != "openai" or record["input_revision"] != revision or
                record["transport"] not in {"native", "codex-cli", "openai-api"} or
                record["output_dir"] != f"characters/{id}/generated/{generation_id}" or
                record["image_count"] != len(artworks) or
                not isinstance(record["outputs"], list) or len(record["outputs"]) != len(artworks)):
            raise ValueError
        for expected, output in zip(artworks, record["outputs"]):
            if expected != {"path": output["path"], "sha256": output["sha256"]}:
                raise ValueError
            _batch_art(root, record, output)
    except (KeyError, TypeError, ValueError):
        raise ws.WorkspaceError("invalid", "Character artwork does not match a completed OpenAI batch.") from None
    return record


def _reference_hashes(record):
    try:
        references = record["resolved_references"]
        if not isinstance(references, list): raise ValueError
        return [image["sha256"] for item in references for image in item["images"]]
    except (KeyError, TypeError, ValueError):
        raise ws.WorkspaceError("invalid", "Generation reference record is malformed.") from None


def _registered_candidates(root, id):
    folder = _folder(root, id)
    candidates = _json(folder / "01_design/candidates.json")
    batch = _verified_batch(root, id, "character-concepts", candidates[0]["generation_id"],
                            creative_review_state(root, "character", id, "brief")["fingerprint"],
                            [{"path": c["path"], "sha256": c["sha256"]} for c in candidates])
    for index, candidate in enumerate(candidates, 1):
        material = ws._material(root, candidate["material_id"])
        if (candidate["id"] != f"concept-{index}" or candidate["generation_id"] != batch["id"] or
                candidate["material_id"] != f"{id}-{batch['id']}-concept-{index}" or
                material["source"] != candidate["path"] or material["rights"] != "OpenAI generated"):
            raise ws.WorkspaceError("invalid", "Candidate provenance does not match its OpenAI batch.")
    return candidates


def _registered_reference(root, id):
    folder = _folder(root, id)
    reference = _json(folder / "02_identity/reference-set.json")
    candidates = _registered_candidates(root, id)
    selected = [c for c in candidates if c["selected"]]
    if len(selected) != 1 or reference["candidate_id"] != selected[0]["id"] or reference["candidate_path"] != selected[0]["path"] or reference["candidate_sha256"] != selected[0]["sha256"]:
        raise ws.WorkspaceError("invalid", "Identity does not bind the selected concept.")
    revision = creative_review_state(root, "character", id, "design")["fingerprint"]
    if reference["design_revision"] != revision:
        raise ws.WorkspaceError("conflict", "Identity design revision changed.")
    record = _verified_batch(root, id, "character-identity", reference["generation_id"], revision,
                             [{"path": reference[name], "sha256": reference[name + "_sha256"]} for name in ("sheet", "in_scene")])
    hashes = _reference_hashes(record)
    if reference["candidate_sha256"] not in hashes:
        raise ws.WorkspaceError("invalid", "Identity batch omitted the selected concept reference.")
    for name in ("sheet", "in_scene"):
        material_key = "in-scene" if name == "in_scene" else name
        material = ws._material(root, reference["material_ids"][material_key])
        if (reference["material_ids"][material_key] != f"{id}-{reference['generation_id']}-{material_key}" or
                material["source"] != reference[name] or material["rights"] != "OpenAI generated"):
            raise ws.WorkspaceError("invalid", "Identity material provenance is invalid.")
    return reference


def _registered_variant(root, id, variant):
    folder = _folder(root, id)
    data = _json(folder / "03_animation" / variant / "variant.json")
    reference = _registered_reference(root, id)
    if (data["id"] != variant or data["appearance"] != reference["appearance"] or
            data["reference_set_sha256"] != ws._file_hash(folder / "02_identity/reference-set.json") or
            data["reference_material_ids"] != reference["material_ids"]):
        raise ws.WorkspaceError("invalid", "Variant does not retain canonical identity.")
    record = _verified_batch(root, id, "character-variant", data["generation_id"], data["identity_revision"],
                             [{"path": data["artwork"]["path"], "sha256": data["artwork"]["sha256"]}])
    hashes = _reference_hashes(record)
    if (reference["sheet_sha256"] not in hashes or reference["in_scene_sha256"] not in hashes):
        raise ws.WorkspaceError("invalid", "Variant batch omitted canonical references.")
    ws._style(root, data["style_id"])
    context = record.get("context")
    if (not isinstance(context, dict) or context != {"variant_id": variant, "style_id": data["style_id"],
            "style_revision": ws._style_revision(root, data["style_id"]),
            "monochrome_exception": data["monochrome_exception"]}):
        raise ws.WorkspaceError("invalid", "Variant batch target or style revision changed.")
    return data


def snapshot_variant_for_style(root, id, variant, style_id):
    """A video may only freeze a registered variant of its selected visual style."""
    data = _registered_variant(root, id, variant)
    if data["style_id"] != style_id:
        raise ws.WorkspaceError("blocked", "Character variant belongs to a different style.")
    return data


def _replace_record(folder, path, revision, confirm):
    if not confirm or not isinstance(revision, str) or revision != ws._file_hash(path):
        raise ws.WorkspaceError("conflict", "Confirm replacement of the current saved registry revision.")
    archive = folder / "history" / path.stem / f"{revision}.json"
    if not archive.is_file():
        ws._atomic_write(archive, path.read_bytes())


def register_character_candidates(root, id, generation_id, expected_revision, *, replace_revision=None, confirm_replace=False):
    with ws.workspace_lock(root):
        folder = _folder(root, id)
        record = generation_detail(root, generation_id)
        state = creative_review_state(root, "character", id, "brief")
        if state["state"] not in {"approved", "accepted"} or not state["ready"] or state["fingerprint"] != expected_revision or record["input_revision"] != expected_revision:
            raise ws.WorkspaceError("conflict", "Approved character brief changed.")
        if record["subject_id"] != id or record["purpose"] != "character-concepts" or record["state"] != "completed" or len(record["outputs"]) != 3 or record["provider"] != "openai":
            raise ws.WorkspaceError("blocked", "A completed OpenAI three-concept batch is required.")
        path = folder / "01_design/candidates.json"
        if path.exists():
            previous = _json(path)
            old_batch = generation_detail(root, previous[0]["generation_id"])
            design = creative_review_state(root, "character", id, "design")
            if old_batch["input_revision"] == expected_revision and design["state"] not in {"stale", "changes-requested"}:
                raise ws.WorkspaceError("conflict", "Current candidates need a changes-requested decision before replacement.")
            if not confirm_replace or replace_revision != ws._file_hash(path):
                raise ws.WorkspaceError("conflict", "Confirm replacement of the current saved candidate revision.")
        candidates = []
        for index, output in enumerate(record["outputs"], 1):
            digest = _batch_art(root, record, output)
            candidates.append({"id": f"concept-{index}", "path": output["path"], "sha256": digest,
                               "generation_id": generation_id, "provider": "openai", "selected": False,
                               "material_id": f"{id}-{generation_id}-concept-{index}"})
        if len({c["sha256"] for c in candidates}) != 3:
            raise ws.WorkspaceError("invalid", "Three distinct concept artworks are required.")
        for candidate in candidates:
            _material(root, candidate["material_id"], f"{id} {candidate['id']}", candidate["path"])
        if path.exists(): _replace_record(folder, path, replace_revision, confirm_replace)
        ws._atomic_write(path, (json.dumps(candidates, indent=2) + "\n").encode())
    return character_detail(root, id)


def select_character_candidate(root, id, candidate_id, expected_revision):
    folder = _folder(root, id)
    with ws.workspace_lock(root):
        state = creative_review_state(root, "character", id, "design")
        if state["fingerprint"] != expected_revision:
            raise ws.WorkspaceError("conflict", "Character candidates changed since you opened them.")
        candidates = _registered_candidates(root, id)
        if not isinstance(candidates, list) or len(candidates) != 3 or sum(c.get("id") == candidate_id for c in candidates) != 1:
            raise ws.WorkspaceError("invalid", "Choose one of three saved concepts.")
        for candidate in candidates: _art(root, candidate["path"], candidate["sha256"])
        for candidate in candidates: candidate["selected"] = candidate["id"] == candidate_id
        ws._atomic_write(folder / "01_design/candidates.json", (json.dumps(candidates, indent=2) + "\n").encode())
    return character_detail(root, id)


def prepare_character_identity(root, id, *, transport="codex-cli", image_model=None, max_paid_spend=None):
    detail = character_detail(root, id)
    state = detail["reviews"]["design"]
    selected = [item for item in detail["candidates"] if item.get("selected") is True]
    if state["state"] not in {"approved", "accepted"} or len(selected) != 1:
        raise ws.WorkspaceError("blocked", "An approved selected concept is required.")
    concept = selected[0]
    _art(root, concept["path"], concept["sha256"])
    prompt = ("Refine the selected character concept into exactly two matching references: first a character sheet "
              "with front and three-quarter-right views, then an in-scene example. Preserve the same facial identity, "
              "hair, eyes, proportions and professional clothing. Do not mirror asymmetric features. "
              f"Character direction: {( _folder(root, id) / '01_design/brief.md').read_text(encoding='utf-8').strip()}")
    return prepare_generation(root, {"id": f"identity-{uuid.uuid4().hex[:12]}", "subject_type": "character", "subject_id": id,
        "purpose": "character-identity", "prompt": prompt, "references": [{"material_id": concept["material_id"], "role": "selected concept; preserve identity"}],
        "transparent": False, "image_count": 2, "input_revision": state["fingerprint"],
        "transport": transport, "image_model": image_model, "max_paid_spend": max_paid_spend})


def register_character_identity(root, id, generation_id, constraints, expected_revision, *, replace_revision=None, confirm_replace=False):
    if not isinstance(constraints, dict) or set(constraints) != _APPEARANCE or any(not isinstance(value, str) or not value.strip() for value in constraints.values()):
        raise ws.WorkspaceError("invalid", "Choose explicit hair, eyes, face, proportions and clothing constraints.")
    with ws.workspace_lock(root):
        folder = _folder(root, id)
        state = creative_review_state(root, "character", id, "design")
        record = generation_detail(root, generation_id)
        candidates = _registered_candidates(root, id)
        selected = [item for item in candidates if item["selected"]]
        if state["state"] not in {"approved", "accepted"} or not state["ready"] or state["fingerprint"] != expected_revision or record["input_revision"] != expected_revision:
            raise ws.WorkspaceError("conflict", "Approved design changed.")
        if len(selected) != 1 or record["subject_id"] != id or record["purpose"] != "character-identity" or record["state"] != "completed" or record["provider"] != "openai" or len(record["outputs"]) != 2:
            raise ws.WorkspaceError("blocked", "A completed OpenAI identity batch is required.")
        path = folder / "02_identity/reference-set.json"
        if path.exists():
            identity_state = creative_review_state(root, "character", id, "identity")["state"]
            if identity_state not in {"stale", "changes-requested"}:
                raise ws.WorkspaceError("conflict", "Identity revision needs a changes-requested decision.")
            current_revision = ws._file_hash(path)
            if ((identity_state == "stale" and not confirm_replace) or
                    (replace_revision is not None and replace_revision != current_revision) or
                    (confirm_replace and replace_revision != current_revision)):
                raise ws.WorkspaceError("conflict", "Confirm replacement of the current saved identity revision.")
            replace_revision = current_revision
            confirm_replace = True
        concept = selected[0]
        outputs = record["outputs"]
        for output in outputs: _batch_art(root, record, output)
        if concept["sha256"] not in _reference_hashes(record):
            raise ws.WorkspaceError("blocked", "Identity batch omitted the selected concept reference.")
        material_ids = {name: f"{id}-{generation_id}-{name}" for name in ("sheet", "in-scene")}
        for name, output in zip(material_ids, outputs):
            _material(root, material_ids[name], f"{id} {name}", output["path"])
        reference_set = {"candidate_id": concept["id"], "candidate_path": concept["path"], "candidate_sha256": concept["sha256"],
                         "appearance": constraints, "views": _VIEWS, "sheet": outputs[0]["path"], "sheet_sha256": outputs[0]["sha256"],
                         "in_scene": outputs[1]["path"], "in_scene_sha256": outputs[1]["sha256"], "material_ids": material_ids,
                         "generation_id": generation_id, "design_revision": expected_revision}
        if path.exists(): _replace_record(folder, path, replace_revision, confirm_replace)
        ws._atomic_write(path, (json.dumps(reference_set, indent=2) + "\n").encode())
    return character_detail(root, id)


def register_character_variant(root, id, variant, manifest, expected_revision, *, replace_revision=None, confirm_replace=False):
    ws._id(variant)
    with ws.workspace_lock(root):
        folder = _folder(root, id)
        state = creative_review_state(root, "character", id, "identity")
        reference = _registered_reference(root, id)
        if state["state"] not in {"approved", "accepted"} or not state["ready"] or state["fingerprint"] != expected_revision:
            raise ws.WorkspaceError("conflict", "Approved canonical identity changed.")
        if not isinstance(manifest, dict) or set(manifest) != {"style_id", "views", "appearance", "monochrome_exception", "generation_id"} or not isinstance(manifest["style_id"], str) or not ws.ID.fullmatch(manifest["style_id"]) or manifest["views"] != _VIEWS or manifest["appearance"] != reference["appearance"] or not isinstance(manifest["monochrome_exception"], bool):
            raise ws.WorkspaceError("invalid", "Variant must retain exact master identity and both approved views.")
        generation = generation_detail(root, manifest["generation_id"])
        if generation["subject_id"] != id or generation["purpose"] != "character-variant" or generation["state"] != "completed" or generation["provider"] != "openai" or generation["input_revision"] != expected_revision or len(generation["outputs"]) != 1:
            raise ws.WorkspaceError("blocked", "A completed OpenAI variant artwork batch is required.")
        ws._style(root, manifest["style_id"])
        if generation.get("context") != {"variant_id": variant, "style_id": manifest["style_id"],
                "style_revision": ws._style_revision(root, manifest["style_id"]),
                "monochrome_exception": manifest["monochrome_exception"]}:
            raise ws.WorkspaceError("conflict", "Variant batch target or style inputs changed.")
        output = generation["outputs"][0]
        _batch_art(root, generation, output)
        hashes = _reference_hashes(generation)
        if reference["sheet_sha256"] not in hashes or reference["in_scene_sha256"] not in hashes:
            raise ws.WorkspaceError("blocked", "Variant batch omitted canonical references.")
        path = folder / "03_animation" / variant / "variant.json"
        if path.exists():
            if not confirm_replace or replace_revision != ws._file_hash(path):
                raise ws.WorkspaceError("conflict", "Confirm replacement of the current saved variant revision.")
        result = {**manifest, "id": variant, "identity_revision": expected_revision,
                  "reference_set_sha256": ws._file_hash(folder / "02_identity/reference-set.json"),
                  "reference_material_ids": reference["material_ids"],
                  "artwork": {"path": output["path"], "sha256": output["sha256"], "views": _VIEWS}}
        if path.exists(): _replace_record(folder, path, replace_revision, confirm_replace)
        ws._atomic_write(path, (json.dumps(result, indent=2) + "\n").encode())
    return result


def prepare_character_variant(root, id, variant, style_id, prompt, monochrome_exception=False, *, transport="codex-cli", image_model=None, max_paid_spend=None):
    folder = _folder(root, id)
    ws._id(variant)
    ws._id(style_id)
    state = creative_review_state(root, "character", id, "identity")
    if state["state"] not in {"approved", "accepted"}:
        raise ws.WorkspaceError("blocked", "Current canonical identity approval is required.")
    reference = _json(folder / "02_identity/reference-set.json")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ws.WorkspaceError("invalid", "Describe the requested style variant artwork.")
    if not isinstance(monochrome_exception, bool):
        raise ws.WorkspaceError("invalid", "Monochrome exception must be explicit.")
    ws._style(root, style_id)
    context = {"variant_id": variant, "style_id": style_id, "style_revision": ws._style_revision(root, style_id),
               "monochrome_exception": monochrome_exception}
    return prepare_generation(root, {"id": f"variant-{uuid.uuid4().hex[:12]}", "subject_type": "character", "subject_id": id,
        "purpose": "character-variant", "context": context, "prompt": (f"{prompt.strip()} Preserve exact master appearance: " +
            json.dumps(reference["appearance"], ensure_ascii=False) + ". Use front and three-quarter-right views; "
            "do not mirror asymmetric features. Monochrome exception requested: " + str(monochrome_exception).lower() +
            ". Any monochrome treatment needs separate review."),
        "references": [{"material_id": reference["material_ids"]["sheet"], "role": "canonical character sheet"},
                       {"material_id": reference["material_ids"]["in-scene"], "role": "canonical in-scene identity"}],
        "transparent": True, "image_count": 1, "input_revision": state["fingerprint"],
        "transport": transport, "image_model": image_model, "max_paid_spend": max_paid_spend})
