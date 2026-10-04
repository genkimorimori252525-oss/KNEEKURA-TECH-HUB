import test from 'node:test';
import assert from 'node:assert/strict';
import {validTerrainGroundQuery} from '../terrain-ground-query.mjs';
import {queryDecisionDrilldown} from '../decision-drilldown.mjs';
import {observeDebugWorkspaceDecision} from '../debug-workspace-decision-adapter.mjs';

const uuid='00000000-0000-0000-0000-000000000001';
const identity={debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,arenaEpoch:2,targetRevision:1};
function row() {
  return {kind:'observation',lane:'AI_DECISION',observationId:'obs:terrain:100',...identity,
    scope:{kind:'ENTITY_UUID',entityUuid:uuid},epistemicStatus:'OBSERVED',completeness:{complete:true},
    gameTime:100,writerSeq:10,source:{side:'SERVER',method:'fixture'},payload:{
      schema:'kneekura.terrain-ground-query/v1',semantics:'OBSERVER_QUERIED_GROUND_NOT_PATHFINDER_EVALUATION',
      targetRevision:1,sampleTick:100,observerCostNanos:10,observerCostScope:'GROUND_CAPTURE_ONLY_EXCLUDES_ENCODING_WRITER_VIEWER',
      data:{radius:0,requestedCellCount:1,classificationScope:'STATIC_GROUND_NOT_SELECTED_EVALUATOR_ADMISSION',
        effectiveMalusStatus:'NOT_EXPOSED',observerDeadlineScope:'CHECKED_BETWEEN_CELLS_CANNOT_PREEMPT_ONE_CLASSIFIER_CALL',
        dimension:'minecraft:overworld',centerX:0,centerY:64,centerZ:0,
        chunkAccessScope:'LOADED_NONBLOCKING_MAY_WARM_LOOKUP_CACHE_AND_PROFILER',status:'AVAILABLE',truncated:false,
        cells:[{x:0,y:64,z:0,status:'AVAILABLE',pathType:'WALKABLE',defaultTypeMalus:0,
          selectedMobOverrideStatus:'AVAILABLE',selectedMobOverride:2.5,
          observationRole:'OBSERVER_QUERIED_GROUND_ONLY',effectiveMalusStatus:'NOT_EXPOSED',evaluatedByPathfinderStatus:'NOT_CAPTURED'}]}}};
}
const query=observations=>queryDecisionDrilldown({observations,subjectUuid:uuid,identity,
  request:{channel:'terrain_ground',startTick:99,endTick:101,limit:2,maxNodes:1}});

test('terrain retained query remains distinct from original path/malus evaluations',()=>{
  const record=row(),before=JSON.stringify(record);
  assert.equal(validTerrainGroundQuery(record),true);
  const out=query([record]);assert.equal(out.items.length,1);
  assert.deepEqual(out.items[0].source_observation_ids,['obs:terrain:100']);
  assert.equal(out.items[0].data.cells[0].selectedMobOverride,2.5);
  assert.equal(out.items[0].data.cells[0].effectiveMalusStatus,'NOT_EXPOSED');
  assert.equal(out.items[0].causal_relation,'UNKNOWN_CAUSALITY');
  assert.equal(out.semantics.queriedTerrainImpliesPathfinderEvaluation,false);
  assert.equal(JSON.stringify(record),before);
});
test('Decision adapter exposes terrain as observer query state without candidate/evaluation claims',()=>{
  const out=observeDebugWorkspaceDecision({observations:[row()],subjectUuid:uuid,identity});
  assert.equal(out.capabilities.terrain_ground.status,'AVAILABLE');
  assert.equal(out.stages.STATE.facts[0].key,'terrain_ground');
  assert.equal(out.stages.STATE.facts[0].causal_relation,'UNKNOWN_CAUSALITY');
  assert.equal(out.stages.EVALUATION,undefined);assert.equal(out.stages.CANDIDATE,undefined);
  assert.deepEqual(out.available_drilldowns,['terrain_ground']);
});
test('unavailable and time-truncated ground is retained without invented air/effective malus',()=>{
  const record=row();record.payload.data.status='PARTIAL';record.payload.data.cells[0]={x:0,y:64,z:0,
    status:'NOT_EXPOSED',detail:'IOException',observationRole:'OBSERVER_QUERIED_GROUND_ONLY',
    effectiveMalusStatus:'NOT_EXPOSED',evaluatedByPathfinderStatus:'NOT_CAPTURED'};
  assert.equal(validTerrainGroundQuery(record),true);
  assert.equal(query([record]).items[0].data.cells[0].pathType,undefined);
  record.payload.data.cells=[];record.payload.data.truncated=true;
  assert.equal(validTerrainGroundQuery(record),true);
});
test('terrain rejects substituted effective values, fake evaluation, out-of-range and mismatched time',()=>{
  for(const change of [r=>r.payload.data.cells[0].effectiveMalus=2.5,
    r=>r.payload.data.cells[0].evaluatedByPathfinderStatus='AVAILABLE',r=>r.payload.data.cells[0].x=1,
    r=>r.payload.sampleTick=99,r=>r.payload.data.cells[0].defaultTypeMalus=NaN,
    r=>r.payload.data.cells.push({...r.payload.data.cells[0]}),r=>r.payload.data.status='PARTIAL',
    r=>r.source.side='CLIENT',r=>r.payload.observerCostNanos=-1]) {
    const record=row();change(record);assert.equal(validTerrainGroundQuery(record),false);
    assert.equal(query([record]).items.length,0);
  }
});
test('terrain query excludes foreign run, Arena, selection and UUID',()=>{
  for(const change of [r=>r.runId='other',r=>r.arenaEpoch=3,r=>r.payload.targetRevision=2,
    r=>r.scope.entityUuid='00000000-0000-0000-0000-000000000002']) {
    const record=row();change(record);assert.equal(query([record]).items.length,0);
  }
});
