// Underline: the text snaps in, then an accent line draws under it after a short beat. Rewritten from Onda Underline (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  FX.underline = function (H, el, o = {}) {
    const at = H.at(o.at == null ? 0 : o.at);
    const dur = o.dur == null ? 0.25 : o.dur;
    const lineDelay = o.lineDelay == null ? 0.3 : o.lineDelay;
    const lineDur = o.lineDur == null ? 0.5 : o.lineDur;
    const rise = o.rise == null ? 24 : o.rise;
    const text = o.text != null ? o.text : el.textContent;
    el.textContent = "";
    el.classList.add("fx-underline");
    el.style.setProperty("--fx-ul-color", FX.kit.color(o.lineColor, "accent"));
    el.style.setProperty("--fx-ul-thick", (o.thickness == null ? 0.08 : o.thickness) + "em");
    el.style.setProperty("--fx-ul-off", (o.offset == null ? 0.04 : o.offset) + "em");
    const label = H.mk("span", "fx-underline-text", el, text);
    const line = H.mk("span", "fx-underline-line", label);
    H.tl.fromTo(label, { autoAlpha: 0, y: rise }, { autoAlpha: 1, y: 0, duration: dur, ease: "power4.out", immediateRender: true }, at);
    H.tl.fromTo(line, { scaleX: 0 }, { scaleX: 1, duration: lineDur, ease: "power3.out", immediateRender: true }, at + lineDelay);
    return { el, text: label, line, end: at + lineDelay + lineDur };
  };
})();
