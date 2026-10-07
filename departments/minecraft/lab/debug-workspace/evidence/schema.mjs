export const EVIDENCE_VERSION = 1;

export const EPISTEMIC_STATUS = Object.freeze([
  'OBSERVED',
  'DERIVED',
  'CORRELATED',
  'INFERRED',
  'UNKNOWN',
]);

export const COMPLETENESS_STATUS = Object.freeze([
  'COMPLETE',
  'PARTIAL',
  'UNKNOWN',
]);

export const LANE_STATUS = Object.freeze([
  'HEALTHY',
  'IDLE',
  'DEGRADED',
  'STALE',
  'STOPPED',
  'UNKNOWN',
]);

export const SCOPE_KINDS = Object.freeze([
  'GLOBAL_HEALTH',
  'ARENA',
  'ENTITY_UUID',
  'ENTITY_SET',
  'REGION',
  'PACKET_TYPE',
  'SUBSYSTEM',
  'EXPERIMENT',
]);

export const OBSERVATION_LEVELS = Object.freeze(['L0', 'L1', 'L2', 'L3', 'L4']);

export const DEFAULT_LANES = Object.freeze([
  'SERVER_TICK',
  'CLIENT_TICK',
  'TARGET_TRACKED',
  'ENTITY_STATE',
  'SERVER_TARGET_TRACKED',
  'SERVER_ENTITY_STATE',
  'TANK_ROOM_ROSTER',
  'AI_TARGET',
  'BRAIN_MEMORY',
  'RUNNING_BEHAVIORS',
  'BEHAVIOR_TRANSITION',
  'TLM_STATE',
  'REIMU_STATE',
  'AI_DECISION',
  'NAVIGATION',
  'PACKET_SEND',
  'PACKET_RECEIVE',
  'PACKET_HANDLER',
  'MOLANG_M5',
  'MOLANG_M6',
  'RENDER_ENTERED',
  'YSM_ENTERED',
  'YSM_COMPLETED',
  'ACTION_APPLIED',
  'OBSERVATION_WRITTEN',
]);

const ID_RE = /^[A-Za-z0-9._:-]{1,160}$/;

export function isPlainObject(value) {
  return value != null && typeof value === 'object' && !Array.isArray(value);
}

function requireString(errors, obj, field, options = {}) {
  const value = obj?.[field];
  if (typeof value !== 'string' || !value.trim()) {
    errors.push(field + ' must be a non-empty string');
    return null;
  }
  const trimmed = value.trim();
  if (options.id === true && !ID_RE.test(trimmed)) {
    errors.push(field + ' contains unsupported characters');
  }
  return trimmed;
}

function requirePositiveInteger(errors, obj, field) {
  const value = obj?.[field];
  if (!Number.isInteger(value) || value < 0) {
    errors.push(field + ' must be an integer >= 0');
    return null;
  }
  return value;
}

function validIso(value) {
  return typeof value === 'string' && Number.isFinite(Date.parse(value));
}

export function normalizeCompleteness(value) {
  if (value == null) {
    return {
      status: 'UNKNOWN',
      complete: false,
      visited: null,
      visitBudget: null,
      depthBudget: null,
      truncatedContainers: null,
      timedOut: null,
    };
  }
  if (!isPlainObject(value)) {
    throw new TypeError('completeness must be an object');
  }

  const complete = value.complete === true;
  const status = value.status ||
    (complete ? 'COMPLETE' : 'PARTIAL');

  if (!COMPLETENESS_STATUS.includes(status)) {
    throw new TypeError('invalid completeness.status: ' + status);
  }

  return {
    status,
    complete,
    visited: Number.isInteger(value.visited) ? value.visited : null,
    visitBudget: Number.isInteger(value.visitBudget) ? value.visitBudget : null,
    depthBudget: Number.isInteger(value.depthBudget) ? value.depthBudget : null,
    truncatedContainers: Number.isInteger(value.truncatedContainers)
      ? value.truncatedContainers
      : null,
    timedOut: typeof value.timedOut === 'boolean' ? value.timedOut : null,
  };
}

