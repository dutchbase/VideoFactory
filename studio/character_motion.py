"""Validated authored character packs and contained-browser frame export."""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import tempfile
from fractions import Fraction
from pathlib import Path

from PIL import Image

from studio import workspace as ws
from studio.characters import _registered_variant, _registered_reference, _verified_batch, _reference_hashes
from studio.creative import creative_fingerprint, creative_review_state
from studio.generation import generation_detail, prepare_generation

VIEWS = ("front", "three-quarter-right")
ACTIONS = {"idle", "blink", "talk", "point", "present", "wave", "sit", "stand", "computer",
           "happy", "puzzled", "surprised", "disappointed", "hold-prop", "present-prop"}
EXPRESSIONS = {"neutral", "blink", "happy", "puzzled", "surprised", "disappointed"}
ENGINE = Path(__file__).resolve().parents[1] / "_runtime/character.js"
RENDERER_REVISION = 2
_FRAME_EXPORT_REVISION = "canvas-origin-v2"
_UNSET = object()
_MOTION_HINTS = {
    "idle": {"body": [(0.5, 0, 0, 0)]},
    "blink": {"head": [(0.5, 0, -1, 0)]},
    "talk": {"head": [(0.5, 0, -1, 0.03)]},
    "point": {"arm-right": [(0.5, 3, -2, -0.5)]},
    "present": {"arm-right": [(0.5, 4, -1, -0.35)], "arm-left": [(0.5, -2, -1, 0.2)]},
    "wave": {"arm-right": [(0.25, 1, -3, -0.4), (0.5, 1, -3, 0.3), (0.75, 1, -3, -0.4)]},
    "sit": {"body": [(0.5, 0, 5, 0)], "head": [(0.5, 0, 5, 0)],
            "arm-left": [(0.5, 0, 5, 0)], "arm-right": [(0.5, 0, 5, 0)]},
    "stand": {"body": [(0.5, 0, 0, 0)], "head": [(0.5, 0, 0, 0)],
              "arm-left": [(0.5, 0, 0, 0)], "arm-right": [(0.5, 0, 0, 0)]},
    "computer": {"arm-left": [(0.25, -1, 1, 0), (0.5, 0, 0, 0), (0.75, -1, 1, 0)],
                 "arm-right": [(0.25, 0, 0, 0), (0.5, 1, 1, 0), (0.75, 0, 0, 0)]},
    "happy": {"head": [(0.5, 0, -2, -0.05)]},
    "puzzled": {"head": [(0.5, 0, 0, 0.12)]},
    "surprised": {"head": [(0.5, 0, -3, 0)]},
    "disappointed": {"head": [(0.5, 0, 2, -0.08)]},
    "hold-prop": {"arm-right": [(0.5, 1, -1, -0.1)]},
    "present-prop": {"arm-right": [(0.5, 4, -2, -0.4)]},
}


def motion_template(action):
    """Editable motion starting point; cropped art and a review are still required."""
    if action not in ACTIONS: raise ws.WorkspaceError("invalid", "Unknown controlled character action.")
    duration = 4 if action == "idle" else 2
    loop = action not in {"sit", "stand"}
    tracks = {}
    for part, middle in _MOTION_HINTS[action].items():
        start = (0, 0, 5, 0) if action == "stand" else (0, 0, 0, 0)
        end = (duration, 0, 5, 0) if action == "sit" else (duration, 0, 0, 0)
        keys = [start, *((duration * t, x, y, rotation) for t, x, y, rotation in middle), end]
        tracks[part] = [dict(zip(("t", "x", "y", "rotation"), key)) for key in keys]
    return {"duration": duration, "expression": action if action in EXPRESSIONS - {"blink"} else "neutral",
            "requires_prop": action in {"hold-prop", "present-prop"}, "loop": loop, "tracks": tracks}


def _pack(root, id, variant):
    return ws.safe_path(root, f"characters/{ws._id(id)}/03_animation/{ws._id(variant)}")


def _read(path):
    try:
        if path.stat().st_size > ws.TEXT_LIMIT: raise ValueError
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        raise ws.WorkspaceError("invalid", f"Unreadable animation source: {path.name}.") from None


