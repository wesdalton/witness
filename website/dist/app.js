import {Swarm, DEFAULTS, random, validateConfig} from './engine.js';

const $ = id => document.getElementById(id);
const C = {wrong: '#c2410c', correct: '#0f766e', neutral: '#b5b9ad', check: '#3f51b5', ink: '#18211d'};
const PROTOCOLS = ['endorsement', 'provenance', 'reserved'];
const POLICY = {
  endorsement: {label: 'Peer endorsements', color: '#c2410c'},
  provenance: {label: 'Original sources', color: '#2f6db3'},
  reserved: {label: 'Sources + reserve', color: '#7a4fc9'},
};
const FIELDS = ['population', 'topology', 'communication', 'delay', 'seedShare', 'allocation', 'truth', 'seed', 'initialEvidence', 'reinforcement'];
const FRACTIONS = ['communication', 'seedShare', 'initialEvidence'];
const fmt = n => n.toLocaleString('en-US');
const pct = (n, digits = 1) => `${(n * 100).toFixed(digits)}%`;
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;

const SCENARIOS = [
  {id: 'echoes', title: 'Echoes', q: 'Does repeated agreement mislead the swarm?', protocol: 'endorsement', config: {},
    detail: 'Agents weigh what their neighbours say. A few start with the false report. <b>Watch</b> orange spread before any check returns, then the correction travel back.'},
  {id: 'sources', title: 'Count sources, not voices', q: 'Does tracking where evidence came from help?', protocol: 'provenance', config: {},
    detail: 'Agents count distinct original sources, so repeats of one report add nothing. <b>Compare</b> the blue line with the orange one.'},
  {id: 'reserve', title: 'Keep a checking reserve', q: 'What if agents always set aside some budget for checks?', protocol: 'reserved', config: {},
    detail: 'At least 15% of unchecked agents request the probe each round. <b>Watch</b> the effort split and the purple line.'},
  {id: 'true', title: 'When the report is true', q: 'What does checking cost when nothing is wrong?', protocol: 'reserved', config: {truth: true},
    detail: 'Same swarm, but Patch A really works. <b>Look at</b> effort spent on checks that change nothing.'},
  {id: 'loop', title: 'Switch off the loop', q: 'What if confidence did not reduce checking?', protocol: 'endorsement', config: {allocation: 'fixed'},
    detail: 'Agents check at a fixed rate however sure they feel, which removes the feedback loop. <b>Compare</b> with Echoes.'},
  {id: 'scale', title: 'Ten thousand agents', q: 'Do the same rules behave the same at scale?', protocol: 'endorsement', config: {population: 10000},
    detail: 'Same rules, 10,000 agents. This shows the engine scales. It says nothing new about real swarms.'},
];

let config = validateConfig({...DEFAULTS});
let protocol = 'endorsement';
let scenario = 'echoes';
let live, precomputed = {}, summaries = null, extra = null, job = 0;
let running = false, timer = null, positions = [], visibleEdges = [], totalEdges = 0, selected = null, toastTimer;

function toast(message) {
  $('toast').textContent = message; $('toast').hidden = false;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => { $('toast').hidden = true; }, 3200);
}
function status(message) { $('status').textContent = message; }
const wrongPhrase = () => config.truth ? 'wrongly reject the true claim' : 'believe the false claim';

/* ---------- configuration ---------- */
function writeControls() {
  for (const key of FIELDS) $(key).value = FRACTIONS.includes(key) ? Math.round(config[key] * 100) : String(config[key]);
  for (const key of FRACTIONS) $(`${key}-value`).textContent = `${Math.round(config[key] * 100)}%`;
  $('delay-value').textContent = `${config.delay} round${config.delay === 1 ? '' : 's'}`;
  $('reinforcement-value').textContent = Number(config.reinforcement).toFixed(1);
}
function readControls() {
  const next = {...config};
  for (const key of FIELDS) {
    const raw = $(key).value;
    next[key] = FRACTIONS.includes(key) ? Number(raw) / 100
      : key === 'truth' ? raw === 'true'
      : ['topology', 'allocation'].includes(key) ? raw : Number(raw);
  }
  return validateConfig(next);
}
const baseKey = c => JSON.stringify({...c, protocol: null});

