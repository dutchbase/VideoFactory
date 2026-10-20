// RGB glitch text: two colour copies ride just off the text and burst wider now and then, then the text settles clean. Rewritten from Onda RgbGlitchText (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  FX.rgbGlitchText = function (H, el, o = {}) {
    const at = H.at(o.at == null ? 0 : o.at);
    const dur = o.dur == null ? 2.4 : o.dur;
    const base = o.split == null ? 0.02 : o.split;
    const power = o.intensity == null ? 0.07 : o.intensity;
    const period = o.period == null ? 0.8 : o.period;
    const burst = o.burst == null ? 0.2 : o.burst;
    const rate = o.rate == null ? 12 : o.rate;
    const seed = o.seed == null ? 7 : o.seed;
    const text = o.text != null ? o.text : el.textContent;
    el.textContent = "";
    el.classList.add("fx-rgb-glitch-text");
    el.style.setProperty("--fx-rg-a", FX.kit.color(o.colorA, "accent"));
    el.style.setProperty("--fx-rg-b", FX.kit.color(o.colorB, "green"));
    el.style.setProperty("--fx-rg-main", FX.kit.color(o.color, "ink"));
    const wrap = H.mk("span", "fx-rgb-glitch-text-wrap", el);
    const la = H.mk("span", "fx-rgb-glitch-text-a", wrap, text);
    const lb = H.mk("span", "fx-rgb-glitch-text-b", wrap, text);
    H.mk("span", "fx-rgb-glitch-text-main", wrap, text);
    la.setAttribute("aria-hidden", "true");
    lb.setAttribute("aria-hidden", "true");
    function draw(p, t) {
      const local = t - at;
      if (local >= dur || local < 0) { la.style.display = lb.style.display = "none"; return; }
      la.style.display = lb.style.display = "block";
      const inBurst = local < burst || local % period < burst;
      const r = FX.kit.rand(seed + Math.floor(local * rate) * 7919);
      const k = inBurst ? r() * 2 - 1 : 0;
      const dx = base + k * power, dy = inBurst ? (r() * 2 - 1) * power * 0.4 : 0;
      la.style.transform = `translate(${-dx}em, ${-dy}em)`;
      lb.style.transform = `translate(${dx}em, ${dy}em)`;
    }
    draw(0, at);
    H.tl.fromTo(el, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.001, ease: "none", immediateRender: true }, Math.max(0, at - 0.001));
    H.drive(draw, at, at + dur);
    return { el, end: at + dur };
  };
})();
