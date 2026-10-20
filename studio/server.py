"""Loopback-only studio HTTP API and allowlisted media transport."""

from __future__ import annotations

import hmac
import json
import mimetypes
import re
import secrets
from contextlib import nullcontext
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlsplit

from studio import agent_runs, characters, creative, generation, jobs, references, workspace as ws

JSON_LIMIT = 2 * 1024 * 1024
NATIVE_OUTPUT_LIMIT = generation.NATIVE_OUTPUT_LIMIT
MEDIA = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp3", ".wav", ".m4a", ".ogg", ".mp4", ".webm", ".mov"}
DOWNLOAD = MEDIA | {".pdf", ".docx", ".md", ".txt", ".json", ".svg"}
_VIDEO = re.compile(r"/api/videos/([a-z0-9][a-z0-9_-]*(?:/(?!reviews(?:/|$)|research(?:/|$)|production(?:/|$)|style(?:/|$)|creative(?:/|$))[a-z0-9][a-z0-9-]*)?)(?:/(.*))?\Z")
_JOB = re.compile(r"/api/jobs/([A-Za-z0-9_-]+)(?:/(cancel))?\Z")
_REQUEST = re.compile(r"/api/requests/([A-Za-z0-9_-]+)/(run|cancel|log)\Z")
_STYLE = re.compile(r"/api/styles/([a-z0-9][a-z0-9-]*)\Z")
_CHARACTER = re.compile(r"/api/characters/([a-z0-9][a-z0-9-]*)(?:/(.*))?\Z")
_CREATIVE = re.compile(r"/api/creative/(style|character)/([a-z0-9][a-z0-9-]*)(?:/(.*))?\Z")
_GENERATION = re.compile(r"/api/generations/([a-z0-9][a-z0-9-]*)(?:/(approve|run|outputs))?\Z")
_APP = re.compile(r"/(?:|videos|videos/new|videos/(?:[a-z0-9][a-z0-9_-]*/)?[a-z0-9][a-z0-9-]*|videos/(?:[a-z0-9][a-z0-9_-]*/)?[a-z0-9][a-z0-9-]*/review/[a-z-]+|jobs|jobs/[A-Za-z0-9_-]+|library|styles|styles/new|styles/[a-z0-9][a-z0-9-]*|characters|characters/new|characters/[a-z0-9][a-z0-9-]*|creative/(?:style|character)/[a-z0-9][a-z0-9-]*/review/[a-z0-9:-]+|generations/[a-z0-9][a-z0-9-]*|settings)\Z")
_TRUSTED = re.compile(r"(?:videos/(?:[a-z0-9][a-z0-9_-]*/)?[a-z0-9][a-z0-9-]*/(?:04_scene/(?:index\.html|[A-Za-z0-9_./-]+\.(?:js|css|png|jpg|jpeg|webp|gif|mp3|wav|m4a|ogg|mp4|webm))|creative/[A-Za-z0-9_./,\[\]-]+\.(?:js|css|html|json|png|jpg|jpeg|webp|gif|avif|svg|ttf|woff2?)|05_render/contact\.html|05_render/stills/[A-Za-z0-9_./-]+\.(?:png|jpg|jpeg))|styles/[a-z0-9][a-z0-9-]*/(?:template|03_sample/(?:wide|tall))/[A-Za-z0-9_./-]+\.(?:html|js|css|png|jpg|jpeg|webp|gif)|characters/[a-z0-9][a-z0-9-]*/03_animation/[a-z0-9][a-z0-9-]*/preview/[a-z0-9][a-z0-9-]*/[A-Za-z0-9_./-]+\.(?:html|js|css|png|jpg|jpeg|webp|gif)|_runtime/[A-Za-z0-9_./-]+\.(?:js|css|html|png|jpg|jpeg|webp|gif))\Z")
_CUES = re.compile(r"videos/(?:[a-z0-9][a-z0-9_-]*/)?[a-z0-9][a-z0-9-]*/03_cues/cues\.js\Z")
_VOICE = re.compile(r"videos/(?:[a-z0-9][a-z0-9_-]*/)?[a-z0-9][a-z0-9-]*/01_voice/(?:voice\.(?:wav|mp3|m4a|ogg)|takes/[0-9]+\.mp3)\Z")
_FONT = re.compile(r"_runtime/fonts/[A-Za-z0-9_./,\[\]-]+\.(?:css|ttf|woff2?)\Z")
_LIBRARY = re.compile(r"library/(?:(?:icons|graphics|lottie)/[A-Za-z0-9_./-]+\.(?:svg|js|png|jpg|jpeg|webp|gif)|blocks/(?:GALLERY\.html|[a-z0-9-]+/preview\.png))\Z")
_BRAND_LIBRARY = re.compile(r"brands/[a-z0-9][a-z0-9_-]*/library/[A-Za-z0-9_./-]+\.(?:html|css|svg|js|png|jpg|jpeg|webp|gif|mp3|wav|m4a|ogg|mp4|webm)\Z")
_SOUND = re.compile(r"_shared/sound/[A-Za-z0-9_./-]+\.(?:mp3|wav|m4a|ogg)\Z")


