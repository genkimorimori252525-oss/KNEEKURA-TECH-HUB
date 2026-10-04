import test from 'node:test';
import assert from 'node:assert/strict';
import {decisionBurstFromArgs} from '../../decision-burst-cli.mjs';
import {validOriginalDecisionEvent,appendOriginalDecisionEvents} from '../original-decision-events.mjs';
import {queryDecisionDrilldown} from '../decision-drilldown.mjs';
const uuid='00000000-0000-0000-0000-000000000001';
const identity={debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,arenaEpoch:2,targetRevision:1};
function row(operation='POP',index=1){
 const insertion=operation.endsWith('INSERT'),change=operation==='CHANGE_COST';
 return {kind:'observation',lane:'AI_DECISION',...identity,epistemicStatus:'OBSERVED',completeness:{complete:true},
  source:{side:'SERVER'},scope:{kind:'ENTITY_UUID',entityUuid:uuid},observationId:'obs:heap:'+index,gameTime:100+index,
  payload:{schema:'kneekura.original-decision-event/v1',semantics:'ORIGINAL_INVOCATION_RETURN_ONLY',targetRevision:1,
   eventIndex:index,burstId:'burst:1:90',kind:'PATH_HEAP_OPERATION_RETURN',observerCostNanos:1,
   observerCostScope:'BUILD_AND_FIRST_BYTE_CHECK_EXCLUDES_FINAL_ENCODING_WRITER',data:{searchId:'search:1:1',
    heapClass:'net.minecraft.world.level.pathfinder.BinaryHeap',operation,
    phase:insertion?'AFTER_ORIGINAL_INSERT':change?'AFTER_ORIGINAL_CHANGE_COST':'AFTER_ORIGINAL_POP_BEFORE_CALLER_CLOSE',
    nodeRole:change?'PASSED_NODE_AFTER_ORIGINAL_CALL':'ORIGINAL_RETURNED_NODE',
    node:{status:'AVAILABLE',data:{className:'net.minecraft.world.level.pathfinder.Node',x:0,y:64,z:0,pathType:'WALKABLE',
     g:5,h:3,f:8,costMalus:1,walkedDistance:4,openAtReturn:operation!=='POP',closedAtReturn:false}},
    nodeIdentity:{status:'AVAILABLE',id:'search:1:1:node:1'},maxNodes:2,
    ...(insertion?{argumentMatchesReturned:true}:{}),...(change?{requestedCost:8}:{}),
    dispatchScope:'ORIGINAL_PATHFINDER_INNER_HEAP_CALL_RETURN',subjectRelationScope:'SELECTED_OUTER_FIND_PATH_INVOCATION',
    neighborPopulationStatus:'NOT_EXPOSED',rejectionReasonStatus:'NOT_EXPOSED',finalPathCostStatus:'NOT_EXPOSED'}}};
}
test('heap operation capture is opt-in and keeps pop-before-close separate from later state',()=>{
 assert.equal(decisionBurstFromArgs(['--decision-burst']).channels.includes('frontier'),false);
 assert.deepEqual(decisionBurstFromArgs(['--decision-burst','--decision-channels','path,frontier']).channels,['path','frontier']);
 const rows=['START_INSERT','CHANGE_COST','POP'].map((op,i)=>row(op,i+1)),before=JSON.stringify(rows);
 for(const r of rows)assert.equal(validOriginalDecisionEvent(r),true);
 const stages={},capabilities={},timeline=[];appendOriginalDecisionEvents(rows,stages,capabilities,timeline);
 assert.equal(stages.EVALUATION.facts.length,3);assert.equal(capabilities.path_heap_operations.status,'PARTIAL');
 assert.equal(stages.SELECTION,undefined);assert.equal(stages.RESULT,undefined);
 assert.equal(stages.EVALUATION.facts[2].value.node.data.closedAtReturn,false);
 assert.equal(stages.EVALUATION.facts[2].value.phase,'AFTER_ORIGINAL_POP_BEFORE_CALLER_CLOSE');
 const query=queryDecisionDrilldown({observations:rows,subjectUuid:uuid,identity,
  request:{channel:'path_heap_operations',startTick:90,endTick:110,limit:10,maxNodes:2}});
 assert.equal(query.items.length,3);assert.deepEqual(query.items.map(x=>x.source_observation_ids[0]),rows.map(r=>r.observationId));
 assert.equal(JSON.stringify(rows),before);
});
test('heap facts preserve changed return identity, requested cost and bounded unknown identities',()=>{
 const insertion=row('RELAXATION_INSERT');insertion.payload.data.argumentMatchesReturned=false;
 insertion.payload.data.heapClass='example.CustomHeap';assert.equal(validOriginalDecisionEvent(insertion),true);
 const update=row('CHANGE_COST');update.payload.data.requestedCost=9;
 assert.equal(validOriginalDecisionEvent(update),true);assert.equal(update.payload.data.node.data.f,8);
 const limited=row();limited.payload.data.nodeIdentity={status:'NOT_EXPOSED',detail:'NODE_IDENTITY_LIMIT'};
 assert.equal(validOriginalDecisionEvent(limited),true);
 for(const mutate of [d=>d.operation='REJECTED',d=>d.phase='AFTER_CALLER_CLOSE',d=>d.nodeIdentity.id='search:1:2:node:1',
  d=>d.nodeIdentity.id='search:1:1:node:3',d=>d.nodeIdentity.id='search:1:1:node:0',d=>d.maxNodes=65,
  d=>d.rejectionReasonStatus='AVAILABLE',d=>d.finalPathCostStatus='AVAILABLE',d=>d.node.data.g=NaN,
  d=>d.argumentMatchesReturned=true,d=>d.requestedCost=8,d=>d.rejectedNodes=[]]){
  const bad=row();mutate(bad.payload.data);assert.equal(validOriginalDecisionEvent(bad),false);
 }
});
test('a partial heap stream cannot join equal coordinates or import another observation context',()=>{
 const first=row(),second=row('POP',2);second.payload.data.nodeIdentity.id='search:1:1:node:2';
 const foreign=row('POP',3);foreign.arenaEpoch++;
 const stale=row('POP',4);stale.payload.targetRevision=2;
 const rows=[first,second,foreign,stale],before=JSON.stringify(rows);
 const query=queryDecisionDrilldown({observations:rows,subjectUuid:uuid,identity,
  request:{channel:'path_heap_operations',startTick:90,endTick:110,limit:10,maxNodes:2}});
 assert.equal(query.items.length,2);
 assert.deepEqual(query.items.map(i=>i.data.nodeIdentity.id),['search:1:1:node:1','search:1:1:node:2']);
 assert.deepEqual(query.items.map(i=>i.data.node.data.x),[0,0]);
 assert.equal(JSON.stringify(rows),before);
});