/* ---------- simulation lifecycle ---------- */
function stop() {
  running = false; clearTimeout(timer);
  $('play-icon').textContent = '▶'; $('play-label').textContent = live && live.round >= live.config.rounds ? 'Replay' : 'Run';
}
function resetLive() {
  stop();
  live = new Swarm({...config, protocol});
  selected = null; $('agent-card').hidden = true;
  $('agent-id').max = config.population; $('agent-id').value = 1;
  $('round-total').textContent = config.rounds;
  layout(); render();
}
function applyConfig(next, {recompute = true} = {}) {
  const changed = baseKey(next) !== baseKey(config);
  config = next; writeControls(); updateTruthLabels();
  resetLive();
  if (recompute && (changed || !summaries)) precompute();
  syncPolicySwitch(); syncURL();
}
function precompute() {
  const token = ++job;
  precomputed = {}; summaries = null; extra = null;
  for (const p of PROTOCOLS) precomputed[p] = new Swarm({...config, protocol: p});
  const list = Object.values(precomputed);
  if (scenario === 'loop') {
    extra = new Swarm({...config, protocol: 'endorsement', allocation: config.allocation === 'adaptive' ? 'fixed' : 'adaptive'});
    list.push(extra);
  }
  $('scenario-finding').textContent = 'Computing all three policies…';
  const work = () => {
    if (token !== job) return;
    const started = performance.now();
    while (performance.now() - started < 14) {
      const pending = list.filter(s => s.round < s.config.rounds);
      if (!pending.length) break;
      for (const s of pending) s.step();
    }
    if (list.some(s => s.round < s.config.rounds)) { drawChart(); setTimeout(work, 0); return; }
    summaries = Object.fromEntries(PROTOCOLS.map(p => [p, summarize(precomputed[p].history)]));
    renderTable(); renderFinding(); drawChart();
  };
  work();
}
function summarize(history) {
  let peak = 0, peakRound = 0;
  history.forEach(h => { if (h.wrong > peak) { peak = h.wrong; peakRound = h.round; } });
  const last = history.at(-1);
  return {
    peak, peakRound,
    mean: history.reduce((s, h) => s + h.wrong, 0) / history.length,
    above: history.filter(h => h.wrong >= 0.1).length,
    checkShare: last.effort ? last.requests * 4 / last.effort : 0,
    checkUnits: last.requests * 4,
    final: last.wrong, finalCorrect: last.correct,
  };
}

/* ---------- guided scenarios ---------- */
function renderScenarios() {
  const list = $('scenario-list'); list.replaceChildren();
  SCENARIOS.forEach((s, i) => {
    const li = document.createElement('li');
    const b = document.createElement('button');
    b.className = 'scenario'; b.type = 'button'; b.dataset.id = s.id;
    b.setAttribute('aria-pressed', String(s.id === scenario));
    b.innerHTML = `<span class="n">0${i + 1}</span><span class="t"></span><span class="q"></span>`;
    b.querySelector('.t').textContent = s.title; b.querySelector('.q').textContent = s.q;
    if (s.id === scenario) {
      const d = document.createElement('span'); d.className = 'scenario-detail'; d.innerHTML = s.detail; b.append(d);
    }
    b.addEventListener('click', () => activateScenario(s.id, true));
    li.append(b); list.append(li);
  });
}
function activateScenario(id, autoplay = false) {
  const s = SCENARIOS.find(x => x.id === id); if (!s) return;
  scenario = id; protocol = s.protocol;
  renderScenarios();
  config = validateConfig({...DEFAULTS, ...s.config});
  summaries = null;
  writeControls(); updateTruthLabels(); resetLive(); precompute(); syncPolicySwitch(); syncURL();
  status(`Scenario: ${s.title}. ${autoplay ? 'Running.' : 'Press Run to watch it unfold.'}`);
  if (autoplay && !reduceMotion) play();
}
function renderFinding() {
  const el = $('scenario-finding'); if (!summaries) return;
  const e = summaries.endorsement, p = summaries.provenance, r = summaries.reserved;
  const P = (x, d = 0) => `<b>${pct(x, d)}</b>`;
  const W = x => `<b class="hl-wrong">${pct(x, 0)}</b>`;
  const ending = s => s.final === 0 ? 'every agent ended correct' : `${pct(s.final)} were still wrong at round ${config.rounds}`;
  let html;
  if (scenario === 'echoes') {
    html = `With peer endorsements, up to ${W(e.peak)} of agents came to ${wrongPhrase()} (round ${e.peakRound}). Only ${P(e.checkShare, 1)} of all effort went to checking. Once probe results spread, ${ending(e)}.`;
  } else if (scenario === 'sources') {
    html = p.peak > e.peak
      ? `Counting sources made things <b>worse</b> here: a peak of ${W(p.peak)} versus ${W(e.peak)} for endorsements. Under these rules one unverified report moves an agent to 68% support, past the 65% line counted as belief. Ignoring repeats does not make the first report less persuasive. This is exactly the kind of assumption a real-model study has to measure.`
      : `Counting sources lowered the peak from ${W(e.peak)} to ${W(p.peak)}. Repeats of one report no longer add confidence.`;
  } else if (scenario === 'reserve') {
    html = `The reserve raised checking from ${P(p.checkShare, 1)} to ${P(r.checkShare, 1)} of effort. Peak: ${W(r.peak)} with the reserve versus ${W(p.peak)} for sources alone. Each check takes ${config.delay} rounds to return, so extra checks land after the report has spread. Try lowering the check delay under “Change the assumptions”.`;
  } else if (scenario === 'true') {
    const worst = Math.max(e.peak, p.peak, r.peak);
    html = `With a true report, the most agents ever wrongly rejecting it under any policy was ${P(worst)}. The reserve still spent <b>${fmt(r.checkUnits)}</b> units on checks, versus <b>${fmt(e.checkUnits)}</b> for endorsements. Interventions have to be judged on true reports too, where checking is pure cost.`;
  } else if (scenario === 'loop' && extra) {
    const x = summarize(extra.history);
    const [fixed, adaptive] = config.allocation === 'fixed' ? [e, x] : [x, e];
    html = `Peak with a fixed checking rate: ${W(fixed.peak)}. With confidence-driven checking: ${W(adaptive.peak)}. In this model the loop changes little; the check delay and the pull of a single report matter more. Whether real agents check less when peers agree is the question this model cannot answer.`;
  } else if (scenario === 'scale') {
    html = `At ${fmt(config.population)} agents the peak was ${W(e.peak)} with endorsements and ${W(p.peak)} with source counting. Scale here is an engineering check, not evidence about real swarms.`;
  } else {
    html = `Custom settings. Peak share that ${wrongPhrase()}: endorsements ${W(e.peak)}, sources ${W(p.peak)}, reserve ${W(r.peak)}. Effort on checking: ${P(e.checkShare, 1)}, ${P(p.checkShare, 1)}, ${P(r.checkShare, 1)}.`;
  }
  el.innerHTML = html;
}

