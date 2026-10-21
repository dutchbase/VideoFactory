"""OpenAI image generation handoff with explicit batch approval and verified files."""

from __future__ import annotations

import json
import base64
import binascii
import hashlib
import os
import shutil
import subprocess
import sys
import uuid
from collections import Counter
from pathlib import Path

from PIL import Image

from studio import workspace as ws
from studio.creative import creative_fingerprint, creative_review_state
from studio.production import production_lock, lease_fds, child_environment
from studio.permissions import require_permission, child_environment as permission_environment
from studio.paid_requests import atomic_json, money

_ROUTES = {"native", "codex-cli", "openai-api"}
_PURPOSES = {"character-concepts": ("character", "brief", 3),
             "character-identity": ("character", "design", 2),
             "character-variant": ("character", "identity", 1),
             "character-animation": ("character", "identity", 1),
             "style-material": ("style", "brief", 1)}
_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
MAX_IMAGE_BYTES = 16 * 1024 * 1024
MAX_IMAGE_PIXELS = 4096 * 4096
NATIVE_OUTPUT_LIMIT = 4 * MAX_IMAGE_BYTES + 1024 * 1024  # Three base64 images plus bounded JSON metadata.
_API_SCRIPT = Path.home() / ".codex/skills/.system/imagegen/scripts/image_gen.py"


def _record_path(root, ident):
    return Path(root) / ".studio/generations" / f"{ws._id(ident)}.json"


def _save(root, record):
    ws._atomic_write(_record_path(root, record["id"]), (json.dumps(record, ensure_ascii=False, indent=2) + "\n").encode())


def generation_detail(root, id):
    path = _record_path(root, id)
    if not path.is_file():
        raise ws.WorkspaceError("missing", "Generation request does not exist.")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ws.WorkspaceError("invalid", "Generation record is unreadable.") from None


def _references(root, references):
    if not isinstance(references, list) or len(references) > 8:
        raise ws.WorkspaceError("invalid", "Use at most eight image references.")
    resolved = []
    for item in references:
        if not isinstance(item, dict) or set(item) != {"material_id", "role"} or not isinstance(item["role"], str) or not item["role"].strip() or len(item["role"]) > 200:
            raise ws.WorkspaceError("invalid", "Each reference needs a material ID and role.")
        material = ws._material(root, ws._id(item["material_id"]))
        images = []
        source = material["source"]
        names = material["files"] + ([source] if isinstance(source, str) and not source.startswith(("http:", "https:")) and source != "upload" else [])
        for name in names:
            path = ws.safe_path(root, name)
            if path.suffix.lower() in _IMAGE_SUFFIXES and path.is_file():
                try:
                    with Image.open(path) as image: image.verify()
                except (OSError, ValueError):
                    raise ws.WorkspaceError("invalid", "Reference image is unreadable.") from None
                images.append({"path": name, "sha256": ws._file_hash(path)})
        if not images:
            raise ws.WorkspaceError("invalid", "Reference material has no readable raster image.")
        resolved.append({"material_id": item["material_id"], "role": item["role"].strip(),
                         "material_sha256": ws._file_hash(ws.safe_path(root, material["path"])),
                         "images": images})
    return resolved


def _canonical_paths(root, subject_id, purpose):
    if purpose == "character-identity":
        path = ws.safe_path(root, f"characters/{subject_id}/01_design/candidates.json")
        try:
            candidates = json.loads(path.read_text(encoding="utf-8"))
            selected = [entry for entry in candidates if isinstance(entry, dict) and entry.get("selected") is True]
            if len(selected) != 1 or not isinstance(selected[0].get("path"), str): raise ValueError
            return [selected[0]["path"]]
        except (OSError, ValueError, TypeError):
            raise ws.WorkspaceError("blocked", "Select exactly one approved concept before identity generation.") from None
    if purpose in {"character-variant", "character-animation"}:
        path = ws.safe_path(root, f"characters/{subject_id}/02_identity/reference-set.json")
        try:
            reference_set = json.loads(path.read_text(encoding="utf-8"))
            paths = [reference_set[name] for name in ("sheet", "in_scene")]
            if not all(isinstance(item, str) for item in paths): raise ValueError
            return paths
        except (OSError, ValueError, TypeError, KeyError):
            raise ws.WorkspaceError("blocked", "Approved sheet and in-scene references are required.") from None
    return []


