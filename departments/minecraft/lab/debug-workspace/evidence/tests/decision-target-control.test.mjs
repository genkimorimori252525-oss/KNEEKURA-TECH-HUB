import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {setTargetControl,clearTargetControl} from '../target-control.mjs';

test('Decision snapshot control defaults OFF and explicit arming is revision fenced',async t=>{
  const runDir=await mkdtemp(path.join(tmpdir(),'kneekura-decision-target-'));
  t.after(()=>rm(runDir,{recursive:true,force:true}));
  const current={runDir,debugSessionId:'s',runId:'r',runSnapshotId:'snapshot',processEpoch:1};
  const uuid='00000000-0000-0000-0000-000000000001';
  assert.equal((await setTargetControl(current,uuid)).decisionSnapshot,false);
  const armed=await setTargetControl(current,uuid,{decisionSnapshot:true});
  assert.equal(armed.decisionSnapshot,true);
  assert.equal(armed.revision,2);
  assert.equal((await clearTargetControl(current)).decisionSnapshot,false);
  await assert.rejects(setTargetControl(current,uuid,{decisionSnapshot:'true'}),/decisionSnapshot must be boolean/);
  await assert.rejects(setTargetControl(current,null,{decisionSnapshot:true}),/requires a target/);
});

test('Decision burst is explicit, finite, channel-scoped and reset by every selection',async t=>{
  const runDir=await mkdtemp(path.join(tmpdir(),'kneekura-decision-burst-'));
  t.after(()=>rm(runDir,{recursive:true,force:true}));
  const current={runDir,debugSessionId:'s',runId:'r',runSnapshotId:'snapshot',processEpoch:1,decisionHooksEnabled:true};
  const uuid='00000000-0000-0000-0000-000000000001';
  const burst={ticks:50,maxEvents:128,maxBytes:65536,maxNodes:16,channels:['goal','path']};
  assert.deepEqual((await setTargetControl(current,uuid,{decisionBurst:burst})).decisionBurst,burst);
  assert.equal((await setTargetControl(current,uuid)).decisionBurst,null);
  assert.equal((await clearTargetControl(current)).decisionBurst,null);
  await assert.rejects(setTargetControl({...current,decisionHooksEnabled:false},uuid,{decisionBurst:burst}),/DECISION_HOOKS_NOT_ENABLED/);
  await assert.rejects(setTargetControl(current,null,{decisionBurst:burst}),/requires a target/);
  for(const invalid of [{...burst,ticks:201},{...burst,maxEvents:257},{...burst,maxBytes:524289},{...burst,maxNodes:65},
    {...burst,ticks:'50'},{...burst,ticks:0},{...burst,channels:['goal','goal']},{...burst,channels:['unknown']},{...burst,unknown:1}]){
    await assert.rejects(setTargetControl(current,uuid,{decisionBurst:invalid}),/Invalid decisionBurst/);
  }
});
test('projectile-only burst is explicit and finite without arming movement controls',async t=>{
  const runDir=await mkdtemp(path.join(tmpdir(),'kneekura-projectile-target-'));
  t.after(()=>rm(runDir,{recursive:true,force:true}));
  const current={runDir,debugSessionId:'s',runId:'r',runSnapshotId:'snapshot',processEpoch:1,decisionHooksEnabled:true};
  const uuid='00000000-0000-0000-0000-000000000001';
  const burst={ticks:200,maxEvents:256,maxBytes:524288,maxNodes:8,channels:['projectile']};
  const armed=await setTargetControl(current,uuid,{decisionBurst:burst});
  assert.deepEqual(armed.decisionBurst,burst);assert.equal(armed.decisionSnapshot,false);
  assert.equal((await setTargetControl(current,uuid)).decisionBurst,null);
  const all={...burst,channels:['goal','brain','path','control','malus','sensor','mod','projectile']};
  assert.deepEqual((await setTargetControl(current,uuid,{decisionBurst:all})).decisionBurst,all);
  for(const channels of [['projectile','projectile'],['projectile','unknown']])await assert.rejects(setTargetControl(current,uuid,{decisionBurst:{...burst,channels}}),/Invalid decisionBurst/);
});