def _pair(value, *, integer=False):
    return (isinstance(value, list) and len(value) == 2 and
            all(type(x) in ((int,) if integer else (int, float)) and
                (type(x) is int or math.isfinite(x)) for x in value))


def _source_revision(root, id, variant, action):
    """Only this action's motion and shared art/rig/engine affect its export."""
    pack = _pack(root, id, variant)
    digest = hashlib.sha256()
    for path in (pack / "variant.json", pack / "assets.json", pack / "rig.json", ENGINE,
                 Path(root) / f"characters/{id}/02_identity/reference-set.json"):
        digest.update(ws._file_hash(path).encode() if path.is_file() else b"missing")
    try: motions = _read(pack / "motions.json")
    except ws.WorkspaceError: motions = {}
    all_actions = motions.get("actions", {}) if isinstance(motions, dict) else {}
    selected = all_actions.get(action) if isinstance(all_actions, dict) else None
    digest.update(json.dumps(selected, sort_keys=True).encode())
    try: assets = _read(pack / "assets.json")
    except ws.WorkspaceError: assets = {}
    asset_views = assets.get("views", {}) if isinstance(assets, dict) else {}
    for perspective in asset_views.values() if isinstance(asset_views, dict) else []:
        if not isinstance(perspective, dict): continue
        for part in perspective.values():
            if isinstance(part, dict) and isinstance(part.get("path"), str):
                try: digest.update(ws._file_hash(ws.safe_path(root, part["path"])).encode())
                except ws.WorkspaceError: digest.update(b"unsafe")
    return digest.hexdigest()


def _export_revision(manifest, prop):
    return hashlib.sha256((manifest["source_revision"] + "\0" + (prop or "") +
                           "\0" + _FRAME_EXPORT_REVISION).encode()).hexdigest()


def _allowed_art(root, id, variant, variant_data):
    allowed = {variant_data["artwork"]["path"]: variant_data["artwork"]["sha256"]}
    reference = _registered_reference(root, id)
    directory = Path(root) / ".studio/generations"
    if not directory.is_dir(): return allowed
    for path in directory.glob("*.json"):
        try:
            record = generation_detail(root, path.stem)
            context = {key: variant_data[key] for key in ("style_id", "monochrome_exception")}
            context.update(variant_id=variant, style_revision=ws._style_revision(root, variant_data["style_id"]))
            if (record.get("purpose") != "character-animation" or record.get("subject_id") != id or
                    record.get("context") != context or record.get("input_revision") != variant_data["identity_revision"] or
                    record.get("state") != "completed"):
                continue
            outputs = record.get("outputs", [])
            _verified_batch(root, id, "character-animation", record["id"], variant_data["identity_revision"],
                            [{"path": o["path"], "sha256": o["sha256"]} for o in outputs])
            hashes = _reference_hashes(record)
            if not all(value in hashes for value in (reference["sheet_sha256"], reference["in_scene_sha256"],
                                                      variant_data["artwork"]["sha256"])):
                raise ws.WorkspaceError("invalid", "Animation batch omitted canonical or variant references.")
            allowed.update({o["path"]: o["sha256"] for o in outputs})
        except (KeyError, TypeError, ValueError):
            raise ws.WorkspaceError("invalid", "Animation artwork batch is malformed.") from None
    return allowed


