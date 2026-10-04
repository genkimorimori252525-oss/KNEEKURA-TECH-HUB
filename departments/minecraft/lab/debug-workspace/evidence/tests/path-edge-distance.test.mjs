import test from 'node:test';
import assert from 'node:assert/strict';
import {decisionBurstFromArgs} from '../../decision-burst-cli.mjs';
import {validOriginalDecisionEvent,appendOriginalDecisionEvents} from '../original-decision-events.mjs';
import {queryDecisionDrilldown} from '../decision-drilldown.mjs';
import {observeDebugWorkspaceDecision} from '../debug-workspace-decision-adapter.mjs';
const uuid='00000000-0000-0000-0000-000000000001';
const identity={debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,arenaEpoch:2,targetRevision:1};
const node=()=>({status:'AVAILABLE',data:{className:'custom.Node',x:0,y:64,z:0,pathType:'WALKABLE',
 g:8,h:2,f:100,costMalus:1,walkedDistance:4,openAtReturn:true,closedAtReturn:false}});
function row(index=1){return {kind:'observation',lane:'AI_DECISION',...identity,source:{side:'SERVER'},
 scope:{kind:'ENTITY_UUID',entityUuid:uuid},epistemicStatus:'OBSERVED',completeness:{complete:true},gameTime:100+index,
 observationId:'obs:edge-distance:'+index,payload:{schema:'kneekura.original-decision-event/v1',semantics:'ORIGINAL_INVOCATION_RETURN_ONLY',
 targetRevision:1,eventIndex:index,burstId:'burst:1:90',kind:'PATH_EDGE_DISTANCE_RETURN',observerCostNanos:1,
 observerCostScope:'BUILD_AND_FIRST_BYTE_CHECK_EXCLUDES_FINAL_ENCODING_WRITER',data:{searchId:'search:1:1',maxNodes:2,
 receiverClass:'custom.PathFinder',receiverScope:'ORIGINAL_CALLER_THIS',returnedDistance:31.25,returnedDistanceScope:'ORIGINAL_VIRTUAL_CALL_RETURN',
 fromNode:node(),fromIdentity:{status:'AVAILABLE',id:'search:1:1:node:1'},toNode:node(),toIdentity:{status:'AVAILABLE',id:'search:1:1:node:2'},
 phase:'AFTER_ORIGINAL_EDGE_DISTANCE_BEFORE_WALKED_DISTANCE_WRITE',dispatchScope:'ORIGINAL_PATHFINDER_INNER_PROTECTED_VIRTUAL_DISTANCE_RETURN',
 subjectRelationScope:'SELECTED_OUTER_FIND_PATH_INVOCATION',fieldScope:'BASE_NODE_FIELDS_AFTER_ORIGINAL_RETURN_AND_CAPTURE_GATES',
 comparisonOperandsStatus:'NOT_EXPOSED',neighborPopulationStatus:'NOT_EXPOSED',rejectionReasonStatus:'NOT_EXPOSED',
 finalPathCostStatus:'NOT_EXPOSED',navigationAdoptionStatus:'NOT_EXPOSED'}}};}
