const TRACE_SCHEMA = 'kneekura.sampled-motion-trace/v1';
const TRACE_CLASSES = Object.freeze(['MOB_ACTUAL', 'PROJECTILE_ACTUAL', 'NAVIGATION_DECLARED']);
const TRACE_EPISTEMIC = 'DERIVED_FROM_SAMPLED_OBSERVATIONS';
const SEGMENT_SEMANTICS = 'SAMPLED_ENDPOINT_CONNECTION';

function finiteNumber(value, name) {
  if (typeof value !== 'number' || !Number.isFinite(value)) throw new TypeError(name + ' must be a finite number');
  return value;
}
function nonEmpty(value, name) {
  if (typeof value !== 'string' || value.length === 0) throw new TypeError(name + ' must be a non-empty string');
  return value;
}
function nullableIdentity(value) {
  return value === undefined ? null : value;
}
function sameIdentity(a, b) {
  return a.run_id === b.run_id &&
    a.run_snapshot_id === b.run_snapshot_id &&
    a.arena_id === b.arena_id &&
    a.arena_epoch === b.arena_epoch &&
    a.world_id === b.world_id &&
    a.dimension_id === b.dimension_id;
}
function distance(a, b) {
  return Math.hypot(b.x - a.x, b.y - a.y, b.z - a.z);
}
function speedOf(sample) {
  if (typeof sample.vx !== 'number' || typeof sample.vy !== 'number' || typeof sample.vz !== 'number') return null;
  return Math.hypot(sample.vx, sample.vy, sample.vz);
}
function normalizeObservation(raw, index, defaults) {
  if (!raw || typeof raw !== 'object') throw new TypeError('observation[' + index + '] must be an object');
  const tick = raw.tick ?? raw.t;
  if (!Number.isInteger(tick)) throw new TypeError('observation[' + index + '].tick must be an integer');
  const sample = {
    sample_id: 'sample-' + String(index).padStart(6, '0'),
    tick,
    x: finiteNumber(raw.x, 'observation[' + index + '].x'),
    y: finiteNumber(raw.y, 'observation[' + index + '].y'),
    z: finiteNumber(raw.z, 'observation[' + index + '].z'),
    source_observation_id: nonEmpty(raw.source_observation_id ?? raw.sourceId, 'observation[' + index + '].source_observation_id'),
    source_kind: nonEmpty(raw.source_kind ?? raw.sourceKind, 'observation[' + index + '].source_kind'),
    run_id: nullableIdentity(raw.run_id ?? defaults.run_id),
    run_snapshot_id: nullableIdentity(raw.run_snapshot_id ?? defaults.run_snapshot_id),
    arena_id: nullableIdentity(raw.arena_id ?? defaults.arena_id),
    arena_epoch: nullableIdentity(raw.arena_epoch ?? defaults.arena_epoch),
    world_id: nullableIdentity(raw.world_id ?? defaults.world_id),
    dimension_id: nullableIdentity(raw.dimension_id ?? defaults.dimension_id),
  };
  for (const key of ['vx', 'vy', 'vz']) {
    if (raw[key] !== undefined) sample[key] = finiteNumber(raw[key], 'observation[' + index + '].' + key);
  }
  if (raw.game_time !== undefined) sample.game_time = raw.game_time;
  if (raw.timestamp !== undefined) sample.timestamp = raw.timestamp;
  return sample;
}
function normalizeDiscontinuity(raw, index) {
  if (!raw || typeof raw !== 'object') throw new TypeError('discontinuity[' + index + '] must be an object');
  if (!Number.isInteger(raw.after_tick) || !Number.isInteger(raw.before_tick)) {
    throw new TypeError('discontinuity[' + index + '] must define integer after_tick and before_tick');
  }
  if (raw.before_tick <= raw.after_tick) throw new TypeError('discontinuity[' + index + '] before_tick must be greater than after_tick');
  return {
    after_tick: raw.after_tick,
    before_tick: raw.before_tick,
    kind: nonEmpty(raw.kind, 'discontinuity[' + index + '].kind'),
    source_observation_id: raw.source_observation_id ?? null,
  };
}
function explicitBreakBetween(a, b, discontinuities) {
  return discontinuities.find(d => d.after_tick >= a.tick && d.before_tick <= b.tick) ?? null;
}
function computeMetrics(samples, segments, gaps) {
  if (samples.length === 0) {
    return {
      sample_count: 0, segment_count: 0, gap_count: gaps.length,
      first_tick: null, last_tick: null, duration_ticks: 0,
      net_displacement: 0, sampled_polyline_length: 0,
      min_altitude: null, max_altitude: null, speed: null,
    };
  }
  const first = samples[0], last = samples[samples.length - 1];
  const speeds = samples.map(speedOf).filter(v => v !== null);
  const speed = speeds.length ? {
    observed_sample_count: speeds.length,
    min: Math.min(...speeds),
    max: Math.max(...speeds),
    mean: speeds.reduce((a, b) => a + b, 0) / speeds.length,
  } : null;
  return {
    sample_count: samples.length,
    segment_count: segments.length,
    gap_count: gaps.length,
    first_tick: first.tick,
    last_tick: last.tick,
    duration_ticks: last.tick - first.tick,
    net_displacement: distance(first, last),
    sampled_polyline_length: segments.reduce((sum, s) => sum + s.distance, 0),
    min_altitude: Math.min(...samples.map(s => s.y)),
    max_altitude: Math.max(...samples.map(s => s.y)),
    speed,
  };
}

