import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {randomUUID} from 'node:crypto';
import {hash,versions,inventory,inventoryHash,validateProfile} from './profile.mjs';

/**
 * `tank.json` in a MOD project: the few facts only its developer knows. Everything derivable
 * (hashes, inventory, revision, player UUID, immutable artifact copy) is derived here.
 * {schema:'kneekura.tank-project/v1', id, mods:[{id,jar,kind}], world, mode?, playerUuid?, subjectUuid?, maxTicks?, maxWallMs?, maxEvents?}
 * `jar` and `world` are absolute or relative to the project; `jar` may use `*` in its file name (newest match wins).
 */
export const PROJECT_SCHEMA='kneekura.tank-project/v1';
export const LIFECYCLE_SUBJECT='7a4b0000-0000-4000-8000-000000000001';
const optional=['mode','playerUuid','subjectUuid','maxTicks','maxWallMs','maxEvents'];
export function validateProject(value){
 assert(value&&typeof value==='object'&&!Array.isArray(value),'TANK_PROJECT_OBJECT');
 for(const key of Object.keys(value))assert(['schema','id','mods','world',...optional].includes(key),'TANK_PROJECT_UNKNOWN_FIELD_'+key);
 assert.equal(value.schema,PROJECT_SCHEMA,'TANK_PROJECT_SCHEMA');assert(typeof value.id==='string'&&/^[a-z][a-z0-9-]{1,63}$/.test(value.id),'TANK_PROJECT_ID');
 assert(Array.isArray(value.mods)&&value.mods.length>0,'TANK_PROJECT_MODS');
 for(const m of value.mods){assert(m&&typeof m==='object'&&Object.keys(m).sort().join()==='id,jar,kind','TANK_PROJECT_MOD_FIELDS');assert(typeof m.jar==='string'&&m.jar.endsWith('.jar'),'TANK_PROJECT_JAR');}
 assert(typeof value.world==='string'&&value.world,'TANK_PROJECT_WORLD');const mode=value.mode??'LIFECYCLE';
 assert(mode==='LIFECYCLE'||value.subjectUuid,'TANK_PROJECT_SUBJECT_REQUIRED_FOR_'+mode);
 return {...value,mode};
}
/** Newest regular file matching a `*` pattern in the last path component only. */
export async function resolveJar(projectDir,pattern){
 const full=path.resolve(projectDir,pattern),dir=path.dirname(full),base=path.basename(full);assert(!dir.includes('*'),'TANK_PROJECT_JAR_GLOB_DIRECTORY');
 const re=new RegExp('^'+base.split('*').map(part=>part.replace(/[.+?^${}()|[\]\\]/g,'\\$&')).join('.*')+'$','i');
 const rows=[];for(const entry of await fs.readdir(dir,{withFileTypes:true}))if(entry.isFile()&&re.test(entry.name)){const file=path.join(dir,entry.name);rows.push({file,mtimeMs:(await fs.stat(file)).mtimeMs});}
 assert(rows.length>0,'TANK_PROJECT_JAR_NOT_FOUND '+full);rows.sort((a,b)=>b.mtimeMs-a.mtimeMs);return {file:rows[0].file,candidates:rows.length,builtAt:new Date(rows[0].mtimeMs).toISOString()};
}
/** The world's only saved Player is the one the trial must log in as; ambiguity requires an explicit UUID. */
export async function inferPlayerUuid(world){
 const ids=(await fs.readdir(path.join(world,'playerdata')).catch(()=>[])).filter(name=>/^[0-9a-f-]{36}\.dat$/i.test(name)).map(name=>name.slice(0,36).toLowerCase());
 assert.equal(ids.length,1,'TANK_PROJECT_PLAYER_UUID_AMBIGUOUS_SET_playerUuid ('+ids.length+' saved players)');return ids[0];
}
function gitRevision(dir){try{const rev=execFileSync('git',['rev-parse','HEAD'],{cwd:dir,encoding:'utf8',windowsHide:true,stdio:['ignore','pipe','ignore']}).trim();const dirty=execFileSync('git',['status','--porcelain','--untracked-files=no'],{cwd:dir,encoding:'utf8',windowsHide:true,stdio:['ignore','pipe','ignore']}).trim()!=='';return {revision:/^[a-f0-9]{40}$/.test(rev)?rev:null,dirty};}catch{return {revision:null,dirty:null};}}

