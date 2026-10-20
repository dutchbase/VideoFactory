// scene.js - timed parts of this scene that HTML attributes cannot say. Guide: _shared/modern.md.
// The setup test has no voice: the cues come from @times in 03_cues/cues.md.
const tl = P.timeline();

// The last card lifts a little once all three have landed.
tl.to('.vf-card.hot', { y: -14, duration: 0.6, ease: P.ease.pop }, Modern.at('build+2.4'));
