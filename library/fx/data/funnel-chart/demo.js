// Demo for library/fx/_demo/{modern,hf}.html?fx=data/funnel-chart.
window.FX_DEMO = function (H, stage) {
  const el = document.createElement("div");
  el.style.cssText = "position:absolute;left:160px;top:200px;width:1600px";
  stage.appendChild(el);
  FX.funnelChart(H, el, {
    at: H.at("intro+0.3"), dur: 1.1, stagger: 0.9,
    stages: [{ label: "Visits", value: 12000 }, { label: "Signups", value: 4800 }, { label: "Trials", value: 1900 }, { label: "Customers", value: 640 }],
  });
};
