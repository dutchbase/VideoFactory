// scene.js - the timed parts of the VideoFactory showcase. The tour of the library: every chapter shows the parts the voice names.
// A time is a cue id ('hook'), a cue with an offset ('hook+0.4'), a spoken word ('@money'), or seconds (2.5).
const tl = P.timeline();
const H = Blocks.core(tl);
const at = Modern.at;
const T = window.BrandTokens;
const words = (window.ANIM && window.ANIM.words) || [];
const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const between = (a, b) => words.filter((w) => w.start >= at(a) - 0.01 && w.start < at(b) - 0.01);
const clock = (s) => `${Math.floor(s / 60)}:${(s % 60).toFixed(2).padStart(5, '0')}`;

// What the library gave this video (the counts come from 04_scene/assets/library.md).
// Real data: the loudness shape of four sound effects of this video (24 points, as a share of the peak) and the level of the voice (36 points).
const SFX_ENV = {"whoosh": [5, 10, 23, 23, 18, 52, 41, 46, 87, 100, 34, 50, 41, 44, 19, 19, 14, 11, 4, 4, 2, 2, 1, 0], "pop": [100, 77, 59, 44, 34, 26, 21, 15, 12, 9, 7, 5, 4, 3, 3, 2, 2, 1, 1, 0, 0, 0, 0, 0], "stamp": [100, 100, 64, 32, 35, 27, 26, 14, 9, 5, 6, 5, 5, 4, 3, 3, 3, 3, 3, 3, 3, 2, 2, 2], "chime": [100, 81, 61, 61, 29, 24, 30, 26, 21, 21, 12, 7, 7, 5, 5, 5, 5, 4, 4, 2, 1, 1, 1, 1]};
const VOICE_LEVELS = [58, 62, 53, 49, 51, 51, 58, 58, 57, 57, 54, 52, 55, 62, 55, 48, 55, 55, 58, 58, 53, 58, 53, 57, 62, 56, 63, 54, 60, 52, 52, 65, 55, 60, 58, 54];
const TALLY = { fx: 37, icons: 22, graphics: 18, lottie: 8, motion: 8 };   // motion: 7 motion-pack clips + the HyperFrames 3D cube

// ---- shots that an fx transition plays between: a wrapper is shown from its start and hidden by the transition or at its end ----
const show = (id, t) => tl.set($(id), { autoAlpha: 1 }, Math.max(0, at(t) - 0.001));
const hide = (id, t) => tl.set($(id), { autoAlpha: 0 }, at(t));
const lottie = (name, sel, when, o = {}) => {
  const clipL = Lib.lottie(name, { colors: 'brand' });
  const c = $(sel), ctx = c.getContext('2d'), W = c.width, Hh = c.height;
  P.onFrame((t) => {
    ctx.clearRect(0, 0, W, Hh);
    const s = t - at(when);
    if (clipL.ready && s >= 0) clipL.at(ctx, s, W / 2, Hh / 2, W * (o.fill || 0.86), Hh * (o.fill || 0.86), { loop: !!o.loop });
  });
};

// =============================================================================================================================
// 0:00 hook: a line tracks in, three tools spring in within the first 1.3 s (the hook), then they are struck out (A of the expand-morph)
FX.trackingIn(H, $('#hook-title'), { at: 0.05, dur: 0.9, from: 0.1 });
const tools = $$('#tools .tool');
[['hook+0.45', 0], ['hook+0.85', 1], ['hook+1.25', 2]].forEach(([w, i]) => FX.springIn(H, tools[i], { at: w, config: 'bouncy', travel: 56 }));
tl.to('#tools .tool b', { '--strike': 1, duration: 0.35, ease: P.ease.move, stagger: 0.1 }, at('hook.weekend'));
tl.to('#tools .tool', { y: 24, rotate: (i) => [-4, 3, -2][i], opacity: 0.45, duration: 0.6, ease: P.ease.out, stagger: 0.06 }, at('hook.weekend+0.35'));

