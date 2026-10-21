// Ken Burns: a slow, steady zoom and pan over any element, clipped to its own frame. Rewritten from Onda KenBurns (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  FX.kenBurns = function (H, el, o = {}) {
    const at = H.at(o.at == null ? 0 : o.at), dur = o.dur == null ? 5 : o.dur;
    const s0 = o.fromScale == null ? 1 : o.fromScale, s1 = o.toScale == null ? 1.1 : o.toScale;
    const a = o.from || { x: 0.5, y: 0.5 }, b = o.to || { x: 0.5, y: 0.5 };
    let wrap = null;
    if (o.clip !== false && el.parentNode) {
      // a frame of the same size and place; the zoomed element stays inside it.
      // fx: measure-once (the box of a picture does not depend on fonts; after wrapping, the element fills the frame)
      wrap = document.createElement("div");
      wrap.className = "fx-ken-burns";
      wrap.style.cssText = `left:${el.offsetLeft}px;top:${el.offsetTop}px;width:${el.offsetWidth}px;height:${el.offsetHeight}px`;
      el.parentNode.insertBefore(wrap, el);
      wrap.appendChild(el);
      el.style.position = "absolute"; el.style.left = "0"; el.style.top = "0";
      el.style.width = "100%"; el.style.height = "100%";
    }
    // linear on purpose: an ease reads as a camera that speeds up. The origin moves with the scale, so the view pans.
    H.tl.fromTo(el, { scale: s0, transformOrigin: `${a.x * 100}% ${a.y * 100}%` },
      { scale: s1, transformOrigin: `${b.x * 100}% ${b.y * 100}%`, duration: dur, ease: "none", immediateRender: true }, at);
    return { el, wrap };
  };
})();
