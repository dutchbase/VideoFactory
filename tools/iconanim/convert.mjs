// convert.mjs - lucide-animated (motion/react) -> time-driven icon specs for the VideoFactory engines.
// Run: node tools/iconanim/convert.mjs [--out <dir>]   (needs `npm install` once inside tools/iconanim)
// --out writes the whole result (set folder, GALLERY.html, REPORT.md) somewhere else; the tests use it to prove a re-run is identical.
//
// Input is read as text and parsed with @babel/parser. Nothing from the upstream is ever executed:
// variants, transitions and map() loops are resolved by a small AST evaluator (literals, arithmetic,
// arrow functions, .map over const arrays). An icon that needs anything else is skipped and listed
// in tools/iconanim/REPORT.md with the reason.
//
// Output, in library/icons-animated/lucide-animated/:
//   <name>.svg        static drawing in the normal state (viewBox 0 0 24 24, currentColor)
//   <name>.anim.json  the spec (schema below)
//   <name>.js         window.VF_ANIM_ICONS["lucide-animated/<name>"] = {svg, spec}   (file:// pages cannot fetch)
//   TAGS.json         { name: { tags: [...], groups: [...] } }
// and library/icons-animated/GALLERY.html (human check page).
//
// ---- Spec schema (version 1) ------------------------------------------------------------------
// {
//   "v": 1,
//   "name": "bell",
//   "dur": 0.5 | null,        seconds the "start" run lasts; null = a track repeats forever
//   "rdur": 0.3,              seconds the "reset" run (back to normal) lasts; 0 = nothing to reset
//   "els": [ {
//     "i": 0,                 element = [svg, ...svg.querySelectorAll("*")][i]  (0 is the root <svg>)
//     "origin": { "x": "50%", "y": "50%", "box": "fill" | "view" },  transform origin (fill: of the element box)
//     "base": { "opacity": 0 },   values at rest when they differ from the drawing (applied by mount)
//     "start": [ track, ... ],    normal -> animate, times counted from the start of the run
//     "reset": [ track, ... ]     animate -> normal, times counted from the start of the reset
//   } ]
// }
// track = {
//   "at": 0.1,                step offset inside the run (steps that wait for an earlier step get its end time)
//   "delay": 0, "duration": 0.5,
//   "ease": "easeInOut" | [x1,y1,x2,y2],   linear easeIn easeOut easeInOut circIn circOut circInOut backIn backOut backInOut anticipate
//   "spring": [stiffness, damping, mass],  replaces ease; "duration" is the settle time
//   "times": [0, .4, 1],      keyframe positions (same length as the value arrays)
//   "repeat": 2 | -1,         extra cycles; -1 = forever
//   "repeatType": "loop" | "reverse" | "mirror", "repeatDelay": 0,
//   "props": { "rotate": [0, -10, 10, 0], "opacity": [0, 1] },  every array starts at its real start value
//   "pre": { "opacity": 1 }   optional: props whose first keyframe is not where the value is now; it jumps there at "at"
// }                          (a prop without "pre" continues smoothly from its current value)
// Props: opacity scale scaleX scaleY x y rotate skewX skewY pathLength pathOffset strokeDashoffset strokeOpacity
//        cx cy r rx ry d points width height fill. Staggers and per-item delays are already added to "delay".

import { parse } from '@babel/parser';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..', '..');
const SRC = path.join(ROOT, 'library/cache/upstream/lucide-animated@4662fff2b60f');
const LUCIDE = path.join(ROOT, 'library/cache/upstream/lucide@c29c276f1659/icons');
const outArg = process.argv.indexOf('--out');
const OUT_SET = outArg > 0 ? path.resolve(process.argv[outArg + 1]) : path.join(ROOT, 'library/icons-animated');
const OUT = path.join(OUT_SET, 'lucide-animated');
const REPORT = outArg > 0 ? path.join(OUT_SET, 'REPORT.md') : path.join(HERE, 'REPORT.md');

class Unsupported extends Error {}
const fail = (m) => { throw new Unsupported(m); };
const round = (n) => Math.round(n * 1e4) / 1e4;
const EASES = new Set(['linear', 'easeIn', 'easeOut', 'easeInOut', 'circIn', 'circOut', 'circInOut', 'backIn', 'backOut', 'backInOut', 'anticipate']);

// ---------------------------------------------------------------- evaluator (static, no eval)
const MATH = { abs: Math.abs, min: Math.min, max: Math.max, round: Math.round, floor: Math.floor, ceil: Math.ceil,
  sin: Math.sin, cos: Math.cos, sqrt: Math.sqrt, pow: Math.pow, PI: Math.PI };

class Scope {
  constructor(vars = {}, parent = null) { this.vars = vars; this.parent = parent; }
  has(n) { return n in this.vars || (this.parent ? this.parent.has(n) : false); }
  get(n) { return n in this.vars ? this.vars[n] : this.parent.get(n); }
}

function bindPattern(p, value, vars) {
  if (p.type === 'Identifier') vars[p.name] = value;
  else if (p.type === 'AssignmentPattern') bindPattern(p.left, value === undefined ? ev(p.right, new Scope(vars)) : value, vars);
  else if (p.type === 'ObjectPattern') {
    for (const pr of p.properties) {
      if (pr.type !== 'ObjectProperty') fail('rest in pattern');
      const key = pr.key.type === 'Identifier' ? pr.key.name : pr.key.value;
      bindPattern(pr.value, value == null ? undefined : value[key], vars);
    }
  } else if (p.type === 'ArrayPattern') p.elements.forEach((e, i) => e && bindPattern(e, value[i], vars));
  else fail('pattern ' + p.type);
}

function makeFn(node, scope) {
  return (...args) => {
    const vars = {};
    node.params.forEach((p, i) => bindPattern(p, args[i], vars));
    const inner = new Scope(vars, scope);
    if (node.body.type !== 'BlockStatement') return ev(node.body, inner);
    return runBlock(node.body.body, inner).value;
  };
}

