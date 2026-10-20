// Demo for library/fx/_demo/{modern,hf}.html?fx=backgrounds/animated-noise-grain.
window.FX_DEMO = function (H, stage) {
  const bar = document.createElement("div");
  bar.style.cssText = "position:absolute;left:160px;top:640px;width:1600px;height:40px;border-radius:20px;background:var(--accent);transform-origin:left center";
  stage.appendChild(bar);
  H.tl.fromTo(bar, { scaleX: 0.1 }, { scaleX: 1, duration: 4.4, ease: "power2.inOut", immediateRender: true }, 0.3);
  const el = document.createElement("div");
  el.textContent = "A little grain on top.";
  el.style.cssText = "position:absolute;left:160px;top:380px;width:1600px;font:800 120px/1.1 var(--head);color:var(--ink)";
  stage.appendChild(el);
  H.tl.fromTo(el, { autoAlpha: 0, y: 30 }, { autoAlpha: 1, y: 0, duration: 0.7, ease: "power3.out", immediateRender: true }, H.at("intro+0.3"));
  FX.animatedNoiseGrain(H, stage, { opacity: 0.2, size: 2, to: 6 });
};
