import test from 'node:test';
import assert from 'node:assert/strict';
import {buildRetainedDecisionPresentation} from '../decision-presentation.mjs';
import {validOriginalDecisionEvent} from '../original-decision-events.mjs';
import {
  observeDebugWorkspaceDecision,
  buildDebugWorkspaceMotionTrace,
  buildDebugWorkspaceRelatedProjectileTraces,
} from '../debug-workspace-decision-adapter.mjs';

const UUID='00000000-0000-0000-0000-000000000001';
function obs(lane, gameTime, payload, extra={}) {
  return {
    v:1,kind:'observation',
    observationId:'obs:'+lane+':'+gameTime,
    debugSessionId:'sess-a',runId:'run-a',runSnapshotId:'snap-a',
    processEpoch:1,arenaEpoch:3,resourceEpoch:1,
    writerId:'server',writerSeq:gameTime,
    level:lane==='BEHAVIOR_TRANSITION'?'L2':'L1',
    lane,observedAt:'2026-10-03T00:00:00.000Z',gameTime,
    scope:{kind:'ENTITY_UUID',entityUuid:UUID},
    source:{side:'SERVER',method:'fixture'},
    epistemicStatus:'OBSERVED',completeness:{complete:true},
    payload,
    ...extra,
  };
}
const rows=[
  obs('SERVER_ENTITY_STATE',100,{dimension:'minecraft:overworld',x:1,y:64,z:2,vx:.1,vy:0,vz:0,alive:true}),
  obs('AI_TARGET',100,{present:true,targetUuid:'target-1',lineOfSight:true}),
  obs('BRAIN_MEMORY',100,{attackTargetPresent:true,attackTargetUuid:'target-1',walkTargetPresent:true,walkTargetX:4,walkTargetY:64,walkTargetZ:5}),
  obs('RUNNING_BEHAVIORS',100,{count:1,running:[{index:0,className:'ExampleBehavior',instanceIdentity:'behavior:1'}],instanceIdentityScope:'JVM_PROCESS_TARGET_REVISION_REFERENCE_IDENTITY'}),
  obs('NAVIGATION',100,{navigationDone:false,pathPresent:true,pathDone:false,canReach:true,nodeCount:4,nextNodeIndex:1,nextNodeX:2,nextNodeY:64,nextNodeZ:3}),
  obs('BEHAVIOR_TRANSITION',105,{transitionSemantics:'RUNNING_SET_CHANGED_BETWEEN_SAMPLES',exactTransitionTickKnown:false,reasonKnown:false,started:[{className:'Attack'}],stopped:[]}),
  obs('SERVER_ENTITY_STATE',105,{dimension:'minecraft:overworld',x:2,y:64,z:2,vx:.2,vy:0,vz:0,alive:true}),
];
test('explicit absent target breaks motion even inside the configured sampling gap',()=>{
  const records=[obs('SERVER_ENTITY_STATE',100,{dimension:'minecraft:overworld',x:0,y:64,z:0}),
    obs('SERVER_TARGET_TRACKED',105,{tracked:false}),obs('SERVER_ENTITY_STATE',110,{dimension:'minecraft:overworld',x:1,y:64,z:0})];
  const trace=buildDebugWorkspaceMotionTrace({observations:records,subjectUuid:UUID,maxGapTicks:10});
  assert.equal(trace.segments.length,0);
  assert.equal(trace.gaps[0].kind,'MISSING_SELECTED_ENTITY');
  assert.equal(trace.gaps[0].source_observation_id,'obs:SERVER_TARGET_TRACKED:105');
  for(const r of records)r.payload.targetRevision=1;
  const presentation=buildRetainedDecisionPresentation({observations:records,subjectUuid:UUID,
    identity:{debugSessionId:'sess-a',runId:'run-a',runSnapshotId:'snap-a',processEpoch:1,arenaEpoch:3,targetRevision:1},
    request:{startTick:100,endTick:110}});
  assert.equal(presentation.layers.motion.trace.segments.length,0);
  assert.equal(presentation.layers.motion.trace.gaps[0].kind,'MISSING_SELECTED_ENTITY');
});
test('explicit native Projectile samples retain their trace class and refuse a mixed entity class',()=>{
  const projectile=structuredClone(rows.filter(r=>r.lane==='SERVER_ENTITY_STATE'));
  for(const r of projectile)r.payload.motionTraceClass='PROJECTILE_ACTUAL';
  assert.equal(buildDebugWorkspaceMotionTrace({observations:projectile,subjectUuid:UUID}).trace_class,'PROJECTILE_ACTUAL');
  projectile[0].payload.motionTraceClass='MOB_ACTUAL';
  assert.throws(()=>buildDebugWorkspaceMotionTrace({observations:projectile,subjectUuid:UUID}),/TRACE_CLASS/);
});

