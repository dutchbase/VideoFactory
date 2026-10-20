// Zoom through: shot A pushes past the lens and blurs, hard cut, shot B arrives out of the same push, from blur to sharp (cut K4).
// Numbers from _shared/motion.md (Cuts). Rewritten from RemotionUI ZoomThrough (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  const enter = p => (p >= 1 ? 1 : (1 - Math.pow(2, -10 * p)) / (1 - Math.pow(2, -10)));   // fast start, soft landing
  FX.zoomThrough = function (H, from, to, o = {}) {
    const at = H.at(o.at == null ? 0 : o.at);
    const out = o.out == null ? 0.2 : o.out, dur = o.dur == null ? 0.5 : o.dur, cut = at + out;
    const blur = o.blur == null ? 18 : o.blur;
    const outScale = o.outScale == null ? 1.2 : o.outScale, inScale = o.inScale == null ? 0.75 : o.inScale;
    from.style.zIndex = "1"; to.style.zIndex = "2";
    H.tl.fromTo(from, { scale: 1, filter: "blur(0px)", transformOrigin: "50% 50%" },
      { scale: outScale, filter: `blur(${blur}px)`, duration: out, ease: "power3.in", immediateRender: true }, at);
    H.tl.fromTo(from, { autoAlpha: 1 }, { autoAlpha: 0, duration: 0.001, immediateRender: false }, cut);
    // B starts at the blur A ended with and settles from a smaller scale
    H.tl.fromTo(to, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.001, immediateRender: true }, cut);
    H.tl.fromTo(to, { scale: inScale, filter: `blur(${blur}px)`, transformOrigin: "50% 50%" },
      { scale: 1, filter: "blur(0px)", duration: dur, ease: enter, immediateRender: true }, cut);
    return { cut, end: cut + dur };
  };
})();
