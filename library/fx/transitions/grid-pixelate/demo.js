// Demo for library/fx/_demo/{modern,hf}.html?fx=transitions/grid-pixelate. Two full-frame shots; the cells flip before the "point" cue.
window.FX_DEMO = function (H, stage) {
  const shot = (ground, ink, text) => {
    const el = document.createElement("div");
    el.style.cssText = `position:absolute;inset:0;overflow:hidden;background:var(--${ground});color:var(--${ink})`;
    const bar = document.createElement("div");
    bar.style.cssText = "position:absolute;left:120px;top:140px;width:240px;height:24px;background:var(--accent)";
    const line = document.createElement("div");
    line.textContent = text;
    line.style.cssText = "position:absolute;left:120px;right:120px;top:420px;font:800 104px/1.1 var(--head)";
    el.appendChild(bar); el.appendChild(line);
    stage.appendChild(el);
    return el;
  };
  const a = shot("cream", "ink", "Every part moves on the voice.");
  const b = shot("ink", "cream", "Here is the point.");
  FX.gridPixelate(H, a, b, { at: H.at("point-0.6"), cols: 16 });
};