function original(kind,data,index=1) {
  return obs('AI_DECISION',120+index,{schema:'kneekura.original-decision-event/v1',
    semantics:'ORIGINAL_INVOCATION_RETURN_ONLY',targetRevision:1,burstId:'burst:1:100',eventIndex:index,
    kind,data,observerCostNanos:100,observerCostScope:'BUILD_AND_FIRST_BYTE_CHECK_EXCLUDES_FINAL_ENCODING_WRITER'},
    {source:{side:'SERVER',method:'fixture'}});
}
function teleportReturn(result,tick=103) {
  const record=original('CONTROL_TELEPORT_RETURN',{result,
    requestedPosition:{x:2,y:64,z:2},returnedPosition:{x:result?2:1,y:64,z:2},
    dispatchScope:'BASE_RANDOM_TELEPORT_RETURN',reasonStatus:'NOT_EXPOSED'});
  record.gameTime=tick;record.writerSeq=tick;record.observationId='obs:teleport:'+tick;
  return record;
}
function teleportRows(event) {
  return [obs('SERVER_ENTITY_STATE',100,{targetRevision:1,dimension:'minecraft:overworld',x:1,y:64,z:2}),
    event,obs('SERVER_ENTITY_STATE',105,{targetRevision:1,dimension:'minecraft:overworld',x:2,y:64,z:2})];
}
const PROJECTILE='00000000-0000-0000-0000-000000000002';
const HIT_TARGET='00000000-0000-0000-0000-000000000003';
function ranged(kind,fields={},index=1,tick=101) {
  const data={ownerUuid:UUID,projectileUuid:PROJECTILE,projectileClass:'net.minecraft.world.entity.projectile.Arrow',
    spawnEventIndex:1,relationshipScope:'ACCEPTED_FRESH_SPAWN_SELECTED_CACHED_OWNER',...fields};
  const record=original(kind,data,index);record.gameTime=tick;record.writerSeq=index;
  record.observationId='obs:ranged:'+index;return record;
}
function rangedSpawn(result=true) {
  return ranged('CONTROL_PROJECTILE_SPAWN_RETURN',{result,trackingLimit:16,
    position:{x:1,y:65,z:2},velocity:{x:1,y:0,z:0},dispatchScope:'SERVER_ADD_FRESH_ENTITY_RETURN'});
}
function rangedSample(index,tick,x) {
  return ranged('CONTROL_PROJECTILE_TICK_RETURN',{position:{x,y:65,z:2},velocity:{x:1,y:0,z:0},
    removed:false,dimension:'minecraft:overworld',dispatchScope:'SERVER_NON_PASSENGER_ORIGINAL_TICK_AFTER'},index,tick);
}
test('owned projectile traces use accepted spawn references and only original completed tick samples',()=>{
  const records=[rangedSpawn(),rangedSample(2,102,2),rangedSample(3,103,3)],before=structuredClone(records);
  assert.ok(records.every(validOriginalDecisionEvent));
  const result=buildDebugWorkspaceRelatedProjectileTraces({observations:records,subjectUuid:UUID});
  assert.equal(result.length,1);assert.equal(result[0].trace.subject.id,PROJECTILE);
  assert.equal(result[0].trace.trace_class,'PROJECTILE_ACTUAL');
  assert.deepEqual(result[0].spawn_source_observation_ids,['obs:ranged:1']);
  assert.deepEqual(result[0].trace.samples.map(s=>s.source_observation_id),['obs:ranged:2','obs:ranged:3']);
  assert.equal(result[0].trace.segments.length,1);assert.deepEqual(records,before);
});
test('failed or missing spawn, another owner, changed owner class and invalid spawn reference create no related trace',()=>{
  const sample=rangedSample(2,102,2);
  for(const records of [[rangedSpawn(false),sample],[sample],
    [rangedSpawn(),{...sample,payload:{...sample.payload,data:{...sample.payload.data,ownerUuid:HIT_TARGET}}}],
    [rangedSpawn(),{...sample,payload:{...sample.payload,data:{...sample.payload.data,projectileClass:'OtherProjectile'}}}],
    [rangedSpawn(),{...sample,payload:{...sample.payload,data:{...sample.payload.data,spawnEventIndex:2}}}]]) {
    assert.equal(buildDebugWorkspaceRelatedProjectileTraces({observations:records,subjectUuid:UUID}).length,0);
  }
  const mismatched=rangedSample(2,102,2);mismatched.payload.data.ownerUuid=HIT_TARGET;
  assert.equal(validOriginalDecisionEvent(mismatched),false);
});
test('related projectile traces refuse context/revision mixing and retain removal as a terminal boundary',()=>{
  const spawn=rangedSpawn(),first=rangedSample(2,102,2),removed=rangedSample(3,103,3),late=rangedSample(4,104,4);
  removed.payload.data.removed=true;
  const result=buildDebugWorkspaceRelatedProjectileTraces({observations:[spawn,first,removed,late],subjectUuid:UUID});
  assert.equal(result[0].trace.samples.length,1);assert.deepEqual(result[0].terminal_source_observation_ids,['obs:ranged:3']);
  for(const mutation of [r=>r.runId='other',r=>r.arenaEpoch++,r=>r.processEpoch++,r=>r.payload.targetRevision++]) {
    const changed=structuredClone(first);mutation(changed);
    assert.throws(()=>buildDebugWorkspaceRelatedProjectileTraces({observations:[spawn,changed],subjectUuid:UUID}),/CONTEXT_CHANGED|SELECTION_CHANGED/);
  }
});
test('projectile dispatch and actual hurt return/health delta remain separate typed result facts',()=>{
  const dispatch=ranged('CONTROL_PROJECTILE_HIT_RETURN',{hitType:'ENTITY',targetUuid:HIT_TARGET,
    hitPosition:{x:3,y:65,z:2},dispatchScope:'BASE_PROJECTILE_ON_HIT_RETURN',damageOutcomeStatus:'NOT_EXPOSED'},2,102);
  assert.equal(validOriginalDecisionEvent(dispatch),true);
  for(const [result,before,after] of [[false,20,20],[true,20,20],[true,20,17]]) {
    const hurt=ranged('CONTROL_PROJECTILE_HURT_RETURN',{targetUuid:HIT_TARGET,result,requestedDamage:3,
      preCallObserverCostNanos:10,
      healthStatus:'AVAILABLE',healthBefore:before,healthAfter:after,healthDelta:before-after,
      healthScope:'BASE_LIVING_DATA_HEALTH_ACROSS_ORIGINAL_CALL',
      dispatchScope:'ARROW_OR_FIREBALL_ORIGINAL_ENTITY_HURT_CALL',damageReasonStatus:'NOT_EXPOSED'},3,102);
    assert.equal(validOriginalDecisionEvent(hurt),true);
    const decision=observeDebugWorkspaceDecision({observations:[rangedSpawn(),dispatch,hurt],subjectUuid:UUID});
    const fact=decision.stages.RESULT.facts.find(f=>f.key==='control_projectile_hurt_return');
    assert.equal(fact.value.result,result);assert.equal(fact.value.healthDelta,before-after);
    assert.deepEqual(fact.source_observation_ids,['obs:ranged:3']);
    hurt.payload.data.healthDelta=999;assert.equal(validOriginalDecisionEvent(hurt),false);
  }
  const malformed=structuredClone(dispatch);delete malformed.payload.data.targetUuid;
  assert.equal(validOriginalDecisionEvent(malformed),false);
});
test('retained presentation preserves the original successful teleport gap alongside bounded samples',()=>{
  const event=teleportReturn(true);
  const presentation=buildRetainedDecisionPresentation({observations:teleportRows(event),subjectUuid:UUID,
    identity:{debugSessionId:'sess-a',runId:'run-a',runSnapshotId:'snap-a',processEpoch:1,arenaEpoch:3,targetRevision:1},
    request:{startTick:100,endTick:105}});
  assert.equal(presentation.layers.motion.trace.segments.length,0);
  assert.equal(presentation.layers.motion.trace.gaps[0].kind,'EXPLICIT_TELEPORT');
});
test('related projectile presentation stays default OFF with a global finite sample budget and independent UUIDs',()=>{
  const second='00000000-0000-0000-0000-000000000004';
  const spawn2=rangedSpawn(),sample2=rangedSample(4,104,4);
  spawn2.payload.eventIndex=3;spawn2.payload.data.spawnEventIndex=3;spawn2.writerSeq=3;spawn2.observationId='obs:ranged:3';
  for(const r of [spawn2,sample2]){r.payload.data.projectileUuid=second;r.payload.data.spawnEventIndex=3;}
  const records=[rangedSpawn(),rangedSample(2,102,2),spawn2,sample2];
  const traces=buildDebugWorkspaceRelatedProjectileTraces({observations:records,subjectUuid:UUID,maxSamples:1});
  assert.equal(traces.reduce((n,t)=>n+t.trace.samples.length,0),1);assert.equal(traces[0].trace.subject.id,second);
  const presentation=buildRetainedDecisionPresentation({observations:records,subjectUuid:UUID,
    identity:{debugSessionId:'sess-a',runId:'run-a',runSnapshotId:'snap-a',processEpoch:1,arenaEpoch:3,targetRevision:1},
    request:{startTick:100,endTick:105}});
  assert.equal(presentation.layers.relatedProjectiles.enabledByDefault,false);
  assert.equal(presentation.layers.relatedProjectiles.traces.length,2);
  assert.equal(presentation.layers.motion.trace.samples.length,0);
});
test('ambiguous writer ordering and duplicate related observations do not fabricate projectile traces',()=>{
  const spawn=rangedSpawn(),sample=rangedSample(2,102,2);
  for(const mutation of [r=>r.writerId='',r=>delete r.writerSeq,r=>r.writerSeq=1,r=>r.writerId='different']) {
    const changed=structuredClone(sample);mutation(changed);
    assert.equal(buildDebugWorkspaceRelatedProjectileTraces({observations:[spawn,changed],subjectUuid:UUID}).length,0);
  }
  assert.throws(()=>buildDebugWorkspaceRelatedProjectileTraces({observations:[spawn,sample,structuredClone(sample)],subjectUuid:UUID}),/DUPLICATE_OBSERVATION/);
});

