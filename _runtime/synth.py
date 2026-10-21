"""Built-in sound generator: 15 soft sound effects and two calm music beds, made with numpy only.

This is the free fallback. If the brand has sound files (`brands/<id>/sound/`), those win over this module
(see `_shared/sound.md`). The sounds are soft and modern: sine and triangle tones, FM bells, filtered noise,
gentle envelopes and light pitch sweeps. There are no square waves and no bit-crushing. Everything is
deterministic: the same call always returns the same samples.

Public names: SR, SFX, SONGS, END_ALIGNED, FILE_PEAK, render_sfx, render_song, parse_sfx, soundtrack, write_wav.
"""
import re
import wave
from pathlib import Path

import numpy as np

SR = 44100
FILE_PEAK = 0.5
END_ALIGNED = {"riser"}

_EXTS = ("wav", "mp3", "ogg", "oga", "flac", "m4a", "aif", "aiff")


# --------------------------------------------------------------------------------------------------
# Small building blocks
# --------------------------------------------------------------------------------------------------

def _t(n):
    return np.arange(n) / SR


def _midi(m):
    return 440.0 * 2.0 ** ((np.asarray(m, dtype=float) - 69.0) / 12.0)


def _phase(freq, n):
    f = np.broadcast_to(np.asarray(freq, dtype=float), (n,))
    return 2.0 * np.pi * np.cumsum(f) / SR


def _sine(freq, n):
    return np.sin(_phase(freq, n))


def _tri(freq, n):
    return (2.0 / np.pi) * np.arcsin(np.sin(_phase(freq, n)))


def _env(n, attack=0.002, tau=0.05):
    """Soft attack (sine squared), then an exponential decay."""
    t = _t(n)
    a = np.sin(0.5 * np.pi * np.minimum(t / attack, 1.0)) ** 2
    return a * np.exp(-t / tau)


def _swell(n, attack, release):
    """Smooth rise over `attack` seconds, hold, smooth fall over the last `release` seconds."""
    x = np.ones(n)
    a, r = min(int(attack * SR), n), min(int(release * SR), n)
    if a:
        x[:a] *= np.sin(0.5 * np.pi * np.arange(a) / a) ** 2
    if r:
        x[n - r:] *= np.cos(0.5 * np.pi * np.arange(r) / r) ** 2
    return x


def _noise(n, seed):
    return np.random.default_rng(seed).standard_normal(n)


def _gain_filter(x, gain):
    """Zero-phase filter in the frequency domain. `gain(f)` gives the smooth gain per frequency."""
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    return np.fft.irfft(spec * gain(f), len(x))


def _band(x, lo=None, hi=None, order=2):
    """Low-pass at `hi` and high-pass at `lo` (either can be None). Gentle Butterworth-shaped slopes."""
    def gain(f):
        g = np.ones_like(f)
        if hi:
            g = g / np.sqrt(1.0 + (f / hi) ** (2 * order))
        if lo:
            g = g / np.sqrt(1.0 + (lo / np.maximum(f, 1e-9)) ** (2 * order))
        return g
    return _gain_filter(x, gain)


def _sweep_noise(n, f0, f1, seed, width=0.8, bands=14):
    """Noise whose pitch centre moves from f0 to f1 (exponentially) over the clip."""
    spec = np.fft.rfft(_noise(n, seed))
    f = np.fft.rfftfreq(n, 1.0 / SR)
    logf = np.log2(np.maximum(f, 20.0))
    pos = np.linspace(0.0, 1.0, n)
    out, norm = np.zeros(n), np.zeros(n)
    sigma = 1.0 / (bands - 1)
    for k, centre in enumerate(np.geomspace(f0, f1, bands)):
        band = np.fft.irfft(spec * np.exp(-0.5 * ((logf - np.log2(centre)) / width) ** 2), n)
        w = np.exp(-0.5 * ((pos - k / (bands - 1)) / sigma) ** 2)
        out += band * w
        norm += w
    return out / np.maximum(norm, 1e-9)


