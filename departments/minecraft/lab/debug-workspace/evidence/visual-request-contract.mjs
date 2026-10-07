import { exactKeys, hashId, identifier, integer } from '../bridge/json.mjs';

// Source parity: TECH minecraft/experiment_contract.py, request/action/assertion.
// This validates inert intent only; it grants no execution or capture authority.
const REQUEST_FIELDS = ['schema_version', 'experiment_id', 'generation', 'target',
  'arena', 'subjects', 'initial_state', 'actions', 'observation_scopes', 'visual_rig',
  'assertions', 'budgets'];
const TARGET_FIELDS = ['profile_id', 'index_snapshot_id', 'build_artifact_hash',
  'source_revision', 'dirty_hash', 'config_hash', 'resource_hash'];
const LANES = new Set(['SERVER_TICK', 'CLIENT_TICK', 'TARGET_TRACKED', 'ENTITY_STATE',
  'SERVER_TARGET_TRACKED', 'SERVER_ENTITY_STATE', 'AI_TARGET', 'BRAIN_MEMORY',
  'RUNNING_BEHAVIORS', 'BEHAVIOR_TRANSITION', 'NAVIGATION', 'PACKET_SEND',
  'PACKET_RECEIVE', 'PACKET_HANDLER', 'RENDER_ENTERED', 'YSM_ENTERED', 'YSM_COMPLETED',
  'ACTION_APPLIED', 'OBSERVATION_WRITTEN']);
const VISUAL_CHECKS = new Set(['feet_below_ground', 'mesh_clipping', 'texture_present',
  'wrong_facing', 'displaced_part', 'projectile_obstacle_side', 'subject_visible']);
const require = (condition, label) => { if (!condition) throw new TypeError(label); };
const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const number = (value, min, max) => typeof value === 'number' && Number.isFinite(value) && value >= min && value <= max;

function id(value) {
  identifier(value);
  // JS `$` also matches before a final newline; Python fullmatch does not.
  require(!/[^A-Za-z0-9._:-]/.test(value), 'INVALID_IDENTIFIER');
  return value;
}
function hash(value) {
  hashId(value);
  require(value.length === 64, 'INVALID_SHA256');
}
function uuid(value) {
  require(typeof value === 'string' && /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}(?![\s\S])/.test(value), 'CANONICAL_UUID_REQUIRED');
}
function resource(value) {
  require(typeof value === 'string' && value.length <= 128 &&
    /^[a-z0-9_]+:[a-z0-9_./-]+(?![\s\S])/.test(value) &&
    value.split(':')[1].split('/').every(part => !['', '.', '..'].includes(part)), 'INVALID_RESOURCE_ID');
}
function list(value, max, label, min = 0) {
  require(Array.isArray(value) && value.length >= min && value.length <= max, 'INVALID_' + label);
}
function vector(value, count, min, max, label) {
  require(Array.isArray(value) && value.length === count &&
    [...value].every(n => number(n, min, max)), 'INVALID_' + label);
}
function uniqueIds(rows, field, label) {
  const ids = new Set();
  for (const row of rows) {
    require(object(row), 'INVALID_' + label);
    const value = id(row[field]);
    require(!ids.has(value), 'DUPLICATE_' + label);
    ids.add(value);
  }
  return ids;
}
function position(value, bounds, block = false) {
  vector(value, 3, -30000000, 30000000, 'POSITION');
  require(value.every((n, i) => bounds.min[i] <= n && n < bounds.max[i]), 'ACTION_OUTSIDE_ARENA');
  if (block) require(value.every(Number.isInteger), 'INTEGER_BLOCK_POSITION_REQUIRED');
}
function action(value, subjects, bounds) {
  require(object(value), 'INVALID_ACTION');
  const base = ['action_id', 'operation'];
  switch (value.operation) {
    case 'wait_ticks':
      exactKeys(value, [...base, 'ticks'], 'WAIT_TICKS');
      integer(value.ticks, 1, 1200, 'WAIT_TICKS');
      break;
    case 'teleport_subject':
      exactKeys(value, [...base, 'subject_id', 'position', 'rotation'], 'TELEPORT_SUBJECT');
      require(subjects.has(value.subject_id), 'UNKNOWN_ACTION_SUBJECT');
      position(value.position, bounds);
      vector(value.rotation, 2, -180, 180, 'ROTATION');
      require(value.rotation[1] >= -90 && value.rotation[1] <= 90, 'INVALID_PITCH');
      break;
    case 'use_item':
      exactKeys(value, [...base, 'subject_id', 'hand', 'ticks'], 'USE_ITEM');
      require(subjects.has(value.subject_id) && ['main_hand', 'off_hand'].includes(value.hand), 'INVALID_ITEM_USE_SUBJECT_OR_HAND');
      integer(value.ticks, 1, 20, 'ITEM_USE_TICKS');
      break;
    case 'set_block':
      exactKeys(value, [...base, 'position', 'block'], 'SET_BLOCK');
      position(value.position, bounds, true);
      resource(value.block);
      break;
    default: throw new TypeError('UNSUPPORTED_EXPERIMENT_ACTION');
  }
}
function assertion(value, subjects, visual) {
  require(object(value), 'INVALID_ASSERTION');
  const base = ['assertion_id', 'kind', 'subject_id', 'expected'];
  require(subjects.has(value.subject_id), 'UNKNOWN_ASSERTION_SUBJECT');
  if (value.kind === 'visual') {
    exactKeys(value, [...base, 'check'], 'VISUAL_ASSERTION');
    require(visual && VISUAL_CHECKS.has(value.check) && ['YES', 'NO'].includes(value.expected), 'UNSUPPORTED_VISUAL_CHECK');
    return;
  }
  require(value.kind === 'structured', 'UNSUPPORTED_ASSERTION_KIND');
  exactKeys(value, [...base, 'field', 'operator'], 'STRUCTURED_ASSERTION');
  const { field, operator, expected } = value;
  require(typeof field === 'string' && (['health', 'alive', 'target_uuid', 'position', 'velocity', 'collision'].includes(field) || field.startsWith('effect.')), 'UNSUPPORTED_STRUCTURED_FIELD');
  if (field.startsWith('effect.')) resource(field.slice(7));
  require(['equals', 'less_than', 'greater_than'].includes(operator), 'UNSUPPORTED_ASSERTION_OPERATOR');
  if (['alive', 'collision'].includes(field) || field.startsWith('effect.')) {
    require(typeof expected === 'boolean' && operator === 'equals', 'BOOLEAN_ASSERTION_REQUIRES_EQUALS');
  } else if (['position', 'velocity'].includes(field)) {
    vector(expected, 3, -30000000, 30000000, 'EXPECTED_VECTOR');
    require(operator === 'equals', 'VECTOR_ASSERTION_REQUIRES_EQUALS');
  } else if (field === 'target_uuid') {
    uuid(expected);
    require(operator === 'equals', 'IDENTITY_ASSERTION_REQUIRES_EQUALS');
  } else {
    require(number(expected, 0, 1024), 'INVALID_EXPECTED_HEALTH');
  }
}

