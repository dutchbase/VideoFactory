// Demo for library/fx/_demo/{modern,hf}.html?fx=text/handwriting-text. Two lines, the first with a hand-drawn underline.
window.FX_DEMO = function (H, stage) {
  const mk = (text, top, size) => {
    const el = document.createElement("div");
    el.textContent = text;
    el.style.cssText = `position:absolute;left:160px;top:${top}px;font-size:${size}px`;
    stage.appendChild(el);
    return el;
  };
  FX.handwritingText(H, mk("Written by hand.", 300, 160), { at: H.at("intro+0.2"), underline: true });
  FX.handwritingText(H, mk("One letter at a time.", 620, 110), { at: H.at("@here"), seed: 7, penColor: "accent" });
};
