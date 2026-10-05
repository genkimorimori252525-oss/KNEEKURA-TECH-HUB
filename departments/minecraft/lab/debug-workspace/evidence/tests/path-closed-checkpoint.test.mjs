import test from 'node:test';
import assert from 'node:assert/strict';
import {validOriginalDecisionEvent,appendOriginalDecisionEvents} from '../original-decision-events.mjs';
import {queryDecisionDrilldown} from '../decision-drilldown.mjs';
import {observeDebugWorkspaceDecision} from '../debug-workspace-decision-adapter.mjs';
const uuid='00000000-0000-0000-0000-000000000001';
const identity={debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,arenaEpoch:2,targetRevision:1};
function row(index=2){
 return {kind:'observation',lane:'AI_DECISION',...identity,epistemicStatus:'OBSERVED',completeness:{complete:true},
  source:{side:'SERVER'},scope:{kind:'ENTITY_UUID',entityUuid:uuid},observationId:'obs:closed:'+index,gameTime:100+index,
  payload:{schema:'kneekura.original-decision-event/v1',semantics:'ORIGINAL_FIELD_WRITE_CHECKPOINT_ONLY',targetRevision:1,
   eventIndex:index,burstId:'burst:1:90',kind:'PATH_NODE_CLOSED_CHECKPOINT',observerCostNanos:1,
   observerCostScope:'BUILD_AND_FIRST_BYTE_CHECK_EXCLUDES_FINAL_ENCODING_WRITER',data:{searchId:'search:1:1',
    priorPopEventIndex:1,nodeRole:'PRECEDING_ORIGINAL_POP_RETURN_REFERENCE',
    node:{status:'AVAILABLE',data:{className:'net.minecraft.world.level.pathfinder.Node',x:0,y:64,z:0,pathType:'WALKABLE',
     g:5,h:3,f:8,costMalus:1,walkedDistance:4,openAtCheckpoint:false,closedAtCheckpoint:true}},
    nodeIdentity:{status:'AVAILABLE',id:'search:1:1:node:1'},maxNodes:2,
    phase:'AFTER_ORIGINAL_CALLER_CLOSED_FIELD_WRITE',dispatchScope:'ORIGINAL_PATHFINDER_INNER_CLOSED_FIELD_WRITE',
    subjectRelationScope:'SELECTED_OUTER_FIND_PATH_INVOCATION',referenceScope:'RETAINED_ORIGINAL_POP_RETURN_REFERENCE',
    neighborPopulationStatus:'NOT_EXPOSED',rejectionReasonStatus:'NOT_EXPOSED',finalPathCostStatus:'NOT_EXPOSED'}}};
}
test('closed checkpoint is algorithm state with its own boundary, never an invocation return or selected path',()=>{
 const r=row(),before=JSON.stringify(r);assert.equal(validOriginalDecisionEvent(r),true);
 const stages={},capabilities={},timeline=[];appendOriginalDecisionEvents([r],stages,capabilities,timeline);
 const fact=stages.EVALUATION.facts[0];assert.equal(fact.epistemic_status,'INSTRUMENTED_ALGORITHM_STATE');
 assert.equal(fact.causal_relation,'ALGORITHM_TRACE_RELATION');assert.deepEqual(fact.source_observation_ids,[r.observationId]);
 assert.equal(capabilities.path_closed_nodes.status,'PARTIAL');assert.equal(stages.SELECTION,undefined);assert.equal(stages.RESULT,undefined);
 const q=queryDecisionDrilldown({observations:[r],subjectUuid:uuid,identity,
  request:{channel:'path_closed_nodes',startTick:90,endTick:110,limit:10,maxNodes:2}});
 assert.equal(q.items.length,1);assert.equal(q.items[0].epistemic_status,'INSTRUMENTED_ALGORITHM_STATE');
 assert.equal(q.items[0].causal_relation,'ALGORITHM_TRACE_RELATION');assert.equal(q.items[0].reasonKnown,false);
 assert.equal(q.items[0].data.priorPopEventIndex,1);assert.deepEqual(q.items[0].source_observation_ids,[r.observationId]);
 const packet=observeDebugWorkspaceDecision({observations:[r],subjectUuid:uuid,identity,tick:110});
 assert.ok(packet.available_drilldowns.includes('path_closed_nodes'));
 assert.equal(packet.capabilities.path_closed_nodes.status,'PARTIAL');
 // A retained pop record may be absent: its index is a producer reference, not an invented observation ID.
 assert.equal(JSON.stringify(r),before);
});
test('checkpoint validates phase-specific flags, bounded identities and unknown costs without claiming closed always stays true',()=>{
 const unknown=row();unknown.payload.data.nodeIdentity={status:'NOT_EXPOSED',detail:'NODE_IDENTITY_LIMIT'};
 unknown.payload.data.node.data.closedAtCheckpoint=false;assert.equal(validOriginalDecisionEvent(unknown),true);
 delete unknown.payload.data.node.data.g;unknown.payload.data.node.data.gStatus='NOT_EXPOSED';assert.equal(validOriginalDecisionEvent(unknown),true);
 for(const mutate of [r=>r.payload.semantics='ORIGINAL_INVOCATION_RETURN_ONLY',r=>r.payload.kind='PATH_HEAP_OPERATION_RETURN',
  r=>r.payload.data.priorPopEventIndex=0,r=>r.payload.data.priorPopEventIndex=2,r=>r.payload.data.priorPopEventIndex=1.5,
  r=>r.payload.data.node.data.closedAtReturn=true,r=>delete r.payload.data.node.data.closedAtCheckpoint,
  r=>r.payload.data.node={status:'NOT_EXPOSED',detail:'NULL_NODE'},r=>r.payload.data.nodeIdentity.id='search:1:2:node:1',
  r=>r.payload.data.nodeIdentity.id='search:1:1:node:3',r=>r.payload.data.nodeIdentity.detail='NULL_NODE',
  r=>r.payload.data.maxNodes=65,r=>r.payload.data.phase='AFTER_ORIGINAL_POP_BEFORE_CALLER_CLOSE',
  r=>r.payload.data.referenceScope='COORDINATE_MATCH',r=>r.payload.data.rejectionReasonStatus='AVAILABLE',
  r=>r.payload.data.finalPathCost=8,r=>r.payload.data.node.data.g=NaN]){
  const bad=row();mutate(bad);assert.equal(validOriginalDecisionEvent(bad),false);
 }
});
test('checkpoint query fences context and revision and does not join equal coordinates or missing pops',()=>{
 const first=row(),second=row(3);second.payload.data.nodeIdentity.id='search:1:1:node:2';
 const foreign=row(4);foreign.arenaEpoch++;const stale=row(5);stale.payload.targetRevision=2;
 const rows=[first,second,foreign,stale],before=JSON.stringify(rows);
 const q=queryDecisionDrilldown({observations:rows,subjectUuid:uuid,identity,
  request:{channel:'path_closed_nodes',startTick:90,endTick:110,limit:1,maxNodes:2}});
 assert.equal(q.totalMatchingItems,2);assert.equal(q.truncated,true);assert.equal(q.items[0].data.nodeIdentity.id,'search:1:1:node:2');
 assert.deepEqual(q.items[0].source_observation_ids,[second.observationId]);assert.equal(JSON.stringify(rows),before);
});