// Statements allowed in a literal function: const, if / else, return.
function runBlock(stmts, scope) {
  for (const st of stmts) {
    if (st.type === 'ReturnStatement') return { done: true, value: st.argument ? ev(st.argument, scope) : undefined };
    if (st.type === 'VariableDeclaration') { for (const d of st.declarations) { const o = {}; bindPattern(d.id, ev(d.init, scope), o); Object.assign(scope.vars, o); } continue; }
    if (st.type === 'IfStatement') {
      const br = ev(st.test, scope) ? st.consequent : st.alternate;
      if (!br) continue;
      const r = runBlock(br.type === 'BlockStatement' ? br.body : [br], scope);
      if (r.done) return r;
      continue;
    }
    fail('statement ' + st.type + ' in function');
  }
  return { done: false, value: undefined };
}

function ev(n, scope) {
  switch (n.type) {
    case 'NumericLiteral': case 'StringLiteral': case 'BooleanLiteral': return n.value;
    case 'NullLiteral': return null;
    case 'TemplateLiteral': return n.quasis.reduce((s, q, i) => s + q.value.cooked + (i < n.expressions.length ? String(ev(n.expressions[i], scope)) : ''), '');
    case 'ParenthesizedExpression': case 'TSAsExpression': case 'TSSatisfiesExpression': case 'TSNonNullExpression': return ev(n.expression, scope);
    case 'Identifier':
      if (n.name === 'undefined') return undefined;
      if (n.name === 'Infinity') return Infinity;
      if (n.name === 'cubicBezier' && !scope.has(n.name)) return (...a) => a;   // -> [x1, y1, x2, y2]
      if (scope.has(n.name)) return scope.get(n.name);
      if (EASES.has(n.name)) return n.name;   // imported from motion/react
      return fail('unknown identifier ' + n.name);
    case 'UnaryExpression': {
      const v = ev(n.argument, scope);
      if (n.operator === '-') return -v; if (n.operator === '+') return +v; if (n.operator === '!') return !v;
      return fail('unary ' + n.operator);
    }
    case 'BinaryExpression': {
      const a = ev(n.left, scope), b = ev(n.right, scope);
      switch (n.operator) {
        case '+': return a + b; case '-': return a - b; case '*': return a * b; case '/': return a / b; case '%': return a % b; case '**': return a ** b;
        case '===': case '==': return a === b; case '!==': case '!=': return a !== b;
        case '<': return a < b; case '>': return a > b; case '<=': return a <= b; case '>=': return a >= b;
      }
      return fail('binary ' + n.operator);
    }
    case 'LogicalExpression': {
      const a = ev(n.left, scope);
      if (n.operator === '&&') return a ? ev(n.right, scope) : a;
      if (n.operator === '||') return a ? a : ev(n.right, scope);
      return a ?? ev(n.right, scope);
    }
    case 'ConditionalExpression': return ev(n.test, scope) ? ev(n.consequent, scope) : ev(n.alternate, scope);
    case 'ArrayExpression': {
      const out = [];   // a hole (`[a, , ]`) stays a hole: map() skips it, like in JS
      for (const e of n.elements) { if (e === null) out.length++; else if (e.type === 'SpreadElement') out.push(...ev(e.argument, scope)); else out.push(ev(e, scope)); }
      return out;
    }
    case 'ObjectExpression': {
      const o = {};
      for (const p of n.properties) {
        if (p.type === 'SpreadElement') { Object.assign(o, ev(p.argument, scope)); continue; }
        if (p.type !== 'ObjectProperty') fail('object member ' + p.type);
        const key = p.computed ? ev(p.key, scope) : p.key.type === 'Identifier' ? p.key.name : p.key.value;
        o[key] = ev(p.value, scope);
      }
      return o;
    }
    case 'ArrowFunctionExpression': case 'FunctionExpression': return makeFn(n, scope);
    case 'MemberExpression': case 'OptionalMemberExpression': {
      if (n.object.type === 'Identifier' && n.object.name === 'Number' && n.property.name === 'POSITIVE_INFINITY') return Infinity;
      if (n.object.type === 'Identifier' && n.object.name === 'Math' && !scope.has('Math')) return MATH[n.property.name] ?? fail('Math.' + n.property.name);
      const o = ev(n.object, scope);
      const k = n.computed ? ev(n.property, scope) : n.property.name;
      if (o == null) return fail('member of ' + o);
      if (typeof o === 'function') return fail('member of function');
      return o[k];
    }
    case 'CallExpression': case 'OptionalCallExpression': {
      const c = n.callee;
      if (c.type === 'MemberExpression' && !c.computed && c.property.name === 'map') {
        const arr = ev(c.object, scope);
        if (!Array.isArray(arr)) fail('map on non-array');
        return arr.map(ev(n.arguments[0], scope));
      }
      const f = ev(c, scope);
      if (typeof f !== 'function') fail('call of non-function');
      return f(...n.arguments.map((a) => ev(a, scope)));
    }
  }
  return fail('expression ' + n.type);
}

// ---------------------------------------------------------------- JSX -> node tree
const DROP_ATTRS = new Set(['animate', 'initial', 'variants', 'custom', 'transition', 'key', 'exit', 'style', 'className', 'ref']);
const KEEP_CAMEL = new Set(['viewBox', 'pathLength', 'patternUnits', 'preserveAspectRatio', 'gradientUnits', 'gradientTransform', 'patternTransform', 'markerWidth', 'markerHeight', 'clipPathUnits']);
const kebab = (s) => KEEP_CAMEL.has(s) ? s : s.replace(/[A-Z]/g, (c) => '-' + c.toLowerCase());
const JSX_ENTITIES = { '&nbsp;': ' ', '&amp;': '&', '&lt;': '<', '&gt;': '>' };

function tagName(el) {
  const nm = el.openingElement.name;
  if (nm.type === 'JSXIdentifier') return { tag: nm.name, motion: false };
  if (nm.type === 'JSXMemberExpression' && nm.object.name === 'motion') return { tag: nm.property.name, motion: true };
  return fail('component ' + (nm.name || 'member'));
}

