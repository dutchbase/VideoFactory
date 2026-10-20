// Particle field: dots drift with depth on a canvas. Rewritten from RemotionUI ParticleField (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  FX.particleField = function (H, root, o = {}) {
    const K = FX.kit;
    const from = H.at(o.from == null ? 0 : o.from);
    const to = o.to == null ? ((window.ANIM && window.ANIM.meta && window.ANIM.meta.duration) || 10) : H.at(o.to);
    const n = Math.max(1, Math.round(o.count || 70)), speed = o.speed == null ? 1 : o.speed;
    const size = o.size || 14, minSize = o.minSize == null ? 2 : o.minSize, drift = o.drift == null ? 4 : o.drift;
    const glow = o.glow == null ? 1.6 : o.glow, intensity = o.intensity == null ? 1 : o.intensity;
    const rad = ((o.angle == null ? 8 : o.angle) * Math.PI) / 180;
    const dir = [Math.sin(rad), -Math.cos(rad)], perp = [Math.cos(rad), Math.sin(rad)];
    const r = K.rand(o.seed == null ? 1 : o.seed);
    // depth is squared so most dots sit far back; depth drives size, speed, brightness and focus together
    const dots = Array.from({ length: n }, () => ({ depth: r() ** 2, start: r(), lane: r(), sway: 0.4 + r() * 1.6,
      swayT: 1.1 + r() * 1.3, swayP: r() * 6.283, flickT: 0.9 + r() * 1.2, flickP: r() * 6.283 }));
    dots.sort((a, b) => a.depth - b.depth);  // far dots first, near dots on top
    const { canvas, ctx, w, h } = K.canvas(root, "fx-particle-field");
    root.insertBefore(canvas, root.firstChild);
    const color = K.token(o.color || "accent") || K.token("ink");
    const SPAN = 1.4;   // a dot travels 140% of the frame, so it enters and leaves off screen
    function draw(p, t) {
      const time = (t - from) * speed;
      ctx.clearRect(0, 0, w, h);
      ctx.globalCompositeOperation = "lighter";
      for (const d of dots) {
        const along = (((d.start + time * (0.35 + d.depth * 0.95) / 8) % 1) + 1) % 1;
        const sway = Math.sin((time / d.swayT) * 6.283 + d.swayP) * drift * d.sway / 100;
        const across = d.lane * SPAN - SPAN / 2 + sway, fwd = along * SPAN - SPAN / 2;
        const x = (0.5 + dir[0] * fwd + perp[0] * across) * w, y = (0.5 + dir[1] * fwd + perp[1] * across) * h;
        const rr = (minSize + (size - minSize) * d.depth) / 2 * (1 + glow);
        const flick = 0.7 + 0.3 * Math.sin((time / d.flickT) * 6.283 + d.flickP);
        ctx.globalAlpha = Math.min(1, (0.18 + d.depth * 0.7) * flick * intensity);
        const g = ctx.createRadialGradient(x, y, 0, x, y, rr);
        g.addColorStop(0, color); g.addColorStop(0.34 / (1 + glow) + 0.2 * (1 - d.depth), color); g.addColorStop(1, "transparent");
        ctx.fillStyle = g;
        ctx.beginPath(); ctx.arc(x, y, rr, 0, 6.283); ctx.fill();
      }
      ctx.globalAlpha = 1;
      ctx.globalCompositeOperation = "source-over";
    }
    draw(0, from);
    H.drive(draw, from, to);
    return { canvas };
  };
})();