test('presentation retains pre-window spawn evidence while displaying only in-window stationary projectile samples',()=>{
  const spawn=rangedSpawn(),early=rangedSample(2,102,2),first=rangedSample(3,103,3),stopped=rangedSample(4,104,3),future=rangedSample(5,105,4);
  const records=[spawn,early,first,stopped,future],before=structuredClone(records);
  const identity={debugSessionId:'sess-a',runId:'run-a',runSnapshotId:'snap-a',processEpoch:1,arenaEpoch:3,targetRevision:1};
  const request={startTick:103,endTick:104};
  const direct=buildDebugWorkspaceRelatedProjectileTraces({observations:records,subjectUuid:UUID,identity,window:request});
  assert.equal(direct.length,1);
  const out=buildRetainedDecisionPresentation({observations:records,subjectUuid:UUID,identity,request});
  assert.equal(out.layers.relatedProjectiles.status,'PARTIAL');
  assert.deepEqual(out.layers.relatedProjectiles.traces,direct);
  assert.deepEqual(out.layers.relatedProjectiles.traces[0].spawn_source_observation_ids,[spawn.observationId]);
  assert.deepEqual(out.layers.relatedProjectiles.traces[0].trace.samples.map(s=>s.source_observation_id),[first.observationId,stopped.observationId]);
  assert.equal(out.layers.relatedProjectiles.traces[0].trace.segments.length,1);
  assert.ok(out.overview.timeline.every(event=>event.tick>=request.startTick&&event.tick<=request.endTick));
  assert.equal(out.layers.motion.trace.samples.length,0);assert.deepEqual(records,before);
});

