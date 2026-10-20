"""check.py - sensors for a scene: counters that must read zero before a render ships (_shared/review.md).

Text boxes come from _runtime/textcheck.js (idea: cth9191/animate tools/textcheck.mjs, MIT, licenses/animate-LICENSE.txt).
Reading floor and the counter block: re-expressed from public motion-design notes (no code copied).
"""
import json
import re

import numpy as np

QUALITY_KEYS = ("sound design missing", "too few beats")  # quality bar, see quality_counters
SFX_KEYS = ("sound effect unknown", "sound effect unlicensed")  # every brand, see sfx_counters
FAIL_KEYS = ("page errors", "cue warnings", "clock use", "nondeterministic frames",
             "text cut off", "text overlaps", "text too short to read", "invented labels") + QUALITY_KEYS + SFX_KEYS + (
             "brand missing", "brand font unlicensed", "brand contrast", "brand grads")
BRAND_KEYS = FAIL_KEYS[-4:]
HF_FAIL_KEYS = ("lint errors", "video vs voice length", "no visual layer", "composition errors", "invented labels") + QUALITY_KEYS + SFX_KEYS + BRAND_KEYS  # hyperframes videos (anim.py hf_check)
_VISUAL = re.compile(r'<(?:img|video|svg|canvas)\b|<script[^>]+src=["\']blocks/(?!core\.js)[^"\']+\.js["\']', re.I)  # core.js is text helpers only
_CLOCK = re.compile(r"\b(Math\.random|Date\.now|performance\.now|setTimeout|setInterval|new Date)\b")
_NUM = re.compile(r"^[\s\d.,%$€+\-:/x×]+$")
# Invented labels (_shared/plan-check.md S2): production metadata a viewer does not need. Whole strings only, so real copy
# such as "Step 1 of 3", "€49", "9:00–17:00" or "24/7" passes. Re-expressed from motionmaxxing scripts/lint.mjs C3/C4 (Apache-2.0).
_LABELS = (  # zero-padded numbers only: scores (10 / 10), dates (05/10), countdowns (03) and "CHAPTER 3" stay real copy
    ("counter", re.compile(r"0\d\s+/\s+\d{2}")),                                          # 02 / 05
    ("counter", re.compile(r"0\d\s*[—–]\s*[A-Z][A-Z ]+|0\d\s+-\s+[A-Z][A-Z ]+")),            # 01 — THE WAIT
    ("counter", re.compile(r"(?:FILM|SCENE|CHAPTER|ACT|SHOT|PART)\s+0\d")),       # FILM 01 (caps only)
    ("metadata", re.compile(r"00:\d{2}:\d{2}(?::\d{2})?|\d{1,2}:\d{2}:\d{2}:\d{2}")),          # timecode, not a clock
    ("metadata", re.compile(r"(?i)\d+(?:\.\d+)?\s?(?:bpm|fps)|frame\s+\d+|t\+\d.*|v\d+(?:\.\d+)+|(?:●\s*)?rec(?:\s*●)?")),
    ("metadata", re.compile(r"\d{3,4}\s?[x×]\s?\d{3,4}")),                                 # 1920x1080
)


def invented_labels(strings):
    """[(string, rule)] for every unique on-screen string that is a chapter counter or production metadata."""
    out, seen = [], set()
    for raw in strings:
        s = raw.strip()
        if s in seen:
            continue
        seen.add(s)
        rule = next((name for name, rx in _LABELS if rx.fullmatch(s)), None)
        if rule:
            out.append((s, rule))
    return out


def no_visual_layer(html: str) -> int:
    """1 when a HyperFrames scene is text only: no library block, image, video, svg or canvas (_shared/motion.md)."""
    return 0 if _VISUAL.search(html) else 1


# Quality bar (_shared/sound.md, _shared/motion.md):
# a hook by 2 s, a new beat every 3 to 5 s, sound effects, a ducked music bed and a sound file with licences.
QUALITY_BRANDS = {"videofactory"}
HOOK_S, BEAT_MAX_S, END_HOLD_S = 2.0, 5.0, 6.0  # first cue by, longest gap between cues, longest final hold (CTA card)
_LICENCE = re.compile(r"licen[cst]|licentie", re.I)