function detachedJSON(input) {
  // Reject JS-only values before JSON serialization can omit/coerce them.
  const ancestors = new Set();
  function visit(value, depth = 0) {
    require(depth <= 64, 'INVALID_REQUEST_JSON_DEPTH');
    if (value === null || typeof value === 'boolean' || typeof value === 'string') return;
    if (typeof value === 'number') { require(Number.isFinite(value), 'NON_FINITE_REQUEST_JSON'); return; }
    require(typeof value === 'object' && !ancestors.has(value), 'INVALID_REQUEST_JSON');
    require(Array.isArray(value) || Object.getPrototypeOf(value) === Object.prototype || Object.getPrototypeOf(value) === null, 'INVALID_REQUEST_JSON_OBJECT');
    require(Object.getOwnPropertySymbols(value).length === 0, 'INVALID_REQUEST_JSON_KEY');
    ancestors.add(value);
    if (Array.isArray(value)) {
      for (let i = 0; i < value.length; i++) { require(Object.hasOwn(value, i), 'SPARSE_REQUEST_JSON'); visit(value[i], depth + 1); }
      require(Object.keys(value).length === value.length, 'INVALID_REQUEST_JSON_ARRAY');
    } else {
      for (const descriptor of Object.values(Object.getOwnPropertyDescriptors(value))) {
        if (!descriptor.enumerable) continue;
        require(Object.hasOwn(descriptor, 'value'), 'INVALID_REQUEST_JSON_ACCESSOR');
        visit(descriptor.value, depth + 1);
      }
    }
    ancestors.delete(value);
  }
  visit(input);
  require(Buffer.byteLength(JSON.stringify(input), 'utf8') <= 128 * 1024, 'EXPERIMENT_REQUEST_SIZE_LIMIT');
  return structuredClone(input);
}

