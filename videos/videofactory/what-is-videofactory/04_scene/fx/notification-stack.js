// Notification stack: toasts slide in, stack, and dismiss themselves; the ones below close the gap smoothly. Rewritten from RemotionUI notification-stack (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  const NS = "http://www.w3.org/2000/svg";
  // simple glyphs, drawn with strokes in the tone colour (no logos)
  const GLYPH = {
    success: "M5.5 12.5l4.3 4.3L18.5 7.6",
    error: "M7.4 7.4l9.2 9.2M16.6 7.4l-9.2 9.2",
    warn: "M12 5L21 19.5H3L12 5ZM12 10.5v4",
    info: "M12 11v5.5M12 7.6v.1",
  };
  const TONE = { info: "ink", success: "green", warn: "accent", error: "accent" };
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));

  FX.notificationStack = function (H, el, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at);
    const toasts = o.toasts || [{ title: "Saved", body: "All changes are stored.", tone: "success", meta: "now" }];
    const stagger = o.stagger == null ? 0.7 : o.stagger, life = o.life == null ? 2.2 : o.life, showProgress = o.progress !== false;
    const enterFor = 0.4, leaveFor = 0.35;
    const { w: W, h: Hh } = K.size(el);
    const align = o.align || "top-right", right = align.endsWith("right"), bottom = align.startsWith("bottom");
    const margin = o.margin == null ? 60 : o.margin, width = o.width == null ? 640 : o.width, gap = o.gap == null ? 20 : o.gap;
    const hOne = o.heightOne == null ? 112 : o.heightOne, hTwo = o.heightTwo == null ? 156 : o.heightTwo;
    const sp = K.spring({ dur: enterFor + 0.1, bounce: 0.1 });

    const root = H.mk("div", "fx-notes", el);
    root.style.cssText = `width:${width}px;${right ? "right" : "left"}:${margin}px;${bottom ? "bottom" : "top"}:${margin}px`;
    const items = toasts.map((t, i) => {
      const spawn = at + (t.at == null ? i * stagger : t.at);
      const hold = t.hold == null ? life : t.hold;
      const h = t.body ? hTwo : hOne;
      const tone = t.tone || "info", color = K.color(TONE[tone] || "ink");
      const card = H.mk("div", "fx-note", root);
      card.style.cssText = `height:${h}px;${bottom ? "bottom" : "top"}:0;visibility:hidden;opacity:0`;
      const icon = H.mk("div", "fx-note-icon", card);
      icon.style.cssText = `border-color:${color};color:${color}`;
      const svg = document.createElementNS(NS, "svg");
      svg.setAttribute("viewBox", "0 0 24 24");
      const path = document.createElementNS(NS, "path");
      path.setAttribute("d", GLYPH[tone] || GLYPH.info);
      svg.appendChild(path); icon.appendChild(svg);
      const text = H.mk("div", "fx-note-text", card);
      const row = H.mk("div", "fx-note-row", text);
      H.mk("span", "fx-note-title", row, t.title || "");
      if (t.meta) H.mk("span", "fx-note-meta", row, t.meta);
      if (t.body) H.mk("div", "fx-note-body", text, t.body);
      let bar = null;
      if (showProgress) { bar = H.mk("div", "fx-note-bar", card); bar.style.background = color; }
      return { card, bar, spawn, hold, h };
    });
    const end = Math.max(...items.map(n => n.spawn + n.hold + leaveFor));
    const dir = right ? 1 : -1;

    // every toast is placed from t alone: its slot is the sum of the heights above it, so a dismissal pulls the rest up smoothly
    function draw(p, t) {
      const st = items.map(n => {
        const enter = clamp((t - n.spawn) / enterFor);
        const leave = clamp((t - n.spawn - n.hold) / leaveFor);
        const e = 1 - Math.pow(1 - enter, 3), l = leave * leave * leave;
        return { enter, e, l, occ: e * (1 - l) };
      });
      items.forEach((n, i) => {
        const s = st[i];
        let off = 0;
        for (let j = 0; j < i; j++) off += st[j].occ * (items[j].h + gap);
        const slide = s.enter <= 0 ? 0 : sp(s.enter * (enterFor + 0.1));
        const x = ((1 - slide) * 90 + s.l * 110) * dir, y = (bottom ? -off : off);
        const a = s.e * (1 - s.l);
        n.card.style.visibility = a > 0.001 ? "visible" : "hidden";
        n.card.style.opacity = String(a);
        n.card.style.transform = `translate(${x}px, ${y}px)`;
        if (n.bar) n.bar.style.transform = `scaleX(${1 - clamp((t - n.spawn) / n.hold)})`;
      });
    }
    draw(0, at - 1);
    H.drive(draw, at, end);
    return { el: root, toasts: items.map(n => n.card), end };
  };
})();
