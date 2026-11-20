import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {randomUUID} from 'node:crypto';
import {hash,versions,inventory,inventoryHash,validateProfile} from './profile.mjs';

/**
 * `tank.json` in a MOD project: the few facts only its developer knows. Everything derivable
 * (hashes, inventory, revision, player UUID, immutable artifact copy) is derived here.
 * {schema:'kneekura.tank-project/v1', id, mods:[{id,jar,kind}], world, subjectUuid?, mode?, playerUuid?, look?, view?, selfTest?, maxTicks?, maxWallMs?, maxEvents?}
 * `world` is a path (absolute or project-relative) or `@name` of a Tank fixture carrying `tank-fixture.json`, which also supplies player/subject.
 * subjectUuid is the living entity READY waits for (every mode); it cannot be read from a world without NBT, so it is never guessed.
 * look: 'plain' (default) | 'grid' (client grid, v2 presentation). view: 'tank' (default; render 4 / simulation 5) | 'native' (game defaults).
 * trails: true (default) draws sampled Mob/Projectile trails near the Player; false disables.
 * ai: true (default) shows what nearby Mob AI is doing (running goals, target, path, MOD state fields) and logs ai.jsonl; false disables.
 * selfTest: true passes -Dkneekura.tank.selfTest=<trial nonce>; the MOD reports `KNEEKURA_TANK_SELFTEST <nonce> PASS|FAIL <name> ...` and `... DONE pass=N fail=M`.
 * `jar` may use `*` in its file name (newest match wins).
 */