export function buildSampledMotionTrace({
  traceClass,
  subject,
  observations,
  identity = {},
  window = null,
  maxGapTicks = null,
  explicitDiscontinuities = [],
  maxSamples = 4096,
} = {}) {
  if (!TRACE_CLASSES.includes(traceClass)) throw new TypeError('unsupported traceClass: ' + traceClass);
  if (!subject || typeof subject !== 'object') throw new TypeError('subject is required');
  const subjectId = subject.id ?? subject.uuid;
  if (subjectId === undefined || subjectId === null || subjectId === '') throw new TypeError('subject.id or subject.uuid is required');
  if (!Array.isArray(observations)) throw new TypeError('observations must be an array');
  if (!Number.isInteger(maxSamples) || maxSamples < 1) throw new TypeError('maxSamples must be a positive integer');
  if (maxGapTicks !== null && (!Number.isInteger(maxGapTicks) || maxGapTicks < 1)) throw new TypeError('maxGapTicks must be null or a positive integer');

  const startTick = window?.start_tick ?? window?.startTick ?? -Infinity;
  const endTick = window?.end_tick ?? window?.endTick ?? Infinity;
  if (startTick > endTick) throw new TypeError('window start must not exceed end');

  const selected = observations
    .map((o, i) => normalizeObservation(o, i, identity))
    .filter(o => o.tick >= startTick && o.tick <= endTick)
    .sort((a, b) => a.tick - b.tick);

  if (selected.length > maxSamples) throw new RangeError('requested trace exceeds maxSamples=' + maxSamples);
  for (let i = 1; i < selected.length; i++) {
    if (selected[i].tick === selected[i - 1].tick) throw new Error('duplicate motion observation tick ' + selected[i].tick);
  }

  const discontinuities = explicitDiscontinuities.map(normalizeDiscontinuity);
  const segments = [];
  const gaps = [];
  for (let i = 1; i < selected.length; i++) {
    const a = selected[i - 1], b = selected[i];
    let reason = null;
    const explicit = explicitBreakBetween(a, b, discontinuities);
    if (explicit) reason = { kind: explicit.kind, source_observation_id: explicit.source_observation_id };
    else if (!sameIdentity(a, b)) reason = { kind: 'IDENTITY_BOUNDARY', source_observation_id: null };
    else if (maxGapTicks !== null && b.tick - a.tick > maxGapTicks) reason = { kind: 'SOURCE_GAP', source_observation_id: null };

    if (reason) {
      gaps.push({
        after_sample_id: a.sample_id,
        before_sample_id: b.sample_id,
        after_tick: a.tick,
        before_tick: b.tick,
        ...reason,
      });
      continue;
    }
    segments.push({
      from_sample_id: a.sample_id,
      to_sample_id: b.sample_id,
      elapsed_ticks: b.tick - a.tick,
      distance: distance(a, b),
      semantics: SEGMENT_SEMANTICS,
      continuity: 'DISPLAY_DERIVED',
    });
  }

  const sourceIdentities = [...new Set(selected.map(s => s.source_observation_id))];
  return {
    schema: TRACE_SCHEMA,
    version: 1,
    trace_class: traceClass,
    epistemic_status: TRACE_EPISTEMIC,
    subject: {
      id: String(subjectId),
      type: subject.type ?? null,
      role: subject.role ?? null,
    },
    request_window: {
      start_tick: Number.isFinite(startTick) ? startTick : null,
      end_tick: Number.isFinite(endTick) ? endTick : null,
    },
    samples: selected,
    segments,
    gaps,
    source_observation_ids: sourceIdentities,
    metrics: computeMetrics(selected, segments, gaps),
    semantics: {
      raw_samples_are_evidence: true,
      trace_is_derived_presentation: true,
      continuous_path_claimed: false,
      segment_semantics: SEGMENT_SEMANTICS,
    },
  };
}

