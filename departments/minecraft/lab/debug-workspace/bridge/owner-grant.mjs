/** Pure supervisor-owned lease intent. This object is NEVER a runtime authorization proof. */
import { exactKeys, identifier, integer, hashId, stableJson } from './json.mjs';
import { validateTechHubBinding } from './registration.mjs';

function resource(value) {
  return typeof value === 'string' && value.length <= 128 &&
    /^[a-z0-9_]+:[a-z0-9_/.-]+$/.test(value) &&
    !value.split(':')[1].split('/').some(part => !part || part === '.' || part === '..');
}

export function buildOwnerGrantIntent({ binding, request, identity, selection }) {
  binding = validateTechHubBinding(binding);
  if (request?.experiment_id !== binding.experiment_id || request.generation !== binding.generation ||
      stableJson(request.target) !== stableJson(binding.target) ||
      request.arena?.arena_id !== binding.arena_id || request.arena.baseline_hash !== binding.arena_baseline_hash) {
    throw new Error('GRANT_REQUEST_BINDING_MISMATCH');
  }
  return buildGrantFromSealedRequest({ request, requestHash: binding.request_hash, identity, selection });
}

/** Reconstruct the exact grant from an already hash-verified request, without inventing an assertions blob hash. */
export function buildGrantFromSealedRequest({ request, requestHash, identity, selection }) {
  hashId(requestHash);
  if (!request || typeof request !== 'object') throw new TypeError('INVALID_OWNER_REQUEST');
  identifier(request.experiment_id);
  integer(request.generation, 1, 1000000);
  identifier(request.arena?.arena_id);
  hashId(request.arena?.baseline_hash);
  exactKeys(identity, ['debugSessionId', 'runId', 'runSnapshotId', 'processEpoch', 'handshakeNonce',
    'dimensionId', 'disposableWorldName'], 'GRANT_IDENTITY');
  exactKeys(selection, ['grantId', 'leaseId', 'arenaEpoch', 'expectedArenaRevision', 'allowedActions'], 'GRANT_SELECTION');
  for (const key of ['debugSessionId', 'runId', 'runSnapshotId', 'handshakeNonce']) identifier(identity[key]);
  for (const key of ['grantId', 'leaseId']) identifier(selection[key]);
  for (const key of ['arenaEpoch', 'expectedArenaRevision']) integer(selection[key], 0, Number.MAX_SAFE_INTEGER);
  integer(identity.processEpoch, 1, 2147483647);
  if (identity.handshakeNonce.length < 16) throw new TypeError('INVALID_NONCE_LENGTH');
  if (identity.disposableWorldName !== 'KNEEKURA_DEBUG_WORLD' || !resource(identity.dimensionId)) {
    throw new TypeError('INVALID_DISPOSABLE_WORLD_INTENT');
  }
  const bounds = request.arena.bounds;
  exactKeys(bounds, ['min', 'max'], 'GRANT_BOUNDS');
  for (const point of [bounds.min, bounds.max]) {
    if (!Array.isArray(point) || point.length !== 3) throw new TypeError('INVALID_GRANT_BOUNDS');
    for (const n of point) integer(n, -30000000, 30000000);
  }
  const edges = bounds.max.map((n, i) => n - bounds.min[i]);
  if (edges.some(n => n <= 0 || n > 64) || edges.reduce((a, b) => a * b, 1) > 4096 ||
      bounds.min[1] < -64 || bounds.max[1] > 320) {
    throw new TypeError('GRANT_BOUNDS_LIMIT');
  }
  if (!Array.isArray(request.subjects) || request.subjects.length < 1 || request.subjects.length > 16) {
    throw new TypeError('GRANT_SUBJECT_LIMIT');
  }
  const subjects = request.subjects.map(row => {
    exactKeys(row, ['subject_id', 'uuid', 'entity_type'], 'GRANT_SUBJECT');
    identifier(row.subject_id);
    if (typeof row.uuid !== 'string' ||
        !/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/.test(row.uuid) ||
        !resource(row.entity_type) || row.entity_type === 'minecraft:player') {
      throw new TypeError('INVALID_GRANT_SUBJECT');
    }
    return { subjectId: row.subject_id, uuid: row.uuid, entityType: row.entity_type };
  });
  if (new Set(subjects.map(s => s.subjectId)).size !== subjects.length ||
      new Set(subjects.map(s => s.uuid)).size !== subjects.length) {
    throw new TypeError('DUPLICATE_GRANT_SUBJECT');
  }
  exactKeys(request.budgets, ['time_budget_ms', 'max_actions', 'max_captures'], 'GRANT_BUDGET');
  integer(request.budgets.time_budget_ms, 1, 120000);
  integer(request.budgets.max_actions, 0, 32);
  integer(request.budgets.max_captures, 0, 16);
  if (!Array.isArray(request.initial_state) || !Array.isArray(request.actions) ||
      request.initial_state.length + request.actions.length > request.budgets.max_actions) {
    throw new TypeError('GRANT_ACTION_BUDGET');
  }
  const actions = [...new Set([...request.initial_state, ...request.actions].map(a => a.operation))].sort();
  const allowed = selection.allowedActions;
  if (!Array.isArray(allowed) || allowed.length > 3 || new Set(allowed).size !== allowed.length ||
      allowed.some(action => !['wait_ticks', 'teleport_subject', 'set_block'].includes(action)) ||
      stableJson([...allowed].sort()) !== stableJson(actions)) {
    throw new TypeError('GRANT_ACTION_SCOPE');
  }
  return {
    schemaVersion: 1, grantId: selection.grantId, ...identity,
    experimentId: request.experiment_id, requestHash: hashId(requestHash), generation: request.generation,
    arenaId: request.arena.arena_id, arenaEpoch: selection.arenaEpoch,
    expectedArenaRevision: selection.expectedArenaRevision,
    baselineHash: hashId(request.arena.baseline_hash), bounds: structuredClone(bounds), subjects,
    leaseId: selection.leaseId, timeBudgetMs: request.budgets.time_budget_ms,
    maxActions: request.budgets.max_actions, maxCaptures: request.budgets.max_captures,
    allowedActions: [...allowed],
  };
}
