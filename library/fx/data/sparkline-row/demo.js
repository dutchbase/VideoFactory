// Demo for library/fx/_demo/{modern,hf}.html?fx=data/sparkline-row.
window.FX_DEMO = function (H, stage) {
  const el = document.createElement("div");
  el.style.cssText = "position:absolute;left:160px;top:270px;width:1600px";
  stage.appendChild(el);
  FX.sparklineRow(H, el, {
    at: H.at("intro+0.3"), dur: 1.8, stagger: 0.8,
    rows: [
      { label: "Visits", values: [12, 14, 13, 18, 22, 21, 27], delta: "+18%", unit: "k" },
      { label: "Signups", values: [8, 9, 12, 10, 14, 13, 16], delta: "+12%", color: "green" },
      { label: "Refunds", values: [9, 8, 9, 7, 6, 7, 5], delta: "−9%" },
    ],
  });
};
