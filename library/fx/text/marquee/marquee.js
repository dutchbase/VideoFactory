// Marquee: a seamless band of words that scrolls at a steady speed. Rewritten from Onda Marquee (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  FX.marquee = function (H, el, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at);
    const to = o.to == null ? ((window.ANIM && window.ANIM.meta && window.ANIM.meta.duration) || 10) : H.at(o.to);
    const speed = o.speed == null ? 120 : o.speed, dir = o.direction === "right" ? 1 : -1;
    const gap = o.gap == null ? 96 : o.gap, size = o.size == null ? 96 : o.size;
    const items = o.items && o.items.length ? o.items : el.textContent.trim().split(/\s+/).filter(Boolean);
    const dots = o.dots !== false;
    el.classList.add("fx-marquee");
    el.textContent = "";
    el.style.fontSize = size + "px";
    el.style.setProperty("--fx-marquee-gap", gap + "px");
    el.style.setProperty("--fx-marquee-color", K.color(o.color, "ink"));
    const track = H.mk("div", "fx-marquee-track", el);
    const makeSet = () => {
      const set = H.mk("div", "fx-marquee-set", track);
      items.forEach(t => {
        H.mk("span", "fx-marquee-word", set, t);
        if (dots) H.mk("span", "fx-marquee-dot", set);
      });
      return set;
    };
    const first = makeSet();
    // The band must be wider than the frame plus one set, so the wrap never shows. Measured at draw time, so late fonts do not matter.
    function fill(setW, w) {
      const want = Math.min(60, Math.ceil(w / setW) + 2);
      while (track.children.length < want) makeSet();
    }
    function draw(p, t) {
      const setW = first.offsetWidth || 1;
      fill(setW, Math.max(el.clientWidth, K.size(el).w));
      const run = (((Math.max(0, t - at) * speed) % setW) + setW) % setW;
      track.style.transform = `translate3d(${dir < 0 ? -run : run - setW}px,0,0)`;
    }
    H.tl.fromTo(el, { autoAlpha: 0 }, { autoAlpha: 1, duration: o.dur == null ? 0.5 : o.dur, ease: "power3.out", immediateRender: true }, at);
    draw(0, at);
    H.drive(draw, at, to);
    return { el, track };
  };
})();