// 0:06 turn: expand-morph from the hook into the chat (B)
show('#w-hook', 0);
FX.expandMorph(H, $('#w-hook'), $('#w-turn'), { at: 'turn-0.7', lead: 0.14, dur: 0.8 });
tl.set($('#w-hook'), { autoAlpha: 0 }, at('turn-0.7') + 0.45);   // the card covers it by now
FX.strikethroughReplace(H, $('#turn-line'), { at: 'turn.chat-0.5', to: 'One conversation.', strike: 0.3, hold: 0.35 });
FX.springIn(H, $('#chat'), { at: 'turn+0.5', config: 'smooth', travel: 40 });
const bub = $$('#chat .bubble');
['turn+0.8', 'turn.chat-0.2', 'turn.chat+0.3'].forEach((w, i) => Modern.in(tl, bub[i], w, 'rise'));
lottie('chat-bubble', '#lot-chat', 'turn.chat', { fill: 0.9 });
hide('#w-turn', 'what');

// 0:09 what: a folder, an agent and six checked stages joined by lines
const links = FX.connectorLines(H, $('#stages'), {
  at: 'what.check', shape: 'straight', dot: true, dur: 0.45, stagger: 0.3,
  anchors: [0, 1, 2, 3, 4, 5].map((i) => ({ id: `s${i}`, el: $(`#st${i}`) })),
  edges: [0, 1, 2, 3, 4].map((i) => ({ from: `s${i}`, to: `s${i + 1}` })),
});
Modern.in(tl, '.stage .ck', 'what.check+0.5', 'pop', { stagger: 0.32 });
tl.set(links.svg, { autoAlpha: 0 }, at('setup'));

// 0:19 setup: what you need (A of the whip pan), then the doctor (B)
show('#w-setup', 'setup');
FX.whipPan(H, $('#w-setup'), $('#w-setup2'), { at: 'setup.type-0.3', dir: 'left' });
FX.terminal(H, $('#setup-slot'), {
  at: 'setup.type+0.05', command: '/vf-setup', prompt: '>', title: 'Terminal', size: 40, width: 1000, typeDur: 1.5, lead: 0.2, outputDelay: 0.7, stagger: 0.42,
  output: [
    { text: 'OK  Python 3.12 or newer', tone: 'green' },
    { text: 'OK  Chromium for Playwright', tone: 'green' },
    { text: 'OK  ffmpeg', tone: 'green' },
    { text: 'OK  Fonts (local, with licences)', tone: 'green' },
    { text: 'OK  Whisper (word times)', tone: 'green' },
  ],
});
FX.progressBar(H, $('#pb-slot'), { at: 'setup.doctor', dur: 3.0, value: 100, label: 'Installing the rest', suffix: '%', width: 520, height: 36 });
FX.springIn(H, $('#testcard'), { at: 'setup.test', config: 'bouncy', travel: 36 });
lottie('check-mark', '#lot-check', 'setup.test+0.4');
hide('#w-setup2', 'optional');

// 0:36 optional: eight parts, one panel that says what the lit part does (A of the zoom-through)
show('#w-optional', 'optional');
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
const spots = $$('[data-spot]');
spots.forEach((el, i) => {
  if (i) Modern.in(tl, el, `${el.dataset.spot}+0.05`, 'rise');
  if (spots[i + 1]) Modern.out(tl, el, `${spots[i + 1].dataset.spot}-0.3`, 'sink');
});
Modern.in(tl, '#photos img', 'optional.photos+0.1', 'rise', { stagger: 0.14 });
Modern.in(tl, '#bf-url', 'optional.browser', 'rise');
// Whisper: a real word of this video, and the time Whisper gave it rolls in.
const first = words.find((w) => /explainer/i.test(w.text));
if (first) {
  $('#spot-word b').textContent = first.text;
  $('#spot-word small').textContent = clock(first.start);
  FX.slotRoll(H, $('#spot-word small'), { at: 'optional.whisper+0.5', from: '0:00.00', to: clock(first.start), dur: 0.9, glyphs: '0123456789', color: 'accent' });
}
// ElevenLabs: a live wave. Earshot: a live level meter. Node: the HyperFrames 3D cube, rendered as a clip.
const meter = $('#meter');
const bars = Array.from({ length: 18 }, () => meter.appendChild(document.createElement('i')));
P.onFrame((t) => {
  bars.forEach((b, i) => {
    const v = 0.18 + 0.82 * Math.abs(Math.sin(t * 5.3 + i * 0.7) * Math.sin(t * 2.1 + i * 0.31));
    b.style.height = `${(v * 100).toFixed(1)}%`;
  });
  let d = '';
  for (let x = 0; x <= 600; x += 6) {
    const env = Math.sin(Math.PI * x / 600);
    d += `${x ? 'L' : 'M'}${x} ${(75 + env * 52 * Math.sin(x / 19 + t * 7) * Math.sin(x / 53 - t * 2.3)).toFixed(1)}`;
  }
  $('#owave').setAttribute('d', d);
});
Modern.clip('#cube-clip', 'engines-cube', 'optional.node');