def _check_canonical_references(root, subject_id, purpose, resolved):
    hashes = Counter(image["sha256"] for ref in resolved for image in ref["images"])
    for relative in _canonical_paths(root, subject_id, purpose):
        path = ws.safe_path(root, relative)
        if not path.is_file() or hashes[ws._file_hash(path)] < 1:
            raise ws.WorkspaceError("blocked", "Batch must attach the approved canonical image references.")
        hashes[ws._file_hash(path)] -= 1


def _current(root, record):
    subject_type, subject_id = record["subject_type"], record["subject_id"]
    gate = _PURPOSES[record["purpose"]][1]
    state = creative_review_state(root, subject_type, subject_id, gate)
    if state["state"] not in {"approved", "accepted"} or not state["ready"] or state["fingerprint"] != record["input_revision"]:
        raise ws.WorkspaceError("conflict", "Approved creative inputs changed.")
    if _references(root, record["references"]) != record["resolved_references"]:
        raise ws.WorkspaceError("conflict", "Generation reference files changed.")
    _check_canonical_references(root, subject_id, record["purpose"], record["resolved_references"])
    if record["purpose"] == "character-animation":
        _check_animation_variant(root, subject_id, record["context"], record["resolved_references"])
    if record["purpose"] in {"character-variant", "character-animation"}:
        context = record.get("context", {})
        ws._style(root, context["style_id"])
        if context["style_revision"] != ws._style_revision(root, context["style_id"]):
            raise ws.WorkspaceError("conflict", "Variant style inputs changed.")


def _check_animation_variant(root, subject_id, context, resolved):
    from studio.characters import _registered_variant
    variant = _registered_variant(root, subject_id, context["variant_id"])
    if variant["style_id"] != context["style_id"] or variant["monochrome_exception"] != context["monochrome_exception"]:
        raise ws.WorkspaceError("conflict", "Animation target variant changed.")
    if variant["artwork"]["sha256"] not in [image["sha256"] for item in resolved for image in item["images"]]:
        raise ws.WorkspaceError("blocked", "Animation batch must attach the registered variant artwork.")