/** Pure, detached validation of the complete TECH ExperimentRequest contract. */
export function validateVisualExperimentRequest(input) {
  try {
    const r = detachedJSON(input);
    exactKeys(r, REQUEST_FIELDS, 'EXPERIMENT_REQUEST');
    integer(r.schema_version, 1, 1, 'SCHEMA_VERSION');
    integer(r.generation, 1, 1000000, 'GENERATION');
    id(r.experiment_id);
    exactKeys(r.target, TARGET_FIELDS, 'TARGET');
    for (const field of TARGET_FIELDS) {
      if (field === 'source_revision') require(typeof r.target[field] === 'string' && /^(?:[a-f0-9]{40}|[a-f0-9]{64})(?![\s\S])/.test(r.target[field]), 'EXACT_SOURCE_REVISION_REQUIRED');
      else hash(r.target[field]);
    }
    exactKeys(r.arena, ['arena_id', 'preset', 'baseline_hash', 'bounds'], 'ARENA');
    id(r.arena.arena_id); id(r.arena.preset); hash(r.arena.baseline_hash);
    const bounds = r.arena.bounds;
    exactKeys(bounds, ['min', 'max'], 'ARENA_BOUNDS');
    for (const field of ['min', 'max']) {
      vector(bounds[field], 3, -30000000, 30000000, 'ARENA_BOUNDS');
      require(bounds[field].every(Number.isInteger), 'INTEGER_ARENA_BOUNDS_REQUIRED');
    }
    require(bounds.max.every((n, i) => n - bounds.min[i] > 0 && n - bounds.min[i] <= 64), 'ARENA_EDGE_LIMIT');
    require(bounds.min[1] >= -64 && bounds.max[1] <= 320, 'ARENA_HEIGHT_LIMIT');
    list(r.subjects, 16, 'SUBJECTS', 1);
    const subjects = uniqueIds(r.subjects, 'subject_id', 'SUBJECT_ID');
    const uuids = new Set();
    for (const row of r.subjects) {
      exactKeys(row, ['subject_id', 'uuid', 'entity_type'], 'SUBJECT');
      uuid(row.uuid); resource(row.entity_type);
      require(!uuids.has(row.uuid), 'DUPLICATE_SUBJECT_UUID'); uuids.add(row.uuid);
    }
    for (const field of ['initial_state', 'actions']) list(r[field], 32, field.toUpperCase());
    const actions = [...r.initial_state, ...r.actions];
    require(actions.length <= 32, 'TOTAL_ACTION_LIMIT');
    uniqueIds(actions, 'action_id', 'ACTION_ID');
    for (const row of actions) action(row, subjects, bounds);
    list(r.observation_scopes, 16, 'OBSERVATION_SCOPES', 1);
    const scopeIds = new Set();
    for (const scope of r.observation_scopes) {
      exactKeys(scope, ['kind', 'subject_id', 'lanes', 'level'], 'OBSERVATION_SCOPE');
      require(scope.kind === 'ENTITY_UUID' && subjects.has(scope.subject_id) && ['L0', 'L1', 'L2', 'L3', 'L4'].includes(scope.level), 'UNSUPPORTED_OBSERVATION_SCOPE');
      list(scope.lanes, 16, 'OBSERVATION_LANES', 1);
      require(scope.lanes.every(lane => typeof lane === 'string' && LANES.has(lane)) && new Set(scope.lanes).size === scope.lanes.length, 'INVALID_OBSERVATION_LANES');
      const identity = JSON.stringify([scope.subject_id, scope.level]);
      require(!scopeIds.has(identity), 'DUPLICATE_OBSERVATION_SCOPE'); scopeIds.add(identity);
    }
    const rig = r.visual_rig;
    require(object(rig), 'INVALID_VISUAL_RIG');
    const visual = ['cardinal-4-snapshot-v1','tank-cardinal-4-snapshot-v2'].includes(rig.mode);
    const mobPov = rig.mode === 'mob-eye-live-v1';
    if (visual || mobPov) {
      exactKeys(rig, ['mode', 'fov', 'viewport'], 'VISUAL_RIG');
      require(number(rig.fov, 30, 100), 'INVALID_VISUAL_FOV');
      vector(rig.viewport, 2, 64, 2048, 'VIEWPORT');
      require(rig.viewport.every(Number.isInteger), 'INTEGER_VIEWPORT_REQUIRED');
    } else {
      exactKeys(rig, ['mode'], 'VISUAL_RIG');
      require(rig.mode === 'none', 'UNSUPPORTED_VISUAL_RIG');
    }
    list(r.assertions, 32, 'ASSERTIONS', 1);
    uniqueIds(r.assertions, 'assertion_id', 'ASSERTION_ID');
    for (const row of r.assertions) assertion(row, subjects, visual);
    const budgets = r.budgets;
    exactKeys(budgets, ['time_budget_ms', 'max_actions', 'max_captures'], 'BUDGETS');
    integer(budgets.time_budget_ms, 1, 120000, 'TIME_BUDGET');
    integer(budgets.max_actions, 0, 32, 'ACTION_BUDGET');
    integer(budgets.max_captures, 0, 16, 'CAPTURE_BUDGET');
    require(actions.length <= budgets.max_actions, 'ACTIONS_EXCEED_BUDGET');
    require(visual ? budgets.max_captures >= 4 : mobPov || budgets.max_captures === 0, 'CAPTURE_BUDGET_RIG_MISMATCH');
    require(actions.reduce((sum, row) => sum + (row.ticks ?? 0), 0) * 50 <= budgets.time_budget_ms, 'TICKS_EXCEED_TIME_BUDGET');
    return r;
  } catch (error) {
    if (error instanceof TypeError) throw error;
    throw new TypeError('MALFORMED_EXPERIMENT_REQUEST', { cause: error });
  }
}
