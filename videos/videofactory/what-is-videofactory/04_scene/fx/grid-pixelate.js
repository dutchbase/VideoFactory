// Grid pixelate: cells of B's ground cover shot A in a seeded scatter, shot B takes over under them, then the cells clear (cut K5 variant).
// Rewritten from Onda GridPixelate (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  function groundOf(to, role) {
    if (role) return FX.kit.token(role);
    const bg = getComputedStyle(to).backgroundColor;
    return !bg || /transparent|,\s*0\)$/.test(bg) ? FX.kit.token("cream") : bg;
  }
  FX.gridPixelate = function (H, from, to, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at), dur = o.dur == null ? 0.6 : o.dur, t1 = at + dur, mid = at + dur / 2;
    const parent = to.parentNode;
    const { canvas, ctx, w, h } = K.canvas(parent, "fx-grid-pixelate");
    const cols = Math.round(K.clamp(o.cols == null ? 16 : o.cols, 2, 64));
    const rows = Math.round(K.clamp(o.rows == null ? cols * h / w : o.rows, 2, 64));
    const accent = K.clamp(o.accent == null ? 0 : o.accent), r = K.rand(o.seed == null ? 1 : o.seed);
    const ground = groundOf(to, o.ground), hot = K.token("accent");
    // Each cell has a time it turns on (before the middle) and a time it turns off (after it). Hard steps, no fades.
    const cells = Array.from({ length: cols * rows }, () => ({ on: r() * 0.499, off: 0.501 + r() * 0.499, hot: r() < accent }));
    from.style.zIndex = "1"; to.style.zIndex = "2"; canvas.style.zIndex = "3";
    const cw = w / cols, ch = h / rows;
    function draw(p) {
      ctx.clearRect(0, 0, w, h);
      cells.forEach((c, i) => {
        if (p < c.on || p >= c.off) return;
        ctx.fillStyle = c.hot ? hot : ground;
        const x = Math.floor((i % cols) * cw), y = Math.floor(Math.floor(i / cols) * ch);
        ctx.fillRect(x, y, Math.ceil(cw) + 1, Math.ceil(ch) + 1);
      });
    }
    draw(0);
    // The shots swap in one frame in the middle, when every cell is on.
    H.tl.fromTo(to, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.001, immediateRender: true }, mid);
    H.tl.fromTo(from, { autoAlpha: 1 }, { autoAlpha: 0, duration: 0.001, immediateRender: false }, mid);
    H.drive(draw, at, t1);
    return { canvas, end: t1 };
  };
})();
