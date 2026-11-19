import {normalizeDecisionTerrain} from './evidence/target-control.mjs';

/** A radius is the explicit opt-in; no live AI/effective-malus replay is requested. */
export function terrainQueryFromArgs(args) {
  const options={'--terrain-radius':'radius','--terrain-cells':'maxCells','--terrain-millis':'maxMillis'};
  if(!args.includes('--terrain-radius')) {
    if(args.some(a=>Object.hasOwn(options,a)))throw new TypeError('TERRAIN_RADIUS_OPT_IN_REQUIRED');
    return null;
  }
  const value={radius:null,maxCells:49,maxMillis:10};
  for(const [flag,key] of Object.entries(options)) {
    const positions=args.flatMap((a,i)=>a===flag?[i]:[]);
    if(!positions.length)continue;
    if(positions.length!==1)throw new TypeError('DUPLICATE_TERRAIN_OPTION: '+flag);
    const raw=args[positions[0]+1];
    if(typeof raw!=='string'||!raw.trim()||raw.startsWith('--'))throw new TypeError('MISSING_TERRAIN_OPTION: '+flag);
    value[key]=Number(raw);
  }
  return normalizeDecisionTerrain(value);
}
