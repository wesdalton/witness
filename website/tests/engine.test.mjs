import test from 'node:test';
import assert from 'node:assert/strict';
import {Swarm,runSimulation,replayRun,assertReplayMatches,makeNetwork,validateConfig} from '../dist/engine.js';
test('deterministic trajectories',()=>assert.deepEqual(runSimulation({population:64}),runSimulation({population:64})));
test('effort conservation and check accounting including interventions',()=>{
 for(const protocol of ['endorsement','provenance','reserved']){
  const s=new Swarm({population:64,protocol,communication:.5,delay:4});
  for(let r=0;r<60;r++){s.step();if(r===2)s.injectCorrection();const m=s.history.at(-1);
   assert.equal(m.effort,64*s.round*4);assert.equal(m.effort,m.messages+m.requests*4);
   assert.equal(m.requests,m.checks+m.pending+m.canceledRequests);assert.ok(Math.abs(m.wrong+m.correct+m.uncertain-1)<1e-12);}
 }
});
test('copies never multiply source evidence',()=>{
 const s=new Swarm({population:64,protocol:'provenance',communication:1,seedShare:1,initialEvidence:0});
 for(let r=0;r<10;r++)s.step();for(const a of s.agents){assert.equal(a.roots.size,1);assert.ok(Math.abs(a.p-.68)<1e-12);}
});
test('no information preserves uncertainty',()=>{
 for(const protocol of ['endorsement','provenance'])assert.equal(runSimulation({population:64,protocol,communication:1,seedShare:0,initialEvidence:0}).history.at(-1).uncertain,1);
});
test('grounded checks are absorbing for either truth value',()=>{
 for(const truth of [true,false])assert.ok(runSimulation({population:64,initialEvidence:1,truth}).history.every(h=>h.correct===1&&h.wrong===0));
});
test('verification arrives at request round plus delay',()=>{
 const s=new Swarm({population:64,communication:0,allocation:'fixed',delay:3,initialEvidence:0});
 s.step();assert.equal(s.checks,0);assert.equal(s.requests,64);s.step();s.step();assert.equal(s.checks,0);s.step();assert.equal(s.checks,64);
 const t=new Swarm({population:64,communication:0,allocation:'fixed',delay:0,initialEvidence:0});t.step();assert.equal(t.checks,64);
});
test('policy arms share initial state and network',()=>{
 const a=new Swarm({population:64}),b=new Swarm({population:64,protocol:'provenance'});assert.deepEqual(a.graph,b.graph);assert.deepEqual(a.agents,b.agents);
});
test('exact replay of partial run with repeated interventions',()=>{
 const s=new Swarm({population:64,communication:.5});s.injectCorrection();for(let i=0;i<17;i++){s.step();if(i===2){s.injectCorrection();s.injectCorrection();}}assert.deepEqual(replayRun(s.exportRun()),s.exportRun());
});
test('networks are simple connected and undirected',()=>{
 for(const population of [8,17,64,10000])for(const topology of ['small-world','modular','hub']){
 const g=makeNetwork(validateConfig({population,topology})),seen=new Set([0]),q=[0];
 while(q.length){const i=q.pop();for(const j of g[i]){assert.notEqual(i,j);assert.ok(g[j].includes(i));if(!seen.has(j)){seen.add(j);q.push(j);}}}assert.equal(seen.size,population);}
});
test('invalid configurations rejected',()=>{
 for(const c of [null,[],{extra:1},{population:10001},{population:12.1},{delay:-1},{seed:NaN},{truth:'false'},{protocol:'magic'},{reinforcement:Infinity}])assert.throws(()=>new Swarm(c));
});
test('10,000 agents execute under the same budget',()=>{
 const r=runSimulation({population:10000,rounds:3});assert.equal(r.final_agents.length,10000);assert.equal(r.history.at(-1).effort,120000);assert.ok(Number.isFinite(r.history.at(-1).brier));
});
test('cross-engine replay tolerates rounding only in beliefs and Brier scores',()=>{
 const original=runSimulation({population:16,rounds:4});
 const rounded=structuredClone(original);
 rounded.history[2].brier+=1e-15;rounded.final_agents[0].belief+=1e-15;
 assert.doesNotThrow(()=>assertReplayMatches(rounded));
 for(const mutate of [
  r=>r.history[2].brier+=1e-8,
  r=>r.history[2].wrong+=1e-15,
  r=>r.history[2].messages++,
  r=>r.config.communication+=1e-15,
  r=>r.final_agents[0].checked=!r.final_agents[0].checked,
  r=>r.extra='unrecognized',
  r=>r.final_agents[0].source_ids.push('fabricated'),
 ]){const changed=structuredClone(original);mutate(changed);assert.throws(()=>assertReplayMatches(changed,original),/Replay/);}
});
test('replay rejects malformed histories and intervention inputs',()=>{
 const s=new Swarm({population:16,rounds:5});s.step();s.injectCorrection();s.step();
 const original=s.exportRun();
 for(const mutate of [
  r=>r.history=[],
  r=>r.history[1].round=3,
  r=>r.interventions[0].round=3,
  r=>r.interventions[0].agent_ids=[16],
  r=>r.interventions[0].agent_ids=[0,0],
  r=>r.interventions[0].agent_ids=[0.1],
  r=>r.interventions[0].type='unknown',
  r=>r.interventions[0].extra=true,
 ]){const changed=structuredClone(original);mutate(changed);assert.throws(()=>replayRun(changed));}
});
test('modular group edges respect boundaries for uneven populations',()=>{
 const population=17,seed=42;
 const g=makeNetwork(validateConfig({population,topology:'modular',seed}));
 for(let i=0;i<population;i++){
  const group=Math.floor(i*4/population),start=Math.ceil(group*population/4),end=Math.ceil((group+1)*population/4);
  const local=start+(i-start+2)%(end-start);
  if(local!==i)assert.ok(g[i].includes(local));
 }
});