export const PROJECT_SCHEMA='kneekura.tank-project/v1',FIXTURE_SCHEMA='kneekura.tank-fixture/v1';
export const VIEWS=Object.freeze({tank:{renderDistance:4,simulationDistance:5},native:null});
const optional=['mode','playerUuid','subjectUuid','look','view','selfTest','trails','ai','maxTicks','maxWallMs','maxEvents'];
export function validateProject(value){
 assert(value&&typeof value==='object'&&!Array.isArray(value),'TANK_PROJECT_OBJECT');
 for(const key of Object.keys(value))assert(['schema','id','mods','world',...optional].includes(key),'TANK_PROJECT_UNKNOWN_FIELD_'+key);
 assert.equal(value.schema,PROJECT_SCHEMA,'TANK_PROJECT_SCHEMA');assert(typeof value.id==='string'&&/^[a-z][a-z0-9-]{1,63}$/.test(value.id),'TANK_PROJECT_ID');
 assert(Array.isArray(value.mods)&&value.mods.length>0,'TANK_PROJECT_MODS');
 for(const m of value.mods){assert(m&&typeof m==='object'&&Object.keys(m).sort().join()==='id,jar,kind','TANK_PROJECT_MOD_FIELDS');assert(typeof m.jar==='string'&&m.jar.endsWith('.jar'),'TANK_PROJECT_JAR');}
 assert(typeof value.world==='string'&&value.world,'TANK_PROJECT_WORLD');const mode=value.mode??'LIFECYCLE';
 assert(value.world.startsWith('@')||typeof value.subjectUuid==='string'&&value.subjectUuid,'TANK_PROJECT_SUBJECT_REQUIRED (UUID of a living entity saved in the world; READY waits for it)');
 const look=value.look??'plain';assert(['plain','grid'].includes(look),'TANK_PROJECT_LOOK');const view=value.view??'tank';assert(Object.hasOwn(VIEWS,view),'TANK_PROJECT_VIEW');
 assert(value.selfTest===undefined||typeof value.selfTest==='boolean','TANK_PROJECT_SELFTEST');
 assert(value.trails===undefined||typeof value.trails==='boolean','TANK_PROJECT_TRAILS');
 assert(value.ai===undefined||typeof value.ai==='boolean','TANK_PROJECT_AI');
 return {...value,mode,look,view,selfTest:value.selfTest===true,trails:value.trails!==false,ai:value.ai!==false};
}
/** `@name` → the fixture whose tank-fixture.json declares that name. Exactly one match. */
export async function resolveFixture(tankRoot,name){
 const root=path.join(tankRoot,'fixtures');const found=[];
 for(const entry of await fs.readdir(root,{withFileTypes:true}).catch(()=>[])){if(!entry.isDirectory())continue;const file=path.join(root,entry.name,'tank-fixture.json');const value=await fs.readFile(file,'utf8').then(JSON.parse).catch(()=>null);if(value?.name===name)found.push({dir:path.join(root,entry.name),value});}
 assert.equal(found.length,1,'TANK_FIXTURE_'+(found.length?'AMBIGUOUS':'NOT_FOUND')+' @'+name);const {dir,value}=found[0];
 assert.equal(value.schema,FIXTURE_SCHEMA,'TANK_FIXTURE_SCHEMA');assert(typeof value.world==='string'&&!path.isAbsolute(value.world),'TANK_FIXTURE_WORLD');
 const world=path.resolve(dir,value.world);assert(!path.relative(dir,world).startsWith('..'),'TANK_FIXTURE_ESCAPE');
 return {world,playerUuid:value.playerUuid,subjectUuid:value.subjectUuid,description:value.description??null};
}
/** Lines from the MOD carrying this trial's nonce only; stale or foreign lines are ignored. Bounded to 256 rows. */
export function parseSelfTest(text,nonce){
 const rows=[];let done=null;const marker='KNEEKURA_TANK_SELFTEST '+nonce+' ';
 for(const line of (text??'').split(/\r?\n/)){const at=line.indexOf(marker);if(at<0)continue;const rest=line.slice(at+marker.length).trim();const [verdict,...words]=rest.split(/\s+/);
  if(verdict==='DONE'){const m=rest.match(/pass=(\d+)\s+fail=(\d+)/);done=m?{pass:Number(m[1]),fail:Number(m[2])}:{malformed:rest.slice(0,200)};}
  else if((verdict==='PASS'||verdict==='FAIL')&&rows.length<256)rows.push({verdict,name:(words[0]??'').slice(0,120),detail:words.slice(1).join(' ').slice(0,300)});}
 const pass=rows.filter(r=>r.verdict==='PASS').length,fail=rows.length-pass;
 const status=!done?'INCOMPLETE_NO_DONE':done.malformed!==undefined||done.pass!==pass||done.fail!==fail?'INCONSISTENT':fail>0?'FAIL':pass>0?'PASS':'EMPTY';
 return {status,scope:'MOD_SELF_REPORTED_NOT_TANK_VERIFIED',pass,fail,done,rows};
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
 const fixture=project.world.startsWith('@')?await resolveFixture(tankRoot,project.world.slice(1)):null;
 const world=fixture?fixture.world:path.resolve(projectDir,project.world);const git=gitRevision(projectDir);
 const subjectUuid=project.subjectUuid??fixture?.subjectUuid;assert(typeof subjectUuid==='string','TANK_PROJECT_SUBJECT_REQUIRED (fixture declares none)');
 const view=VIEWS[project.view];
 const profile=validateProfile({schema:project.look==='grid'?'kneekura.tank-profile/v2':'kneekura.tank-profile/v1',id:project.id+'-'+project.mode.toLowerCase().replaceAll('_','-'),runtime:{minecraft:versions.minecraft,forge:versions.forge,java:versions.java},mods,
  world:{directory:world,inventorySha256:inventoryHash(await inventory(world))},playerUuid:(project.playerUuid??fixture?.playerUuid??await inferPlayerUuid(world)).toLowerCase(),subjectUuid:subjectUuid.toLowerCase(),
  sourceRevision:git.revision,mode:project.mode,maxTicks:project.maxTicks??600,maxWallMs:project.maxWallMs??30000,maxEvents:project.maxEvents??128,
  ...(project.look==='grid'?{presentation:{grid:true,brightness:'NATIVE'}}:{}),...(view?{view:{...view}}:{}),...(project.selfTest?{selfTest:true}:{}),...(project.trails?{trails:true}:{}),...(project.ai?{ai:true}:{})});
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
 // Native adapter's own explanation of why READY never came (bounded files it wrote under the run's derived evidence).
 const derived=await findDerived(path.join(trial,'runtime'));
 if(derived){out.readyWait=(await fs.readFile(path.join(derived,'ready-wait.jsonl'),'utf8').catch(()=>'')).split('\n').filter(Boolean).slice(-8).map(line=>{try{return JSON.parse(line).reason;}catch{return 'UNPARSEABLE';}});
  for(const name of ['bootstrap-subject.json','bootstrap-timeout.json'])out[name]=await fs.readFile(path.join(derived,name),'utf8').then(JSON.parse).catch(()=>undefined);}
 return out;
}
async function findDerived(runtime){
 const sessions=path.join(runtime,'sessions');for(const s of await fs.readdir(sessions).catch(()=>[]))for(const r of await fs.readdir(path.join(sessions,s,'runs')).catch(()=>[])){const dir=path.join(sessions,s,'runs',r,'evidence/derived/manual-interaction');if(await fs.stat(dir).catch(()=>null))return dir;}
 return null;
}
