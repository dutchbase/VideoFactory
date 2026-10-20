// Demo for library/fx/_demo/{modern,hf}.html?fx=cinematic/ken-burns. The "photo" is an inline SVG scene in brand colours: no media is loaded.
window.FX_DEMO = function (H, stage) {
  const NS = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(NS, "svg");
  svg.setAttribute("viewBox", "0 0 1600 760");
  svg.setAttribute("preserveAspectRatio", "xMidYMid slice");
  svg.style.cssText = "width:100%;height:100%;display:block";
  const photo = document.createElement("div");
  photo.style.cssText = "position:absolute;left:160px;top:80px;width:1600px;height:760px";
  photo.appendChild(svg);
  const add = (tag, attrs) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); svg.appendChild(e); return e; };
  add("rect", { x: 0, y: 0, width: 1600, height: 760, style: "fill:color-mix(in srgb, var(--ink) 12%, var(--cream))" });
  add("circle", { cx: 1180, cy: 230, r: 110, style: "fill:var(--accent)" });
  add("path", { d: "M0 520 C 250 380 420 380 640 500 C 860 330 1060 330 1260 470 C 1400 400 1500 410 1600 450 L1600 760 L0 760 Z", style: "fill:var(--dim);opacity:.55" });
  add("path", { d: "M0 600 C 260 500 520 520 760 610 C 1000 520 1300 520 1600 620 L1600 760 L0 760 Z", style: "fill:var(--green);opacity:.8" });
  add("path", { d: "M0 690 C 400 640 900 650 1600 700 L1600 760 L0 760 Z", style: "fill:var(--cream)" });
  [[300, 560, 90], [420, 590, 60], [1330, 585, 80]].forEach(([x, y, h]) => add("path", { d: `M${x} ${y} L${x - h * 0.32} ${y + h} L${x + h * 0.32} ${y + h} Z`, style: "fill:var(--cream)" }));
  stage.appendChild(photo);
  const cap = document.createElement("div");
  cap.textContent = "A slow drift over any picture.";
  cap.style.cssText = "position:absolute;left:160px;top:880px;width:1600px;font:800 80px/1.1 var(--head);color:var(--ink)";
  stage.appendChild(cap);
  FX.kenBurns(H, photo, { at: 0.2, dur: 5.6, fromScale: 1, toScale: 1.3, from: { x: 0.25, y: 0.7 }, to: { x: 0.75, y: 0.3 } });
};
