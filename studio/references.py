"""Public website evidence, material choices, and rendered style samples."""

from __future__ import annotations

import asyncio
import fcntl
import hashlib
import html as htmllib
import http.client
import ipaddress
import json
import mimetypes
import os
import re
import socket
import ssl
import subprocess
import uuid
from fractions import Fraction
from io import BytesIO
from PIL import Image
from libcore import ALLOWED
from pathlib import Path
from urllib.parse import unquote, urlsplit

from studio import workspace as ws
from studio.creative import creative_fingerprint, creative_review_state


def _public_address(url):
    if not isinstance(url, str) or len(url) > 2048 or "\\" in url or any(ord(char) < 32 for char in url):
        raise ws.WorkspaceError("invalid", "Public HTTP(S) URL required.")
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise ws.WorkspaceError("invalid", "Public HTTP(S) URL without credentials or fragment required.")
    try:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
    except (OSError, ValueError):
        raise ws.WorkspaceError("invalid", "Website host does not resolve.") from None
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ws.WorkspaceError("invalid", "Website must resolve only to public addresses.")
    chosen = next((item for item in addresses if item[0] == socket.AF_INET), addresses[0])
    return parsed, chosen[4][0], parsed.port or (443 if parsed.scheme == "https" else 80)


def public_url(url):
    _public_address(url)
    return url


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host, address, port):
        super().__init__(host, port, timeout=15, context=ssl.create_default_context())
        self.address = address

    def connect(self):
        raw = socket.create_connection((self.address, self.port), self.timeout)
        self.sock = self._context.wrap_socket(raw, server_hostname=self.host)


def _pinned_fetch(url, request_headers):
    parsed, address, port = _public_address(url)
    connection = (_PinnedHTTPSConnection(parsed.hostname, address, port) if parsed.scheme == "https" else
                  http.client.HTTPConnection(address, port, timeout=15))
    path = (parsed.path or "/") + ("?" + parsed.query if parsed.query else "")
    headers = {"Host": parsed.netloc, **{key: value for key, value in request_headers.items()
                                        if key.lower() in {"accept", "accept-language", "user-agent"}}}
    try:
        connection.request("GET", path, headers=headers)
        response = connection.getresponse()
        body = response.read(20 * 1024 * 1024 + 1)
        if len(body) > 20 * 1024 * 1024:
            raise ws.WorkspaceError("invalid", "Website resource exceeds 20 MiB.")
        kept = {key: value for key, value in response.getheaders()
                if key.lower() in {"content-type", "content-encoding", "location", "cache-control"}}
        return response.status, kept, body
    finally:
        connection.close()


def plan_style_materials(root, style_id):
    style = ws._style(root, style_id)
    setting = style.get("setting", "")
    environment = style.get("environment", "")
    return {"style_id": style_id, "setting": setting, "environment": environment,
            "input_revision": creative_fingerprint(root, "style", style_id, "materials"),
            "state": "waiting-for-agent", "linked_materials": style["materials"],
            "options": [
                {"route": "supplied", "description": "Use images or footage you supply; describe the exact file, scene use and permission in a material record."},
                {"route": "openai", "description": "Request OpenAI imagery for the recurring setting, using the approved style brief and a reviewed generation batch."},
                {"route": "licensed-stock", "description": "Search the existing stock tooling; keep source URL, creator, licence and intended scene use in a material record."},
            ]}


def request_style_materials(root, style_id, route, description, *, url=None, expected_revision=None):
    if route not in {"supplied", "openai", "licensed-stock", "website"} or not isinstance(description, str) or not description.strip() or len(description) > 2000:
        raise ws.WorkspaceError("invalid", "Choose a material route and describe its scene use.")
    if url is not None: public_url(url)
    if route == "website" and url is None:
        raise ws.WorkspaceError("invalid", "Website inspection needs a public URL.")
    if creative_review_state(root, "style", style_id, "brief")["state"] != "approved":
        raise ws.WorkspaceError("blocked", "Approve the current style brief first.")
    from studio import jobs
    plan = plan_style_materials(root, style_id)
    if expected_revision != plan["input_revision"]:
        raise ws.WorkspaceError("conflict", "Style materials changed since you opened the plan.")
    instructions = (f"Style {style_id}: {description.strip()}\nRoute: {route}. "
                    "Record exact source files or URLs, intended scene use, rights and capture provenance in material records. "
                    "OpenAI imagery requires a separately reviewed generation batch; licensed stock uses existing stock search/use tools. "
                    "Website inspection uses the contained browser and unknown-rights logos remain references only.")
    if url: instructions += f"\nPublic website: {url}"
    return jobs.create_request(root, None, "website-reference" if route == "website" else "creative-material",
                               instructions, None, uuid.uuid4().hex, subject={"type": "style", "id": style_id},
                               input_revision=plan["input_revision"])


