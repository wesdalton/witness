import {Swarm, DEFAULTS, random, validateConfig} from './engine.js';

const $ = id => document.getElementById(id);
const C = {wrong: '#c2410c', correct: '#0f766e', neutral: '#b9bcb2', check: '#4453c4', ink: '#1d2420'};
const PROTOCOLS = ['endorsement', 'provenance', 'reserved'];
const POLICY = {
  endorsement: {label: 'Peer endorsements', color: '#c2410c'},
  provenance: {label: 'Original sources', color: '#2f6db3'},
  reserved: {label: 'Sources + reserve', color: '#7a4fc9'},
};
const PRESETS = {
  sources: {protocol: 'provenance', config: {}},
  fast: {protocol: 'reserved', config: {delay: 0}},
  true: {protocol: 'reserved', config: {truth: true}},
};
const FIELDS = ['population', 'topology', 'communication', 'delay', 'seedShare', 'allocation', 'truth', 'seed', 'initialEvidence', 'reinforcement'];
const FRACTIONS = ['communication', 'seedShare', 'initialEvidence'];
const fmt = n => n.toLocaleString('en-US');
const pct = (n, digits = 1) => `${(n * 100).toFixed(digits)}%`;
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;

let config = validateConfig({...DEFAULTS});
let protocol = 'endorsement';
let live, precomputed = {}, summaries = null, job = 0;
let running = false, timer = null, positions = [], visibleEdges = [], totalEdges = 0, selected = null, toastTimer;

function toast(message) {
  $('toast').textContent = message; $('toast').hidden = false;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => { $('toast').hidden = true; }, 3200);
}
const status = message => { $('status').textContent = message; };
const wrongPhrase = () => config.truth ? 'wrongly reject the true claim' : 'believe the false claim';

/* configuration */
function writeControls() {
  for (const key of FIELDS) $(key).value = FRACTIONS.includes(key) ? Math.round(config[key] * 100) : String(config[key]);
  for (const key of FRACTIONS) $(`${key}-value`).textContent = `${Math.round(config[key] * 100)}%`;
  $('delay-value').textContent = config.delay === 0 ? 'immediate' : `${config.delay} round${config.delay === 1 ? '' : 's'}`;
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
function updateTruthLabels() {
  $('truth-pill').textContent = config.truth ? 'The claim is true' : 'The claim is false';
  $('truth-pill').classList.toggle('true', config.truth);
  $('wrong-label').textContent = config.truth ? 'Wrongly reject it now' : 'Believe it now';
  $('legend-wrong').textContent = config.truth ? 'wrongly rejects the claim' : 'believes the false claim';
  $('chart-title').textContent = config.truth ? 'Share of agents wrongly rejecting the true claim' : 'Share of agents believing the false claim';
}

/* lifecycle */
function stop() {
  running = false; clearTimeout(timer);
  $('play-icon').textContent = '▶';
  $('play-label').textContent = live && live.round >= live.config.rounds ? 'Replay' : 'Run';
}
function resetLive() {
  stop();
  live = new Swarm({...config, protocol});
  selected = null; $('agent-card').hidden = true;
  $('agent-id').max = config.population; $('agent-id').value = 1;
  $('round-total').textContent = config.rounds;
  layout(); render();
}
function load(next, nextProtocol = protocol) {
  protocol = nextProtocol;
  config = validateConfig({...next, protocol});
  writeControls(); updateTruthLabels(); resetLive(); precompute(); syncPolicySwitch(); syncURL();
}
function precompute() {
  const token = ++job;
  precomputed = Object.fromEntries(PROTOCOLS.map(p => [p, new Swarm({...config, protocol: p})]));
  summaries = null; renderTable();
  const list = Object.values(precomputed);
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
    renderTable(); drawChart();
  };
  work();
}
function summarize(history) {
  const last = history.at(-1);
  return {
    peak: Math.max(...history.map(h => h.wrong)),
    mean: history.reduce((s, h) => s + h.wrong, 0) / history.length,
    checkShare: last.effort ? last.requests * 4 / last.effort : 0,
    final: last.wrong,
  };
}

