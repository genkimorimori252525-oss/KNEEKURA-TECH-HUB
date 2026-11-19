import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {cleanupFailedLaunch} from './tank.mjs';
import {hash} from './profile.mjs';

// Regression: a launch that died before manual-claim.json used to fail with ENOENT and keep host-lock.json forever.
async function fixture(t){
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'tank-unbound-'));t.after(()=>fs.rm(root,{recursive:true,force:true}));
 const installed=path.join(root,'host'),trial=path.join(root,'runs','five-lifecycle-1');await fs.mkdir(installed,{recursive:true});await fs.mkdir(path.join(trial,'inputs'),{recursive:true});
 await fs.writeFile(path.join(trial,'inputs/manual-request.json'),'{"v":1}\n');
 const lock={file:path.join(installed,'host-lock.json'),token:'token-1'};await fs.writeFile(lock.file,JSON.stringify({token:'token-1',operation:'run:'+trial}));await fs.writeFile(path.join(trial,'host-lock.json'),JSON.stringify(lock));
 const current={runDir:path.join(trial,'runtime/run'),pid:500,spawnedAtEpochMs:50000,status:'FAILED'};const stops=[];
 const core={readCurrent:async()=>current,stopCurrent:async()=>{stops.push(1);return {cleanup:{status:'VERIFIED_EXIT'}};}};
 const p={trial,config:{},state:{installed,manifest:{javaHome:path.join(root,'jdk')}}};
 return {p,core,lock,trial,stops,requestHash:hash(await fs.readFile(path.join(trial,'inputs/manual-request.json')))};
}
const quiet=[{pid:1,parentPid:0,name:'System',commandLine:null,startedAtEpochMs:1},{pid:700,parentPid:1,name:'java.exe',commandLine:'"C:/other/java.exe" -jar x.jar',startedAtEpochMs:10}];
const exists=file=>fs.stat(file).then(()=>true,()=>false);

test('unbound failed launch with positively absent trial processes is cleaned up and its own lock released',async t=>{
 const f=await fixture(t);const result=await cleanupFailedLaunch(f.p,f.core,{list:async()=>quiet,waitMs:0});
 assert.equal(result.status,'FAILED_BEFORE_NATIVE_CLAIM_NO_TRIAL_PROCESS_VERIFIED');assert.equal(result.worldAcceptance,'NOT_ESTABLISHED');assert.equal(f.stops.length,1);
 assert.equal(await exists(f.lock.file),false);assert.equal(JSON.parse(await fs.readFile(path.join(f.trial,'failed-run-cleanup.json'),'utf8')).status,result.status);
});
test('unbound failed launch keeps the lock while an identity-bearing Minecraft java is alive',async t=>{
 const f=await fixture(t);const rows=[...quiet,{pid:600,parentPid:44,name:'java.exe',commandLine:'java -Dkneekura.tank.requestSha256='+f.requestHash+' Main',startedAtEpochMs:60000}];
 await assert.rejects(cleanupFailedLaunch(f.p,f.core,{list:async()=>rows,waitMs:0}),/TANK_UNBOUND_TRIAL_PROCESS_PRESENT 600/);
 assert.equal(await exists(f.lock.file),true);assert.equal(f.stops.length,0);assert.equal(await exists(path.join(f.trial,'failed-run-cleanup.json')),false);
});
test('unbound failed launch keeps the lock when ownership is unknown or the listing fails',async t=>{
 const f=await fixture(t);const javaHome=f.p.state.manifest.javaHome;
 await assert.rejects(cleanupFailedLaunch(f.p,f.core,{list:async()=>[...quiet,{pid:601,parentPid:44,name:'java.exe',commandLine:'"'+path.join(javaHome,'bin/java.exe')+'" @"gone.txt"',startedAtEpochMs:60000,argFiles:[{file:'gone.txt',text:null}]}],waitMs:0}),/TANK_UNBOUND_TRIAL_PROCESS_UNKNOWN/);
 await assert.rejects(cleanupFailedLaunch(f.p,f.core,{list:async()=>{throw Error('TANK_PROCESS_LISTING_FAILED');},waitMs:0}),/LISTING_FAILED/);
 assert.equal(await exists(f.lock.file),true);assert.equal(f.stops.length,0);
});
test('unbound cleanup never removes a lock already taken by a later trial',async t=>{
 const f=await fixture(t);await fs.writeFile(f.lock.file,JSON.stringify({token:'later-trial'}));
 await cleanupFailedLaunch(f.p,f.core,{list:async()=>quiet,waitMs:0});assert.equal(JSON.parse(await fs.readFile(f.lock.file,'utf8')).token,'later-trial');
});
test('a slowly exiting JVM is observed again within the bounded wait, never terminated',async t=>{
 const f=await fixture(t);let calls=0;const alive=[...quiet,{pid:600,parentPid:44,name:'java.exe',commandLine:'java -Dkneekura.tank.requestSha256='+f.requestHash,startedAtEpochMs:60000}];
 const result=await cleanupFailedLaunch(f.p,f.core,{list:async()=>++calls<3?alive:quiet,waitMs:5000,pollMs:1});assert.equal(result.status,'FAILED_BEFORE_NATIVE_CLAIM_NO_TRIAL_PROCESS_VERIFIED');assert.equal(calls,3);
});