def prepare_generation(root, request):
    root = Path(root).resolve()
    if not isinstance(request, dict) or set(request) - {"id", "subject_type", "subject_id", "purpose", "prompt", "references", "transparent", "image_count", "input_revision", "provider", "transport", "image_model", "context", "max_paid_spend"}:
        raise ws.WorkspaceError("invalid", "Malformed generation request.")
    ident = ws._id(request.get("id"))
    purpose = request.get("purpose")
    if purpose not in _PURPOSES or request.get("subject_type") != _PURPOSES[purpose][0]:
        raise ws.WorkspaceError("invalid", "Unsupported generation purpose or subject.")
    subject_id = ws._id(request.get("subject_id"))
    scope = request["subject_type"] + ":" + subject_id
    try: require_permission(root, scope)
    except ValueError as exc: raise ws.WorkspaceError("blocked", str(exc)) from None
    if request.get("provider", "openai") != "openai" or request.get("transport", "codex-cli") not in _ROUTES:
        raise ws.WorkspaceError("invalid", "Only the selected OpenAI route is supported.")
    if request.get("image_model") is not None and (request.get("transport") != "openai-api" or request["image_model"] not in {"gpt-image-2", "gpt-image-1.5"}):
        raise ws.WorkspaceError("invalid", "Explicit image model selection is only for the OpenAI API route.")
    if request.get("transport") == "openai-api" and request.get("transparent") is True and request.get("image_model") != "gpt-image-1.5":
        raise ws.WorkspaceError("invalid", "Transparent OpenAI API art requires an explicit gpt-image-1.5 choice.")
    if request.get("transport") == "openai-api":
        maximum = money(request.get("max_paid_spend"))
        if maximum <= 0: raise ws.WorkspaceError("invalid", "Choose a positive maximum image spend.")
    elif request.get("max_paid_spend") is not None:
        raise ws.WorkspaceError("invalid", "Maximum paid spend applies to the API route.")
    if not isinstance(request.get("prompt"), str) or not request["prompt"].strip() or len(request["prompt"]) > 20000:
        raise ws.WorkspaceError("invalid", "A generation prompt is required.")
    if not isinstance(request.get("transparent"), bool) or type(request.get("image_count")) is not int or request["image_count"] not in range(1, 4):
        raise ws.WorkspaceError("invalid", "Transparency and one to three images are required.")
    if request["image_count"] != _PURPOSES[purpose][2]:
        raise ws.WorkspaceError("invalid", "Image count does not match the review purpose.")
    context = request.get("context")
    if purpose in {"character-variant", "character-animation"}:
        if (not isinstance(context, dict) or set(context) != {"variant_id", "style_id", "style_revision", "monochrome_exception"} or
                not isinstance(context["monochrome_exception"], bool) or
                not isinstance(context["style_revision"], str) or len(context["style_revision"]) != 64):
            raise ws.WorkspaceError("invalid", "Variant generation needs a target and current style revision.")
        ws._id(context["variant_id"])
        ws._id(context["style_id"])
        ws._style(root, context["style_id"])
        if context["style_revision"] != ws._style_revision(root, context["style_id"]):
            raise ws.WorkspaceError("conflict", "Variant style inputs changed.")
    elif context is not None:
        raise ws.WorkspaceError("invalid", "This generation purpose does not accept variant context.")
    gate = _PURPOSES[purpose][1]
    state = creative_review_state(root, request["subject_type"], subject_id, gate)
    if state["state"] not in {"approved", "accepted"} or not state["ready"] or request.get("input_revision") != state["fingerprint"]:
        raise ws.WorkspaceError("blocked", "Current upstream approval is required.")
    references = request.get("references", [])
    resolved = _references(root, references)
    _check_canonical_references(root, subject_id, purpose, resolved)
    if purpose == "character-animation":
        _check_animation_variant(root, subject_id, context, resolved)
    output_dir = f"{'characters' if request['subject_type'] == 'character' else 'styles'}/{subject_id}/generated/{ident}"
    ws.safe_path(root, output_dir)
    record = {"id": ident, "subject_type": request["subject_type"], "subject_id": subject_id,
              "purpose": purpose, "prompt": request["prompt"].strip(), "references": references,
              "resolved_references": resolved, "transparent": request["transparent"],
              "image_count": request["image_count"], "input_revision": state["fingerprint"],
              "context": context,
              "provider": "openai", "transport": request.get("transport", "codex-cli"),
              "output_dir": output_dir, "state": "awaiting-batch-approval", "created_at": ws._now(),
              "outputs": [], "image_model": "unknown", "requested_image_model": request.get("image_model"), "coordinator": None,
              "max_paid_spend": str(maximum) if request.get("transport") == "openai-api" else None,
              "review": {"purpose": purpose, "image_count": request["image_count"], "context": context,
                         "route": request.get("transport", "codex-cli"), "prompt": request["prompt"].strip()}}
    with ws.workspace_lock(root):
        if _record_path(root, ident).exists():
            raise ws.WorkspaceError("conflict", "Generation request ID already exists.")
        _save(root, record)
        if record["transport"] == "openai-api":
            atomic_json(root / '.studio/runs' / (ident + '.json'),
                        dict(id=ident, scope=scope, settings=dict(max_paid_spend=str(maximum))))
    return record


