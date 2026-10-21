// scene.js - timed parts of the VideoFactory showcase that HTML attributes cannot say. Guide: _shared/modern.md.
// A time is a cue id ('hook'), a cue with an offset ('hook+0.4'), a spoken word ('@money'), or seconds (2.5).
const tl = P.timeline();
const at = Modern.at;
const T = window.BrandTokens;
const words = (window.ANIM && window.ANIM.words) || [];
const $ = (s) => document.querySelector(s);
const between = (a, b) => words.filter((w) => w.start >= at(a) - 0.01 && w.start < at(b) - 0.01);
const clock = (s) => `${Math.floor(s / 60)}:${(s % 60).toFixed(2).padStart(5, '0')}`;

// hook: "a timeline" lifts its card; the three tools get struck through and sink on "a lost weekend".
tl.to('[data-cue="hook"] .tool:nth-child(2)', { y: -22, borderColor: T.accent, duration: 0.35, ease: P.ease.pop }, at('@timeline'));
tl.to('[data-cue="hook"] .tool b', { '--strike': 1, duration: 0.35, ease: P.ease.move, stagger: 0.1 }, at('hook.weekend'));
tl.to('[data-cue="hook"] .tool', { y: 26, rotate: (i) => [-4, 3, -2][i], opacity: 0.45, duration: 0.6, ease: P.ease.out, stagger: 0.06 },
  at('hook.weekend+0.35'));

// turn: the struck tools fold into one chat.
tl.fromTo('.fold .tool', { x: 0, scale: 1, opacity: 0.45 },
  { x: (i) => [364, 0, -364][i], scale: 0.4, opacity: 0, duration: 0.55, ease: P.ease.exit }, at('turn+0.1'));
Modern.in(tl, '.chat', 'turn+0.4', 'pop');
Modern.in(tl, '.chat .bubble', 'turn+0.6', 'rise', { stagger: 0.4 });

// what: each stage gets its check mark, one by one.
Modern.in(tl, '.stage .ck', 'what.check+0.5', 'pop', { stagger: 0.3 });

// setup, /vf and new video: the terminals type their command.
Modern.type('#t-setup', 'setup.type+0.2', { cps: 14 });
Modern.type('#t-vf', 'vf.type+0.1', { cps: 10 });
Modern.type('#t-video', 'video+0.3', { cps: 18 });
Modern.type('#t-status', 'status+0.1', { cps: 16 });

// optional: each card lights up when the voice names it.
const light = (sel, when, stagger = 0) => {
  tl.fromTo(sel, { '--lit': 0 }, { '--lit': 1, duration: 0.45, ease: P.ease.out, stagger }, at(when));
  tl.fromTo(sel, { scale: 1 }, { scale: 1.07, duration: 0.18, ease: P.ease.out, yoyo: true, repeat: 1, stagger }, at(when));
};
light('#o-whisper', 'optional.whisper');
light('#o-eleven', 'optional.eleven');
light('.o-stock', 'optional.stock', 0.35);
light('#o-earshot', 'optional.earshot');
light('#o-node', 'optional.node');
light('#o-form', 'optional.form');
// The panel beside the grid says what the named part does; it swaps when the voice names the next one.
const spots = [...document.querySelectorAll('[data-spot]')];
spots.forEach((el, i) => {
  if (i) Modern.in(tl, el, `${el.dataset.spot}+0.05`, 'rise');   // the first panel is the headline; its words enter by data-in
  if (spots[i + 1]) Modern.out(tl, el, `${spots[i + 1].dataset.spot}-0.3`, 'sink');
});
Modern.in(tl, '#photos img', 'optional.photos+0.1', 'rise', { stagger: 0.14 });
Modern.in(tl, '#bf-url', 'optional.browser', 'rise');
// Whisper: a real word of this video with the time Whisper gave it.
const first = words.find((w) => /explainer/i.test(w.text));
if (first) {
  $('#spot-word b').textContent = first.text;
  $('#spot-word small').textContent = clock(first.start);
}

// Earshot: a live level meter while the voice names it.
const meter = $('#meter');
const bars = Array.from({ length: 18 }, () => meter.appendChild(document.createElement('i')));
P.onFrame((t) => bars.forEach((b, i) => {
  const v = 0.18 + 0.82 * Math.abs(Math.sin(t * 5.3 + i * 0.7) * Math.sin(t * 2.1 + i * 0.31));
  b.style.height = `${(v * 100).toFixed(1)}%`;
}));

