// Blinds: slats open one after the other and show shot B over shot A (cut K5 variant). Rewritten from RemotionUI TransitionBlinds (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  const inOut = p => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2);
  FX.blinds = function (H, from, to, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at), dur = o.dur == null ? 0.6 : o.dur, t1 = at + dur;
    const n = Math.round(K.clamp(o.slats == null ? 8 : o.slats, 2, 48));
    const vertical = o.orientation === "vertical";
    const stagger = K.clamp(o.stagger == null ? 0.5 : o.stagger, 0, 0.9), soft = K.clamp(o.soft == null ? 0.12 : o.soft, 0.01, 0.6);
    const alternate = !!o.alternate;
    from.style.zIndex = "1"; to.style.zIndex = "2";
    // One mask layer per slat. A slat is a strip of the frame that opens along the long axis, with a soft leading edge.
    const size = 100 / n + 0.25;   // a slat is a little longer than its share, so no seam shows between slats
    function draw(p) {
      if (p >= 1) { to.style.webkitMaskImage = to.style.maskImage = "none"; return; }
      const img = [], pos = [];
      for (let i = 0; i < n; i++) {
        const start = n > 1 ? (i / (n - 1)) * stagger : 0;   // the last slat still ends at p = 1
        const m = (-soft + inOut(K.clamp((p - start) / (1 - stagger))) * (1 + soft)) * 100;
        const rev = alternate && i % 2 === 1;
        const axis = vertical ? (rev ? "to top" : "to bottom") : (rev ? "to left" : "to right");
        img.push(`linear-gradient(${axis}, black ${m}%, transparent ${m + soft * 100}%)`);
        pos.push(vertical ? `${(i / (n - 1)) * 100}% 0` : `0 ${(i / (n - 1)) * 100}%`);
      }
      const sz = Array(n).fill(vertical ? `${size}% 100%` : `100% ${size}%`).join(",");
      const css = { WebkitMaskImage: img.join(","), maskImage: img.join(","), WebkitMaskSize: sz, maskSize: sz,
        WebkitMaskPosition: pos.join(","), maskPosition: pos.join(","), WebkitMaskRepeat: "no-repeat", maskRepeat: "no-repeat" };
      Object.assign(to.style, css);
    }
    draw(0);
    H.tl.fromTo(to, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.001, immediateRender: true }, at);
    H.tl.fromTo(from, { autoAlpha: 1 }, { autoAlpha: 0, duration: 0.001, immediateRender: false }, t1);
    H.drive(draw, at, t1);
    return { end: t1, slats: n };
  };
})();