export function buildTraceFromSimStore({
  store,
  entityId,
  traceClass,
  identity = {},
  startTick = null,
  endTick = null,
  maxSamples = 4096,
  maxGapTicks = null,
  explicitDiscontinuities = [],
} = {}) {
  if (!store || typeof store.trackOf !== 'function') throw new TypeError('store.trackOf is required');
  const track = store.trackOf(entityId);
  if (!track) return null;
  if (typeof track.samples !== 'function') {
    throw new Error('SIMSTORE_RETAINED_SAMPLES_UNAVAILABLE: refusing to reinterpret forward-filled state as sampled evidence');
  }
  const start = startTick === null ? track.t0 : Math.max(startTick, track.t0);
  const end = endTick === null ? track.t1 : Math.min(endTick, track.t1);
  const observations = track.samples(start, end, maxSamples);
  const entity = store.entities?.get ? store.entities.get(entityId) : null;
  return buildSampledMotionTrace({
    traceClass,
    subject: { id: entityId, type: entity?.type ?? null, role: entity?.role ?? null },
    observations,
    identity,
    window: { start_tick: start, end_tick: end },
    maxSamples,
    maxGapTicks,
    explicitDiscontinuities,
  });
}

export function motionTraceAvailability(store, entityIds = null) {
  if (!store || typeof store.trackOf !== 'function') return [];
  const ids = entityIds ?? (store.entities?.keys ? [...store.entities.keys()] : []);
  const out = [];
  for (const id of ids) {
    const tr = store.trackOf(id);
    if (!tr || typeof tr.samples !== 'function') continue;
    const entity = store.entities?.get ? store.entities.get(id) : null;
    out.push({
      subject_id: String(id),
      subject_type: entity?.type ?? null,
      trace_class: entity?.role === 'projectile' ? 'PROJECTILE_ACTUAL' : 'MOB_ACTUAL',
      retained_start_tick: tr.t0,
      retained_end_tick: tr.t1,
    });
  }
  return out;
}

export const MOTION_TRACE_V1 = Object.freeze({
  schema: TRACE_SCHEMA,
  traceClasses: TRACE_CLASSES,
  epistemicStatus: TRACE_EPISTEMIC,
  segmentSemantics: SEGMENT_SEMANTICS,
});