def compile_character_pack(root, id, variant, *, action=None, view=None):
    root = Path(root).resolve()
    pack = _pack(root, id, variant)
    variant_data = _registered_variant(root, id, variant)
    assets, rig, motions = (_read(pack / f"{name}.json") for name in ("assets", "rig", "motions"))
    if (not isinstance(assets, dict) or set(assets) != {"schema", "canvas", "views"} or assets["schema"] != 1 or
            not _pair(assets["canvas"], integer=True) or any(not 1 <= n <= 2048 for n in assets["canvas"]) or
            not isinstance(assets["views"], dict) or set(assets["views"]) != set(VIEWS) or
            not isinstance(rig, dict) or set(rig) != {"schema", "views"} or rig["schema"] != 1 or
            not isinstance(rig["views"], dict) or set(rig["views"]) != set(VIEWS) or
            not isinstance(motions, dict) or set(motions) != {"schema", "actions"} or motions["schema"] != 1 or
            not isinstance(motions["actions"], dict) or not motions["actions"] or
            set(motions["actions"]) - ACTIONS):
        raise ws.WorkspaceError("invalid", "Character pack schema or views are invalid.")
    if view is not None and view not in VIEWS: raise ws.WorkspaceError("unavailable", "Character view is unavailable.")
    if action is not None and action not in motions["actions"]: raise ws.WorkspaceError("unavailable", "Character action is unavailable.")
    allowed = _allowed_art(root, id, variant, variant_data)
    dimensions = {}
    views = {}
    required_part_fields = {"path", "sha256", "crop", "at", "anchor", "layer"}
    optional_part_fields = {"size", "material_id", "clip"}
    for name in VIEWS:
        parts, mapping = assets["views"][name], rig["views"][name]
        if not isinstance(parts, dict) or len(parts) > 64 or not isinstance(mapping, dict) or set(mapping) != {"draw_order", "expressions", "mouths", "props"}:
            raise ws.WorkspaceError("invalid", "Character parts or rig are invalid.")
        if (any(not isinstance(mapping[group], dict) for group in ("expressions", "mouths", "props")) or
                not isinstance(mapping["draw_order"], list) or
                not all(isinstance(k, str) for k in mapping["draw_order"]) or
                set(mapping["draw_order"]) != set(parts) or
                len(mapping["draw_order"]) != len(parts) or not all(isinstance(k, str) for k in parts) or
                any(not isinstance(parts[k], dict) or
                    not required_part_fields <= set(parts[k]) or
                    set(parts[k]) - required_part_fields - optional_part_fields for k in parts)):
            raise ws.WorkspaceError("invalid", "Character draw order must name each part once.")
        for key, part in parts.items():
            path, sha = part["path"], part["sha256"]
            if "material_id" in part:
                if key not in mapping["props"].values():
                    raise ws.WorkspaceError("invalid", "Only props may use supplied material art.")
                material = ws._material(root, ws._id(part["material_id"]))
                if (path not in material["files"] + [material["source"]] or material["kind"] != "image" or
                        not material["description"].strip() or material["rights"].strip().lower() in {"", "unknown"}):
                    raise ws.WorkspaceError("invalid", "Prop material must describe its source and rights.")
            elif not isinstance(path, str) or allowed.get(path) != sha or not isinstance(sha, str):
                raise ws.WorkspaceError("invalid", "Character part is not registered artwork.")
            file = ws.safe_path(root, path)
            if ws._file_hash(file) != sha: raise ws.WorkspaceError("conflict", "Character part artwork changed.")
            if path not in dimensions:
                try:
                    with Image.open(file) as image:
                        image.verify()
                    with Image.open(file) as image:
                        dimensions[path] = image.size
                except (OSError, ValueError):
                    raise ws.WorkspaceError("invalid", "Character part artwork is unreadable.") from None
            crop = part["crop"]
            if "clip" in part:
                clip = part["clip"]
                if (not isinstance(clip, list) or not 3 <= len(clip) <= 128 or
                        any(not _pair(point) or any(not 0 <= n <= 1 for n in point) for point in clip)):
                    raise ws.WorkspaceError("invalid", "Character clip polygon is invalid.")
                area = sum((Fraction(point[0]) * Fraction(next_point[1]) -
                            Fraction(next_point[0]) * Fraction(point[1]))
                           for point, next_point in zip(clip, clip[1:] + clip[:1]))
                if not area:
                    raise ws.WorkspaceError("invalid", "Character clip polygon must have nonzero signed area.")
            if (not isinstance(crop, list) or len(crop) != 4 or any(type(n) is not int for n in crop) or
                    min(crop[2:]) <= 0 or min(crop[:2]) < 0 or
                    crop[0] + crop[2] > dimensions[path][0] or crop[1] + crop[3] > dimensions[path][1] or
                    not _pair(part["at"]) or not _pair(part["anchor"]) or
                    ("size" in part and (not _pair(part["size"]) or any(not 0 < n <= 2048 for n in part["size"]))) or
                    any(abs(n) > 2048 for n in part["at"] + part["anchor"]) or
                    type(part["layer"]) is not int or abs(part["layer"]) > 100):
                raise ws.WorkspaceError("invalid", "Character crop, anchor or layer is invalid.")
        if mapping["draw_order"] != sorted(parts, key=lambda k: parts[k]["layer"]):
            raise ws.WorkspaceError("invalid", "Character draw order must follow explicit layers.")
        roles = []
        required_expressions = {"neutral"} | ({"blink"} if "blink" in motions["actions"] else set())
        required_expressions |= {pose["expression"] for pose in motions["actions"].values() if isinstance(pose, dict) and isinstance(pose.get("expression"), str)}
        for group, required in (("expressions", required_expressions),
                                ("mouths", {"closed", "half", "open"} if "talk" in motions["actions"] else {"closed"}),
                                ("props", set())):
            values = mapping[group]
            if not required <= set(values):
                raise ws.WorkspaceError("invalid", "Character expression, mouth or prop rig is incomplete.")
            for value in values.values():
                if group == "expressions":
                    group_parts = value if isinstance(value, list) else [value] if isinstance(value, str) else []
                    if (not 1 <= len(group_parts) <= 8 or
                            any(not isinstance(part, str) or part not in parts for part in group_parts) or
                            len(set(group_parts)) != len(group_parts)):
                        raise ws.WorkspaceError("invalid", "Character expression, mouth or prop rig is incomplete.")
                    roles.extend(group_parts)
                else:
                    if not isinstance(value, str) or value not in parts:
                        raise ws.WorkspaceError("invalid", "Character expression, mouth or prop rig is incomplete.")
                    roles.append(value)
        core = {"body", "head", "hair", "arm-left", "arm-right"}
        if len(set(roles)) != len(roles) or core & set(roles):
            raise ws.WorkspaceError("invalid", "Character visual roles must be distinct from core parts and each other.")
        if not core <= set(parts):
            raise ws.WorkspaceError("invalid", "Character lacks independently placed core parts.")
        views[name] = {"parts": parts, "rig": mapping}
    for key in ("body", "head", "hair"):
        front, angled = (views[name]["parts"][key] for name in VIEWS)
        if front["path"] == angled["path"] and front["crop"] == angled["crop"]:
            raise ws.WorkspaceError("invalid", "Front and three-quarter core artwork must use distinct real crops.")
    actions = {}
    for name, pose in motions["actions"].items():
        duration = 4 if name == "idle" else 2
        if (not isinstance(pose, dict) or set(pose) != {"duration", "expression", "requires_prop", "loop", "tracks"} or
                pose["duration"] != duration or not isinstance(pose["expression"], str) or pose["expression"] not in EXPRESSIONS or
                type(pose["requires_prop"]) is not bool or pose["requires_prop"] != (name in {"hold-prop", "present-prop"}) or
                type(pose["loop"]) is not bool or (name in {"idle", "blink", "talk", "computer"} and not pose["loop"]) or
                (name in {"sit", "stand"} and pose["loop"]) or
                not isinstance(pose["tracks"], dict) or not pose["tracks"] or
                any(part not in views["front"]["parts"] or part not in views[VIEWS[1]]["parts"] for part in pose["tracks"])):
            raise ws.WorkspaceError("invalid", "Character action has invalid duration, expression or tracks.")
        for frames in pose["tracks"].values():
            if (not isinstance(frames, list) or not 2 <= len(frames) <= 32 or
                    any(not isinstance(f, dict) or set(f) != {"t", "x", "y", "rotation"} or
                        any(type(v) not in (int, float) or not math.isfinite(v) or abs(v) > 2048 for v in f.values()) for f in frames) or
                    frames[0]["t"] != 0 or frames[-1]["t"] != duration or
                    any(a["t"] >= b["t"] for a, b in zip(frames, frames[1:])) or
                    (pose["loop"] and any(frames[0][k] != frames[-1][k] for k in ("x", "y", "rotation")))):
                raise ws.WorkspaceError("invalid", "Character motion keys must form a bounded track, seamless when looping.")
        actions[name] = pose
    return {"schema": 1, "renderer_revision": RENDERER_REVISION, "engine_sha256": ws._file_hash(ENGINE),
            "canvas": assets["canvas"], "views": views,
            "actions": {action: actions[action]} if action else actions,
            "source_revision": _source_revision(root, id, variant, action) if action else None}


