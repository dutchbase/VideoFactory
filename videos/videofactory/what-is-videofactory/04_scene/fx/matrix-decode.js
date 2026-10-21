// Matrix decode: a scramble of glyphs resolves left to right into the real text. Rewritten from RemotionUI matrix-decode (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  FX.matrixDecode = function (H, el, o = {}) {
    const at = H.at(o.at == null ? 0 : o.at);
    const dur = o.dur == null ? 1.0 : o.dur;
    const rate = o.rate == null ? 24 : o.rate;
    const jit = o.jitter == null ? 2 : o.jitter;
    const pool = Array.from(o.glyphs || "0123456789ABCDEFGHJKLMNPQRSTUVXYZ#$%&*+=<>/");
    const text = o.text != null ? o.text : el.textContent;
    el.textContent = text;
    el.classList.add("fx-matrix-decode");
    el.style.setProperty("--fx-md-ink", FX.kit.color(o.color, "ink"));
    el.style.setProperty("--fx-md-hot", FX.kit.color(o.hotColor, "accent"));
    el.style.setProperty("--fx-md-dim", FX.kit.color(o.scrambleColor, "dim"));
    const parts = FX.kit.split(el, "chars", "fx-matrix-decode-ch");
    const rnd = FX.kit.rand(o.seed == null ? "matrix-decode" : o.seed);
    const offs = parts.map(() => Math.round((rnd() * 2 - 1) * jit));
    const cells = parts.map(p => {
      const ch = p.textContent;
      p.textContent = "";
      const real = H.mk("span", "fx-matrix-decode-real", p, ch);
      const glyph = H.mk("span", "fx-matrix-decode-glyph", p);
      return { real, glyph };
    });
    const n = parts.length;
    function draw(p) {
      const front = p * (n + 2 * jit) - jit;
      const done = parts.map((_, i) => p >= 1 || i + offs[i] < front);
      const hot = done.indexOf(false);
      const step = Math.floor(p * dur * rate);
      cells.forEach((c, i) => {
        c.real.style.visibility = done[i] ? "visible" : "hidden";
        c.glyph.style.display = done[i] ? "none" : "block";
        if (!done[i]) {
          c.glyph.textContent = pool[(i * 17 + step) % pool.length];
          c.glyph.style.color = i === hot ? "var(--fx-md-hot)" : "var(--fx-md-dim)";
        }
      });
    }
    draw(0);
    H.tl.fromTo(el, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.001, ease: "none", immediateRender: true }, Math.max(0, at - 0.001));
    H.drive(draw, at, at + dur);
    return { el, parts, end: at + dur };
  };
})();
