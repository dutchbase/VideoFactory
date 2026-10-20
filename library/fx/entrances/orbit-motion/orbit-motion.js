// Orbit motion: the children of el travel round a tilted ellipse, with depth in size and fade. Rewritten from RemotionUI OrbitMotion (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  FX.orbitMotion = function (H, el, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at);
    const to = o.to == null ? ((window.ANIM && window.ANIM.meta && window.ANIM.meta.duration) || 10) : H.at(o.to);
    const rx = o.radiusX == null ? 520 : o.radiusX, ry = o.radiusY == null ? 190 : o.radiusY;
    const period = Math.max(0.5, o.period == null ? 8 : o.period), tilt = o.tilt == null ? -12 : o.tilt;
    const sign = o.direction === "ccw" ? -1 : 1, phase = ((o.phase || 0) * Math.PI) / 180;
    const depth = o.depth == null ? 0.28 : o.depth, depthFade = o.depthFade == null ? 0.4 : o.depthFade;
    const upright = o.upright !== false, enter = o.enter == null ? 0.7 : o.enter, stagger = o.stagger == null ? 0.1 : o.stagger;
    const items = Array.from(el.children);
    el.classList.add("fx-orbit");
    const ring = H.mk("div", "fx-orbit-ring", el);
    ring.style.left = (o.centerX == null ? 50 : o.centerX) + "%";
    ring.style.top = (o.centerY == null ? 50 : o.centerY) + "%";
    const cs = Math.cos((tilt * Math.PI) / 180), sn = Math.sin((tilt * Math.PI) / 180);
    let path = null;
    if (o.showPath) {
      path = H.mk("div", "fx-orbit-path", ring);
      path.style.cssText = `left:${-rx}px;top:${-ry}px;width:${rx * 2}px;height:${ry * 2}px;transform:rotate(${tilt}deg)`;
    }
    items.forEach(it => { it.classList.add("fx-orbit-item"); ring.appendChild(it); });
    const n = Math.max(1, items.length);
    const out = p => 1 - (1 - p) ** 3;
    function draw(p, t) {
      const turn = (Math.max(0, t - at) / period) * sign;
      if (path) path.style.opacity = K.clamp((t - at) / enter).toFixed(3);
      items.forEach((it, i) => {
        const e = out(K.clamp((t - at - i * stagger) / enter));
        const a = (turn + i / n) * Math.PI * 2 + phase;
        const near = Math.sin(a);
        const ex = Math.cos(a) * rx * e, ey = Math.sin(a) * ry * e;
        const x = ex * cs - ey * sn, y = ex * sn + ey * cs;   // the ellipse is tilted; the ring itself has no transform, so z-index works across items
        it.style.left = x.toFixed(2) + "px";
        it.style.top = y.toFixed(2) + "px";
        it.style.transform = `translate(-50%,-50%) scale(${((1 + depth * near) * (0.6 + 0.4 * e)).toFixed(4)})${upright ? ` rotate(${-tilt}deg)` : ""}`;
        it.style.opacity = (e * (1 - depthFade * (1 - (near + 1) / 2))).toFixed(3);
        it.style.zIndex = near >= 0 ? 20 : 1;
      });
    }
    draw(0, at);
    H.drive(draw, at, to);
    return { el, items };
  };
})();