export function validateScope(scope) {
  const errors = [];
  if (!isPlainObject(scope)) {
    return { ok: false, errors: ['scope must be an object'] };
  }

  if (!SCOPE_KINDS.includes(scope.kind)) {
    errors.push('scope.kind invalid: ' + scope.kind);
  }

  if (scope.kind === 'ENTITY_UUID') {
    requireString(errors, scope, 'entityUuid', { id: true });
  }
  if (scope.kind === 'EXPERIMENT') {
    requireString(errors, scope, 'experimentId', { id: true });
  }
  if (scope.kind === 'SUBSYSTEM') {
    requireString(errors, scope, 'subsystem', { id: true });
  }
  if (scope.kind === 'PACKET_TYPE') {
    requireString(errors, scope, 'packetType');
  }
  if (scope.kind === 'REGION' && !isPlainObject(scope.region)) {
    errors.push('scope.region must be an object for REGION scope');
  }

  return { ok: errors.length === 0, errors };
}

export function validateObservation(record) {
  const errors = [];
  if (!isPlainObject(record)) {
    return { ok: false, errors: ['observation must be an object'] };
  }

  if (record.v !== EVIDENCE_VERSION) errors.push('v must be ' + EVIDENCE_VERSION);
  if (record.kind !== 'observation') errors.push('kind must be observation');

  requireString(errors, record, 'observationId', { id: true });
  requireString(errors, record, 'debugSessionId', { id: true });
  requireString(errors, record, 'runId', { id: true });
  if (record.runSnapshotId != null) {
    requireString(errors, record, 'runSnapshotId', { id: true });
  }
  requirePositiveInteger(errors, record, 'processEpoch');
  requirePositiveInteger(errors, record, 'arenaEpoch');
  requirePositiveInteger(errors, record, 'resourceEpoch');
  requireString(errors, record, 'writerId', { id: true });
  requirePositiveInteger(errors, record, 'writerSeq');

  if (!OBSERVATION_LEVELS.includes(record.level)) {
    errors.push('level invalid: ' + record.level);
  }
  if (typeof record.lane !== 'string' || !record.lane.trim()) {
    errors.push('lane must be a non-empty string');
  }
  if (!validIso(record.observedAt)) {
    errors.push('observedAt must be ISO timestamp');
  }
  if (record.clock != null) {
    if (!isPlainObject(record.clock)) {
      errors.push('clock must be an object when present');
    } else {
      requireString(errors, record.clock, 'domain', { id: true });
      if (record.clock.domain !== 'JVM_PROCESS_MONOTONIC') {
        errors.push('clock.domain invalid: ' + record.clock.domain);
      }
      if (!Number.isInteger(record.clock.processId) || record.clock.processId <= 0) {
        errors.push('clock.processId must be a positive integer');
      }
      if (record.clock.processStartedAt != null &&
          !validIso(record.clock.processStartedAt)) {
        errors.push('clock.processStartedAt must be ISO timestamp when present');
      }
      if (!validIso(record.clock.monotonicOriginWallClock)) {
        errors.push('clock.monotonicOriginWallClock must be ISO timestamp');
      }
      if (!Number.isInteger(record.clock.monotonicElapsedNanos) ||
          record.clock.monotonicElapsedNanos < 0) {
        errors.push('clock.monotonicElapsedNanos must be an integer >= 0');
      }
      if (!validIso(record.clock.wallClockSample)) {
        errors.push('clock.wallClockSample must be ISO timestamp');
      }
    }
  }
  if (!EPISTEMIC_STATUS.includes(record.epistemicStatus)) {
    errors.push('epistemicStatus invalid: ' + record.epistemicStatus);
  }
  if (record.producerDeltaApplied != null &&
      typeof record.producerDeltaApplied !== 'boolean') {
    errors.push('producerDeltaApplied must be boolean when present');
  }
  if (record.writerQueueDepth != null &&
      (!Number.isInteger(record.writerQueueDepth) || record.writerQueueDepth < 0)) {
    errors.push('writerQueueDepth must be an integer >= 0 when present');
  }
  if (record.writerDroppedTotal != null &&
      (!Number.isInteger(record.writerDroppedTotal) || record.writerDroppedTotal < 0)) {
    errors.push('writerDroppedTotal must be an integer >= 0 when present');
  }

  const scope = validateScope(record.scope);
  if (!scope.ok) errors.push(...scope.errors);

  if (!isPlainObject(record.source)) {
    errors.push('source must be an object');
  } else {
    requireString(errors, record.source, 'side');
    requireString(errors, record.source, 'method');
  }

  if (!isPlainObject(record.payload)) {
    errors.push('payload must be an object');
  }

  try {
    normalizeCompleteness(record.completeness);
  } catch (error) {
    errors.push(error.message);
  }

  return { ok: errors.length === 0, errors };
}

