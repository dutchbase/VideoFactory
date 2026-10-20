// Motion trail: an element flies in and leaves fading echoes behind it. Rewritten from RemotionUI MotionTrail (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  FX.motionTrail = function (H, el, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at);
    const dur = o.dur == null ? 0.9 : o.dur;
    const fx = o.x == null ? -520 : o.x, fy = o.y == null ? 0 : o.y;            // start offset in px; the element flies to its own place
    const count = Math.max(0, Math.round(o.count == null ? 5 : o.count)), gap = o.gap == null ? 0.06 : o.gap;
    const opacity = o.opacity == null ? 0.45 : o.opacity, falloff = o.falloff == null ? 1.6 : o.falloff;
    const scale = o.scale == null ? 0.82 : o.scale, blur = o.blur == null ? 4 : o.blur, ease = o.ease || "power3.out";
    const parent = el.parentNode;
    const echoes = [];
    for (let i = 0; i < count; i++) {
      const age = (i + 1) / (count + 1), lag = gap * (i + 1);
      const c = el.cloneNode(true);
      c.removeAttribute("id");
      c.querySelectorAll("[id]").forEach(n => n.removeAttribute("id"));
      c.setAttribute("aria-hidden", "true");
      c.classList.add("fx-trail-echo");
      c.style.cssText += ";position:absolute;margin:0;pointer-events:none;z-index:0";
      if (o.color) c.style.color = K.color(o.color);
      parent.insertBefore(c, el);   // behind the real element
      const s = at + lag, vis = opacity * (1 - age) ** falloff;
      const sc = 1 - (1 - scale) * age, fl = `blur(${(blur * age).toFixed(2)}px)`;
      H.tl.fromTo(c, { x: fx, y: fy, scale: sc, filter: fl }, { x: 0, y: 0, scale: sc, filter: fl, duration: dur, ease, immediateRender: true }, s);
      H.tl.fromTo(c, { autoAlpha: 0 }, { autoAlpha: vis, duration: 0.02, ease: "none", immediateRender: true }, s);
      H.tl.fromTo(c, { autoAlpha: vis }, { autoAlpha: 0, duration: 0.2, ease: "power1.out", immediateRender: false }, s + dur * 0.55);
      echoes.push(c);
    }
    // the copies take the box of el; measured now and again when the brand fonts have loaded
    K.layout(() => echoes.forEach(c => {
      c.style.left = el.offsetLeft + "px"; c.style.top = el.offsetTop + "px";
      c.style.width = el.offsetWidth + "px"; c.style.height = el.offsetHeight + "px";
    }));
    H.tl.fromTo(el, { x: fx, y: fy }, { x: 0, y: 0, duration: dur, ease, immediateRender: true }, at);
    H.tl.fromTo(el, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.15, ease: "none", immediateRender: true }, at);
    return { el, echoes, end: at + dur + gap * count };
  };
})();
