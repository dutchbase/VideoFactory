// Stat card: a big number counts up, its label follows word by word, an accent rule closes it. Rewritten from Onda StatCard (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  FX.statCard = function (H, el, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at);
    const dur = o.dur == null ? 1.2 : o.dur;
    const value = o.value == null ? 100 : o.value, dec = Math.max(0, o.decimals || 0);
    const nl = o.locale === "nl", group = nl ? "." : ",", point = nl ? "," : ".";
    const fmt = v => {
      const [i, f] = v.toFixed(dec).split(".");
      return (o.separator === false ? i : i.replace(/\B(?=(\d{3})+(?!\d))/g, group)) + (f ? point + f : "");
    };
    el.classList.add("fx-stat-card");
    el.textContent = "";
    const box = H.mk("div", "fx-stat-box", el);
    const num = H.mk("div", "fx-stat-num", box);
    const label = H.mk("div", "fx-stat-label", box, o.label == null ? "" : o.label);
    const rule = o.rule === false ? null : H.mk("div", "fx-stat-rule", box);
    num.style.fontSize = (o.numberSize == null ? 240 : o.numberSize) + "px";
    label.style.fontSize = (o.labelSize == null ? 72 : o.labelSize) + "px";
    if (o.color) num.style.color = K.color(o.color);
    if (rule) rule.style.background = K.color(o.ruleColor, "accent");
    const words = K.split(label, "words", "fx-stat-word");
    const sp = K.spring({ dur, bounce: 0 });
    const draw = (p, t) => {
      const e = p >= 1 ? 1 : sp(p * dur);
      num.textContent = (o.prefix || "") + fmt(value * e) + (o.suffix || "");
    };
    draw(0, at);
    H.tl.fromTo(num, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.2, ease: "power2.out", immediateRender: true }, at);
    H.drive(draw, at, at + dur);
    const ls = at + dur * 0.6, step = 0.08;   // the label starts a beat before the count settles
    words.forEach((w, i) => H.tl.fromTo(w, { autoAlpha: 0, y: 22 }, { autoAlpha: 1, y: 0, duration: 0.45, ease: "power3.out", immediateRender: true }, ls + i * step));
    const end = ls + words.length * step + 0.3;
    if (rule) H.tl.fromTo(rule, { scaleX: 0, transformOrigin: "50% 50%" }, { scaleX: 1, duration: 0.5, ease: "power3.out", immediateRender: true }, end);
    return { el, num, label, end: end + 0.5 };
  };
})();