/* ---------- policy switch ---------- */
function syncPolicySwitch() {
  document.querySelectorAll('.policy-switch button').forEach(b => {
    const on = b.dataset.protocol === protocol;
    b.setAttribute('aria-checked', String(on)); b.tabIndex = on ? 0 : -1;
  });
  renderTable();
}
document.querySelectorAll('.policy-switch button').forEach((b, i, all) => {
  b.addEventListener('click', () => { protocol = b.dataset.protocol; config = validateConfig({...config, protocol}); resetLive(); syncPolicySwitch(); syncURL(); status(`Viewing ${POLICY[protocol].label.toLowerCase()}. Same agents and network.`); });
  b.addEventListener('keydown', ev => {
    if (!['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(ev.key)) return;
    ev.preventDefault();
    const next = all[(i + (ev.key === 'ArrowLeft' || ev.key === 'ArrowUp' ? all.length - 1 : 1)) % all.length];
    next.focus(); next.click();
  });
});

/* ---------- playback ---------- */
function advance() {
  live.step(); render();
  if (live.round >= live.config.rounds) {
    stop(); const m = live.history.at(-1);
    status(`Round ${live.round}: ${pct(m.wrong)} ${wrongPhrase()}, ${pct(m.correct)} correct, ${pct(m.uncertain)} undecided.`);
  }
}
function tick() { if (!running) return; advance(); if (running) timer = setTimeout(tick, config.population >= 10000 ? 140 : 95); }
function play() {
  if (live.round >= live.config.rounds) resetLive();
  running = true; $('play-icon').textContent = '❚❚'; $('play-label').textContent = 'Pause'; tick();
}
$('play').addEventListener('click', () => { if (running) { stop(); status(`Paused at round ${live.round}.`); } else play(); });
$('step').addEventListener('click', () => { stop(); if (live.round < live.config.rounds) advance(); });
$('restart').addEventListener('click', () => { resetLive(); status('Restarted at round 0.'); });
$('correct').addEventListener('click', () => {
  const count = live.injectCorrection(); render();
  status(`Gave the probe result to ${fmt(count)} agents at round ${live.round}, outside the effort budget. Only this run changes.`);
});

/* ---------- drawing ---------- */
function canvasContext(id) {
  const canvas = $(id), box = canvas.getBoundingClientRect(), dpr = Math.min(devicePixelRatio || 1, 2);
  const w = box.width, h = box.height;
  if (canvas.width !== Math.round(w * dpr) || canvas.height !== Math.round(h * dpr)) { canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr); }
  const ctx = canvas.getContext('2d'); ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, w, h);
  return {ctx, w, h};
}
function layout() {
  const n = config.population, seed = config.seed, hubs = Math.max(2, Math.ceil(Math.sqrt(n) / 2));
  positions = live.agents.map((a, i) => {
    if (config.topology === 'modular') {
      const group = Math.min(3, Math.floor(i * 4 / n));
      const angle = random(seed, i, 101) * Math.PI * 2, radius = Math.sqrt(random(seed, i, 102));
      return {x: [.27, .73, .27, .73][group] + Math.cos(angle) * radius * .2, y: [.27, .27, .73, .73][group] + Math.sin(angle) * radius * .2};
    }
    if (config.topology === 'hub' && i < hubs) {
      const a = i / hubs * Math.PI * 2;
      return {x: .5 + Math.cos(a) * .07, y: .5 + Math.sin(a) * .07};
    }
    const angle = i * 2.399963229728653 + seed * .01, radius = Math.sqrt((i + .5) / n);
    return {x: .5 + Math.cos(angle) * radius * .47, y: .5 + Math.sin(angle) * radius * .47};
  });
  totalEdges = live.graph.reduce((s, nb) => s + nb.length, 0) / 2;
  visibleEdges = [];
  for (let i = 0; i < live.graph.length; i++) for (const j of live.graph[i]) {
    if (j > i && (totalEdges <= 1600 || random(seed, i, j, 105) <= 1600 / totalEdges)) visibleEdges.push([i, j]);
  }
}
function project(p, w, h) {
  const top = 56, bottom = 60, side = 24, ah = h - top - bottom, aw = Math.min(w - 2 * side, ah * 1.7);
  return {x: (w - aw) / 2 + p.x * aw, y: top + p.y * ah};
}
function stateColor(a) {
  if (a.p > .35 && a.p < .65) return C.neutral;
  return (a.p >= .65) === config.truth ? C.correct : C.wrong;
}
function nodeRadius() { const n = config.population; return n <= 64 ? 7 : n <= 256 ? 4.6 : n <= 1024 ? 2.6 : 1.25; }
function drawNetwork() {
  const {ctx, w, h} = canvasContext('network');
  ctx.lineWidth = .7; ctx.strokeStyle = 'rgba(60,70,62,.10)'; ctx.beginPath();
  for (const [i, j] of visibleEdges) { const a = project(positions[i], w, h), b = project(positions[j], w, h); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); }
  ctx.stroke();
  const r = nodeRadius();
  for (const color of [C.neutral, C.correct, C.wrong]) {
    ctx.fillStyle = color; ctx.beginPath();
    for (const a of live.agents) if (stateColor(a) === color) { const p = project(positions[a.id], w, h); ctx.moveTo(p.x + r, p.y); ctx.arc(p.x, p.y, r, 0, Math.PI * 2); }
    ctx.fill();
  }
  if (config.population <= 1024) {
    ctx.lineWidth = r > 4 ? 1.8 : 1.2; ctx.strokeStyle = C.ink; ctx.beginPath();
    for (const a of live.agents) if (a.checked) { const p = project(positions[a.id], w, h); ctx.moveTo(p.x + r + 2.2, p.y); ctx.arc(p.x, p.y, r + 2.2, 0, Math.PI * 2); }
    ctx.stroke();
    ctx.setLineDash([2.5, 2]); ctx.strokeStyle = C.check; ctx.beginPath();
    for (const a of live.agents) if (a.pending !== null) { const p = project(positions[a.id], w, h); ctx.moveTo(p.x + r + 2.6, p.y); ctx.arc(p.x, p.y, r + 2.6, 0, Math.PI * 2); }
    ctx.stroke(); ctx.setLineDash([]);
  }
  if (selected !== null) {
    const p = project(positions[selected], w, h);
    ctx.strokeStyle = C.ink; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.arc(p.x, p.y, r + 7, 0, Math.PI * 2); ctx.stroke();
  }
  $('network-hint').textContent = totalEdges > 1600 ? `${fmt(visibleEdges.length)} of ${fmt(totalEdges)} links drawn · click an agent` : 'Click any agent to trace its evidence';
  const m = live.history.at(-1);
  $('network').setAttribute('aria-label', `${fmt(config.population)} agents at round ${live.round}: ${pct(m.wrong)} ${wrongPhrase()}, ${pct(m.correct)} correct, ${pct(m.uncertain)} undecided.`);
}
function drawChart() {
  const {ctx, w, h} = canvasContext('chart'), left = 44, right = 12, top = 10, bottom = 26;
  const rounds = config.rounds;
  const x = r => left + r / rounds * (w - left - right), y = v => top + (1 - v) * (h - top - bottom);
  ctx.font = '11px ui-monospace, Menlo, monospace'; ctx.fillStyle = '#6b746e'; ctx.lineWidth = 1;
  ctx.textAlign = 'right';
  for (const v of [0, .25, .5, .75, 1]) { ctx.strokeStyle = v ? '#ece8df' : '#cfc9bc'; ctx.beginPath(); ctx.moveTo(left, y(v)); ctx.lineTo(w - right, y(v)); ctx.stroke(); ctx.fillText(`${v * 100}%`, left - 8, y(v) + 4); }
  ctx.textAlign = 'center';
  for (let r = 0; r <= rounds; r += rounds >= 40 ? 10 : 5) ctx.fillText(String(r), x(r), h - 7);
  const line = (history, color, width, dash = [], alpha = 1) => {
    if (!history || history.length < 1) return;
    ctx.globalAlpha = alpha; ctx.strokeStyle = color; ctx.lineWidth = width; ctx.setLineDash(dash); ctx.beginPath();
    history.forEach((p, i) => i ? ctx.lineTo(x(p.round), y(p.wrong)) : ctx.moveTo(x(p.round), y(p.wrong)));
    ctx.stroke(); ctx.setLineDash([]); ctx.globalAlpha = 1;
  };
  for (const p of PROTOCOLS) if (p !== protocol && precomputed[p]) line(precomputed[p].history, POLICY[p].color, 1.8, [], .75);
  const watching = live && live.config.protocol === protocol ? live : null;
  const edited = watching && watching.interventions.length;
  if (precomputed[protocol]) line(precomputed[protocol].history, POLICY[protocol].color, 2, edited ? [5, 4] : [], edited ? .5 : .3);
  if (watching) {
    line(watching.history, POLICY[protocol].color, 3.2);
    ctx.strokeStyle = C.ink; ctx.lineWidth = 1; ctx.setLineDash([3, 3]);
    ctx.beginPath(); ctx.moveTo(x(watching.round), top); ctx.lineTo(x(watching.round), h - bottom); ctx.stroke(); ctx.setLineDash([]);
    ctx.fillStyle = C.check;
    for (const ev of watching.interventions) { ctx.beginPath(); ctx.arc(x(ev.round), h - bottom, 4, 0, Math.PI * 2); ctx.fill(); }
  }
  const key = $('chart-key'); key.replaceChildren();
  for (const p of PROTOCOLS) {
    const s = document.createElement('span'), i = document.createElement('i');
    i.style.background = POLICY[p].color; if (p === protocol) i.style.height = '4px';
    s.append(i, document.createTextNode(POLICY[p].label + (p === protocol ? ' (viewing)' : ''))); key.append(s);
  }
}
function renderTable() {
  const body = $('compare-body'); body.replaceChildren();
  for (const p of PROTOCOLS) {
    const tr = document.createElement('tr'); if (p === protocol) tr.className = 'selected';
    const th = document.createElement('th'); th.scope = 'row';
    const sw = document.createElement('i'); sw.style.background = POLICY[p].color; th.append(sw, document.createTextNode(POLICY[p].label)); tr.append(th);
    const s = summaries && summaries[p];
    const cells = s ? [pct(s.peak), pct(s.mean), String(s.above), pct(s.checkShare), pct(s.final)] : ['…', '…', '…', '…', '…'];
    for (const v of cells) { const td = document.createElement('td'); td.textContent = v; tr.append(td); }
    body.append(tr);
  }
}
function render() {
  const m = live.history.at(-1);
  let peak = 0, peakRound = 0; live.history.forEach(h => { if (h.wrong > peak) { peak = h.wrong; peakRound = h.round; } });
  $('round').textContent = live.round;
  $('wrong-now').textContent = pct(m.wrong);
  $('wrong-bar').style.width = `${m.wrong * 100}%`;
  $('wrong-peak').textContent = pct(peak);
  $('wrong-peak-round').textContent = `at round ${peakRound}`;
  $('checks').textContent = `${fmt(m.checks)} / ${fmt(m.pending)}`;
  $('probe-reach').textContent = `${pct(m.verifiedReach)} hold probe evidence`;
  const checkUnits = m.requests * 4, listen = m.messages, total = checkUnits + listen;
  const lp = total ? listen / total : 0, cp = total ? checkUnits / total : 0;
  $('split-listen').style.width = `${lp * 100}%`; $('split-verify').style.width = `${cp * 100}%`;
  $('split-text').textContent = total ? `Listening ${pct(lp)} · Checking ${pct(cp)}` : 'No effort spent yet';
  $('step').disabled = live.round >= live.config.rounds;
  drawNetwork(); drawChart();
  if (selected !== null) inspectAgent(selected, false);
}
function updateTruthLabels() {
  const pill = $('truth-pill');
  pill.textContent = `Ground truth: ${config.truth ? 'true (Patch A)' : 'false (Patch B)'}`;
  pill.classList.toggle('true', config.truth);
  $('wrong-label').textContent = config.truth ? 'Wrongly reject it now' : 'Believe the false claim now';
  $('legend-wrong').textContent = config.truth ? 'Wrongly rejects the claim' : 'Believes the false claim';
  $('chart-title').textContent = config.truth ? 'Share wrongly rejecting the true claim, by policy' : 'Share believing the false claim, by policy';
}

