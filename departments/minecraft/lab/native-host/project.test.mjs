import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {validateProject,resolveJar,inferPlayerUuid,buildProfile,summarizeFailure} from './project.mjs';
import {hash,inventory,inventoryHash} from './profile.mjs';

const player='380df991-f603-344c-a090-369bad2a924a',subject='67676767-1007-4000-8000-000000000001';
async function project(t,extra={}){
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'tank-project-'));t.after(()=>fs.rm(root,{recursive:true,force:true}));
 const dir=path.join(root,'mod'),tank=path.join(root,'Tank'),world=path.join(root,'fixture/KNEEKURA_DEBUG_WORLD');
 await fs.mkdir(path.join(dir,'build/libs'),{recursive:true});await fs.mkdir(path.join(world,'playerdata'),{recursive:true});await fs.mkdir(tank);
 await fs.writeFile(path.join(world,'level.dat'),'level');await fs.writeFile(path.join(world,'playerdata',player+'.dat'),'p');await fs.writeFile(path.join(world,'playerdata',player+'.dat_old'),'p');
 const old=path.join(dir,'build/libs/demo-0.1.jar'),neu=path.join(dir,'build/libs/demo-0.2.jar');await fs.writeFile(old,'old');await fs.writeFile(neu,'new');
 await fs.utimes(old,new Date(1000),new Date(1000));await fs.utimes(neu,new Date(2000000),new Date(2000000));
 await fs.writeFile(path.join(dir,'tank.json'),JSON.stringify({schema:'kneekura.tank-project/v1',id:'demo',mods:[{id:'demo_mod',jar:'build/libs/demo-*.jar',kind:'forge-distribution'}],world:path.relative(dir,world),subjectUuid:subject,...extra}));
 return {dir,tank,world,neu};
}
test('tank.json needs only developer facts; unknown fields and a missing subject are rejected in every mode',()=>{
 const ok={schema:'kneekura.tank-project/v1',id:'demo',mods:[{id:'m',jar:'a.jar',kind:'mapped-dev'}],world:'w',subjectUuid:subject};
 assert.equal(validateProject(ok).mode,'LIFECYCLE');
 assert.throws(()=>validateProject({...ok,sha256:'x'}),/UNKNOWN_FIELD_sha256/);
 const {subjectUuid,...noSubject}=ok;assert.throws(()=>validateProject(noSubject),/SUBJECT_REQUIRED/);
 assert.throws(()=>validateProject({...ok,mods:[{id:'m',jar:'a.zip',kind:'mapped-dev'}]}),/TANK_PROJECT_JAR/);
});
test('newest matching build artifact is chosen and reported with the number of candidates',async t=>{
 const p=await project(t);const found=await resolveJar(p.dir,'build/libs/demo-*.jar');assert.equal(found.file,p.neu);assert.equal(found.candidates,2);
 await assert.rejects(resolveJar(p.dir,'build/libs/none-*.jar'),/JAR_NOT_FOUND/);
});
test('the single saved Player is inferred; ambiguity requires an explicit UUID',async t=>{
 const p=await project(t);assert.equal(await inferPlayerUuid(p.world),player);
 await fs.writeFile(path.join(p.world,'playerdata','11111111-1111-4111-8111-111111111111.dat'),'q');await assert.rejects(inferPlayerUuid(p.world),/PLAYER_UUID_AMBIGUOUS/);
});
test('buildProfile stores the artifact by content hash and pins world inventory without changing the world',async t=>{
 const p=await project(t);const before=inventoryHash(await inventory(p.world));const built=await buildProfile(p.dir,p.tank);
 const m=built.profile.mods[0];assert.equal(m.sha256,hash(Buffer.from('new')));assert.equal(m.file,path.join(p.tank,'mods/demo_mod',m.sha256+'-forge-distribution.jar'));assert.equal(await fs.readFile(m.file,'utf8'),'new');
 assert.equal(built.profile.world.inventorySha256,before);assert.equal(inventoryHash(await inventory(p.world)),before);
 assert.equal(built.profile.id,'demo-lifecycle');assert.equal(built.profile.playerUuid,player);assert.equal(built.profile.subjectUuid,subject);assert.equal(built.profile.sourceRevision,null);
 assert.deepEqual(JSON.parse(await fs.readFile(built.file,'utf8')),built.profile);
 const again=await buildProfile(p.dir,p.tank);assert.equal(again.profile.mods[0].file,m.file);assert.notEqual(again.file,built.file);
});
test('failure digest is bounded to crash description and last error lines',async t=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'tank-digest-'));t.after(()=>fs.rm(root,{recursive:true,force:true}));
 await fs.mkdir(path.join(root,'game/logs'),{recursive:true});await fs.mkdir(path.join(root,'game/crash-reports'));
 await fs.writeFile(path.join(root,'game/crash-reports/crash-1.txt'),'---- Minecraft Crash Report ----\nTime: x\nDescription: Mod loading error\n\norg.spongepowered.asm.mixin.injection.throwables.InvalidInjectionException: bad\n');
 await fs.writeFile(path.join(root,'game/logs/latest.log'),Array.from({length:30},(_,i)=>'[main/ERROR] line '+i).join('\n')+'\n[main/INFO] ok\n');
 await fs.writeFile(path.join(root,'launch-failure.json'),'{"error":"x"}');
 const d=await summarizeFailure(root);assert.equal(d.crashReport.excerpt[0],'Description: Mod loading error');assert.equal(d.logErrors.length,12);assert.equal(d.logErrors.at(-1),'[main/ERROR] line 29');assert.equal(d['launch-failure.json'].error,'x');
});
// Fixture names, look/view presets and the MOD self-test channel.
import {resolveFixture,parseSelfTest,VIEWS} from './project.mjs';
test('presets: default view is tank-sized, look grid selects v2 presentation, selfTest flag is carried',async t=>{
 const p=await project(t);const plain=await buildProfile(p.dir,p.tank);assert.equal(plain.profile.schema,'kneekura.tank-profile/v1');assert.deepEqual(plain.profile.view,VIEWS.tank);assert.equal(Object.hasOwn(plain.profile,'selfTest'),false);assert.equal(plain.profile.trails,true);assert.equal(plain.profile.ai,true);
 const q=await project(t,{look:'grid',view:'native',selfTest:true,trails:false,ai:false});const grid=await buildProfile(q.dir,q.tank);
 assert.equal(grid.profile.schema,'kneekura.tank-profile/v2');assert.deepEqual(grid.profile.presentation,{grid:true,brightness:'NATIVE'});assert.equal(Object.hasOwn(grid.profile,'view'),false);assert.equal(grid.profile.selfTest,true);assert.equal(Object.hasOwn(grid.profile,'trails'),false);assert.equal(Object.hasOwn(grid.profile,'ai'),false);
 assert.throws(()=>validateProject({schema:'kneekura.tank-project/v1',id:'dd',mods:[{id:'m',jar:'a.jar',kind:'mapped-dev'}],world:'w',subjectUuid:subject,look:'neon'}),/LOOK/);
});
test('@fixture supplies world, player and subject; unknown or duplicate names are refused',async t=>{
 const p=await project(t);const fixtureDir=path.dirname(p.world);
 await fs.writeFile(path.join(fixtureDir,'tank-fixture.json'),JSON.stringify({schema:'kneekura.tank-fixture/v1',name:'demo',world:'KNEEKURA_DEBUG_WORLD',playerUuid:player,subjectUuid:subject}));
 // Fixtures live under Tank/fixtures; move the prepared one there.
 const placed=path.join(p.tank,'fixtures','demo-1');await fs.mkdir(path.dirname(placed),{recursive:true});await fs.cp(fixtureDir,placed,{recursive:true});
 const f=await resolveFixture(p.tank,'demo');assert.equal(f.subjectUuid,subject);assert.equal(f.world,path.join(placed,'KNEEKURA_DEBUG_WORLD'));
 const tankJson=JSON.parse(await fs.readFile(path.join(p.dir,'tank.json'),'utf8'));delete tankJson.subjectUuid;tankJson.world='@demo';await fs.writeFile(path.join(p.dir,'tank.json'),JSON.stringify(tankJson));
 const built=await buildProfile(p.dir,p.tank);assert.equal(built.profile.world.directory,f.world);assert.equal(built.profile.subjectUuid,subject);assert.equal(built.profile.playerUuid,player);
 await assert.rejects(resolveFixture(p.tank,'missing'),/FIXTURE_NOT_FOUND/);await fs.cp(placed,path.join(p.tank,'fixtures','demo-2'),{recursive:true});await assert.rejects(resolveFixture(p.tank,'demo'),/FIXTURE_AMBIGUOUS/);
});
test('self-test lines are trusted only with this trial nonce and a consistent DONE line',()=>{
 const n='aaaa-1',log=['[x/INFO] KNEEKURA_TANK_SELFTEST old-nonce FAIL stale','[x/INFO] KNEEKURA_TANK_SELFTEST aaaa-1 PASS registry ok','[x/INFO] KNEEKURA_TANK_SELFTEST aaaa-1 PASS mixin'].join('\n');
 assert.equal(parseSelfTest(log,n).status,'INCOMPLETE_NO_DONE');
 assert.equal(parseSelfTest(log+'\nKNEEKURA_TANK_SELFTEST aaaa-1 DONE pass=2 fail=0',n).status,'PASS');
 assert.equal(parseSelfTest(log+'\nKNEEKURA_TANK_SELFTEST aaaa-1 DONE pass=3 fail=0',n).status,'INCONSISTENT');
 const failed=parseSelfTest(log+'\nKNEEKURA_TANK_SELFTEST aaaa-1 FAIL spell damage=0\nKNEEKURA_TANK_SELFTEST aaaa-1 DONE pass=2 fail=1',n);assert.equal(failed.status,'FAIL');assert.deepEqual(failed.rows[2],{verdict:'FAIL',name:'spell',detail:'damage=0'});
 assert.equal(parseSelfTest('KNEEKURA_TANK_SELFTEST aaaa-1 DONE pass=0 fail=0',n).status,'EMPTY');assert.equal(parseSelfTest(log,n).scope,'MOD_SELF_REPORTED_NOT_TANK_VERIFIED');
});
