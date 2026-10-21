// SVG mask reveal: any SVG shape grows from a point and uncovers the element. Rewritten from RemotionUI svg-mask-reveal (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  const C = 0.5523;  // bezier circle constant
  // Preset shapes on a 0-100 box, written with absolute M L C Q Z commands only.
  const star = (() => { const p = []; for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + i * Math.PI / 5, r = i % 2 ? 22 : 50; p.push(`${(50 + Math.cos(a) * r).toFixed(2)} ${(50 + Math.sin(a) * r).toFixed(2)}`); } return "M " + p.join(" L ") + " Z"; })();
  const hex = (() => { const p = []; for (let i = 0; i < 6; i++) { const a = Math.PI / 6 + i * Math.PI / 3; p.push(`${(50 + Math.cos(a) * 50).toFixed(2)} ${(50 + Math.sin(a) * 50).toFixed(2)}`); } return "M " + p.join(" L ") + " Z"; })();
  const SHAPES = {
    circle: `M 50 0 C ${50 + 50 * C} 0 100 ${50 - 50 * C} 100 50 C 100 ${50 + 50 * C} ${50 + 50 * C} 100 50 100 C ${50 - 50 * C} 100 0 ${50 + 50 * C} 0 50 C 0 ${50 - 50 * C} ${50 - 50 * C} 0 50 0 Z`,
    diamond: "M 50 0 L 100 50 L 50 100 L 0 50 Z",
    square: "M 0 0 L 100 0 L 100 100 L 0 100 Z",
    hexagon: hex,
    star,
    plus: "M 35 0 L 65 0 L 65 35 L 100 35 L 100 65 L 65 65 L 65 100 L 35 100 L 35 65 L 0 65 L 0 35 L 35 35 Z",
    heart: "M 50 92 C 8 60 0 36 6 22 C 14 4 40 2 50 26 C 60 2 86 4 94 22 C 100 36 92 60 50 92 Z",
  };
  // Parse an absolute path into [{c: 'M'|'L'|'C'|'Q'|'Z', n: [numbers]}]; H and V become L.
  function parse(d) {
    const out = [], re = /([MLHVCQZ])([^MLHVCQZ]*)/gi;
    let cur = [0, 0], m;
    const need = { M: 2, L: 2, H: 1, V: 1, C: 6, Q: 4, Z: 0 };
    while ((m = re.exec(d))) {
      const c = m[1], n = (m[2].match(/-?\d*\.?\d+(?:e-?\d+)?/gi) || []).map(Number);
      if (c !== c.toUpperCase()) throw new Error("svgMaskReveal: use absolute path commands (M L H V C Q Z)");
      const k = need[c];
      for (let i = 0; i === 0 || (k && i + k <= n.length); i += Math.max(k, 1)) {
        let seg = n.slice(i, i + k);
        if (c === "H") seg = [seg[0], cur[1]];
        if (c === "V") seg = [cur[0], seg[0]];
        const cc = c === "H" || c === "V" ? "L" : c === "M" && i > 0 ? "L" : c;
        if (cc !== "Z") cur = seg.slice(-2);
        out.push({ c: cc, n: seg });
        if (!k) break;
      }
    }
    return out;
  }
  // Smallest distance from the box centre to the outline, in box units: how far the shape must grow to cover a frame.
  function inradius(cmds) {
    const pts = []; let cur = [0, 0], start = [0, 0];
    for (const { c, n } of cmds) {
      if (c === "M") { cur = start = n; pts.push(cur); }
      else if (c === "L") { cur = n; pts.push(cur); }
      else if (c === "C" || c === "Q") {
        for (let i = 1; i <= 16; i++) {
          const t = i / 16, u = 1 - t;
          pts.push(c === "C"
            ? [u * u * u * cur[0] + 3 * u * u * t * n[0] + 3 * u * t * t * n[2] + t * t * t * n[4], u * u * u * cur[1] + 3 * u * u * t * n[1] + 3 * u * t * t * n[3] + t * t * t * n[5]]
            : [u * u * cur[0] + 2 * u * t * n[0] + t * t * n[2], u * u * cur[1] + 2 * u * t * n[1] + t * t * n[3]]);
        }
        cur = n.slice(-2);
      } else if (c === "Z") { pts.push(start); cur = start; }
    }
    let best = Infinity;
    for (let i = 1; i < pts.length; i++) {
      const [x1, y1] = pts[i - 1], [x2, y2] = pts[i], dx = x2 - x1, dy = y2 - y1, l2 = dx * dx + dy * dy || 1;
      const t = Math.max(0, Math.min(1, ((50 - x1) * dx + (50 - y1) * dy) / l2));
      best = Math.min(best, Math.hypot(x1 + dx * t - 50, y1 + dy * t - 50));
    }
    return Math.max(best, 1);
  }

  FX.svgMaskReveal = function (H, el, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at), dur = o.dur == null ? 1 : o.dur;
    const W = el.offsetWidth || K.size(el).w, Hh = el.offsetHeight || K.size(el).h;
    const org = o.origin || { x: 0.5, y: 0.5 }, rot = o.rotation || 0, invert = !!o.invert;
    const cx = org.x * W, cy = org.y * Hh;
    const cmds = parse(SHAPES[o.shape || "circle"] || o.shape);
    // scale at which the outline of the shape reaches the far corner, so the shape covers the whole frame at the end
    const reach = Math.max(Math.hypot(cx, cy), Math.hypot(W - cx, cy), Math.hypot(cx, Hh - cy), Math.hypot(W - cx, Hh - cy));
    const full = (reach * 1.02) / inradius(cmds);
    const sp = K.spring({ dur, bounce: 0.2 });
    const ease = o.bouncy ? (p => (p >= 1 ? 1 : sp(p * dur))) : (p => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2));
    function draw(p) {
      const q = invert ? 1 - ease(p) : ease(p), s = q * full, a = (q * rot * Math.PI) / 180, ca = Math.cos(a), sa = Math.sin(a);
      if (!invert && p >= 1) { el.style.clipPath = "none"; return; }
      const f = (x, y) => { const px = (x - 50) * s, py = (y - 50) * s; return `${(cx + px * ca - py * sa).toFixed(1)} ${(cy + px * sa + py * ca).toFixed(1)}`; };
      let d = "";
      for (const { c, n } of cmds) {
        if (c === "Z") { d += "Z "; continue; }
        const pts = []; for (let i = 0; i < n.length; i += 2) pts.push(f(n[i], n[i + 1]));
        d += c + " " + pts.join(" ") + " ";
      }
      el.style.clipPath = `path('${d.trim()}')`;
    }
    draw(0);
    H.drive(draw, at, at + dur);
    return { el };
  };
})();
