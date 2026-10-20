// Mesh gradient: soft blobs of brand colour drift slowly behind the content. Rewritten from Onda MeshGradient (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  FX.meshGradient = function (H, root, o = {}) {
    const K = FX.kit;
    const from = H.at(o.from == null ? 0 : o.from);
    const to = o.to == null ? ((window.ANIM && window.ANIM.meta && window.ANIM.meta.duration) || 10) : H.at(o.to);
    const roles = o.colors && o.colors.length ? o.colors : ["accent", "line", "dim"];
    const speed = o.speed == null ? 1 : o.speed, opacity = o.opacity == null ? 0.5 : o.opacity;
    const radius = (o.size == null ? 0.45 : o.size) * K.size(root).w;
    const r = K.rand(o.seed == null ? 1 : o.seed);
    // each blob: a home place, how far it drifts, a phase; all from the seed
    const blobs = roles.map(role => ({ role, phase: r() * 6.283, ax: 10 + r() * 12, ay: 10 + r() * 12, bx: 25 + r() * 50, by: 25 + r() * 50 }));
    const el = document.createElement("div");
    el.className = "fx-mesh";
    if (o.background) el.style.background = K.color(o.background);
    const layer = document.createElement("div");
    layer.className = "fx-mesh-blobs";
    layer.style.opacity = String(opacity);
    el.appendChild(layer);
    root.insertBefore(el, root.firstChild);
    function draw(p, t) {
      const w = (t - from) * 0.4 * speed;   // radians per second: one slow lap in about 16 s
      layer.style.backgroundImage = blobs.map(b => {
        const x = b.bx + Math.sin(w + b.phase) * b.ax, y = b.by + Math.cos(w * 0.8 + b.phase) * b.ay;
        return `radial-gradient(circle ${radius.toFixed(0)}px at ${x.toFixed(2)}% ${y.toFixed(2)}%, ${K.color(b.role)} 0%, transparent 100%)`;
      }).join(",");
    }
    draw(0, from);
    H.drive(draw, from, to);
    return { el };
  };
})();