// 0:59 /vf: it reads the folders and names the next step (B of the zoom-through)
FX.zoomThrough(H, $('#w-optional'), $('#w-vf'), { at: 'vf-0.2', out: 0.2, dur: 0.5 });
FX.maskedSlideReveal(H, $('#vf-title'), { at: 'vf', by: 'words', stagger: 0.08, align: 'center' });
FX.terminal(H, $('#vf-slot'), {
  at: 'vf.type', command: '/vf', prompt: '>', title: 'Terminal', size: 46, width: 880, typeDur: 0.5, lead: 0.2, outputDelay: 1.1, stagger: 0.5,
  output: [
    { text: 'Reading brands ...  ok', tone: 'green' },
    { text: 'Reading videos ...  ok', tone: 'green' },
    { text: 'Reading stages ...  ok', tone: 'green' },
  ],
});
FX.notificationStack(H, $('#note-slot'), {
  at: 'vf.reads', align: 'top-left', width: 640, margin: 0, life: 99, progress: false,
  toasts: [{ title: 'Next step', body: '/vf-render: check and render the MP4', tone: 'success', at: '@next>vf.reads', hold: 99 }],
});
hide('#w-vf', 'vf.help');

// 1:06 /vf-help: the whole command list slides in (A of the blinds), then the brand (B)
show('#w-vfhelp', 'vf.help');
FX.maskedSlideReveal(H, $('#cmdlist'), {
  at: 'vf.help+0.3', by: 'lines', stagger: 0.4, align: 'center',
  lines: ['/vf  /vf-help  /vf-setup', '/vf-new-brand  /vf-new-style  /vf-new-character', '/vf-new-video  /vf-research  /vf-script', '/vf-voice  /vf-transcript  /vf-cues', '/vf-scene  /vf-render  /vf-status'],
});
FX.blinds(H, $('#w-vfhelp'), $('#w-brand'), { at: 'brand-0.4', dur: 0.36, slats: 8, orientation: 'horizontal' });

// 1:09 brand: logo, colours, handwriting, fonts, voice
FX.meshGradient(H, $('#mesh-brand'), { from: 'brand-0.4', to: 'brand.style', colors: ['accent', 'line', 'dim'], opacity: 0.45 });
FX.svgMaskReveal(H, $('#logo-mark'), { at: 'brand', dur: 0.9, shape: 'circle', bouncy: true });
FX.maskReveal(H, $('#wordmark'), { at: 'brand+0.25', dur: 0.7, direction: 'left' });
Modern.in(tl, '#pal-tile', 'brand.new', 'pop');
Modern.in(tl, '#swatches .sw', 'brand.new+0.3', 'pop', { stagger: 0.4 });
FX.handwritingText(H, $('#hand-note'), { at: '@colours', perChar: 0.06, underline: true, wobble: 0 });
Modern.in(tl, '#fonts', 'brand.fonts', 'rise');
Modern.in(tl, '#voicec', 'brand.fonts+0.4', 'pop');
hide('#w-brand', 'brand.style');

// 1:17 /vf-new-style
Modern.in(tl, '.styles > #style-a', 'brand.style+0.3', 'left');
Modern.in(tl, '.styles > #style-b', 'brand.style+0.55', 'right');
FX.markerHighlight(H, $('#mh-look'), { at: '@a>brand.style', variant: 'marker', stagger: 0.18 });

// 1:21 /vf-new-character: four steps, each approved
Modern.in(tl, '.char-steps .vf-step', 'brand.character+0.2', 'rise', { stagger: 1.0 });
Modern.in(tl, '.stamp', 'brand.approve+0.1', 'zoom', { stagger: 0.22 });
FX.shakeEmphasis(H, $('#stamp-tile'), { at: 'brand.approve+0.15', dur: 0.6, intensity: 12 });