def _trusted(relative: str) -> bool:
    return any(pattern.fullmatch(relative) for pattern in (_TRUSTED, _CUES, _VOICE, _FONT, _LIBRARY, _BRAND_LIBRARY, _SOUND))


def _decoded_path(raw: str) -> str:
    if re.search(r"%(?:25(?:2e|2f|5c)|2f|5c|00)", raw, re.I):
        raise ws.WorkspaceError("invalid", "Invalid encoded path.")
    path = unquote(raw)
    if "%" in path or "\\" in path or "\x00" in path or any(p in (".", "..") or p.startswith(".") for p in path.split("/") if p):
        raise ws.WorkspaceError("invalid", "Invalid path.")
    return path


def _range(value: str | None, size: int) -> tuple[int, int] | None:
    if value is None:
        return None
    match = re.fullmatch(r"bytes=(\d*)-(\d*)", value)
    if not match or not size or not (match[1] or match[2]):
        raise ValueError("invalid range")
    if match[1]:
        start = int(match[1]); end = min(int(match[2]), size - 1) if match[2] else size - 1
    else:
        suffix = int(match[2])
        if not suffix: raise ValueError("invalid suffix")
        start, end = max(0, size - suffix), size - 1
    if start >= size or start > end:
        raise ValueError("outside range")
    return start, end


