// Stroke to fill text: outline letters, then a solid fill floods each letter. Rewritten from RemotionUI stroke-to-fill-text (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  FX.strokeToFillText = function (H, el, o = {}) {
    const at = H.at(o.at == null ? 0 : o.at);
    const outlineDur = o.outlineDur == null ? 0.35 : o.outlineDur;
    const fillDelay = o.fillDelay == null ? 0.4 : o.fillDelay;
    const fillDur = o.fillDur == null ? 0.6 : o.fillDur;
    const stagger = o.stagger == null ? 0.04 : o.stagger;
    const soft = Math.max(0, o.softness == null ? 14 : o.softness);
    const sw = o.strokeWidth == null ? 3 : o.strokeWidth;
    const retain = o.retain == null ? 0.35 : o.retain;
    const dirs = { up: "to top", down: "to bottom", left: "to left", right: "to right" };
    if (o.text != null) el.textContent = o.text;
    el.classList.add("fx-stroke-to-fill-text");
    el.style.setProperty("--fx-sf-dir", dirs[o.direction] || dirs.up);
    el.style.setProperty("--fx-sf-soft", soft);
    el.style.setProperty("--fx-sf-stroke", FX.kit.color(o.strokeColor, "ink"));
    el.style.setProperty("--fx-sf-fill", FX.kit.color(o.fillColor, "ink"));
    const parts = o.by === "words" || o.by === "whole" ? FX.kit.split(el, "words", "fx-stroke-to-fill-text-part") : FX.kit.split(el, "chars", "fx-stroke-to-fill-text-part");
    parts.forEach((p, i) => {
      p.setAttribute("data-t", p.textContent);
      const t0 = at + (o.by === "whole" ? 0 : i * stagger);
      H.tl.fromTo(p, { autoAlpha: 0 }, { autoAlpha: 1, duration: outlineDur, ease: "power2.out", immediateRender: true }, at + i * Math.min(stagger, 0.02));
      H.tl.fromTo(p, { "--fx-sf-f": 0, "--fx-sf-sw": sw },
        { "--fx-sf-f": 100 + soft, "--fx-sf-sw": sw * retain, duration: fillDur, ease: "power2.inOut", immediateRender: true }, t0 + fillDelay);
    });
    return { el, parts, end: at + fillDelay + fillDur + (parts.length - 1) * stagger };
  };
})();
