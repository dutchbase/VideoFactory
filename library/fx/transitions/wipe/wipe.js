// Wipe: a soft-edged wipe from shot A to shot B, painted in B's ground colour (cut K5). Rewritten from Onda wipe (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  const AXIS = { right: "to right", left: "to left", down: "to bottom", up: "to top" };
  const inOut = p => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2);
  const setMask = (el, g) => { el.style.webkitMaskImage = g; el.style.maskImage = g; };
  // The ground colour of shot B: a role name from the option, else the background B already has.
  function groundOf(to, role) {
    if (role) return FX.kit.token(role);
    const bg = getComputedStyle(to).backgroundColor;
    return !bg || /transparent|,\s*0\)$/.test(bg) ? FX.kit.token("cream") : bg;
  }
  FX.wipe = function (H, from, to, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at), dur = o.dur == null ? 0.58 : o.dur, t1 = at + dur;
    const soft = K.clamp(o.soft == null ? 0.36 : o.soft, 0.02, 0.8);
    const dir = AXIS[o.dir || "right"] || AXIS.right;
    const paint = o.ground !== false;
    const lag = paint ? K.clamp(o.lag == null ? 0.28 : o.lag, 0, 0.6) : 0;
    const parent = to.parentNode;
    let panel = null;
    if (paint) {
      panel = document.createElement("div");
      panel.className = "fx-wipe-ground";
      panel.style.background = groundOf(to, o.ground);
      parent.insertBefore(panel, to);
    }
    from.style.zIndex = "1"; if (panel) panel.style.zIndex = "2"; to.style.zIndex = "3";
    // m = place of the edge in % of the axis; the soft zone runs from m to m + soft. At p = 0 nothing is open, at p = 1 all is.
    const grad = m => `linear-gradient(${dir}, black ${m}%, transparent ${m + soft * 100}%)`;
    const edge = e => (-soft + e * (1 + soft)) * 100;
    function draw(p) {
      if (panel) setMask(panel, grad(edge(inOut(p))));
      setMask(to, grad(edge(inOut(K.clamp((p - lag) / (1 - lag))))));
    }
    draw(0);
    // B shows from the start of the wipe (its mask is still shut), A and the paint go away when the wipe is done.
    H.tl.fromTo(to, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.001, immediateRender: true }, at);
    H.tl.fromTo(from, { autoAlpha: 1 }, { autoAlpha: 0, duration: 0.001, immediateRender: false }, t1);
    if (panel) H.tl.fromTo(panel, { autoAlpha: 1 }, { autoAlpha: 0, duration: 0.001, immediateRender: false }, t1);
    H.drive(draw, at, t1);
    return { panel, end: t1 };
  };
})();