// 1:28 /vf-new-video: brand, format, brief
Modern.type('#t-video', 'video+0.3', { cps: 6 });
Modern.in(tl, '#brand-chip', '@brand>video.format', 'pop');
Modern.out(tl, '#brand-chip', 'video.brief-0.1', 'sink');
FX.springIn(H, $('#frm-wide'), { at: '@wide', config: 'snappy', travel: 30 });
FX.springIn(H, $('#frm-tall'), { at: '@tall', config: 'snappy', travel: 30 });
FX.codeBlock(H, $('#brief-slot'), {
  at: 'video.brief', title: 'brief.md', lang: 'js', by: 'chars', size: 40, width: 900, typeDur: 3.6, lead: 0.2,
  code: 'for:   friends who make content\n       or code a little\nafter: they know every command\n       and make a video',
});

// 1:39 /vf-research: a public page and a source
Modern.type('#t-research', 'research+0.5', { cps: 14 });
FX.kenBurns(H, $('#research-img'), { at: 'research+0.4', dur: 6, fromScale: 1, toScale: 1.12, from: { x: 0.4, y: 0.1 }, to: { x: 0.45, y: 0.3 } });
FX.arrowAnnotate(H, $('#r-browser'), { at: 'research.web', label: 'Public page', from: { x: 1120, y: 470 }, to: { x: 860, y: 360 }, labelSize: 46 });
FX.callout(H, $('#r-browser'), { at: 'research.source', label: 'The source', target: $('#r-url'), position: 'bottom-left', size: 46 });

// 1:45 /vf-script and the tone check
FX.markerHighlight(H, $('#mk1'), { at: '@narration', variant: 'marker' });
FX.markerHighlight(H, $('#mk2'), { at: '@narration+0.5', variant: 'marker' });
FX.springIn(H, $('#tone-line'), { at: 'script.tone+0.2', config: 'snappy', travel: 30 });
FX.strikethroughReplace(H, $('#tone-line'), { at: '@hype', to: 'Make your video', strike: 0.3, hold: 0.35 });

// 1:54 /vf-voice: a free recording or a paid voice; the paid card plays the AI voice clip
FX.kenBurns(H, $('#mic'), { at: 'voice.free', dur: 5, fromScale: 1.0, toScale: 1.14, from: { x: 0.5, y: 0.45 }, to: { x: 0.5, y: 0.45 } });
Modern.clip('#ai-clip', 'ai-voice', 'voice.eleven');