/* ---------- agent inspector ---------- */
function inspectAgent(id, focus = true) {
  selected = id; const a = live.agents[id];
  $('agent-card').hidden = false; $('agent-id').value = id + 1;
  $('agent-title').textContent = `Agent ${fmt(id + 1)}`;
  const evidence = a.checked ? 'Has checked directly.' : a.roots.has('probe:0') ? 'Heard the probe result secondhand.' : 'Has no probe evidence.';
  $('agent-summary').textContent = `Support for the claim: ${pct(a.p, 0)}. ${evidence} ${a.pending !== null ? `Check result due in round ${a.pending}. ` : ''}${fmt(a.received)} messages read. Last: ${a.lastAction.toLowerCase()}.`;
  const box = $('agent-evidence'); box.replaceChildren();
  if (!a.roots.size) { const p = document.createElement('p'); p.textContent = 'No original evidence has reached this agent yet.'; box.append(p); }
  for (const [rid, root] of a.roots) {
    const d = document.createElement('div'); d.className = 'ev';
    const code = document.createElement('code'); code.className = rid.startsWith('probe') ? 'probe' : 'report'; code.textContent = rid;
    const span = document.createElement('span');
    span.textContent = `${root.origin} · says the claim is ${root.value ? 'true' : 'false'} · ${root.hops === 0 ? 'observed directly' : `${root.hops} hop${root.hops === 1 ? '' : 's'} away`}${root.verified ? ' · definitive in this model' : ' · unverified'}`;
    d.append(code, span); box.append(d);
  }
  if (focus) { drawNetwork(); $('agent-title').focus({preventScroll: true}); }
}
$('network').addEventListener('click', ev => {
  const box = $('network').getBoundingClientRect(), mx = ev.clientX - box.left, my = ev.clientY - box.top;
  let best = -1, dist = Infinity;
  positions.forEach((p, i) => { const q = project(p, box.width, box.height), d = (q.x - mx) ** 2 + (q.y - my) ** 2; if (d < dist) { dist = d; best = i; } });
  if (best >= 0 && dist < 400) inspectAgent(best);
});
$('close-agent').addEventListener('click', () => { selected = null; $('agent-card').hidden = true; drawNetwork(); });
$('agent-navigation').addEventListener('submit', ev => {
  ev.preventDefault(); const id = Number($('agent-id').value) - 1;
  if (Number.isInteger(id) && id >= 0 && id < config.population) { inspectAgent(id); $('network-wrap').scrollIntoView({behavior: reduceMotion ? 'auto' : 'smooth', block: 'center'}); }
});