test('pre-window projectile relationship evidence cannot cross identity, revision, source or subject boundaries',()=>{
  const sample=rangedSample(2,103,2);
  const identity={debugSessionId:'sess-a',runId:'run-a',runSnapshotId:'snap-a',processEpoch:1,arenaEpoch:3,targetRevision:1};
  for(const mutate of [r=>r.runId='other',r=>r.processEpoch++,r=>r.arenaEpoch++,r=>r.payload.targetRevision++,
    r=>r.source.side='CLIENT',r=>r.scope.entityUuid=HIT_TARGET,r=>r.payload.data.ownerUuid=HIT_TARGET,
    r=>r.gameTime=105,r=>r.payload.data.result=false]) {
    const spawn=rangedSpawn();mutate(spawn);
    const out=buildRetainedDecisionPresentation({observations:[spawn,sample],subjectUuid:UUID,identity,request:{startTick:103,endTick:104}});
    assert.equal(out.layers.relatedProjectiles.traces.length,0);
  }
});

test('pre-window removal remains a terminal boundary and cannot resurrect later projectile positions',()=>{
  const removed=rangedSample(2,102,2);removed.payload.data.removed=true;
  const out=buildRetainedDecisionPresentation({observations:[rangedSpawn(),removed,rangedSample(3,103,3)],subjectUuid:UUID,
    identity:{debugSessionId:'sess-a',runId:'run-a',runSnapshotId:'snap-a',processEpoch:1,arenaEpoch:3,targetRevision:1},
    request:{startTick:103,endTick:104}});
  assert.equal(out.layers.relatedProjectiles.traces.length,0);
});
test('actual successful original teleport return is a result and typed gap without a fabricated sample',()=>{
  const event=teleportReturn(true),records=teleportRows(event),before=structuredClone(records);
  assert.equal(validOriginalDecisionEvent(event),true);
  const decision=observeDebugWorkspaceDecision({observations:records,subjectUuid:UUID});
  assert.equal(decision.stages.RESULT.facts[0].key,'control_teleport_return');
  assert.equal(decision.stages.RESULT.facts[0].value.result,true);
  assert.equal(decision.stages.RESULT.facts[0].epistemic_status,'DIRECT_OBSERVED');
  assert.deepEqual(decision.stages.RESULT.facts[0].source_observation_ids,[event.observationId]);
  const trace=buildDebugWorkspaceMotionTrace({observations:records,subjectUuid:UUID});
  assert.equal(trace.samples.length,2);assert.equal(trace.segments.length,0);
  assert.equal(trace.gaps[0].kind,'EXPLICIT_TELEPORT');
  assert.equal(trace.gaps[0].source_observation_id,event.observationId);
  assert.deepEqual(records,before);
});
test('failed or malformed teleport attempts do not become successful trace discontinuities',()=>{
  const failed=teleportReturn(false);
  assert.equal(validOriginalDecisionEvent(failed),true);
  assert.equal(observeDebugWorkspaceDecision({observations:[failed],subjectUuid:UUID}).stages.RESULT.facts[0].value.result,false);
  assert.equal(buildDebugWorkspaceMotionTrace({observations:teleportRows(failed),subjectUuid:UUID}).segments.length,1);
  for(const corrupt of [d=>d.result='true',d=>delete d.returnedPosition.z,d=>d.requestedPosition.x=Infinity,
    d=>d.dispatchScope='FORGE_PRE_TELEPORT_EVENT',d=>d.reasonStatus='INFERRED']){
    const malformed=teleportReturn(true);corrupt(malformed.payload.data);
    assert.equal(validOriginalDecisionEvent(malformed),false);
    assert.equal(buildDebugWorkspaceMotionTrace({observations:teleportRows(malformed),subjectUuid:UUID}).segments.length,1);
  }
});
test('same-tick teleport is assigned only across points with explicit writer ordering',()=>{
  const event=teleportReturn(true,100);event.writerSeq=101;
  assert.equal(buildDebugWorkspaceMotionTrace({observations:teleportRows(event),subjectUuid:UUID}).gaps[0]?.kind,'EXPLICIT_TELEPORT');
  event.writerSeq=99;
  assert.equal(buildDebugWorkspaceMotionTrace({observations:teleportRows(event),subjectUuid:UUID}).segments.length,1);
  event.gameTime=105;event.writerSeq=104;
  assert.equal(buildDebugWorkspaceMotionTrace({observations:teleportRows(event),subjectUuid:UUID}).gaps[0]?.kind,'EXPLICIT_TELEPORT');
  event.writerSeq=106;
  assert.equal(buildDebugWorkspaceMotionTrace({observations:teleportRows(event),subjectUuid:UUID}).segments.length,1);
  event.writerSeq=104;event.writerId='different-server-writer';
  assert.equal(buildDebugWorkspaceMotionTrace({observations:teleportRows(event),subjectUuid:UUID}).segments.length,1);
  const unknownOrder=teleportRows(event);for(const r of unknownOrder)delete r.writerId;
  assert.equal(buildDebugWorkspaceMotionTrace({observations:unknownOrder,subjectUuid:UUID}).segments.length,1);
});
test('teleport records keep selected subject and run/revision identity fences',()=>{
  const other=teleportReturn(true);other.scope.entityUuid='another-mob';
  assert.equal(buildDebugWorkspaceMotionTrace({observations:teleportRows(other),subjectUuid:UUID}).segments.length,1);
  const mixed=teleportReturn(true);mixed.runId='another-run';
  assert.throws(()=>buildDebugWorkspaceMotionTrace({observations:teleportRows(mixed),subjectUuid:UUID}),/CONTEXT_CHANGED/);
  mixed.runId='run-a';mixed.payload.targetRevision=2;
  assert.throws(()=>buildDebugWorkspaceMotionTrace({observations:teleportRows(mixed),subjectUuid:UUID}),/SELECTION_CHANGED/);
});
const goalReturn=()=>original('GOAL_ELIGIBILITY_RETURN',{selector:'goal',instanceIdentity:'goal:1:1',
  instanceIdentityStatus:'AVAILABLE',goalClass:'ExampleGoal',priority:2,result:false,
  rejectionReasonStatus:'NOT_EXPOSED',callSiteStatus:'NOT_EXPOSED'});
