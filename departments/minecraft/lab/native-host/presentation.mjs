import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
const exact=(v,keys)=>assert(v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).sort().join()===keys.sort().join(),'TANK_PRESENTATION_FIELDS');
const canonical=v=>Array.isArray(v)?'['+v.map(canonical).join(',')+']':v&&typeof v==='object'?'{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}':JSON.stringify(v);
export function validatePresentationSettings(v){exact(v,['grid','brightness']);assert.equal(v.grid,true);assert.equal(v.brightness,'NATIVE','TANK_GRID_DOES_NOT_GRANT_BRIGHTNESS');return structuredClone(v);}
export function validatePresentation(v){
 exact(v,['renderer','grid','brightness','recipeHash','min','max']);validatePresentationSettings({grid:v.grid,brightness:v.brightness});assert.equal(v.renderer,'tank-grid-v1');assert(typeof v.recipeHash==='string'&&/^[a-f0-9]{64}$/.test(v.recipeHash));
 for(const k of ['min','max'])assert(Array.isArray(v[k])&&v[k].length===3&&v[k].every(Number.isInteger),'TANK_GRID_BOUNDS');
 const size=v.max.map((n,i)=>n-v.min[i]);assert(size.every(n=>n>0&&n<=64)&&size.reduce((a,b)=>a*b,1)<=65536,'TANK_GRID_VOLUME');
 assert(v.min[1]>=-63&&v.max[1]<=319&&[0,2].every(i=>v.min[i]>=-29999983&&v.max[i]<=29999984),'TANK_GRID_WORLD_BOUNDS');return structuredClone(v);
}
export function presentationFromRecipe(saved,settings){
 validatePresentationSettings(settings);assert.equal(saved.status,'GEOMETRY_VERIFIED');const r=saved.recipe;assert(r?.v===1&&r.kind==='tank_recipe'&&r.dimension==='minecraft:overworld','TANK_GRID_RECIPE');
 const recipeHash=createHash('sha256').update(canonical(r)).digest('hex');assert.equal(saved.recipeHash.replace(/^sha256:/,''),recipeHash,'TANK_GRID_RECIPE_HASH');
 const min=['x','y','z'].map(k=>r.origin[k]),size=['width','height','depth'].map(k=>r.dimensions[k]);
 return validatePresentation({renderer:'tank-grid-v1',...settings,recipeHash,min,max:min.map((n,i)=>n+size[i])});
}
export async function preparePresentation(world,settings){const file=path.join(world,'kneekura-tank-owner.json');const stat=await fs.lstat(file);assert(stat.isFile()&&!stat.isSymbolicLink()&&stat.size<=65536,'TANK_GRID_SAVED_RECIPE');return presentationFromRecipe(JSON.parse(await fs.readFile(file,'utf8')),settings);}