// brand: the swatch labels come from the brand tokens; stamps land batch by batch.
Modern.in(tl, '.stamp', 'brand.approve', 'zoom', { stagger: 0.22 });

Modern.type('#t-research', 'research+0.5', { cps: 16 });
Modern.type('#t-transcript', 'transcript+0.1', { cps: 18 });

// research: the captured page scrolls slowly while the voice talks about it.
const research = $('#research-img');
P.onFrame(() => {
  research.style.transform = `translateY(${-520 * P.prog('research.web', { dur: 5, ease: P.ease.sine })}px)`;
});

// script: the tone check strikes the hype line.
Modern.in(tl, '#bad', 'script.tone+0.2', 'rise');
tl.fromTo('#bad', { '--strike': 0 }, { '--strike': 1, duration: 0.4, ease: P.ease.move }, at('script.tone+0.9'));

// voice: a live wave for the AI voice; the photo drifts.
const vwave = $('#vwave'), mic = $('#mic');
P.onFrame((t) => {
  let d = '';
  for (let x = 0; x <= 600; x += 6) {
    const env = Math.sin(Math.PI * x / 600);
    const y = 100 + env * 70 * Math.sin(x / 19 + t * 7) * Math.sin(x / 53 - t * 2.3);
    d += `${x ? 'L' : 'M'}${x} ${y.toFixed(1)}`;
  }
  vwave.setAttribute('d', d);
  $('#owave').setAttribute('d', d.replace(/ (\d+(\.\d+)?)/g, (m, y) => ` ${(y * 0.75).toFixed(1)}`));
  mic.style.transform = `scale(${1.04 + 0.08 * P.prog('voice.free', { dur: 9, ease: P.ease.sine })})`;
});

