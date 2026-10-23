import assert from 'node:assert/strict';
import path from 'node:path';
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';

export const versions=Object.freeze({minecraft:'1.20.1',forge:'47.4.10',java:17,gradle:'8.8',forgeGradle:'6.0.54'});
export const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const exact=(value,fields)=>assert(value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).sort().join()===fields.sort().join(),'TANK_EXACT_FIELDS');
const hex=(value,n)=>typeof value==='string'&&new RegExp('^[a-f0-9]{'+n+'}$').test(value);
const uuid=value=>typeof value==='string'&&/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i.test(value);

/** Data only: never resolves commands, executes builds, changes a world or launches. */
export function validateProfile(p){
 exact(p,['schema','id','runtime','mods','world','playerUuid','subjectUuid','sourceRevision','mode','maxTicks','maxWallMs','maxEvents']);
 assert.equal(p.schema,'kneekura.tank-profile/v1');assert(typeof p.id==='string'&&/^[a-z][a-z0-9-]{1,63}$/.test(p.id),'TANK_PROFILE_ID');
 exact(p.runtime,['minecraft','forge','java']);for(const name of ['minecraft','forge','java'])assert.equal(p.runtime[name],versions[name],'TANK_COMPATIBILITY_'+name);
 assert(Array.isArray(p.mods)&&p.mods.length<=32,'TANK_MOD_LIMIT');
 const ids=new Set();for(const m of p.mods){exact(m,['id','file','sha256','kind']);assert(typeof m.id==='string'&&/^[a-z][a-z0-9_]{1,63}$/.test(m.id),'TANK_MOD_ID');assert(!ids.has(m.id)&&!['kneekura_manual_adapter','kneekura_tank_host'].includes(m.id),'TANK_DUPLICATE_MOD');ids.add(m.id);assert(path.isAbsolute(m.file)&&m.file.endsWith('.jar'),'TANK_MOD_PATH');assert(hex(m.sha256,64),'TANK_MOD_HASH');assert(['mapped-dev','forge-distribution'].includes(m.kind),'TANK_ARTIFACT_KIND');}
 exact(p.world,['directory','inventorySha256']);assert(path.isAbsolute(p.world.directory)&&hex(p.world.inventorySha256,64),'TANK_WORLD_PIN');
 assert(uuid(p.playerUuid)&&uuid(p.subjectUuid)&&p.playerUuid!==p.subjectUuid,'TANK_ACTORS');assert(p.sourceRevision===null||hex(p.sourceRevision,40),'TANK_SOURCE_REVISION');
 assert(['LIFECYCLE','MANUAL_RALLY','MANUAL_OBSERVE'].includes(p.mode),'TANK_MODE');for(const [key,max] of [['maxTicks',2400],['maxWallMs',120000],['maxEvents',512]])assert(Number.isInteger(p[key])&&p[key]>0&&p[key]<=max,'TANK_BOUND_'+key);
 return structuredClone(p);
}
/** Reject symlinks/junctions in every existing path component, not only the leaf. */
export async function regularPath(file,directory=false){
 assert(path.isAbsolute(file),'TANK_ABSOLUTE_PATH');let current=path.resolve(file);
 while(true){const info=await fs.lstat(current);assert(!info.isSymbolicLink(),'TANK_REPARSE_PATH');if(current===path.parse(current).root)break;current=path.dirname(current);}
 const info=await fs.stat(file);assert(directory?info.isDirectory():info.isFile(),'TANK_PATH_KIND');return fs.realpath(file);
}
export async function inventory(root,relative=''){
 if(!relative)await regularPath(root,true);const rows=[];
 for(const e of await fs.readdir(path.join(root,relative),{withFileTypes:true})){assert(!e.isSymbolicLink(),'TANK_WORLD_REPARSE');const file=path.join(relative,e.name);if(e.isDirectory())rows.push(...await inventory(root,file));else{assert(e.isFile(),'TANK_WORLD_ENTRY');rows.push({file:file.replaceAll('\\','/'),sha256:hash(await fs.readFile(path.join(root,file)))});}}
 return rows.sort((a,b)=>a.file.localeCompare(b.file,'en'));
}
export const inventoryHash=rows=>hash(Buffer.from(JSON.stringify(rows)));
export async function verifyProfile(profile){
 const p=validateProfile(profile);
 for(const m of p.mods){await regularPath(m.file);assert.equal(hash(await fs.readFile(m.file)),m.sha256,'TANK_MOD_TAMPERED_'+m.id);}
 const rows=await inventory(p.world.directory);assert.equal(inventoryHash(rows),p.world.inventorySha256,'TANK_WORLD_TAMPERED');
 return {profile:p,worldInventory:rows};
}
