/** Read authority only. Interior bounds never replace the action grant. */
import {exactKeys,integer,hashId,stableJson,sha256} from './json.mjs';
import {validTankGeometry} from '../evidence/tank-contract.mjs';

export const TANK_OBSERVATION_PERMISSION='TANK_OBSERVATION_READ';
export function validateTankObservation(value,world,saved=null){
 exactKeys(value,['schemaVersion','scope','dimensionId','min','max','recipeHash','maxEntities','maxSamples'],'TANK_OBSERVATION');
 integer(value.schemaVersion,1,1);hashId(value.recipeHash);integer(value.maxEntities,1,64);integer(value.maxSamples,1,8);
 if(value.scope!==TANK_OBSERVATION_PERMISSION||value.dimensionId!=='minecraft:overworld'||value.dimensionId!==world.dimensionId||!world.permissions.includes(TANK_OBSERVATION_PERMISSION))throw new Error('TANK_OBSERVATION_PERMISSION');
 if(!Array.isArray(value.min)||!Array.isArray(value.max)||value.min.length!==3||value.max.length!==3)throw new Error('TANK_OBSERVATION_BOUNDS');
 value.min.forEach(n=>integer(n,-30000000,30000000));value.max.forEach(n=>integer(n,-30000000,30000000));
 const [x,y,z]=value.min,[width,height,depth]=value.max.map((n,i)=>n-value.min[i]);
 if(!validTankGeometry({x,y,z,width,height,depth}))throw new Error('TANK_OBSERVATION_BOUNDS');
 if(saved!==null){
  const r=saved?.recipe,o=r?.origin,d=r?.dimensions;
  if(saved?.status!=='GEOMETRY_VERIFIED'||r?.v!==1||r?.kind!=='tank_recipe'||r?.dimension!==value.dimensionId||
    saved.recipeHash?.replace(/^sha256:/,'')!==value.recipeHash||sha256(stableJson(r))!==value.recipeHash||
    stableJson([o?.x,o?.y,o?.z])!==stableJson(value.min)||stableJson([o?.x+d?.width,o?.y+d?.height,o?.z+d?.depth])!==stableJson(value.max))throw new Error('TANK_OBSERVATION_RECIPE');
 }
 return structuredClone(value);
}
export function tankBounds(scope){
 return {semantics:'MIN_INCLUSIVE_MAX_EXCLUSIVE',interior:{min:[...scope.min],max:[...scope.max]},
  physical:{min:scope.min.map(n=>n-1),max:scope.max.map(n=>n+1)}};
}
