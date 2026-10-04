import test from 'node:test';
import assert from 'node:assert/strict';
import {validOriginalDecisionEvent,appendOriginalDecisionEvents} from '../original-decision-events.mjs';
import {buildRetainedDecisionPresentation} from '../decision-presentation.mjs';
const uuid='00000000-0000-0000-0000-000000000001';
const identity={debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,arenaEpoch:2,targetRevision:1};
function row(result=true){return {kind:'observation',lane:'AI_DECISION',...identity,epistemicStatus:'OBSERVED',completeness:{complete:true},
 source:{side:'SERVER'},scope:{kind:'ENTITY_UUID',entityUuid:uuid},observationId:'obs:ghast-reach:1',gameTime:100,
 payload:{schema:'kneekura.original-decision-event/v1',semantics:'ORIGINAL_INVOCATION_RETURN_ONLY',targetRevision:1,
  eventIndex:1,burstId:'burst:1:90',kind:'CONTROL_GHAST_REACH_RETURN',observerCostNanos:1,
  observerCostScope:'BUILD_AND_FIRST_BYTE_CHECK_EXCLUDES_FINAL_ENCODING_WRITER',data:{receiverUuid:uuid,
    controllerClass:'net.minecraft.world.entity.monster.Ghast$GhastMoveControl',direction:{x:0,y:0.6,z:0.8},
    stepCount:7,result,dispatchScope:'GHAST_ORIGINAL_CAN_REACH_RETURN',
    pathSemantics:'CUSTOM_STEERING_REACH_NOT_A_STAR',collisionLocationStatus:'NOT_EXPOSED',reasonStatus:'NOT_EXPOSED'}}};}
test('original true/false custom-flight reach is direct evaluation without candidates, path or inferred collision reason',()=>{
 for(const result of [true,false]){
  const r=row(result),before=JSON.stringify(r);assert.equal(validOriginalDecisionEvent(r),true);
  const stages={},capabilities={},timeline=[];appendOriginalDecisionEvents([r],stages,capabilities,timeline);
  assert.equal(stages.EVALUATION.facts[0].value.result,result);assert.equal(stages.EVALUATION.facts[0].epistemic_status,'DIRECT_OBSERVED');
  assert.equal(stages.EVALUATION.facts[0].value.pathSemantics,'CUSTOM_STEERING_REACH_NOT_A_STAR');
  assert.equal(capabilities.custom_flight_reach.status,'PARTIAL');assert.equal(stages.CANDIDATE,undefined);assert.equal(stages.SELECTION,undefined);
  assert.equal(stages.RESULT,undefined);assert.deepEqual(stages.EVALUATION.facts[0].source_observation_ids,[r.observationId]);
  assert.equal(JSON.stringify(r),before);
 }
 const emptyLoop=row();emptyLoop.payload.data.stepCount=0;emptyLoop.payload.data.direction={x:0,y:0,z:0};
 assert.equal(validOriginalDecisionEvent(emptyLoop),true,'short/zero length does not fabricate a collision-loop iteration');
});
test('wrong receiver/controller, malformed arguments and invented collision/path data are refused',()=>{
 for(const mutate of [d=>d.receiverUuid='00000000-0000-0000-0000-000000000002',d=>d.controllerClass='example.CustomFlight',
  d=>d.direction.x=NaN,d=>d.direction.collisionReason='INFERRED',d=>d.stepCount=-1,d=>d.stepCount=1.5,d=>d.stepCount=2147483648,d=>d.result='true',
  d=>d.dispatchScope='REPLAYED_REACH',d=>d.pathSemantics='A_STAR',d=>d.collisionLocationStatus='AVAILABLE',
  d=>d.collisionPosition={x:1,y:2,z:3},d=>d.reasonStatus='AVAILABLE',d=>d.finalDestination={x:1,y:2,z:3}]){
  const bad=row();mutate(bad.payload.data);assert.equal(validOriginalDecisionEvent(bad),false);
 }
});
test('retained packet keeps late-arm and other-identity reach absent without reconstructing a decision',()=>{
 const r=row(),before=JSON.stringify(r),request={startTick:90,endTick:110,maxSamples:8,maxNodes:8};
 const active=buildRetainedDecisionPresentation({observations:[r],subjectUuid:uuid,identity,request});
 assert.equal(active.overview.stages.EVALUATION.status,'AVAILABLE');assert.equal(active.layers.motion.status,'NOT_CAPTURED');
 assert.equal(active.overview.stages.SELECTION.status,'NOT_CAPTURED');assert.equal(active.layers.pathCache.status,'NOT_CAPTURED');
 const late=buildRetainedDecisionPresentation({observations:[r],subjectUuid:uuid,identity,request:{...request,startTick:101}});
 assert.equal(late.overview.stages.EVALUATION.status,'NOT_CAPTURED');assert.equal(late.overview.timeline.length,0);
 for(const mutate of [x=>x.runId='other',x=>x.arenaEpoch++,x=>x.payload.targetRevision++,x=>x.scope.entityUuid='00000000-0000-0000-0000-000000000002']){
  const other=row();mutate(other);
  const out=buildRetainedDecisionPresentation({observations:[other],subjectUuid:uuid,identity,request});
  assert.equal(out.overview.stages.EVALUATION.status,'NOT_CAPTURED');assert.equal(out.overview.timeline.length,0);
 }
 assert.equal(JSON.stringify(r),before);
});
