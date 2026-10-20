// Mask reveal: text appears from behind a mask that slides away with a hard edge, no fade. Rewritten from Onda MaskReveal (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  FX.maskReveal = function (H, el, o = {}) {
    const at = H.at(o.at == null ? 0 : o.at);
    const dur = o.dur == null ? 0.7 : o.dur;
    const sp = FX.kit.spring({ dur, bounce: 0 });
    const ease = p => (p >= 1 ? 1 : sp(p * dur));
    // inset(top right bottom left); the three open sides stay 10% wide so a glyph tail is never cut
    const m = "-10%", c = "100%";
    const covered = { left: `inset(${m} ${c} ${m} ${m})`, right: `inset(${m} ${m} ${m} ${c})`,
      top: `inset(${m} ${m} ${c} ${m})`, bottom: `inset(${c} ${m} ${m} ${m})` };
    const dir = covered[o.direction] ? o.direction : "left";
    H.tl.fromTo(el, { clipPath: covered[dir] }, { clipPath: `inset(${m} ${m} ${m} ${m})`, duration: dur, ease, immediateRender: true }, at);
    return { el, at, dur };
  };
})();
