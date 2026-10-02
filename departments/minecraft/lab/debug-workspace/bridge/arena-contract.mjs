import { exactKeys, identifier, hashId, integer } from './json.mjs';

const STATE_CLASSES = new Set([
  'blocks', 'block_entities', 'entities', 'effects', 'target_state', 'scheduled_ticks',
  'game_rules', 'time_weather', 'chunk_tickets', 'probe_state',
]);
const RESET_CLASSIFICATIONS = new Set(['RESETTABLE', 'PERSISTENT_BY_DESIGN', 'EXTERNAL', 'UNKNOWN']);

function vector(value, count, min, max) {
  if (!Array.isArray(value) || value.length !== count || value.some(
    item => typeof item !== 'number' || !Number.isFinite(item) || item < min || item > max,
  )) throw new TypeError('INVALID_VECTOR');
}

function bounds(value) {
  exactKeys(value, ['min', 'max'], 'BOUNDS');
  for (const point of [value.min, value.max]) {
    vector(point, 3, -30000000, 30000000);
    if (point.some(item => !Number.isInteger(item))) throw new TypeError('INTEGER_BOUNDS_REQUIRED');
  }
  if (value.min.some((item, i) => value.max[i] - item <= 0 || value.max[i] - item > 64) ||
      value.min[1] < -64 || value.max[1] > 320) throw new TypeError('ARENA_BOUNDS_LIMIT');
}

function position(value, region, block = false) {
  vector(value, 3, -30000000, 30000000);
  if (value.some((item, i) => item < region.min[i] || item >= region.max[i]) ||
      (block && value.some(item => !Number.isInteger(item)))) {
    throw new TypeError('ACTION_OUTSIDE_BOUNDS');
  }
}

function resource(value) {
  if (typeof value !== 'string' || value.length > 128 ||
      !/^([a-z0-9_]+):[a-z0-9_./-]+$/.test(value) ||
      value.split(':')[1].split('/').some(part => !part || part === '.' || part === '..')) {
    throw new TypeError('INVALID_RESOURCE');
  }
}

function currentIdentity(value, identity) {
  for (const key of ['debugSessionId', 'runId', 'runSnapshotId']) {
    identifier(value[key]);
    if (value[key] !== identity[key]) throw new Error('STALE_COMMAND_REJECTED');
  }
  integer(value.processEpoch, 0, Number.MAX_SAFE_INTEGER);
  if (value.processEpoch !== identity.processEpoch) throw new Error('STALE_COMMAND_REJECTED');
}

export function validateArenaContract(value) {
  exactKeys(value, [
    'schemaVersion', 'arenaId', 'arenaEpoch', 'arenaRevision', 'baselineHash',
    'bounds', 'allowedMutationBounds', 'resetClasses',
  ], 'ARENA');
  integer(value.schemaVersion, 1, 1);
  identifier(value.arenaId);
  integer(value.arenaEpoch, 0, Number.MAX_SAFE_INTEGER);
  integer(value.arenaRevision, 0, Number.MAX_SAFE_INTEGER);
  hashId(value.baselineHash);
  bounds(value.bounds);
  bounds(value.allowedMutationBounds);
  if (value.allowedMutationBounds.min.some((item, i) => item < value.bounds.min[i]) ||
      value.allowedMutationBounds.max.some((item, i) => item > value.bounds.max[i])) {
    throw new TypeError('MUTATION_BOUNDS_OUTSIDE_ARENA');
  }
  if (!value.resetClasses || Array.isArray(value.resetClasses) ||
      typeof value.resetClasses !== 'object' || Object.keys(value.resetClasses).length === 0) {
    throw new TypeError('INVALID_RESET_CLASSES');
  }
  for (const [name, status] of Object.entries(value.resetClasses)) {
    if (!STATE_CLASSES.has(name) || !RESET_CLASSIFICATIONS.has(status)) {
      throw new TypeError('INVALID_RESET_CLASS');
    }
  }
  return structuredClone(value);
}

function validateSubject(args, identity) {
  identifier(args.subject_id);
  const uuid = identity.subjects?.[args.subject_id];
  if (typeof uuid !== 'string' ||
      !/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/.test(uuid)) {
    throw new TypeError('UNKNOWN_SUBJECT');
  }
}

