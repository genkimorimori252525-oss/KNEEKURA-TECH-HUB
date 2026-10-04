import test from 'node:test';
import assert from 'node:assert/strict';
import {queryDecisionDrilldown} from '../decision-drilldown.mjs';
import {validOriginalDecisionEvent,appendOriginalDecisionEvents} from '../original-decision-events.mjs';
const uuid='00000000-0000-0000-0000-000000000001';
const identity={debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,arenaEpoch:2,targetRevision:1};
function row(kind,data,tick=100){return {kind:'observation',lane:'AI_DECISION',observationId:'obs:'+kind+':'+tick,
  ...identity,scope:{kind:'ENTITY_UUID',entityUuid:uuid},epistemicStatus:'OBSERVED',completeness:{complete:true},
  gameTime:tick,writerSeq:tick,source:{side:'SERVER',method:'fixture'},payload:{schema:'kneekura.original-decision-event/v1',
  semantics:'ORIGINAL_INVOCATION_RETURN_ONLY',kind,data,targetRevision:1,burstId:'burst:1:90',eventIndex:1,
  observerCostNanos:10,observerCostScope:'BUILD_AND_FIRST_BYTE_CHECK_EXCLUDES_FINAL_ENCODING_WRITER'}};}
const request=channel=>({channel,startTick:90,endTick:110,limit:8,maxNodes:1});
const query=(observations,channel='path_search')=>queryDecisionDrilldown({observations,subjectUuid:uuid,identity,request:request(channel)});

test('native Gson omitted unknown identities preserve original callbacks without inventing IDs',()=>{
  const fixtures=[
    ['GOAL_START_RETURN',{selector:'goal',goalClass:'Goal',priority:1,instanceIdentityStatus:'NOT_EXPOSED',running:true,reasonStatus:'NOT_EXPOSED'}],
    ['BRAIN_TICK_RETURN',{brainClass:'Brain',storedBrainMatch:true}],
    ['BEHAVIOR_TRY_START_RETURN',{className:'Behavior',cachedStatus:'RUNNING',result:true,reasonStatus:'NOT_EXPOSED'}],
    ['SENSOR_SCAN_RETURN',{className:'Sensor',candidatePopulationStatus:'NOT_EXPOSED'}]];
  for(const [kind,data] of fixtures){
    const record=row(kind,data),before=JSON.stringify(record);assert.equal(validOriginalDecisionEvent(record),true,kind);
    const stages={},capabilities={},timeline=[];appendOriginalDecisionEvents([record],stages,capabilities,timeline);
    assert.equal(timeline.length,1);assert.equal(timeline[0].summary.instanceIdentity,null);
    assert.equal(timeline[0].summary.instanceIdentityStatus,'NOT_EXPOSED');assert.equal(JSON.stringify(record),before);
    if(kind==='SENSOR_SCAN_RETURN')assert.equal(query([record],'sensor_execution').items[0].data.instanceIdentityStatus,'NOT_EXPOSED');
    if(kind.startsWith('GOAL_'))assert.equal(query([record],'goal_transitions').items.length,1);
    const invalid=structuredClone(record);invalid.payload.data.instanceIdentityStatus='AVAILABLE';
    assert.equal(validOriginalDecisionEvent(invalid),false);
  }
});
function frontier(){return {status:'AVAILABLE',data:{nodes:[0,1].map(x=>({x,y:64,z:0,g:x,h:1,f:x+1,costMalus:0,
  walkedDistance:x,pathType:'WALKABLE',openAtReturn:true,closedAtReturn:false,cacheRole:'OPEN_AT_RETURN'})),
  cacheNodeCount:2,truncated:false,phase:'OUTER_BEFORE_DONE_AFTER_INNER_RETURN',neighborEvaluationTraceStatus:'NOT_EXPOSED',
  rejectionReasonStatus:'NOT_EXPOSED'}};}
