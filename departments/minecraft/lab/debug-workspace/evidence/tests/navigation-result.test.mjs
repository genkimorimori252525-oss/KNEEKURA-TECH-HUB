import test from 'node:test';
import assert from 'node:assert/strict';
import {normalizeDecisionBurst} from '../target-control.mjs';
import {decisionBurstFromArgs} from '../../decision-burst-cli.mjs';
import {validOriginalDecisionEvent,appendOriginalDecisionEvents} from '../original-decision-events.mjs';

const reference=n=>({status:'AVAILABLE',allocator:'SNAPSHOT_REFERENCE',targetRevision:7,token:'path:7:'+n});
const path=n=>({present:true,className:'net.minecraft.world.level.pathfinder.Path',identity:reference(n),cachedFields:{
  status:'AVAILABLE',className:'net.minecraft.world.level.pathfinder.Path',encoding:'TYPED_CACHED_MEMORY_V1',kind:'PATH',data:{
    instanceIdentity:reference(n),target:{status:'AVAILABLE',x:2,y:0,z:0},nextNodeIndex:0,canReach:false,
    distanceToTarget:{status:'AVAILABLE',value:1},nodeCount:1,truncated:false,nodesStatus:'AVAILABLE',
    nodes:[{status:'AVAILABLE',x:1,y:0,z:0,type:'WALKABLE',costMalus:0}],
    semantics:'CACHED_MEMORY_ROUTE_NOT_ADOPTION_ACTUAL_MOTION_OR_SEARCH_FRONTIER'}}});
const record=()=>({source:{side:'SERVER'},observationId:'obs:nav:1',gameTime:100,payload:{
  schema:'kneekura.original-decision-event/v1',semantics:'ORIGINAL_INVOCATION_RETURN_ONLY',targetRevision:7,
  burstId:'burst:7:100',eventIndex:1,kind:'NAVIGATION_MOVE_TO_RETURN',observerCostNanos:1,
  observerCostScope:'BUILD_AND_FIRST_BYTE_CHECK_EXCLUDES_FINAL_ENCODING_WRITER',data:{
    navigationClass:'Navigation',instanceIdentity:'component:7:1',instanceIdentityStatus:'AVAILABLE',result:true,
    requestedSpeed:0.75,cachedSpeed:0.75,requestedMatchesCachedPath:false,requestedPath:path(1),cachedPath:path(2),
    dispatchScope:'BASE_PATHNAVIGATION_NORMAL_RETURN_NOT_FINAL_CUSTOM_OVERRIDE',
    fieldScope:'BASE_NAVIGATION_AND_EXACT_PATH_CACHED_FIELDS_AFTER_RETURN_AND_CAPTURE_GATES',
    resultScope:'ORIGINAL_BASE_METHOD_BOOLEAN_NOT_ARRIVAL',referenceScope:'RAW_ARGUMENT_VS_CACHED_PATH_REFERENCE_EQUALITY',
    reasonStatus:'NOT_EXPOSED',arrivalStatus:'NOT_EXPOSED',searchRelationStatus:'NOT_EXPOSED'}}});

test('navigation result channel is explicit and defaults remain unchanged',()=>{
  assert.equal(decisionBurstFromArgs(['--decision-burst']).channels.includes('navigation_result'),false);
  assert.deepEqual(decisionBurstFromArgs(['--decision-burst','--decision-channels','navigation_result']).channels,['navigation_result']);
  assert.throws(()=>normalizeDecisionBurst({...decisionBurstFromArgs(['--decision-burst']),channels:['navigation_result','navigation_result']}));
});
test('original boolean and equal-route distinct references remain execution with unknown arrival',()=>{
  const r=record();assert.equal(validOriginalDecisionEvent(r),true);
  const stages={},capabilities={},timeline=[];appendOriginalDecisionEvents([r],stages,capabilities,timeline);
  assert.equal(stages.EXECUTION.facts[0].value.result,true);assert.equal(capabilities.navigation_move_to.status,'PARTIAL');
  for(const name of ['CANDIDATE','SELECTION','RESULT'])assert.equal(stages[name],undefined);
  assert.equal(timeline.length,1);
  const d=r.payload.data;d.requestedPath={present:false};d.cachedPath={present:false};d.result=false;d.requestedMatchesCachedPath=true;
  assert.equal(validOriginalDecisionEvent(r),true);
});
test('forged reference equality, complete fields, scopes, speeds and arrival are rejected',()=>{
  for(const mutate of [
    d=>d.instanceIdentity='component:8:1',d=>d.instanceIdentity='component:7:129',
    d=>d.requestedPath.identity.targetRevision=8,d=>d.requestedPath.identity.token='path:7:257',
    d=>d.requestedPath.identity.allocator='SEARCH_REFERENCE',d=>d.requestedPath.cachedFields.data.instanceIdentity.token='path:7:2',
    d=>d.requestedMatchesCachedPath=true,d=>d.cachedPath=structuredClone(d.requestedPath),
    d=>{d.requestedPath={present:false};d.requestedMatchesCachedPath=true;},d=>d.resultScope='ARRIVAL_SUCCESS',d=>d.arrivalStatus='AVAILABLE',
    d=>d.reasonStatus='AVAILABLE',d=>d.searchRelationStatus='AVAILABLE',d=>d.requestedSpeedStatus='NOT_EXPOSED',
    d=>delete d.cachedSpeed,d=>d.requestedPath.cachedFields.kind='WALK_TARGET',
    d=>d.requestedPath.cachedFields.data.nodes=[],d=>d.requestedPath.cachedFields.data.nodeCount=65,
    d=>d.requestedPath.cachedFields.data.nodes[0].status='PARTIAL',d=>d.requestedPath.cachedFields.data.target.status='NOT_EXPOSED']){
    const r=record();mutate(r.payload.data);assert.equal(validOriginalDecisionEvent(r),false);
  }
});
test('custom Path, nonfinite speed, bounded partial fields and capped identities remain unknown',()=>{
  const r=record(),d=r.payload.data;
  d.requestedPath.className='CustomPath';d.requestedPath.cachedFields={className:'CustomPath',status:'NOT_EXPOSED'};
  delete d.requestedSpeed;d.requestedSpeedStatus='NOT_EXPOSED';delete d.cachedSpeed;d.cachedSpeedStatus='NOT_EXPOSED';
  delete d.instanceIdentity;d.instanceIdentityStatus='NOT_EXPOSED';assert.equal(validOriginalDecisionEvent(r),true);
  const p=d.cachedPath,unknown={status:'NOT_EXPOSED',allocator:'SNAPSHOT_REFERENCE',targetRevision:7,detail:'REFERENCE_LIMIT'};
  p.identity=unknown;p.cachedFields.data.instanceIdentity=structuredClone(unknown);p.cachedFields.status='PARTIAL';
  assert.equal(validOriginalDecisionEvent(r),true);
  p.cachedFields.status='AVAILABLE';assert.equal(validOriginalDecisionEvent(r),false);
  p.cachedFields.status='PARTIAL';p.identity.token='path:7:256';assert.equal(validOriginalDecisionEvent(r),false);
});
