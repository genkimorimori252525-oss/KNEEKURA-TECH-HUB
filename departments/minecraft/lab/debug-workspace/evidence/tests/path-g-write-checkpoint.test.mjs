import test from 'node:test';
import assert from 'node:assert/strict';
import {decisionBurstFromArgs} from '../../decision-burst-cli.mjs';
import {validOriginalDecisionEvent,appendOriginalDecisionEvents} from '../original-decision-events.mjs';
import {queryDecisionDrilldown} from '../decision-drilldown.mjs';
import {observeDebugWorkspaceDecision} from '../debug-workspace-decision-adapter.mjs';
const uuid='00000000-0000-0000-0000-000000000001';
const identity={debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,arenaEpoch:2,targetRevision:1};
function row(index=1){return {kind:'observation',lane:'AI_DECISION',...identity,source:{side:'SERVER'},
 scope:{kind:'ENTITY_UUID',entityUuid:uuid},epistemicStatus:'OBSERVED',completeness:{complete:true},gameTime:100+index,
 observationId:'obs:g-write:'+index,payload:{schema:'kneekura.original-decision-event/v1',semantics:'ORIGINAL_FIELD_WRITE_CHECKPOINT_ONLY',
 targetRevision:1,eventIndex:index,burstId:'burst:1:90',kind:'PATH_NODE_G_WRITE_CHECKPOINT',observerCostNanos:1,
 observerCostScope:'BUILD_AND_FIRST_BYTE_CHECK_EXCLUDES_FINAL_ENCODING_WRITER',data:{searchId:'search:1:1',maxNodes:2,
 writtenG:8,writtenGScope:'ORIGINAL_PUTFIELD_ARGUMENT',nodeRole:'ORIGINAL_FIELD_WRITE_RECEIVER',
 node:{status:'AVAILABLE',data:{className:'net.minecraft.world.level.pathfinder.Node',x:0,y:64,z:0,pathType:'WALKABLE',
 g:8,h:2,f:100,costMalus:1,walkedDistance:4,openAtCheckpoint:true,closedAtCheckpoint:false}},
 nodeIdentity:{status:'AVAILABLE',id:'search:1:1:node:1'},predecessorPresent:true,
 predecessorIdentity:{status:'AVAILABLE',id:'search:1:1:node:2'},
 phase:'AFTER_ORIGINAL_ACCEPTED_G_FIELD_WRITE_BEFORE_HEURISTIC_UPDATE',dispatchScope:'ORIGINAL_PATHFINDER_INNER_ACCEPTED_G_FIELD_WRITE',
 subjectRelationScope:'SELECTED_OUTER_FIND_PATH_INVOCATION',fieldScope:'BASE_NODE_FIELDS_AFTER_WRITE_AND_CAPTURE_GATES',
 comparisonOperandsStatus:'NOT_EXPOSED',neighborPopulationStatus:'NOT_EXPOSED',rejectionReasonStatus:'NOT_EXPOSED',
 finalPathCostStatus:'NOT_EXPOSED',navigationAdoptionStatus:'NOT_EXPOSED'}}};}