test('original eligibility return is direct evidence without guessed reason or selection',()=>{
  const out=observeDebugWorkspaceDecision({observations:[goalReturn()],subjectUuid:UUID});
  assert.equal(out.capabilities.goal_eligibility.status,'PARTIAL');
  assert.equal(out.stages.EVALUATION.facts[0].value.result,false);
  assert.equal(out.stages.EVALUATION.facts[0].epistemic_status,'DIRECT_OBSERVED');
  assert.equal(out.stages.SELECTION,undefined);
  assert.equal(out.timeline[0].summary.rejectionReasonStatus,'NOT_EXPOSED');
  assert.deepEqual(out.timeline[0].source_observation_ids,['obs:AI_DECISION:121']);
});
test('post-search cache remains bounded algorithm state, not evaluated-neighbor or terrain proof',()=>{
  const record=original('PATH_SEARCH_STATE',{searchId:'search:1:1',frontier:{status:'PARTIAL',data:{
    nodes:[{x:0,y:64,z:0,g:0,h:1,f:1,costMalus:0,walkedDistance:0,pathType:'OPEN',
      openAtReturn:false,closedAtReturn:false,cacheRole:'OTHER_CACHED'}],cacheNodeCount:12,truncated:true,
    phase:'OUTER_BEFORE_DONE_AFTER_INNER_RETURN',neighborEvaluationTraceStatus:'NOT_EXPOSED',rejectionReasonStatus:'NOT_EXPOSED'}}});
  const out=observeDebugWorkspaceDecision({observations:[record],subjectUuid:UUID});
  assert.equal(out.capabilities.path_search_frontier.status,'PARTIAL');
  assert.equal(out.stages.EVALUATION.facts[0].epistemic_status,'INSTRUMENTED_ALGORITHM_STATE');
  assert.equal(out.stages.EVALUATION.facts[0].value.frontier.data.nodes[0].cacheRole,'OTHER_CACHED');
  assert.equal(out.stages.CANDIDATE,undefined);
});
test('malformed deep events are excluded without promoting capabilities',()=>{
  for(const change of [r=>r.payload.eventIndex=257,r=>r.payload.data.result='false',
    r=>r.payload.data.rejectionReasonStatus='AVAILABLE',r=>r.payload.semantics='REPLAYED',
    r=>r.payload.data.extra='x'.repeat(513),r=>r.source.side='CLIENT',r=>r.payload.kind='INVENTED_CAUSE']) {
    const record=goalReturn();change(record);
    const out=observeDebugWorkspaceDecision({observations:[record],subjectUuid:UUID});
    assert.equal(out.capabilities.goal_eligibility.status,'NOT_EXPOSED');
    assert.equal(out.timeline.length,0);
  }
});
test('deep events retain full run/process/Arena and selection fences',()=>{
  const first=goalReturn(),second=goalReturn();second.observationId+=':other';second.processEpoch=2;
  assert.throws(()=>observeDebugWorkspaceDecision({observations:[first,second],subjectUuid:UUID}),/CONTEXT_CHANGED/);
  second.processEpoch=1;second.payload.targetRevision=2;
  assert.throws(()=>observeDebugWorkspaceDecision({observations:[first,second],subjectUuid:UUID}),/SELECTION_CHANGED/);
});

