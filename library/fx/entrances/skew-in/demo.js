// Demo for library/fx/_demo/{modern,hf}.html?fx=entrances/skew-in. Three words lean in from alternate sides.
window.FX_DEMO = function (H, stage) {
  const mk = (text, top, color) => {
    const el = document.createElement("div");
    el.className = "fx-skew-in";
    el.textContent = text;
    el.style.cssText = `position:absolute;left:160px;top:${top}px;font:800 200px/1 var(--head);color:var(${color})`;
    stage.appendChild(el);
    return el;
  };
  FX.skewIn(H, mk("Write.", 120, "--ink"), { at: H.at("intro+0.3") });
  FX.skewIn(H, mk("Record.", 400, "--accent"), { at: H.at("@here"), direction: "right" });
  FX.skewIn(H, mk("Render.", 680, "--ink"), { at: H.at("@and") });
};