test('typed path drill-down cites the original cache/result pair and bounds returned nodes',()=>{
  const rows=[row('PATH_SEARCH_STATE',{searchId:'search:1:1',frontier:frontier()}),
    row('PATH_SEARCH_RESULT',{searchId:'search:1:1',resultPresent:true,resultClass:'net.minecraft.world.level.pathfinder.Path',canReach:true,resultNodeCount:3},101)];
  const before=JSON.stringify(rows);const out=query(rows);
  assert.equal(out.status,'PARTIAL');assert.equal(out.items[0].frontier.data.nodes.length,1);
  assert.equal(out.items[0].queryNodesTruncated,true);assert.equal(out.items[0].result.canReach,true);
  assert.deepEqual(out.items[0].source_observation_ids,['obs:PATH_SEARCH_STATE:100','obs:PATH_SEARCH_RESULT:101']);
  assert.equal(out.items[0].neighborEvaluationTraceStatus,'NOT_EXPOSED');assert.equal(JSON.stringify(rows),before);
});
test('missing path result stays NOT_CAPTURED and does not imply unreachable',()=>{
  const out=query([row('PATH_SEARCH_STATE',{searchId:'search:1:1',frontier:frontier()})]);
  assert.equal(out.items[0].resultStatus,'NOT_CAPTURED');assert.equal(out.items[0].result,null);
});
test('typed drill-down requires full identity and bounded known read-only options',()=>{
  for(const change of [v=>delete v.identity.processEpoch,v=>v.request.endTick=20000,
    v=>v.request.limit=257,v=>v.request.maxNodes=65,v=>v.request.channel='execute',
    v=>v.request.authority=true,v=>v.identity.targetRevision=0]) {
    const value={observations:[],subjectUuid:uuid,identity:{...identity},request:request('path_search')};change(value);
    assert.throws(()=>queryDecisionDrilldown(value));
  }
});
test('requested identity excludes foreign UUID, revision and process without guessed transitions',()=>{
  const data={selector:'goal',instanceIdentity:'goal:1:1',instanceIdentityStatus:'AVAILABLE',goalClass:'Goal',priority:1,running:true,reasonStatus:'NOT_EXPOSED'};
  const kept=row('GOAL_START_RETURN',data),foreign=row('GOAL_STOP_RETURN',{...data,running:false},101);foreign.processEpoch=2;
  const revision=row('GOAL_STOP_RETURN',{...data,running:false},102);revision.payload.targetRevision=2;
  const other=row('GOAL_STOP_RETURN',{...data,running:false},103);other.scope.entityUuid='00000000-0000-0000-0000-000000000002';
  const out=query([kept,foreign,revision,other],'goal_transitions');
  assert.equal(out.items.length,1);assert.equal(out.items[0].kind,'GOAL_START_RETURN');
  assert.equal(out.items[0].reasonKnown,false);assert.equal(out.semantics.adjacentEventsProveCausality,false);
});
test('empty and malformed event evidence remains NOT_CAPTURED',()=>{
  const invalid=row('PATH_SEARCH_STATE',{searchId:'search:1:1',frontier:frontier()});invalid.payload.data.frontier.data.nodes[0].g='invented';
  assert.equal(query([invalid]).status,'NOT_CAPTURED');assert.equal(query([]).items.length,0);
});
function memory(tick,value,ttl=20,status='AVAILABLE') {
  const result=row('ignored',{},tick);result.payload={schema:'kneekura.vanilla-decision-snapshot/v1',
    targetRevision:1,semantics:'MOB_COMPONENT_SNAPSHOT_ONLY',sections:Object.fromEntries(
      ['goal_scheduler','brain_memory','brain_activities','navigation_path','movement_control'].map(k=>[k,{status:'NOT_EXPOSED'}]))};
  result.payload.sections.brain_memory={status,data:{truncated:status==='PARTIAL',entries:[
    {key:'minecraft:attack_target',registered:true,present:true,timeToLive:String(ttl),value}]}};
  return result;
}
test('memory changes cite both samples; TTL countdown and capture gaps do not become value changes',()=>{
  const same=memory(95,{status:'AVAILABLE',value:'a'},20),ttl=memory(100,{status:'AVAILABLE',value:'a'},15),
    changed=memory(105,{status:'AVAILABLE',value:'b'},10),gap=memory(120,{status:'AVAILABLE',value:'c'},5);
  const value={observations:[same,ttl,changed,gap],subjectUuid:uuid,identity,request:{...request('brain_memory_changes'),endTick:130}};
  const out=queryDecisionDrilldown(value);assert.equal(out.items.length,1);
  assert.equal(out.items[0].exactChangeTickKnown,false);
  assert.deepEqual(out.items[0].source_observation_ids,['obs:ignored:100','obs:ignored:105']);
  assert.equal(out.items[0].causal_relation,'TEMPORAL_ASSOCIATION');
});
test('partial memory capture breaks the baseline and does not prove a transition',()=>{
  const out=query([memory(95,{value:'a'}),memory(100,{value:'b'},20,'PARTIAL'),memory(105,{value:'c'})],'brain_memory_changes');
  assert.equal(out.items.length,0);assert.equal(out.status,'NOT_CAPTURED');
});
test('duplicate retained observation IDs are refused instead of chosen silently',()=>{
  const one=row('PATH_SEARCH_STATE',{searchId:'search:1:1',frontier:frontier()});
  assert.throws(()=>query([one,structuredClone(one)]),/DUPLICATED/);
});