function buildNode(el, scope) {
  const { tag, motion } = tagName(el);
  if (!/^[a-z]+$/.test(tag)) fail('tag ' + tag);
  const node = { tag, motion, attrs: {}, style: {}, kids: [], text: '' };
  for (const a of el.openingElement.attributes) {
    if (a.type !== 'JSXAttribute') fail('spread attribute');
    const name = a.name.name;
    let val = true;
    if (a.value) val = a.value.type === 'StringLiteral' ? a.value.value : a.value.type === 'JSXExpressionContainer' ? ev(a.value.expression, scope) : fail('attr value');
    if (name === 'animate') node.animate = val;
    else if (name === 'initial') node.initial = val;
    else if (name === 'variants') node.variants = val;
    else if (name === 'custom') node.custom = val;
    else if (name === 'transition') node.transition = val;
    else if (name === 'style') node.style = val;
    else if (name.startsWith('on') || DROP_ATTRS.has(name)) continue;
    else if (name === 'width' || name === 'height') { if (tag !== 'svg') node.attrs[name] = val; }
    else node.attrs[kebab(name)] = val;
  }
  for (const c of el.children) {
    if (c.type === 'JSXText') { const t = c.value.replace(/\s+/g, ' ').trim(); if (t) node.text += t.replace(/&\w+;/g, (m) => JSX_ENTITIES[m] ?? m); }
    else node.kids.push(...jsxValue(c, scope));
  }
  return node;
}

function jsxValue(n, scope) {
  switch (n.type) {
    case 'JSXElement': return [buildNode(n, scope)];
    case 'JSXFragment': return n.children.flatMap((c) => c.type === 'JSXText' ? [] : jsxValue(c, scope));
    case 'JSXText': return [];
    case 'JSXExpressionContainer': return n.expression.type === 'JSXEmptyExpression' ? [] : jsxValue(n.expression, scope);
    case 'ParenthesizedExpression': return jsxValue(n.expression, scope);
    case 'LogicalExpression': return n.operator === '&&' ? (ev(n.left, scope) ? jsxValue(n.right, scope) : []) : fail('logical jsx');
    case 'ConditionalExpression': return jsxValue(ev(n.test, scope) ? n.consequent : n.alternate, scope);
    case 'NullLiteral': return [];
    case 'CallExpression': {
      const c = n.callee;
      if (c.type === 'MemberExpression' && c.property.name === 'map') {
        const arr = ev(c.object, scope), fn = n.arguments[0];
        if (!Array.isArray(arr) || !/Function/.test(fn.type)) fail('jsx map');
        return arr.flatMap((item, idx) => {
          const vars = {};
          fn.params.forEach((p, i) => bindPattern(p, [item, idx][i], vars));
          const inner = new Scope(vars, scope);
          let body = fn.body;
          if (body.type === 'BlockStatement') {
            const ret = body.body.at(-1);
            for (const st of body.body.slice(0, -1)) {
              if (st.type !== 'VariableDeclaration') fail('statement in map');
              for (const d of st.declarations) { const o = {}; bindPattern(d.id, ev(d.init, inner), o); Object.assign(inner.vars, o); }
            }
            if (ret.type !== 'ReturnStatement') fail('map without return');
            body = ret.argument;
          }
          return jsxValue(body, inner);
        });
      }
      return fail('jsx call');
    }
  }
  return fail('jsx child ' + n.type);
}

// ---------------------------------------------------------------- motion defaults and transitions
const DEFAULTS = { xPercent: 0, yPercent: 0, strokeWidth: 2, opacity: 1, scale: 1, scaleX: 1, scaleY: 1, x: 0, y: 0, rotate: 0, skewX: 0, skewY: 0, pathLength: 1, pathOffset: 0, strokeDashoffset: 0, strokeOpacity: 1 };
const ALIAS = { translateX: 'x', translateY: 'y', rotateZ: 'rotate' };
const PROPS = new Set([...Object.keys(DEFAULTS), 'cx', 'cy', 'r', 'rx', 'ry', 'd', 'points', 'width', 'height', 'fill', 'x1', 'x2', 'y1', 'y2']);
const IGNORED = new Set(['pathSpacing', 'transition', 'transitionEnd', 'originX', 'originY', 'originZ', 'transformOrigin', 'transformBox']);
const ORIGIN_KEYS = new Set(['originX', 'originY', 'transformOrigin', 'transformBox']);
const ATTR_PROPS = new Set(['cx', 'cy', 'r', 'rx', 'ry', 'd', 'points', 'width', 'height', 'x1', 'x2', 'y1', 'y2', 'strokeWidth']);
const TR_META = new Set(['delay', 'repeat', 'repeatType', 'repeatDelay', 'from', 'elapsed']);

// Closed-form damped spring (same family as P.spring in _runtime/player.js), x(0)=0 -> x(inf)=1.
function springAt(k, c, m, s) {
  const w0 = Math.sqrt(k / m), z = c / (2 * Math.sqrt(k * m));
  if (z < 1) { const wd = w0 * Math.sqrt(1 - z * z); return 1 - Math.exp(-z * w0 * s) * (Math.cos(wd * s) + (z * w0 / wd) * Math.sin(wd * s)); }
  if (z === 1) return 1 - Math.exp(-w0 * s) * (1 + w0 * s);
  const q = w0 * Math.sqrt(z * z - 1), r1 = -z * w0 + q, r2 = -z * w0 - q;
  return 1 - (r2 * Math.exp(r1 * s) - r1 * Math.exp(r2 * s)) / (r2 - r1);
}
function settle(k, c, m) {   // last moment the spring is more than 0.5% away from rest
  let last = 0;
  for (let s = 0; s <= 6; s += 1 / 240) if (Math.abs(1 - springAt(k, c, m, s)) > 0.005) last = s;
  return Math.min(4, Math.max(0.12, round(last + 1 / 240)));
}

// Motion's own defaults for a value that has no transition (physical props spring, opacity tweens).
function defaultTransition(prop, keyframes, target) {
  if (keyframes) return { duration: 0.8 };
  if (prop === 'x' || prop === 'y' || prop === 'rotate') return { type: 'spring', stiffness: 500, damping: 25 };
  if (prop === 'opacity') return { duration: 0.3, ease: 'linear' };
  const crit = (t) => ({ type: 'spring', stiffness: 550, damping: t === 0 ? 2 * Math.sqrt(550) : 30 });
  return crit(target);
}

function valueTransition(tr, prop) {
  if (!tr) return {};
  const own = tr[prop] && typeof tr[prop] === 'object' && !Array.isArray(tr[prop]) ? tr[prop] : tr.default && typeof tr.default === 'object' ? tr.default : tr;
  return { ...(own === tr ? {} : { delay: tr.delay, repeat: tr.repeat, repeatType: tr.repeatType, repeatDelay: tr.repeatDelay }), ...own };
}

