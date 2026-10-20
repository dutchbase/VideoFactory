// Pie reveal: one ring fills clockwise to a percent while the number in the middle counts. Rewritten from Onda PieReveal (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  const NS = "http://www.w3.org/2000/svg";
  const out = x => 1 - Math.pow(1 - Math.min(1, Math.max(0, x)), 4);
  const fmt = (n, d) => { const [i, f] = n.toFixed(d).split("."); return i.replace(/\B(?=(\d{3})+(?!\d))/g, ",") + (f ? "." + f : ""); };
  FX.pieReveal = function (H, el, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at), dur = o.dur == null ? 1.4 : o.dur;
    const max = o.max == null ? 100 : o.max, value = K.clamp(o.value == null ? 72 : o.value, 0, max);
    const size = o.size || 560, th = o.thickness || 56, r = (size - th) / 2, c = size / 2, circ = 2 * Math.PI * r;
    const dec = o.decimals || 0, suffix = o.suffix == null ? "%" : o.suffix;
    const root = H.mk("div", "fx-pie-reveal", el);
    root.style.width = root.style.height = size + "px";
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("class", "fx-pie-reveal-svg");
    svg.setAttribute("viewBox", `0 0 ${size} ${size}`);
    svg.setAttribute("width", size); svg.setAttribute("height", size);
    root.appendChild(svg);
    const ring = (cls, role) => {
      const ci = document.createElementNS(NS, "circle");
      ci.setAttribute("class", cls);
      ci.setAttribute("cx", c); ci.setAttribute("cy", c); ci.setAttribute("r", r);
      ci.setAttribute("fill", "none"); ci.setAttribute("stroke", K.color(role)); ci.setAttribute("stroke-width", th);
      svg.appendChild(ci);
      return ci;
    };
    ring("fx-pie-reveal-track", o.trackColor || "line");
    const arc = ring("fx-pie-reveal-arc", o.color || "accent");
    arc.setAttribute("stroke-linecap", "round");
    const mid = H.mk("div", "fx-pie-reveal-center", root);
    mid.style.fontSize = Math.round(size * 0.2) + "px";
    const num = H.mk("span", "fx-pie-reveal-value", mid);
    const label = o.label ? H.mk("span", "fx-pie-reveal-label", mid, o.label) : null;
    function draw(p) {
      const e = out(p), len = circ * e * value / max;
      arc.setAttribute("stroke-dasharray", `${len.toFixed(2)} ${circ.toFixed(2)}`);
      arc.setAttribute("stroke-opacity", len < 0.5 ? 0 : 1);   // a zero-length round cap would show as a dot
      num.textContent = fmt(e * value, dec) + suffix;
    }
    draw(0);
    H.tl.fromTo(root, { autoAlpha: 0, y: 20 }, { autoAlpha: 1, y: 0, duration: 0.35, ease: "power3.out", immediateRender: true }, at);
    H.drive(draw, at, at + dur);
    return { el, root, value: num, label, arc };
  };
})();
