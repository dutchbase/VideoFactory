// Demo for library/fx/_demo/{modern,hf}.html?fx=data/timeline.
window.FX_DEMO = function (H, stage) {
  const el = document.createElement("div");
  el.style.cssText = "position:absolute;left:160px;top:400px;width:1600px";
  stage.appendChild(el);
  FX.timeline(H, el, {
    at: H.at("intro+0.3"), dur: 3.6,
    points: [{ label: "Plan", sub: "Week 1" }, { label: "Build", sub: "Week 2" }, { label: "Test", sub: "Week 3" }, { label: "Launch", sub: "Week 4" }, { label: "Grow", sub: "Week 5" }],
  });
};
