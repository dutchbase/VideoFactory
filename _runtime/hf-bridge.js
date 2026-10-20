// HyperFrames bridge: brand tokens -> CSS vars, voice cues -> seconds, timelines object.
// Load after brands/<id>/tokens.js, gsap.min.js and 03_cues/cues.js; before scene.js.
(function () {
  // Measured eases for GSAP (ease: Eases.whip). Math from tejashmakwana/motionmaxxing runtime/motion.js (Apache-2.0,
  // licenses/motionmaxxing-Apache-2.0.txt). Twin: P.ease in player.js. Each f(0) = 0, f(1) = 1, clamped outside.
  function clamp01(f) { return function (x) { return x <= 0 ? 0 : x >= 1 ? 1 : f(x); }; }
  function snapOver(A, ta, td) {
    function f(x) { return (1 + A * Math.exp(-x / td)) * (1 - Math.exp(-x / ta)); }
    var n = f(1);
    return function (x) { return f(x) / n; };
  }
  function expoOut(k) { var d = 1 - Math.exp(-k); return function (x) { return (1 - Math.exp(-k * x)) / d; }; }
  window.Eases = {
    crashIn: clamp01(snapOver(2.0, 0.19, 0.218)),
    whip: clamp01(function (x) { return 1 - Math.pow(1 - x, 2.52); }),
    softLand: clamp01(expoOut(3.41)),
    accelExit: clamp01(function (x) { return Math.pow(x, 2.6); })
  };

  var t = window.BrandTokens;
  if (!t) throw new Error('hf-bridge: window.BrandTokens is missing. Load brands/<id>/tokens.js first.');
  var s = document.documentElement.style;
  s.setProperty('--ink', t.ink);
  s.setProperty('--accent', t.ramp[3]);
  s.setProperty('--cream', t.bg);
  s.setProperty('--dim', t.dim);
  s.setProperty('--line', t.line);
  s.setProperty('--green', t.green);
  s.setProperty('--font', t.font);
  s.setProperty('--head', t.head);
  // The Modern kit names too, so a part from library/fx/ looks the same in both engines.
  var more = { bg: t.bg, surface: t.surface, raised: t.raised, faint: t.faint, accent2: t.accent2, danger: t.danger,
    mono: t.mono, hand: t.hand, 'grad-a': t.grads && t.grads[0] && t.grads[0][0], 'grad-b': t.grads && t.grads[0] && t.grads[0][1] };
  for (var k in more) if (more[k]) s.setProperty('--' + k, more[k]);

  // cue('id') -> start second of that cue in 03_cues/cues.js (window.ANIM.cueList).
  window.cue = function (id) {
    var list = (window.ANIM && window.ANIM.cueList) || [];
    for (var i = 0; i < list.length; i++) if (list[i].id === id) return list[i].start;
    throw new Error('hf-bridge: unknown cue "' + id + '". Known: ' + (list.map(function (c) { return c.id; }).join(', ') || 'none (run anim.py cues)'));
  };

  // The HyperFrames runtime reads the paused timeline from window.__timelines[compositionId].
  window.__timelines = window.__timelines || {};
})();
