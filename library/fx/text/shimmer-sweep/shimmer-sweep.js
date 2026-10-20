// Shimmer sweep: one band of colour travels across the text, once or several times, without moving the layout. Rewritten from Onda ShimmerSweep (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  FX.shimmerSweep = function (H, el, o = {}) {
    const at = H.at(o.at == null ? 0 : o.at);
    const dur = o.dur == null ? 0.9 : o.dur;
    const repeat = Math.max(1, o.repeat == null ? 1 : o.repeat);
    const interval = o.interval == null ? 1.6 : o.interval;
    const text = o.text != null ? o.text : el.textContent;
    el.textContent = "";
    el.classList.add("fx-shimmer-sweep");
    el.style.setProperty("--fx-ss-base", FX.kit.color(o.color, "ink"));
    el.style.setProperty("--fx-ss-shine", FX.kit.color(o.shimmerColor, "accent"));
    el.style.setProperty("--fx-ss-angle", (o.angle == null ? 100 : o.angle) + "deg");
    const span = H.mk("span", "fx-shimmer-sweep-text", el, text);
    for (let k = 0; k < repeat; k++) {
      H.tl.fromTo(span, { "--fx-ss-pos": 150 }, { "--fx-ss-pos": -50, duration: dur, ease: "power2.inOut", immediateRender: k === 0 }, at + k * interval);
    }
    return { el, text: span, end: at + (repeat - 1) * interval + dur };
  };
})();