test('existing exact-subject lanes populate conservative DecisionObservation stages',()=>{
  const out=observeDebugWorkspaceDecision({observations:rows,subjectUuid:UUID,subjectType:'touhou_little_maid:maid',tick:105});
  assert.equal(out.subject.id,UUID);
  assert.equal(out.capabilities.server_entity_state.status,'AVAILABLE');
  assert.equal(out.capabilities.ai_target.status,'AVAILABLE');
  assert.equal(out.capabilities.brain_memory.status,'AVAILABLE');
  assert.equal(out.capabilities.navigation.status,'AVAILABLE');
  assert.equal(out.capabilities.goal_scheduler.status,'NOT_EXPOSED');
  assert.equal(out.capabilities.path_search_frontier.status,'NOT_EXPOSED');
  assert.equal(out.stages.STATE.facts.every(f=>f.epistemic_status==='SAMPLED_OBSERVED'),true);
  assert.equal(out.stages.EXECUTION.facts.some(f=>f.key==='navigation'),true);
});

test('sampled behavior transition remains derived temporal association with unknown reason',()=>{
  const out=observeDebugWorkspaceDecision({observations:rows,subjectUuid:UUID,tick:105});
  assert.equal(out.timeline.length,1);
  assert.equal(out.timeline[0].epistemic_status,'DERIVED_FROM_OBSERVED');
  assert.equal(out.timeline[0].causal_relation,'TEMPORAL_ASSOCIATION');
  assert.equal(out.timeline[0].summary.exactTransitionTickKnown,false);
  assert.equal(out.timeline[0].summary.reasonKnown,false);
});