// -> a normalised transition: { delay, duration, ease|spring, times, repeat, repeatType, repeatDelay }
function normTransition(raw, prop, keyframes, target, staggerDelay) {
  let o = { ...raw };
  const defined = Object.keys(o).some((k) => !TR_META.has(k) && o[k] !== undefined);
  if (!defined) o = { ...defaultTransition(prop, keyframes, target), ...Object.fromEntries(Object.entries(o).filter(([, v]) => v !== undefined)) };
  const delay = o.delay !== undefined ? o.delay : staggerDelay;
  const spring = o.type === 'spring' || (o.type === undefined && ['stiffness', 'damping', 'mass', 'bounce', 'visualDuration'].some((k) => o[k] !== undefined));
  const out = { delay: round(delay || 0) };
  if (spring) {
    let { stiffness, damping, mass = 1 } = o;
    if (stiffness === undefined || damping === undefined) {
      const dur = o.visualDuration ?? o.duration ?? 0.3, bounce = o.bounce ?? 0.25;
      const w = (2 * Math.PI) / dur; stiffness = w * w * mass; damping = 2 * (1 - bounce) * Math.sqrt(stiffness * mass);
    } else if (o.stiffness === undefined) stiffness = 100;
    if (damping === undefined) damping = 10;
    out.spring = [round(stiffness), round(damping), round(mass)];
    out.duration = settle(stiffness, damping, mass);
  } else {
    out.duration = round(o.duration ?? 0.3);
    const e = o.ease === undefined ? 'easeInOut' : o.ease;
    const one = (x) => (Array.isArray(x) && x.length === 4 && x.every((v) => typeof v === 'number')) ? x.map(round) : (typeof x === 'string' && EASES.has(x)) ? x : fail('ease ' + JSON.stringify(x));
    out.ease = Array.isArray(e) && !e.every((v) => typeof v === 'number') ? e.map(one) : one(e);   // an array of eases = one per keyframe segment
  }
  if (o.times) out.times = o.times.map(round);
  const rep = o.repeat === undefined ? 0 : o.repeat === Infinity ? -1 : o.repeat;
  if (rep) { out.repeat = rep; out.repeatType = o.repeatType || 'loop'; if (o.repeatDelay) out.repeatDelay = o.repeatDelay; }
  return out;
}

// ---------------------------------------------------------------- component analysis
function findComponent(ast) {
  const topConsts = new Map();
  let jsxRoot = null;
  const ctlNames = new Set();
  const fns = {};   // name -> function node (startAnimation, stopAnimation, handleMouseEnter ...)
  let handleKeys = null;
  const visit = (n, depth) => {
    if (!n || typeof n.type !== 'string') return;
    if (n.type === 'VariableDeclarator' && n.id.type === 'Identifier') {
      const init = n.init;
      if (init && !topConsts.has(n.id.name) && !(init.type === 'CallExpression' && /^use[A-Z]/.test(init.callee.name || ''))) topConsts.set(n.id.name, init);
      if (init && init.type === 'CallExpression' && init.callee.name === 'useAnimation') ctlNames.add(n.id.name);
      if (init && init.type === 'CallExpression' && init.callee.name === 'useCallback' && /Function/.test(init.arguments[0].type)) fns[n.id.name] = init.arguments[0];
    }
    if (n.type === 'CallExpression' && n.callee.name === 'useImperativeHandle') {
      const f = n.arguments[1];
      const walkRet = (b) => { for (const st of b.body || []) if (st.type === 'ReturnStatement' && st.argument.type === 'ObjectExpression') handleKeys = st.argument; };
      if (f.body.type === 'BlockStatement') walkRet(f.body); else if (f.body.type === 'ObjectExpression') handleKeys = f.body;
    }
    if ((n.type === 'JSXElement') && !jsxRoot) { const nm = n.openingElement.name; if ((nm.type === 'JSXIdentifier' && nm.name === 'svg') || (nm.type === 'JSXMemberExpression' && nm.property.name === 'svg')) jsxRoot = n; }
    for (const k of Object.keys(n)) {
      if (k === 'loc' || k === 'start' || k === 'end') continue;
      const v = n[k];
      if (Array.isArray(v)) v.forEach((c) => visit(c, depth + (n.type === 'Program' ? 0 : 1)));
      else if (v && typeof v.type === 'string') visit(v, depth + (n.type === 'Program' ? 0 : 1));
    }
  };
  visit(ast.program, 0);
  return { topConsts, jsxRoot, ctlNames, fns, handleKeys };
}

function flagsOf(src) {
  const f = [];
  if (/\buseEffect\b/.test(src)) f.push('useEffect');
  if (/\buseAnimate\b/.test(src)) f.push('useAnimate');
  if (/\bsetTimeout\b|\bsetInterval\b/.test(src)) f.push('timer');
  return f;
}

