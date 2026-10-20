// Demo for library/fx/_demo/{modern,hf}.html?fx=entrances/orbit-motion. Five chips orbit a title.
window.FX_DEMO = function (H, stage) {
  const title = document.createElement("div");
  title.textContent = "Pipeline";
  title.style.cssText = "position:absolute;left:560px;width:800px;top:430px;text-align:center;font:800 150px/1.1 var(--head);color:var(--ink);z-index:10";
  stage.appendChild(title);
  const ring = document.createElement("div");
  ["Script", "Voice", "Words", "Cues", "Scene"].forEach(t => {
    const chip = document.createElement("div");
    chip.textContent = t;
    chip.style.cssText = "padding:14px 36px;border:5px solid var(--accent);border-radius:999px;background:var(--cream);font:800 72px/1.1 var(--head);color:var(--ink)";
    ring.appendChild(chip);
  });
  stage.appendChild(ring);
  FX.orbitMotion(H, ring, { at: H.at("intro+0.3"), showPath: true, radiusX: 600, radiusY: 250, period: 7 });
};
