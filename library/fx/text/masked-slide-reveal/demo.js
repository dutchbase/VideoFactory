// Demo for library/fx/_demo/{modern,hf}.html?fx=text/masked-slide-reveal.
window.FX_DEMO = function (H, stage) {
  const mk = (top, size) => {
    const el = document.createElement("div");
    el.style.cssText = `position:absolute;left:10%;top:${top}%;width:80%;font:800 ${size}px/1.12 var(--head);color:var(--ink)`;
    stage.appendChild(el);
    return el;
  };
  const a = mk(22, 92);
  a.textContent = "Every part moves on the voice.";
  FX.maskedSlideReveal(H, a, { at: H.at("intro+0.3"), align: "left" });
  FX.maskedSlideReveal(H, mk(58, 80), { at: H.at("@here"), lines: ["Quick jobs, quietly done,", "begin with one clear step."], align: "left", stagger: 0.18 });
};
