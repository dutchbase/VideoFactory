// Shake emphasis: a short impact shake that dies away. Rewritten from RemotionUI ShakeEmphasis (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  FX.shakeEmphasis = function (H, el, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at);
    const dur = o.dur == null ? 0.6 : o.dur;
    const intensity = o.intensity == null ? 14 : o.intensity, rotation = o.rotation == null ? 1.4 : o.rotation;
    const punch = o.punch == null ? 0.05 : o.punch, freq = o.frequency == null ? 22 : o.frequency;
    const decay = o.decay == null ? 2.2 : o.decay, axis = o.axis || "both", seed = o.seed == null ? 1 : o.seed;
    const repeat = Math.max(1, Math.round(o.repeat || 1)), every = o.every == null ? dur + 0.6 : o.every;
    const attack = Math.min(0.04, dur * 0.2);   // starts from rest: a time before `at` is never shaken
    const wave = (t, salt) => K.noise(t * freq, salt, seed) * 2 - 1;
    function draw(p, t) {
      const since = t - at;
      const k = Math.min(repeat - 1, Math.max(0, Math.floor(since / every)));
      const local = since - k * every;
      const x = K.clamp(local / dur);
      const env = since < 0 || local >= dur ? 0 : Math.min(1, local / attack) * (1 - x) ** decay;
      const recoil = since < 0 || local >= dur ? 0 : Math.sin(Math.PI * x) * (1 - x);
      const tt = local + k * 17;   // a different stretch of noise in each repeat
      const dx = axis === "y" ? 0 : wave(tt, 1) * intensity * env, dy = axis === "x" ? 0 : wave(tt, 2) * intensity * env;
      el.style.translate = `${dx.toFixed(2)}px ${dy.toFixed(2)}px`;
      el.style.rotate = (wave(tt, 3) * rotation * env).toFixed(3) + "deg";
      el.style.scale = (1 - punch * env + punch * 0.6 * recoil).toFixed(4);
    }
    const end = at + (repeat - 1) * every + dur;
    draw(0, at);
    H.drive(draw, at, end);
    return { el, at, end };
  };
})();
