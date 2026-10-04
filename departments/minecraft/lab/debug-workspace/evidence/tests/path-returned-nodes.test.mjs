import test from 'node:test';
import assert from 'node:assert/strict';
import {decisionBurstFromArgs} from '../../decision-burst-cli.mjs';
import {validOriginalDecisionEvent,appendOriginalDecisionEvents} from '../original-decision-events.mjs';
import {queryDecisionDrilldown} from '../decision-drilldown.mjs';
import {buildRetainedDecisionPresentation} from '../decision-presentation.mjs';
const uuid='00000000-0000-0000-0000-000000000001';
const identity={debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,arenaEpoch:2,targetRevision:1};
const nodeIdentity=i=>i<2?{status:'AVAILABLE',id:'search:1:1:node:'+(i+1)}:{status:'NOT_EXPOSED',detail:'NODE_IDENTITY_LIMIT'};
function entry(index){return {index,node:{status:'AVAILABLE',data:{className:'net.minecraft.world.level.pathfinder.Node',x:index,y:64,z:0,
 pathType:'WALKABLE',g:index?20:0,h:3-index,f:20+3-index,costMalus:1,walkedDistance:index,openAtReturn:false,closedAtReturn:true}},
 nodeIdentity:nodeIdentity(index),predecessorPresent:index>0,
 predecessorIdentity:index?nodeIdentity(index-1):{status:'NOT_EXPOSED',detail:'NULL_NODE'}};}
function row(index=1){return {kind:'observation',lane:'AI_DECISION',...identity,epistemicStatus:'OBSERVED',completeness:{complete:true},
 source:{side:'SERVER'},scope:{kind:'ENTITY_UUID',entityUuid:uuid},observationId:'obs:returned:'+index,gameTime:100+index,
 payload:{schema:'kneekura.original-decision-event/v1',semantics:'ORIGINAL_INVOCATION_RETURN_ONLY',targetRevision:1,
 eventIndex:index,burstId:'burst:1:90',kind:'PATH_RETURNED_NODES',observerCostNanos:1,
 observerCostScope:'BUILD_AND_FIRST_BYTE_CHECK_EXCLUDES_FINAL_ENCODING_WRITER',data:{searchId:'search:1:1',resultPresent:true,
 resultClass:'net.minecraft.world.level.pathfinder.Path',maxNodes:2,dimension:'minecraft:overworld',
 pathNodes:{status:'PARTIAL',data:{listClass:'java.util.ArrayList',nodeCount:3,retainedNodeCount:2,truncated:true,
 nodes:[entry(0),entry(1)],terminalNode:{status:'AVAILABLE',data:entry(2)},
 target:{status:'AVAILABLE',data:{x:3,y:64,z:0}},canReach:true,nextNodeIndex:0,distanceToTarget:1,
 distanceToTargetScope:'PATH_CONSTRUCTOR_CACHED_VALUE'}},phase:'AFTER_ORIGINAL_OUTER_FIND_PATH_RETURN',
 dispatchScope:'SELECTED_OUTER_FIND_PATH_RETURN',fieldScope:'BASE_PATH_AND_NODE_CACHED_FIELDS_AT_RETURN',
 navigationAdoptionStatus:'NOT_EXPOSED',finalEffectiveCostStatus:'NOT_EXPOSED'}}};}