test('g-field checkpoint is explicitly armed algorithm state, with separate written g and unupdated cached h/f',()=>{
 assert.equal(decisionBurstFromArgs(['--decision-burst']).channels.includes('path_g'),false);
 assert.deepEqual(decisionBurstFromArgs(['--decision-burst','--decision-channels','path_g']).channels,['path_g']);
 const all=['goal','brain','path','control','malus','sensor','mod','projectile','neighbors','effective_malus','frontier','path_nodes','path_g'];
 assert.deepEqual(decisionBurstFromArgs(['--decision-burst','--decision-channels',all.join(',')]).channels,all);
 assert.throws(()=>decisionBurstFromArgs(['--decision-burst','--decision-channels','path_g,path_g']));
 const r=row(),before=JSON.stringify(r);assert.equal(validOriginalDecisionEvent(r),true);
 const stages={},capabilities={};appendOriginalDecisionEvents([r],stages,capabilities,[]);
 assert.equal(stages.EVALUATION.facts[0].epistemic_status,'INSTRUMENTED_ALGORITHM_STATE');
 assert.equal(stages.EVALUATION.facts[0].causal_relation,'ALGORITHM_TRACE_RELATION');
 assert.equal(stages.SELECTION,undefined);assert.equal(stages.RESULT,undefined);assert.equal(capabilities.path_g_writes.status,'PARTIAL');
 const q=queryDecisionDrilldown({observations:[r],subjectUuid:uuid,identity,
 request:{channel:'path_g_writes',startTick:90,endTick:110,limit:10,maxNodes:2}});
 assert.equal(q.items[0].data.writtenG,8);assert.equal(q.items[0].data.node.data.f,100);
 assert.equal(q.items[0].epistemic_status,'INSTRUMENTED_ALGORITHM_STATE');assert.equal(q.items[0].reasonKnown,false);
 assert.deepEqual(q.items[0].source_observation_ids,[r.observationId]);
 const p=observeDebugWorkspaceDecision({observations:[r],subjectUuid:uuid,identity,tick:110});
 assert.ok(p.available_drilldowns.includes('path_g_writes'));assert.equal(JSON.stringify(r),before);
});
test('unknown g and bounded receiver/predecessor identity do not become numeric costs or coordinate joins',()=>{
 const r=row(),d=r.payload.data;delete d.writtenG;d.writtenGStatus='NOT_EXPOSED';delete d.node.data.g;d.node.data.gStatus='NOT_EXPOSED';
 d.nodeIdentity={status:'NOT_EXPOSED',detail:'NODE_IDENTITY_LIMIT'};d.predecessorIdentity={status:'NOT_EXPOSED',detail:'NODE_IDENTITY_LIMIT'};
 assert.equal(validOriginalDecisionEvent(r),true);d.predecessorPresent=false;d.predecessorIdentity={status:'NOT_EXPOSED',detail:'NULL_NODE'};
 assert.equal(validOriginalDecisionEvent(r),true);
 d.writtenG=9;delete d.writtenGStatus;assert.equal(validOriginalDecisionEvent(r),true,'passed written g and later unknown cached g have separate scopes');
 d.node.data.g=77;delete d.node.data.gStatus;assert.equal(validOriginalDecisionEvent(r),true,'a later differing cached field is not rewritten to equal the original argument');
});
test('g checkpoint rejects invented returns, contradictory cached/written values and expanded decision claims',()=>{
 for(const change of [r=>r.payload.semantics='ORIGINAL_INVOCATION_RETURN_ONLY',r=>r.payload.data.writtenGScope='RECOMPUTED_COST',
  r=>r.payload.data.writtenG=NaN,r=>r.payload.data.writtenGStatus='NOT_EXPOSED',r=>r.payload.data.node.data.gStatus='NOT_EXPOSED',
  r=>r.payload.data.node={status:'NOT_EXPOSED',detail:'NULL_NODE'},r=>r.payload.data.maxNodes=65,
  r=>r.payload.data.nodeIdentity.id='search:1:2:node:1',r=>r.payload.data.predecessorIdentity.id='search:1:1:node:3',
  r=>r.payload.data.predecessorPresent=false,r=>r.payload.data.phase='AFTER_ORIGINAL_HEAP_RETURN',
  r=>r.payload.data.fieldScope='BASE_NODE_FIELDS_IMMEDIATELY_AFTER_G_WRITE',
  r=>r.payload.data.node.data.closedAtReturn=true,r=>r.payload.data.nodeRole='COORDINATE_MATCH',
  r=>r.payload.data.comparisonOperandsStatus='AVAILABLE',r=>r.payload.data.rejectionReasonStatus='AVAILABLE',
  r=>r.payload.data.finalPathCost=8,r=>r.payload.data.navigationAdoptionStatus='AVAILABLE']){
  const r=row();change(r);assert.equal(validOriginalDecisionEvent(r),false);
 }
});
test('same-coordinate receivers remain separate and exact context/revision/query caps fence g writes',()=>{
 const first=row(),second=row(2);second.payload.data.nodeIdentity.id='search:1:1:node:2';
 const foreign=row(3);foreign.arenaEpoch++;const stale=row(4);stale.payload.targetRevision++;
 const rows=[first,second,foreign,stale],before=JSON.stringify(rows);
 const q=queryDecisionDrilldown({observations:rows,subjectUuid:uuid,identity,
 request:{channel:'path_g_writes',startTick:90,endTick:110,limit:1,maxNodes:2}});
 assert.equal(q.totalMatchingItems,2);assert.equal(q.truncated,true);assert.equal(q.items[0].data.nodeIdentity.id,'search:1:1:node:2');
 assert.deepEqual(q.items[0].source_observation_ids,[second.observationId]);assert.equal(JSON.stringify(rows),before);
});
