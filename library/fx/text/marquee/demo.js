// Demo for library/fx/_demo/{modern,hf}.html?fx=text/marquee. Two bands run in opposite directions.
window.FX_DEMO = function (H, stage) {
  const band = (top, size) => {
    const el = document.createElement("div");
    el.style.cssText = `position:absolute;left:0;width:1920px;top:${top}px`;
    stage.appendChild(el);
    return el;
  };
  FX.marquee(H, band(300, 140), { at: H.at("intro+0.3"), items: ["Script", "Voice", "Words", "Cues", "Scene", "Render"], size: 140, speed: 170 });
  FX.marquee(H, band(580, 96), { at: H.at("@here"), items: ["Every part moves on the voice", "One call per part"], size: 96, speed: 130, direction: "right", color: "accent" });
};
