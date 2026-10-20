// Masked slide reveal: words (or lines) slide up out of a line mask. Rewritten from RemotionUI masked-slide-reveal (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  FX.maskedSlideReveal = function (H, el, o = {}) {
    const at = H.at(o.at == null ? 0 : o.at);
    const dur = o.dur == null ? 0.55 : o.dur;
    const stagger = o.stagger == null ? 0.09 : o.stagger;
    const raw = o.lines || (o.text != null ? o.text : el.textContent);
    const lines = Array.isArray(raw) ? raw : String(raw).split("\n").map(s => s.trim()).filter(Boolean);
    const byLines = Array.isArray(raw) || lines.length > 1 || o.by === "lines";
    const items = byLines ? lines : String(raw).trim().split(/\s+/).filter(Boolean);
    const align = o.align || "center";
    el.textContent = "";
    el.classList.add("fx-masked-slide-reveal", byLines ? "fx-masked-slide-reveal-lines" : "fx-masked-slide-reveal-words");
    el.style.setProperty("--fx-msr-align", align === "left" ? "flex-start" : align === "right" ? "flex-end" : "center");
    el.style.setProperty("--fx-msr-gap", (o.gap == null ? 0.28 : o.gap) + "em");
    const inners = items.map(t => {
      const mask = H.mk("span", "fx-masked-slide-reveal-mask", el);
      return H.mk("span", "fx-masked-slide-reveal-item", mask, t);
    });
    inners.forEach((inner, i) => H.tl.fromTo(inner, { yPercent: 135 },
      { yPercent: 0, duration: dur, ease: "power4.out", immediateRender: true }, at + i * stagger));
    return { el, parts: inners, end: at + (items.length - 1) * stagger + dur };
  };
})();