def make_server(root: Path, port: int = 8765) -> ThreadingHTTPServer:
    root = Path(root).resolve()
    token = secrets.token_urlsafe(32)
    jobs.recover_jobs(root)
    agent_runs.recover(root)

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *args):
            pass

        def _send(self, code: int, body: bytes, content_type: str, extra: dict | None = None):
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store")
            if extra:
                for key, value in extra.items(): self.send_header(key, value)
            self.end_headers()
            if self.command != "HEAD": self.wfile.write(body)

        def _json(self, code: int, value):
            self._send(code, json.dumps(value, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

        def _error(self, code: int, reason: str, message: str):
            self._json(code, {"error": {"code": reason, "message": message}})

        def _guard(self, write=False, allow_opaque=False):
            expected = f"127.0.0.1:{self.server.server_port}"
            if self.headers.get("Host") not in (expected, f"localhost:{self.server.server_port}"):
                self._error(403, "blocked", "Host is not the local studio.")
                return False
            origin = self.headers.get("Origin")
            if origin and not (origin == "null" and allow_opaque) and urlsplit(origin) not in (urlsplit(f"http://{expected}"), urlsplit(f"http://localhost:{self.server.server_port}")):
                self._error(403, "blocked", "Origin is not the local studio.")
                return False
            if write and not hmac.compare_digest(self.headers.get("X-Studio-Token", ""), token):
                self._error(403, "blocked", "Studio was restarted or this page is out of date: reload the page (F5) and try again.")
                return False
            return True

        def _body(self, limit=JSON_LIMIT):
            try: size = int(self.headers.get("Content-Length", "-1"))
            except ValueError: size = -1
            if size < 0 or size > limit:
                self.close_connection = True
                raise ws.WorkspaceError("invalid", f"JSON body must be at most {limit // (1024 * 1024)} MiB.")
            self._body_read = True
            try: value = json.loads(self.rfile.read(size))
            except (ValueError, UnicodeDecodeError):
                raise ws.WorkspaceError("invalid", "Invalid JSON body.") from None
            if not isinstance(value, dict): raise ws.WorkspaceError("invalid", "Expected a JSON object.")
            return value

        def _file(self, path: Path, *, attachment=False, public_asset=False):
            try:
                size = path.stat().st_size
                interval = _range(self.headers.get("Range"), size)
            except FileNotFoundError:
                self._error(404, "missing", "File not found."); return
            except ValueError:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Content-Length", "0")
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers(); return
            start, end = interval if interval else (0, size - 1)
            length = end - start + 1 if size else 0
            mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            self.send_response(206 if interval else 200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(length))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store")
            if public_asset and self.headers.get("Origin") == "null":
                self.send_header("Access-Control-Allow-Origin", "null")
            if path.suffix.lower() == ".svg":
                self.send_header("Content-Security-Policy", "script-src 'none'; object-src 'none'")
                if self.headers.get("Sec-Fetch-Dest") != "image": attachment = True
            if attachment:
                fallback = path.name.encode("ascii", "replace").decode("ascii")
                fallback = re.sub(r'["\\\\\x00-\x1f\x7f]', "_", fallback)
                self.send_header("Content-Disposition", f'attachment; filename="{fallback}"; filename*=UTF-8\'\'{quote(path.name, safe="")}')
            if interval: self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.end_headers()
            if self.command == "HEAD": return
            try:
                with path.open("rb") as source:
                    source.seek(start)
                    remaining = length
                    while remaining:
                        chunk = source.read(min(65536, remaining))
                        if not chunk: break
                        self.wfile.write(chunk)
                        remaining -= len(chunk)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def _public_file(self, relative, *, attachment=False, trusted=False):
            try:
                referer = urlsplit(self.headers.get("Referer", "")).path
                scene = re.match(r"/videos/([a-z0-9][a-z0-9_-]*(?:/[a-z0-9][a-z0-9-]*)?)/(?:04_scene|creative)/", referer)
                if scene and (root / "videos" / scene[1] / "creative/snapshot.json").is_file() and relative.startswith(("_runtime/", "_shared/", "library/", "styles/", "characters/")):
                    raise ws.WorkspaceError("missing", "Shared dependency is outside this video snapshot.")
                path = ws.safe_path(root, relative)
                if not path.is_file() or path.is_symlink(): raise ws.WorkspaceError("missing", "File not found.")
                if trusted:
                    if not _trusted(relative) or ".." in relative.split("/"):
                        raise ws.WorkspaceError("missing", "File not found.")
                elif path.suffix.lower() not in (DOWNLOAD if attachment else MEDIA):
                    raise ws.WorkspaceError("missing", "File not found.")
                if path.suffix.lower() in {".svg", ".html", ".js"} and not trusted:
                    attachment = True
                self._file(path, attachment=attachment, public_asset=True)
            except ws.WorkspaceError:
                self._error(404, "missing", "File not found.")

        def _source_file(self, relative):
            try:
                if Path(relative).suffix.lower() not in {".js", ".html", ".css"}:
                    raise ws.WorkspaceError("missing", "Source not found.")
                declared = {source for row in (*ws.list_style_families(root), *ws.list_styles(root))
                            for source in row.get("references", [])}
                if relative in declared:
                    source = ws._style_reference_path(root, relative)
                elif relative.startswith(("_runtime/", "_templates/")) or not _trusted(relative):
                    raise ws.WorkspaceError("missing", "Source not found.")
                else:
                    source = ws.safe_path(root, relative)
                if not source.is_file() or source.is_symlink():
                    raise ws.WorkspaceError("missing", "Source not found.")
                self._file(source, attachment=True, public_asset=True)
            except ws.WorkspaceError:
                self._error(404, "missing", "File not found.")

        def _handle(self):
            raw = urlsplit(self.path)
            try: path = _decoded_path(raw.path)
            except ws.WorkspaceError:
                self._error(404, "missing", "Route not found."); return
            public_asset = (path.startswith("/media/") or (path.startswith("/") and _trusted(path[1:]))) and self.command in ("GET", "HEAD")
            if not self._guard(write=self.command in ("POST", "PUT", "PATCH", "DELETE"), allow_opaque=public_asset): return
            try:
                if path == "/api/bootstrap" and self.command in ("GET", "HEAD"):
                    shell = parse_qs(raw.query).get("view") == ["shell"]
                    data = {"brands": sorted(p.parent.name for p in (root / "brands").glob("*/tokens.js")), "token": token, "jobs": jobs.list_jobs(root), "requests": jobs.list_requests(root)}
                    if not shell:
                        data.update(videos=ws.list_videos(root), styles=ws.list_styles(root))
                    self._json(200, data)
                elif path == "/api/videos" and self.command == "GET":
                    self._json(200, ws.list_videos(root, summary=parse_qs(raw.query).get("view") == ["summary"]))
                elif path == "/api/files" and self.command == "GET":
                    relative = parse_qs(raw.query).get("path", [""])[0]
                    if "%" in relative: raise ws.WorkspaceError("invalid", "Invalid encoded path.")
                    self._json(200, ws.read_file(root, relative))
                elif path == "/api/files" and self.command == "PUT":
                    body = self._body()
                    self._json(200, ws.save_text(root, body.get("path"), body.get("text"), body.get("expected_revision")))
                elif path == "/api/jobs" and self.command == "GET": self._json(200, jobs.list_jobs(root))
                elif path == "/api/jobs" and self.command == "POST":
                    body = self._body()
                    self._json(202, jobs.start_job(root, body.get("action"), body.get("slug"), body.get("options", {}),
                                                    body.get("expected_fingerprint"), body.get("request_id")))
                elif path == "/api/requests" and self.command == "GET": self._json(200, jobs.list_requests(root))
                elif path == "/api/requests" and self.command == "POST":
                    body = self._body()
                    self._json(202, jobs.create_request(root, body.get("slug"), body.get("kind"), body.get("instructions"),
                                                        body.get("fingerprint"), body.get("request_id"),
                                                        subject=body.get("subject"), input_revision=body.get("input_revision")))
                elif path == "/api/materials" and self.command == "GET":
                    filters = {k: v[0] for k, v in parse_qs(raw.query).items()}
                    if "ids" in filters:
                        self._json(200, ws.material_details(root, [ident for ident in filters["ids"].split(",") if ident]))
                    elif filters.pop("view", None) == "summary":
                        self._json(200, ws.inventory_page(root, "materials", filters))
                    else:
                        self._json(200, ws.list_materials(root, filters))
                elif path == "/api/materials/item" and self.command == "GET":
                    self._json(200, ws.material_detail(root, parse_qs(raw.query).get("id", [""])[0]))
                elif path == "/api/materials" and self.command == "POST": self._json(201, ws.create_material(root, self._body()))
                elif path == "/api/materials/link" and self.command == "POST":
                    body = self._body()
                    self._json(200, ws.link_material(root, body.get("owner_kind"), body.get("owner_id"), body.get("material_id")))
                elif path == "/api/materials/files" and self.command == "GET":
                    filters = {k: v[0] for k, v in parse_qs(raw.query).items()}
                    self._json(200, ws.inventory_page(root, "files", filters) if filters.get("view") == "summary" else ws.list_public_files(root))
                elif path == "/api/materials/upload" and self.command == "POST": self._upload()
                elif path == "/api/styles" and self.command == "GET": self._json(200, ws.list_styles(root))
                elif path == "/api/characters" and self.command == "GET": self._json(200, characters.list_characters(root))
                elif path == "/api/characters" and self.command == "POST":
                    body = self._body()
                    self._json(201, characters.create_character(root, body.get("id"), body.get("prompt"), body.get("metadata", {})))
                elif (match := _CHARACTER.fullmatch(path)):
                    ident, tail = match.groups()
                    if tail is None and self.command == "GET": self._json(200, characters.character_detail(root, ident))
                    elif tail == "candidates" and self.command == "POST":
                        body = self._body()
                        self._json(200, characters.register_character_candidates(root, ident, body.get("generation_id"), body.get("expected_revision"),
                            replace_revision=body.get("replace_revision"), confirm_replace=body.get("confirm_replace") is True))
                    elif tail == "candidate" and self.command == "PUT":
                        body = self._body()
                        self._json(200, characters.select_character_candidate(root, ident, body.get("candidate_id"), body.get("expected_revision")))
                    elif tail == "identity/generation" and self.command == "POST":
                        body = self._body()
                        if set(body) - {"transport", "image_model"}: raise ws.WorkspaceError("invalid", "Unknown identity batch option.")
                        self._json(201, characters.prepare_character_identity(root, ident,
                            transport=body.get("transport", "codex-cli"), image_model=body.get("image_model")))
                    elif tail == "identity/reference-set" and self.command == "PUT":
                        body = self._body()
                        self._json(200, characters.register_character_identity(root, ident, body.get("generation_id"),
                            body.get("constraints"), body.get("expected_revision"),
                            replace_revision=body.get("replace_revision"), confirm_replace=body.get("confirm_replace") is True))
                    elif tail and re.fullmatch(r"variants/[a-z0-9][a-z0-9-]*", tail) and self.command == "POST":
                        body = self._body()
                        self._json(201, characters.register_character_variant(root, ident, tail.split("/")[1],
                            body.get("manifest"), body.get("expected_revision"),
                            replace_revision=body.get("replace_revision"), confirm_replace=body.get("confirm_replace") is True))
                    elif tail and re.fullmatch(r"variants/[a-z0-9][a-z0-9-]*/capabilities", tail) and self.command == "GET":
                        self._json(200, characters.character_capabilities(root, ident, tail.split("/")[1]))
                    elif tail and re.fullmatch(r"variants/[a-z0-9][a-z0-9-]*/native/capabilities", tail) and self.command == "GET":
                        self._json(200, characters.character_capabilities(root, ident, tail.split("/")[1])["native"])
                    elif tail and re.fullmatch(r"variants/[a-z0-9][a-z0-9-]*/native/candidate", tail) and self.command == "POST":
                        body = self._body()
                        if set(body) - {"expected_variant_revision", "expected_source_sha256", "replace_revision", "confirm_replace"}:
                            raise ws.WorkspaceError("invalid", "Unknown native candidate option.")
                        self._json(201, characters.register_native_candidate(root, ident, tail.split("/")[1],
                            body.get("expected_variant_revision"), body.get("expected_source_sha256"),
                            replace_revision=body.get("replace_revision"), confirm_replace=body.get("confirm_replace")))
                    elif tail and re.fullmatch(r"variants/[a-z0-9][a-z0-9-]*/native/activate", tail) and self.command == "POST":
                        body = self._body()
                        if set(body) - {"expected_fingerprint"}:
                            raise ws.WorkspaceError("invalid", "Unknown native activation option.")
                        self._json(200, characters.activate_native_candidate(root, ident, tail.split("/")[1], body.get("expected_fingerprint")))
                    elif tail and re.fullmatch(r"variants/[a-z0-9][a-z0-9-]*/native/render", tail) and self.command == "POST":
                        body = self._body()
                        if set(body) - {"view", "action", "expression", "expected_fingerprint", "request_id"}:
                            raise ws.WorkspaceError("invalid", "Unknown native render option.")
                        self._json(202, jobs.start_job(root, "native-render", ident,
                            {"variant": tail.split("/")[1], "view": body.get("view"), "action": body.get("action"),
                             "expression": body.get("expression")}, body.get("expected_fingerprint"), body.get("request_id")))
                    elif tail and re.fullmatch(r"variants/[a-z0-9][a-z0-9-]*/generation", tail) and self.command == "POST":
                        body = self._body()
                        if set(body) - {"style_id", "prompt", "monochrome_exception", "transport", "image_model"}:
                            raise ws.WorkspaceError("invalid", "Unknown variant batch option.")
                        self._json(201, characters.prepare_character_variant(root, ident, tail.split("/")[1], body.get("style_id"),
                            body.get("prompt"), body.get("monochrome_exception", False),
                            transport=body.get("transport", "codex-cli"), image_model=body.get("image_model")))
                    elif tail and re.fullmatch(r"variants/[a-z0-9][a-z0-9-]*/actions/[a-z0-9][a-z0-9-]*/(manifest|template|prepare|export)", tail):
                        from studio import character_motion
                        _, variant, _, action, operation = tail.split("/")
                        if operation == "manifest" and self.command == "GET":
                            self._json(200, character_motion.compile_character_pack(root, ident, variant, action=action))
                        elif operation == "template" and self.command == "GET":
                            self._json(200, character_motion.motion_template(action))
                        elif operation == "prepare" and self.command == "POST":
                            body = self._body()
                            if set(body) - {"transport", "image_model"}: raise ws.WorkspaceError("invalid", "Unknown animation art batch option.")
                            self._json(201, character_motion.prepare_animation(root, ident, variant, action,
                                transport=body.get("transport", "codex-cli"), image_model=body.get("image_model")))
                        elif operation == "export" and self.command == "POST":
                            body = self._body()
                            if set(body) - {"view", "fps", "prop"}: raise ws.WorkspaceError("invalid", "Unknown animation export option.")
                            self._json(200, character_motion.export_character_frames(root, ident, variant, action,
                                                                                       body.get("view"), body.get("fps", 30), prop=body.get("prop")))
                        else: self._error(404, "missing", "Route not found.")
                    else: self._error(404, "missing", "Route not found.")
                elif path == "/api/style-families" and self.command == "GET": self._json(200, ws.list_style_families(root))
                elif path == "/api/generations" and self.command == "GET":
                    records = []
                    for file in sorted((root / ".studio/generations").glob("*.json"), reverse=True)[:100]:
                        if ws.ID.fullmatch(file.stem):
                            try: records.append(generation.generation_detail(root, file.stem))
                            except ws.WorkspaceError: continue
                    self._json(200, records)
                elif path == "/api/generations" and self.command == "POST":
                    self._json(201, generation.prepare_generation(root, self._body()))
                elif (match := _GENERATION.fullmatch(path)):
                    ident, operation = match.groups()
                    if operation is None and self.command == "GET": self._json(200, generation.generation_detail(root, ident))
                    elif operation == "approve" and self.command == "POST":
                        body = self._body()
                        if set(body) - {"reviewer", "billing_acknowledged"}: raise ws.WorkspaceError("invalid", "Unknown batch approval option.")
                        self._json(200, generation.approve_generation(root, ident, body.get("reviewer"),
                                                                       billing_acknowledged=body.get("billing_acknowledged", False)))
                    elif operation == "run" and self.command == "POST":
                        body = self._body()
                        if set(body) - {"transport"}: raise ws.WorkspaceError("invalid", "Unknown generation run option.")
                        record = generation.generation_detail(root, ident)
                        self._json(200, generation.run_generation(root, ident, body.get("transport", record["transport"])))
                    elif operation == "outputs" and self.command == "POST":
                        body = self._body(NATIVE_OUTPUT_LIMIT)
                        if set(body) != {"outputs", "provenance"}: raise ws.WorkspaceError("invalid", "Native output registration needs files and tool provenance.")
                        self._json(200, generation.register_generated_outputs(root, ident, body["outputs"], body["provenance"]))
                    else: self._error(404, "missing", "Route not found.")
                elif path == "/api/creative" and self.command == "POST":
                    body = self._body()
                    self._json(201, creative.create_creative(root, body.get("type"), body.get("id"), body.get("prompt"), body.get("metadata", {})))
                elif path == "/api/creative" and self.command == "GET" and parse_qs(raw.query).get("view") == ["summary"]:
                    self._json(200, creative.review_summaries(root))
                elif (match := _CREATIVE.fullmatch(path)):
                    subject_type, ident, tail = match.groups()
                    if tail is None and self.command == "GET": self._json(200, creative.creative_detail(root, subject_type, ident))
                    elif tail == "answers" and self.command == "PUT":
                        body = self._body()
                        answers = body.get("form", body.get("answers"))
                        if "form" not in body and "answers" in body and any(key in body for key in creative._FORM_FIELDS):
                            answers = {key: body[key] for key in ("answers", *creative._FORM_FIELDS) if key in body}
                        self._json(200, creative.save_workshop_answers(root, subject_type, ident, answers,
                                                                        brief=body.get("brief"), form_url=body.get("form_url"),
                                                                        expected_revision=body.get("expected_revision")))
                    elif subject_type == "style" and tail == "materials-plan" and self.command == "GET":
                        self._json(200, references.plan_style_materials(root, ident))
                    elif subject_type == "style" and tail == "materials-request" and self.command == "POST":
                        body = self._body()
                        self._json(202, references.request_style_materials(root, ident, body.get("route"), body.get("description"),
                                                                            url=body.get("url"), expected_revision=body.get("expected_revision")))
                    elif subject_type == "style" and tail == "website-reference" and self.command == "POST":
                        body = self._body()
                        self._json(200, references.save_website_reference(root, ident, body.get("evidence"), body.get("expected_revision")))
                    elif subject_type == "style" and tail in {"sample/wide", "sample/tall"} and self.command == "GET":
                        self._json(200, references.sample_status(root, ident, tail.split("/")[1]))
                    elif subject_type == "style" and tail in {"sample/wide", "sample/tall"} and self.command == "POST":
                        body = self._body()
                        if set(body) - {"expected_revision"}: raise ws.WorkspaceError("invalid", "Sample render accepts only an input revision.")
                        self._json(200, references.prepare_style_sample(root, ident, tail.split("/")[1], expected_revision=body.get("expected_revision")))
                    elif tail and tail.startswith("reviews/"):
                        bits = tail.split("/")
                        gate = bits[1] if len(bits) > 1 else ""
                        if len(bits) == 2 and self.command == "GET":
                            self._json(200, creative.creative_review_state(root, subject_type, ident, gate))
                        elif len(bits) == 3 and self.command == "POST":
                            body = self._body()
                            if bits[2] == "ready":
                                state = creative.mark_creative_ready(root, subject_type, ident, gate, body.get("expected_revision"))
                            elif bits[2] == "decision":
                                state = creative.decide_creative(root, subject_type, ident, gate, body.get("decision"), body.get("reviewer"),
                                                                  body.get("note", ""), body.get("expected_revision"))
                            else:
                                self._error(404, "missing", "Route not found."); return
                            state["review_url"] = f"http://{self.headers['Host']}/creative/{subject_type}/{ident}/review/{quote(gate, safe=':')}"
                            self._json(200, state)
                        else: self._error(404, "missing", "Route not found.")
                    else: self._error(404, "missing", "Route not found.")
                elif path == "/api/styles" and self.command == "POST":
                    body = self._body()
                    self._json(201, ws.create_style(root, body.get("id"), body.get("title"), body.get("base_kit", "modern")))
                elif (match := _STYLE.fullmatch(path)):
                    style_id = match[1]
                    if self.command == "GET": self._json(200, ws.read_file(root, f"styles/{style_id}/style.md"))
                    elif self.command == "PUT":
                        body = self._body()
                        self._json(200, ws.save_style(root, style_id, body.get("text"), body.get("expected_revision")))
                    else: self._error(404, "missing", "Route not found.")
                elif (match := _REQUEST.fullmatch(path)):
                    request_id, tail = match.groups()
                    if tail == "run" and self.command == "POST": self._json(200, agent_runs.start_run(root, request_id, self._body().get("mode")))
                    elif tail == "cancel" and self.command == "POST": self._json(200, agent_runs.cancel_run(root, request_id))
                    elif tail == "log" and self.command == "GET": self._json(200, agent_runs.run_status(root, request_id))
                    else: self._error(404, "missing", "Route not found.")
                elif (match := _JOB.fullmatch(path)):
                    job_id, tail = match.groups()
                    if not tail and self.command == "GET": self._json(200, jobs.job_detail(root, job_id))
                    elif tail == "cancel" and self.command == "POST": self._json(200, jobs.cancel_job(root, job_id))
                    else: self._error(404, "missing", "Route not found.")
                elif (match := _VIDEO.fullmatch(path)):
                    slug, tail = match.groups()
                    if tail is None and self.command == "GET":
                        self._json(200, ws.video_detail(root, slug, summary=parse_qs(raw.query).get("view") in (["summary"], ["shell"])))
                    elif tail == "production" and self.command == "GET":
                        self._json(200, jobs.managed_runs(root, slug))
                    elif tail == "production" and self.command == "POST":
                        body = self._body()
                        self._json(202, jobs.start_managed_run(root, slug, body.get("settings"), body.get("resume")))
                    elif tail and tail.startswith("reviews/"):
                        bits = tail.split("/")
                        gate = bits[1]
                        if len(bits) == 2 and self.command == "GET": self._json(200, ws.review_state(root, slug, gate))
                        elif len(bits) == 3 and self.command == "POST":
                            body = self._body()
                            if bits[2] == "ready": self._json(200, ws.mark_ready(root, slug, gate, body.get("expected_fingerprint")))
                            elif bits[2] == "decision": self._json(200, ws.decide_review(root, slug, gate, body.get("decision"), body.get("reviewer"), body.get("note", ""), body.get("expected_fingerprint")))
                            else: self._error(404, "missing", "Route not found.")
                        else: self._error(404, "missing", "Route not found.")
                    elif tail == "research/skip" and self.command == "POST":
                        body = self._body(); self._json(200, ws.skip_research(root, slug, body.get("reason"), body.get("reviewer")))
                    elif tail == "style" and self.command == "POST":
                        body = self._body(); self._json(200, ws.apply_style(root, slug, body.get("style_id"), body.get("expected_revision"), bool(body.get("confirm", False))))
                    elif tail == "creative" and self.command == "POST":
                        body = self._body()
                        self._json(200, ws.apply_creative_snapshot(root, slug, body.get("style_id"), body.get("characters", []),
                                                                    body.get("expected_revision"), bool(body.get("confirm", False))))
                    else: self._error(404, "missing", "Route not found.")
                elif path.startswith("/media/") and self.command in ("GET", "HEAD"):
                    self._public_file(path[7:])
                elif path.startswith("/download/") and self.command in ("GET", "HEAD"):
                    self._public_file(path[10:], attachment=True)
                elif path.startswith("/source/") and self.command in ("GET", "HEAD"):
                    self._source_file(path[8:])
                elif path in ("/app.js", "/app.css", "/creative.js") and self.command in ("GET", "HEAD"):
                    self._file(root / "studio/web" / path[1:])
                elif (scene := re.fullmatch(r"/videos/([a-z0-9][a-z0-9_-]*(?:/[a-z0-9][a-z0-9-]*)?)/04_scene/index\.html", path)) and (root / "videos" / scene[1] / "creative/snapshot.json").is_file() and self.command in ("GET", "HEAD"):
                    self._send(200, ws.creative_scene_html(root, scene[1]).encode("utf-8"), "text/html; charset=utf-8")
                elif (scene := re.fullmatch(r"/videos/([a-z0-9][a-z0-9_-]*(?:/[a-z0-9][a-z0-9-]*)?)/04_scene/([A-Za-z0-9_./-]+\.(?:js|css|html))", path)) and (root / "videos" / scene[1] / "creative/snapshot.json").is_file() and self.command in ("GET", "HEAD"):
                    mime = mimetypes.guess_type(scene[2])[0] or "text/plain"
                    self._send(200, ws.creative_scene_source(root, scene[1], scene[2]).encode("utf-8"), mime + "; charset=utf-8")
                elif path.startswith("/fonts/") and self.command in ("GET", "HEAD") and re.fullmatch(r"/fonts/[A-Za-z0-9_.-]+\.(?:woff2?|ttf)", path):
                    self._file(root / "studio/web" / path[1:])
                elif path.startswith("/") and _trusted(path[1:]) and self.command in ("GET", "HEAD"):
                    self._public_file(path[1:], trusted=True)
                elif _APP.fullmatch(path) and self.command in ("GET", "HEAD"):
                    self._file(root / "studio/web/index.html")
                else: self._error(404, "missing", "Route not found.")
            except ws.WorkspaceError as error:
                status = {"invalid": 400, "missing": 404, "conflict": 409, "blocked": 409, "busy": 409, "io": 500}.get(error.code, 500)
                self._error(status, error.code, str(error))
            except (BrokenPipeError, ConnectionResetError):
                return
            except (OSError, ValueError, TypeError):
                self._error(500, "io", "Studio could not complete this request.")

        def _upload(self):
            try: size = int(self.headers.get("Content-Length", "-1"))
            except ValueError: size = -1
            limit = 500 * 1024 * 1024
            if size < 0 or size > limit:
                raise ws.WorkspaceError("invalid", "Upload exceeds the 500 MiB limit.")
            self._body_read = True
            filename = self.headers.get("X-Material-Filename", "")
            encoding = self.headers.get("X-Material-Filename-Encoding")
            if encoding == "uri":
                if re.search(r"%(?![0-9a-fA-F]{2})", filename):
                    raise ws.WorkspaceError("invalid", "Invalid encoded upload filename.")
                try: filename = unquote(filename, encoding="utf-8", errors="strict")
                except UnicodeDecodeError:
                    raise ws.WorkspaceError("invalid", "Invalid encoded upload filename.") from None
            elif encoding is not None:
                raise ws.WorkspaceError("invalid", "Unknown upload filename encoding.")
            if not filename or "/" in filename or "\\" in filename or any(ord(c) < 32 or ord(c) == 127 for c in filename):
                raise ws.WorkspaceError("invalid", "Invalid upload filename.")
            metadata_header = self.headers.get("X-Material-Metadata", "{}")
            if len(metadata_header) > 8192: raise ws.WorkspaceError("invalid", "Material metadata is too large.")
            try: metadata = json.loads(metadata_header)
            except ValueError: raise ws.WorkspaceError("invalid", "Invalid material metadata.") from None
            if not isinstance(metadata, dict): raise ws.WorkspaceError("invalid", "Invalid material metadata.")
            import tempfile
            with tempfile.TemporaryFile() as stream:
                remaining = size
                while remaining:
                    chunk = self.rfile.read(min(65536, remaining))
                    if not chunk: raise ws.WorkspaceError("io", "Upload ended before the file was complete.")
                    stream.write(chunk); remaining -= len(chunk)
                stream.seek(0)
                self._json(201, ws.create_material(root, metadata, content=stream, filename=filename))

        def _handle_request(self):
            self._body_read = False
            with ws.read_scope() if self.command in ("GET", "HEAD") else nullcontext():
                self._handle()
            if self.command in ("POST", "PUT", "PATCH", "DELETE"):
                ws.readcache.invalidate(root)
            # A body the route never read would be parsed as the next request on this connection.
            try: size = int(self.headers.get("Content-Length", "0"))
            except ValueError: size = -1
            if not self._body_read and size:
                if 0 < size <= JSON_LIMIT: self.rfile.read(size)
                else: self.close_connection = True

        do_GET = _handle_request
        do_HEAD = _handle_request
        do_POST = _handle_request
        do_PUT = _handle_request

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def serve(root: Path, port: int = 8765) -> None:
    server = make_server(root, port)
    print(f"studio: http://127.0.0.1:{server.server_port}/  (Ctrl+C stops it)")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally:
        server.shutdown()
        server.server_close()