// voice.approve: scroll the real review page down to its Approved bar, then one camera move onto that bar.
// The image origin is the bar (465, 815); the move brings it to the middle of the 1360 x 560 view.
const review = $('#review-img');
P.onFrame(() => {
  const s = P.prog('voice.approve', { delay: 0.6, dur: 1.8, ease: P.ease.inOut });
  const z = P.prog('voice.stamp', { delay: 0.1, dur: 1.4, ease: P.ease.inOut });
  const x = 215 * z, y = -370 * s + (-535 + 370) * z;
  review.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px) scale(${P.zoom(1, 3, z).toFixed(4)})`;
});

// transcript: the real words of this sentence, each with its time, light up when spoken.
const wordBox = $('#words');
for (const w of between('transcript', 'cues')) {
  const el = document.createElement('div');
  el.className = 'word';
  el.innerHTML = `<b></b><small>${clock(w.start)}</small>`;
  el.querySelector('b').textContent = w.text.replace(/[.,]$/, '');
  wordBox.appendChild(el);
  tl.to(el.querySelector('b'), { color: T.ink, duration: 0.15 }, w.start);
  tl.to(el, { borderColor: T.accent, duration: 0.15 }, w.start);
}
Modern.in(tl, '#words .word', 'transcript+0.05', 'rise', { stagger: 0.04 });
tl.to('#words small', { backgroundColor: T.accent, color: T.bg, duration: 0.2, stagger: 0.04 }, at('transcript.exact'));

// cues: words on a time line, a moving play head, and the two cue markers that snap onto their words.
const track = $('#track'), span = [at('cues'), at('scene')];
const xOf = (s) => 1500 * (s - span[0]) / (span[1] - span[0]);
for (const w of between('cues', 'scene')) {
  const tick = document.createElement('i'); tick.className = 'tick'; tick.style.left = `${xOf(w.start)}px`;
  const lab = document.createElement('span'); lab.className = 'tw'; lab.style.left = `${xOf(w.start) + 2}px`;
  lab.textContent = w.text.replace(/[.,]$/, '');
  track.append(tick, lab);
}
// Only every other word gets a label, so the labels never touch.
[...track.querySelectorAll('.tw')].forEach((el, i) => { if (i % 2) el.remove(); });
for (const [id, off] of [['cues', 260], ['cues.change', -300]]) {
  const mk = document.createElement('div'); mk.className = 'mk';
  mk.innerHTML = `<i></i><span>${id}</span>`;
  mk.style.left = `${xOf(at(id))}px`;
  track.appendChild(mk);
  tl.fromTo(mk, { x: off, opacity: 0.35 }, { x: 0, opacity: 1, duration: 0.5, ease: P.ease.pop }, at('cues.change+0.15'));
}
const head = document.createElement('div');
head.style.cssText = 'position:absolute;top:120px;width:4px;height:120px;border-radius:2px;background:var(--accent2)';
track.appendChild(head);
P.onFrame((t) => { head.style.left = `${P.clamp((t - span[0]) / (span[1] - span[0])) * 1500}px`; });

// library: a Lottie animation from the library, in brand colours, on a loop.
const chart = Lib.lottie('growth-chart', { colors: 'brand' });
const lc = $('#lottie').getContext('2d');
P.onFrame((t) => {
  lc.clearRect(0, 0, 1040, 1040);
  if (chart.ready) chart.at(lc, t - at('scene.library'), 520, 520, 860, 860, { loop: true });
});

// stock, capture and motion: real clips on the scene clock.
Modern.clip('#stock-clip', 'timeline', 'scene.stock');
Modern.clip('#rec-clip', 'browser-search', 'scene.capture-1.2', { speed: 1.3 });
Modern.clip('#motion-clip', 'agent-flow', 'scene.motion', { speed: 1.4, from: 0.8 });
Modern.clip('#player-clip', 'player', 'render', { from: 1.2 });

// sound: four effect shapes that keep moving.
const fx = [...document.querySelectorAll('.fxw')];
P.onFrame((t) => {
  for (const p of fx) {
    const k = +p.dataset.k;
    let d = '';
    for (let x = 0; x <= 300; x += 4) {
      const u = x / 300;
      const env = [Math.sin(Math.PI * u) ** 2, Math.exp(-((u - 0.3) ** 2) / 0.004), Math.exp(-u * 5) * (u > 0.12), Math.exp(-u * 2.2)][k];
      const f = [0.9, 0.35, 0.6, 0.28][k];
      const y = 55 + 46 * env * Math.sin(x * f + t * (6 + k * 2));
      d += `${x ? 'L' : 'M'}${x} ${y.toFixed(1)}`;
    }
    p.setAttribute('d', d);
  }
});

// check: the counters start at the numbers of this video's first check and count down to zero.
for (const [id, n] of [['#c1', 5], ['#c2', 6], ['#c3', 1]]) {
  const el = $(id);
  P.onFrame(() => {
    const v = Math.round(n * (1 - P.prog('check.zero', { dur: 1.3 })));
    el.textContent = v;
    el.style.color = v ? T.danger : T.green;
  });
}

// render: voice, music and effects run as three lines and merge into one mix.
const mix = [0, 1, 2].map((i) => $(`#mw${i}`));
P.onFrame((t) => {
  const m = P.prog('render.mix', { dur: 1.4, ease: P.ease.inOut });
  mix.forEach((p, i) => {
    const y0 = 56 + i * 120, y = y0 + (180 - y0) * m, amp = [34, 18, 26][i] * (1 - 0.35 * m);
    let d = '';
    for (let x = 140; x <= 760; x += 6) {
      const v = Math.sin(x / [23, 61, 9][i] + t * [5, 2, 9][i]) * Math.sin(x / 170 + t);
      d += `${x > 140 ? 'L' : 'M'}${x} ${(y + amp * v).toFixed(1)}`;
    }
    p.setAttribute('d', d);
    p.style.opacity = i && m > 0.95 ? 1 - (m - 0.95) * 20 : 1;
  });
});

// rules: one step lights, then it stops; the next step lights only after the yes.
const dots = [...document.querySelectorAll('#dots span')];
for (const [k, when] of [[0, 'rules+0.8'], [1, 'rules.yes+0.9']]) {
  tl.to(dots[k].querySelector('i'), { backgroundColor: T.accent, duration: 0.25 }, at(when));
  tl.to(dots[k], { color: T.ink, duration: 0.25 }, at(when));
}

// studio: the videos page starts in the middle and moves aside when the review page arrives.
// left and top, not x and y: the data-in entrance already moves y.
tl.fromTo('#studio-a', { left: 190, top: 80 }, { left: 0, top: 0, duration: 0.6, ease: P.ease.move, immediateRender: true }, at('studio.pages-0.2'));

// call to action: the clone line types, then the first command.
Modern.type('#t-clone', 'cta.clone+0.1', { cps: 32 });
Modern.in(tl, '#l-setup', 'cta.clone+1.9', 'fade');
