// Demo for library/fx/_demo/{modern,hf}.html?fx=data/donut-chart.
window.FX_DEMO = function (H, stage) {
  const box = (left, top, w) => {
    const el = document.createElement("div");
    el.style.cssText = `position:absolute;left:${left}px;top:${top}px;width:${w}px`;
    stage.appendChild(el);
    return el;
  };
  FX.donutChart(H, box(360, 280, 1200), {
    at: H.at("intro+0.3"), dur: 3.4, totalLabel: "Total", unit: "",
    segments: [{ label: "Design", value: 420 }, { label: "Build", value: 310 }, { label: "Test", value: 180 }, { label: "Ship", value: 90 }],
  });
  const note = document.createElement("div");
  note.textContent = "Parts of one whole.";
  note.style.cssText = "position:absolute;left:360px;top:880px;font:800 72px/1.1 var(--head);color:var(--ink)";
  stage.appendChild(note);
  H.tl.fromTo(note, { autoAlpha: 0, y: 24 }, { autoAlpha: 1, y: 0, duration: 0.5, ease: "power3.out", immediateRender: true }, H.at("@here"));
};