/* ---------- assumptions, sharing, export ---------- */
for (const key of FIELDS) $(key).addEventListener('change', () => {
  try { scenario = 'custom'; renderScenarios(); applyConfig({...readControls(), protocol}); status('Settings changed. All three policies recomputed from round 0.'); }
  catch (error) { toast(error.message); writeControls(); }
});
for (const key of [...FRACTIONS, 'delay', 'reinforcement']) $(key).addEventListener('input', () => {
  const v = $(key).value;
  $(`${key}-value`).textContent = key === 'delay' ? `${v} round${v === '1' ? '' : 's'}` : key === 'reinforcement' ? Number(v).toFixed(1) : `${v}%`;
});
$('reset-config').addEventListener('click', () => activateScenario('echoes'));
function configURL() {
  const url = new URL(location.href);
  url.hash = `experiment=${new URLSearchParams(Object.entries({...config, protocol})).toString()}`;
  return url;
}
function syncURL() { if (location.hash.startsWith('#experiment=')) history.replaceState(null, '', configURL()); }
$('share').addEventListener('click', async () => {
  const url = configURL(); history.replaceState(null, '', url);
  try { await navigator.clipboard.writeText(url.href); toast('Link copied. It reopens these settings at round 0.'); }
  catch { toast('Settings saved in the address bar. Copy the URL to share.'); }
});
$('export').addEventListener('click', () => {
  const blob = new Blob([JSON.stringify(live.exportRun(), null, 2) + '\n'], {type: 'application/json'});
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
  a.download = `witness-${protocol}-seed-${config.seed}-round-${live.round}.json`; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  toast('Downloaded the configuration, interventions and trajectory. Replay it with sweep.mjs --replay.');
});

