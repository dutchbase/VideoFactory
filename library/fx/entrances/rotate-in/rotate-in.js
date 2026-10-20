// Rotate in: text settles from a slight angle to 0 while it fades in. Rewritten from Onda RotateIn (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  FX.rotateIn = function (H, el, o = {}) {
    const at = H.at(o.at == null ? 0 : o.at);
    const dur = o.dur == null ? 0.7 : o.dur;
    const angle = FX.kit.clamp(o.angle == null ? -8 : o.angle, -12, 12);   // the calm range is -12..12 degrees
    const sp = FX.kit.spring({ dur, bounce: 0 });
    const ease = p => (p >= 1 ? 1 : sp(p * dur));
    const parts = o.by ? FX.kit.split(el, o.by, "fx-rotate-part") : [el];
    parts.forEach((p, i) => {
      const s = at + i * (o.stagger == null ? 0.08 : o.stagger);
      H.tl.fromTo(p, { rotation: angle, transformOrigin: o.origin || "50% 50%" }, { rotation: 0, duration: dur, ease, immediateRender: true }, s);
      H.tl.fromTo(p, { autoAlpha: 0 }, { autoAlpha: 1, duration: dur, ease, immediateRender: true }, s);
    });
    return { el, parts };
  };
})();