export function validateActionEnvelope(value, arena, identity) {
  validateArenaContract(arena);
  exactKeys(value, [
    'schemaVersion', 'debugSessionId', 'runId', 'runSnapshotId', 'processEpoch',
    'arenaId', 'arenaEpoch', 'expectedArenaRevision', 'experimentId', 'actionId',
    'idempotencyKey', 'type', 'args',
  ], 'ACTION');
  integer(value.schemaVersion, 1, 1);
  currentIdentity(value, identity);
  for (const key of ['arenaId', 'experimentId', 'actionId', 'idempotencyKey']) identifier(value[key]);
  if (value.arenaId !== arena.arenaId || value.arenaEpoch !== arena.arenaEpoch ||
      value.experimentId !== identity.experimentId) throw new Error('STALE_COMMAND_REJECTED');
  if (value.expectedArenaRevision !== arena.arenaRevision) throw new Error('ARENA_REVISION_CONFLICT');
  const args = value.args;
  switch (value.type) {
    case 'wait_ticks':
      exactKeys(args, ['ticks'], 'WAIT');
      integer(args.ticks, 1, 1200);
      break;
    case 'teleport_subject':
      exactKeys(args, ['subject_id', 'position', 'rotation'], 'TELEPORT');
      validateSubject(args, identity);
      position(args.position, arena.allowedMutationBounds);
      vector(args.rotation, 2, -180, 180);
      if (Math.abs(args.rotation[1]) > 90) throw new TypeError('INVALID_PITCH');
      break;
    case 'use_item':
      exactKeys(args, ['subject_id', 'hand', 'ticks'], 'USE_ITEM');
      validateSubject(args, identity);
      if (!['main_hand', 'off_hand'].includes(args.hand)) throw new TypeError('INVALID_HAND');
      integer(args.ticks, 1, 20);
      break;
    case 'set_block':
      exactKeys(args, ['position', 'block'], 'SET_BLOCK');
      position(args.position, arena.allowedMutationBounds, true);
      resource(args.block);
      break;
    default:
      throw new TypeError('UNSUPPORTED_TYPED_ACTION');
  }
  return {
    scope: 'CONTRACT_ONLY', backend: 'UNAVAILABLE', action: structuredClone(value),
    subjectUuid: args.subject_id ? identity.subjects[args.subject_id] : null,
  };
}

export function validateResetEvidence(value, arena, identity) {
  validateArenaContract(arena);
  exactKeys(value, [
    'schemaVersion', 'debugSessionId', 'runId', 'runSnapshotId', 'processEpoch',
    'arenaId', 'beforeEpoch', 'afterEpoch', 'beforeRevision', 'afterRevision',
    'expectedBaselineHash', 'measuredBaselineHash', 'resetClasses', 'remainingClasses', 'evidenceHashes',
  ], 'RESET_EVIDENCE');
  integer(value.schemaVersion, 1, 1);
  currentIdentity(value, identity);
  for (const key of ['beforeEpoch', 'afterEpoch', 'beforeRevision', 'afterRevision']) {
    integer(value[key], 0, Number.MAX_SAFE_INTEGER);
  }
  if (value.arenaId !== arena.arenaId || value.beforeEpoch !== arena.arenaEpoch ||
      value.beforeRevision !== arena.arenaRevision || value.afterEpoch !== value.beforeEpoch + 1 ||
      value.afterRevision !== value.beforeRevision + 1) throw new Error('RESET_IDENTITY_MISMATCH');
  if (value.expectedBaselineHash !== arena.baselineHash) throw new Error('RESET_BASELINE_IDENTITY');
  hashId(value.measuredBaselineHash);
  for (const key of ['resetClasses', 'remainingClasses']) {
    if (!Array.isArray(value[key]) || new Set(value[key]).size !== value[key].length ||
        value[key].some(item => !Object.hasOwn(arena.resetClasses, item))) {
      throw new TypeError('INVALID_RESET_CLASSES');
    }
  }
  if (!Array.isArray(value.evidenceHashes) || value.evidenceHashes.length > 32) {
    throw new TypeError('INVALID_EVIDENCE');
  }
  value.evidenceHashes.forEach(hashId);
  const incomplete = value.evidenceHashes.length === 0 || value.remainingClasses.length > 0 ||
    Object.entries(arena.resetClasses).some(([key, status]) =>
      status === 'UNKNOWN' || status === 'EXTERNAL' ||
      (status === 'RESETTABLE' && !value.resetClasses.includes(key)),
    );
  return {
    valid: true, scope: 'CONTRACT_ONLY', runtimeAttestation: 'NOT_ESTABLISHED',
    classification: value.measuredBaselineHash !== arena.baselineHash
      ? 'ARENA_NOT_CLEAN' : incomplete ? 'INCONCLUSIVE' : 'REPORTED_BASELINE_MATCH',
  };
}
