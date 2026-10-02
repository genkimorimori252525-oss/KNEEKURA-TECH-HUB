import test from 'node:test';
import assert from 'node:assert/strict';
import { buildSampledMotionTrace, buildTraceFromSimStore, motionTraceAvailability, MOTION_TRACE_V1 } from './motion-trace.mjs';

const obs = (tick, x, y=64, z=0, extra={}) => ({
  tick, x, y, z,
  source_observation_id: 'obs-' + tick,
  source_kind: 'TEST_POSITION',
  run_id: 'run-a',
  arena_id: 'arena-a',
  arena_epoch: 1,
  world_id: 'world-a',
  dimension_id: 'minecraft:overworld',
  ...extra,
});

test('SampledMotionTrace v1 preserves source identity and derives bounded metrics', () => {
  const trace = buildSampledMotionTrace({
    traceClass: 'MOB_ACTUAL',
    subject: { id: 'mob-1', type: 'minecraft:zombie' },
    observations: [obs(10,0), obs(11,3), obs(12,3,68,4,{vx:0,vy:1,vz:1})],
  });
  assert.equal(trace.schema, MOTION_TRACE_V1.schema);
  assert.equal(trace.epistemic_status, 'DERIVED_FROM_SAMPLED_OBSERVATIONS');
  assert.equal(trace.samples.length, 3);
  assert.equal(trace.segments.length, 2);
  assert.equal(trace.segments[0].semantics, 'SAMPLED_ENDPOINT_CONNECTION');
  assert.equal(trace.semantics.continuous_path_claimed, false);
  assert.deepEqual(trace.source_observation_ids, ['obs-10','obs-11','obs-12']);
  assert.equal(trace.metrics.sampled_polyline_length, 8);
  assert.equal(trace.metrics.net_displacement, Math.sqrt(41));
  assert.equal(trace.metrics.min_altitude, 64);
  assert.equal(trace.metrics.max_altitude, 68);
  assert.equal(trace.metrics.speed.observed_sample_count, 1);
});

test('source gap creates a visible break instead of an interpolated segment', () => {
  const trace = buildSampledMotionTrace({
    traceClass: 'PROJECTILE_ACTUAL',
    subject: { id: 'p-1' },
    observations: [obs(1,0), obs(4,4)],
    maxGapTicks: 1,
  });
  assert.equal(trace.segments.length, 0);
  assert.equal(trace.gaps.length, 1);
  assert.equal(trace.gaps[0].kind, 'SOURCE_GAP');
  assert.equal(trace.metrics.sampled_polyline_length, 0);
});

test('identity boundary is never bridged', () => {
  const trace = buildSampledMotionTrace({
    traceClass: 'MOB_ACTUAL',
    subject: { id: 'mob-1' },
    observations: [obs(1,0), obs(2,1,64,0,{arena_epoch:2})],
  });
  assert.equal(trace.segments.length, 0);
  assert.equal(trace.gaps[0].kind, 'IDENTITY_BOUNDARY');
});

test('typed teleport stays a discontinuity marker and is not normal movement', () => {
  const trace = buildSampledMotionTrace({
    traceClass: 'MOB_ACTUAL',
    subject: { id: 'mob-1' },
    observations: [obs(1,0), obs(2,20)],
    explicitDiscontinuities: [{
      after_tick: 1, before_tick: 2, kind: 'EXPLICIT_TELEPORT',
      source_observation_id: 'action-teleport-1',
    }],
  });
  assert.equal(trace.segments.length, 0);
  assert.equal(trace.gaps[0].kind, 'EXPLICIT_TELEPORT');
  assert.equal(trace.gaps[0].source_observation_id, 'action-teleport-1');
});

test('SimStore adapter requires retained sample access and never falls back to forward-filled at(t)', () => {
  const bad = { trackOf(){ return {t0:0,t1:1,at(){ return obs(0,0); }}; } };
  assert.throws(() => buildTraceFromSimStore({store:bad,entityId:1,traceClass:'MOB_ACTUAL'}), /SIMSTORE_RETAINED_SAMPLES_UNAVAILABLE/);
});

test('SimStore adapter consumes only retained samples', () => {
  const samples=[obs(5,0),obs(6,1)];
  const entities=new Map([[7,{id:7,type:'minecraft:zombie',role:'target'}]]);
  const store={
    entities,
    trackOf(id){ assert.equal(id,7); return {t0:5,t1:6,samples(){ return samples; }}; },
  };
  const trace=buildTraceFromSimStore({store,entityId:7,traceClass:'MOB_ACTUAL'});
  assert.equal(trace.samples.length,2);
  assert.equal(trace.subject.type,'minecraft:zombie');
  assert.equal(trace.segments.length,1);
  assert.equal(motionTraceAvailability(store)[0].trace_class,'MOB_ACTUAL');
});

test('duplicate ticks are rejected rather than silently choosing an observation', () => {
  assert.throws(() => buildSampledMotionTrace({
    traceClass:'MOB_ACTUAL', subject:{id:'x'}, observations:[obs(1,0), {...obs(1,1), source_observation_id:'other'}],
  }), /duplicate motion observation tick/);
});
