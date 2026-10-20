// Skew in: an element slides in leaning, then stands up straight. Rewritten from RemotionUI SkewIn (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  FX.skewIn = function (H, el, o = {}) {
    const at = H.at(o.at == null ? 0 : o.at);
    const dur = o.dur == null ? 0.6 : o.dur;
    const lean = o.direction === "right" ? -1 : 1;
    const skew = o.skew == null ? 14 : o.skew, skewY = o.skewY == null ? 0 : o.skewY, travel = o.travel == null ? 56 : o.travel;
    const sp = FX.kit.spring({ dur, bounce: 0 });
    const ease = p => (p >= 1 ? 1 : sp(p * dur));
    H.tl.fromTo(el, { skewX: skew * lean, skewY: skewY * lean, x: -travel * lean, transformOrigin: o.origin || "0% 100%" },
      { skewX: 0, skewY: 0, x: 0, duration: dur, ease, immediateRender: true }, at);
    H.tl.fromTo(el, { autoAlpha: 0 }, { autoAlpha: 1, duration: dur * 0.6, ease: "power2.out", immediateRender: true }, at);
    return { el, at, dur };
  };
})();
