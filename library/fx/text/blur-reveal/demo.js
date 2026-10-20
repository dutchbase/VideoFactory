// Demo for library/fx/_demo/{modern,hf}.html?fx=text/blur-reveal.
window.FX_DEMO = function (H, stage) {
  const mk = (text, top, size) => {
    const el = document.createElement("div");
    el.textContent = text;
    el.style.cssText = `position:absolute;left:10%;top:${top}%;width:80%;font:800 ${size}px/1.1 var(--head);color:var(--ink)`;
    stage.appendChild(el);
    return el;
  };
  FX.blurReveal(H, mk("Every part moves on the voice.", 30, 96), { at: H.at("intro+0.3") });
  FX.blurReveal(H, mk("Word by word, when you need it.", 55, 64), { at: H.at("@here"), by: "words" });
};
