// Whip pan: both shots slide along one axis in about 8 frames, with a motion blur that follows the speed (cut K7).
// Rewritten from RemotionUI TransitionWhipPan (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  const VEC = { left: [-1, 0], right: [1, 0], up: [0, -1], down: [0, 1] };
  // A curve from 0 to 1 whose speed peaks early: the move is mostly done in its first half.
  const curve = (p, punch) => {
    const q = 1 - Math.pow(1 - p, 1.7);
    if (q <= 0) return 0;
    if (q >= 1) return 1;
    const a = Math.pow(q, punch);
    return a / (a + Math.pow(1 - q, punch));
  };
  FX.whipPan = function (H, from, to, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at), dur = o.dur == null ? 8 / 30 : o.dur, t1 = at + dur;
    const [dx, dy] = VEC[o.dir || "left"] || VEC.left;
    const blur = o.blur == null ? 20 : o.blur, punch = o.punch == null ? 2.2 : o.punch;
    const { w, h } = K.size(to), travel = K.clamp(o.travel == null ? 1 : o.travel, 0.2, 1.5);
    const dist = (dx ? w : h) * travel;
    // speed of the curve, as a share of its peak: the blur follows it
    const speed = p => (curve(Math.min(1, p + 0.01), punch) - curve(Math.max(0, p - 0.01), punch)) / 0.02;
    let peak = 1e-6;
    for (let i = 0; i <= 100; i++) peak = Math.max(peak, speed(i / 100));
    from.style.zIndex = "1"; to.style.zIndex = "2";
    function draw(p) {
      const e = curve(p, punch), px = blur * speed(p) / peak;
      const f = px > 0.05 ? `blur(${px.toFixed(2)}px)` : "none";
      gsap.set(from, { x: e * dist * dx, y: e * dist * dy, filter: f });
      gsap.set(to, { x: (e - 1) * dist * dx, y: (e - 1) * dist * dy, filter: f });
    }
    draw(0);
    H.tl.fromTo(to, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.001, immediateRender: true }, at);
    H.tl.fromTo(from, { autoAlpha: 1 }, { autoAlpha: 0, duration: 0.001, immediateRender: false }, t1);
    H.drive(draw, at, t1);
    return { end: t1 };
  };
})();
