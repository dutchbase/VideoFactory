// Tracking in: wide letter-spacing collapses to normal while the text sharpens. Rewritten from RemotionUI tracking-in (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  FX.trackingIn = function (H, el, o = {}) {
    const at = H.at(o.at == null ? 0 : o.at);
    const dur = o.dur == null ? 0.8 : o.dur;
    const from = o.from == null ? 0.28 : o.from;
    const blur = o.blur == null ? 6 : o.blur;
    const sp = FX.kit.spring({ dur, bounce: o.bounce == null ? 0 : o.bounce });
    const ease = p => (p >= 1 ? 1 : sp(p * dur));
    el.classList.add("fx-tracking-in");
    H.tl.fromTo(el, { letterSpacing: from + "em", filter: `blur(${blur}px)` },
      { letterSpacing: "0em", filter: "blur(0px)", duration: dur, ease, immediateRender: true }, at);
    H.tl.fromTo(el, { autoAlpha: 0 }, { autoAlpha: 1, duration: dur * 0.6, ease: "power1.out", immediateRender: true }, at);
    return { el, end: at + dur };
  };
})();
