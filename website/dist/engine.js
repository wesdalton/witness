/**
 * Witness mechanistic baseline, v0.1.
 * These authored update rules are NOT fitted to LLMs. The same engine is used
 * by the browser and the reproducible CLI. See methods.md for the equations.
 */
export const VERSION = '0.1.0';
export const DEFAULTS = Object.freeze({
  population: 256, topology: 'small-world', protocol: 'endorsement',
  communication: 0.98, delay: 6, seedShare: 0.08, initialEvidence: 0.01, reinforcement: 6,
  rounds: 60, seed: 42, truth: false, allocation: 'adaptive',
});
export const PROTOCOLS = ['endorsement', 'provenance', 'reserved'];
export const TOPOLOGIES = ['small-world', 'modular', 'hub'];
export function random(seed, a = 0, b = 0, c = 0) {
  let x = (seed ^ Math.imul(a + 1, 0x9e3779b1) ^ Math.imul(b + 1, 0x85ebca6b)
    ^ Math.imul(c + 1, 0xc2b2ae35)) >>> 0;
  x ^= x >>> 16; x = Math.imul(x, 0x7feb352d); x ^= x >>> 15;
  x = Math.imul(x, 0x846ca68b); x ^= x >>> 16;
  return (x >>> 0) / 4294967296;
}
export function validateConfig(input = {}) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) throw new Error('Configuration must be an object');
  for (const key of Object.keys(input)) {
    if (!Object.hasOwn(DEFAULTS, key)) throw new Error(`Unknown configuration key: ${key}`);
  }
  const c = {...DEFAULTS, ...input};
  const ranges = {population: [8, 10000], communication: [0, 1], delay: [0, 20],
    seedShare: [0, 1], initialEvidence: [0, 1], reinforcement: [0, 10], rounds: [1, 200], seed: [0, 2147483647]};
  for (const [key, [lo, hi]] of Object.entries(ranges)) {
    if (!Number.isFinite(c[key]) || c[key] < lo || c[key] > hi) throw new Error(`Invalid ${key}`);
  }
  for (const key of ['population', 'delay', 'rounds', 'seed']) {
    if (!Number.isInteger(c[key])) throw new Error(`${key} must be an integer`);
  }
  if (!PROTOCOLS.includes(c.protocol) || !TOPOLOGIES.includes(c.topology)) throw new Error('Invalid protocol or topology');
  if (!['adaptive', 'fixed'].includes(c.allocation) || typeof c.truth !== 'boolean') throw new Error('Invalid allocation or truth');
  return c;
}
export function makeNetwork(config) {
  const {population: n, topology, seed} = config;
  const graph = Array.from({length: n}, () => new Set());
  const link = (a, b) => {if (a !== b) {graph[a].add(b); graph[b].add(a);}};
  const groups = 4;
  for (let i = 0; i < n; i++) {
    link(i, (i + 1) % n);
    if (topology === 'small-world') {
      link(i, (i + 2) % n);
      if (random(seed, i, 1) < 0.3) link(i, Math.floor(random(seed, i, 2) * n));
    } else if (topology === 'modular') {
      const g = Math.min(groups - 1, Math.floor(i * groups / n));
      const start = Math.ceil(g * n / groups), end = Math.ceil((g + 1) * n / groups);
      link(i, start + (i - start + 2) % (end - start));
      link(i, start + Math.floor(random(seed, i, 3) * (end - start)));
      if (random(seed, i, 4) < 0.035) link(i, Math.floor(random(seed, i, 5) * n));
    } else {
      const hubCount = Math.max(2, Math.ceil(Math.sqrt(n) / 2));
      link(i, Math.floor(random(seed, i, 6) * hubCount));
      if (i < hubCount) link(i, (i + 1) % hubCount);
    }
  }
  return graph.map(set => Array.from(set).sort((a, b) => a - b));
}
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const sigmoid = x => 1 / (1 + Math.exp(-x));
const logit = p => Math.log(p / (1 - p));