/** Copy each artifact into the Tank's content-addressed store, then emit a pinned v1 profile. No launch. */
export async function buildProfile(projectDir,tankRoot){
 projectDir=path.resolve(projectDir);const project=validateProject(JSON.parse(await fs.readFile(path.join(projectDir,'tank.json'),'utf8')));
 const mods=[],artifacts=[];
 for(const m of project.mods){
  const found=await resolveJar(projectDir,m.jar);const bytes=await fs.readFile(found.file);const sha256=hash(bytes);
  const store=path.join(tankRoot,'mods',m.id);await fs.mkdir(store,{recursive:true});const file=path.join(store,sha256+'-'+m.kind+'.jar');
  await fs.writeFile(file,bytes,{flag:'wx'}).catch(error=>{if(error.code!=='EEXIST')throw error;});assert.equal(hash(await fs.readFile(file)),sha256,'TANK_STORE_COLLISION_'+m.id);
  mods.push({id:m.id,file,sha256,kind:m.kind});artifacts.push({id:m.id,source:found.file,builtAt:found.builtAt,candidates:found.candidates,sha256});
 }
 const world=path.resolve(projectDir,project.world);const git=gitRevision(projectDir);
 const profile=validateProfile({schema:'kneekura.tank-profile/v1',id:project.id+'-'+project.mode.toLowerCase().replaceAll('_','-'),runtime:{minecraft:versions.minecraft,forge:versions.forge,java:versions.java},mods,
  world:{directory:world,inventorySha256:inventoryHash(await inventory(world))},playerUuid:(project.playerUuid??await inferPlayerUuid(world)).toLowerCase(),subjectUuid:project.subjectUuid??LIFECYCLE_SUBJECT,
  sourceRevision:git.revision,mode:project.mode,maxTicks:project.maxTicks??600,maxWallMs:project.maxWallMs??30000,maxEvents:project.maxEvents??128});
 const profiles=path.join(tankRoot,'profiles');await fs.mkdir(profiles,{recursive:true});const file=path.join(profiles,profile.id+'-'+randomUUID()+'.json');
 await fs.writeFile(file,JSON.stringify(profile,null,2)+'\n',{flag:'wx'});return {profile,file,artifacts,sourceDirty:git.dirty};
}
/** Short, bounded failure digest: crash-report description and the last error lines of the game log. */
export async function summarizeFailure(trial){
 const game=path.join(trial,'game');const out={};
 const reports=await fs.readdir(path.join(game,'crash-reports')).catch(()=>[]);
 if(reports.length){const name=reports.sort().at(-1);const text=await fs.readFile(path.join(game,'crash-reports',name),'utf8');const lines=text.split(/\r?\n/);const at=lines.findIndex(line=>line.startsWith('Description:'));out.crashReport={file:path.join(game,'crash-reports',name),excerpt:lines.slice(Math.max(0,at),Math.max(0,at)+8).map(line=>line.slice(0,300))};}
 const log=await fs.readFile(path.join(game,'logs/latest.log'),'utf8').catch(()=>null);
 if(log)out.logErrors=log.split(/\r?\n/).filter(line=>/\b(ERROR|FATAL)\b|Exception|Caused by/.test(line)).slice(-12).map(line=>line.slice(0,300));
 for(const name of ['launch-failure.json','failed-run-cleanup.json'])out[name]=await fs.readFile(path.join(trial,name),'utf8').then(JSON.parse).catch(()=>undefined);
 return out;
}