test('edge-distance original virtual return is opt-in direct evidence independent of geometry and cached aggregate fields',()=>{
 assert.equal(decisionBurstFromArgs(['--decision-burst']).channels.includes('path_distance'),false);
 assert.deepEqual(decisionBurstFromArgs(['--decision-burst','--decision-channels','path_distance']).channels,['path_distance']);
 const all=['goal','brain','path','control','malus','sensor','mod','projectile','neighbors','effective_malus','frontier','path_nodes','path_g','path_distance'];
 assert.deepEqual(decisionBurstFromArgs(['--decision-burst','--decision-channels',all.join(',')]).channels,all);
 assert.throws(()=>decisionBurstFromArgs(['--decision-burst','--decision-channels','path_distance,path_distance']));
 const r=row(),before=JSON.stringify(r);assert.equal(validOriginalDecisionEvent(r),true);
 const stages={},capabilities={};appendOriginalDecisionEvents([r],stages,capabilities,[]);
 assert.equal(stages.EVALUATION.facts[0].epistemic_status,'DIRECT_OBSERVED');assert.equal(stages.SELECTION,undefined);assert.equal(stages.RESULT,undefined);
 assert.equal(capabilities.path_edge_distances.status,'PARTIAL');
 const q=queryDecisionDrilldown({observations:[r],subjectUuid:uuid,identity,request:{channel:'path_edge_distances',startTick:90,endTick:110,limit:10,maxNodes:2}});
 assert.equal(q.items[0].data.returnedDistance,31.25);assert.equal(q.items[0].data.fromNode.data.g,8);
 assert.equal(q.items[0].reasonKnown,false);assert.deepEqual(q.items[0].source_observation_ids,[r.observationId]);
 assert.ok(observeDebugWorkspaceDecision({observations:[r],subjectUuid:uuid,identity,tick:110}).available_drilldowns.includes('path_edge_distances'));
 assert.equal(JSON.stringify(r),before);
});
test('nonfinite original return, null custom-call arguments and capped exact-reference identities stay explicit',()=>{
 const r=row(),d=r.payload.data;delete d.returnedDistance;d.returnedDistanceStatus='NOT_EXPOSED';
 d.fromIdentity={status:'NOT_EXPOSED',detail:'NODE_IDENTITY_LIMIT'};d.toNode={status:'NOT_EXPOSED',detail:'NULL_NODE'};
 d.toIdentity={status:'NOT_EXPOSED',detail:'NULL_NODE'};assert.equal(validOriginalDecisionEvent(r),true);
 d.returnedDistance=-0;delete d.returnedDistanceStatus;assert.equal(validOriginalDecisionEvent(r),true);
 d.fromNode.data.walkedDistance=77;assert.equal(validOriginalDecisionEvent(r),true,'later cached field does not replace the original returned float');
});
test('edge-distance rejects invented cost/rejection/receiver/phase and contradictory unknowns',()=>{
 for(const change of [r=>r.payload.semantics='ORIGINAL_FIELD_WRITE_CHECKPOINT_ONLY',r=>r.payload.data.returnedDistanceScope='RECOMPUTED_EUCLIDEAN',
  r=>r.payload.data.returnedDistance=NaN,r=>r.payload.data.returnedDistanceStatus='NOT_EXPOSED',r=>r.payload.data.fromNode.data.gStatus='NOT_EXPOSED',
  r=>r.payload.data.toIdentity.id='search:1:2:node:1',r=>r.payload.data.fromIdentity.id='search:1:1:node:3',
  r=>r.payload.data.receiverScope='ARBITRARY_RECEIVER',r=>r.payload.data.phase='AFTER_RANGE_REJECTION',r=>r.payload.data.maxNodes=65,
  r=>r.payload.data.fieldScope='EXACT_ORIGINAL_COMPARISON_OPERANDS',r=>r.payload.data.toNode.data.openAtCheckpoint=true,
  r=>r.payload.data.fromNode={status:'NOT_EXPOSED',detail:'NULL_NODE'},r=>r.payload.data.rejectionReasonStatus='AVAILABLE',
  r=>r.payload.data.comparisonOperandsStatus='AVAILABLE',r=>r.payload.data.finalPathCost=31.25,r=>r.payload.data.navigationAdoptionStatus='AVAILABLE']){
  const r=row();change(r);assert.equal(validOriginalDecisionEvent(r),false);
 }
});
test('same-coordinate edges, repeats and query/context caps never invent a candidate population or overwrite the retained data',()=>{
 const first=row(),second=row(2);second.payload.data.fromIdentity.id='search:1:1:node:2';second.payload.data.toIdentity.id='search:1:1:node:1';
 const foreign=row(3);foreign.arenaEpoch++;const stale=row(4);stale.payload.targetRevision++;
 const rows=[first,second,foreign,stale],before=JSON.stringify(rows);
 const q=queryDecisionDrilldown({observations:rows,subjectUuid:uuid,identity,request:{channel:'path_edge_distances',startTick:90,endTick:110,limit:1,maxNodes:1}});
 assert.equal(q.totalMatchingItems,2);assert.equal(q.truncated,true);assert.equal(q.items[0].data.toIdentity.id,'search:1:1:node:1');
 assert.deepEqual(q.items[0].source_observation_ids,[second.observationId]);assert.equal(JSON.stringify(rows),before);
});
