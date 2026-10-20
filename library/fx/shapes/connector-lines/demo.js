// Demo for library/fx/_demo/{modern,hf}.html?fx=shapes/connector-lines. Four boxes; a solid set of edges, then a dashed set.
window.FX_DEMO = function (H, stage) {
  const node = (x, y, text) => {
    const e = document.createElement("div");
    e.textContent = text;
    e.style.cssText = `position:absolute;left:${x}px;top:${y}px;width:420px;height:170px;display:flex;align-items:center;justify-content:center;` +
      "border-radius:28px;border:3px solid var(--line);background:color-mix(in srgb, var(--ink) 8%, var(--cream));" +
      "font:700 60px/1 var(--head);color:var(--ink);z-index:2";
    stage.appendChild(e);
    return e;
  };
  const a = node(100, 455, "Input");
  const b = node(750, 130, "Parse");
  const c = node(750, 780, "Check");
  const d = node(1400, 455, "Output");
  FX.connectorLines(H, stage, {
    at: H.at("intro+0.3"), color: "accent",
    anchors: [{ id: "a", el: a }, { id: "b", el: b }, { id: "c", el: c }, { id: "d", el: d }],
    edges: [{ from: "a", to: "b", bow: 0.14 }, { from: "a", to: "c", bow: -0.14 }, { from: "b", to: "d", bow: 0.14 }, { from: "c", to: "d", bow: -0.14 }],
  });
  FX.connectorLines(H, stage, {
    at: H.at("point+0.4"), color: "green", dashed: true,
    anchors: [{ id: "b", el: b }, { id: "c", el: c }],
    edges: [{ from: "b", to: "c", shape: "straight", dot: false }],
  });
};
