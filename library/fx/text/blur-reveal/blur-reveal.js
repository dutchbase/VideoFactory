// Blur reveal: text rises out of a soft blur on a calm spring. Rewritten from Onda BlurReveal (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  FX.blurReveal = function (H, el, o = {}) {
    const at = H.at(o.at == null ? 0 : o.at);
    const dur = o.dur == null ? 0.7 : o.dur;
    const blur = o.blur == null ? 10 : o.blur, rise = o.rise == null ? 16 : o.rise;
    const sp = FX.kit.spring({ dur, bounce: 0 });
    const ease = p => (p >= 1 ? 1 : sp(p * dur));
    const parts = o.by ? FX.kit.split(el, o.by, "fx-blur-part") : [el];
    parts.forEach((p, i) => H.tl.fromTo(p, { autoAlpha: 0, filter: `blur(${blur}px)`, y: rise },
      { autoAlpha: 1, filter: "blur(0px)", y: 0, duration: dur, ease, immediateRender: true }, at + i * (o.stagger == null ? 0.06 : o.stagger)));
    return { el, parts };
  };
})();