test('returned Path nodes are explicitly armed original-result data, not Motion, adopted navigation or a minimum cost',()=>{
 assert.equal(decisionBurstFromArgs(['--decision-burst']).channels.includes('path_nodes'),false);
 assert.deepEqual(decisionBurstFromArgs(['--decision-burst','--decision-channels','path_nodes']).channels,['path_nodes']);
 const r=row(),before=JSON.stringify(r);assert.equal(validOriginalDecisionEvent(r),true);
 const stages={},capabilities={},timeline=[];appendOriginalDecisionEvents([r],stages,capabilities,timeline);
 assert.equal(stages.RESULT.facts[0].epistemic_status,'DIRECT_OBSERVED');assert.equal(capabilities.returned_path_nodes.status,'PARTIAL');
 assert.equal(stages.SELECTION,undefined);assert.equal(stages.RESULT.facts[0].value.pathNodes.data.terminalNode.data.node.data.g,20);
 const q=queryDecisionDrilldown({observations:[r],subjectUuid:uuid,identity,
 request:{channel:'path_returned_nodes',startTick:90,endTick:110,limit:10,maxNodes:1}});
 assert.equal(q.items.length,1);assert.equal(q.items[0].data.pathNodes.data.nodes.length,1);
 assert.equal(q.items[0].queryNodesTruncated,true);assert.equal(q.items[0].data.pathNodes.data.retainedNodeCount,2);
 assert.equal(q.items[0].data.pathNodes.data.terminalNode.data.index,2);assert.deepEqual(q.items[0].source_observation_ids,[r.observationId]);
 const p=buildRetainedDecisionPresentation({observations:[r],subjectUuid:uuid,identity,request:{startTick:90,endTick:110,maxNodes:1}});
 assert.equal(p.layers.motion.trace.samples.length,0);assert.equal(p.layers.declaredNavigation.status,'NOT_CAPTURED');
 assert.equal(p.layers.returnedPath.enabledByDefault,false);assert.equal(p.layers.returnedPath.nodes.length,1);
 assert.equal(p.layers.returnedPath.nodes[0].index,0);assert.equal(p.layers.returnedPath.terminal.index,2);
 assert.equal(p.layers.returnedPath.target.x,3);assert.deepEqual(p.layers.returnedPath.source_observation_ids,[r.observationId]);
 assert.equal(p.semantics.returnedPathProvesNavigationAdoption,false);assert.equal(JSON.stringify(r),before);
});
test('null/custom results and unknown cached numbers do not promote cost/adoption availability',()=>{
 for(const detail of ['NULL_PATH','CUSTOM_PATH_CLASS','CUSTOM_NODE_LIST']){
  const r=row();r.payload.data.pathNodes={status:'NOT_EXPOSED',detail};
  if(detail==='NULL_PATH'){r.payload.data.resultPresent=false;delete r.payload.data.resultClass;}
  if(detail==='CUSTOM_PATH_CLASS')r.payload.data.resultClass='example.CustomPath';
  assert.equal(validOriginalDecisionEvent(r),true);const stages={},caps={};appendOriginalDecisionEvents([r],stages,caps,[]);
  assert.equal(caps.returned_path_nodes,undefined);assert.equal(stages.RESULT.facts[0].value.pathNodes.detail,detail);
 }
 const r=row();delete r.payload.data.pathNodes.data.terminalNode.data.node.data.g;
 r.payload.data.pathNodes.data.terminalNode.data.node.data.gStatus='NOT_EXPOSED';assert.equal(validOriginalDecisionEvent(r),true);
 const empty=row();empty.payload.data.pathNodes={status:'AVAILABLE',data:{...empty.payload.data.pathNodes.data,
 nodeCount:0,retainedNodeCount:0,nodes:[],truncated:false,terminalNode:{status:'NOT_EXPOSED',detail:'EMPTY_PATH'}}};
 assert.equal(validOriginalDecisionEvent(empty),true);
});
test('strict returned-node slots, reference identities and field scopes reject invented or contradictory facts',()=>{
 for(const change of [d=>d.pathNodes.data.nodes[0].index=1,d=>d.pathNodes.data.terminalNode.data.index=1,
  d=>d.pathNodes.data.nodeCount=1,d=>d.pathNodes.data.retainedNodeCount=1,d=>d.pathNodes.status='AVAILABLE',
  d=>d.pathNodes.data.truncated=false,d=>d.pathNodes.data.listClass='example.GetterList',d=>d.resultClass='example.Path',
  d=>d.pathNodes.data.nodes[0].predecessorIdentity={status:'AVAILABLE',id:'search:1:1:node:2'},
  d=>d.pathNodes.data.nodes[0].nodeIdentity.id='search:2:1:node:1',d=>d.navigationAdoptionStatus='AVAILABLE',
  d=>d.finalEffectiveCostStatus='AVAILABLE',d=>d.finalCost=20,d=>d.pathNodes.data.distanceToTarget=NaN,
  d=>d.pathNodes.data.distanceToTargetScope='REPLAYED_DISTANCE',d=>d.maxNodes=65]){
  const r=row();change(r.payload.data);assert.equal(validOriginalDecisionEvent(r),false);
 }
 const bad=row();bad.payload.semantics='ORIGINAL_FIELD_WRITE_CHECKPOINT_ONLY';assert.equal(validOriginalDecisionEvent(bad),false);
});
test('returned Path reads cannot import another context or carry a stale/missing path into a later result',()=>{
 const first=row(),foreign=row(2);foreign.arenaEpoch++;const stale=row(3);stale.payload.targetRevision=2;
 const absent=row(4);absent.payload.data.resultPresent=false;delete absent.payload.data.resultClass;
 absent.payload.data.pathNodes={status:'NOT_EXPOSED',detail:'NULL_PATH'};
 const p=buildRetainedDecisionPresentation({observations:[first,foreign,stale,absent],subjectUuid:uuid,identity,
 request:{startTick:90,endTick:110}});assert.equal(p.layers.returnedPath.status,'NOT_EXPOSED');
 assert.deepEqual(p.layers.returnedPath.nodes,[]);assert.deepEqual(p.layers.returnedPath.source_observation_ids,[absent.observationId]);
 const q=queryDecisionDrilldown({observations:[first,foreign,stale],subjectUuid:uuid,identity,
 request:{channel:'path_returned_nodes',startTick:90,endTick:110,limit:10,maxNodes:2}});assert.equal(q.items.length,1);
});
test('the terminal slot within the retained prefix agrees with that exact snapshot, independent of JSON key order',()=>{
 const r=row(),s=r.payload.data.pathNodes.data;s.nodeCount=2;s.truncated=false;r.payload.data.pathNodes.status='AVAILABLE';
 s.terminalNode.data=structuredClone(s.nodes[1]);assert.equal(validOriginalDecisionEvent(r),true);
 s.terminalNode.data=Object.fromEntries(Object.entries(s.terminalNode.data).reverse());assert.equal(validOriginalDecisionEvent(r),true);
 s.terminalNode.data.node.data.g++;assert.equal(validOriginalDecisionEvent(r),false,'one retained slot cannot claim two cached values');
});
test('null interior slots preserve actual indices and dimensions cannot be mixed in a presentation',()=>{
 const r=row(),s=r.payload.data.pathNodes.data;r.payload.data.maxNodes=3;s.retainedNodeCount=3;s.truncated=false;
 r.payload.data.pathNodes.status='AVAILABLE';s.nodes=[entry(0),{index:1,node:{status:'NOT_EXPOSED',detail:'NULL_NODE'},
   nodeIdentity:{status:'NOT_EXPOSED',detail:'NULL_NODE'},predecessorPresent:false,predecessorIdentity:{status:'NOT_EXPOSED',detail:'NULL_NODE'}},entry(2)];
 assert.equal(validOriginalDecisionEvent(r),true);const before=JSON.stringify(r);
 const args={observations:[r],subjectUuid:uuid,identity,request:{startTick:90,endTick:110}};
 const p=buildRetainedDecisionPresentation(args);assert.deepEqual(p.layers.returnedPath.nodes.map(n=>n.index),[0,2]);
 assert.equal(p.layers.motion.trace.samples.length,0);assert.equal(JSON.stringify(r),before);
 const state={...identity,kind:'observation',lane:'SERVER_ENTITY_STATE',scope:{kind:'ENTITY_UUID',entityUuid:uuid},source:{side:'SERVER'},
   epistemicStatus:'OBSERVED',observationId:'obs:dimension',gameTime:100,completeness:{complete:true},
   payload:{targetRevision:1,dimension:'minecraft:the_nether',x:0,y:64,z:0,alive:true,removed:false}};
 assert.throws(()=>buildRetainedDecisionPresentation({...args,observations:[r,state]}),/DIMENSION_BOUNDARY/);
});