export function validateFinding(record) {
  const errors = [];
  if (!isPlainObject(record)) {
    return { ok: false, errors: ['finding must be an object'] };
  }

  if (record.v !== EVIDENCE_VERSION) errors.push('v must be ' + EVIDENCE_VERSION);
  if (record.kind !== 'finding') errors.push('kind must be finding');
  requireString(errors, record, 'findingId', { id: true });
  requireString(errors, record, 'debugSessionId', { id: true });
  requireString(errors, record, 'runId', { id: true });
  if (record.runSnapshotId != null) {
    requireString(errors, record, 'runSnapshotId', { id: true });
  }
  requireString(errors, record, 'statement');
  if (!['DERIVED', 'CORRELATED', 'INFERRED', 'UNKNOWN'].includes(record.epistemicStatus)) {
    errors.push('finding epistemicStatus cannot be OBSERVED');
  }
  if (!Array.isArray(record.evidenceIds) || record.evidenceIds.length === 0) {
    errors.push('finding.evidenceIds must be a non-empty array');
  }
  if (record.evidenceIds?.some((x) => typeof x !== 'string' || !x.trim())) {
    errors.push('finding.evidenceIds must contain non-empty strings');
  }
  if (!validIso(record.createdAt)) errors.push('createdAt must be ISO timestamp');

  return { ok: errors.length === 0, errors };
}

export function validateLaneHealth(record) {
  const errors = [];
  if (!isPlainObject(record)) {
    return { ok: false, errors: ['lane health must be an object'] };
  }
  if (record.v !== EVIDENCE_VERSION) errors.push('v must be ' + EVIDENCE_VERSION);
  if (record.kind !== 'lane_health') errors.push('kind must be lane_health');
  requireString(errors, record, 'debugSessionId', { id: true });
  requireString(errors, record, 'runId', { id: true });
  if (record.runSnapshotId != null) {
    requireString(errors, record, 'runSnapshotId', { id: true });
  }
  requireString(errors, record, 'lane', { id: true });
  if (!LANE_STATUS.includes(record.status)) {
    errors.push('lane status invalid: ' + record.status);
  }
  for (const field of ['count', 'lastSequence', 'dropped', 'errors']) {
    if (!Number.isInteger(record[field]) || record[field] < 0) {
      errors.push(field + ' must be an integer >= 0');
    }
  }
  if (record.lastAt != null && !validIso(record.lastAt)) {
    errors.push('lastAt must be null or ISO timestamp');
  }
  return { ok: errors.length === 0, errors };
}

export function assertValidObservation(record) {
  const result = validateObservation(record);
  if (!result.ok) {
    throw new TypeError('invalid observation: ' + result.errors.join('; '));
  }
  return record;
}

export function assertValidFinding(record) {
  const result = validateFinding(record);
  if (!result.ok) {
    throw new TypeError('invalid finding: ' + result.errors.join('; '));
  }
  return record;
}
