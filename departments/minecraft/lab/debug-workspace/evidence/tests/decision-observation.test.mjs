import assert from 'node:assert/strict';
import test from 'node:test';
import {
  DECISION_STAGES,buildDecisionObservationModel,buildDecisionObservationPacket,
  assertSameDecisionIdentity
} from '../decision-observation.mjs';

const identity={debugSessionId:'session',runId:'run',runSnapshotId:'snapshot',processEpoch:1,
  arenaId:'arena',arenaEpoch:2,arenaRevision:3,resourceEpoch:0,
  entityUuid:'00000000-0000-4000-8000-000000000001',entityType:'minecraft:zombie',
  gameTime:420,observedAt:'2026-10-03T00:00:00.000Z'};
const adapter={id:'kneekura:generic_mob',version:1,minecraftVersion:'1.20.1',loader:'forge',
  instrumentation:'existing LAB observations',observerEffectRisk:'LOW_BASELINE'};
const caps={target:'DIRECT',scheduler:'NOT_EXPOSED',running_actions:'NOT_EXPOSED',
  candidate_actions:'NOT_EXPOSED',candidate_scores:'NOT_EXPOSED',rejection_reason:'NOT_EXPOSED',
  navigation:'DIRECT',search_frontier:'CAPTURE_REQUIRED',result_motion_trace:'AVAILABLE'};

test('neutral stages are optional, canonical ordered and source-bound',()=>{
  const m=buildDecisionObservationModel({identity,adapter,capabilities:caps,stages:[
    {stage:'RESULT',epistemicStatus:'SAMPLED_OBSERVED',facts:{position:[4,64,2]},sourceIds:['motion:1']},
    {stage:'STATE',epistemicStatus:'DIRECT_OBSERVED',facts:{targetUuid:'player'},sourceIds:['obs:target']},
  ]});
  assert.deepEqual(m.stages.map(x=>x.stage),['STATE','RESULT']);
  assert.equal(m.policy.allStagesOptional,true); assert.equal(m.policy.motivesInferred,false);
  assert.deepEqual(DECISION_STAGES,['INPUT','STATE','CANDIDATE','EVALUATION','SELECTION','EXECUTION','RESULT']);
});

test('partial and unavailable capabilities remain explicit in packet',()=>{
  const m=buildDecisionObservationModel({identity,adapter,capabilities:{target:'DIRECT',scheduler:'PARTIAL',
    candidate_scores:'NOT_EXPOSED',search_frontier:'NOT_CAPTURED',brain:'NOT_APPLICABLE'},stages:[]});
  const p=buildDecisionObservationPacket(m);
  assert.equal(p.capabilitySummary.available.scheduler,'PARTIAL');
  assert.equal(p.capabilitySummary.unavailable.candidate_scores,'NOT_EXPOSED');
  assert.equal(p.capabilitySummary.unavailable.search_frontier,'NOT_CAPTURED');
  assert.equal(p.capabilitySummary.unavailable.brain,'NOT_APPLICABLE');
});

test('runtime model rejects community hypothesis as runtime truth',()=>{
  assert.throws(()=>buildDecisionObservationModel({identity,adapter,capabilities:caps,stages:[
    {stage:'EVALUATION',epistemicStatus:'COMMUNITY_HYPOTHESIS',facts:{reason:'probably afraid'},sourceIds:['forum:1']}
  ]}),/research-only/);
});

test('observed stage requires exact source IDs while unavailable stage may be empty',()=>{
  assert.throws(()=>buildDecisionObservationModel({identity,adapter,capabilities:caps,stages:[
    {stage:'STATE',epistemicStatus:'DIRECT_OBSERVED',facts:{target:'x'},sourceIds:[]}
  ]}),/requires sourceIds/);
  const m=buildDecisionObservationModel({identity,adapter,capabilities:caps,stages:[
    {stage:'CANDIDATE',epistemicStatus:'NOT_EXPOSED',facts:{},sourceIds:[]}
  ]});
  assert.equal(m.stages[0].epistemicStatus,'NOT_EXPOSED');
});