test('adapter refuses to combine exact subject records across arena identity',()=>{
  const mixed=[...rows,obs('SERVER_ENTITY_STATE',110,{x:3,y:64,z:2},{arenaEpoch:4,observationId:'obs:mixed'})];
  assert.throws(()=>observeDebugWorkspaceDecision({observations:mixed,subjectUuid:UUID,tick:110}),/DECISION_EVIDENCE_CONTEXT_CHANGED/);
});

test('Debug Workspace SERVER_ENTITY_STATE can feed the common sampled motion contract',()=>{
  const trace=buildDebugWorkspaceMotionTrace({
    observations:rows,subjectUuid:UUID,subjectType:'touhou_little_maid:maid',
    window:{start_tick:100,end_tick:105},
  });
  assert.equal(trace.trace_class,'MOB_ACTUAL');
  assert.equal(trace.samples.length,2);
  assert.equal(trace.samples[0].source_observation_id,'obs:SERVER_ENTITY_STATE:100');
  assert.equal(trace.samples[1].source_kind,'DEBUG_WORKSPACE_SERVER_ENTITY_STATE');
  assert.equal(trace.segments.length,1);
  assert.equal(trace.semantics.continuous_path_claimed,false);
});

test('other entity records are excluded by exact UUID scope',()=>{
  const other={...obs('AI_TARGET',101,{present:false}),observationId:'obs:other',scope:{kind:'ENTITY_UUID',entityUuid:'00000000-0000-0000-0000-000000000099'}};
  const out=observeDebugWorkspaceDecision({observations:[...rows,other],subjectUuid:UUID,tick:105});
  assert.equal(out.timeline.length,1);
  assert.equal(out.stages.STATE.facts.find(f=>f.key==='mob_target').value.present,true);
});

test('incomplete or non-observed rows are not promoted into sampled decision evidence',()=>{
  const incomplete={...obs('AI_TARGET',106,{present:false}),observationId:'obs:incomplete',completeness:{complete:false}};
  const inferred={...obs('NAVIGATION',106,{pathPresent:true}),observationId:'obs:inferred',epistemicStatus:'INFERRED'};
  const out=observeDebugWorkspaceDecision({observations:[incomplete,inferred],subjectUuid:UUID,tick:106});
  assert.equal(out.capabilities.ai_target.status,'NOT_CAPTURED');
  assert.equal(out.capabilities.navigation.status,'NOT_CAPTURED');
  assert.equal(out.stages.STATE,undefined);
  assert.equal(out.stages.EXECUTION,undefined);
});