// The statements run on hover: [{ctl, label|fn, override, awaited}] in order.
function readSteps(fn, ctlNames, scope, refValue, fns) {
  const steps = [];
  const body = fn.body.type === 'BlockStatement' ? fn.body.body : [{ type: 'ExpressionStatement', expression: fn.body }];
  const isRef = (n) => n.type === 'MemberExpression' && n.property.name === 'current';
  const startCall = (c, awaited) => {
    if (c.type === 'CallExpression' && c.callee.type === 'MemberExpression' && c.callee.property.name === 'start' && c.callee.object.type === 'Identifier' && ctlNames.has(c.callee.object.name)) {
      const a0 = c.arguments[0];
      const arg = a0.type === 'StringLiteral' ? a0.value : ev(a0, scope);
      steps.push({ ctl: c.callee.object.name, arg, override: c.arguments[1] ? ev(c.arguments[1], scope) : undefined, awaited });
      return true;
    }
    return false;
  };
  const expr = (e, awaited) => {
    if (e.type === 'AwaitExpression') return expr(e.argument, true);
    if (e.type === 'CallExpression' && e.callee.type === 'MemberExpression' && e.callee.property.name === 'catch') return expr(e.callee.object, awaited);   // controls.start(..).catch(() => {})
    if (e.type === 'CallExpression' && e.callee.type === 'Identifier' && fns[e.callee.name] && !e.arguments.length) { run(fns[e.callee.name].body.type === 'BlockStatement' ? fns[e.callee.name].body.body : [{ type: 'ExpressionStatement', expression: fns[e.callee.name].body }]); return; }
    if (startCall(e, awaited)) return;
    if (e.type === 'CallExpression' && e.callee.type === 'MemberExpression' && e.callee.object.name === 'Promise' && e.callee.property.name === 'all') {
      const first = steps.length;
      for (const x of e.arguments[0].elements) if (!startCall(x, false)) fail('Promise.all member');
      if (awaited) steps.push({ barrier: true, from: first });
      return;
    }
    if (e.type === 'AssignmentExpression' && isRef(e.left)) return;
    if (e.type === 'OptionalCallExpression' || (e.type === 'CallExpression' && /^on[A-Z]/.test(e.callee.name || ''))) return;
    fail('statement ' + e.type + (e.callee ? ' ' + (e.callee.name || e.callee.property?.name) : ''));
  };
  const run = (stmts) => {
    for (const st of stmts) {
      if (st.type === 'ExpressionStatement') expr(st.expression, false);
      else if (st.type === 'ReturnStatement') return true;
      else if (st.type === 'IfStatement') {
        // `if (isAnimatingRef.current) return;`: the ref is false when a run starts and true when it stops
        const neg = st.test.type === 'UnaryExpression' && st.test.operator === '!';
        const t = neg ? st.test.argument : st.test;
        if (t.type === 'MemberExpression' && isRef(t)) {
          if ((neg ? !refValue : refValue) && st.consequent) { if (run(st.consequent.type === 'BlockStatement' ? st.consequent.body : [st.consequent])) return true; }
          continue;
        }
        fail('if statement');
      } else if (st.type === 'TryStatement') { run(st.block.body); }
      else if (st.type === 'EmptyStatement') continue;
      else fail('statement ' + st.type);
    }
    return false;
  };
  run(body);
  return steps;
}

