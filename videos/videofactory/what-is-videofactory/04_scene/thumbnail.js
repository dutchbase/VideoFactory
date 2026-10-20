// thumbnail.js - still frames for the video cover. `python anim.py thumbnail <slug>` renders every key in THUMBS.
// ?v=<key> picks the variant; add a <section data-thumb="3"> and '3' below for more.
window.THUMBS = ['1', '2'];
const pick = new URLSearchParams(location.search).get('v') || '1';
for (const el of document.querySelectorAll('[data-thumb]')) el.hidden = el.dataset.thumb !== pick;