function decisionSnapshot(revision=1, extra={}) {
  return obs('AI_DECISION',110,{
    schema:'kneekura.vanilla-decision-snapshot/v1',targetRevision:revision,
    semantics:'MOB_COMPONENT_SNAPSHOT_ONLY',
    sections:{
      goal_scheduler:{status:'AVAILABLE',data:{goal:{entries:[{instanceIdentity:'goal:1:1',priority:2,running:true}],truncated:false},target:{entries:[],truncated:false}}},
      brain_memory:{status:'AVAILABLE',data:{entries:[{key:'minecraft:walk_target',registered:true,present:false}],truncated:false}},
      brain_activities:{status:'NOT_EXPOSED',detail:'accessor unavailable'},
      navigation_path:{status:'PARTIAL',data:{entries:[{index:0,x:3,y:64,z:5}],truncated:true}},
      movement_control:{status:'AVAILABLE',data:{move:{className:'CustomMove',fieldScope:'BASE_CONTROL_FIELDS_ONLY'}}},
    },...extra,
  });
}

test('versioned snapshot exposes component state without eligibility or frontier claims',()=>{
  const out=observeDebugWorkspaceDecision({observations:[decisionSnapshot()],subjectUuid:UUID});
  assert.equal(out.capabilities.goal_scheduler.status,'AVAILABLE');
  assert.equal(out.capabilities.goal_eligibility.status,'NOT_EXPOSED');
  assert.equal(out.capabilities.navigation_path.status,'PARTIAL');
  assert.equal(out.capabilities.brain_activities.status,'NOT_EXPOSED');
  assert.equal(out.capabilities.path_search_frontier.status,'NOT_EXPOSED');
  const f=out.stages.STATE.facts.find(f=>f.key==='goal_scheduler');
  assert.deepEqual(f.source_observation_ids,['obs:AI_DECISION:110']);
  assert.equal(f.epistemic_status,'SAMPLED_OBSERVED');
  assert.equal(out.stages.CANDIDATE,undefined);
  assert.equal(out.stages.EVALUATION,undefined);
  assert.equal(out.available_drilldowns.includes('goal_scheduler'),true);
});

test('snapshot revisions fence reselection instead of joining separate selections',()=>{
  const a=decisionSnapshot(1);
  const b={...decisionSnapshot(2),gameTime:115,observationId:'obs:new-selection'};
  assert.throws(()=>observeDebugWorkspaceDecision({observations:[a,b],subjectUuid:UUID}),/DECISION_SELECTION_CHANGED/);
});

test('foreign, invalid and oversized snapshot payloads never become component evidence',()=>{
  for(const payload of [
    {schema:'other/v1'},
    {...decisionSnapshot().payload,targetRevision:0},
    {...decisionSnapshot().payload,sections:{goal_scheduler:{status:'AVAILABLE',data:{entries:Array(65).fill({})}}}},
    {...decisionSnapshot().payload,padding:'x'.repeat(65537)},
  ]) {
    const out=observeDebugWorkspaceDecision({observations:[obs('AI_DECISION',110,payload)],subjectUuid:UUID});
    assert.equal(out.capabilities.goal_scheduler.status,'NOT_EXPOSED');
    assert.equal(out.stages.STATE,undefined);
  }
});

test('Goal running-set changes cite both samples and never invent transition tick or reason',()=>{
  const a=decisionSnapshot();
  const b=structuredClone(a);
  b.gameTime=115;b.observationId='obs:goal-stopped';
  b.payload.sections.goal_scheduler.data.goal.entries[0].running=false;
  const out=observeDebugWorkspaceDecision({observations:[a,b],subjectUuid:UUID});
  assert.equal(out.timeline.length,1);
  assert.equal(out.timeline[0].kind,'GOAL_RUNNING_SET_CHANGED_BETWEEN_SAMPLES');
  assert.deepEqual(out.timeline[0].source_observation_ids,[a.observationId,b.observationId]);
  assert.deepEqual(out.timeline[0].summary.interval,{start_tick:110,end_tick:115});
  assert.equal(out.timeline[0].summary.exactTransitionTickKnown,false);
  assert.equal(out.timeline[0].summary.reasonKnown,false);
  assert.equal(out.timeline[0].causal_relation,'TEMPORAL_ASSOCIATION');
  b.payload.sections.goal_scheduler.status='PARTIAL';
  assert.equal(observeDebugWorkspaceDecision({observations:[a,b],subjectUuid:UUID}).timeline.length,0);
});