// ---------------------------------------------------------------- one icon
function convertIcon(name, file) {
  const code = fs.readFileSync(file, 'utf8');
  const early = flagsOf(code);
  const ast = parse(code, { sourceType: 'module', plugins: ['jsx', 'typescript'] });
  const comp = findComponent(ast);
  if (!comp.jsxRoot) fail('no svg element');
  if (early.includes('useAnimate')) fail('useAnimate');

  const root = new Scope({ size: 24 });
  const consts = new Scope({}, root);
  const cache = {};
  const resolveTop = (n) => {   // top-level consts are evaluated on first use
    if (n in cache) return cache[n];
    const init = comp.topConsts.get(n);
    cache[n] = undefined;
    const v = ev(init, consts);
    cache[n] = v;
    return v;
  };
  for (const n of comp.topConsts.keys()) Object.defineProperty(consts.vars, n, { get: () => resolveTop(n), enumerable: true, configurable: true });
  for (const c of comp.ctlNames) consts.vars[c] = { __ctl: c };

  // 1. drawing tree
  const rootEl = comp.jsxRoot;
  const tree = buildNode(rootEl, consts);
  tree.isRoot = true;

  // 2. flatten in document order; inherit controls, custom, initial; register stagger children
  const all = [];
  const label = (v) => (v && typeof v === 'object' && v.__ctl) ? v.__ctl : undefined;
  const walk = (node, inh, parentIdx) => {
    node.index = all.length; all.push(node);
    const ownCtl = node.animate !== undefined ? label(node.animate) : undefined;
    if (node.animate !== undefined && ownCtl === undefined) fail('animate prop is not a controls object');
    node.ctl = ownCtl ?? inh.ctl;
    node.controlling = ownCtl !== undefined;
    node.customV = node.custom !== undefined ? node.custom : inh.custom;
    node.initialV = node.initial !== undefined ? node.initial : inh.initial;
    node.vparent = node.motion ? inh.motion : undefined;
    if (node.motion && node.variants && !node.controlling && inh.motion) { inh.motion.vkids = inh.motion.vkids || []; node.vorder = inh.motion.vkids.length; inh.motion.vkids.push(node); }
    const next = { ctl: node.ctl, custom: node.customV, initial: node.initialV, motion: node.motion ? node : inh.motion };
    for (const k of node.kids) walk(k, next, node.index);
  };
  walk(tree, { ctl: undefined, custom: undefined, initial: undefined, motion: undefined }, -1);

  // 3. controllers -> steps
  const fnStart = comp.fns.startAnimation || fnFromHandle(comp.handleKeys, 'startAnimation', comp.fns);
  const fnStop = comp.fns.stopAnimation || fnFromHandle(comp.handleKeys, 'stopAnimation', comp.fns);
  if (!fnStart) fail('no startAnimation');
  if (early.includes('useEffect') && !comp.fns.startAnimation && !(comp.handleKeys && comp.handleKeys.properties.some((p) => p.value.type !== 'Identifier' && /Function/.test(p.value.type) && p.value.body.type === 'BlockStatement' || /Function/.test(p.value.type) && p.value.body.type === 'CallExpression' && p.value.body.callee.name === 'controls'))) fail('state-driven animation (useEffect)');
  let startSteps = readSteps(fnStart, comp.ctlNames, consts, false, comp.fns);
  let stopSteps = fnStop ? readSteps(fnStop, comp.ctlNames, consts, true, comp.fns) : [...comp.ctlNames].map((c) => ({ ctl: c, arg: 'normal', awaited: false }));
  if (!startSteps.length) fail('startAnimation starts nothing');

  // 4. simulation
  const els = all.filter((n) => n.motion && n.variants);
  const variantOf = (n, arg) => {
    let v;
    if (typeof arg === 'string') v = n.variants[arg]; else v = arg;
    if (typeof v === 'function') v = v(n.customV);
    return v;
  };
  // A variant target as [[prop, value | keyframes]]: units stripped, aliases resolved, origins noted on the node.
  const unit = (k, v) => {
    if (typeof v !== 'string') return [k, v];
    const m = /^(-?\d*\.?\d+)(px|deg|%)?$/.exec(v.trim());
    if (!m) return [k, v];
    if (m[2] === '%') return [k === 'x' ? 'xPercent' : k === 'y' ? 'yPercent' : fail('percent for ' + k), +m[1]];
    return [k, +m[1]];
  };
  const entriesOf = (n, target) => {
    const out = [];
    for (const [k0, v0] of Object.entries(target)) {
      if (ORIGIN_KEYS.has(k0)) { n.originV = { ...n.originV, [k0]: v0 }; continue; }
      if (IGNORED.has(k0)) continue;
      const k = ALIAS[k0] || k0;
      if (!PROPS.has(k)) fail('property ' + k0);
      if (Array.isArray(v0)) { const m = v0.map((x) => unit(k, x)); out.push([m[0][0], m.map((x) => x[1])]); }
      else { const [kk, v] = unit(k, v0); out.push([kk, v]); }
    }
    return out;
  };
  const stateOf = new Map();
  const attrNum = (n, p) => (n.attrs[p] !== undefined && !isNaN(+n.attrs[p])) ? +n.attrs[p] : undefined;
  const cur = (n) => stateOf.get(n);

  // base state
  for (const n of els) {
    const base = {};
    const init = n.initialV;
    let t0;
    if (init && typeof init === 'object') t0 = init;
    else if (typeof init === 'string') t0 = variantOf(n, init);
    else if (n.variants.normal) t0 = variantOf(n, 'normal');
    if (t0) for (const [k, v] of entriesOf(n, t0)) {
      const val = Array.isArray(v) ? v.at(-1) : v;
      if (val !== null && val !== undefined && val !== 'currentColor') base[k] = val;
    }
    stateOf.set(n, { vals: base, baseVals: { ...base } });
  }
  const getCur = (n, p) => {
    const s = cur(n).vals;
    if (p in s) return s[p];
    if (ATTR_PROPS.has(p)) { const a = attrNum(n, p); if (a !== undefined || (p === 'd' || p === 'points') && n.attrs[p]) return a ?? n.attrs[p]; }
    if (p === 'strokeWidth') return +(tree.attrs['stroke-width'] ?? 2);   // inherited from the root
    if (p in DEFAULTS) return DEFAULTS[p];
    return fail('no start value for ' + p);
  };

  const getCur0 = () => +(tree.attrs['stroke-width'] ?? 2);
  const orchestration = (n, arg, override) => {
    const par = n.vparent;
    if (!par || !par.variants || n.controlling || n.vorder === undefined) return 0;
    let pv = variantOf(par, arg);
    if (!pv) return 0;
    const tr = (pv.transition) || {};
    const sc = tr.staggerChildren || 0, dc = tr.delayChildren || 0;
    const nk = par.vkids.length;
    const idx = tr.staggerDirection === -1 ? nk - 1 - n.vorder : n.vorder;
    return dc + idx * sc;
  };

  const play = (steps) => {
    // returns { perEl: Map(node -> tracks), end }
    const perEl = new Map();
    let cursor = 0, end = 0;
    const stepEnds = [];
    for (const st of steps) {
      if (st.barrier) { cursor = Math.max(...stepEnds.slice(st.from)); continue; }
      let stEnd = cursor;
      for (const n of els) {
        if (n.ctl !== st.ctl) continue;
        const target = variantOf(n, st.arg);
        if (!target) continue;
        const stagger = orchestration(n, st.arg);
        const rawTr = st.override !== undefined ? st.override : (target.transition !== undefined ? target.transition : n.transition);
        const groups = new Map();
        for (const [k, v] of entriesOf(n, target)) {
          const start = getCur(n, k);
          let kf = Array.isArray(v) ? v.map((x) => x === null ? start : x) : [v];
          const keyframes = kf.length > 1;
          if (!keyframes) { if (kf[0] === start) continue; kf = [start, kf[0]]; }
          if (kf.some((x) => typeof x === 'string' && k !== 'd' && k !== 'points' && k !== 'fill') ) fail('string value for ' + k);
          if (kf.every((x) => x === kf[0])) { cur(n).vals[k] = kf[0]; continue; }
          const vt = normTransition(valueTransition(rawTr, k), k, keyframes, kf.at(-1), stagger);
          const gk = JSON.stringify(vt);
          if (!groups.has(gk)) groups.set(gk, { tr: vt, props: {}, pre: {} });
          const g = groups.get(gk);
          g.props[k] = kf.map((x) => typeof x === 'number' ? round(x) : x);
          if (keyframes && kf[0] !== start) g.pre[k] = typeof start === 'number' ? round(start) : start;   // the value jumps here -> first keyframe
        }
        for (const g of groups.values()) {
          const tr = g.tr;
          const props = Object.fromEntries(Object.entries(g.props).sort(([a], [b]) => a < b ? -1 : 1));
          if (tr.times && Object.values(props).some((a) => a.length !== tr.times.length)) delete tr.times;
          const pre = Object.fromEntries(Object.entries(g.pre).sort(([a], [b]) => a < b ? -1 : 1));
          const track = { at: round(cursor), ...tr, props, ...(Object.keys(pre).length ? { pre } : {}) };
          if (!perEl.has(n)) perEl.set(n, []);
          perEl.get(n).push(track);
          const rep = tr.repeat === undefined ? 0 : tr.repeat;
          const total = rep === -1 ? Infinity : tr.delay + tr.duration * (rep + 1) + (tr.repeatDelay || 0) * rep;
          stEnd = Math.max(stEnd, cursor + total);
          end = Math.max(end, cursor + total);
          for (const [k, a] of Object.entries(props)) {
            const back = rep > 0 && tr.repeatType !== 'loop' && (rep + 1) % 2 === 0;
            cur(n).vals[k] = back ? a[0] : a.at(-1);
          }
        }
        // a variant whose values already match still moves the state
        for (const [k, v] of entriesOf(n, target)) if (!Array.isArray(v) && v !== null) cur(n).vals[k] = v;
      }
      stepEnds.push(stEnd);
      if (st.awaited) { cursor = stEnd; if (!isFinite(cursor)) break; }
    }
    return { perEl, end };
  };

  const startRun = play(startSteps);
  const stopRun = play(stopSteps);
  if (!startRun.perEl.size) fail('start run changes nothing');

  // 5. spec
  const originOf = (n) => {
    const st = { ...(n.style || {}), ...(n.originV || {}) };
    let ox = st.originX, oy = st.originY, box = st.transformBox === 'view-box' ? 'view' : 'fill';
    let ts = typeof st.transformOrigin === 'string' ? st.transformOrigin.trim().split(/\s+/) : null;
    const kw = { left: '0%', right: '100%', top: '0%', bottom: '100%', center: '50%' };
    if (ts) {
      if (ts.length === 1) ts = ts[0] === 'top' || ts[0] === 'bottom' ? ['center', ts[0]] : [ts[0], 'center'];
      if (['top', 'bottom'].includes(ts[0]) || ['left', 'right'].includes(ts[1])) ts = [ts[1], ts[0]];
      [ox, oy] = ts.map((x) => kw[x] ?? x);
    }
    const fmt = (v) => v === undefined ? '50%' : typeof v === 'number' ? round(v * 100) + '%' : String(v);
    return { x: fmt(ox), y: fmt(oy), box };
  };
  const specEls = [];
  const sorted = [...new Set([...startRun.perEl.keys(), ...stopRun.perEl.keys()])].sort((a, b) => a.index - b.index);
  for (const n of sorted) {
    const e = { i: n.index };
    const usesT = [...(startRun.perEl.get(n) || []), ...(stopRun.perEl.get(n) || [])].some((t) => Object.keys(t.props).some((p) => ['scale', 'scaleX', 'scaleY', 'x', 'y', 'rotate', 'skewX', 'skewY'].includes(p)));
    if (usesT) e.origin = originOf(n);
    const base = {};
    for (const [k, v] of Object.entries(cur(n).baseVals)) {
      if (!(k in DEFAULTS) || DEFAULTS[k] !== v) { if (n.index === 0 && ['x', 'y'].includes(k)) fail('root x/y initial'); base[k] = v; }
    }
    // an inherited stroke width has no attribute to tween: write it down
    const tracked = new Set([...(startRun.perEl.get(n) || []), ...(stopRun.perEl.get(n) || [])].flatMap((t) => Object.keys(t.props)));
    if (tracked.has('strokeWidth') && n.attrs['stroke-width'] === undefined) base.strokeWidth = getCur0();
    if (Object.keys(base).length) e.base = base;
    if (startRun.perEl.has(n)) e.start = startRun.perEl.get(n);
    if (stopRun.perEl.has(n)) e.reset = stopRun.perEl.get(n);
    specEls.push(e);
  }
  const spec = { v: 1, name, dur: isFinite(startRun.end) ? round(startRun.end) : null, rdur: round(stopRun.end), els: specEls };

  // 6. static svg
  return { svg: serialize(tree), spec };
}

