// Library test (Modern kit): fx parts, an animated icon (index.html) and a Lottie clip. Guide: _shared/modern.md.
const H = Blocks.core(P.timeline());
const $ = (s) => document.querySelector(s);

FX.dynamicGrid(H, $('.lt-bg'), { variant: 'dots', glow: 0.25 });

// intro: the name decodes, then the line under it is underlined
FX.matrixDecode(H, $('.lt-title'), { at: H.at('intro+0.1'), dur: 1.2 });
FX.underline(H, $('.lt-sub'), { at: H.at('@script') });

// cut to the voice shot: a circle opens just before the phrase (K5)
const cut = FX.circleReveal(H, $('.lt-a'), $('.lt-b'), { at: H.at('voice-0.15') });
// B's hero starts 0.1 s before the wipe is done (cut table, K5)
H.tl.fromTo('.lt-b .vf-title', { autoAlpha: 0, y: 40 }, { autoAlpha: 1, y: 0, duration: 0.45, ease: 'power3.out', immediateRender: true }, cut.end - 0.1);
H.hide($('.lt-b'), H.at('scene'));
Modern.push('.lt-b', 'voice', 'scene');  // the shot keeps moving while the voice talks

// scene: the three cards rise (data-in), an arrow points at the voice card, the tick lands
FX.arrowAnnotate(H, $('.lt-scene'), { at: H.at('@picture'), target: '.lt-target', from: { x: 600, y: 820 }, label: 'every beat' });
const tick = Lib.lottie('success-check', { colors: 'brand' });
const canvas = $('.lt-lottie'), ctx = canvas.getContext('2d');
const tickAt = Modern.at('@lands');
P.onFrame((t) => {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (t >= tickAt) tick.at(ctx, t - tickAt, 300, 300, 600, 600);
});

// render: the command types out and prints its result
FX.terminal(H, $('.lt-term'), { at: H.at('render+0.1'), command: 'python anim.py render', output: [{ text: 'done: 05_render/video.mp4', tone: 'green' }] });
