// Callout: a label box that points at one spot; the box lands first, then the line draws to the anchor. Rewritten from Onda Callout (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  const NS = "http://www.w3.org/2000/svg";
  function box(e, root) {
    let x = 0, y = 0, n = e;
    while (n && n !== root) { x += n.offsetLeft; y += n.offsetTop; n = n.offsetParent; }
    return { x, y, w: e.offsetWidth, h: e.offsetHeight };
  }
  // First point where the segment P -> C enters rect r (C when P is already inside).
  function enter(px, py, cx, cy, r) {
    let t0 = 0, t1 = 1;
    const dx = cx - px, dy = cy - py;
    for (const [p, d, lo, hi] of [[px, dx, r.x, r.x + r.w], [py, dy, r.y, r.y + r.h]]) {
      if (Math.abs(d) < 1e-9) { if (p < lo || p > hi) return { x: cx, y: cy }; continue; }
      let a = (lo - p) / d, b = (hi - p) / d;
      if (a > b) [a, b] = [b, a];
      t0 = Math.max(t0, a); t1 = Math.min(t1, b);
    }
    return t0 > t1 ? { x: cx, y: cy } : { x: px + dx * t0, y: py + dy * t0 };
  }

  FX.callout = function (H, el, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at), dur = o.dur == null ? 0.5 : o.dur;
    const lineDelay = o.lineDelay == null ? 0.3 : o.lineDelay, lineDur = o.lineDur == null ? 0.5 : o.lineDur;
    const offset = o.offset == null ? 170 : o.offset, margin = o.margin == null ? 60 : o.margin, gap = o.gap == null ? 20 : o.gap;
    const col = K.color(o.color || "accent");
    if (getComputedStyle(el).position === "static") el.style.position = "relative";
    const tgt = typeof o.target === "string" ? document.querySelector(o.target) : o.target;
    const pos = o.position || "top-right";
    const sx = pos.endsWith("right") ? 1 : -1, sy = pos.startsWith("bottom") ? 1 : -1;

    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("class", "fx-callout-svg");
    el.appendChild(svg);
    const bubble = document.createElement("div");
    bubble.className = "fx-callout";
    bubble.textContent = o.label == null ? "Look here" : o.label;
    bubble.style.cssText = `font-size:${o.size == null ? 52 : o.size}px;border-color:${col}`;
    el.appendChild(bubble);
    const path = document.createElementNS(NS, "path");
    path.setAttribute("class", "fx-callout-line");
    path.setAttribute("pathLength", "1");
    path.style.cssText = `stroke:${col};stroke-width:${o.lineWidth == null ? 5 : o.lineWidth}px;stroke-dasharray:1 2`;
    const dot = document.createElementNS(NS, "circle");
    dot.setAttribute("class", "fx-callout-dot");
    dot.setAttribute("r", 11);
    dot.style.fill = col;
    svg.appendChild(path); svg.appendChild(dot);
    const anchor = { x: 0, y: 0 };

    // Every size comes from the page: measured again once the fonts have loaded.
    K.layout(() => {
      const W = el.offsetWidth || K.size(el).w, Hh = el.offsetHeight || K.size(el).h;
      const tb = tgt ? box(tgt, el) : null;
      const ax = tb ? tb.x + tb.w / 2 : (o.x == null ? W / 2 : o.x), ay = tb ? tb.y + tb.h / 2 : (o.y == null ? Hh / 2 : o.y);
      anchor.x = ax; anchor.y = ay;
      svg.setAttribute("viewBox", `0 0 ${W} ${Hh}`);
      const bw = bubble.offsetWidth, bh = bubble.offsetHeight;
      // the box sits `offset` px beyond the target's corner (beyond the point when there is no target), inside the margin
      const hw = tb ? tb.w / 2 : 0, hh = tb ? tb.h / 2 : 0;
      const bx = Math.min(W - margin - bw / 2, Math.max(margin + bw / 2, ax + sx * (hw + offset * 1.3)));
      const by = Math.min(Hh - margin - bh / 2, Math.max(margin + bh / 2, ay + sy * (hh + offset)));
      bubble.style.left = bx + "px"; bubble.style.top = by + "px";
      // the line runs from the edge of the box to the edge of the target (or to the anchor point)
      const s = enter(ax, ay, bx, by, { x: bx - bw / 2, y: by - bh / 2, w: bw, h: bh });
      const e = tb ? enter(bx, by, ax, ay, { x: tb.x - gap, y: tb.y - gap, w: tb.w + 2 * gap, h: tb.h + 2 * gap }) : { x: ax, y: ay };
      path.setAttribute("d", `M ${s.x} ${s.y} L ${e.x} ${e.y}`);
      dot.setAttribute("cx", e.x); dot.setAttribute("cy", e.y);
    });

    const sp = K.spring({ dur, bounce: 0 });
    const ease = p => (p >= 1 ? 1 : sp(p * dur));
    H.tl.fromTo(bubble, { autoAlpha: 0, scale: 0.92, xPercent: -50, yPercent: -50 },
      { autoAlpha: 1, scale: 1, xPercent: -50, yPercent: -50, duration: dur, ease, immediateRender: true }, at);
    const t1 = at + lineDelay;
    H.tl.fromTo(path, { strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: lineDur, ease: "power2.inOut", immediateRender: true }, t1);
    H.tl.fromTo(dot, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.15, ease: "none", immediateRender: true }, t1 + lineDur * 0.85);
    if (o.exitAt != null) H.tl.to([bubble, path, dot], { autoAlpha: 0, duration: o.exitDur == null ? 0.25 : o.exitDur, ease: "power2.in", immediateRender: false }, H.at(o.exitAt));
    return { el: bubble, svg, anchor };
  };
})();
