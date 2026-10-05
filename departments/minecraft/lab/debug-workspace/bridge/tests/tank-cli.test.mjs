import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,writeFile,readFile,rm} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {sha256,stableJson} from '../json.mjs';
import {readTankContext,prepareTankResourceFile} from '../../tank-cli.mjs';

test('retained-only CLI context remains UNKNOWN and has no dispatch side effects',async()=>{
  const current={debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,live:false};
  const profile={kind:'OBSERVE_GRID',grid:true,brightness:false,motion:false,decisionChannels:[]};
  const timeBudget={experimentMs:1000,finalizationMs:1000,cleanupMs:1000,marginMs:1000};
  const result=await readTankContext({current,observations:[],arenaEpoch:0,profile,timeBudget});
  assert.equal(result.preflight.status,'UNKNOWN');assert.equal(result.preflight.leaseCheck.remainingMs,null);
  assert.equal(result.status.presentation.pixelEvidence.status,'NOT_CAPTURED');
  assert.equal(result.preflight.semantics.grantsAuthority,false);
});
test('resource CLI prepares a new bounded ZIP and refuses to overwrite an artifact',async t=>{
  const root=await mkdtemp(path.join(os.tmpdir(),'tank-cli-test-'));t.after(()=>rm(root,{recursive:true,force:true}));
  const recipe={v:1,kind:'tank_recipe',dimension:'minecraft:overworld',origin:{x:0,y:64,z:0},dimensions:{width:16,height:8,depth:16},presentation:{gridSpacing:1,mode:'NATIVE'}};
  const saved={status:'GEOMETRY_VERIFIED',recipe,recipeHash:sha256(stableJson(recipe)),displayMode:'NATIVE'};
  const savedFile=path.join(root,'marker.json'),profileFile=path.join(root,'profile.json'),output=path.join(root,'resource.zip');
  await writeFile(savedFile,JSON.stringify(saved));
  await writeFile(profileFile,JSON.stringify({kind:'OBSERVE_GRID',grid:true,brightness:false,motion:false,decisionChannels:[]}));
  const result=await prepareTankResourceFile({savedFile,profileFile,output});
  assert.equal(result.requiresNewRegistration,true);assert.equal(result.grantsAuthority,false);
  const before=await readFile(output);assert.equal(before.readUInt32LE(0),0x04034b50);
  await assert.rejects(prepareTankResourceFile({savedFile,profileFile,output}),{code:'EEXIST'});
  assert.deepEqual(await readFile(output),before);assert.deepEqual(JSON.parse(await readFile(savedFile,'utf8')),saved);
});