def prepare_animation(root, id, variant, action, *, transport="codex-cli", image_model=None, max_paid_spend=None):
    from studio.characters import _material
    import uuid
    if action not in ACTIONS: raise ws.WorkspaceError("invalid", "Unknown controlled character action.")
    data = _registered_variant(root, id, variant)
    state = creative_review_state(root, "character", id, "identity")
    if state["state"] not in {"approved", "accepted"} or data["identity_revision"] != state["fingerprint"]:
        raise ws.WorkspaceError("blocked", "Current character identity approval is required.")
    reference = _registered_reference(root, id)
    material_id = f"{id}-{data['generation_id']}-variant"
    try: material = ws._material(root, material_id)
    except ws.WorkspaceError as error:
        if error.code != "missing": raise
        material = _material(root, material_id, f"{id} {variant} two-view sheet", data["artwork"]["path"])
    if material["source"] != data["artwork"]["path"]:
        raise ws.WorkspaceError("invalid", "Variant reference material changed.")
    context = {"variant_id": variant, "style_id": data["style_id"],
               "style_revision": ws._style_revision(root, data["style_id"]),
               "monochrome_exception": data["monochrome_exception"]}
    batch = prepare_generation(root, {"id": f"animation-{uuid.uuid4().hex[:12]}", "subject_type": "character",
        "subject_id": id, "purpose": "character-animation", "context": context,
        "prompt": (f"Prepare transparent reusable part artwork for controlled {action} animation of this exact character. "
                   "Supply separately placeable head, hair, torso, arms, expressions and closed/half/open mouths "
                   "for front and three-quarter-right, preserving both asymmetries. No rendered motion frames. "
                   f"Master appearance: {json.dumps(reference['appearance'], ensure_ascii=False)}"),
        "references": [{"material_id": reference["material_ids"]["sheet"], "role": "canonical identity sheet"},
                       {"material_id": reference["material_ids"]["in-scene"], "role": "canonical in-scene identity"},
                       {"material_id": material_id, "role": "approved style variant two-view sheet"}],
        "transparent": True, "image_count": 1, "input_revision": state["fingerprint"],
        "transport": transport, "image_model": image_model, "max_paid_spend": max_paid_spend})
    return {**batch, "motion_template": motion_template(action)}