/* policy switch */
function syncPolicySwitch() {
  document.querySelectorAll('.policy-switch button').forEach(b => {
    const on = b.dataset.protocol === protocol;
    b.setAttribute('aria-checked', String(on)); b.tabIndex = on ? 0 : -1;
  });
  renderTable();
}
document.querySelectorAll('.policy-switch button').forEach((b, i, all) => {
  b.addEventListener('click', () => {
    protocol = b.dataset.protocol; config = validateConfig({...config, protocol});
    resetLive(); syncPolicySwitch(); syncURL(); drawChart();
  });
  b.addEventListener('keydown', ev => {
    if (!['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(ev.key)) return;
    ev.preventDefault();
    const next = all[(i + (ev.key === 'ArrowLeft' || ev.key === 'ArrowUp' ? all.length - 1 : 1)) % all.length];
    next.focus(); next.click();
  });
});

/* in-text presets */
document.querySelectorAll('.try').forEach(b => b.addEventListener('click', () => {
  const p = PRESETS[b.dataset.preset]; if (!p) return;
  load({...DEFAULTS, ...p.config}, p.protocol);
  $('fig-sim').scrollIntoView({behavior: reduceMotion ? 'auto' : 'smooth', block: 'start'});
  status(`Loaded: ${POLICY[protocol].label.toLowerCase()}${p.config.delay === 0 ? ', checks return immediately' : ''}${p.config.truth ? ', the report is true' : ''}.`);
  if (!reduceMotion) setTimeout(play, 450);
}));

/* playback */
function advance() {
  live.step(); render();
  if (live.round >= live.config.rounds) {
    stop(); const m = live.history.at(-1);
    status(`Round ${live.round}: ${pct(m.wrong)} ${wrongPhrase()}, ${pct(m.correct)} correct, ${pct(m.uncertain)} undecided.`);
  }
}
function tick() { if (!running) return; advance(); if (running) timer = setTimeout(tick, config.population >= 10000 ? 140 : 90); }
function play() {
  if (live.round >= live.config.rounds) resetLive();
  running = true; $('play-icon').textContent = '❚❚'; $('play-label').textContent = 'Pause'; tick();
}
$('play').addEventListener('click', () => { if (running) { stop(); status(`Paused at round ${live.round}.`); } else play(); });
$('step').addEventListener('click', () => { stop(); if (live.round < live.config.rounds) advance(); });
$('restart').addEventListener('click', () => { resetLive(); status(''); });
$('correct').addEventListener('click', () => {
  const count = live.injectCorrection(); render();
  status(`Gave the probe result to ${fmt(count)} agents at round ${live.round}, outside the budget. Only the run you're watching changes.`);
});

/* drawing */
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
  const top = 40, bottom = 14, side = 16, ah = h - top - bottom, aw = Math.min(w - 2 * side, ah * 1.5);
  return {x: (w - aw) / 2 + p.x * aw, y: top + p.y * ah};
}
function stateColor(a) {
  if (a.p > .35 && a.p < .65) return C.neutral;
  return (a.p >= .65) === config.truth ? C.correct : C.wrong;
}
const nodeRadius = () => { const n = config.population; return n <= 64 ? 6.5 : n <= 256 ? 4.2 : n <= 1024 ? 2.4 : 1.2; };
function drawNetwork() {
  const {ctx, w, h} = canvasContext('network');
  ctx.lineWidth = .7; ctx.strokeStyle = 'rgba(60,70,62,.09)'; ctx.beginPath();
  for (const [i, j] of visibleEdges) { const a = project(positions[i], w, h), b = project(positions[j], w, h); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); }
  ctx.stroke();
  const r = nodeRadius();
  for (const color of [C.neutral, C.correct, C.wrong]) {
    ctx.fillStyle = color; ctx.beginPath();
    for (const a of live.agents) if (stateColor(a) === color) { const p = project(positions[a.id], w, h); ctx.moveTo(p.x + r, p.y); ctx.arc(p.x, p.y, r, 0, Math.PI * 2); }
    ctx.fill();
  }
  if (config.population <= 1024) {
    ctx.lineWidth = r > 4 ? 1.6 : 1.1; ctx.strokeStyle = C.ink; ctx.beginPath();
    for (const a of live.agents) if (a.checked) { const p = project(positions[a.id], w, h); ctx.moveTo(p.x + r + 2, p.y); ctx.arc(p.x, p.y, r + 2, 0, Math.PI * 2); }
    ctx.stroke();
    ctx.setLineDash([2.5, 2]); ctx.strokeStyle = C.check; ctx.beginPath();
    for (const a of live.agents) if (a.pending !== null) { const p = project(positions[a.id], w, h); ctx.moveTo(p.x + r + 2.4, p.y); ctx.arc(p.x, p.y, r + 2.4, 0, Math.PI * 2); }
    ctx.stroke(); ctx.setLineDash([]);
  }
  if (selected !== null) {
    const p = project(positions[selected], w, h);
    ctx.strokeStyle = C.ink; ctx.lineWidth = 2.2; ctx.beginPath(); ctx.arc(p.x, p.y, r + 6, 0, Math.PI * 2); ctx.stroke();
  }
  const m = live.history.at(-1);
  $('network').setAttribute('aria-label', `${fmt(config.population)} agents at round ${live.round}: ${pct(m.wrong)} ${wrongPhrase()}, ${pct(m.correct)} correct, ${pct(m.uncertain)} undecided.`);
}
function drawChart() {
  const {ctx, w, h} = canvasContext('chart'), left = 40, right = 8, top = 8, bottom = 22, rounds = config.rounds;
  const x = r => left + r / rounds * (w - left - right), y = v => top + (1 - v) * (h - top - bottom);
  ctx.font = '11px ui-monospace, Menlo, monospace'; ctx.fillStyle = '#7a827c'; ctx.lineWidth = 1; ctx.textAlign = 'right';
  for (const v of [0, .25, .5, .75, 1]) { ctx.strokeStyle = v ? '#eeebe4' : '#cfc9bc'; ctx.beginPath(); ctx.moveTo(left, y(v)); ctx.lineTo(w - right, y(v)); ctx.stroke(); ctx.fillText(`${v * 100}%`, left - 6, y(v) + 4); }
  ctx.textAlign = 'center';
  for (let r = 0; r <= rounds; r += rounds >= 40 ? 10 : 5) ctx.fillText(String(r), x(r), h - 5);
  const line = (history, color, width, alpha = 1, dash = []) => {
    if (!history || !history.length) return;
    ctx.globalAlpha = alpha; ctx.strokeStyle = color; ctx.lineWidth = width; ctx.setLineDash(dash); ctx.beginPath();
    history.forEach((p, i) => i ? ctx.lineTo(x(p.round), y(p.wrong)) : ctx.moveTo(x(p.round), y(p.wrong)));
    ctx.stroke(); ctx.setLineDash([]); ctx.globalAlpha = 1;
  };
  for (const p of PROTOCOLS) if (p !== protocol && precomputed[p]) line(precomputed[p].history, POLICY[p].color, 1.6, .55);
  const watching = live && live.config.protocol === protocol ? live : null;
  const edited = watching && watching.interventions.length;
  if (precomputed[protocol]) line(precomputed[protocol].history, POLICY[protocol].color, 1.6, edited ? .45 : .25, edited ? [4, 3] : []);
  if (watching) {
    line(watching.history, POLICY[protocol].color, 3);
    ctx.strokeStyle = '#9a9488'; ctx.lineWidth = 1; ctx.setLineDash([3, 3]);
    ctx.beginPath(); ctx.moveTo(x(watching.round), top); ctx.lineTo(x(watching.round), h - bottom); ctx.stroke(); ctx.setLineDash([]);
    ctx.fillStyle = C.check;
    for (const ev of watching.interventions) { ctx.beginPath(); ctx.arc(x(ev.round), h - bottom, 3.5, 0, Math.PI * 2); ctx.fill(); }
  }
  const key = $('chart-key'); key.replaceChildren();
  for (const p of PROTOCOLS) {
    const s = document.createElement('span'), i = document.createElement('i');
    i.style.background = POLICY[p].color; if (p === protocol) i.style.height = '4px';
    s.append(i, document.createTextNode(POLICY[p].label + (p === protocol ? ' (playing)' : ''))); key.append(s);
  }
}
function renderTable() {
  const body = $('compare-body'); body.replaceChildren();
  for (const p of PROTOCOLS) {
    const tr = document.createElement('tr'); if (p === protocol) tr.className = 'selected';
    const th = document.createElement('th'); th.scope = 'row';
    const sw = document.createElement('i'); sw.style.background = POLICY[p].color; th.append(sw, document.createTextNode(POLICY[p].label)); tr.append(th);
    const s = summaries && summaries[p];
    for (const v of s ? [pct(s.peak), pct(s.mean), pct(s.checkShare), pct(s.final)] : ['…', '…', '…', '…']) {
      const td = document.createElement('td'); td.textContent = v; tr.append(td);
    }
    body.append(tr);
  }
}
function render() {
  const m = live.history.at(-1);
  let peak = 0, peakRound = 0; live.history.forEach(h => { if (h.wrong > peak) { peak = h.wrong; peakRound = h.round; } });
  $('round').textContent = live.round;
  $('wrong-now').textContent = pct(m.wrong);
  $('wrong-peak').textContent = pct(peak);
  $('wrong-peak-round').textContent = peak ? `round ${peakRound}` : '';
  const checkUnits = m.requests * 4, total = checkUnits + m.messages, cp = total ? checkUnits / total : 0;
  $('split-text').textContent = pct(cp);
  $('step').disabled = live.round >= live.config.rounds;
  drawNetwork(); drawChart();
  if (selected !== null) inspectAgent(selected, false);
}

