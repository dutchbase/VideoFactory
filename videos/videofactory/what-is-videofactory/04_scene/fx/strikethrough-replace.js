// Strikethrough replace: a line strikes out the old phrase, a short hold, then the new phrase takes its place in one frame (cut K10). Rewritten from RemotionUI strikethrough-replace (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  FX.strikethroughReplace = function (H, el, o = {}) {
    const at = H.at(o.at == null ? 0 : o.at);
    const strike = o.strike == null ? 0.3 : o.strike;
    const hold = o.hold == null ? 0.35 : o.hold;
    const swap = at + strike + hold;
    const from = o.from != null ? o.from : el.textContent;
    const align = o.align || "center";
    el.textContent = "";
    el.classList.add("fx-strikethrough-replace");
    el.style.setProperty("--fx-sr-justify", align === "left" ? "start" : align === "right" ? "end" : "center");
    el.style.setProperty("--fx-sr-strike", FX.kit.color(o.strikeColor, "accent"));
    el.style.setProperty("--fx-sr-new", FX.kit.color(o.replaceColor, "ink"));
    el.style.setProperty("--fx-sr-weight", (o.weight == null ? 0.07 : o.weight) + "em");
    el.style.setProperty("--fx-sr-height", (o.height == null ? 0.56 : o.height) + "em");
    el.style.setProperty("--fx-sr-tilt", (o.tilt == null ? -0.6 : o.tilt) + "deg");
    const oldWrap = H.mk("span", "fx-strikethrough-replace-old", el);
    const oldText = H.mk("span", "fx-strikethrough-replace-text", oldWrap, from);
    const tilt = H.mk("span", "fx-strikethrough-replace-tilt", oldText);
    const line = H.mk("span", "fx-strikethrough-replace-line", tilt);
    const newWrap = H.mk("span", "fx-strikethrough-replace-new", el, o.to == null ? "" : o.to);
    H.tl.fromTo(line, { scaleX: 0 }, { scaleX: 1, duration: strike, ease: "power2.inOut", immediateRender: true }, at);
    H.tl.fromTo(oldWrap, { autoAlpha: 1 }, { autoAlpha: 0, duration: 0.001, ease: "none", immediateRender: true }, swap - 0.001);
    H.tl.fromTo(newWrap, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.001, ease: "none", immediateRender: true }, swap - 0.001);
    return { el, swap, end: swap };
  };
})();
