// Demo for library/fx/_demo/{modern,hf}.html?fx=text/stroke-to-fill-text.
window.FX_DEMO = function (H, stage) {
  const mk = (text, top, size) => {
    const el = document.createElement("div");
    el.textContent = text;
    el.style.cssText = `position:absolute;left:10%;top:${top}%;width:80%;font:800 ${size}px/1.1 var(--head);color:var(--ink)`;
    stage.appendChild(el);
    return el;
  };
  FX.strokeToFillText(H, mk("Every part moves", 26, 120), { at: H.at("intro+0.2") });
  FX.strokeToFillText(H, mk("on the voice.", 52, 96), { at: H.at("@here"), fillColor: "accent", strokeColor: "accent", direction: "right", stagger: 0.05 });
};