/* agent inspector */
function inspectAgent(id, focus = true) {
  selected = id; const a = live.agents[id];
  $('agent-card').hidden = false; $('agent-id').value = id + 1;
  $('agent-title').textContent = `Agent ${fmt(id + 1)}`;
  const evidence = a.checked ? 'It has checked for itself.' : a.roots.has('probe:0') ? 'It heard the probe result secondhand.' : 'It has no probe evidence.';
  $('agent-summary').textContent = `Confidence the patch works: ${pct(a.p, 0)}. ${evidence}${a.pending !== null ? ` Its check returns in round ${a.pending}.` : ''} It has read ${fmt(a.received)} messages.`;
  const box = $('agent-evidence'); box.replaceChildren();
  if (!a.roots.size) { const p = document.createElement('p'); p.textContent = 'No original evidence has reached it yet.'; box.append(p); }
  for (const [rid, root] of a.roots) {
    const d = document.createElement('div'); d.className = 'ev';
    const code = document.createElement('code'); code.textContent = rid === 'probe:0' ? 'the probe' : 'the test report';
    const span = document.createElement('span');
    span.textContent = `says the patch ${root.value ? 'works' : 'does not work'} · ${root.hops === 0 ? 'seen directly' : `${root.hops} hop${root.hops === 1 ? '' : 's'} away`}`;
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

/* assumptions, sharing, export */
for (const key of FIELDS) $(key).addEventListener('change', () => {
  try { load(readControls()); status('Settings changed. All three policies recomputed from round 0.'); }
  catch (error) { toast(error.message); writeControls(); }
});
for (const key of [...FRACTIONS, 'delay', 'reinforcement']) $(key).addEventListener('input', () => {
  const v = $(key).value;
  $(`${key}-value`).textContent = key === 'delay' ? (v === '0' ? 'immediate' : `${v} round${v === '1' ? '' : 's'}`) : key === 'reinforcement' ? Number(v).toFixed(1) : `${v}%`;
});
$('reset-config').addEventListener('click', () => { load({...DEFAULTS}, 'endorsement'); status('Default settings restored.'); });
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
  toast('Downloaded this run. Replay it with: node website/scripts/sweep.mjs --replay FILE');
});

