// A row of accent chips with a check mark, snapping in one after another.
(function () {
  window.Blocks = window.Blocks || {};
  const TICK = '<svg viewBox="0 0 24 24"><path d="M4 12l5 5L20 6"/></svg>';
  window.Blocks.checklist = function (H, root, o) {
    const el = H.mk("div", "b-ticks", root);
    const items = o.items.map(t => {
      const s = H.mk("span", "b-tick b-hide", el);
      s.innerHTML = TICK;
      s.appendChild(document.createTextNode(t));
      return s;
    });
    return { el, items, show(at, step = 0.12) { items.forEach((s, i) => H.snap(s, at + i * step, { y: 20 }, 0.12)); } };
  };
})();
