// Shared helpers for library/fx parts. Works in both engines (Modern kit and HyperFrames): plain maths and DOM, no clock.
// Every fx part loads it after core.js. Measure the page only inside FX.kit.layout(place) or a H.drive draw function. Rules for parts: library/fx/CONTEXT.md. Porting guide: _shared/porting.md.
(function () {
  const FX = window.FX = window.FX || {};
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const lerp = (a, b, p) => a + (b - a) * p;

  // Piecewise-linear map of x over the stops xs -> ys, clamped at both ends. ease (optional) shapes each segment.
  function interp(x, xs, ys, ease) {
    if (x <= xs[0]) return ys[0];
    for (let i = 1; i < xs.length; i++) {
      if (x <= xs[i]) {
        const p = (x - xs[i - 1]) / (xs[i] - xs[i - 1] || 1);
        return lerp(ys[i - 1], ys[i], ease ? ease(p) : p);
      }
    }
    return ys[ys.length - 1];
  }

  // A spring from 0 to 1 that settles in about `dur` seconds; bounce 0 = no overshoot. Twin: P.spring in player.js.
  function spring({ dur = 0.5, bounce = 0 } = {}) {
    const sigma = 6.5 / Math.max(0.05, dur);
    const zeta = clamp(1 - bounce, 0.05, 1);
    if (zeta >= 1) return s => (s <= 0 ? 0 : 1 - (1 + sigma * s) * Math.exp(-sigma * s));
    const wd = (sigma / zeta) * Math.sqrt(1 - zeta * zeta), k = sigma / wd;
    return s => (s <= 0 ? 0 : 1 - Math.exp(-sigma * s) * (Math.cos(wd * s) + k * Math.sin(wd * s)));
  }

  // Seeded random numbers in [0, 1): same seed, same sequence. Never use Math.random in a part.
  function rand(seed) {
    let s = typeof seed === "string" ? [...seed].reduce((h, ch) => Math.imul(h ^ ch.charCodeAt(0), 16777619), 2166136261) : seed;
    s >>>= 0;
    return () => {
      s = (s + 0x6d2b79f5) >>> 0;
      let x = Math.imul(s ^ (s >>> 15), s | 1);
      x ^= x + Math.imul(x ^ (x >>> 7), x | 61);
      return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
    };
  }

  // Smooth value noise in [0, 1) on a lattice: noise(x, y, seed). Same input, same output.
  function hash2(i, j, seed) {
    let h = Math.imul(i, 374761393) + Math.imul(j, 668265263) + Math.imul(seed | 0, 2147483647);
    h = Math.imul(h ^ (h >>> 13), 1274126177);
    return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
  }
  function noise(x, y = 0, seed = 1) {
    const i = Math.floor(x), j = Math.floor(y), fx = x - i, fy = y - j;
    const u = fx * fx * (3 - 2 * fx), v = fy * fy * (3 - 2 * fy);
    const a = hash2(i, j, seed), b = hash2(i + 1, j, seed), c = hash2(i, j + 1, seed), d = hash2(i + 1, j + 1, seed);
    return lerp(lerp(a, b, u), lerp(c, d, u), v);
  }

  // The stage size in px (data-width / data-height of #stage or the composition root).
  function size(root) {
    const s = (root && root.closest && root.closest("[data-width]")) || document.querySelector("[data-width]");
    return { w: +(s && s.dataset.width) || 1920, h: +(s && s.dataset.height) || 1080 };
  }

  // A brand colour or font from its CSS variable, for canvas drawing: token("accent") -> "#FF5B2E".
  const token = name => getComputedStyle(document.documentElement).getPropertyValue("--" + name).trim();

  // A canvas that fills `root` at stage resolution, with class `cls`. Returns { canvas, ctx, w, h }.
  function canvas(root, cls) {
    const { w, h } = size(root);
    const c = document.createElement("canvas");
    c.width = w; c.height = h;
    c.className = cls || "fx-canvas";
    root.appendChild(c);
    return { canvas: c, ctx: c.getContext("2d"), w, h };
  }

  // Wrap the text of `el` in spans, one per character ("chars") or word ("words"); spaces stay. Returns the spans.
  function split(el, by = "chars", cls = "fx-part") {
    const text = el.textContent;
    el.textContent = "";
    const parts = by === "words" ? text.split(/(\s+)/) : Array.from(text);
    const out = [];
    for (const part of parts) {
      if (!part) continue;
      if (/^\s+$/.test(part)) { el.appendChild(document.createTextNode(part)); continue; }
      const s = document.createElement("span");
      s.className = cls;
      s.textContent = part;
      s.style.display = "inline-block";
      el.appendChild(s);
      out.push(s);
    }
    return out;
  }

  // A brand colour role for an option: "accent" -> "var(--accent)". A part never takes a hex colour.
  const color = (role, fallback = "ink") => `var(--${role || fallback})`;

  // Sizes and positions measured from the page (text width, a target's box). A scene script runs before the brand fonts
  // have loaded and before the page has loaded, so place() runs now, again each time fonts finish loading, and once on
  // the load event (after the engine has set up the stage). place() only sets sizes, positions and attributes from fresh
  // measurements; it never adds tweens. Returns place.
  function layout(place) {
    place();
    if (document.readyState !== "complete") window.addEventListener("load", () => place(), { once: true });
    if (document.fonts) {
      document.fonts.addEventListener("loadingdone", () => place());
      if (document.fonts.status !== "loaded") document.fonts.ready.then(() => place());
    }
    return place;
  }

  FX.kit = { clamp, lerp, interp, spring, rand, noise, size, token, canvas, split, color, layout };
})();
