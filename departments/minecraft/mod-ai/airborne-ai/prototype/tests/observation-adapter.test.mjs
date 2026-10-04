import test from 'node:test';
import assert from 'node:assert/strict';
import { TierAHeroFlyer } from '../tier-a.mjs';
import { TierBCommonFlyer } from '../tier-b.mjs';
import {
  AIRBORNE_MODEL_OBSERVATION_SCHEMA,
  createAirborneModelObservation,
  createAirborneModelPacket,
} from '../observation-adapter.mjs';

function allFacts(observation) {
  return Object.values(observation.stages).flatMap(stage => stage.facts ?? []);
}

function fact(observation, key) {
  return allFacts(observation).find(row => row.key === key);
}

function assertDeepFrozen(value) {
  if (!value || typeof value !== 'object') return;
  assert.equal(Object.isFrozen(value), true);
  for (const child of Object.values(value)) assertDeepFrozen(child);
}

test('Tier A model observation is distinct from runtime Decision evidence', () => {
  const flyer = new TierAHeroFlyer({ selfId: 'hero', position: [0, 80, 0] });
  flyer.issueIntent({ purpose: 'CHASE', targetPosition: [10, 90, 0], targetId: 'target' });
  flyer.planRoute({ directClear: true });
  const observation = createAirborneModelObservation(flyer.snapshot(), { tier: 'A', tick: 12 });

  assert.equal(observation.schema, AIRBORNE_MODEL_OBSERVATION_SCHEMA);
  assert.notEqual(observation.schema, 'kneekura.mod-decision-snapshot/v1');
  assert.equal(observation.semantics.source_semantics, 'OFFLINE_MODEL_STATE_ONLY');
  assert.equal(observation.semantics.runtime_evidence, false);
  assert.equal(observation.semantics.retained_evidence, false);
  assert.equal(observation.semantics.future_runtime_mapping_requires_source_proven_adapter, true);
  assert.equal(observation.identity.run_id, null);
  assert.equal(observation.identity.world_id, null);
});

test('adapter is read-only and does not mutate Tier A snapshot', () => {
  const flyer = new TierAHeroFlyer({ selfId: 'hero', position: [0, 80, 0] });
  flyer.issueIntent({ purpose: 'CRUISE', targetPosition: [4, 85, 2] });
  const snapshot = flyer.snapshot();
  const before = structuredClone(snapshot);
  createAirborneModelObservation(snapshot, { tier: 'A' });
  assert.deepEqual(snapshot, before);
  assert.deepEqual(flyer.snapshot(), before);
});

test('adapter output and packet are deeply frozen', () => {
  const flyer = new TierBCommonFlyer({ selfId: 'mob', position: [0, 70, 0] });
  flyer.setTarget({ targetId: 'target', position: [10, 70, 0] });
  flyer.tickCombat({ collisionClear: true });
  const observation = createAirborneModelObservation(flyer.snapshot(), { tier: 'B' });
  const packet = createAirborneModelPacket(observation);
  assertDeepFrozen(observation);
  assertDeepFrozen(packet);
  assert.throws(() => { packet.subject.id = 'changed'; }, TypeError);
});

test('all seven Decision vocabulary stages are retained without invented evidence', () => {
  const flyer = new TierAHeroFlyer({ selfId: 'hero' });
  const observation = createAirborneModelObservation(flyer.snapshot(), { tier: 'A' });
  assert.deepEqual(
    Object.keys(observation.stages),
    ['INPUT', 'STATE', 'CANDIDATE', 'EVALUATION', 'SELECTION', 'EXECUTION', 'RESULT'],
  );
  for (const row of allFacts(observation)) {
    assert.equal(row.runtime_epistemic_status, 'NOT_RUNTIME_EVIDENCE');
    assert.equal(row.causal_relation, 'NO_RUNTIME_CAUSALITY_CLAIM');
    assert.deepEqual(row.source_observation_ids, []);
  }
});

test('Tier A route mode stays a model route and never claims Minecraft navigation adoption', () => {
  const flyer = new TierAHeroFlyer({ selfId: 'hero' });
  flyer.issueIntent({ purpose: 'CHASE', targetPosition: [8, 84, 0], targetId: 'target' });
  flyer.planRoute({ directClear: true });
  const observation = createAirborneModelObservation(flyer.snapshot(), { tier: 'A' });
  const route = fact(observation, 'airborne:route_mode');
  assert.equal(route.value, 'DIRECT');
  assert.match(route.note, /MODEL_ROUTE_MODE_NOT_DECLARED_MINECRAFT_NAVIGATION/);
  assert.equal(observation.capabilities['airborne:actual_motion'].status, 'NOT_MODELED');
});

test('Tier A missing visibility remains NOT_MODELED rather than invented false', () => {
  const flyer = new TierAHeroFlyer({ selfId: 'hero' });
  const observation = createAirborneModelObservation(flyer.snapshot(), { tier: 'A' });
  const visible = fact(observation, 'airborne:target_visible');
  assert.equal(visible.value, null);
  assert.equal(visible.model_status, 'NOT_MODELED');
});

test('Tier B explicitly marks route, landing and LOS memory as unavailable in the model', () => {
  const flyer = new TierBCommonFlyer({ selfId: 'mob' });
  const observation = createAirborneModelObservation(flyer.snapshot(), { tier: 'B' });
  assert.equal(observation.capabilities['airborne:route'].status, 'NOT_APPLICABLE');
  assert.equal(observation.capabilities['airborne:landing'].status, 'NOT_APPLICABLE');
  assert.equal(observation.capabilities['airborne:target_memory'].status, 'NOT_MODELED');
  assert.equal(observation.capabilities['airborne:air_ground_state'].status, 'NOT_APPLICABLE');
});

test('Tier B command velocity is not promoted to actual motion', () => {
  const flyer = new TierBCommonFlyer({ selfId: 'mob', chaseSpeed: 0.5 });
  flyer.setTarget({ targetId: 'target', position: [10, 70, 0] });
  flyer.tickCombat({ collisionClear: true });
  const observation = createAirborneModelObservation(flyer.snapshot(), { tier: 'B' });
  const velocity = fact(observation, 'airborne:command_velocity');
  assert.deepEqual(velocity.value, [0.5, 0, 0]);
  assert.match(velocity.note, /MODEL_COMMAND_NOT_ACTUAL_MOTION/);
  assert.equal(observation.semantics.command_velocity_proves_actual_motion, false);
});

test('unretained Tier B collision probe remains UNKNOWN', () => {
  const flyer = new TierBCommonFlyer({ selfId: 'mob' });
  const observation = createAirborneModelObservation(flyer.snapshot(), { tier: 'B' });
  const probe = fact(observation, 'airborne:collision_probe_result');
  assert.equal(probe.value, null);
  assert.equal(probe.model_status, 'UNKNOWN');
  assert.match(probe.note, /NOT_RETAINED/);
});

test('adapter refuses malformed non-finite snapshot data instead of sanitizing it', () => {
  const flyer = new TierBCommonFlyer({ selfId: 'mob' });
  const snapshot = { ...flyer.snapshot(), velocity: [0, Number.NaN, 0] };
  assert.throws(() => createAirborneModelObservation(snapshot, { tier: 'B' }), /finite/);
});

test('adapter requires an explicit supported tier', () => {
  const flyer = new TierAHeroFlyer({ selfId: 'hero' });
  assert.throws(() => createAirborneModelObservation(flyer.snapshot(), { tier: 'C' }), /tier must be A or B/);
});
