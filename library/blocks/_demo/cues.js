// Fake voice timing for block demos (library/blocks/<id>/demo.html); a real video uses 03_cues/cues.js.
window.ANIM = {
  meta: { duration: 4, slug: "block-demo" },
  cueList: [{ id: "demo", start: 0, end: 4 }],
  words: [
    { text: "This", start: 0.2, end: 0.4 }, { text: "block", start: 0.4, end: 0.8 }, { text: "works", start: 0.8, end: 1.0 },
    { text: "well", start: 1.0, end: 1.4 }, { text: "in", start: 1.5, end: 1.6 }, { text: "a", start: 1.6, end: 1.8 },
    { text: "real", start: 1.8, end: 2.2 }, { text: "video.", start: 2.2, end: 2.7 },
  ],
};