def save_website_reference(root, style_id, evidence, expected_revision):
    folder = ws.safe_path(root, f"styles/{ws._id(style_id)}")
    if not isinstance(evidence, dict) or set(evidence) - {"url", "final_url", "captured_at", "title", "screenshot", "palette", "fonts", "components", "logo_candidates", "motion", "motion_capture"}:
        raise ws.WorkspaceError("invalid", "Unexpected website evidence field.")
    public_url(evidence.get("url"))
    public_url(evidence.get("final_url", evidence["url"]))
    if not isinstance(evidence.get("captured_at"), str) or not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)", evidence["captured_at"]):
        raise ws.WorkspaceError("invalid", "Capture time needs an ISO timestamp.")
    screenshot = evidence.get("screenshot")
    if not isinstance(screenshot, str) or not screenshot.startswith(f"styles/{style_id}/02_assets/website/") or Path(screenshot).suffix.lower() != ".png":
        raise ws.WorkspaceError("invalid", "Screenshot must be an original PNG under this style's website assets.")
    image = ws.safe_path(root, screenshot)
    if not image.is_file() or image.stat().st_size > 20 * 1024 * 1024:
        raise ws.WorkspaceError("invalid", "Screenshot is missing or too large.")
    try:
        with Image.open(image) as screenshot_image:
            if screenshot_image.format != "PNG" or min(screenshot_image.size) < 100:
                raise ValueError
            screenshot_image.verify()
    except (OSError, ValueError):
        raise ws.WorkspaceError("invalid", "Screenshot must contain a readable original PNG.") from None
    if not isinstance(evidence.get("title", ""), str) or len(evidence.get("title", "")) > 500:
        raise ws.WorkspaceError("invalid", "Website title is too long.")
    if "motion_capture" in evidence:
        motion_capture = evidence["motion_capture"]
        if not isinstance(motion_capture, str) or not motion_capture.startswith(f"styles/{style_id}/02_assets/website/") or Path(motion_capture).suffix.lower() not in {".mp4", ".webm"} or not ws.safe_path(root, motion_capture).is_file():
            raise ws.WorkspaceError("invalid", "Motion capture must be a saved file under this style.")
        try: duration = float(sample_probe(ws.safe_path(root, motion_capture))["duration"])
        except (KeyError, ValueError, TypeError): duration = 0
        if not 0 < duration <= 15:
            raise ws.WorkspaceError("invalid", "Motion capture must be a clip of at most 15 seconds.")
    for key in ("palette", "fonts", "components", "logo_candidates"):
        items = evidence.get(key)
        if not isinstance(items, list) or len(items) > 40 or any(not isinstance(item, dict) for item in items):
            raise ws.WorkspaceError("invalid", f"{key} must be a bounded evidence list.")
        if any(any(not isinstance(value, str) or len(value) > 1000 for value in item.values()) for item in items):
            raise ws.WorkspaceError("invalid", "Website evidence values must be short text.")
    for item in evidence["logo_candidates"]:
        if item.get("rights") != "unknown" and not item.get("rights_source"):
            raise ws.WorkspaceError("invalid", "Logo rights need a source; otherwise record unknown.")
        public_url(item.get("url"))
        if "path" in item:
            source_path = item["path"]
            if not source_path.startswith(f"styles/{style_id}/02_assets/website/") or Path(source_path).suffix.lower() not in {".png", ".jpg", ".webp", ".gif"}:
                raise ws.WorkspaceError("invalid", "Logo originals must stay under this style's website assets.")
            original = ws.safe_path(root, source_path)
            if not original.is_file() or item.get("sha256") != hashlib.sha256(original.read_bytes()).hexdigest():
                raise ws.WorkspaceError("invalid", "Logo original is missing or changed.")
            try:
                with Image.open(original) as logo_image: logo_image.verify()
            except OSError:
                raise ws.WorkspaceError("invalid", "Logo original is not a readable raster image.") from None
    if "motion" in evidence:
        motion = evidence["motion"]
        if not isinstance(motion, list) or any(not isinstance(item, dict) or
            not isinstance(item.get("description"), str) or len(item["description"]) > 1000 for item in motion):
            raise ws.WorkspaceError("invalid", "Motion observations must be descriptions.")
    encoded = (json.dumps({**evidence, "screenshot_sha256": hashlib.sha256(image.read_bytes()).hexdigest()}, ensure_ascii=False, indent=2) + "\n").encode()
    with ws.workspace_lock(root):
        if expected_revision != creative_fingerprint(root, "style", style_id, "materials"):
            raise ws.WorkspaceError("conflict", "Style references changed during capture.")
        destination = folder / "02_assets/website/reference.json"
        ws._atomic_write(destination, encoded)
    return {"evidence": json.loads(encoded), "path": destination.relative_to(root).as_posix(),
            "revision": creative_fingerprint(root, "style", style_id, "materials")}