function fnFromHandle(obj, key, fns) {
  if (!obj) return null;
  const p = obj.properties.find((x) => x.key && x.key.name === key);
  if (!p) return null;
  const v = p.value ?? null;
  if (v && v.type === 'Identifier') return fns[v.name] || null;
  if (v && /Function/.test(v.type)) return v;
  return null;
}

// ---------------------------------------------------------------- svg text
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');
function styleText(st) {
  const keep = [];
  for (const [k, v] of Object.entries(st || {})) if (k === 'overflow' && typeof v === 'string') keep.push(`overflow:${v}`);
  return keep.join(';');
}
function serialize(node) {
  const a = { ...node.attrs };
  if (node.isRoot) {
    for (const k of ['xmlns']) delete a[k];
    const head = { xmlns: 'http://www.w3.org/2000/svg', viewBox: a['viewBox'] || '0 0 24 24', fill: a.fill || 'none', stroke: a.stroke || 'currentColor',
      'stroke-width': a['stroke-width'] || '2', 'stroke-linecap': a['stroke-linecap'] || 'round', 'stroke-linejoin': a['stroke-linejoin'] || 'round' };
    for (const k of Object.keys(head)) delete a[k];
    Object.assign(a, {}); Object.keys(a).forEach((k) => { if (a[k] === undefined) delete a[k]; });
    var attrs = { ...head, ...a };
  } else attrs = a;
  const sty = styleText(node.style);
  const parts = Object.entries(attrs).filter(([, v]) => v !== false && v !== undefined).map(([k, v]) => v === true ? k : `${k}="${esc(typeof v === 'number' ? round(v) : v)}"`);
  if (sty) parts.push(`style="${sty}"`);
  const open = `<${node.tag}${parts.length ? ' ' + parts.join(' ') : ''}`;
  if (!node.kids.length && !node.text) return open + '/>';
  return `${open}>${node.text ? esc(node.text).replace(/&quot;/g, '"') : ''}${node.kids.map(serialize).join('')}</${node.tag}>`;
}

// ---------------------------------------------------------------- metadata
function keywordIndex() {
  const ast = parse(fs.readFileSync(path.join(SRC, 'icons/index.ts'), 'utf8'), { sourceType: 'module', plugins: ['jsx', 'typescript'] });
  const out = {};
  const visit = (n) => {
    if (!n || typeof n.type !== 'string') return;
    if (n.type === 'VariableDeclarator' && n.id.name === 'ICON_LIST') {
      let arr = n.init;
      while (arr.type === 'CallExpression') arr = arr.callee.object;   // [...].sort(...)
      for (const el of arr.elements) {
        const o = {};
        for (const p of el.properties) if (p.key.name === 'name') o.name = p.value.value; else if (p.key.name === 'keywords') o.keywords = p.value.elements.map((x) => x.value);
        out[o.name] = o.keywords || [];
      }
      return;
    }
    for (const k of Object.keys(n)) { const v = n[k]; if (Array.isArray(v)) v.forEach(visit); else if (v && typeof v.type === 'string') visit(v); }
  };
  visit(ast.program);
  return out;
}

function lucideMeta(name) {
  const parts = name.split('-');
  for (let n = parts.length; n >= 1; n--) {
    const f = path.join(LUCIDE, parts.slice(0, n).join('-') + '.json');
    if (fs.existsSync(f)) { const j = JSON.parse(fs.readFileSync(f, 'utf8')); return { tags: j.tags || [], groups: j.categories || [], exact: n === parts.length }; }
  }
  return { tags: [], groups: [], exact: false };
}

