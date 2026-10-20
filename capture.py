"""Web capture for the scenes: screenshots and scripted screen recordings. Used by anim.py grab / record / login."""
import json
import os
import re
import shlex
import time
from pathlib import Path

AUTH_DIR = Path(__file__).resolve().parent / "_auth"
# action -> number of arguments
ACTIONS = {"goto": 1, "click": 1, "hover": 1, "type": 2, "press": 1, "scroll": 1, "wait": 1, "wait_for": 1, "shot": 1, "crop": 1}
BREAKPOINTS = {"mobile": (390, 844), "tablet": (768, 1024), "laptop": (1280, 800), "desktop": (1920, 1080)}


def size(bp: str):
    if bp in BREAKPOINTS:
        return BREAKPOINTS[bp]
    m = re.fullmatch(r"(\d{3,4})x(\d{3,4})", bp)
    if not m:
        raise ValueError(f"unknown breakpoint '{bp}'. Use {', '.join(BREAKPOINTS)}, all, or WxH like 1000x700")
    return int(m[1]), int(m[2])


def breakpoints(opts: dict, cli):
    raw = cli or opts.get("breakpoints") or "laptop"
    out = list(BREAKPOINTS) if raw.strip() == "all" else [b.strip() for b in raw.split(",") if b.strip()]
    for b in out:
        size(b)  # validates
    return out


def steps_for(steps, bp: str):
    return [(act, args) for act, args, only in steps if only is None or bp in only]


def suffix(name: str, bps, bp: str) -> str:
    return name if len(bps) == 1 else f"{name}-{bp}"


def parse_steps(text: str):
    """Header lines `key: value`, a `---` line, then one step per line (optional `@bp,bp` prefix). Raises ValueError naming the line."""
    opts, steps, in_steps = {}, [], False
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line == "---":
            in_steps = True
            continue
        if not in_steps:
            key, _, val = line.partition(":")
            if not val:
                raise ValueError(f"line {n}: expected 'key: value' above the --- line")
            opts[key.strip()] = val.strip()
            continue
        words = shlex.split(line)
        only = None
        if words and words[0].startswith("@"):
            only = tuple(b for b in words[0][1:].split(",") if b)
            try:
                for b in only:
                    size(b)
            except ValueError as e:
                raise ValueError(f"line {n}: {e}") from None
            words = words[1:]
        if not words:
            raise ValueError(f"line {n}: a step is missing after the @ prefix")
        act, args = words[0], words[1:]
        if act not in ACTIONS:
            raise ValueError(f"line {n}: unknown step '{act}'. Known: {', '.join(ACTIONS)}")
        if len(args) != ACTIONS[act]:
            raise ValueError(f"line {n}: '{act}' takes {ACTIONS[act]} argument(s), got {len(args)}")
        if act == "type" and "password" in args[0].lower():
            raise ValueError(f"line {n}: never type a password in a steps file. Use: python anim.py login")
        steps.append((act, args, only))
    return opts, steps


def mask_script(selectors: str) -> str:
    """Init script: blur these elements on every page (best-effort redaction of names, emails, ...)."""
    css = f"{selectors}{{filter:blur(10px)!important}}"
    return ("document.addEventListener('DOMContentLoaded',()=>{const s=document.createElement('style');"
            f"s.textContent={json.dumps(css)};document.head.appendChild(s)}});")


def auth_path(name: str) -> Path:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name):
        raise ValueError(f"login name '{name}': use lowercase letters, digits and hyphens")
    return AUTH_DIR / f"{name}.json"


def save_auth(name: str, state: dict) -> Path:
    """Write a browser session to _auth/<name>.json: folder 0700, file 0600 from the first byte.
    Never print or log its content."""
    f = auth_path(name)
    AUTH_DIR.mkdir(mode=0o700, exist_ok=True)
    AUTH_DIR.chmod(0o700)
    tmp = f.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as out:
        json.dump(state, out)
    os.replace(tmp, f)
    return f


def clamp_box(box: dict, w: int, h: int) -> dict:
    """The crop box limited to the viewport: ffmpeg would shift a box that runs past the edge inward and take pixels
    from outside the element (a sidebar with chat history). An empty box is refused."""
    x0, y0 = max(0, box["x"]), max(0, box["y"])
    x1, y1 = min(w, box["x"] + box["width"]), min(h, box["y"] + box["height"])
    if x1 - x0 < 2 or y1 - y0 < 2:
        raise RuntimeError("crop: the element is outside the view")
    return {"x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0}


def expect_locator(page, expect: str):
    """`expect` is a CSS selector when it looks like one (#id, .class, [attr], tag=...), else visible text.
    Only visible matches count: a page often holds the same text in a hidden menu or alt text first."""
    loc = page.locator(expect) if expect.startswith(("#", ".", "[")) or "=" in expect else page.get_by_text(expect)
    return loc.filter(visible=True)


async def login_session(name: str, url: str, expect: str, timeout: float, headless: bool = False) -> Path:
    """Open a browser, let the user log in, save the session as soon as `expect` shows. Nothing is saved on a timeout."""
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=headless)
        try:
            ctx = await b.new_context()
            pg = await ctx.new_page()
            await pg.goto(url)
            try:
                await expect_locator(pg, expect).first.wait_for(timeout=timeout * 1000)
            except Exception:
                raise RuntimeError("not logged in, or a check page; nothing saved") from None
            return save_auth(name, await ctx.storage_state())
        finally:
            await b.close()