async def _inspect_page(endpoint, url):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(endpoint)
        context = await browser.new_context(viewport={"width": 1280, "height": 800},
                                            service_workers="block", java_script_enabled=False)
        async def allow(route):
            if route.request.url.startswith("data:"):
                await route.continue_(); return
            if route.request.method != "GET":
                await route.abort(); return
            try:
                status, headers, body = await asyncio.to_thread(_pinned_fetch, route.request.url, route.request.headers)
            except (ws.WorkspaceError, OSError, ValueError, ssl.SSLError):
                await route.abort(); return
            await route.fulfill(status=status, headers=headers, body=body)
        await context.route("**/*", allow)
        await context.route_web_socket("**/*", lambda connection: connection.close())
        page = await context.new_page()
        responses = []
        page.on("response", lambda response: responses.append(response))
        response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        if response is None or response.status >= 400 or "text/html" not in response.headers.get("content-type", ""):
            raise ws.WorkspaceError("invalid", "Website did not return a public HTML page.")
        public_url(page.url)
        data = await page.evaluate("""() => {
          const pick = (q) => [...document.querySelectorAll(q)].slice(0, 12);
          const color = (e, property) => getComputedStyle(e)[property];
          const components = pick('button,a,input,nav,header,footer').map(e => ({
            name: e.tagName.toLowerCase(), description: `${(e.innerText || e.getAttribute('aria-label') || '').trim().slice(0,80)}; background ${color(e,'backgroundColor')}; radius ${color(e,'borderRadius')}`
          }));
          const palette = [...new Set(pick('body,header,nav,button,a,h1,h2').flatMap(e => [color(e,'color'),color(e,'backgroundColor')]))]
            .filter(x => x && x !== 'rgba(0, 0, 0, 0)').map(color => ({color,source:'computed style'}));
          const fonts = [...new Set(pick('body,h1,h2,button,a').map(e => color(e,'fontFamily')))]
            .map(family => ({family,source:'computed font-family'}));
          const logo_candidates = pick('img[src],link[rel="icon"]').map(e => ({
            url: e.src || e.href, rights:'unknown', description: e.alt || e.rel || ''
          })).filter(x => (x.url.startsWith('https://') || x.url.startsWith('http://')) && /logo|icon/i.test(x.url+' '+x.description));
          return {title:document.title,palette,fonts,components,logo_candidates};
        }""")
        screenshot = await page.screenshot(full_page=True, type="png")
        originals = {}
        for item in data["logo_candidates"]:
            response = next((r for r in responses if r.url == item["url"] and r.ok), None)
            if response and response.headers.get("content-type", "").split(";", 1)[0] in {"image/png", "image/jpeg", "image/webp", "image/gif"}:
                try: original = await response.body()
                except Exception: continue
                if len(original) <= 5 * 1024 * 1024:
                    try:
                        with Image.open(BytesIO(original)) as image:
                            if image.format not in {"PNG", "JPEG", "WEBP", "GIF"}: raise ValueError
                            image.verify()
                        originals[item["url"]] = original
                    except (OSError, ValueError):
                        pass
        final_url = page.url
        await context.close()
        await browser.close()
        return data, screenshot, final_url, originals