def quality_counters(meta, cue_list, sound_md):
    """({"sound design missing": n, "too few beats": n}, details) from cues.json meta and cueList plus the text of
    04_scene/assets/sound.md (None when the file is missing). Cue starts stand in for visual beats; the MP4 itself is
    checked for still stretches after render (dead stretches)."""
    miss = []
    if not meta.get("music"):
        miss.append("sound design: no music bed (a music: line before the first cue in cues.md)")
    if not any(c.get("sfx") for c in cue_list):
        miss.append("sound design: no sound effects ([sfx: ...] on cuts, snaps and reveals)")
    if sound_md is None:
        miss.append("sound design: no 04_scene/assets/sound.md (sound plan, music and effect sources and licences)")
    elif not _LICENCE.search(sound_md):
        miss.append("sound design: 04_scene/assets/sound.md names no licence")
    starts = sorted(float(c["start"]) for c in cue_list)
    dur = float(meta.get("duration") or (starts[-1] if starts else 0.0))
    gaps = []
    if not starts or starts[0] > HOOK_S:
        gaps.append(f"beats: no cue in the first {HOOK_S:g} s (hook)")
    for a, b in zip(starts, starts[1:]):
        if b - a > BEAT_MAX_S:
            gaps.append(f"beats: {a:.1f}-{b:.1f} s has no new cue (at most {BEAT_MAX_S:g} s)")
    if starts and dur - starts[-1] > END_HOLD_S:
        gaps.append(f"beats: last cue at {starts[-1]:.1f} s, video ends at {dur:.1f} s (final hold at most {END_HOLD_S:g} s)")
    return {"sound design missing": len(miss), "too few beats": len(gaps)}, miss + gaps


# File effects ([sfx: file:<name>]) are third-party audio: one line in 04_scene/assets/sound.md names the file,
# its source (a URL, or "source:"/"bron:") and its licence (_shared/sound.md). Built-in names are own synthesis.
_SFX_LICENCE = re.compile(r"licen[cst]|licentie|\bCC0\b|\bCC[ -]?BY\b|public domain|publiek domein", re.I)
_SFX_SOURCE = re.compile(r"https?://|\bsource\b|\bbron\b", re.I)


def sfx_counters(cue_list, sound_md, find_file, parse):
    """({"sound effect unknown": n, "sound effect unlicensed": n}, details) for every [sfx: ...] token in cueList.
    parse(token) -> (kind, name, gain) or ValueError (synth.parse_sfx); find_file(name) -> path or None.
    Unknown: a malformed token, an unknown built-in name or a missing file. Unlicensed: a file effect without a
    sound.md line that names the file with a source and a licence. Each distinct token counts once."""
    unknown, unlicensed, seen = [], [], set()
    lines = (sound_md or "").splitlines()
    for c in cue_list:
        for token in c.get("sfx") or []:
            if token in seen:
                continue
            seen.add(token)
            try:
                kind, name, _ = parse(token)
            except ValueError as e:
                unknown.append(f"sound effect: cue {c.get('id')}: {e}")
                continue
            if kind != "file":
                continue
            if find_file(name) is None:
                unknown.append(f"sound effect: cue {c.get('id')}: file '{name}' not found in 04_scene/assets/ or library/sfx/")
            base = name.rsplit("/", 1)[-1]
            if not any(base in ln and _SFX_LICENCE.search(ln) and _SFX_SOURCE.search(ln) for ln in lines):
                unlicensed.append(f"sound effect: '{name}' needs one line in 04_scene/assets/sound.md with the file name, "
                                  "its source URL and its licence")
    return {"sound effect unknown": len(unknown), "sound effect unlicensed": len(unlicensed)}, unknown + unlicensed


# HyperFrames sub-compositions: index.html mounts compositions/*.html with data-composition-src (paths relative to
# 04_scene, the HyperFrames project root). Text, visual layers and audio tags in those files count like the root's.
_COMP_SRC = re.compile(r"""\bdata-composition-src\s*=\s*(["'])(.*?)\1""", re.I | re.S)


def scene_documents(scene_dir, root_name="index.html"):
    """([(relative name, html text)], problems): the root document first, then every composition it references,
    depth first, recursively. Each file is read once (a composition mounted twice is one file); a reference back
    into the current chain is a cycle; a missing file or a path outside scene_dir is a problem, not a crash."""
    from pathlib import Path
    scene_dir = Path(scene_dir)
    base = scene_dir.resolve()
    docs, problems, done = [], [], set()

    def visit(rel, chain):
        path = (scene_dir / rel).resolve()
        if path in chain:
            problems.append("composition cycle: " + " -> ".join([*(c.relative_to(base).as_posix() for c in chain), rel]))
            return
        if path in done:
            return
        if not path.is_relative_to(base):
            problems.append(f"composition outside 04_scene: {rel} (in {chain[-1].relative_to(base).as_posix()})")
            return
        if not path.is_file():
            where = f" (in {chain[-1].relative_to(base).as_posix()})" if chain else ""
            problems.append(f"composition not found: {rel}{where}")
            return
        done.add(path)
        text = path.read_text(encoding="utf-8")
        docs.append((path.relative_to(base).as_posix(), text))
        for m in _COMP_SRC.finditer(re.sub(r"<!--.*?-->", "", text, flags=re.S)):
            src = m.group(2).strip()
            if src and not re.match(r"[a-z][\w+.-]*:", src, re.I):  # skip http:, data: ...
                visit(src.split("#")[0].split("?")[0].removeprefix("./"), chain + [path])
    visit(root_name, [])
    return docs, problems


