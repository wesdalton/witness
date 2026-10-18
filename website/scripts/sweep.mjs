#!/usr/bin/env node
import {readFile,writeFile} from 'node:fs/promises';
import {runSimulation,assertReplayMatches,VERSION} from '../dist/engine.js';
const args=process.argv.slice(2);
if(args[0]==='--replay'){
 const record=JSON.parse(await readFile(args[1],'utf8'));
 const records=record.schema==='witness.comparison.v1'?[record.primary,record.alternate]:[record];
 for(const r of records)assertReplayMatches(r);
 console.log(`Verified replay of ${records.length} run(s): exact structure and discrete outcomes; belief/Brier tolerance 1e-12.`);
}else{
 const seeds=args.includes('--seeds')?Number(args[args.indexOf('--seeds')+1]):10,out=args.includes('--out')?args[args.indexOf('--out')+1]:'swarm-baseline.json';
 if(!Number.isInteger(seeds)||seeds<1||seeds>1000)throw new Error('Use --seeds 1..1000');
 const rows=[];
 for(let seed=0;seed<seeds;seed++)for(const truth of [false,true])for(const topology of ['small-world','modular','hub'])for(const protocol of ['endorsement','provenance','reserved'])for(const communication of [.9,.98,1]){
 const r=runSimulation({seed,truth,topology,protocol,communication});
 rows.push({seed,truth,topology,protocol,communication,final:r.history.at(-1),peak_wrong:Math.max(...r.history.map(h=>h.wrong)),mean_wrong:r.history.reduce((a,h)=>a+h.wrong,0)/r.history.length});}
 await writeFile(out,JSON.stringify({schema:'witness.sweep.v1',engine_version:VERSION,kind:'authored_mechanistic_baseline',calibrated_to_llms:false,seeds,rows},null,2)+'\n');
 console.log(`Wrote ${rows.length} synthetic runs to ${out}; these are not LLM observations.`);
}
