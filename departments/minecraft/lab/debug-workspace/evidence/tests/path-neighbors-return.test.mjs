import test from 'node:test';
import assert from 'node:assert/strict';
import {decisionBurstFromArgs} from '../../decision-burst-cli.mjs';
import {validOriginalDecisionEvent,appendOriginalDecisionEvents} from '../original-decision-events.mjs';
import {queryDecisionDrilldown} from '../decision-drilldown.mjs';
const uuid='00000000-0000-0000-0000-000000000001';
const identity={debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,arenaEpoch:2,targetRevision:1};
const node=x=>({status:'AVAILABLE',data:{className:'net.minecraft.world.level.pathfinder.Node',x,y:64,z:0,
  pathType:'WALKABLE',g:x,h:1,f:x+1,costMalus:0,walkedDistance:x,openAtReturn:false,closedAtReturn:false}});
function row(){return {kind:'observation',lane:'AI_DECISION',...identity,epistemicStatus:'OBSERVED',completeness:{complete:true},
 source:{side:'SERVER'},scope:{kind:'ENTITY_UUID',entityUuid:uuid},observationId:'obs:neighbors:1',gameTime:100,
 payload:{schema:'kneekura.original-decision-event/v1',semantics:'ORIGINAL_INVOCATION_RETURN_ONLY',targetRevision:1,
  eventIndex:1,burstId:'burst:1:90',kind:'PATH_NEIGHBORS_RETURN',observerCostNanos:1,
  observerCostScope:'BUILD_AND_FIRST_BYTE_CHECK_EXCLUDES_FINAL_ENCODING_WRITER',data:{searchId:'search:1:1',
    evaluatorClass:'net.minecraft.world.level.pathfinder.WalkNodeEvaluator',currentNode:node(0),returnedCount:3,
    returnedArrayLength:32,maxNodes:2,neighbors:[{slot:0,node:node(2)},{slot:1,node:node(1)}],truncated:true,
    phase:'AFTER_ORIGINAL_GET_NEIGHBORS_BEFORE_RELAXATION',dispatchScope:'ORIGINAL_VIRTUAL_GET_NEIGHBORS_RETURN',
    subjectRelationScope:'SELECTED_OUTER_FIND_PATH_INVOCATION',fieldScope:'BASE_NODE_FIELDS_BEFORE_RELAXATION',
    neighborPopulationStatus:'NOT_EXPOSED',rejectionReasonStatus:'NOT_EXPOSED'}}};}
test('original neighbor observation is additional opt-in and preserves returned slots before relaxation',()=>{
  assert.equal(decisionBurstFromArgs(['--decision-burst']).channels.includes('neighbors'),false);
  assert.deepEqual(decisionBurstFromArgs(['--decision-burst','--decision-channels','path,neighbors']).channels,['path','neighbors']);
  const r=row(),before=JSON.stringify(r);assert.equal(validOriginalDecisionEvent(r),true);
  const stages={},capabilities={},timeline=[];appendOriginalDecisionEvents([r],stages,capabilities,timeline);
  assert.deepEqual(stages.EVALUATION.facts[0].value.neighbors.map(n=>n.node.data.x),[2,1]);
  assert.equal(capabilities.path_search_neighbors.status,'PARTIAL');assert.equal(stages.SELECTION,undefined);
  assert.deepEqual(timeline[0].source_observation_ids,[r.observationId]);assert.equal(JSON.stringify(r),before);
  const query=queryDecisionDrilldown({observations:[r],subjectUuid:uuid,identity,
    request:{channel:'path_neighbors',startTick:90,endTick:110,limit:1,maxNodes:1}});
  assert.equal(query.items[0].data.neighbors.length,1);assert.equal(query.items[0].queryNodesTruncated,true);
  assert.equal(query.items[0].data.returnedCount,3);assert.equal(JSON.stringify(r),before);
});
test('partial original neighbor output cannot invent rejected population or reorder the source slots',()=>{
  const r=row();r.payload.data.neighbors[1].node={status:'NOT_EXPOSED',detail:'NULL_NODE'};
  assert.equal(validOriginalDecisionEvent(r),true);
  for(const mutate of [d=>d.neighbors[0].slot=1,d=>d.returnedCount=33,d=>d.maxNodes=65,d=>d.truncated=false,
    d=>d.neighborPopulationStatus='AVAILABLE',d=>d.rejectionReasonStatus='AVAILABLE',d=>d.rejectedNeighbors=[node(3)],
    d=>d.phase='AFTER_RELAXATION',d=>d.neighbors[0].node.data.g=NaN]) {
    const bad=row();mutate(bad.payload.data);assert.equal(validOriginalDecisionEvent(bad),false);
  }
});