export class Swarm {
  constructor(input) {
    this.config = validateConfig(input);
    const {population: n, seed, seedShare, initialEvidence, truth} = this.config;
    this.graph = makeNetwork(this.config);
    this.round = 0; this.messages = 0; this.requests = 0; this.checks = 0; this.canceledRequests = 0;
    this.effort = 0; this.events = []; this.interventions = [];
    this.agents = Array.from({length: n}, (_, id) => {
      const seeded = random(seed, id, 10) < seedShare;
      const checked = random(seed, id, 11) < initialEvidence;
      const roots = new Map();
      if (seeded) roots.set('report:0', {value: true, verified: false, origin: 'reported success', hops: 0});
      if (checked) roots.set('probe:0', {value: truth, verified: true, origin: 'recorded behavioral probe', hops: 0});
      const p = checked ? (truth ? 0.99 : 0.01) : seeded ? 0.82 : 0.5;
      return {id, p, checked, pending: null, roots, received: 0, lastFrom: null,
        lastAction: checked ? 'Initial probe evidence' : seeded ? 'Received the success claim' : 'No evidence yet'};
    });
    this.initialChecks = this.agents.filter(a => a.checked).length;
    this.history = [this.measure()];
  }
  sourceBelief(agent) {
    const verified = Array.from(agent.roots.values()).find(r => r.verified);
    if (verified) return verified.value ? 0.99 : 0.01;
    let odds = 0;
    for (const r of agent.roots.values()) odds += (r.value ? 1 : -1) * logit(0.68);
    return sigmoid(clamp(odds, -4.6, 4.6));
  }
  addRoot(agent, id, root) {
    if (agent.roots.has(id)) return;
    if (agent.roots.size >= 12) {
      const evict = Array.from(agent.roots).find(([, r]) => !r.verified);
      if (!evict) return;
      agent.roots.delete(evict[0]);
    }
    agent.roots.set(id, {...root, hops: root.hops + 1});
  }
  completeCheck(agent, externallyInjected = false) {
    if (externallyInjected && agent.pending !== null) this.canceledRequests++;
    agent.checked = true; agent.pending = null;
    agent.roots.set('probe:0', {value: this.config.truth, verified: true,
      origin: 'recorded behavioral probe', hops: 0});
    agent.p = this.config.truth ? 0.99 : 0.01;
    agent.lastAction = externallyInjected ? 'Received an external correction' : 'Probe result arrived';
    if (!externallyInjected) this.checks++;
    this.log({type: 'verification', agent: agent.id, text: agent.lastAction});
  }
  log(event) {
    this.events.push({round: this.round, ...event});
    if (this.events.length > 80) this.events.shift();
  }
  injectCorrection() {
    const count = Math.max(1, Math.ceil(this.agents.length * 0.01));
    const ids = this.agents.map(a => a.id).sort((a, b) =>
      random(this.config.seed, a, this.round, 90) - random(this.config.seed, b, this.round, 90)
    ).slice(0, count);
    for (const id of ids) this.completeCheck(this.agents[id], true);
    this.interventions.push({round: this.round, type: 'external_correction', agent_ids: ids});
    this.history[this.history.length - 1] = this.measure();
    return count;
  }
  step() {
    if (this.round >= this.config.rounds) return this.history.at(-1);
    this.round++;
    const c = this.config;
    // All choices read the same start-of-round state. No loop-order advantage.
    const previous = this.agents.map(a => ({p: a.p, roots: Array.from(a.roots)}));
    for (const agent of this.agents) {
      if (agent.pending !== null && agent.pending <= this.round) this.completeCheck(agent);
      const confidence = Math.abs(previous[agent.id].p - 0.5) * 2;
      let verifyProbability = 1 - c.communication;
      if (c.allocation === 'adaptive') verifyProbability *= 1 - 0.85 * confidence;
      if (c.protocol === 'reserved') verifyProbability = Math.max(0.15, 1 - c.communication);
      // A verification costs the whole four-unit turn. A relay costs one unit.
      if (!agent.checked && agent.pending === null && random(c.seed, this.round, agent.id, 20) < verifyProbability) {
        this.requests++; this.effort += 4;
        agent.pending = this.round + c.delay;
        agent.lastAction = 'Requested a probe (4 effort units)';
        this.log({type: 'request', agent: agent.id, text: agent.lastAction});
        if (c.delay === 0) this.completeCheck(agent);
        continue;
      }
      const neighbors = this.graph[agent.id];
      let sum = 0;
      for (let slot = 0; slot < 4; slot++) {
        const sender = neighbors[Math.floor(random(c.seed, this.round, agent.id, 30 + slot) * neighbors.length)];
        const message = previous[sender];
        sum += message.p; agent.lastFrom = sender; agent.received++;
        this.messages++; this.effort++;
        // One evidence item per message, selected independently of its value.
        if (message.roots.length) {
          const [id, root] = message.roots[Math.floor(random(c.seed, this.round, agent.id, 50 + slot) * message.roots.length)];
          this.addRoot(agent, id, root);
        }
      }
      if (!agent.checked) {
        if (c.protocol === 'endorsement') {
          // Soft social reinforcement is an explicit model assumption.
          const social = sigmoid(c.reinforcement * (sum / 4 - 0.5));
          agent.p = clamp(0.55 * previous[agent.id].p + 0.45 * social, 0.01, 0.99);
        } else agent.p = this.sourceBelief(agent);
      }
      agent.lastAction = `Read 4 peer messages; last from agent ${agent.lastFrom + 1}`;
    }
    const m = this.measure(); this.history.push(m);
    return m;
  }
  measure() {
    let correct = 0, wrong = 0, uncertain = 0, roots = 0, verifiedReach = 0, brier = 0;
    const truth = Number(this.config.truth);
    for (const a of this.agents) {
      const support = a.p >= 0.65, refute = a.p <= 0.35;
      if (!support && !refute) uncertain++;
      else if ((support && truth === 1) || (refute && truth === 0)) correct++;
      else wrong++;
      roots += a.roots.size;
      verifiedReach += a.roots.has('probe:0') ? 1 : 0;
      brier += (a.p - truth) ** 2;
    }
    const n = this.agents.length;
    return {round: this.round, correct: correct / n, wrong: wrong / n, uncertain: uncertain / n,
      brier: brier / n, meanSources: roots / n, verifiedReach: verifiedReach / n,
      messages: this.messages, checks: this.checks, requests: this.requests,
      pending: this.agents.filter(a => a.pending !== null).length,
      canceledRequests: this.canceledRequests, effort: this.effort};
  }
  exportRun() {
    return {schema: 'witness.mechanistic.v1', engine_version: VERSION,
      kind: 'mechanistic_simulation', calibrated_to_llms: false,
      assumptions: ['Authored belief and allocation rules; no LLM calls.',
        'A single reused report root and a single definitive probe root.',
        'Verification costs four effort units; reading one message costs one.',
        'Directly checked agents retain the correct result.',
        'Provenance metadata is supplied by the simulation and cannot be forged.'],
      config: {...this.config}, initial_checks: this.initialChecks,
      interventions: structuredClone(this.interventions), history: structuredClone(this.history),
      final_agents: this.agents.map(a => ({id: a.id, belief: a.p, checked: a.checked,
        source_ids: Array.from(a.roots.keys()), received: a.received})),
    };
  }
}
export function runSimulation(config) {
  const sim = new Swarm(config);
  while (sim.round < sim.config.rounds) sim.step();
  return sim.exportRun();
}
export function replayRun(record) {
  if (!record || record.schema !== 'witness.mechanistic.v1' || record.engine_version !== VERSION) throw new Error('Unsupported run version');
  const sim = new Swarm(record.config);
  if (!Array.isArray(record.history) || record.history.length < 1 || record.history.length > sim.config.rounds + 1) throw new Error('Invalid replay history');
  if (!record.history.every((entry, index) => entry && entry.round === index)) throw new Error('Replay rounds must be consecutive from zero');
  if (!Array.isArray(record.interventions)) throw new Error('Invalid replay interventions');
  const lastRound = record.history.at(-1).round;
  let previousRound = -1;
  for (const event of record.interventions) {
    if (!event || event.type !== 'external_correction' || !Number.isInteger(event.round)
      || event.round < previousRound || event.round < 0 || event.round > lastRound
      || !Array.isArray(event.agent_ids) || !event.agent_ids.length
      || new Set(event.agent_ids).size !== event.agent_ids.length
      || event.agent_ids.some(id => !Number.isInteger(id) || id < 0 || id >= sim.config.population)
      || Object.keys(event).some(key => !['round', 'type', 'agent_ids'].includes(key))) {
      throw new Error('Invalid replay intervention');
    }
    previousRound = event.round;
  }
  let interventionIndex = 0;
  for (let round = 0; round <= lastRound; round++) {
    if (round) sim.step();
    while (record.interventions[interventionIndex]?.round === round) {
      const event = record.interventions[interventionIndex++];
      for (const id of event.agent_ids) sim.completeCheck(sim.agents[id], true);
      sim.interventions.push(structuredClone(event));
      sim.history[sim.history.length - 1] = sim.measure();
    }
  }
  return sim.exportRun();
}