def _area(b):
    return max(0.0, b["x1"] - b["x0"]) * max(0.0, b["y1"] - b["y0"])


def overlaps(boxes, frac=0.15):
    """Pairs of different strings whose boxes share more than `frac` of the smaller box."""
    out, seen = [], set()
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            if a["s"] in b["s"] or b["s"] in a["s"]:  # same label twice, or a lit word over its own line
                continue
            w = min(a["x1"], b["x1"]) - max(a["x0"], b["x0"])
            h = min(a["y1"], b["y1"]) - max(a["y0"], b["y0"])
            if w > 0 and h > 0 and w * h > frac * min(_area(a), _area(b)):
                key = tuple(sorted((a["s"], b["s"])))
                if key not in seen:
                    seen.add(key)
                    out.append(key)
    return out


def cut_off(b, w, h, tol=2):
    """Partly inside the frame and partly outside it. Text that is fully outside is parked, not cut."""
    inside = b["x1"] > 0 and b["y1"] > 0 and b["x0"] < w and b["y0"] < h
    whole = b["x0"] >= -tol and b["y0"] >= -tol and b["x1"] <= w + tol and b["y1"] <= h + tol
    return inside and not whole


def read_floor(s):
    """Seconds a string must stay on screen to be read: max(0.7, 0.25 + chars / 17)."""
    return max(0.7, 0.25 + len(s.strip()) / 17)


def too_short(samples, dt, end):
    """samples: [(t, [strings visible at t])]. Strings shown for less than read_floor. Skips numbers, strings that
    grow into a longer one or shrink from one (typing, deleting), single glyphs (scramble and decode effects),
    and strings still on screen at the end.
    Sampling can miss up to one step of screen time, so one step is given back."""
    spans, open_ = [], {}
    for t, strs in samples + [(end + dt, [])]:
        now = set(strs)
        for s in list(open_):
            if s not in now:
                spans.append((s, open_.pop(s), t))
        for s in now:
            open_.setdefault(s, t)
    later = [(t, s) for t, strs in samples for s in strs]
    out = []
    for s, t0, t1 in spans:
        if t1 > end or _NUM.match(s) or len(s.strip()) < 2:
            continue
        if any(o != s and o.startswith(s) and t0 - 0.5 <= tt <= t1 + 0.5 for tt, o in later):
            continue
        if t1 - t0 + dt < read_floor(s):
            out.append((s, t0, t1 - t0))
    return out


def lasting(seen, dt, min_s=0.5):
    """seen: {pair: [sample times]}. Pairs that overlap for min_s or more without a break. Shorter overlaps are
    cross-fades between two shots: reported as info, not counted."""
    out = []
    for pair, ts in seen.items():
        run = best = 1
        for a, b in zip(ts, ts[1:]):
            run = run + 1 if b - a <= dt * 1.5 else 1
            best = max(best, run)
        if best * dt >= min_s - 1e-9:
            out.append(pair)
    return out


def clock_use(js):
    """Wall-clock or random calls in scene code: they make frames differ between runs."""
    code = re.sub(r"//[^\n]*|/\*.*?\*/", "", js, flags=re.S)
    return [m.group(1) for m in _CLOCK.finditer(code)]


_GENERIC_FONTS = {"system-ui", "sans-serif", "serif", "monospace"}


