// Demo for library/fx/_demo/{modern,hf}.html?fx=data/comparison-bars.
window.FX_DEMO = function (H, stage) {
  const box = (top) => {
    const el = document.createElement("div");
    el.style.cssText = `position:absolute;left:160px;top:${top}px;width:1600px`;
    stage.appendChild(el);
    return el;
  };
  FX.comparisonBars(H, box(280), {
    at: H.at("intro+0.3"), dur: 1.6, stagger: 0.7, unit: "",
    rows: [{ label: "Speed", before: 40, after: 68 }, { label: "Quality", before: 55, after: 82 }, { label: "Cost", before: 90, after: 60 }],
  });
};
