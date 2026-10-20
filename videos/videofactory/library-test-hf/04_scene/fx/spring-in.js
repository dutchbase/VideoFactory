// Spring in: scale and rise on a spring, with snappy, smooth and bouncy presets. Rewritten from RemotionUI SpringIn (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  const PRESETS = { snappy: { dur: 0.4, bounce: 0.12 }, smooth: { dur: 0.65, bounce: 0 }, bouncy: { dur: 0.8, bounce: 0.45 } };
  FX.springIn = function (H, el, o = {}) {
    const at = H.at(o.at == null ? 0 : o.at);
    const cfg = PRESETS[o.config] || PRESETS.snappy;
    const dur = o.dur == null ? cfg.dur : o.dur;
    const sp = FX.kit.spring({ dur, bounce: o.bounce == null ? cfg.bounce : o.bounce });
    const ease = p => (p >= 1 ? 1 : sp(p * dur));
    const from = o.from == null ? 0.88 : o.from, travel = o.travel == null ? 24 : o.travel;
    const side = { up: [0, travel], down: [0, -travel], left: [travel, 0], right: [-travel, 0] }[o.direction || "up"] || [0, travel];
    H.tl.fromTo(el, { scale: from, x: side[0], y: side[1], transformOrigin: o.origin || "50% 50%" },
      { scale: 1, x: 0, y: 0, duration: dur, ease, immediateRender: true }, at);
    H.tl.fromTo(el, { autoAlpha: 0 }, { autoAlpha: 1, duration: Math.min(0.25, dur * 0.5), ease: "power2.out", immediateRender: true }, at);
    return { el, at, dur };
  };
})();
