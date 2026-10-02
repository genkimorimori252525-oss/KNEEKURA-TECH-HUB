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

function svgNumber(v) {
  return Number(v.toFixed(3));
}
function traceStyle(traceClass) {
  if (traceClass === 'MOB_ACTUAL') return { width: 3, dash: '12 7', marker: 'circle' };
  if (traceClass === 'PROJECTILE_ACTUAL') return { width: 2, dash: '4 4', marker: 'diamond' };
  return { width: 1.5, dash: '1 5', marker: 'square' };
}
function projectTraceSample(sample, view) {
  if (view === 'PLAN_XZ') return [sample.x, sample.z];
  if (view === 'ELEVATION') return [sample.tick, sample.y];
  if (view === 'ISOMETRIC_3D') return [sample.x - sample.z, (sample.x + sample.z) * 0.5 - sample.y];
  throw new TypeError('unsupported motion trace view: ' + view);
}
function svgMarker(marker, x, y) {
  if (marker === 'circle') return '<circle cx="' + x + '" cy="' + y + '" r="3"/>';
  if (marker === 'diamond') return '<path d="M ' + x + ' ' + (y - 3) + ' L ' + (x + 3) + ' ' + y + ' L ' + x + ' ' + (y + 3) + ' L ' + (x - 3) + ' ' + y + ' Z"/>';
  return '<rect x="' + (x - 2.5) + '" y="' + (y - 2.5) + '" width="5" height="5"/>';
}

export function renderMotionTraceSvg(trace, view, { width = 640, height = 360, padding = 28 } = {}) {
  if (!trace || trace.schema !== TRACE_SCHEMA) throw new TypeError('trace must be SampledMotionTrace v1');
  if (!['PLAN_XZ', 'ELEVATION', 'ISOMETRIC_3D'].includes(view)) throw new TypeError('unsupported motion trace view: ' + view);
  if (!Number.isFinite(width) || !Number.isFinite(height) || width <= padding * 2 || height <= padding * 2) {
    throw new TypeError('invalid SVG dimensions');
  }
  const style = traceStyle(trace.trace_class);
  const raw = trace.samples.map(s => projectTraceSample(s, view));
  const xs = raw.map(p => p[0]), ys = raw.map(p => p[1]);
  const minX = raw.length ? Math.min(...xs) : 0, maxX = raw.length ? Math.max(...xs) : 1;
  const minY = raw.length ? Math.min(...ys) : 0, maxY = raw.length ? Math.max(...ys) : 1;
  const spanX = Math.max(1e-9, maxX - minX), spanY = Math.max(1e-9, maxY - minY);
  const scale = Math.min((width - padding * 2) / spanX, (height - padding * 2) / spanY);
  const usedW = spanX * scale, usedH = spanY * scale;
  const ox = (width - usedW) / 2 - minX * scale;
  const oy = (height - usedH) / 2 + maxY * scale;
  const projected = new Map();
  for (let i = 0; i < trace.samples.length; i++) {
    const [x, y] = raw[i];
    projected.set(trace.samples[i].sample_id, [svgNumber(ox + x * scale), svgNumber(oy - y * scale)]);
  }
  const lines = trace.segments.map(seg => {
    const a = projected.get(seg.from_sample_id), b = projected.get(seg.to_sample_id);
    if (!a || !b) return '';
    return '<line x1="' + a[0] + '" y1="' + a[1] + '" x2="' + b[0] + '" y2="' + b[1] + '"/>';
  }).join('');
  const markers = trace.samples.map(s => {
    const p = projected.get(s.sample_id);
    return p ? svgMarker(style.marker, p[0], p[1]) : '';
  }).join('');
  const gapMarkers = trace.gaps.map(g => {
    const a = projected.get(g.after_sample_id), b = projected.get(g.before_sample_id);
    if (!a || !b) return '';
    const x = svgNumber((a[0] + b[0]) / 2), y = svgNumber((a[1] + b[1]) / 2);
    return '<path class="gap" d="M ' + (x - 4) + ' ' + (y - 4) + ' L ' + (x + 4) + ' ' + (y + 4) + ' M ' + (x + 4) + ' ' + (y - 4) + ' L ' + (x - 4) + ' ' + (y + 4) + '"/>';
  }).join('');
  return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + width + ' ' + height + '" role="img" data-derived="true" data-view="' + view + '" data-trace-class="' + trace.trace_class + '">' +
    '<g fill="none" stroke="currentColor" stroke-width="' + style.width + '" stroke-dasharray="' + style.dash + '" stroke-linecap="round">' + lines + '</g>' +
    '<g fill="currentColor" stroke="currentColor">' + markers + '</g>' +
    '<g fill="none" stroke="currentColor" stroke-width="1.5">' + gapMarkers + '</g>' +
    '</svg>';
}

export function buildMotionTracePacket(trace, { views = [], includeMetrics = true } = {}) {
  if (!trace || trace.schema !== TRACE_SCHEMA) throw new TypeError('trace must be SampledMotionTrace v1');
  if (!Array.isArray(views)) throw new TypeError('views must be an array');
  const allowed = new Set(['PLAN_XZ', 'ELEVATION', 'ISOMETRIC_3D']);
  for (const view of views) if (!allowed.has(view)) throw new TypeError('unsupported motion trace view: ' + view);
  return {
    schema: 'kneekura.motion-trace-packet/v1',
    version: 1,
    trace_class: trace.trace_class,
    subject: trace.subject,
    request_window: trace.request_window,
    epistemic_status: trace.epistemic_status,
    metrics: includeMetrics ? trace.metrics : null,
    gaps: trace.gaps,
    source_observation_ids: trace.source_observation_ids,
    artifacts: [...new Set(views)].map(view => ({
      view,
      mime_type: 'image/svg+xml',
      derived: true,
      content: renderMotionTraceSvg(trace, view),
    })),
    semantics: trace.semantics,
  };
}

export const MOTION_TRACE_V1 = Object.freeze({
  schema: TRACE_SCHEMA,
  traceClasses: TRACE_CLASSES,
  epistemicStatus: TRACE_EPISTEMIC,
  segmentSemantics: SEGMENT_SEMANTICS,
});
