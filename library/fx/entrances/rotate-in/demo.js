// Demo for library/fx/_demo/{modern,hf}.html?fx=entrances/rotate-in.
window.FX_DEMO = function (H, stage) {
  const mk = (text, top, size) => {
    const el = document.createElement("div");
    el.textContent = text;
    el.style.cssText = `position:absolute;left:160px;top:${top}px;width:1600px;font:800 ${size}px/1.1 var(--head);color:var(--ink)`;
    stage.appendChild(el);
    return el;
  };
  FX.rotateIn(H, mk("Every part moves.", 250, 160), { at: H.at("intro+0.3") });
  FX.rotateIn(H, mk("Word by word, on the voice.", 520, 96), { at: H.at("@here"), by: "words", angle: 10 });
  FX.rotateIn(H, mk("And done.", 740, 96), { at: H.at("@and"), origin: "0% 100%" });
};