test('temporal association stays temporal and packet never invents because/motive',()=>{
  const m=buildDecisionObservationModel({identity,adapter,capabilities:caps,
    stages:[
      {stage:'EXECUTION',epistemicStatus:'DIRECT_OBSERVED',facts:{event:'Goal A START'},sourceIds:['obs:goal']},
      {stage:'RESULT',epistemicStatus:'SAMPLED_OBSERVED',facts:{event:'Mob moved'},sourceIds:['motion:1']}
    ],
    relations:[{relationId:'r1',fromRef:'obs:goal',toRef:'motion:1',semantics:'TEMPORAL_ASSOCIATION',
      epistemicStatus:'DERIVED_FROM_OBSERVED',sourceIds:['obs:goal','motion:1']}]
  });
  const p=buildDecisionObservationPacket(m);
  assert.equal(p.relations[0].semantics,'TEMPORAL_ASSOCIATION');
  assert.equal(p.policy.causalNarrativeGenerated,false); assert.equal(p.policy.motivesInferred,false);
  assert.equal(JSON.stringify(p).includes('because'),false);
});

test('algorithm trace relation is preserved only as declared semantics',()=>{
  const m=buildDecisionObservationModel({identity,adapter,capabilities:caps,stages:[
    {stage:'SELECTION',epistemicStatus:'INSTRUMENTED_ALGORITHM_STATE',facts:{selected:'path:17'},sourceIds:['trace:path:17']}
  ],relations:[{relationId:'r1',fromRef:'candidate:4',toRef:'path:17',semantics:'ALGORITHM_TRACE_RELATION',
    epistemicStatus:'INSTRUMENTED_ALGORITHM_STATE',sourceIds:['trace:path:17']}]});
  assert.equal(buildDecisionObservationPacket(m).relations[0].semantics,'ALGORITHM_TRACE_RELATION');
});

test('shared visual primitives keep epistemic status and evidence IDs',()=>{
  const m=buildDecisionObservationModel({identity,adapter,capabilities:caps,stages:[],visualPrimitives:[
    {primitiveId:'target',type:'POINT',epistemicStatus:'DIRECT_OBSERVED',sourceIds:['obs:target'],
      payload:{position:[1,64,1]},label:'current target'},
    {primitiveId:'path',type:'PATH',epistemicStatus:'SAMPLED_OBSERVED',sourceIds:['obs:path'],
      payload:{points:[[0,64,0],[1,64,1]]}}
  ]});
  const p=buildDecisionObservationPacket(m);
  assert.deepEqual(p.visualPrimitives.map(x=>x.type),['POINT','PATH']);
  assert.deepEqual(p.provenance.sourceIds,['obs:target','obs:path']);
});

test('packet is bounded and advertises drill-down only from declared capabilities',()=>{
  const m=buildDecisionObservationModel({identity,adapter,capabilities:caps,stages:[
    {stage:'STATE',epistemicStatus:'DIRECT_OBSERVED',facts:{target:'player'},sourceIds:['obs:target']},
    {stage:'RESULT',epistemicStatus:'SAMPLED_OBSERVED',facts:{moved:true},sourceIds:['motion:1']}
  ]});
  const p=buildDecisionObservationPacket(m,{maxStages:1});
  assert.equal(p.structuredState.length,1); assert.equal(p.truncation.stages,1);
  assert.ok(p.availableDrillDownChannels.includes('search_frontier'));
  assert.ok(!p.availableDrillDownChannels.includes('candidate_scores'));
  assert.equal(p.policy.screenshotsPrimaryInput,false);
});

test('identity guard rejects cross-run/epoch/entity mixing',()=>{
  assert.equal(assertSameDecisionIdentity(identity,{...identity}),true);
  assert.throws(()=>assertSameDecisionIdentity(identity,{...identity,arenaEpoch:3}),/identity mismatch/);
  assert.throws(()=>assertSameDecisionIdentity(identity,{...identity,runId:'other'}),/identity mismatch/);
  assert.throws(()=>assertSameDecisionIdentity(identity,{...identity,entityUuid:'00000000-0000-4000-8000-000000000099'}),/identity mismatch/);
});