def approve_generation(root, request_id, reviewer, *, billing_acknowledged=False):
    if os.environ.get("VF_PERMISSION_WORKER") == "1":
        raise ws.WorkspaceError("blocked", "A worker cannot approve a paid image batch.")
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise ws.WorkspaceError("invalid", "Batch reviewer is required.")
    with ws.workspace_lock(root):
        record = generation_detail(root, request_id)
        try: require_permission(root, record['subject_type'] + ':' + record['subject_id'])
        except ValueError as exc: raise ws.WorkspaceError("blocked", str(exc)) from None
        if record["state"] != "awaiting-batch-approval":
            raise ws.WorkspaceError("conflict", "Batch is no longer awaiting approval.")
        if record["transport"] == "openai-api" and billing_acknowledged is not True:
            raise ws.WorkspaceError("blocked", "OpenAI API billing acknowledgement is required.")
        _current(root, record)
        record.update(state="approved", approved_by=reviewer.strip(), approved_at=ws._now(),
                      billing_acknowledged=bool(billing_acknowledged))
        _save(root, record)
    return record


def _codex_preflight():
    cli = shutil.which("codex")
    if not cli:
        raise ws.WorkspaceError("blocked", "Codex CLI is unavailable.")
    checks = ([cli, "login", "status"], [cli, "features", "list"], [cli, "exec", "--help"])
    try:
        auth, features, help_text = (subprocess.run(args, capture_output=True, text=True, timeout=15) for args in checks)
    except (OSError, subprocess.TimeoutExpired):
        raise ws.WorkspaceError("blocked", "Codex CLI preflight failed.") from None
    if auth.returncode or "logged in" not in auth.stdout.lower() + auth.stderr.lower():
        raise ws.WorkspaceError("blocked", "Codex CLI is not authenticated.")
    if features.returncode or not any(line.split()[-1] == "true" for line in features.stdout.splitlines() if line.startswith("image_generation ")):
        raise ws.WorkspaceError("blocked", "Codex image generation feature is unavailable.")
    if help_text.returncode or not all(flag in help_text.stdout for flag in ("--image", "--output-schema")):
        raise ws.WorkspaceError("blocked", "Codex CLI lacks image attachment or structured output support.")
    return cli


