// Demo for library/fx/_demo/{modern,hf}.html?fx=text/matrix-decode.
window.FX_DEMO = function (H, stage) {
  const mk = (text, top, size) => {
    const el = document.createElement("div");
    el.textContent = text;
    el.style.cssText = `position:absolute;left:10%;top:${top}%;width:80%;font:800 ${size}px/1.1 var(--head);color:var(--ink)`;
    stage.appendChild(el);
    return el;
  };
  FX.matrixDecode(H, mk("Every part moves on the voice.", 28, 88), { at: H.at("intro+0.3"), dur: 1.3 });
  FX.matrixDecode(H, mk("Here is the point.", 55, 72), { at: H.at("@here"), dur: 1.0, hotColor: "accent" });
};
