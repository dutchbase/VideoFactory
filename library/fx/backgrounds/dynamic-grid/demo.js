// Demo for library/fx/_demo/{modern,hf}.html?fx=backgrounds/dynamic-grid.
window.FX_DEMO = function (H, stage) {
  FX.dynamicGrid(H, stage, { cell: 96, speed: 60, variant: "lines" });
  const el = document.createElement("div");
  el.textContent = "A grid that never stops moving.";
  el.style.cssText = "position:absolute;left:120px;top:42%;width:1100px;font:800 88px/1.1 var(--head);color:var(--ink);z-index:1";
  stage.appendChild(el);
};