/* real-model pilot */
let pilot = null;
const ACTION_TEXT = {check: 'Asked for the check', relay: 'Sent its assessment', abstain: 'Abstained', invalid: 'Malformed output (counted as abstaining)'};
function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; }
async function loadPilot() {
  try {
    const r = await fetch('assets/pilot-decisions.json');
    if (!r.ok) throw new Error();
    pilot = await r.json(); showEpisode('false');
  } catch {
    $('pilot-grid').replaceChildren(el('p', 'note', 'The pilot records could not be loaded here. They are in the source archive.'));
  }
}
function showEpisode(key) {
  document.querySelectorAll('.episode-switch button').forEach(b => { const on = b.dataset.episode === key; b.setAttribute('aria-checked', String(on)); b.tabIndex = on ? 0 : -1; });
  renderGrid(pilot.episodes.find(e => e.key === key));
}
function renderGrid(ep) {
  const grid = $('pilot-grid'); grid.replaceChildren();
  const n = ep.config.population, rounds = ep.config.rounds, cells = [];
  grid.append(el('span', 'col-h', ''));
  for (let r = 1; r <= rounds; r++) grid.append(el('span', 'col-h', String(r)));
  for (let a = 0; a < n; a++) {
    const head = el('span', 'row-h');
    head.append(el('span', 'long', 'Agent '), document.createTextNode(String(a + 1)));
    if (ep.decisions.some(d => d.agent === a && d.round === 1 && d.has_report)) { const s = el('span', 'seed', '●'); s.title = 'Started with the report'; head.append(s); }
    grid.append(head);
    for (let r = 1; r <= rounds; r++) {
      const d = ep.decisions.find(x => x.agent === a && x.round === r), kind = d.error ? 'invalid' : d.executed;
      const b = el('button', `cell ${kind}`); b.type = 'button'; b.tabIndex = -1; b.dataset.index = String(cells.length);
      b.setAttribute('aria-label', `Agent ${a + 1}, round ${r}: ${ACTION_TEXT[kind]}${d.p !== null ? `, confidence ${d.p}` : ''}${d.has_probe ? ', holds a probe result' : ''}`);
      if (d.p !== null) { const bar = el('i', 'bar'); bar.style.height = `${Math.max(2, d.p * 32)}px`; b.append(bar); }
      if (d.has_probe) { const m = el('span', 'probe-mark', '◆'); m.setAttribute('aria-hidden', 'true'); b.append(m); }
      b.addEventListener('click', () => select(cells, Number(b.dataset.index), ep));
      b.addEventListener('keydown', ev => {
        const moves = {ArrowRight: 1, ArrowLeft: -1, ArrowDown: rounds, ArrowUp: -rounds};
        if (!(ev.key in moves)) return; ev.preventDefault();
        const j = Number(b.dataset.index) + moves[ev.key]; if (j >= 0 && j < cells.length) { select(cells, j, ep); cells[j].focus(); }
      });
      b._d = d; cells.push(b); grid.append(b);
    }
  }
  const first = cells.findIndex(c => c._d.error) >= 0 ? cells.findIndex(c => c._d.error) : 0;
  select(cells, ep.key === 'true' ? first : 0, ep);
}
function select(cells, index, ep) {
  cells.forEach((c, i) => { c.setAttribute('aria-selected', String(i === index)); c.tabIndex = i === index ? 0 : -1; });
  const d = cells[index]._d, card = $('decision-card'), kind = d.error ? 'invalid' : d.executed;
  card.replaceChildren();
  card.append(el('p', 'who', `Agent ${d.agent + 1}, round ${d.round} · the report is ${ep.truth ? 'true' : 'false'}`));
  card.append(el('h3', '', kind === 'relay' && d.recipient !== null ? `Sent its assessment to agent ${d.recipient + 1}` : ACTION_TEXT[kind]));
  const saw = [];
  if (d.has_report) saw.push('the test report');
  if (d.has_probe) saw.push('a probe result');
  if (d.peer_messages) saw.push(`${d.peer_messages} peer message${d.peer_messages === 1 ? '' : 's'}`);
  const dl = el('dl'), add = (k, v) => dl.append(el('dt', '', k), el('dd', '', v));
  add('Could see', saw.length ? saw.join(', ') : 'nothing yet');
  add('Confidence', d.p !== null ? `${d.p} (was ${d.previous_p})` : `stayed at ${d.previous_p}`);
  add('Budget left', `${d.budget_before} units${d.pending ? ', check already pending' : ''}`);
  card.append(dl);
  if (d.message) card.append(el('blockquote', '', d.message));
  if (d.error) {
    card.append(el('p', 'note', 'A valid decision followed by extra text. The strict parser rejected the whole output; it is kept as recorded:'));
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

/* startup */
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
let initial = null;
try { initial = fromHash(); } catch { toast('That link has unsupported settings, so the defaults loaded.'); }
load(initial || {...DEFAULTS}, initial ? initial.protocol : 'endorsement');
loadPilot().then(() => {
  const target = /^#[a-z]+$/.test(location.hash) && document.querySelector(location.hash);
  if (target) target.scrollIntoView({block: 'start'});
});