def _run_codex(root, record, cli):
    output_dir = ws.safe_path(root, record["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    schema = output_dir / "response-schema.json"
    last = output_dir / "response.json"
    ws._atomic_write(schema, json.dumps({"type": "object", "properties": {
        "outputs": {"type": "array", "items": {"type": "string"}},
        "image_model": {"type": "string"}}, "required": ["outputs"], "additionalProperties": False}).encode())
    remaining = record["image_count"] - len(record["outputs"])
    prompt = ("Use $imagegen and the OpenAI built-in image tool to create exactly " + str(remaining) +
              " raster image(s). Do not use another provider or draw placeholder art. " +
              "Copy each actual generated image into this allowed output directory: " + str(output_dir) +
              ". Never overwrite existing files. Return only relative workspace paths to saved images. " +
              "If the tool is unavailable, return an empty outputs list. Purpose: " + record["purpose"] +
              ". Transparent background required: " + str(record["transparent"]).lower() +
              ". User prompt: " + record["prompt"])
    images = [str(ws.safe_path(root, image["path"])) for ref in record["resolved_references"] for image in ref["images"]]
    if images:
        roles = [ref["role"] for ref in record["resolved_references"] for _ in ref["images"]]
        prompt += "\nAttached input images in order: " + "; ".join(f"{i + 1}: {role}" for i, role in enumerate(roles))
    cmd = [cli, "exec", "--json", "--output-schema", str(schema), "--output-last-message", str(last),
           "--cd", str(root), "--sandbox", "workspace-write"]
    for image in images: cmd += ["--image", image]
    cmd += [prompt]
    try:
        result = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=900,
           pass_fds=lease_fds(), env=os.environ | child_environment(root) | permission_environment(root, record['subject_type'] + ':' + record['subject_id']), start_new_session=True)
    except (OSError, subprocess.TimeoutExpired):
        raise ws.WorkspaceError("blocked", "Codex image generation did not complete.") from None
    events = []
    for line in result.stdout.splitlines():
        try: events.append(json.loads(line))
        except ValueError: pass
    tool_used = any(_completed_image_tool(event) for event in events)
    if result.returncode or not last.is_file():
        return {"outputs": [], "image_tool_used": tool_used, "error": "Codex generation failed."}
    try: answer = json.loads(last.read_text(encoding="utf-8"))
    except ValueError: answer = {"outputs": []}
    return {"outputs": answer.get("outputs", []), "image_model": "unknown",
            "image_tool_used": tool_used}


def _completed_image_tool(event):
    if not isinstance(event, dict) or event.get("type") != "item.completed": return False
    item = event.get("item")
    if not isinstance(item, dict) or item.get("type") != "mcp_tool_call" or item.get("status") != "completed" or item.get("error") or (isinstance(item.get("result"), dict) and item["result"].get("isError")):
        return False
    return ((item.get("server"), item.get("tool")) == ("image_gen", "imagegen") or
            item.get("name") in {"mcp__image_gen__imagegen", "image_gen.imagegen"})


def image_request_id(record, index, model=None):
    """Stable identity used to quote each image, including all reference hashes."""
    value = {key: record.get(key) for key in ('prompt', 'transparent', 'resolved_references', 'purpose', 'context')}
    value.update(index=index, model=model or record.get('requested_image_model') or 'gpt-image-2')
    return 'image-' + hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def _run_api(root, record):
    if not record.get("billing_acknowledged") or not os.environ.get("OPENAI_API_KEY") or not _API_SCRIPT.is_file():
        raise ws.WorkspaceError("blocked", "Explicit API billing acknowledgement, key and installed imagegen script are required.")
    model = record.get("requested_image_model") or "gpt-image-2"
    if record["transparent"] and model != "gpt-image-1.5":
        raise ws.WorkspaceError("blocked", "API transparency requires explicit gpt-image-1.5 selection in the approved batch.")
    output_dir = ws.safe_path(root, record["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for index in range(len(record["outputs"]) + 1, record["image_count"] + 1):
        path = output_dir / f"image-{index}.png"
        images = [str(ws.safe_path(root, image["path"])) for ref in record["resolved_references"] for image in ref["images"]]
        args = [sys.executable, str(_API_SCRIPT), "edit" if images else "generate", "--model", model,
                "--prompt", record["prompt"], "--out", str(path)]
        for image in images: args += ["--image", image]
        if record["transparent"]: args += ["--background", "transparent"]
        from studio.paid_requests import managed_quote, reserve, settle
        request_id = image_request_id(record, index, model)
        purchase = dict(model=model, index=index, image_count=record['image_count'],
                        subject=f"{record['subject_type']}:{record['subject_id']}", purpose=record['purpose'],
                        prompt=record['prompt'], size='auto', quality='medium',
                        transparent=record['transparent'], references=record['resolved_references'])
        managed_run, quote = managed_quote(root, request_id, purpose='image', metadata=purchase, run_id=record['id'])
        request_id = quote['request_id']
        reserve(root, managed_run, request_id, quote['max_cost'], provider='openai', purpose='image')
        try: result = subprocess.run(args, cwd=root, capture_output=True, text=True, timeout=900,
                                     pass_fds=lease_fds(), env=os.environ | child_environment(root) | permission_environment(root, record['subject_type'] + ':' + record['subject_id']), start_new_session=True)
        except (OSError, subprocess.TimeoutExpired): break
        if result.returncode: break
        settle(root, managed_run, request_id, quote['max_cost'], estimated_upper_bound=True)
        outputs.append(path.relative_to(root).as_posix())
    return {"outputs": outputs, "image_tool_used": bool(outputs), "image_model": model}


def run_generation(root, request_id, transport="codex-cli"):
    with production_lock(root, 'image-generation'):
        return _run_generation(root, request_id, transport)


def _run_generation(root, request_id, transport="codex-cli"):
    root = Path(root).resolve()
    if transport != "openai-api":
        raise ws.WorkspaceError("blocked", "Image generation needs a verified maximum-cost quote and separate purchase approval. Use the quoted OpenAI API route.")
    with ws.workspace_lock(root):
        record = generation_detail(root, request_id)
        try: require_permission(root, record['subject_type'] + ':' + record['subject_id'])
        except ValueError as exc: raise ws.WorkspaceError("blocked", str(exc)) from None
        if transport not in _ROUTES or transport != record["transport"]:
            raise ws.WorkspaceError("invalid", "Generation route differs from approved batch.")
        if record["state"] not in {"approved", "partial"}:
            raise ws.WorkspaceError("blocked", "Approve this batch before generation.")
        _current(root, record)
        if transport == "native":
            return {**record, "handoff": "Use the native OpenAI image tool, copy files into output_dir, then register actual outputs and tool results."}
        cli = _codex_preflight() if transport == "codex-cli" else None
        if transport == "openai-api" and (not record.get("billing_acknowledged") or not os.environ.get("OPENAI_API_KEY") or not _API_SCRIPT.is_file()):
            raise ws.WorkspaceError("blocked", "OpenAI API setup and billing acknowledgement are required.")
        run_id = uuid.uuid4().hex
        record["state"] = "running"
        record["run_id"] = run_id
        record["started_at"] = ws._now()
        _save(root, record)
    try:
        result = _run_codex(root, record, cli) if cli else _run_api(root, record)
    except Exception:
        _finish_run(root, request_id, run_id, "Generation transport failed; inspect request output directory for drafts.")
        raise
    provenance = {"provider": "openai", "transport": transport, "coordinator": "Codex CLI" if cli else "OpenAI imagegen CLI",
                  "image_model": result.get("image_model", "unknown"), "image_tool_used": result.get("image_tool_used", False)}
    outputs = result.get("outputs")
    if not isinstance(outputs, list) or any(not isinstance(path, str) for path in outputs) or len(outputs) > record["image_count"] - len(record["outputs"]):
        return _finish_run(root, request_id, run_id, "Transport returned too many or invalid output paths.")
    if not outputs or result.get("image_tool_used") is not True:
        return _finish_run(root, request_id, run_id, result.get("error", "No verified generated image was returned."))
    try:
        for output in outputs:
            _append_outputs(root, request_id, [output], provenance, run_id=run_id)
    except ws.WorkspaceError as error:
        return _finish_run(root, request_id, run_id, str(error))
    return _finish_run(root, request_id, run_id)


def _finish_run(root, request_id, run_id, error=None):
    with ws.workspace_lock(root):
        record = generation_detail(root, request_id)
        if record.get("run_id") != run_id or record["state"] != "running":
            return record
        record["state"] = "completed" if len(record["outputs"]) == record["image_count"] else "partial" if record["outputs"] else "approved"
        record.pop("run_id", None)
        record["finished_at"] = ws._now()
        if error: record["last_error"] = error
        else: record.pop("last_error", None)
        _save(root, record)
        return record


def register_generated_outputs(root, request_id, outputs, provenance):
    """Register a native tool result; CLI/API outputs are private to run_generation."""
    root = Path(root).resolve()
    if not isinstance(provenance, dict) or provenance.get("transport") != "native":
        raise ws.WorkspaceError("invalid", "External registration accepts native image tool results only.")
    return _append_outputs(root, request_id, outputs, provenance)


def _append_outputs(root, request_id, outputs, provenance, *, run_id=None):
    if not isinstance(outputs, list) or not outputs or not isinstance(provenance, dict) or provenance.get("provider") != "openai" or provenance.get("transport") not in _ROUTES or provenance.get("image_tool_used") is not True or not isinstance(provenance.get("coordinator"), str) or not provenance["coordinator"].strip():
        raise ws.WorkspaceError("invalid", "Verified OpenAI tool provenance and image paths are required.")
    with ws.workspace_lock(root):
        record = generation_detail(root, request_id)
        valid_state = record["state"] == "running" and record.get("run_id") == run_id if run_id else record["state"] in {"approved", "partial"} and record["transport"] == "native"
        if not valid_state or provenance["transport"] != record["transport"]:
            raise ws.WorkspaceError("blocked", "Output route or batch approval is invalid.")
        _current(root, record)
        if len(outputs) + len(record["outputs"]) > record["image_count"]:
            raise ws.WorkspaceError("invalid", "Too many images for this approved batch.")
        accepted = []
        tool_results = provenance.get("tool_results")
        if record["transport"] == "native" and (not isinstance(tool_results, list) or len(tool_results) != len(outputs)):
            raise ws.WorkspaceError("invalid", "Native registration needs one actual tool result per output.")
        for relative in outputs:
            path = ws.safe_path(root, relative)
            if path.parent != ws.safe_path(root, record["output_dir"]) or path.suffix.lower() not in _IMAGE_SUFFIXES or not path.is_file() or any(o["path"] == relative for o in record["outputs"] + accepted):
                raise ws.WorkspaceError("invalid", "Output must be a new image in the approved directory.")
            if path.stat().st_size > MAX_IMAGE_BYTES:
                raise ws.WorkspaceError("invalid", "Output image exceeds the 16 MiB limit.")
            try:
                with Image.open(path) as image:
                    if image.width * image.height > MAX_IMAGE_PIXELS:
                        raise ValueError
                    image.load()
                    if image.format not in {"PNG", "JPEG", "WEBP"} or image.width < 1 or image.height < 1:
                        raise ValueError
                    if record["transparent"] and ("A" not in image.getbands() or image.getchannel("A").getextrema()[0] == 255):
                        raise ValueError
                    dimensions = [image.width, image.height]
            except (OSError, ValueError):
                raise ws.WorkspaceError("invalid", "Output image is unreadable or lacks genuine transparency.") from None
            if record["transport"] == "native":
                tool_result = tool_results[len(accepted)]
                url = tool_result.get("image_url") if isinstance(tool_result, dict) else None
                if not isinstance(url, str) or not url.startswith("data:image/") or ";base64," not in url:
                    raise ws.WorkspaceError("invalid", "Native image tool result is missing image bytes.")
                encoded = url.split(";base64,", 1)[1]
                if len(encoded) > 4 * ((MAX_IMAGE_BYTES + 2) // 3):
                    raise ws.WorkspaceError("invalid", "Native image tool result exceeds the 16 MiB limit.")
                try: image_bytes = base64.b64decode(encoded, validate=True)
                except (ValueError, binascii.Error):
                    raise ws.WorkspaceError("invalid", "Native image tool result is malformed.") from None
                if len(image_bytes) > MAX_IMAGE_BYTES:
                    raise ws.WorkspaceError("invalid", "Native image tool result exceeds the 16 MiB limit.")
                if hashlib.sha256(image_bytes).hexdigest() != ws._file_hash(path):
                    raise ws.WorkspaceError("invalid", "Saved native image differs from the tool result.")
            accepted.append({"path": relative, "sha256": ws._file_hash(path), "dimensions": dimensions,
                             "registered_at": ws._now()})
        record["outputs"] += accepted
        record.update(image_model=provenance.get("image_model") or "unknown", coordinator=provenance["coordinator"],
                      last_registered_at=ws._now())
        if not run_id:
            record["state"] = "completed" if len(record["outputs"]) == record["image_count"] else "partial"
        _save(root, record)
    return record
