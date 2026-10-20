// Fake voice timing for fx demos (library/fx/_demo/*.html); a real video uses 03_cues/cues.js.
window.ANIM = {
  meta: { duration: 6, slug: "fx-demo" },
  cueList: [{ id: "intro", start: 0, end: 2 }, { id: "point", start: 2, end: 4 }, { id: "outro", start: 4, end: 6 }],
  words: [
    { text: "Every", start: 0.3, end: 0.6 }, { text: "part", start: 0.6, end: 0.9 }, { text: "moves", start: 0.9, end: 1.3 },
    { text: "on", start: 1.3, end: 1.4 }, { text: "the", start: 1.4, end: 1.5 }, { text: "voice.", start: 1.5, end: 2.0 },
    { text: "Here", start: 2.2, end: 2.5 }, { text: "is", start: 2.5, end: 2.6 }, { text: "the", start: 2.6, end: 2.7 },
    { text: "point.", start: 2.7, end: 3.3 }, { text: "And", start: 4.2, end: 4.4 }, { text: "done.", start: 4.4, end: 5.0 },
  ],
};