def _bell(freq, n, ratio=2.0, index=1.5, tau=0.25, itau=0.06, attack=0.002):
    """Soft FM bell: the brightness (index) dies away faster than the loudness."""
    t = _t(n)
    f = np.broadcast_to(np.asarray(freq, dtype=float), (n,))
    ph = 2.0 * np.pi * np.cumsum(f) / SR
    return _env(n, attack, tau) * np.sin(ph + index * np.exp(-t / itau) * np.sin(ratio * ph))


def _place(total, parts):
    """Sum signals on a silent stream. parts = [(start_seconds, signal), ...]."""
    out = np.zeros(total)
    for start, sig in parts:
        i = int(round(start * SR))
        k = min(len(sig), total - i)
        if k > 0:
            out[i:i + k] += sig[:k]
    return out


def _fit(x, peak, head=0.0005, tail=0.004):
    """Round the first and last samples and scale to an exact peak."""
    x = np.array(x, dtype=float)
    h, t = min(int(head * SR), len(x) // 4), min(int(tail * SR), len(x) // 4)
    if h:
        x[:h] *= np.sin(0.5 * np.pi * np.arange(h) / h) ** 2
    if t:
        x[-t:] *= np.cos(0.5 * np.pi * np.arange(t) / t) ** 2
    m = float(np.max(np.abs(x)))
    return x * (peak / m) if m > 0 else x


# --------------------------------------------------------------------------------------------------
# Sound effects
# --------------------------------------------------------------------------------------------------

def _blip():
    """A single soft sine note that glides up a little. A choice is made."""
    n = int(0.11 * SR)
    f = 880.0 * (1.0 + 0.18 * (1.0 - np.exp(-_t(n) / 0.02)))
    x = _sine(f, n) * _env(n, 0.003, 0.035) + 0.2 * _sine(2 * f, n) * _env(n, 0.003, 0.018)
    return _fit(x, 0.35)


def _tick():
    """A very short, dry, high tick."""
    n = int(0.02 * SR)
    x = _sine(2200.0, n) * _env(n, 0.0004, 0.004)
    x += 0.5 * _band(_noise(n, 11), 2000, 6000) * _env(n, 0.0003, 0.002) * 0.35
    return _fit(x, 0.25, tail=0.003)


def _select():
    """Two soft notes, a fifth apart, going up. A tab changes."""
    n = int(0.15 * SR)
    a, b = int(0.07 * SR), int(0.08 * SR)
    x = _place(n, [(0.0, _tri(659.25, a) * _env(a, 0.003, 0.03)),
                   (0.06, _tri(987.77, b) * _env(b, 0.003, 0.04))])
    return _fit(_band(x, None, 4500), 0.35)


def _coin():
    """A quick two-note glassy bell, ba-ding."""
    n = int(0.5 * SR)
    a, b = int(0.2 * SR), int(0.44 * SR)
    x = _place(n, [(0.0, 0.7 * _bell(1318.5, a, 2.0, 0.8, 0.07, 0.03)),
                   (0.07, _bell(1975.5, b, 2.0, 0.9, 0.16, 0.05))])
    return _fit(_band(x, None, 6500), 0.4, tail=0.02)


def _stamp():
    """A soft low thud with a small paper tap. Something is confirmed."""
    n = int(0.16 * SR)
    t = _t(n)
    body = _sine(70.0 + 110.0 * np.exp(-t / 0.018), n) * _env(n, 0.002, 0.05)
    tap = _band(_noise(n, 21), None, 1100) * _env(n, 0.001, 0.012)
    return _fit(body + 0.45 * tap / max(float(np.max(np.abs(tap))), 1e-9), 0.7, tail=0.02)


def _whoosh():
    """Filtered noise that sweeps up and fades, shaped like a gentle wave."""
    n = int(0.4 * SR)
    x = _sweep_noise(n, 350.0, 3000.0, 31) * np.sin(np.pi * np.arange(n) / n) ** 2
    return _fit(x, 0.4, head=0.01, tail=0.01)


def _pop():
    """A soft bubble: a sine that rises fast and fades."""
    n = int(0.1 * SR)
    f = 300.0 + 700.0 * (1.0 - np.exp(-_t(n) / 0.014))
    return _fit(_sine(f, n) * _env(n, 0.002, 0.025), 0.45, tail=0.01)


def _powerup():
    """A rising run of five soft bell notes."""
    n = int(0.62 * SR)
    notes = (523.25, 659.25, 783.99, 1046.5, 1318.5)
    parts = []
    for k, f in enumerate(notes):
        last = k == len(notes) - 1
        m = int((0.34 if last else 0.16) * SR)
        parts.append((0.07 * k, _bell(f, m, 2.0, 0.9, 0.2 if last else 0.07, 0.04) * (1.0 if last else 0.8)))
    return _fit(_place(n, parts), 0.4, tail=0.03)


def _error():
    """Two low, mellow triangle notes going down. A mistake on screen."""
    n = int(0.42 * SR)
    m = int(0.2 * SR)
    x = _place(n, [(0.0, _tri(311.13, m) * _env(m, 0.01, 0.1)),
                   (0.17, _tri(233.08, int(0.25 * SR)) * _env(int(0.25 * SR), 0.01, 0.11))])
    return _fit(_band(x, None, 1600), 0.4, head=0.002, tail=0.03)


def _chime():
    """One long, bright-but-soft bell with a fifth above it."""
    n = int(0.65 * SR)
    x = _bell(880.0, n, 3.5, 1.0, 0.28, 0.07) + 0.6 * _bell(1320.0, n, 3.5, 0.8, 0.2, 0.05)
    return _fit(_band(x, None, 6500), 0.4, tail=0.05)


def _step():
    """A soft, low, padded tap."""
    n = int(0.028 * SR)
    t = _t(n)
    x = _sine(500.0 + 220.0 * np.exp(-t / 0.006), n) * _env(n, 0.001, 0.008)
    x += 0.3 * _band(_noise(n, 41), None, 1400) * _env(n, 0.001, 0.005)
    return _fit(x, 0.25, tail=0.006)


def _riser():
    """A swelling mix of rising noise and a gliding tone. It is loudest at its end."""
    n = int(1.2 * SR)
    pos = np.arange(n) / n
    grow = pos ** 2.2
    tone = (_sine(180.0 * 4.0 ** pos, n) + 0.4 * _sine(270.0 * 4.0 ** pos, n)) * 0.6
    x = (0.6 * _sweep_noise(n, 300.0, 3600.0, 51, width=0.9) + tone) * grow
    return _fit(x, 0.45, head=0.03, tail=0.006)


def _impact():
    """A deep, soft boom with a short low noise thump and a long sub tail."""
    n = int(0.9 * SR)
    t = _t(n)
    body = _sine(42.0 + 70.0 * np.exp(-t / 0.07), n) * _env(n, 0.003, 0.28)
    body += 0.25 * _sine(2 * (42.0 + 70.0 * np.exp(-t / 0.07)), n) * _env(n, 0.003, 0.1)
    thump = _band(_noise(n, 61), None, 260) * _env(n, 0.002, 0.06)
    sub = _sine(55.0, n) * _env(n, 0.01, 0.5) * 0.35
    x = body + 0.5 * thump / max(float(np.max(np.abs(thump))), 1e-9) + sub
    x *= _swell(n, 0.0, 0.18)
    return _fit(x, 0.8)


def _click():
    """A soft button press: a press tap and a smaller release tap."""
    n = int(0.028 * SR)
    m = int(0.012 * SR)
    t = _t(m)
    press = _sine(1500.0 - 600.0 * np.minimum(t / 0.008, 1.0), m) * _env(m, 0.0004, 0.004)
    press += 0.35 * _band(_noise(m, 71), 1500, 5000) * _env(m, 0.0003, 0.0025)
    rel = _sine(2100.0, m) * _env(m, 0.0004, 0.003) * 0.35
    return _fit(_place(n, [(0.0, press), (0.014, rel)]), 0.3, tail=0.004)


def _key():
    """A soft low key press, a small thock."""
    n = int(0.02 * SR)
    t = _t(n)
    x = _sine(170.0 + 110.0 * np.exp(-t / 0.005), n) * _env(n, 0.0006, 0.006)
    x += 0.35 * _band(_noise(n, 81), None, 2600) * _env(n, 0.0005, 0.003)
    return _fit(x, 0.28, tail=0.004)


SFX = {
    "blip": _blip, "tick": _tick, "select": _select, "coin": _coin, "stamp": _stamp,
    "whoosh": _whoosh, "pop": _pop, "powerup": _powerup, "error": _error, "chime": _chime,
    "step": _step, "riser": _riser, "impact": _impact, "click": _click, "key": _key,
}

_SFX_CACHE = {}


def render_sfx(name):
    """The effect `name` as a mono float64 array at 44100 Hz. KeyError for an unknown name."""
    if name not in _SFX_CACHE:
        _SFX_CACHE[name] = np.clip(np.asarray(SFX[name](), dtype=float), -1.0, 1.0)
    return _SFX_CACHE[name].copy()


# --------------------------------------------------------------------------------------------------
# Music beds
# --------------------------------------------------------------------------------------------------

def _smooth_len(n):
    """The smallest length >= n made of small prime factors (fast FFT). Loops get this length."""
    while True:
        m = n
        for p in (2, 3, 5, 7):
            while m % p == 0:
                m //= p
        if m == 1:
            return n
        n += 1


def _put(buf, start, sig):
    """Add `sig` into the circular buffer `buf` at `start`; the end wraps around to the start."""
    size, start, i = len(buf), start % len(buf), 0
    while i < len(sig):
        k = min(len(sig) - i, size - start)
        buf[start:start + k] += sig[i:i + k]
        i += k
        start = 0


def _warp(beat, swing):
    """Push off-beat eighth notes a little late (swing 0 = straight)."""
    whole = np.floor(beat + 1e-9)
    r = beat - whole
    r = r * (1.0 + swing) if r < 0.5 - 1e-9 else 0.5 * (1.0 + swing) + (r - 0.5) * (1.0 - swing)
    return whole + r


def _reverb_spec(seconds, seed, size):
    """Spectrum of a reverb tail for a loop of `size` samples. Multiplying by it is a circular
    convolution: the tail wraps around, so a loop stays seamless."""
    m = int(seconds * SR)
    ir = _band(_noise(m, seed), 200, 5000) * np.exp(-_t(m) / (seconds / 4.5))
    ramp = int(0.012 * SR)
    ir[:ramp] *= np.linspace(0.0, 1.0, ramp)
    ir /= np.sqrt(np.sum(ir ** 2))
    return np.fft.rfft(ir, size)


def _echo_spec(f, size, delay, feedback, taps=4, tone=3000):
    """Transfer of a soft echo (dark repeats, circular delay) as the sum of `taps` repeats plus the dry sound."""
    z = feedback * np.exp(-2j * np.pi * f * int(delay * SR) / SR) / np.sqrt(1.0 + (f / tone) ** 2)
    return sum(z ** k for k in range(taps + 1))


def _pad_chord(midis, n, seed):
    """A warm, slow pad: each note is two slightly detuned sines with a quiet octave and a slow wobble.
    The pad is dark and smooth, so it is made at a quarter of the sample rate and then upsampled."""
    q = 4
    m = _smooth_len(-(-n // q) + 1)
    rate = SR / q
    t = np.arange(m) / rate
    out = np.zeros(m)
    for k, midi in enumerate(midis):
        for j, cents in enumerate((-5.0, 5.0)):
            wobble = 1.0 + 0.0014 * np.sin(2 * np.pi * 0.17 * t + seed + 0.7 * k + 2.1 * j)
            ph = 2 * np.pi * np.cumsum(_midi(midi) * 2.0 ** (cents / 1200.0) * wobble) / rate
            out += 0.5 * (np.sin(ph) + 0.28 * np.sin(2 * ph))
    return (np.fft.irfft(np.fft.rfft(out), m * q) * q)[:n]


def _bass_note(freq, n):
    ph = _phase(freq, n)
    return (np.sin(ph) + 0.22 * np.sin(2 * ph)) * _env(n, 0.008, 0.45) * _swell(n, 0.0, 0.04)


def _ep_note(freq, n):
    """Soft electric-piano tone: sine FM with brightness that fades quickly."""
    t = _t(n)
    ph = 2 * np.pi * freq * t
    x = np.sin(ph + 1.7 * np.exp(-t / 0.15) * np.sin(ph)) * _env(n, 0.004, 0.55)
    return x * _swell(n, 0.0, 0.08)


def _mallet_note(freq, n):
    """Soft marimba-like pluck."""
    t = _t(n)
    ph = 2 * np.pi * freq * t
    x = np.sin(ph) * np.exp(-t / 0.3) + 0.3 * np.sin(3.93 * ph) * np.exp(-t / 0.07) + 0.08 * np.sin(9.9 * ph) * np.exp(-t / 0.02)
    return x * _env(n, 0.002, 10.0) * _swell(n, 0.0, 0.05)


def _drum_hits(kind, seed):
    if kind == "hat":
        n = int(0.07 * SR)
        return _band(_noise(n, seed), 5500, None) * _env(n, 0.001, 0.013) * 0.25
    if kind == "brush":
        n = int(0.28 * SR)
        return _band(_noise(n, seed), 700, 6500) * _env(n, 0.014, 0.075) * 0.25
    n = int(0.3 * SR)
    t = _t(n)
    return _sine(48.0 + 75.0 * np.exp(-t / 0.03), n) * _env(n, 0.002, 0.11)


def _build_loop(d):
    beats = d["bars"] * 4
    size = _smooth_len(int(round(beats * 60.0 / d["bpm"] * SR)))
    spb = size / beats
    swing = d.get("swing", 0.0)

    def at(beat):
        return int(round(_warp(beat, swing) * spb))

    chord_beats = d["chord_bars"] * 4
    pad, bass, keys, drums = (np.zeros(size) for _ in range(4))
    tail = 1.6  # seconds a pad note rings after its chord

    for i, ch in enumerate(d["chords"]):
        start = i * chord_beats
        n = int(chord_beats * spb + tail * SR)
        _put(pad, int(round(start * spb)), _pad_chord(ch["pad"], n, i * 7) * _swell(n, 0.7, 1.5))
        for bar in range(d["chord_bars"]):
            for beat, length, step in d["bass"]:
                nb = int((length * spb) + 0.05 * SR)
                _put(bass, at(start + bar * 4 + beat), _bass_note(_midi(ch["bass"] + step), nb))
        for beat, m, length in ch["notes"]:
            nk = int(length * spb + 0.25 * SR)
            note = _mallet_note if d["voice"] == "mallet" else _ep_note
            _put(keys, at(start + beat), note(_midi(m), nk) * 0.9)
        for k, m in enumerate(ch.get("comp", ())):
            nk = int(chord_beats * 0.5 * spb)
            _put(keys, int(round(start * spb)) + int(0.035 * SR * k), _ep_note(_midi(m), nk) * 0.35)

    hats = [_drum_hits("hat", 90 + k) for k in range(4)]
    brushes = [_drum_hits("brush", 95 + k) for k in range(2)]
    kick = _drum_hits("kick", 0)
    for bar in range(d["bars"]):
        b0 = bar * 4
        for k, v in enumerate(d["hats"]):
            if v:
                _put(drums, at(b0 + k * 0.5), hats[(bar + k) % 4] * v * d["hat_level"])
        for beat in d["brush"]:
            _put(drums, at(b0 + beat), brushes[bar % 2] * d["brush_level"])
        for beat in d["kick"]:
            _put(drums, at(b0 + beat), kick * d["kick_level"])

    lv = d["levels"]
    f = np.fft.rfftfreq(size, 1.0 / SR)
    spec = np.fft.rfft(pad) * (1.0 + 0.5 * _reverb_spec(2.4, 7, size)) * lv["pad"]
    spec += (np.fft.rfft(keys) * _echo_spec(f, size, d["echo"] * 60.0 / d["bpm"], 0.4)
             * (1.0 + 0.35 * _reverb_spec(1.6, 9, size)) * lv["keys"])
    spec += np.fft.rfft(bass * lv["bass"] + drums * lv["drums"])
    spec *= (1.0 / np.sqrt(1.0 + (28.0 / np.maximum(f, 1e-9)) ** 4)) / np.sqrt(1.0 + (f / d["lowpass"]) ** 4)
    mix = np.fft.irfft(spec, size)
    mix *= 0.17 / np.sqrt(np.mean(mix ** 2))
    knee = 0.7  # soft limiter: leaves quiet parts alone and rounds the peaks, never reaches 1
    a = np.abs(mix)
    return np.where(a < knee, mix, np.sign(mix) * (knee + (1 - knee) * np.tanh((a - knee) / (1 - knee))))


SONGS = {
    "study": {
        "about": "calm lo-fi bed for explaining: A minor, soft pad, sine bass, brushed hats",
        "bpm": 84, "bars": 8, "chord_bars": 2, "swing": 0.14, "voice": "ep",
        "chords": [
            {"pad": (57, 60, 64, 67, 71), "bass": 45, "comp": (57, 64, 71),
             "notes": [(1.5, 76, 1.0), (3.0, 72, 1.5), (5.0, 74, 0.75), (6.5, 69, 1.5)]},
            {"pad": (53, 57, 60, 64, 67), "bass": 41, "comp": (53, 60, 67),
             "notes": [(0.5, 72, 1.0), (2.0, 76, 1.5), (4.5, 74, 0.75), (6.0, 72, 1.5)]},
            {"pad": (50, 53, 57, 60, 64), "bass": 38, "comp": (53, 60, 64),
             "notes": [(1.0, 69, 1.5), (3.0, 72, 0.75), (4.5, 74, 1.0), (6.0, 77, 1.5)]},
            {"pad": (52, 55, 59, 62, 64), "bass": 40, "comp": (55, 62, 71),
             "notes": [(1.0, 71, 1.5), (2.5, 67, 1.0), (4.0, 71, 1.5), (6.0, 76, 1.8)]},
        ],
        "bass": [(0.0, 1.6, 0), (2.5, 1.0, 7)],
        "hats": [1.0, 0.45, 0.7, 0.4, 0.9, 0.45, 0.7, 0.5], "hat_level": 0.30,
        "brush": [1.0, 3.0], "brush_level": 0.28,
        "kick": [0.0, 2.5], "kick_level": 0.30,
        "echo": 0.75, "lowpass": 5200,
        "levels": {"pad": 1.0, "keys": 0.9, "bass": 0.9, "drums": 0.9},
    },
    "tinker": {
        "about": "playful bed for history and demos: C major, bouncy bass, soft mallet riff",
        "bpm": 116, "bars": 8, "chord_bars": 2, "swing": 0.1, "voice": "mallet",
        "chords": [
            {"pad": (60, 64, 67, 71, 74), "bass": 36,
             "notes": [(0.5, 76, 0.5), (1.0, 79, 0.5), (1.5, 76, 0.5), (2.5, 74, 0.5), (3.0, 72, 1.0),
                       (4.5, 76, 0.5), (5.0, 79, 0.5), (5.5, 81, 0.5), (6.5, 79, 0.5), (7.0, 76, 0.8)]},
            {"pad": (57, 60, 64, 67, 71), "bass": 45,
             "notes": [(0.5, 72, 0.5), (1.0, 76, 0.5), (1.5, 81, 0.5), (2.5, 79, 0.5), (3.0, 76, 1.0),
                       (4.5, 72, 0.5), (5.0, 76, 0.5), (5.5, 79, 0.5), (6.5, 76, 0.5), (7.0, 72, 0.8)]},
            {"pad": (53, 57, 60, 64, 67), "bass": 41,
             "notes": [(0.5, 77, 0.5), (1.0, 81, 0.5), (1.5, 77, 0.5), (2.5, 76, 0.5), (3.0, 72, 1.0),
                       (4.5, 81, 0.5), (5.0, 77, 0.5), (5.5, 76, 0.5), (6.5, 72, 0.5), (7.0, 81, 0.8)]},
            {"pad": (55, 59, 62, 64, 69), "bass": 43,
             "notes": [(0.5, 74, 0.5), (1.0, 79, 0.5), (1.5, 83, 0.5), (2.5, 81, 0.5), (3.0, 79, 1.0),
                       (4.5, 74, 0.5), (5.0, 76, 0.5), (5.5, 79, 0.5), (6.5, 76, 0.5), (7.0, 79, 1.0)]},
        ],
        "bass": [(0.0, 0.75, 0), (1.5, 0.5, 12), (2.0, 0.75, 0), (3.0, 0.5, 7), (3.5, 0.5, 12)],
        "hats": [1.0, 0.5, 0.8, 0.5, 0.9, 0.5, 0.8, 0.6], "hat_level": 0.32,
        "brush": [1.0, 3.0], "brush_level": 0.3,
        "kick": [0.0, 1.5, 2.0], "kick_level": 0.3,
        "echo": 0.75, "lowpass": 7000,
        "levels": {"pad": 0.8, "keys": 1.0, "bass": 0.8, "drums": 0.9},
    },
}

_LOOP_CACHE = {}


def _loop(name):
    if name not in _LOOP_CACHE:
        _LOOP_CACHE[name] = _build_loop(SONGS[name])
    return _LOOP_CACHE[name]


def _song_samples(name, n, fade):
    loop = _loop(name)  # raises KeyError for an unknown name
    if n <= 0:
        return np.zeros(0)
    x = np.tile(loop, -(-n // len(loop)))[:n]
    head = min(int(0.05 * SR), n)
    x[:head] *= np.linspace(0.0, 1.0, head, endpoint=False)
    tail = min(int(fade * SR), n)
    if tail > 0:
        x[n - tail:] *= np.linspace(1.0, 0.0, tail)
    return np.clip(x, -1.0, 1.0)


def render_song(name, seconds, fade=2.5):
    """The song `name` as a mono float64 array of int(seconds * 44100) samples. It repeats without a seam.

    A 50 ms fade-in at the start and a linear fade-out over the last `fade` seconds. KeyError for an unknown name.
    """
    return _song_samples(name, int(seconds * SR), fade)


# --------------------------------------------------------------------------------------------------
# Effect tokens and the soundtrack
# --------------------------------------------------------------------------------------------------

_GAIN = r"(?:[ \t\n\r\f\v]+([0-9]+(?:\.[0-9]+)?|\.[0-9]+))?"
_BUILTIN = re.compile(r"([A-Za-z]+)" + _GAIN + r"\Z")
_PART = r"[A-Za-z0-9_.\-]+"
_FILE = re.compile(r"[Ff][Ii][Ll][Ee]:((?:" + _PART + r"/)*" + _PART + r"\.(?:" + "|".join(_EXTS) + r"))" + _GAIN + r"\Z",
                   re.IGNORECASE)


_OFFSET = re.compile(r"@([0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?=[ \t]|\Z)")


def sfx_offset(token) -> float:
    """Seconds after the cue start for `pop@0.4` (`@<seconds>` right after the name); 0 without one."""
    m = _OFFSET.search(str(token))
    return float(m.group(1)) if m else 0.0


def parse_sfx(token):
    """Parse one `[sfx: ...]` item into (kind, name, gain). ValueError for anything else.

    `pop`, `whoosh 0.5` -> ("builtin", name, gain); `file:sfx/door.wav .8` -> ("file", "sfx/door.wav", 0.8).
    An `@<seconds>` offset after the name (`pop@0.4 0.6`) is allowed and ignored here: see sfx_offset.
    """
    text = _OFFSET.sub("", str(token), count=1).strip()
    names = ", ".join(SFX)
    bad = ValueError(f"sound effect '{text}': write a built-in name ({names}) or file:<name>.wav|mp3|ogg|flac, "
                     f"optionally followed by a gain such as 0.5")
    m = _BUILTIN.match(text)
    if m:
        if m.group(1) not in SFX:
            raise ValueError(f"unknown sound effect '{m.group(1)}': built-in effects are {names}; "
                             f"a sound file is file:<name>")
        return "builtin", m.group(1), float(m.group(2) or 1.0)
    m = _FILE.match(text)
    if not m or ".." in m.group(1).split("/"):
        raise bad
    stem = m.group(1).rsplit("/", 1)[-1].rsplit(".", 1)[0]
    if not stem:
        raise bad
    return "file", m.group(1), float(m.group(2) or 1.0)


def soundtrack(seconds, music, events, music_gain=0.5, files=None):
    """Build the music bed and the effect stream for a video. Returns (bed, fx), both mono float64 arrays
    of int(seconds * 44100) + 44100 samples. No limiting is applied; overlapping effects can pass 1."""
    total = int(seconds * SR) + SR
    bed = np.zeros(total)
    if isinstance(music, str) and music in SONGS:
        bed = _song_samples(music, total, 2.5) * music_gain
    fx = np.zeros(total)
    for time, token in events:
        kind, name, gain = parse_sfx(token)
        if kind == "builtin":
            clip = render_sfx(name)
        else:
            if not files or name not in files:
                raise ValueError(f"sound effect file '{name}' was not loaded (04_scene/assets/ or library/sfx/)")
            clip = np.asarray(files[name], dtype=float)
            if clip.ndim > 1:
                clip = clip.mean(axis=1)
            peak = float(np.max(np.abs(clip))) if len(clip) else 0.0
            if peak > 0:
                clip = clip * (FILE_PEAK / peak)
        clip = clip * gain
        start = int(max(0, time) * SR)
        if kind == "builtin" and name in END_ALIGNED:
            start = max(0, start - len(clip))
        k = min(len(clip), total - start)
        if k > 0:
            fx[start:start + k] += clip[:k]
    return bed, fx


def write_wav(path, x, peak=None):
    """Write a 16-bit PCM WAV at 44100 Hz. 1-D `x` is mono; a 2-D `x` has one column per channel.

    With `peak`, `x` is first scaled so its largest absolute value equals `peak` (an all-zero `x` stays zero)."""
    x = np.nan_to_num(np.asarray(x, dtype=float))
    if peak is not None:
        m = float(np.max(np.abs(x))) if x.size else 0.0
        if m > 0:
            x = x * (peak / m)
    pcm = (np.clip(x, -1.0, 1.0) * 32767).astype("<i2")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1 if pcm.ndim == 1 else pcm.shape[1])
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