def _render_frames(root, manifest, action, view, fps, output, prop):
    from playwright.sync_api import sync_playwright
    from studio import jobs
    from studio.server import make_server
    import threading
    server = make_server(root, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    box = None
    try:
        box, endpoint = jobs._contained_browser()
        with sync_playwright() as playwright:
            browser = playwright.chromium.connect_over_cdp(endpoint)
            page = browser.new_page(viewport={"width": manifest["canvas"][0], "height": manifest["canvas"][1]})
            page.goto(f"http://127.0.0.1:{server.server_port}/api/bootstrap")
            page.set_content(f'<html><head><style>html,body{{margin:0;padding:0}}canvas{{display:block}}</style></head>'
                             f'<body><canvas width="{manifest["canvas"][0]}" '
                             f'height="{manifest["canvas"][1]}"></canvas></body></html>')
            page.add_script_tag(content=ENGINE.read_text(encoding="utf-8"))
            page.evaluate("async m => { window.testCharacter = await Character.load(m); }", manifest)
            verifies_bytes = page.evaluate("async m => { const bad = structuredClone(m); "
                "Object.values(bad.views)[0].parts.body.sha256 = '0'.repeat(64); "
                "try { await Character.load(bad); return false; } catch { return true; } }", manifest)
            if not verifies_bytes: raise ws.WorkspaceError("invalid", "Character loader did not verify artwork bytes.")
            verifies_renderer = page.evaluate("async m => { const bad = structuredClone(m); bad.renderer_revision--; "
                "try { await Character.load(bad); return false; } catch { return true; } }", manifest)
            if not verifies_renderer: raise ws.WorkspaceError("invalid", "Character loader did not verify renderer revision.")
            count = int(manifest["actions"][action]["duration"] * fps)
            for index in range(count):
                result = page.evaluate("({time, action, view, prop}) => { const canvas = document.querySelector('canvas'); "
                    "const ctx = canvas.getContext('2d'); ctx.clearRect(0,0,canvas.width,canvas.height); "
                    "return window.testCharacter.draw(ctx,time,{action,view,speechLevel:0,prop}); }",
                    {"time": index / fps, "action": action, "view": view, "prop": prop})
                if not result["available"]: raise ws.WorkspaceError("unavailable", f"Character frame unavailable: {result['reason']}.")
                (output / f"{index:04d}.png").write_bytes(page.locator("canvas").screenshot(omit_background=True))
            result = page.evaluate("({time, action, view, prop}) => { const canvas = document.querySelector('canvas'); "
                "const ctx = canvas.getContext('2d'); ctx.clearRect(0,0,canvas.width,canvas.height); "
                "return window.testCharacter.draw(ctx,time,{action,view,speechLevel:0,prop}); }",
                {"time": manifest["actions"][action]["duration"], "action": action, "view": view, "prop": prop})
            if not result["available"]: raise ws.WorkspaceError("invalid", "Character end pose is unavailable.")
            end = page.locator("canvas").screenshot(omit_background=True)
            if manifest["actions"][action]["loop"] and end != (output / "0000.png").read_bytes():
                raise ws.WorkspaceError("invalid", "Character loop is not deterministic.")
            if not manifest["actions"][action]["loop"]:
                page.evaluate("({time,action,view,prop}) => { const canvas = document.querySelector('canvas'); "
                    "const ctx = canvas.getContext('2d'); ctx.clearRect(0,0,canvas.width,canvas.height); "
                    "return window.testCharacter.draw(ctx,time,{action,view,speechLevel:0,prop}); }",
                    {"time": manifest["actions"][action]["duration"] + 1, "action": action, "view": view, "prop": prop})
                if page.locator("canvas").screenshot(omit_background=True) != end:
                    raise ws.WorkspaceError("invalid", "Character transition does not hold its end pose.")
            if page.evaluate("() => window.testCharacter.draw(document.querySelector('canvas').getContext('2d'),0,{action:'constructor',view:'front'}).available"):
                raise ws.WorkspaceError("invalid", "Missing action must be unavailable.")
            if page.evaluate("({action}) => window.testCharacter.draw(document.querySelector('canvas').getContext('2d'),0,{action,view:'constructor'}).available", {"action": action}):
                raise ws.WorkspaceError("invalid", "Missing view must be unavailable.")
            mouths = page.evaluate("({action,view,prop}) => [0,0.4,0.8].map(speechLevel => "
                "window.testCharacter.draw(document.querySelector('canvas').getContext('2d'),0,{action,view,speechLevel,prop}).mouth)",
                {"action": action, "view": view, "prop": prop})
            available_mouths = manifest["views"][view]["rig"]["mouths"]
            if mouths != [state if state in available_mouths else "closed" for state in ("closed", "half", "open")]:
                raise ws.WorkspaceError("invalid", "Character mouth levels disagree with the authored rig.")
            browser.close()
    finally:
        if box: jobs._stop_box(box)
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


def animation_export_valid(root, id, variant, action, view, *, fps=None, prop=_UNSET, manifest=None):
    try:
        manifest = manifest or compile_character_pack(root, id, variant, action=action, view=view)
        folder = _pack(root, id, variant) / "frames" / action / view
        index = _read(folder / "index.json")
        if not isinstance(index, dict): return False
        expected = int(manifest["actions"][action]["duration"] * index["fps"])
        if (set(index) != {"schema", "character_id", "variant_id", "action", "view", "fps", "duration", "canvas", "source_revision", "prop", "frames"} or
                index["schema"] != 1 or index["character_id"] != id or index["variant_id"] != variant or
                index["action"] != action or index["view"] != view or type(index["fps"]) is not int or
                not 1 <= index["fps"] <= 60 or (fps is not None and index["fps"] != fps) or expected > 240 or
                index["duration"] != manifest["actions"][action]["duration"] or
                index["canvas"] != manifest["canvas"] or
                (prop is not _UNSET and index["prop"] != prop) or
                (index["prop"] is not None and (not isinstance(index["prop"], str) or
                    any(index["prop"] not in perspective["rig"]["props"] for perspective in manifest["views"].values()))) or
                (manifest["actions"][action]["requires_prop"] and index["prop"] is None) or
                index["source_revision"] != _export_revision(manifest, index["prop"]) or
                not isinstance(index["frames"], list) or len(index["frames"]) != expected):
            return False
        for number, frame in enumerate(index["frames"]):
            name = f"{number:04d}.png"
            if not isinstance(frame, dict) or frame.get("path") != name or ws._file_hash(folder / name) != frame.get("sha256"):
                return False
        preview = _pack(root, id, variant) / "preview" / action / f"{view}.png"
        return preview.is_file() and ws._file_hash(preview) == index["frames"][0]["sha256"]
    except (OSError, ValueError, TypeError, KeyError, ws.WorkspaceError):
        return False


def export_character_frames(root, id, variant, action, view, fps=30, *, prop=None):
    root = Path(root).resolve()
    if type(fps) is not int or not 1 <= fps <= 60:
        raise ws.WorkspaceError("invalid", "Frame rate must be 1–60 fps.")
    if action not in ACTIONS or view not in VIEWS:
        raise ws.WorkspaceError("unavailable", "Character action or view is unavailable.")
    state = creative_review_state(root, "character", id, "identity")
    if state["state"] not in {"approved", "accepted"}: raise ws.WorkspaceError("blocked", "Current identity approval is required.")
    manifest = compile_character_pack(root, id, variant, action=action, view=view)
    if (manifest["actions"][action]["requires_prop"] and prop is None) or (prop is not None and
            (not isinstance(prop, str) or any(prop not in perspective["rig"]["props"] for perspective in manifest["views"].values()))):
        raise ws.WorkspaceError("unavailable", "Selected character prop is unavailable.")
    source_revision = _export_revision(manifest, prop)
    count = int(manifest["actions"][action]["duration"] * fps)
    if count > 240: raise ws.WorkspaceError("invalid", "Character export exceeds 240 frames.")
    if animation_export_valid(root, id, variant, action, view, fps=fps, prop=prop, manifest=manifest):
        return _read(_pack(root, id, variant) / "frames" / action / view / "index.json")
    parent = _pack(root, id, variant) / "frames" / action
    parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".export-", dir=parent))
    target = parent / view
    backup = parent / (".previous-" + view)
    preview = _pack(root, id, variant) / "preview" / action / f"{view}.png"
    preview_backup = preview.with_suffix(".old")
    try:
        _render_frames(root, manifest, action, view, fps, temporary, prop)
        frames = []
        for index in range(count):
            path = temporary / f"{index:04d}.png"
            with Image.open(path) as image:
                if image.size != tuple(manifest["canvas"]) or image.mode != "RGBA":
                    raise ws.WorkspaceError("invalid", "Rendered frame has wrong bounds or alpha.")
                image.verify()
            frames.append({"path": path.name, "sha256": ws._file_hash(path)})
        index = {"schema": 1, "character_id": id, "variant_id": variant, "action": action, "view": view,
                 "fps": fps, "duration": manifest["actions"][action]["duration"], "canvas": manifest["canvas"],
                 "source_revision": source_revision, "prop": prop, "frames": frames}
        ws._atomic_write(temporary / "index.json", (json.dumps(index, indent=2) + "\n").encode())
        with ws.workspace_lock(root):
            if _export_revision(compile_character_pack(root, id, variant, action=action, view=view), prop) != source_revision:
                raise ws.WorkspaceError("conflict", "Character pack changed during export.")
            if backup.exists(): shutil.rmtree(backup)
            preview.parent.mkdir(parents=True, exist_ok=True)
            if preview_backup.exists(): preview_backup.unlink()
            moved_target = moved_preview = new_target = False
            try:
                if target.exists(): os.replace(target, backup); moved_target = True
                if preview.exists(): os.replace(preview, preview_backup); moved_preview = True
                os.replace(temporary, target)
                new_target = True
                ws._atomic_write(preview, (target / "0000.png").read_bytes())
            except Exception:
                if new_target and target.exists(): shutil.rmtree(target)
                if moved_target: os.replace(backup, target)
                if moved_preview:
                    if preview.exists(): preview.unlink()
                    os.replace(preview_backup, preview)
                raise
            if backup.exists(): shutil.rmtree(backup, ignore_errors=True)
            if preview_backup.exists(): preview_backup.unlink(missing_ok=True)
        return index
    finally:
        if temporary.exists(): shutil.rmtree(temporary)
