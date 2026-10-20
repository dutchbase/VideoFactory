// Circle reveal: a round hole opens from a point and shows shot B over shot A, with a strip of B's ground ahead of it (cut K5 variant).
// Rewritten from RemotionUI TransitionCircleReveal (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  const inOut = p => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2);
  const setMask = (el, g) => { el.style.webkitMaskImage = g; el.style.maskImage = g; };
  function groundOf(to, role) {
    if (role) return FX.kit.token(role);
    const bg = getComputedStyle(to).backgroundColor;
    return !bg || /transparent|,\s*0\)$/.test(bg) ? FX.kit.token("cream") : bg;
  }
  FX.circleReveal = function (H, from, to, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at), dur = o.dur == null ? 0.58 : o.dur, t1 = at + dur;
    const { w, h } = K.size(to);
    const ox = K.clamp(o.x == null ? 0.5 : o.x), oy = K.clamp(o.y == null ? 0.5 : o.y);
    const soft = K.clamp(o.soft == null ? 0.12 : o.soft, 0.01, 0.6);
    const lag = K.clamp(o.lag == null ? 0.2 : o.lag, 0, 0.6), push = o.push == null ? 1.04 : o.push;
    // the radius that reaches the far corner from the origin, so no wedge stays shut
    const R = Math.hypot(Math.max(ox, 1 - ox) * w, Math.max(oy, 1 - oy) * h), sp = soft * R;
    const paint = o.ground !== false;
    const parent = to.parentNode;
    let panel = null;
    if (paint) {
      panel = document.createElement("div");
      panel.className = "fx-circle-ground";
      panel.style.background = groundOf(to, o.ground);
      parent.insertBefore(panel, to);
    }
    from.style.zIndex = "1"; if (panel) panel.style.zIndex = "2"; to.style.zIndex = "3";
    const hole = e => {
      const r = e * (R + sp);   // outer radius; the soft edge is the last sp pixels
      return `radial-gradient(circle at ${ox * w}px ${oy * h}px, black ${r - sp}px, transparent ${r}px)`;
    };
    function draw(p) {
      if (panel) setMask(panel, hole(inOut(p)));
      setMask(to, hole(inOut(K.clamp((p - (panel ? lag : 0)) / (1 - (panel ? lag : 0))))));
    }
    draw(0);
    H.tl.fromTo(to, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.001, immediateRender: true }, at);
    // A leans a little toward the camera under the hole, so the circle reads as depth
    H.tl.fromTo(from, { scale: 1, transformOrigin: `${ox * 100}% ${oy * 100}%` },
      { scale: push, duration: dur, ease: "power2.in", immediateRender: true }, at);
    H.tl.fromTo(from, { autoAlpha: 1 }, { autoAlpha: 0, duration: 0.001, immediateRender: false }, t1);
    if (panel) H.tl.fromTo(panel, { autoAlpha: 1 }, { autoAlpha: 0, duration: 0.001, immediateRender: false }, t1);
    H.drive(draw, at, t1);
    return { panel, end: t1 };
  };
})();