// 2:01 the review page: scroll to the Approved bar, then one camera move onto it
const review = $('#review-img');
P.onFrame(() => {
  const s = P.prog('voice.approve', { delay: 0.6, dur: 1.8, ease: P.ease.inOut });
  const z = P.prog('voice.stamp', { delay: 0.1, dur: 1.4, ease: P.ease.inOut });
  const x = 215 * z, y = -370 * s + (-535 + 370) * z;
  review.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px) scale(${P.zoom(1, 3, z).toFixed(4)})`;
});

// 2:05 /vf-transcript: the caption clip, and the real words with their times
Modern.type('#t-transcript', 'transcript+0.1', { cps: 12 });
Modern.clip('#cap-clip', 'transcript-cap', 'transcript');
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

// 2:10 /vf-cues: the first cue marks of this video on a time line
lottie('clock-loop', '#lot-clock', 'cues', { loop: true });
FX.timeline(H, $('#cue-slot'), {
  at: 'cues+0.3', dur: 2.4, width: 1500, labelWidth: 280,
  points: (window.ANIM.cueList || []).slice(0, 5).map((c) => ({ label: c.id, sub: clock(c.start) })),
});

// 2:14 /vf-scene: code becomes a picture
FX.codeBlock(H, $('#code-slot'), {
  at: 'scene.build', title: 'index.html', lang: 'js', by: 'chars', size: 32, width: 800, typeDur: 2.4, lead: 0.2,
  code: '<h2 data-in="words">\n  An explainer video\n  usually means\n</h2>',
});

// 2:19 library: animated icons, colour graphics and Lottie (A of the zoom-through), stock (B)
show('#w-library', 'scene.library');
[['bar-graph-loop', '#lot-w1'], ['search', '#lot-w2'], ['growth-chart', '#lot-w3'], ['clock-loop', '#lot-w4']]
  .forEach(([n, sel], i) => lottie(n, sel, `@lottie+${i * 0.1}`, { loop: true, fill: 0.9 }));
FX.zoomThrough(H, $('#w-library'), $('#w-stock'), { at: 'scene.stock-0.2', out: 0.2, dur: 0.5 });
Modern.clip('#stock-clip', 'timeline', 'scene.stock');
Modern.clip('#music-clip', 'audio-bars', 'scene.stock');
FX.kenBurns(H, $('#ph-img'), { at: 'scene.stock', dur: 3.2, fromScale: 1, toScale: 1.15, from: { x: 0.5, y: 0.5 }, to: { x: 0.5, y: 0.5 } });
hide('#w-stock', 'scene.capture');

// 2:26 a real browser recording; 2:30 ready-made motion components
Modern.clip('#rec-clip', 'browser-search', 'scene.capture-1.2', { speed: 1.3 });
Modern.clip('#m-agent', 'agent-flow', 'scene.motion', { speed: 1.4, from: 0.8 });
Modern.clip('#m-stack', 'card-stack', 'scene.motion', { speed: 1.2 });
Modern.clip('#m-ticker', 'ticker', 'scene.motion', { speed: 1.2 });
Modern.in(tl, '#m-agent', 'scene.motion+0.05', 'left');
Modern.in(tl, '#m-stack', 'scene.motion+0.2', 'zoom');
Modern.in(tl, '#m-ticker', 'scene.motion+0.35', 'right');

// 2:33 sound effects and music (A of the pixelate), the counters (B)
show('#w-sound', 'scene.sound');
FX.sparklineRow(H, $('#spark-slot'), {
  at: 'scene.sound+0.2', dur: 1.6, width: 1060, rowHeight: 112, sparkWidth: 700, labelWidth: 200, deltaWidth: 20, stagger: 0.4,
  rows: [['whoosh', 'accent'], ['pop', 'accent2'], ['stamp', 'green'], ['chime', 'accent']].map(([k, c]) => ({ label: k, values: SFX_ENV[k], color: c })),
});
FX.gridPixelate(H, $('#w-sound'), $('#w-check'), { at: 'check-0.5', dur: 0.6, cols: 16, seed: 3 });

// 2:40 check: a still for every cue, a spotlight on one, the counters go to zero
FX.springIn(H, $('#sheet'), { at: 'check+0.4', config: 'smooth', travel: 40 });
FX.spotlight(H, $('#sheet'), { at: 'check.still', shape: 'rect', x: 120, y: 60, w: 300, h: 190, moves: [{ at: 'check.still+1.0', x: 330, y: 150, w: 300, h: 190 }], exitAt: 'check.count', dim: 0.7 });
FX.comparisonBars(H, $('#bars-slot'), {
  at: 'check.count', dur: 3.0, width: 800, labelWidth: 330, valueWidth: 70, deltaWidth: 90, barHeight: 34, rowGap: 40,
  seriesLabels: ['First check', 'Now'],
  rows: [{ label: 'Text overlaps', before: 5, after: 0 }, { label: 'Too short to read', before: 6, after: 0 }, { label: 'Sound missing', before: 1, after: 0 }],
});
lottie('success-check', '#lot-ok', 'check.done');
hide('#w-check', 'render');

// 2:50 render: one file, a mix, a loudness gauge
Modern.clip('#player-clip', 'player', 'render', { from: 1.2 });
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
FX.gaugeDial(H, $('#gauge-slot'), { at: 'render.mix+1.2', dur: 0.9, value: 3, min: 0, max: 20, label: 'effects: dB under the voice', unit: '', size: 400, thickness: 34, showRange: false });

// 2:57 phone copy, thumbnail, chapters
FX.timeline(H, $('#chap-slot'), {
  at: 'render.extras+0.8', dur: 2.2, width: 1500, labelWidth: 260,
  points: [['Intro', 'hook'], ['Setup', 'setup'], ['Brand', 'brand'], ['Scene', 'scene'], ['Render', 'render']].map(([n, c]) => ({ label: n, sub: clock(at(c)).replace(/\.\d+$/, '') })),
});

// 3:01 Earshot listens: the level of the voice over the whole video
FX.lineChart(H, $('#lc-slot'), { at: 'render.earshot+0.3', dur: 2.4, values: VOICE_LEVELS, width: 1100, height: 330, valueGutter: 10, strokeWidth: 8, showDots: false, color: 'accent' });

// 3:05 the Studio: the real page, pulled back into a laptop (A), then two real pages (B)
show('#w-studio', 'studio');
FX.devicePullback(H, $('#w-studio'), $('#w-studiopages'), { at: 'studio+0.05', dur: 1.5, hold: 0.55, device: 'laptop', start: 3, focus: [0.3, 0.2] });
tl.fromTo('#studio-a', { left: 190, top: 80 }, { left: 0, top: 0, duration: 0.6, ease: P.ease.move, immediateRender: true }, at('studio.pages-0.1'));
Modern.in(tl, '#studio-b', 'studio.pages-0.1', 'right');
hide('#w-studiopages', 'status');

// 3:13 /vf-status: the real row for this video, a stat card
FX.terminal(H, $('#status-slot'), {
  at: 'status+0.05', command: '/vf-status', prompt: '>', title: 'Terminal', size: 40, width: 980, typeDur: 0.5, lead: 0.2, outputDelay: 0.1, stagger: 0.15,
  output: [
    { text: 'videofactory/what-is-videofactory', tone: 'accent' },
    '00_research    not used',
    { text: '01_voice       done', tone: 'green' },
    { text: '02_transcript  done', tone: 'green' },
    { text: '03_cues        done', tone: 'green' },
    { text: '04_scene       done', tone: 'green' },
    { text: '05_render      done', tone: 'green' },
  ],
});
FX.statCard(H, $('#stat-slot'), { at: 'status+1.4', value: 5, label: 'stages done', dur: 1.0, numberSize: 200, labelSize: 52 });

// 3:16 the rules: one step, then it stops; a clear yes
FX.maskReveal(H, $('#rule-line'), { at: 'rules', dur: 0.8, direction: 'left' });
FX.shakeEmphasis(H, $('#yes-btn'), { at: 'rules.yes+0.5', dur: 0.6, intensity: 10 });
const dots = $$('#dots span');
for (const [k, when] of [[0, 'rules+0.8'], [1, 'rules.yes+0.9']]) {
  tl.to(dots[k].querySelector('i'), { backgroundColor: T.accent, duration: 0.25 }, at(when));
  tl.to(dots[k], { color: T.ink, duration: 0.25 }, at(when));
}

// 3:24 reveal: the line decodes, the tally counts what this video used (A of the circle reveal)
show('#w-reveal', 'reveal');
FX.matrixDecode(H, $('#rl1'), { at: 'reveal', dur: 1.0 });
FX.matrixDecode(H, $('#rl2'), { at: 'reveal+0.5', dur: 1.0 });
FX.donutChart(H, $('#tally-slot'), {
  at: 'reveal+0.5', dur: 1.8, size: 330, thickness: 44, width: 780, totalLabel: 'parts used',
  segments: [
    { label: 'fx parts', value: TALLY.fx, color: 'accent' }, { label: 'animated icons', value: TALLY.icons, color: 'accent2' },
    { label: 'colour graphics', value: TALLY.graphics, color: 'green' }, { label: 'Lottie', value: TALLY.lottie, color: 'dim' },
    { label: 'motion + 3D clips', value: TALLY.motion, color: 'ink' },
  ],
});
FX.circleReveal(H, $('#w-reveal'), $('#w-cta'), { at: 'cta-0.45', dur: 0.36, x: 0.5, y: 0.5 });

// 3:27 call to action (B): the mark comes down, the repo URL shimmers, confetti on "today"
FX.particleField(H, $('#pf-cta'), { from: 'cta-0.45', color: 'accent', count: 50 });
tl.fromTo('#end-mark', { scale: 1.3 }, { scale: 1, duration: 0.8, ease: P.ease.out, immediateRender: true }, at('cta-0.3'));
Modern.type('#t-clone', 'cta.clone+0.1', { cps: 30 });
Modern.in(tl, '#l-setup', 'cta.clone+1.9', 'fade');
Modern.in(tl, '#url-row', 'cta.today', 'pop');
FX.shimmerSweep(H, $('#cta-url'), { at: 'cta.today+0.4', dur: 0.9, repeat: 2, interval: 0.4 });
lottie('confetti-burst', '#lot-confetti', 'cta.today', { fill: 1 });
