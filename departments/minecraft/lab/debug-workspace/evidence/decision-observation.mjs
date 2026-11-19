const OBSERVATION_SCHEMA = 'kneekura.decision-observation/v1';
const PACKET_SCHEMA = 'kneekura.decision-observation-packet/v1';

const STAGES = Object.freeze(['INPUT', 'STATE', 'CANDIDATE', 'EVALUATION', 'SELECTION', 'EXECUTION', 'RESULT']);
const EPISTEMIC_STATUSES = Object.freeze([
  'DIRECT_OBSERVED',
  'SAMPLED_OBSERVED',
  'INSTRUMENTED_ALGORITHM_STATE',
  'DERIVED_FROM_OBSERVED',
  'NOT_EXPOSED',
  'NOT_APPLICABLE',
  'NOT_CAPTURED',
  'UNKNOWN',
]);
const CAUSAL_RELATIONS = Object.freeze([
  'DIRECT_RUNTIME_RELATION',
  'ALGORITHM_TRACE_RELATION',
  'TEMPORAL_ASSOCIATION',
  'DERIVED_SPATIAL_ASSOCIATION',
  'UNKNOWN_CAUSALITY',
]);
const CAPABILITY_STATUSES = Object.freeze([
  'AVAILABLE',
  'PARTIAL',
  'NOT_EXPOSED',
  'NOT_APPLICABLE',
  'NOT_CAPTURED',
  'UNKNOWN',
]);

function object(value, name) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new TypeError(name + ' must be an object');
  return value;
}
function string(value, name) {
  if (typeof value !== 'string' || value.length === 0) throw new TypeError(name + ' must be a non-empty string');
  return value;
}
function refs(value, name) {
  if (value == null) return [];
  if (!Array.isArray(value) || value.some(v => typeof v !== 'string' || v.length === 0)) {
    throw new TypeError(name + ' must be an array of non-empty strings');
  }
  return [...new Set(value)];
}
function requireSourceForEvidencedClaim(status, relation, sourceRefs, where) {
  const evidencedStatus = status === 'DIRECT_OBSERVED' ||
    status === 'SAMPLED_OBSERVED' ||
    status === 'INSTRUMENTED_ALGORITHM_STATE' ||
    status === 'DERIVED_FROM_OBSERVED';
  const evidencedRelation = relation === 'DIRECT_RUNTIME_RELATION' ||
    relation === 'ALGORITHM_TRACE_RELATION' ||
    relation === 'DERIVED_SPATIAL_ASSOCIATION';
  if ((evidencedStatus || evidencedRelation) && sourceRefs.length === 0) {
    throw new Error(where + ' requires at least one source_observation_id');
  }
}
function normalizeFact(raw, where) {
  object(raw, where);
  const status = string(raw.epistemic_status, where + '.epistemic_status');
  if (!EPISTEMIC_STATUSES.includes(status)) throw new TypeError(where + ': unsupported epistemic_status ' + status);
  const relation = raw.causal_relation ?? 'UNKNOWN_CAUSALITY';
  if (!CAUSAL_RELATIONS.includes(relation)) throw new TypeError(where + ': unsupported causal_relation ' + relation);
  const sourceRefs = refs(raw.source_observation_ids, where + '.source_observation_ids');
  requireSourceForEvidencedClaim(status, relation, sourceRefs, where);
  return {
    fact_id: raw.fact_id == null ? null : string(raw.fact_id, where + '.fact_id'),
    key: string(raw.key, where + '.key'),
    value: raw.value,
    epistemic_status: status,
    causal_relation: relation,
    source_observation_ids: sourceRefs,
    adapter_namespace: raw.adapter_namespace ?? null,
    note: raw.note ?? null,
  };
}
function normalizeCapability(name, raw) {
  object(raw, 'capabilities.' + name);
  const status = string(raw.status, 'capabilities.' + name + '.status');
  if (!CAPABILITY_STATUSES.includes(status)) throw new TypeError('capabilities.' + name + ': unsupported status ' + status);
  return {
    status,
    source_observation_ids: refs(raw.source_observation_ids, 'capabilities.' + name + '.source_observation_ids'),
    detail: raw.detail ?? null,
  };
}
function normalizeStage(stage, raw) {
  if (!STAGES.includes(stage)) throw new TypeError('unsupported stage ' + stage);
  object(raw, 'stages.' + stage);
  const facts = raw.facts ?? [];
  if (!Array.isArray(facts)) throw new TypeError('stages.' + stage + '.facts must be an array');
  return {
    status: raw.status ?? 'AVAILABLE',
    facts: facts.map((f, i) => normalizeFact(f, 'stages.' + stage + '.facts[' + i + ']')),
  };
}
function normalizeTimelineEvent(raw, index) {
  const where = 'timeline[' + index + ']';
  object(raw, where);
  if (!Number.isInteger(raw.tick)) throw new TypeError(where + '.tick must be an integer');
  const stage = raw.stage ?? null;
  if (stage !== null && !STAGES.includes(stage)) throw new TypeError(where + ': unsupported stage ' + stage);
  const status = string(raw.epistemic_status, where + '.epistemic_status');
  if (!EPISTEMIC_STATUSES.includes(status)) throw new TypeError(where + ': unsupported epistemic_status ' + status);
  const relation = raw.causal_relation ?? 'TEMPORAL_ASSOCIATION';
  if (!CAUSAL_RELATIONS.includes(relation)) throw new TypeError(where + ': unsupported causal_relation ' + relation);
  const sourceRefs = refs(raw.source_observation_ids, where + '.source_observation_ids');
  requireSourceForEvidencedClaim(status, relation, sourceRefs, where);
  return {
    event_id: raw.event_id == null ? null : string(raw.event_id, where + '.event_id'),
    tick: raw.tick,
    stage,
    kind: string(raw.kind, where + '.kind'),
    summary: raw.summary ?? null,
    epistemic_status: status,
    causal_relation: relation,
    source_observation_ids: sourceRefs,
  };
}