def _lum(hex_):
    c = [int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b):
    """WCAG contrast ratio of two #RRGGBB colours."""
    hi, lo = sorted((_lum(a), _lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def brand_counters(root, brand):
    """Counters for brands/<brand>/tokens.js (flat file, see brands/videofactory/tokens.js): file exists, fonts have a
    licence record and a local @font-face, ramp[0] on ramp[6] reads at 4.5 or better, grads has 5 pairs."""
    out = {k: 0 for k in BRAND_KEYS}
    tokens = root / "brands" / brand / "tokens.js"
    if not tokens.is_file():
        out["brand missing"] = 1
        return out
    js = tokens.read_text(encoding="utf-8")
    sources = json.loads((root / "FONT-SOURCES.json").read_text(encoding="utf-8"))
    dirs = {p["path"].split("/")[2] for p in sources if p["path"].startswith("_runtime/fonts/")}
    css = (root / "_runtime" / "fonts" / "fonts.css").read_text(encoding="utf-8")
    faces = {m.group(1) for m in re.finditer(r"font-family:\s*['\"]([^'\"]+)['\"]", css)}
    for key in ("font", "head"):
        m = re.search(rf"\b{key}:\s*'([^']*)'", js)
        first = re.search(r'"([^"]+)"', m.group(1)) if m else None
        fam = first.group(1) if first else None
        if fam is None and m:  # no quoted family: only a generic name is fine
            fam = next((n for n in (x.strip() for x in m.group(1).split(",")) if n not in _GENERIC_FONTS), None)
        if m is None or (fam and (fam.replace(" ", "").lower() not in dirs or fam not in faces)):
            out["brand font unlicensed"] += 1
    ramp = re.search(r"\bramp:\s*\[([^\]]*)\]", js)
    colours = re.findall(r"#[0-9A-Fa-f]{6}\b", ramp.group(1)) if ramp else []
    if len(colours) != 8 or contrast(colours[0], colours[6]) < 4.5:
        out["brand contrast"] = 1
    grads = re.search(r"\bgrads:\s*\[(.*)\]\s*,?\s*\n?\s*\}", js, re.S)
    pairs = re.findall(r"\[\s*'#[0-9A-Fa-f]{6}'\s*,\s*'#[0-9A-Fa-f]{6}'\s*\]", grads.group(1)) if grads else []
    if len(pairs) != 5:
        out["brand grads"] = 1
    return out


def report(counters, info):
    rows = [(k, counters.get(k, 0)) for k in FAIL_KEYS] + sorted(info.items())
    wid = max(len(k) for k, _ in rows)
    return "\n".join(f"{k:<{wid}}  {v}" for k, v in rows)


# ── after render: the MP4 itself ────────────────────────────────────────────

def flashes(g, thr=8.0):
    """One-frame glitches: frame n differs from both neighbours while n-1 and n+1 look alike. A cut is not a flash.
    g: (frames, h, w) uint8 grey. Idea: howseen-ai/claude-motion-design render_template.py (MIT)."""
    f = g.astype(np.int16)

    def d(a, b):
        return np.abs(f[a] - f[b]).mean()
    return [n for n in range(1, len(f) - 1) if d(n, n - 1) > thr and d(n + 1, n) > thr and d(n + 1, n - 1) < thr / 3]


def dead(g, fps, thr=0.3, min_s=3.0):
    """Stretches of at least min_s seconds where the picture barely changes (they stop the render unless the project allows it)."""
    diff = np.abs(np.diff(g.astype(np.int16), axis=0)).mean(axis=(1, 2))
    out, k0 = [], None
    for k, v in enumerate(list(diff) + [thr + 1]):
        if v < thr and k0 is None:
            k0 = k
        elif v >= thr and k0 is not None:
            if (k - k0) / fps >= min_s:
                out.append((k0 / fps, (k + 1) / fps))
            k0 = None
    return out


def flat_runs(g, fps, max_ok=3, std=1.5, rng=8):
    """(start s, end s) of every run of more than max_ok frames that are one flat field (black, cream, any solid colour):
    luma std under std and max - min under rng. Idea: motionmaxxing scripts/look.py gate G2 (Apache-2.0)."""
    f = g.reshape(len(g), -1)
    flat = list((f.std(axis=1) < std) & (np.ptp(f, axis=1) < rng)) + [False]
    out, k0 = [], None
    for k, v in enumerate(flat):
        if v and k0 is None:
            k0 = k
        elif not v and k0 is not None:
            if k - k0 > max_ok:
                out.append((k0 / fps, k / fps))
            k0 = None
    return out


def ebur128(stderr):
    """(integrated loudness LUFS, true peak dBTP) from ffmpeg's ebur128=peak=true summary."""
    i = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", stderr)[-1])
    p = re.findall(r"Peak:\s+(-?[\d.]+|-inf) dBFS", stderr)[-1]
    return i, float(p)


def subtimes(t, n, fps, cuts, shutter=0.5):
    """n sample times for one motion-blurred frame: a 180-degree shutter (half the frame time), centred on t,
    kept on t's side of every cut. Idea: howseen-ai/claude-motion-design render_template.py (MIT)."""
    if n <= 1:
        return [t]
    out = [t + ((k + 0.5) / n - 0.5) * shutter / fps for k in range(n)]
    for c in cuts:
        out = [max(x, c) if t >= c else min(x, c - 1e-4) for x in out]
    return out