def inspect_website(root, style_id, url):
    """Inspect a public page in an omabox Chromium; retain its screenshot and computed evidence."""
    public_url(url)
    ws._style(root, style_id)
    input_revision = creative_fingerprint(root, "style", style_id, "materials")
    from studio import jobs
    box, endpoint = jobs._contained_browser()
    try:
        data, screenshot, final_url, originals = asyncio.run(_inspect_page(endpoint, url))
    finally:
        jobs._stop_box(box)
    from datetime import datetime, timezone
    relative = f"styles/{style_id}/02_assets/website/original-{hashlib.sha256(screenshot).hexdigest()[:12]}.png"
    path = ws.safe_path(root, relative)
    with ws.workspace_lock(root):
        if creative_fingerprint(root, "style", style_id, "materials") != input_revision:
            raise ws.WorkspaceError("conflict", "Style references changed during capture.")
        path.parent.mkdir(parents=True, exist_ok=True)
        ws._atomic_write(path, screenshot)
        for candidate in data["logo_candidates"]:
            original = originals.get(candidate["url"])
            if original:
                with Image.open(BytesIO(original)) as image:
                    extension = {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp", "GIF": ".gif"}[image.format]
                digest = hashlib.sha256(original).hexdigest()
                candidate_path = f"styles/{style_id}/02_assets/website/logo-{digest[:12]}{extension}"
                ws._atomic_write(ws.safe_path(root, candidate_path), original)
                candidate.update(path=candidate_path, sha256=digest)
        evidence_revision = creative_fingerprint(root, "style", style_id, "materials")
    evidence = {"url": url, "final_url": final_url, "captured_at": datetime.now(timezone.utc).isoformat(),
                "screenshot": relative, **data}
    return save_website_reference(root, style_id, evidence, evidence_revision)


def sample_probe(path):
    try:
        result = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                 "stream=width,height,duration,nb_frames,avg_frame_rate", "-of", "json", str(path)],
                                capture_output=True, text=True, timeout=15, check=True)
        return json.loads(result.stdout)["streams"][0]
    except (OSError, ValueError, KeyError, IndexError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return {}


def _moving_frames(path):
    try:
        result = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf",
                                 "select=eq(n\\,0)+eq(n\\,96)+eq(n\\,192)", "-f", "framehash", "-"],
                                capture_output=True, text=True, timeout=30, check=True)
        hashes = [line.rsplit(",", 1)[-1].strip() for line in result.stdout.splitlines() if line and not line.startswith("#")]
        return len(hashes) == 3 and len(set(hashes)) == 3
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def _verified_generated_image(root, style_id, relative, image_hash):
    for record_path in (Path(root) / ".studio/generations").glob("*.json"):
        try: record = json.loads(record_path.read_text(encoding="utf-8"))
        except (OSError, ValueError): continue
        if (record.get("state") == "completed" and record.get("provider") == "openai" and
            record.get("subject_type") == "style" and record.get("subject_id") == style_id and
            any(output.get("path") == relative and output.get("sha256") == image_hash
                for output in record.get("outputs", []) if isinstance(output, dict))):
            return True
    return False


def _sample_image(root, style):
    for material_id in style["materials"]:
        material = ws._material(root, material_id)
        rights = material["rights"].strip()
        if rights not in ALLOWED | {"User supplied", "OpenAI generated"}:
            continue
        paths = material["files"] if material["source"] == "upload" else [material["source"]]
        for relative in paths:
            if relative.startswith(("http:", "https:")) or Path(relative).suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
                continue
            path = ws.safe_path(root, relative)
            if path.is_file():
                if rights == "OpenAI generated" and not _verified_generated_image(root, style["id"], relative, ws._file_hash(path)):
                    continue
                try:
                    with Image.open(path) as image: image.verify()
                    return path.relative_to(Path(root).resolve()).as_posix()
                except OSError:
                    continue
    return None


