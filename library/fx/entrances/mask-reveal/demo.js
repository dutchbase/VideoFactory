// Demo for library/fx/_demo/{modern,hf}.html?fx=entrances/mask-reveal. Three lines, three directions.
window.FX_DEMO = function (H, stage) {
  const mk = (text, top, size, color) => {
    const el = document.createElement("div");
    el.className = "fx-mask-reveal";
    el.textContent = text;
    el.style.cssText = `position:absolute;left:160px;top:${top}px;font:800 ${size}px/1.1 var(--head);color:var(${color})`;
    stage.appendChild(el);
    return el;
  };
  FX.maskReveal(H, mk("The edge stays sharp.", 220, 140, "--ink"), { at: H.at("intro+0.3"), direction: "left" });
  FX.maskReveal(H, mk("Nothing fades.", 480, 120, "--accent"), { at: H.at("@here"), direction: "bottom" });
  FX.maskReveal(H, mk("It just uncovers.", 720, 120, "--ink"), { at: H.at("@and"), direction: "right" });
};
