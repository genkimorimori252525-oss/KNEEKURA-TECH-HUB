import test from 'node:test';
import assert from 'node:assert/strict';
import { createDecisionObservation, buildDecisionPacket, DECISION_OBSERVATION_V1 } from '../decision-observation.mjs';

const base = () => ({
  subject: { id: 'zombie-1', type: 'minecraft:zombie' },
  identity: { run_id: 'run-a', arena_id: 'arena-a', arena_epoch: 1, tick: 420 },
  adapter: { id: 'vanilla:generic_mob', version: '1', family: 'GENERIC_MOB' },
});

test('DecisionObservationModel v1 allows partial stages and explicit unavailable capability', () => {
  const observation = createDecisionObservation({
    ...base(),
    capabilities: {
      target: { status: 'AVAILABLE', source_observation_ids: ['obs-target'] },
      goal_scheduler: { status: 'NOT_CAPTURED', detail: 'deep capture was not armed' },
      path_search_frontier: { status: 'NOT_EXPOSED' },
    },
    stages: {
      STATE: { facts: [{
        key: 'target',
        value: 'player-1',
        epistemic_status: 'DIRECT_OBSERVED',
        causal_relation: 'DIRECT_RUNTIME_RELATION',
        source_observation_ids: ['obs-target'],
      }] },
      EXECUTION: { facts: [{
        key: 'position',
        value: {x:1,y:64,z:2},
        epistemic_status: 'SAMPLED_OBSERVED',
        source_observation_ids: ['obs-pos'],
      }] },
    },
    availableDrilldowns: ['motion_trace', 'goal_transitions'],
  });
  assert.equal(observation.schema, DECISION_OBSERVATION_V1.observationSchema);
  assert.equal(observation.stages.CANDIDATE, undefined);
  assert.equal(observation.capabilities.goal_scheduler.status, 'NOT_CAPTURED');
  assert.equal(observation.semantics.mind_reading_claims_permitted, false);
});

test('strong direct or algorithm claims require source identity', () => {
  assert.throws(() => createDecisionObservation({
    ...base(),
    stages: { STATE: { facts: [{
      key: 'target', value: 'player-1',
      epistemic_status: 'DIRECT_OBSERVED',
      causal_relation: 'DIRECT_RUNTIME_RELATION',
    }] } },
  }), /requires at least one source_observation_id/);
});

test('temporal adjacency remains temporal association in the packet', () => {
  const observation = createDecisionObservation({
    ...base(),
    timeline: [
      { tick: 400, kind: 'GOAL_START', stage: 'SELECTION', epistemic_status: 'SAMPLED_OBSERVED', causal_relation: 'TEMPORAL_ASSOCIATION', source_observation_ids: ['goal-400'] },
      { tick: 405, kind: 'PATH_SELECTED', stage: 'EXECUTION', epistemic_status: 'INSTRUMENTED_ALGORITHM_STATE', causal_relation: 'ALGORITHM_TRACE_RELATION', source_observation_ids: ['path-405'] },
      { tick: 410, kind: 'MOVED', stage: 'RESULT', epistemic_status: 'SAMPLED_OBSERVED', causal_relation: 'TEMPORAL_ASSOCIATION', source_observation_ids: ['pos-410'] },
    ],
  });
  const packet = buildDecisionPacket(observation);
  assert.equal(packet.timeline[0].causal_relation, 'TEMPORAL_ASSOCIATION');
  assert.equal(packet.timeline[2].causal_relation, 'TEMPORAL_ASSOCIATION');
  assert.equal(packet.semantics.temporal_adjacency_is_not_causality, true);
});

test('unknown MOD AI can be represented without forcing Vanilla Goal/Path semantics', () => {
  const observation = createDecisionObservation({
    subject: { id: 'mod-mob', type: 'example:custom_boss', mod_id: 'example' },
    identity: { run_id: 'run-b' },
    adapter: { id: 'generic:fallback', version: '1', family: 'CUSTOM_UNKNOWN' },
    capabilities: {
      position: { status: 'AVAILABLE', source_observation_ids: ['pos-1'] },
      vanilla_goal: { status: 'NOT_APPLICABLE' },
      vanilla_path: { status: 'NOT_APPLICABLE' },
      custom_decision: { status: 'NOT_EXPOSED' },
    },
    stages: {
      RESULT: { facts: [{
        key: 'position',
        value: {x:0,y:80,z:0},
        epistemic_status: 'SAMPLED_OBSERVED',
        source_observation_ids: ['pos-1'],
      }] },
    },
  });
  assert.equal(observation.capabilities.vanilla_goal.status, 'NOT_APPLICABLE');
  assert.equal(observation.capabilities.custom_decision.status, 'NOT_EXPOSED');
  assert.equal(observation.stages.SELECTION, undefined);
});

test('packet timeline is bounded without changing observation history', () => {
  const timeline = Array.from({length: 5}, (_, i) => ({
    tick: i,
    kind: 'EVENT_' + i,
    epistemic_status: 'SAMPLED_OBSERVED',
    source_observation_ids: ['e-' + i],
  }));
  const observation = createDecisionObservation({...base(), timeline});
  const packet = buildDecisionPacket(observation, {timelineLimit: 2});
  assert.deepEqual(packet.timeline.map(e => e.tick), [3,4]);
  assert.equal(observation.timeline.length, 5);
});
