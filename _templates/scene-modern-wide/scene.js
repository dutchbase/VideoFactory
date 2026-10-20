// TEMPLATE: this is the starter scene. Stage 04 replaces it (anim.py status shows 04_scene as done after that).
// scene.js - timed parts of this scene that HTML attributes cannot say. Guide: _shared/modern.md.
// A time is a cue id ('hook'), a cue with an offset ('hook+0.4'), a spoken word ('@money'), or seconds (2.5).
const tl = P.timeline();

// Examples. Remove the // to use one.
// Modern.in(tl, '#card', 'problem+0.2', 'pop');          // entrance on a cue
// Modern.out(tl, '#card', 'solution-0.4', 'sink');        // exit just before the next cue
// Modern.count('#stat b', '@percent', 87, { suffix: '%' }); // count up when the voice says "percent"
// Modern.type('#prompt', 'demo+0.5');                     // typewriter
// tl.to('#arrow', { rotate: 90, duration: 0.6, ease: P.ease.move }, Modern.at('turn'));  // any GSAP tween