export function createDecisionObservation({
  subject,
  identity = {},
  adapter,
  capabilities = {},
  stages = {},
  timeline = [],
  availableDrilldowns = [],
} = {}) {
  object(subject, 'subject');
  const subjectId = subject.id ?? subject.uuid;
  if (subjectId === undefined || subjectId === null || subjectId === '') throw new TypeError('subject.id or subject.uuid is required');
  object(adapter, 'adapter');
  const normalizedCapabilities = {};
  for (const [name, value] of Object.entries(capabilities)) normalizedCapabilities[name] = normalizeCapability(name, value);

  const normalizedStages = {};
  for (const [stage, value] of Object.entries(stages)) normalizedStages[stage] = normalizeStage(stage, value);
  const normalizedTimeline = timeline.map(normalizeTimelineEvent).sort((a, b) => a.tick - b.tick);

  if (!Array.isArray(availableDrilldowns) || availableDrilldowns.some(v => typeof v !== 'string' || !v)) {
    throw new TypeError('availableDrilldowns must be an array of non-empty strings');
  }

  return {
    schema: OBSERVATION_SCHEMA,
    version: 1,
    identity: {
      run_id: identity.run_id ?? null,
      run_snapshot_id: identity.run_snapshot_id ?? null,
      arena_id: identity.arena_id ?? null,
      arena_epoch: identity.arena_epoch ?? null,
      world_id: identity.world_id ?? null,
      dimension_id: identity.dimension_id ?? null,
      tick: identity.tick ?? null,
    },
    subject: {
      id: String(subjectId),
      type: subject.type ?? null,
      mod_id: subject.mod_id ?? null,
    },
    adapter: {
      id: string(adapter.id, 'adapter.id'),
      version: string(adapter.version, 'adapter.version'),
      family: adapter.family ?? null,
      provenance: adapter.provenance ?? null,
      observer_effect_risk: adapter.observer_effect_risk ?? 'UNKNOWN',
    },
    capabilities: normalizedCapabilities,
    stages: normalizedStages,
    timeline: normalizedTimeline,
    available_drilldowns: [...new Set(availableDrilldowns)],
    semantics: {
      missing_stage_means_unobserved_or_not_applicable: true,
      temporal_adjacency_is_not_causality: true,
      unavailable_state_must_remain_explicit: true,
      mind_reading_claims_permitted: false,
    },
  };
}

export function buildDecisionPacket(observation, { timelineLimit = 64 } = {}) {
  object(observation, 'observation');
  if (observation.schema !== OBSERVATION_SCHEMA) throw new TypeError('observation schema must be ' + OBSERVATION_SCHEMA);
  if (!Number.isInteger(timelineLimit) || timelineLimit < 0) throw new TypeError('timelineLimit must be a non-negative integer');

  const compactStages = {};
  for (const stage of STAGES) {
    const value = observation.stages?.[stage];
    if (!value) continue;
    compactStages[stage] = {
      status: value.status,
      facts: value.facts.map(f => ({
        key: f.key,
        value: f.value,
        epistemic_status: f.epistemic_status,
        causal_relation: f.causal_relation,
        source_observation_ids: f.source_observation_ids,
        adapter_namespace: f.adapter_namespace,
      })),
    };
  }

  return {
    schema: PACKET_SCHEMA,
    version: 1,
    identity: observation.identity,
    subject: observation.subject,
    adapter: observation.adapter,
    capabilities: observation.capabilities,
    stages: compactStages,
    timeline: observation.timeline.slice(Math.max(0, observation.timeline.length - timelineLimit)),
    available_drilldowns: observation.available_drilldowns,
    semantics: observation.semantics,
  };
}

export const DECISION_OBSERVATION_V1 = Object.freeze({
  observationSchema: OBSERVATION_SCHEMA,
  packetSchema: PACKET_SCHEMA,
  stages: STAGES,
  epistemicStatuses: EPISTEMIC_STATUSES,
  causalRelations: CAUSAL_RELATIONS,
  capabilityStatuses: CAPABILITY_STATUSES,
});