def log_capture(assets: Path, name: str, kind: str, url: str, auth: bool, bp: str = "laptop") -> None:
    """One row per capture in 04_scene/assets/captures.md: proof of what is real, where it came from, when.
    The URL is logged without query or fragment: those can hold tokens or personal data."""
    from urllib.parse import urlsplit
    u = urlsplit(url)
    url = f"{u.scheme}://{u.netloc}{u.path}" if u.scheme else url.split("?")[0].split("#")[0]
    f = assets / "captures.md"
    head = ["# Real captures (generated by anim.py grab / record, do not edit)", "",
            "| name | kind | url | breakpoint | date | login |", "|---|---|---|---|---|---|"]
    rows = [r for r in f.read_text(encoding="utf-8").splitlines()[4:] if r.strip()] if f.exists() else []
    rows = [r for r in rows if not r.startswith(f"| {name} |")]
    rows.append(f"| {name} | {kind} | {url} | {bp} | {time.strftime('%Y-%m-%d')} | {'yes' if auth else 'no'} |")
    f.write_text("\n".join(head + rows) + "\n", encoding="utf-8")


CURSOR_JS = """addEventListener('DOMContentLoaded',()=>{const d=document.createElement('div');
d.style.cssText='position:fixed;z-index:2147483647;width:18px;height:18px;border-radius:50%;background:rgba(255,80,80,.75);border:2px solid #fff;pointer-events:none;left:-40px;top:-40px;transform:translate(-50%,-50%)';
document.documentElement.appendChild(d);addEventListener('mousemove',e=>{d.style.left=e.clientX+'px';d.style.top=e.clientY+'px'},true)});"""


async def open_context(p, opts: dict, record_dir, bp: str = "laptop"):
    endpoint = os.environ.get("ANIM_CDP_URL")
    if endpoint:
        b = await p.chromium.connect_over_cdp(endpoint)
    else:
        try:
            b = await p.chromium.launch(channel="chrome")
        except Exception:
            try:
                b = await p.chromium.launch()
            except Exception:
                b = await p.chromium.launch(executable_path="/usr/bin/chromium")
    w, h = size(bp)
    kw = dict(viewport={"width": w, "height": h}, color_scheme=opts.get("scheme", "dark"),
              device_scale_factor=1 if record_dir else 2)
    if "auth" in opts:
        f = auth_path(opts["auth"])
        if not f.exists():
            await b.close()
            raise RuntimeError(f"no saved login '{opts['auth']}'. Run: python anim.py login {opts['auth']} <url>")
        kw["storage_state"] = str(f)
    if record_dir:
        kw["record_video_dir"] = str(record_dir)
        kw["record_video_size"] = {"width": w, "height": h}
    ctx = await b.new_context(**kw)
    ctx.set_default_timeout(15000)
    await ctx.add_init_script(CURSOR_JS)
    if "mask" in opts:
        await ctx.add_init_script(mask_script(opts["mask"]))
    return b, ctx


async def _glide(page, sel):  # move the visible cursor to the element first, so a recording shows where the click goes
    box = await page.locator(sel).first.bounding_box()
    if box:
        await page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=20)


async def _step(page, act, args, shots_dir, shot_suffix="", state=None):
    if act == "goto":
        await page.goto(args[0], wait_until="networkidle", timeout=60000)
    elif act in ("click", "hover"):
        await _glide(page, args[0])
        await (page.click if act == "click" else page.hover)(args[0])
    elif act == "type":
        await page.locator(args[0]).first.press_sequentially(args[1], delay=80)
    elif act == "press":
        await page.keyboard.press(args[0])
    elif act == "scroll":
        left = float(args[0])
        while abs(left) > 0:  # small wheel steps = smooth scroll on video
            d = max(-40.0, min(40.0, left))
            await page.mouse.wheel(0, d)
            await page.wait_for_timeout(16)
            left -= d
    elif act == "wait":
        await page.wait_for_timeout(int(float(args[0]) * 1000))
    elif act == "wait_for":
        await page.wait_for_selector(args[0])
    elif act == "shot":
        await page.wait_for_timeout(600)
        crop = (state or {}).get("crop")
        await page.screenshot(path=str(shots_dir / f"{args[0]}{shot_suffix}.png"), **({"clip": crop} if crop else {}))
    elif act == "crop":  # from here on, the recording and shots keep only this element's box
        box = await page.locator(args[0]).first.bounding_box()
        if not box:
            raise RuntimeError(f"crop: '{args[0]}' is not visible")
        vp = page.viewport_size
        state["crop"] = clamp_box({k: round(box[k]) for k in ("x", "y", "width", "height")}, vp["width"], vp["height"])


async def run(opts: dict, steps: list, shots_dir: Path, record_dir=None, bp: str = "laptop", shot_suffix: str = "") -> dict:
    """Play the steps; returns the run state ({"crop": box} once a crop step ran)."""
    from playwright.async_api import async_playwright
    shots_dir.mkdir(parents=True, exist_ok=True)
    state = {}
    async with async_playwright() as p:
        b, ctx = await open_context(p, opts, record_dir, bp)
        try:
            pg = await ctx.new_page()
            if "url" in opts:
                await pg.goto(opts["url"], wait_until="networkidle", timeout=60000)
                await pg.wait_for_timeout(2500)  # fonts and animations settle
            if "expect" in opts:
                try:
                    await expect_locator(pg, opts["expect"]).first.wait_for(timeout=10000)
                except Exception:
                    raise RuntimeError(f"expected text '{opts['expect']}' not on the page: session expired? Run: python anim.py login") from None
            for i, (act, args) in enumerate(steps, 1):
                try:
                    await _step(pg, act, args, shots_dir, shot_suffix, state)
                except Exception as e:
                    raise RuntimeError(f"step {i} ({act} {' '.join(args)}) failed: {str(e).splitlines()[0]}") from None
        finally:
            await ctx.close()  # finalizes the video file
            await b.close()
    return state