// ---------------------------------------------------------------- gallery page
function galleryHtml(names) {
  const scripts = names.map((n) => `<script src="lucide-animated/${n}.js"></script>`).join('\n');
  const cells = names.map((n) => `<div class="c"><i data-n="${n}"></i><span>${n}</span></div>`).join('');
  return `<!doctype html>
<!-- GENERATED by tools/iconanim/convert.mjs. Never edit. Human check page: every converted icon on ONE paused GSAP timeline. -->
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Animated icons</title>
<style>
:root{color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:#0d1117;color:#e6edf3;font:13px/1.3 system-ui,sans-serif}
header{position:sticky;top:0;z-index:2;display:flex;gap:14px;align-items:center;padding:10px 16px;background:#161b22;border-bottom:1px solid #30363d}
button{font:inherit;color:inherit;background:#21262d;border:1px solid #30363d;border-radius:6px;padding:6px 14px;cursor:pointer}
input[type=range]{flex:1}
#time{font-variant-numeric:tabular-nums;min-width:5ch}
main{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:6px;padding:16px}
.c{display:flex;flex-direction:column;align-items:center;gap:8px;padding:14px 4px 10px;border-radius:8px;background:#161b22}
.c i{display:block;width:40px;height:40px;color:#e6edf3}
.c svg{width:100%;height:100%;display:block;overflow:visible}
.c span{font-size:11px;color:#8b949e;text-align:center;word-break:break-all}
</style></head><body>
<header><button id="pp">Pause</button><input id="scrub" type="range" min="0" max="1000" value="0"><span id="time">0.0 s</span><span>${names.length} icons</span></header>
<main>${cells}</main>
<script src="../../_runtime/vendor/gsap.min.js"></script>
<script src="../../_runtime/animicon.js"></script>
${scripts}
<script>
(function () {
  var SPAN = 8;   // seconds on the timeline; icons loop inside it
  var tl = gsap.timeline({ paused: true, repeat: -1 });
  document.querySelectorAll('i[data-n]').forEach(function (el) {
    var n = 'lucide-animated/' + el.dataset.n;
    AnimIcon.mount(el, n);
    AnimIcon.play(tl, el, n, 0.3, { loop: true, gap: 0.5, until: SPAN });
  });
  tl.to({}, { duration: SPAN }, 0);
  var pp = document.getElementById('pp'), sc = document.getElementById('scrub'), tm = document.getElementById('time');
  function show() { tm.textContent = tl.time().toFixed(1) + ' s'; if (!sc.matches(':active')) sc.value = Math.round(tl.time() / SPAN * 1000); }
  gsap.ticker.add(show);
  pp.onclick = function () { if (tl.paused()) { tl.play(); pp.textContent = 'Pause'; } else { tl.pause(); pp.textContent = 'Play'; } };
  sc.oninput = function () { tl.pause(); pp.textContent = 'Play'; tl.time(sc.value / 1000 * SPAN); };
  tl.play(0);
})();
</script></body></html>
`;
}

// ---------------------------------------------------------------- main
function main() {
  const files = fs.readdirSync(path.join(SRC, 'icons')).filter((f) => f.endsWith('.tsx')).sort();
  fs.mkdirSync(OUT, { recursive: true });
  const keywords = keywordIndex();
  const done = [], skipped = [];
  const tags = {};
  const keep = new Set(['TAGS.json']);
  for (const f of files) {
    const name = f.replace(/\.tsx$/, '');
    try {
      const { svg, spec } = convertIcon(name, path.join(SRC, 'icons', f));
      const key = `lucide-animated/${name}`;
      fs.writeFileSync(path.join(OUT, name + '.svg'), svg + '\n');
      fs.writeFileSync(path.join(OUT, name + '.anim.json'), JSON.stringify(spec, null, 1) + '\n');
      fs.writeFileSync(path.join(OUT, name + '.js'), `// GENERATED by tools/iconanim from ${name}.anim.json. Never edit.\n(window.VF_ANIM_ICONS = window.VF_ANIM_ICONS || {})[${JSON.stringify(key)}] = ${JSON.stringify({ svg, spec })};\n`);
      for (const ext of ['.svg', '.anim.json', '.js']) keep.add(name + ext);
      const meta = lucideMeta(name);
      const tagList = [...new Set([...(keywords[name] || []), ...meta.tags])];
      tags[name] = { tags: tagList, groups: meta.groups };
      done.push({ name, dur: spec.dur, tracks: spec.els.length, loose: !meta.exact });
    } catch (e) {
      if (!(e instanceof Unsupported)) { e.message = name + ': ' + e.message; throw e; }
      skipped.push({ name, reason: e.message });
    }
  }
  // remove files of icons that are no longer converted
  for (const f of fs.readdirSync(OUT)) if (!keep.has(f)) fs.rmSync(path.join(OUT, f));
  const sortedTags = Object.fromEntries(Object.keys(tags).sort().map((k) => [k, tags[k]]));
  fs.writeFileSync(path.join(OUT, 'TAGS.json'), JSON.stringify(sortedTags, null, 1) + '\n');
  fs.writeFileSync(path.join(OUT_SET, 'GALLERY.html'), galleryHtml(done.map((d) => d.name)));

  const total = files.length;
  const infinite = done.filter((d) => d.dur === null).length;
  const byReason = {};
  for (const s of skipped) (byReason[s.reason] = byReason[s.reason] || []).push(s.name);
  const md = [
    '# lucide-animated conversion report', '',
    '<!-- GENERATED by tools/iconanim/convert.mjs. Never edit. -->', '',
    `- Icons in the source: ${total}`,
    `- Converted: ${done.length} (${(done.length / total * 100).toFixed(1)}%)`,
    `- Skipped: ${skipped.length}`,
    `- Converted icons whose run repeats forever: ${infinite}`,
    `- Converted icons with no exact Lucide metadata file (closest base name used, or empty groups): ${done.filter((d) => d.loose).length}`, '',
    '## Skipped icons', '',
    ...(skipped.length ? skipped.map((s) => `- \`${s.name}\`: ${s.reason}`) : ['None.']), '',
    '## Skip reasons', '',
    ...Object.entries(byReason).sort((a, b) => b[1].length - a[1].length || (a[0] < b[0] ? -1 : 1)).map(([r, l]) => `- ${r}: ${l.length}`), '',
  ].join('\n');
  fs.writeFileSync(REPORT, md);
  console.log(`converted ${done.length}/${total}, skipped ${skipped.length}`);
}

main();