def _source_hashes(root, style_id, fmt, html, resources):
    root = Path(root).resolve()
    source_files = set()
    for directory in (root / "_runtime", root / f"styles/{style_id}/template/{fmt}"):
        if directory.is_dir():
            source_files.update(path for path in directory.rglob("*") if path.is_file() and not path.is_symlink())
    for relative in resources:
        source_files.add(ws.safe_path(root, relative))
    if html.is_file() and html.name == "index.html": source_files.add(html)
    sources = {path.relative_to(root).as_posix(): ws._file_hash(path) for path in source_files if path.is_file()}
    if html.name != "index.html":
        sources[f"styles/{style_id}/03_sample/{fmt}/index.html"] = ws._file_hash(html)
    return dict(sorted(sources.items()))


def _sample_output_valid(root, style_id, fmt, video, data, html):
    try:
        stream = sample_probe(video)
        dims = (960, 540) if fmt == "wide" else (540, 960)
        return (data["renderer"] == ws._style(root, style_id)["renderer"] and
                data["format"] == fmt and data["duration"] == 12 and data["fps"] == 24 and
                data["materials_revision"] == creative_fingerprint(root, "style", style_id, "materials") and
                data["video_sha256"] == ws._file_hash(video) and
                data["sources"] == _source_hashes(root, style_id, fmt, html, data["resources"]) and
                (int(stream["width"]), int(stream["height"])) == dims and
                11.95 <= float(stream["duration"]) <= 12.05 and int(stream["nb_frames"]) == 288 and
                Fraction(stream["avg_frame_rate"]) == 24 and _moving_frames(video))
    except (OSError, ValueError, KeyError, TypeError, ws.WorkspaceError):
        return False


def sample_valid(root, style_id, fmt):
    folder = ws.safe_path(root, f"styles/{ws._id(style_id)}/03_sample/{fmt}")
    video, manifest = folder / "sample.mp4", folder / "sample.json"
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        authored = ws.safe_path(root, f"styles/{style_id}/template/{fmt}/index.html")
        html = authored if authored.is_file() else folder / "index.html"
        return _sample_output_valid(root, style_id, fmt, video, data, html)
    except (OSError, ValueError, ws.WorkspaceError):
        return False


def _sample_lock(root, style_id, fmt):
    ws._id(style_id)
    if fmt not in {"wide", "tall"}: raise ws.WorkspaceError("invalid", "Unknown sample format.")
    path = Path(root) / ".studio" / f"sample-{style_id}-{fmt}.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def sample_status(root, style_id, fmt):
    ws._style(root, style_id)
    with _sample_lock(root, style_id, fmt).open("a+b") as lock:
        try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: return {"format": fmt, "state": "rendering", "ready": False}
        finally:
            try: fcntl.flock(lock, fcntl.LOCK_UN)
            except OSError: pass
    ready = sample_valid(root, style_id, fmt)
    return {"format": fmt, "state": "rendered" if ready else "missing", "ready": ready}


