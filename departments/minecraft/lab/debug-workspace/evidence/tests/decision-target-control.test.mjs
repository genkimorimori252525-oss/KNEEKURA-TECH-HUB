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
