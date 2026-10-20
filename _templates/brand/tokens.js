// <BRAND NAME> brand tokens. Source: <website, styleguide or logo the colours come from>.
// Keep this file flat: one key per line, single quotes, no helpers. Checkers read it with a regex.
// Example with real values: brands/videofactory/tokens.js
window.BrandTokens = {
  id: '<brand-id>', // same as the folder name in brands/
  name: '<Brand Name>', // shown by data-brand="name"
  bg: '', // page background
  surface: '', // cards, windows, panels
  raised: '', // parts inside a card
  ink: '', // main text
  dim: '', // secondary text
  faint: '', // labels and muted text
  line: '', // borders and dividers
  accent: '', // main brand colour: the one thing to look at
  accent2: '', // second colour: a contrast idea, a second chart series
  green: '', // success
  danger: '', // error
  ramp: ['','','','','','','',''], // 8 colours, darkest to lightest; 0 on 6 must read at contrast 4.5 or better
  font: '"Inter", system-ui, sans-serif', // body text. Fonts must be local: _runtime/fonts/, fonts.css, tools/font_sources.py
  head: '"Archivo", "Inter", system-ui, sans-serif', // headings
  mono: '"JetBrains Mono", ui-monospace, monospace', // labels and code
  hand: '"Caveat", cursive', // handwritten notes
  grads: [['',''],['',''],['',''],['',''],['','']], // 5 gradient pairs [from, to]
};
