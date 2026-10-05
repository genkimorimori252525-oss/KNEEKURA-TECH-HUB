import test from 'node:test';
import assert from 'node:assert/strict';
import {createDecisionObservation} from '../decision-observation.mjs';
import {buildDecisionOverviewPacket,buildRetainedDecisionPresentation} from '../decision-presentation.mjs';
import {renderDecisionPresentationHtml,writeDecisionPresentationArtifact} from '../decision-view.mjs';
import {mkdtemp,mkdir,readFile,rm} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
const uuid='00000000-0000-0000-0000-000000000001';
const identity={debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,arenaEpoch:0,targetRevision:1};
const request={startTick:100,endTick:120};
const row=(lane,tick,payload,id=lane+tick)=>({kind:'observation',lane,gameTime:tick,observationId:'obs:'+id,...identity,
  scope:{kind:'ENTITY_UUID',entityUuid:uuid},source:{side:'SERVER'},epistemicStatus:'OBSERVED',completeness:{complete:true},
  payload:{targetRevision:1,...payload}});
function ground() {
  return row('AI_DECISION',100,{schema:'kneekura.terrain-ground-query/v1',semantics:'OBSERVER_QUERIED_GROUND_NOT_PATHFINDER_EVALUATION',
    sampleTick:100,observerCostNanos:1,observerCostScope:'GROUND_CAPTURE_ONLY_EXCLUDES_ENCODING_WRITER_VIEWER',data:{
      radius:0,requestedCellCount:1,classificationScope:'STATIC_GROUND_NOT_SELECTED_EVALUATOR_ADMISSION',
      effectiveMalusStatus:'NOT_EXPOSED',observerDeadlineScope:'CHECKED_BETWEEN_CELLS_CANNOT_PREEMPT_ONE_CLASSIFIER_CALL',
      dimension:'minecraft:overworld',centerX:0,centerY:64,centerZ:0,
      chunkAccessScope:'LOADED_NONBLOCKING_MAY_WARM_LOOKUP_CACHE_AND_PROFILER',status:'AVAILABLE',truncated:false,cells:[{
        x:0,y:64,z:0,status:'AVAILABLE',pathType:'WALKABLE',defaultTypeMalus:0,selectedMobOverrideStatus:'NOT_PRESENT',
        observationRole:'OBSERVER_QUERIED_GROUND_ONLY',effectiveMalusStatus:'NOT_EXPOSED',evaluatedByPathfinderStatus:'NOT_CAPTURED'}]}});
}
test('overview bounds repeated facts/value/timeline while preserving counts, references and unavailable stages',()=>{
  const observation=createDecisionObservation({subject:{id:uuid},adapter:{id:'test:bounded',version:'1'},
    stages:{EXECUTION:{facts:Array.from({length:100},(_,i)=>({key:'control',value:{i,large:'x'.repeat(10000)},
      epistemic_status:'DIRECT_OBSERVED',causal_relation:'DIRECT_RUNTIME_RELATION',source_observation_ids:['obs:'+i]}))}},
    timeline:Array.from({length:100},(_,i)=>({tick:i,stage:'EXECUTION',kind:'CONTROL_RETURN',
      epistemic_status:'DIRECT_OBSERVED',causal_relation:'DIRECT_RUNTIME_RELATION',source_observation_ids:['obs:'+i]}))});
  const before=JSON.stringify(observation),packet=buildDecisionOverviewPacket(observation,{timelineLimit:4,factLimit:2});
  assert.equal(packet.stages.EXECUTION.totalObservedFacts,100);
  assert.equal(packet.stages.EXECUTION.facts.length,1);
  assert.deepEqual(packet.stages.EXECUTION.facts[0].source_observation_ids,['obs:99']);
  assert.equal(packet.stages.EXECUTION.facts[0].valuePresentationStatus,'OMITTED_BYTE_BUDGET');
  assert.equal(packet.stages.SELECTION.status,'NOT_CAPTURED');
  assert.equal(packet.timeline.length,4);assert.equal(packet.timelineTruncated,true);
  assert.equal(JSON.stringify(observation),before);
});
test('presentation shares exact retained Motion samples, separates observer terrain and leaves drawing OFF',()=>{
  const observations=[ground(),row('SERVER_ENTITY_STATE',100,{x:0,y:64,z:0}),row('SERVER_ENTITY_STATE',105,{x:1,y:64,z:0})];
  const before=JSON.stringify(observations),out=buildRetainedDecisionPresentation({observations,subjectUuid:uuid,identity,request});
  assert.equal(out.layers.motion.enabledByDefault,false);assert.equal(out.layers.terrain.enabledByDefault,false);
  assert.equal(out.layers.motion.trace.samples.length,2);assert.equal(out.layers.motion.trace.segments.length,1);
  assert.equal(out.layers.terrain.cells[0].observationRole,'OBSERVER_QUERIED_GROUND_ONLY');
  assert.equal(out.layers.terrain.cells[0].effectiveMalusStatus,'NOT_EXPOSED');
  assert.equal(out.layers.pathCache.status,'NOT_CAPTURED');
  assert.equal(out.semantics.temporalAdjacencyProvesCausality,false);
  assert.equal(out.overview.stages.EVALUATION.status,'NOT_CAPTURED');assert.equal(JSON.stringify(observations),before);
});
test('missing positions and derived distance threshold break the trace without fabricated teleport events',()=>{
  const observations=[row('SERVER_ENTITY_STATE',100,{x:0,y:64,z:0}),row('SERVER_ENTITY_STATE',105,{alive:false}),
    row('SERVER_ENTITY_STATE',110,{x:1,y:64,z:0}),row('SERVER_ENTITY_STATE',115,{x:100,y:64,z:0})];
  const out=buildRetainedDecisionPresentation({observations,subjectUuid:uuid,identity,request});
  assert.equal(out.layers.motion.trace.segments.length,0);
  assert.deepEqual(out.layers.motion.trace.gaps.map(g=>g.kind),['MISSING_RETAINED_POSITION','DERIVED_DISTANCE_THRESHOLD_BREAK']);
  assert.equal(out.layers.motion.missingPositionRows,1);assert.equal(out.semantics.distanceBreakProvesTeleport,false);
});
test('presentation excludes wrong source/UUID/revision/run and requires bounded complete identity',()=>{
  const seed=row('SERVER_ENTITY_STATE',100,{x:0,y:64,z:0});
  for(const change of [r=>r.source.side='CLIENT',r=>r.scope.entityUuid+='x',r=>r.payload.targetRevision=2,r=>r.runId='other']) {
    const bad=structuredClone(seed);change(bad);
    assert.equal(buildRetainedDecisionPresentation({observations:[bad],subjectUuid:uuid,identity,request}).layers.motion.trace.samples.length,0);
  }
  assert.throws(()=>buildRetainedDecisionPresentation({observations:[seed],subjectUuid:uuid,identity:{},request}));
  assert.throws(()=>buildRetainedDecisionPresentation({observations:[seed],subjectUuid:uuid,identity,request:{...request,worldQuery:true}}));
  assert.throws(()=>buildRetainedDecisionPresentation({observations:[seed],subjectUuid:uuid,identity,request:{startTick:0,endTick:10001}}));
});
test('standalone view safely embeds evidence and starts with every spatial layer disabled',()=>{
  const out=buildRetainedDecisionPresentation({observations:[row('SERVER_ENTITY_STATE',100,{x:0,y:64,z:0})],subjectUuid:uuid,identity,request});
  out.overview.stages.STATE.facts[0].value='</script><script>window.pwned=true</script>';
  const html=renderDecisionPresentationHtml(out);
  assert.ok(!html.includes('</script><script>window.pwned=true</script>'));
  assert.ok(html.includes('\\u003c/script>'));
  assert.ok(html.includes('Content-Security-Policy'));
  assert.equal((html.match(/type="checkbox"/g)??[]).length,Object.keys(out.layers).length);
  assert.ok(!html.includes(' checked'));assert.ok(!html.includes('innerHTML'));
  assert.ok(!html.includes('fetch('));assert.ok(!html.includes('eval('));
});
test('spatial presentation keeps path cache and declared navigation separate with original source IDs',()=>{
  const path=row('AI_DECISION',101,{schema:'kneekura.original-decision-event/v1',semantics:'ORIGINAL_INVOCATION_RETURN_ONLY',
    kind:'PATH_SEARCH_STATE',burstId:'burst:1:90',eventIndex:1,observerCostNanos:1,
    observerCostScope:'BUILD_AND_FIRST_BYTE_CHECK_EXCLUDES_FINAL_ENCODING_WRITER',data:{searchId:'search:1:1',frontier:{status:'AVAILABLE',data:{
      nodes:[{x:0,y:64,z:0,g:0,h:1,f:1,costMalus:0,walkedDistance:0,pathType:'WALKABLE',openAtReturn:true,
        closedAtReturn:false,cacheRole:'OPEN_AT_RETURN'}],cacheNodeCount:1,truncated:false,
      phase:'OUTER_BEFORE_DONE_AFTER_INNER_RETURN',neighborEvaluationTraceStatus:'NOT_EXPOSED',rejectionReasonStatus:'NOT_EXPOSED'}}}});
  const nav=row('AI_DECISION',102,{schema:'kneekura.vanilla-decision-snapshot/v1',semantics:'MOB_COMPONENT_SNAPSHOT_ONLY',
    sections:Object.fromEntries(['goal_scheduler','brain_memory','brain_activities','navigation_path','movement_control'].map(k=>[k,{status:'NOT_EXPOSED'}]))});
  nav.payload.sections.navigation_path={status:'AVAILABLE',data:{pathPresent:true,pathSemantics:'DECLARED_ROUTE_NOT_ACTUAL_MOTION_OR_FRONTIER',
    entries:[{index:0,x:1,y:64,z:1}],truncated:false}};
  const out=buildRetainedDecisionPresentation({observations:[path,nav],subjectUuid:uuid,identity,request});
  assert.equal(out.layers.pathCache.nodes[0].cacheRole,'OPEN_AT_RETURN');
  assert.equal(out.layers.pathCache.data.resultStatus,'NOT_CAPTURED');
  assert.deepEqual(out.layers.declaredNavigation.source_observation_ids,[nav.observationId]);
  assert.equal(out.layers.declaredNavigation.nodes[0].x,1);
  assert.equal(out.semantics.pathCacheContainsAllNeighbors,false);
});
test('spatial overlays refuse dimension boundaries and duplicate motion ticks rather than join them',()=>{
  const a=row('SERVER_ENTITY_STATE',100,{x:0,y:64,z:0,dimension:'minecraft:overworld'});
  const b=row('SERVER_ENTITY_STATE',105,{x:1,y:64,z:0,dimension:'minecraft:the_nether'});
  assert.throws(()=>buildRetainedDecisionPresentation({observations:[a,b],subjectUuid:uuid,identity,request}),/DIMENSION/);
  const duplicate={...a,observationId:'obs:second'};
  assert.throws(()=>buildRetainedDecisionPresentation({observations:[a,duplicate],subjectUuid:uuid,identity,request}),/duplicate motion/);
  const terrain=ground();terrain.payload.data.dimension='minecraft:the_nether';
  assert.throws(()=>buildRetainedDecisionPresentation({observations:[a,terrain],subjectUuid:uuid,identity,request}),/DIMENSION/);
});
test('derived view export refuses run-directory writes and existing files',async()=>{
  const root=await mkdtemp(path.join(os.tmpdir(),'kneekura-decision-view-'));
  try {
    const run=path.join(root,'run');await mkdir(run);
    const out=buildRetainedDecisionPresentation({observations:[],subjectUuid:uuid,identity,request});
    await assert.rejects(writeDecisionPresentationArtifact(out,path.join(run,'new.html'),run),/OUTSIDE_RETAINED_RUN/);
    const file=path.join(root,'view.html');await writeDecisionPresentationArtifact(out,file,run);
    const before=await readFile(file,'utf8');
    await assert.rejects(writeDecisionPresentationArtifact(out,file,run),{code:'EEXIST'});
    assert.equal(await readFile(file,'utf8'),before);
  }finally {await rm(root,{recursive:true,force:true});}
});
