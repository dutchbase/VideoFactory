// Dynamic grid: a technical grid (lines or dots) drifts diagonally and loops by one cell. Rewritten from Onda DynamicGrid (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  FX.dynamicGrid = function (H, root, o = {}) {
    const K = FX.kit;
    const from = H.at(o.from == null ? 0 : o.from);
    const to = o.to == null ? ((window.ANIM && window.ANIM.meta && window.ANIM.meta.duration) || 10) : H.at(o.to);
    const cell = Math.max(16, o.cell == null ? 96 : o.cell), speed = o.speed == null ? 36 : o.speed;
    const rad = ((o.angle == null ? 45 : o.angle) * Math.PI) / 180, opacity = o.opacity == null ? 0.5 : o.opacity;
    const col = K.color(o.color, "dim"), dots = o.variant === "dots", glow = o.glow == null ? 0 : o.glow;
    const el = document.createElement("div");
    el.className = "fx-grid";
    if (o.fade !== false) { const m = "radial-gradient(ellipse at 50% 50%, black 25%, transparent 78%)"; el.style.webkitMaskImage = m; el.style.maskImage = m; }
    const plane = document.createElement("div");
    plane.className = "fx-grid-plane";
    plane.style.inset = `-${cell}px`;
    plane.style.opacity = String(opacity);
    plane.style.backgroundSize = `${cell}px ${cell}px`;
    plane.style.backgroundImage = dots
      ? `radial-gradient(circle at 50% 50%, ${col} 0, ${col} 3px, transparent 3.5px)`
      : `linear-gradient(${col} 0, ${col} 2px, transparent 2px), linear-gradient(90deg, ${col} 0, ${col} 2px, transparent 2px)`;
    el.appendChild(plane);
    if (glow > 0) {   // optional accent light in the middle; keep it away from a centred title
      const g = document.createElement("div");
      g.className = "fx-grid-glow";
      g.style.opacity = String(Math.min(1, glow) * 0.35);
      el.appendChild(g);
    }
    root.insertBefore(el, root.firstChild);
    const wrap = (v, m) => ((v % m) + m) % m;
    function draw(p, t) {
      const d = (t - from) * speed;   // px along the drift direction; wraps by one cell, so the loop has no seam
      const x = wrap(d * Math.cos(rad), cell), y = wrap(d * Math.sin(rad), cell);
      plane.style.transform = `translate3d(${-x}px, ${-y}px, 0)`;
    }
    draw(0, from);
    H.drive(draw, from, to);
    return { el };
  };
})();
