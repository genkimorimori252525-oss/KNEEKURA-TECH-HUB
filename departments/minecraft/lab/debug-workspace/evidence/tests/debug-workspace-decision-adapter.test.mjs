import test from 'node:test';
import assert from 'node:assert/strict';
import {
  observeDebugWorkspaceDecision,
  buildDebugWorkspaceMotionTrace,
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