async def _render_sample(endpoint, html, target, dimensions):
    from playwright.async_api import async_playwright
    from anim import seek_shot
    process = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", "24",
                                "-vcodec", "mjpeg", "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                                "-movflags", "+faststart", str(target)], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(endpoint)
            context = await browser.new_context(viewport={"width": dimensions[0], "height": dimensions[1]}, service_workers="block")
            await context.route_web_socket("**/*", lambda connection: connection.close())
            page = await context.new_page()
            errors = []
            resources = {}
            page.on("pageerror", lambda error: errors.append(str(error)))
            root = html.resolve().parents[4]
            async def local_only(route):
                parsed = urlsplit(route.request.url)
                if parsed.scheme == "data":
                    await route.continue_(); return
                if parsed.scheme != "file":
                    errors.append("External scene resource is blocked.")
                    await route.abort(); return
                path = Path(unquote(parsed.path))
                if path != html and path != html.resolve():
                    try:
                        relative = path.relative_to(root).as_posix()
                        source = ws.safe_path(root, relative)
                        content = source.read_bytes()
                        resources[relative] = hashlib.sha256(content).hexdigest()
                    except (ValueError, OSError, ws.WorkspaceError):
                        errors.append("Scene resource leaves the workspace.")
                        await route.abort(); return
                    await route.fulfill(status=200, body=content,
                                        content_type=mimetypes.guess_type(path.name)[0] or "application/octet-stream")
                    return
                await route.continue_()
            await context.route("**/*", local_only)
            await page.goto(html.as_uri() + "?render")
            await page.wait_for_function("window.__ready === true", timeout=30000)
            if errors: raise ws.WorkspaceError("blocked", "Style sample scene failed: " + "; ".join(errors[:3]))
            for frame in range(288):
                process.stdin.write(await seek_shot(page, frame / 24, quality=84))
            if errors: raise ws.WorkspaceError("blocked", "Style sample scene failed: " + "; ".join(errors[:3]))
            await context.close()
            await browser.close()
        process.stdin.close()
        if process.wait(timeout=90):
            raise ws.WorkspaceError("blocked", "FFmpeg could not encode the sample.")
        return resources
    except Exception:
        process.kill()
        process.wait()
        raise
    finally:
        if process.stdin and not process.stdin.closed: process.stdin.close()
        process.stderr.close()


def _register_sample(root, style_id, fmt, staged_video, staged_manifest, staged_html, materials_revision, generated):
    folder = ws.safe_path(root, f"styles/{style_id}/03_sample/{fmt}")
    data = json.loads(staged_manifest.read_text(encoding="utf-8"))
    if not _sample_output_valid(root, style_id, fmt, staged_video, data, staged_html):
        raise ws.WorkspaceError("blocked", "Rendered sample failed source, duration or format verification.")
    with ws.workspace_lock(root):
        if creative_fingerprint(root, "style", style_id, "materials") != materials_revision:
            raise ws.WorkspaceError("conflict", "Style materials changed during sample rendering.")
        if not _sample_output_valid(root, style_id, fmt, staged_video, data, staged_html):
            raise ws.WorkspaceError("conflict", "Style sample sources changed during rendering.")
        targets = [(staged_video, folder / "sample.mp4"), (staged_manifest, folder / "sample.json")]
        if generated: targets.append((staged_html, folder / "index.html"))
        backups, installed = {}, []
        try:
            for _, target in targets:
                if target.exists():
                    backup = folder / f".previous-{uuid.uuid4().hex}-{target.name}"
                    os.replace(target, backup)
                    backups[target] = backup
            for staged, target in targets:
                os.replace(staged, target)
                installed.append(target)
            if not sample_valid(root, style_id, fmt):
                raise ws.WorkspaceError("blocked", "Registered sample failed verification.")
        except Exception:
            for target in installed: target.unlink(missing_ok=True)
            for target, backup in backups.items(): os.replace(backup, target)
            raise
        finally:
            for target, backup in backups.items():
                if target.exists(): backup.unlink(missing_ok=True)


def prepare_style_sample(root, style_id, format, *, expected_revision=None):
    with _sample_lock(root, style_id, format).open("a+b") as lock:
        try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ws.WorkspaceError("busy", "This style format is already rendering.") from None
        try: return _prepare_style_sample(root, style_id, format, expected_revision)
        finally: fcntl.flock(lock, fcntl.LOCK_UN)


