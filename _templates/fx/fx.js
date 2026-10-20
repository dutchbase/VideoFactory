// <Title>: <one line>. Rewritten from <source> <upstream name> (MIT, see block.md). Rules: library/fx/CONTEXT.md.
(function () {
  const FX = window.FX = window.FX || {};
  FX.<camelId> = function (H, el, o = {}) {
    const at = H.at(o.at == null ? 0 : o.at);
    const dur = o.dur == null ? 0.7 : o.dur;
    H.tl.fromTo(el, { autoAlpha: 0 }, { autoAlpha: 1, duration: dur, ease: "power3.out", immediateRender: true }, at);
    return { el, at };
  };
})();