/**
 * Replay equality is structural and exact for configuration, counts, and outcomes.
 * Math.exp/log implementations may differ by a few ulps across JS engines, so
 * only modeled beliefs and Brier scores use an absolute tolerance of 1e-12.
 */
export function assertReplayMatches(record, replay = replayRun(record)) {
  const compare = (expected, actual, path) => {
    if (Object.is(expected, actual)) return;
    if (/^history\[\d+\]\.brier$|^final_agents\[\d+\]\.belief$/.test(path)
      && Number.isFinite(expected) && Number.isFinite(actual)
      && Math.abs(expected - actual) <= 1e-12) return;
    if (expected && actual && typeof expected === 'object' && typeof actual === 'object'
      && Array.isArray(expected) === Array.isArray(actual)) {
      const keys = Object.keys(expected), actualKeys = Object.keys(actual);
      if (keys.length !== actualKeys.length || keys.some(key => !Object.hasOwn(actual, key))) {
        throw new Error(`Replay structure mismatch at ${path || 'record'}`);
      }
      for (const key of keys) compare(expected[key], actual[key],
        Array.isArray(expected) ? `${path}[${key}]` : path ? `${path}.${key}` : key);
      return;
    }
    throw new Error(`Replay mismatch at ${path || 'record'}`);
  };
  compare(record, replay, '');
  return replay;
}
