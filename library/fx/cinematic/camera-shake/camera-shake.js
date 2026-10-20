// Camera shake: a short, seeded shake that decays to rest. Rewritten from Onda CameraShake (MIT, see block.md).
(function () {
  const FX = window.FX = window.FX || {};
  FX.cameraShake = function (H, el, o = {}) {
    const K = FX.kit;
    const at = H.at(o.at == null ? 0 : o.at), dur = o.dur == null ? 0.6 : o.dur;
    const amp = o.intensity == null ? 14 : o.intensity, rot = o.rotate == null ? 0.5 : o.rotate;
    const rate = o.rate == null ? 20 : o.rate, seed = o.seed == null ? 1 : o.seed, decay = o.decay == null ? 2 : o.decay;
    // two octaves of seeded value noise per axis, in -1..1: smooth like a handheld camera, never a random jump
    const n = (k, t) => (K.noise(t * rate, k * 7.3, seed * 31 + k) + 0.5 * K.noise(t * rate * 2.3, k * 3.1 + 40, seed * 31 + k + 9) - 0.75) / 0.75;
    function draw(p, t) {
      // no shake before the start or after the end: the transform is removed, so the element is exactly as it was
      if (p <= 0 || p >= 1) { window.gsap.set(el, { clearProps: "transform" }); return; }
      const t0 = t - at, env = Math.pow(1 - p, decay);
      window.gsap.set(el, { x: n(1, t0) * amp * env, y: n(2, t0) * amp * env, rotation: n(3, t0) * rot * env });
    }
    H.drive(draw, at, at + dur);
    return { el, at, end: at + dur };
  };
})();
