// Demo for library/fx/_demo/{modern,hf}.html?fx=cinematic/camera-shake. One world element is shaken once, at the impact.
window.FX_DEMO = function (H, stage) {
  const world = document.createElement("div");
  world.className = "fx-camera-shake";
  world.style.cssText = "position:absolute;inset:0";
  stage.appendChild(world);
  const mk = (css, text) => {
    const e = document.createElement("div");
    e.textContent = text;
    e.style.cssText = "position:absolute;" + css;
    world.appendChild(e);
    return e;
  };
  mk("left:120px;top:130px;width:1500px;font:800 96px/1.08 var(--head);color:var(--ink)", "One hit, then calm.");
  const block = mk("left:620px;top:560px;width:680px;height:300px;display:flex;align-items:center;justify-content:center;border-radius:28px;" +
    "background:var(--accent);color:var(--cream);font:800 100px/1 var(--head)", "Impact");
  const line = mk("left:120px;top:900px;width:1500px;font:600 56px/1.2 var(--font);color:var(--dim)", "The shake is seeded and fades out by itself.");
  H.tl.fromTo(block, { y: -700 }, { y: 0, duration: 0.45, ease: "power3.in", immediateRender: true }, H.at("point") - 0.25);
  H.tl.fromTo(block, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.01, immediateRender: true }, H.at("point") - 0.25);
  H.tl.fromTo(line, { autoAlpha: 0, y: 12 }, { autoAlpha: 1, y: 0, duration: 0.3, ease: "power3.out", immediateRender: true }, H.at("outro") + 0.2);
  FX.cameraShake(H, world, { at: H.at("point") + 0.2, dur: 0.7, intensity: 22 });
};
