import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {setTargetControl,clearTargetControl} from '../target-control.mjs';
import {terrainQueryFromArgs} from '../../terrain-query-cli.mjs';

test('terrain query is explicitly armed, bounded and independent of decision hooks',async t=>{
  const runDir=await mkdtemp(path.join(tmpdir(),'kneekura-terrain-'));
  t.after(()=>rm(runDir,{recursive:true,force:true}));
  const current={runDir,debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,decisionHooksEnabled:false};
  const uuid='00000000-0000-0000-0000-000000000001';
  const query={radius:0,maxCells:1,maxMillis:10};
  assert.equal((await setTargetControl(current,uuid)).decisionTerrain,null);
  assert.deepEqual((await setTargetControl(current,uuid,{decisionTerrain:query})).decisionTerrain,query);
  assert.equal((await setTargetControl(current,uuid)).decisionTerrain,null);
  assert.equal((await clearTargetControl(current)).decisionTerrain,null);
  await assert.rejects(setTargetControl(current,null,{decisionTerrain:query}),/requires a target/);
  for(const invalid of [{...query,radius:4},{...query,radius:-1},{...query,maxCells:50},{...query,maxMillis:51},
    {...query,maxCells:0},{...query,radius:'0'},{...query,maxMillis:NaN},{...query,worldLoad:true}]) {
    await assert.rejects(setTargetControl(current,uuid,{decisionTerrain:invalid}),/Invalid decisionTerrain/);
  }
});

test('terrain CLI leaves default OFF and refuses unarmed, missing, repeated and invalid limits',()=>{
  assert.equal(terrainQueryFromArgs([]),null);
  assert.deepEqual(terrainQueryFromArgs(['--terrain-radius','0']),{radius:0,maxCells:49,maxMillis:10});
  assert.deepEqual(terrainQueryFromArgs(['--terrain-radius','3','--terrain-cells','2','--terrain-millis','1']),
    {radius:3,maxCells:2,maxMillis:1});
  for(const args of [['--terrain-cells','2'],['--terrain-radius'],['--terrain-radius','4'],
    ['--terrain-radius','NaN'],['--terrain-radius','0','--terrain-radius','1'],
    ['--terrain-radius','0','--terrain-millis','51'],['--terrain-radius','0','--terrain-cells','']]) {
    assert.throws(()=>terrainQueryFromArgs(args));
  }
});
