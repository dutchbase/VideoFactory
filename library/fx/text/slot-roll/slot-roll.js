// Slot roll: each character spins through the glyph pool like a reel and lands on the new character, column by column. Rewritten from RemotionUI slot-roll (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  FX.slotRoll = function (H, el, o = {}) {
    const at = H.at(o.at == null ? 0 : o.at);
    const dur = o.dur == null ? 1.0 : o.dur;
    const stagger = o.stagger == null ? 0.08 : o.stagger;
    const spins = o.spins == null ? 2 : o.spins;
    const from = String(o.from != null ? o.from : el.textContent);
    const to = String(o.to != null ? o.to : from);
    const numeric = /^[0-9]+$/.test(from.trim()) && /^[0-9]+$/.test(to.trim());
    const pool = Array.from(o.glyphs || (numeric ? "0123456789" : "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"));
    const len = Math.max(from.length, to.length);
    const a = Array.from(from.padStart(len, " ")), b = Array.from(to.padStart(len, " "));
    el.textContent = "";
    el.classList.add("fx-slot-roll");
    el.style.setProperty("--fx-sl-cell", (o.cell == null ? 0.64 : o.cell) + "em");
    el.style.setProperty("--fx-sl-color", FX.kit.color(o.color, "ink"));
    const cells = a.map(() => H.mk("span", "fx-slot-roll-cell", el));
    const colDur = Math.max(0.1, dur - stagger * (len - 1));
    const show = (cell, ch) => { cell.textContent = ch === " " ? " " : ch; };
    function draw(p, t) {
      const local = t - at;
      cells.forEach((cell, i) => {
        const cp = FX.kit.clamp((local - i * stagger) / colDur);
        if (cp >= 1 || a[i] === b[i]) return show(cell, b[i]);
        if (cp <= 0) return show(cell, a[i]);
        const fi = pool.indexOf(a[i]), ti = pool.indexOf(b[i]);
        if (fi < 0 || ti < 0) return show(cell, cp < 0.5 ? a[i] : b[i]);
        const travel = (spins + (i % 2)) * pool.length + ((ti - fi + pool.length) % pool.length);
        show(cell, pool[Math.floor(fi + travel * (1 - Math.pow(1 - cp, 3))) % pool.length]);
      });
    }
    draw(0, at);
    H.drive(draw, at, at + dur);
    return { el, cells, end: at + dur };
  };
})();
