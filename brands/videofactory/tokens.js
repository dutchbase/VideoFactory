// VideoFactory brand tokens: the house brand of this repo. Dark studio look, one warm accent, one cool accent.
// Keep this file flat: one key per line, single quotes, no helpers. Checkers read it with a regex.
window.BrandTokens = {
  id: 'videofactory', // same as the folder name in brands/
  name: 'VideoFactory',
  bg: '#0B0B10', // page background
  surface: '#16161F', // cards, windows, panels
  raised: '#20202C', // parts inside a card
  ink: '#F5F2EA', // main text
  dim: '#B4B1BF', // secondary text
  faint: '#77758A', // labels and muted text
  line: '#2C2C3A', // borders and dividers
  accent: '#FF5B2E', // brand orange: the one thing to look at
  accent2: '#7C5CFF', // violet: the second voice
  green: '#3DDC84', // success
  danger: '#FF4D5E', // error
  ramp: ['#0B0B10','#16161F','#8A2E14','#FF5B2E','#FF9A6B','#FFD8C7','#F5F2EA','#FBF9F4'], // darkest to lightest; 3 = accent, 6 = cream
  font: '"Inter", system-ui, sans-serif', // body text
  head: '"Archivo", "Inter", system-ui, sans-serif', // headings
  mono: '"JetBrains Mono", ui-monospace, monospace', // labels and code
  hand: '"Caveat", cursive', // handwritten notes
  grads: [['#FF5B2E','#FFB547'],['#7C5CFF','#C084FC'],['#14B8A6','#5EEAD4'],['#3DDC84','#A3E635'],['#FF4D8D','#FF9A6B']], // gradient pairs [from, to]
};
