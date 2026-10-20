// Demo for library/fx/_demo/{modern,hf}.html?fx=backgrounds/mesh-gradient. The text is left-aligned, not centred: no centred title on a gradient.
window.FX_DEMO = function (H, stage) {
  FX.meshGradient(H, stage, { colors: ["accent", "line", "dim"], opacity: 0.55 });
  const el = document.createElement("div");
  el.textContent = "Calm colour behind your words.";
  el.style.cssText = "position:absolute;left:120px;bottom:140px;width:900px;font:800 88px/1.1 var(--head);color:var(--ink);z-index:1";
  stage.appendChild(el);
};
