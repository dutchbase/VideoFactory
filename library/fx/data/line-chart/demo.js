// Demo for library/fx/_demo/{modern,hf}.html?fx=data/line-chart.
window.FX_DEMO = function (H, stage) {
  const el = document.createElement("div");
  el.style.cssText = "position:absolute;left:210px;top:210px;width:1500px";
  stage.appendChild(el);
  FX.lineChart(H, el, {
    at: H.at("intro+0.3"), dur: 3.6, unit: "k",
    values: [12, 18, 15, 24, 31, 28, 40], labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"],
  });
};
