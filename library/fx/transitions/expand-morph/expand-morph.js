// Expand morph: shot A shrinks a little (anticipation), then a rounded card of shot B grows from a small origin rect to the full frame (cut K3).
// Rewritten from Onda ExpandMorph (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  const enter = p => (p >= 1 ? 1 : (1 - Math.pow(2, -10 * p)) / (1 - Math.pow(2, -10)));   // calm settle, no overshoot
  FX.expandMorph = function (H, from, to, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at), lead = o.lead == null ? 0.14 : o.lead, dur = o.dur == null ? 0.8 : o.dur;
    const cut = at + lead, t1 = cut + dur, shrink = o.shrink == null ? 0.09 : o.shrink;
    const [ox, oy, ow, oh] = o.origin || [0.36, 0.34, 0.28, 0.32];
    const r0 = o.radius == null ? 28 : o.radius;
    const { w, h } = K.size(to);
    const parent = to.parentNode;
    const shadow = document.createElement("div");
    shadow.className = "fx-expand-shadow";
    parent.insertBefore(shadow, to);
    from.style.zIndex = "1"; shadow.style.zIndex = "2"; to.style.zIndex = "3";
    function draw(p) {
      const e = enter(p);
      const cw = K.lerp(ow, 1, e) * w, ch = K.lerp(oh, 1, e) * h, l = K.lerp(ox, 0, e) * w, t = K.lerp(oy, 0, e) * h;
      const r = K.lerp(r0, 0, e), s = cw / w;
      // B keeps its shape and scales to the card width; the card crops it to its own height
      gsap.set(to, { x: l, y: t, scale: s, transformOrigin: "0 0" });
      to.style.clipPath = p >= 1 ? "none" : `inset(0 0 ${Math.max(0, h - ch / s)}px 0 round ${r / s}px)`;
      Object.assign(shadow.style, { left: l + "px", top: t + "px", width: cw + "px", height: ch + "px", borderRadius: r + "px" });
    }
    draw(0);
    // A leans back 9 %, the biggest step last (anticipation); it stays under the growing card
    H.tl.fromTo(from, { scale: 1, transformOrigin: "50% 50%" }, { scale: 1 - shrink, duration: lead, ease: "power3.in", immediateRender: true }, at);
    H.tl.fromTo(to, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.001, immediateRender: true }, cut);
    H.tl.fromTo(shadow, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.001, immediateRender: true }, cut);
    H.tl.fromTo(shadow, { autoAlpha: 1 }, { autoAlpha: 0, duration: 0.001, immediateRender: false }, t1);
    H.tl.fromTo(from, { autoAlpha: 1 }, { autoAlpha: 0, duration: 0.001, immediateRender: false }, t1);
    H.drive(draw, cut, t1);
    return { shadow, cut, end: t1 };
  };
})();