/* ---------- real-model pilot ---------- */
let pilot = null, episodeKey = 'false', cellIndex = 0;
const ACTION_TEXT = {check: 'Requested a check', relay: 'Relayed an assessment', abstain: 'Abstained', invalid: 'Output rejected, counted as abstention'};
function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; }
async function loadPilot() {
  try {
    const [data, audit] = await Promise.all([
      fetch('assets/pilot-decisions.json').then(r => { if (!r.ok) throw new Error(); return r.json(); }),
      fetch('assets/pilot-audit.json').then(r => r.ok ? r.json() : null).catch(() => null),
    ]);
    pilot = data;
    const ep = data.episodes[0], meta = $('pilot-meta'); meta.replaceChildren();
    const rows = [
      ['Model', ep.model.replace(/^openrouter\//, '')],
      ['Reasoning', 'off · 256 output tokens max'],
      ['Agents × rounds', `${ep.config.population} × ${ep.config.rounds}`],
      ['Budget', `${ep.config.budget} units per agent · check costs 4`],
      ['Check delay', `${ep.config.delay} rounds`],
    ];
    if (audit) rows.push(['Spent, all attempts', `US$${Number(audit.provider_key_usage_usd).toFixed(4)}`]);
    for (const [k, v] of rows) { const d = el('div', 'kv'); d.append(el('span', '', k), el('span', '', v)); meta.append(d); }
    showEpisode('false');
  } catch {
    $('pilot-stats').replaceChildren(el('p', 'fine', 'The recorded pilot data could not be loaded. It is included in the source archive.'));
  }
}
function showEpisode(key) {
  episodeKey = key;
  document.querySelectorAll('.episode-switch button').forEach(b => { const on = b.dataset.episode === key; b.setAttribute('aria-checked', String(on)); b.tabIndex = on ? 0 : -1; });
  const ep = pilot.episodes.find(e => e.key === key), n = ep.config.population;
  const checkers = new Set(ep.decisions.filter(d => d.executed === 'check').map(d => d.agent)).size;
  const firstRound = ep.decisions.filter(d => d.round === 1 && d.executed === 'check').length;
  const everWrong = Math.round(Math.max(...ep.rounds.map(r => r.wrong)) * n);
  const invalid = ep.decisions.filter(d => d.error).length;
  const stats = $('pilot-stats'); stats.replaceChildren();
  for (const [v, t] of [
    [`${checkers}/${n}`, 'agents requested the probe at least once'],
    [`${firstRound}/${n}`, 'checked in round 1, before any peer had spoken'],
    [`${everWrong}/${n}`, `most agents ${ep.truth ? 'wrongly rejecting the claim' : 'believing the false claim'} at any round's end`],
    [`${invalid}/${ep.decisions.length}`, 'malformed outputs, kept and counted as abstentions'],
  ]) { const s = el('div', 'stat'); s.append(el('strong', '', v), el('span', '', t)); stats.append(s); }
  renderGrid(ep);
}
function renderGrid(ep) {
  const grid = $('pilot-grid'); grid.replaceChildren();
  const n = ep.config.population, rounds = ep.config.rounds;
  grid.append(el('span', 'col-h', ''));
  for (let r = 1; r <= rounds; r++) grid.append(el('span', 'col-h', `R${r}`));
  const cells = [];
  for (let a = 0; a < n; a++) {
    const seeded = ep.decisions.some(d => d.agent === a && d.round === 1 && d.has_report);
    const head = el('span', 'row-h');
    head.append(el('span', 'long', 'Agent '), document.createTextNode(String(a + 1)));
    if (seeded) { const s = el('span', 'seed', '●'); s.title = 'Started with the original report'; head.append(s); }
    grid.append(head);
    for (let r = 1; r <= rounds; r++) {
      const d = ep.decisions.find(x => x.agent === a && x.round === r);
      const kind = d.error ? 'invalid' : d.executed;
      const b = el('button', `cell ${kind}`); b.type = 'button'; b.tabIndex = -1;
      b.dataset.index = String(cells.length);
      b.setAttribute('aria-label', `Agent ${a + 1}, round ${r}: ${ACTION_TEXT[kind]}${d.p !== null ? `, support ${d.p}` : ''}${d.has_probe ? ', holds a probe result' : ''}`);
      if (d.p !== null) { const bar = el('i', 'bar'); bar.style.height = `calc((100% - 8px) * ${d.p})`; bar.style.minHeight = '2px'; b.append(bar); }
      if (d.has_probe) { const m = el('span', 'probe-mark', '◆'); m.setAttribute('aria-hidden', 'true'); b.append(m); }
      b.addEventListener('click', () => selectCell(cells, Number(b.dataset.index), ep));
      b.addEventListener('keydown', ev => {
        const i = Number(b.dataset.index), moves = {ArrowRight: 1, ArrowLeft: -1, ArrowDown: rounds, ArrowUp: -rounds};
        if (!(ev.key in moves)) return; ev.preventDefault();
        const j = i + moves[ev.key]; if (j >= 0 && j < cells.length) { selectCell(cells, j, ep); cells[j].focus(); }
      });
      cells.push(b); b._decision = d; grid.append(b);
    }
  }
  const firstCheck = cells.findIndex(c => c._decision.executed === 'check');
  selectCell(cells, firstCheck >= 0 ? firstCheck : 0, ep);
}
function selectCell(cells, index, ep) {
  cellIndex = index;
  cells.forEach((c, i) => { c.setAttribute('aria-selected', String(i === index)); c.tabIndex = i === index ? 0 : -1; });
  const d = cells[index]._decision, card = $('decision-card'); card.replaceChildren();
  const kind = d.error ? 'invalid' : d.executed;
  card.append(el('p', 'tiny', `Agent ${d.agent + 1} · round ${d.round}`));
  card.append(el('h3', '', kind === 'relay' && d.recipient !== null ? `Relayed an assessment to agent ${d.recipient + 1}` : ACTION_TEXT[kind]));
  const saw = [];
  if (d.has_report) saw.push('the original report');
  if (d.has_probe) saw.push('a probe result');
  if (d.peer_messages) saw.push(`${d.peer_messages} peer message${d.peer_messages === 1 ? '' : 's'}`);
  const dl = el('dl');
  const add = (k, v) => { dl.append(el('dt', '', k), el('dd', '', v)); };
  add('Could see', saw.length ? saw.join(', ') : 'nothing yet');
  add('Support for claim', d.p !== null ? `${d.p} (was ${d.previous_p})` : `unchanged at ${d.previous_p}`);
  add('Ground truth', ep.truth ? 'true' : 'false');
  add('Budget before', `${d.budget_before} units${d.pending ? ' · a check was already pending' : ''}`);
  card.append(dl);
  if (d.message) card.append(el('blockquote', '', `“${d.message}”`));
  if (d.sources && d.sources.length) {
    const p = el('p', 'fine', 'Cited: '); for (const s of d.sources) p.append(el('span', 'src', s)); card.append(p);
  }
  if (d.error) {
    card.append(el('p', 'fine', 'The model returned a valid decision followed by extra text. The strict parser rejected the whole output; it was kept, not repaired. Raw output:'));
    card.append(el('pre', '', d.raw_output || ''));
  }
}
document.querySelectorAll('.episode-switch button').forEach((b, i, all) => {
  b.addEventListener('click', () => { if (pilot) showEpisode(b.dataset.episode); });
  b.addEventListener('keydown', ev => {
    if (!['ArrowLeft', 'ArrowRight'].includes(ev.key)) return; ev.preventDefault();
    const next = all[(i + 1) % all.length]; next.focus(); next.click();
  });
});

/* ---------- page chrome ---------- */
const navLinks = [...document.querySelectorAll('.site-header nav a')];
const observer = new IntersectionObserver(entries => {
  for (const e of entries) if (e.isIntersecting) navLinks.forEach(a => a.classList.toggle('active', a.getAttribute('href') === `#${e.target.id}`));
}, {rootMargin: '-45% 0px -50% 0px'});
for (const id of ['case', 'question', 'model', 'pilot', 'program']) observer.observe($(id));
new ResizeObserver(() => { if (live) { drawNetwork(); drawChart(); } }).observe($('network-wrap'));
document.addEventListener('visibilitychange', () => { if (document.hidden && running) { stop(); status(`Paused at round ${live.round} while the tab was hidden.`); } });

function fromHash() {
  if (!location.hash.startsWith('#experiment=')) return null;
  const params = new URLSearchParams(location.hash.slice(12)), parsed = {};
  for (const [key, value] of params) {
    if (params.getAll(key).length !== 1) throw new Error('Repeated setting');
    if (key === 'compare') continue;
    if (!(key in DEFAULTS)) throw new Error('Unknown setting');
    if (typeof DEFAULTS[key] === 'number') { if (!value.trim()) throw new Error('Missing number'); parsed[key] = Number(value); }
    else if (key === 'truth') { if (!['true', 'false'].includes(value)) throw new Error('Invalid truth'); parsed[key] = value === 'true'; }
    else parsed[key] = value;
  }
  const c = validateConfig(parsed);
  if (![64, 256, 1024, 10000].includes(c.population) || c.rounds !== 60
    || FRACTIONS.some(k => Math.abs(c[k] * 100 - Math.round(c[k] * 100)) > 1e-8)
    || !Number.isInteger(c.reinforcement * 2)) throw new Error('Unsupported settings');
  return c;
}

renderScenarios();
let initial = null;
try { initial = fromHash(); } catch { toast('That link has unsupported settings, so the default scenario loaded.'); }
if (initial) {
  scenario = 'custom'; protocol = initial.protocol; renderScenarios();
  config = initial; writeControls(); updateTruthLabels(); resetLive(); precompute(); syncPolicySwitch();
} else activateScenario('echoes');
loadPilot().then(() => {
  const target = /^#[a-z]+$/.test(location.hash) && document.querySelector(location.hash);
  if (target) target.scrollIntoView({block: 'start'});
});
