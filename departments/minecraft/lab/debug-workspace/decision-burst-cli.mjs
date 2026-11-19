import {normalizeDecisionBurst} from './evidence/target-control.mjs';

/** Parse only explicit bounded observation options; launch enablement remains a separate prerequisite. */
export function decisionBurstFromArgs(args) {
  const options={'--decision-ticks':'ticks','--decision-events':'maxEvents','--decision-bytes':'maxBytes',
    '--decision-nodes':'maxNodes','--decision-channels':'channels'};
  const enabled=args.includes('--decision-burst');
  if(!enabled) {
    if(args.some(a=>Object.hasOwn(options,a)))throw new TypeError('DECISION_BURST_OPT_IN_REQUIRED');
    return null;
  }
  if(args.filter(a=>a==='--decision-burst').length!==1)throw new TypeError('DUPLICATE_DECISION_BURST');
  const value={ticks:100,maxEvents:256,maxBytes:262144,maxNodes:32,channels:['goal','brain','path','control','malus','sensor']};
  for(const [flag,key] of Object.entries(options)) {
    const positions=args.flatMap((a,i)=>a===flag?[i]:[]);
    if(!positions.length)continue;
    if(positions.length!==1)throw new TypeError('DUPLICATE_DECISION_OPTION: '+flag);
    const raw=args[positions[0]+1];
    if(typeof raw!=='string'||!raw.length||raw.startsWith('--'))throw new TypeError('MISSING_DECISION_OPTION: '+flag);
    value[key]=key==='channels'?raw.split(','):Number(raw);
  }
  return normalizeDecisionBurst(value);
}