def _prepare_style_sample(root, style_id, format, expected_revision):
    style = ws._style(root, style_id)
    if format not in style["supported_formats"]:
        raise ws.WorkspaceError("invalid", "Format is not claimed by this style.")
    if creative_review_state(root, "style", style_id, "materials")["state"] != "approved":
        raise ws.WorkspaceError("blocked", "Approve current style materials before rendering a sample.")
    materials_revision = creative_fingerprint(root, "style", style_id, "materials")
    if expected_revision is not None and expected_revision != materials_revision:
        raise ws.WorkspaceError("conflict", "Style materials changed since you opened them.")
    dimensions = (960, 540) if format == "wide" else (540, 960)
    folder = ws.safe_path(root, f"styles/{style_id}/03_sample/{format}")
    folder.mkdir(parents=True, exist_ok=True)
    renderer = style["renderer"]
    authored = ws.safe_path(root, f"styles/{style_id}/template/{format}/index.html")
    token = uuid.uuid4().hex
    staged_video = folder / f".sample-render-{token}.mp4"
    staged_manifest = folder / f".sample-manifest-{token}.json"
    staged_html = folder / f".sample-source-{token}.html"
    generated = not authored.is_file()
    image_path = None
    if not generated:
        html = authored
    else:
        if renderer != "modern":
            raise ws.WorkspaceError("blocked", f"{renderer} needs an authored {format} scene template using the existing player runtime.")
        image_path = _sample_image(root, style)
        setting = style.get("setting") or style.get("environment") or "A clear place to learn"
        components = (style.get("components") or ["A focused idea", "A useful next step"])[:3]
        captions = style.get("captions") or "Clear ideas, made visual"
        width, height = dimensions
        html = staged_html
        esc = lambda text: htmllib.escape(str(text))
        photo = (f'<img src="../../../../{esc(image_path)}" alt="" '
                 'style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.18">') if image_path else ""
        cards = "".join(f'<div class="vf-card" data-in="rise"><h3>{esc(item)}</h3></div>' for item in components)
        html_text = f'''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="../../../../_runtime/fonts/fonts.css" rel="stylesheet"><link href="../../../../_runtime/modern.css" rel="stylesheet">
<div id="stage" data-width="{width}" data-height="{height}">
<div class="vf-bg"><div class="vf-glow"></div><div class="vf-glow two"></div></div>{photo}
<section class="vf-shot">
<div class="vf-kicker" data-in="fade">{esc(style["title"])}</div>
<h1 class="vf-title" data-in="words" data-delay="0.2">{esc(setting)}</h1>
<div class="vf-cards" data-stagger="0.4" data-delay="1" style="--cols:{len(components)}">{cards}</div>
<div class="vf-chip hot" data-in="pop" data-delay="3">{esc(captions)}</div>
</section>
</div>
<script>window.ANIM={{meta:{{duration:12}},cueList:[],cues:{{}},words:[]}};</script>
<script src="../../../../_runtime/vendor/gsap.min.js"></script><script src="../../../../_runtime/player.js"></script>
<script src="../../../../_runtime/icons.js"></script><script src="../../../../_runtime/modern.js"></script>
<script>Modern.push(".vf-shot", 0, 12, {{to: 1.05}});</script>'''
        ws._atomic_write(html, html_text.encode())
    input_sources = _source_hashes(root, style_id, format, html, [])
    try:
        from studio import jobs
        box, endpoint = jobs._contained_browser()
        try: resources = asyncio.run(_render_sample(endpoint, html, staged_video, dimensions))
        finally: jobs._stop_box(box)
        current_sources = _source_hashes(root, style_id, format, html, resources)
        if any(current_sources.get(path) != digest for path, digest in {**input_sources, **resources}.items()):
            raise ws.WorkspaceError("conflict", "Style sample sources changed during rendering.")
        manifest = {"format": format, "duration": 12, "renderer": renderer, "fps": 24,
                    "materials_revision": materials_revision, "image_source": image_path,
                    "video_sha256": ws._file_hash(staged_video), "resources": sorted(resources),
                    "sources": current_sources}
        ws._atomic_write(staged_manifest, (json.dumps(manifest, indent=2) + "\n").encode())
        _register_sample(root, style_id, format, staged_video, staged_manifest, html, materials_revision, generated)
    finally:
        staged_video.unlink(missing_ok=True)
        staged_manifest.unlink(missing_ok=True)
        staged_html.unlink(missing_ok=True)
    video = folder / "sample.mp4"
    return {"format": format, "video": video.relative_to(root).as_posix(), "manifest": (folder / "sample.json").relative_to(root).as_posix(),
            "state": "rendered", "review": creative_review_state(root, "style", style_id, "sample"),
            "fingerprint": creative_fingerprint(root, "style", style_id, "sample")}
