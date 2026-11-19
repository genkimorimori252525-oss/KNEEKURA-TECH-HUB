import assert from 'node:assert/strict';
import test from 'node:test';
import { existsSync } from 'node:fs';
import { request, UUID, HASH } from './visual-fixture.mjs';

// Dynamic import makes the absent implementation an explicit RED assertion.
const moduleUrl = new URL('../visual-request-contract.mjs', import.meta.url);
const contract = existsSync(moduleUrl) ? await import(moduleUrl) : {};
const validate = input => {
  assert.equal(typeof contract.validateVisualExperimentRequest, 'function', 'request semantic validator must exist');
  return contract.validateVisualExperimentRequest(input);
};
const altered = change => { const value = request(); change(value); return value; };
const reject = change => assert.throws(() => validate(altered(change)), TypeError);
const accept = change => { const value = altered(change); assert.deepEqual(validate(value), value); };
const structured = (field, expected, operator = 'equals') => ({
  assertion_id: 'assert', kind: 'structured', subject_id: 'subject', field, operator, expected,
});
const visual = (check = 'subject_visible', expected = 'YES') => ({
  assertion_id: 'visual', kind: 'visual', subject_id: 'subject', check, expected,
});
const teleport = () => ({ action_id: 'teleport', operation: 'teleport_subject', subject_id: 'subject', position: [0, 1, 0], rotation: [0, 0] });
const useItem = () => ({ action_id: 'use', operation: 'use_item', subject_id: 'subject', hand: 'main_hand', ticks: 1 });
const setBlock = () => ({ action_id: 'block', operation: 'set_block', position: [0, 0, 0], block: 'minecraft:stone' });

// Same fixture as TECH tests/test_minecraft_experiment_contract.py::request.
function techRequest() {
  return { schema_version: 1, experiment_id: 'staff-repair-01', generation: 1,
    target: { profile_id: HASH, index_snapshot_id: HASH, build_artifact_hash: HASH,
      dirty_hash: HASH, config_hash: HASH, resource_hash: HASH, source_revision: 'b'.repeat(40) },
    arena: { arena_id: 'staff-arena', preset: 'normal', baseline_hash: 'c'.repeat(64), bounds: { min: [0, 60, 0], max: [16, 80, 16] } },
    subjects: [{ subject_id: 'player', uuid: '00000000-0000-4000-8000-000000000001', entity_type: 'minecraft:player' }],
    initial_state: [{ action_id: 'place', operation: 'teleport_subject', subject_id: 'player', position: [8, 64, 8], rotation: [0, 0] }],
    actions: [{ action_id: 'use', operation: 'use_item', subject_id: 'player', hand: 'main_hand', ticks: 1 }, { action_id: 'settle', operation: 'wait_ticks', ticks: 2 }],
    observation_scopes: [{ kind: 'ENTITY_UUID', subject_id: 'player', lanes: ['ENTITY_STATE', 'ACTION_APPLIED'], level: 'L2' }],
    visual_rig: { mode: 'cardinal-4-snapshot-v1', fov: 60, viewport: [320, 320] },
    assertions: [{ assertion_id: 'glow', kind: 'structured', subject_id: 'player', field: 'effect.minecraft:glowing', operator: 'equals', expected: true },
      { assertion_id: 'visible', kind: 'visual', subject_id: 'player', check: 'texture_present', expected: 'YES' }],
    budgets: { time_budget_ms: 30000, max_actions: 8, max_captures: 4 } };
}

test('accepts complete LAB and real TECH fixtures without mutating identities or order', () => {
  for (const original of [request(), techRequest()]) {
    const result = validate(original);
    assert.deepEqual(result, original);
    assert.notEqual(result, original);
    assert.notEqual(result.target, original.target);
    result.subjects[0].uuid = UUID;
    result.actions.reverse();
    assert.deepEqual(original, original.experiment_id === 'experiment' ? request() : techRequest());
  }
});

test('rejects missing or extra fields at every request object boundary', () => {
  for (const field of Object.keys(request())) reject(r => { delete r[field]; });
  for (const path of [[], ['target'], ['arena'], ['arena', 'bounds'], ['subjects', 0], ['actions', 0], ['observation_scopes', 0], ['visual_rig'], ['assertions', 0], ['budgets']]) {
    reject(r => { let object = r; for (const key of path) object = object[key]; object.command = 'execute'; });
    if (path.length) for (const field of Object.keys(path.reduce((object, key) => object[key], request()))) {
      reject(r => { let object = r; for (const key of path) object = object[key]; delete object[field]; });
    }
  }
});

test('requires bounded integer versions, generation and strict identifiers', () => {
  for (const value of [true, false, null, '1', 0, -1, 1.5, Infinity, NaN]) {
    reject(r => { r.schema_version = value; }); reject(r => { r.generation = value; });
  }
  reject(r => { r.schema_version = 2; }); reject(r => { r.generation = 1000001; });
  accept(r => { r.generation = 1000000; r.experiment_id = 'X' + 'x'.repeat(127); });
  for (const value of ['', '_subject', '__proto__', ' x', 'x\n', 'x\r', 'x'.repeat(129), {}, 1]) {
    for (const change of [r => { r.experiment_id = value; }, r => { r.arena.arena_id = value; }, r => { r.arena.preset = value; }, r => { r.subjects[0].subject_id = value; }, r => { r.actions[0].action_id = value; }, r => { r.assertions[0].assertion_id = value; }]) reject(change);
  }
});

test('requires every exact target hash and allows only full lowercase source revisions', () => {
  for (const field of Object.keys(request().target)) for (const value of ['HEAD', 'A'.repeat(64), 'a'.repeat(63), HASH + '\n', null, {}]) reject(r => { r.target[field] = value; });
  accept(r => { r.target.source_revision = 'f'.repeat(64); });
  reject(r => { r.target.source_revision = 'a'.repeat(40) + '\n'; });
  reject(r => { r.arena.baseline_hash = HASH + '\n'; });
});

test('enforces integer arena bounds, 64-block edges and Forge world height', () => {
  for (const bounds of [{ min: [0, 0, 0], max: [0, 1, 1] }, { min: [0, 0, 0], max: [65, 1, 1] }, { min: [0, -65, 0], max: [1, -1, 1] }, { min: [0, 300, 0], max: [1, 321, 1] }, { min: [0.5, 0, 0], max: [1, 1, 1] }, { min: [0, 0], max: [1, 1, 1] }, { min: [0, 0, -30000001], max: [1, 1, -30000000] }]) reject(r => { r.arena.bounds = bounds; });
  accept(r => { r.arena.bounds = { min: [-30000000, -64, 29999936], max: [-29999936, 0, 30000000] }; });
  accept(r => { r.arena.bounds = { min: [0, 256, 0], max: [64, 320, 64] }; });
});

test('checks bounded unique subjects, canonical UUIDs and safe resource IDs', () => {
  for (const value of [[], null, {}, Array.from({ length: 17 }, () => request().subjects[0])]) reject(r => { r.subjects = value; });
  reject(r => { r.subjects.push({ ...r.subjects[0], uuid: '00000000-0000-0000-0000-000000000002' }); });
  reject(r => { r.subjects.push({ ...r.subjects[0], subject_id: 'other' }); });
  for (const value of ['00000000000000000000000000000001', '{' + UUID + '}', '00000000-0000-ABCD-0000-000000000001', UUID + '\n', '', null, {}]) reject(r => { r.subjects[0].uuid = value; });
  for (const value of ['pig', 'Minecraft:pig', 'minecraft:../pig', 'minecraft:a//b', 'minecraft:a/./b', 'minecraft:a/', 'minecraft:/a', 'minecraft:a\\b', 'minecraft:pig\n', 'minecraft:' + 'a'.repeat(119)]) reject(r => { r.subjects[0].entity_type = value; });
  accept(r => { r.subjects[0].entity_type = 'mod_name:a.b/c-d_e'; });
  accept(r => { r.subjects[0].uuid = '00000000-0000-ffff-ffff-000000000000'; });
});

test('uses declared subject membership even for prototype-like names', () => {
  for (const id of ['constructor', 'toString', 'hasOwnProperty', '__proto__']) {
    for (const field of ['action', 'scope', 'assertion']) reject(r => {
      if (field === 'action') r.actions = [{ ...useItem(), subject_id: id }];
      if (field === 'scope') r.observation_scopes[0].subject_id = id;
      if (field === 'assertion') r.assertions[0].subject_id = id;
    });
  }
  accept(r => { r.subjects[0].subject_id = 'constructor'; r.observation_scopes[0].subject_id = 'constructor'; r.assertions[0].subject_id = 'constructor'; r.actions = [{ ...useItem(), subject_id: 'constructor' }]; });
});

test('validates all typed actions and combined action identity and count', () => {
  accept(r => { r.initial_state = [teleport(), setBlock()]; r.actions = [useItem(), r.actions[0]]; r.budgets.max_actions = 4; });
  for (const make of [teleport, setBlock, useItem]) {
    reject(r => { r.actions = [{ ...make(), command: '/op' }]; });
    for (const key of Object.keys(make())) reject(r => { r.actions = [make()]; delete r.actions[0][key]; });
  }
  for (const operation of ['command', null, {}, '__proto__']) reject(r => { r.actions[0].operation = operation; });
  for (const field of ['initial_state', 'actions']) for (const value of [null, {}, Array.from({ length: 33 }, (_, i) => ({ action_id: 'a' + i, operation: 'wait_ticks', ticks: 1 }))]) reject(r => { r[field] = value; });
  reject(r => { r.initial_state = [{ ...r.actions[0] }]; r.budgets.max_actions = 2; });
  reject(r => { r.initial_state = Array.from({ length: 16 }, (_, i) => ({ action_id: 'i' + i, operation: 'wait_ticks', ticks: 1 })); r.actions = Array.from({ length: 17 }, (_, i) => ({ action_id: 'a' + i, operation: 'wait_ticks', ticks: 1 })); r.budgets.max_actions = 32; });
  accept(r => { r.actions = []; r.budgets.max_actions = 0; });
});

test('bounds action positions, block integers, rotations, hands and ticks', () => {
  for (const make of [teleport, setBlock]) for (const position of [[8, 0, 0], [-8.1, 0, 0], [0, 16, 0], [0, 0, -8.1], [0, NaN, 0], [0, 0], [0, true, 0]]) reject(r => { r.actions = [{ ...make(), position }]; });
  accept(r => { r.actions = [{ ...teleport(), position: [-8, 0.5, -8], rotation: [-180, 90] }]; });
  reject(r => { r.actions = [{ ...setBlock(), position: [0.5, 0, 0] }]; });
  reject(r => { r.actions = [{ ...setBlock(), block: 'minecraft:../stone' }]; });
  for (const rotation of [[181, 0], [0, 91], [0, -91], [0], [false, 0], [0, Infinity]]) reject(r => { r.actions = [{ ...teleport(), rotation }]; });
  for (const ticks of [0, -1, 1201, true, 1.5, '1', null]) reject(r => { r.actions[0].ticks = ticks; });
  accept(r => { r.actions[0].ticks = 1200; r.budgets.time_budget_ms = 60000; });
  for (const ticks of [0, 21, true, 1.5, '1']) reject(r => { r.actions = [{ ...useItem(), ticks }]; });
  for (const hand of ['', 'MAIN_HAND', null, {}]) reject(r => { r.actions = [{ ...useItem(), hand }]; });
  accept(r => { r.actions = [{ ...useItem(), hand: 'off_hand', ticks: 20 }]; });
});

const lanes = ['SERVER_TICK', 'CLIENT_TICK', 'TARGET_TRACKED', 'ENTITY_STATE', 'SERVER_TARGET_TRACKED', 'SERVER_ENTITY_STATE', 'AI_TARGET', 'BRAIN_MEMORY', 'RUNNING_BEHAVIORS', 'BEHAVIOR_TRANSITION', 'NAVIGATION', 'PACKET_SEND', 'PACKET_RECEIVE', 'PACKET_HANDLER', 'RENDER_ENTERED', 'YSM_ENTERED', 'YSM_COMPLETED', 'ACTION_APPLIED', 'OBSERVATION_WRITTEN'];
test('requires unique bounded typed observation scopes and all supported lanes', () => {
  for (const lane of lanes) accept(r => { r.observation_scopes[0].lanes = [lane]; });
  for (const level of ['L0', 'L1', 'L2', 'L3', 'L4']) accept(r => { r.observation_scopes[0].level = level; });
  for (const scopes of [[], null, {}, Array.from({ length: 17 }, () => request().observation_scopes[0])]) reject(r => { r.observation_scopes = scopes; });
  for (const value of [[], null, {}, ['SERVER_TICK', 'SERVER_TICK'], ['__proto__'], [null], [{}], lanes.slice(0, 17)]) reject(r => { r.observation_scopes[0].lanes = value; });
  reject(r => { r.observation_scopes[0].kind = 'ALL_ENTITIES'; });
  reject(r => { r.observation_scopes[0].level = 'L5'; });
  reject(r => { r.observation_scopes.push({ ...r.observation_scopes[0], lanes: ['SERVER_TICK'] }); });
  accept(r => { r.observation_scopes.push({ ...r.observation_scopes[0], level: 'L2' }); r.observation_scopes[0].lanes = lanes.slice(0, 16); });
});

test('validates rig modes, finite FOV, integer viewport and capture budgets', () => {
  for (const fov of [29.9, 100.1, NaN, Infinity, true, '60']) reject(r => { r.visual_rig.fov = fov; });
  for (const viewport of [[63, 64], [64, 2049], [64.5, 64], [64], [true, 64], '64,64']) reject(r => { r.visual_rig.viewport = viewport; });
  for (const mode of ['other', null, {}, '__proto__']) reject(r => { r.visual_rig = { mode }; });
  accept(r => { r.visual_rig = { mode: 'cardinal-4-snapshot-v1', fov: 30, viewport: [64, 2048] }; });
  accept(r => { r.visual_rig.fov = 100; });
  accept(r => { r.visual_rig = { mode: 'none' }; r.budgets.max_captures = 0; });
  reject(r => { r.visual_rig = { mode: 'none', fov: 60 }; r.budgets.max_captures = 0; });
  reject(r => { r.visual_rig = { mode: 'none' }; });
  reject(r => { r.visual_rig = { mode: 'none' }; r.budgets.max_captures = 0; r.assertions = [visual()]; });
  reject(r => { r.budgets.max_captures = 3; });
});

test('checks every visual assertion enum and exact YES/NO expectations', () => {
  for (const check of ['feet_below_ground', 'mesh_clipping', 'texture_present', 'wrong_facing', 'displaced_part', 'projectile_obstacle_side', 'subject_visible']) for (const expected of ['YES', 'NO']) accept(r => { r.assertions = [visual(check, expected)]; });
  for (const check of ['arbitrary', '__proto__', null, {}]) reject(r => { r.assertions = [visual(check)]; });
  for (const expected of [true, 'PASS', 'yes', 1, null, {}]) reject(r => { r.assertions = [visual('subject_visible', expected)]; });
  for (const key of Object.keys(visual())) reject(r => { r.assertions = [visual()]; delete r.assertions[0][key]; });
});

test('checks typed structured assertions and forbids mismatched operators', () => {
  for (const field of ['alive', 'collision', 'effect.minecraft:glowing']) {
    for (const expected of [true, false]) accept(r => { r.assertions = [structured(field, expected)]; });
    for (const expected of [0, 1, 'true', null]) reject(r => { r.assertions = [structured(field, expected)]; });
    reject(r => { r.assertions = [structured(field, true, 'less_than')]; });
  }
  for (const field of ['position', 'velocity']) {
    accept(r => { r.assertions = [structured(field, [-30000000, 0.5, 30000000])]; });
    for (const expected of [[0, 0], [0, 0, 30000001], [0, false, 0], [0, Infinity, 0]]) reject(r => { r.assertions = [structured(field, expected)]; });
    reject(r => { r.assertions = [structured(field, [0, 0, 0], 'greater_than')]; });
  }
  accept(r => { r.assertions = [structured('target_uuid', UUID)]; });
  reject(r => { r.assertions = [structured('target_uuid', UUID.toUpperCase().replace(/1$/, 'A'))]; });
  reject(r => { r.assertions = [structured('target_uuid', UUID, 'less_than')]; });
  for (const operator of ['equals', 'less_than', 'greater_than']) for (const expected of [0, 0.5, 1024]) accept(r => { r.assertions = [structured('health', expected, operator)]; });
  for (const expected of [-0.1, 1024.1, true, null, '1', NaN, Infinity]) reject(r => { r.assertions = [structured('health', expected)]; });
  for (const field of ['__proto__', 'command', 'effect.', 'effect.minecraft:../x', null, {}]) reject(r => { r.assertions = [structured(field, true)]; });
  reject(r => { r.assertions = [structured('health', 1, 'evaluate')]; });
});

test('requires bounded unique assertions and rejects malformed object members', () => {
  for (const value of [[], null, {}, Array.from({ length: 33 }, (_, i) => ({ ...structured('health', 1), assertion_id: 'a' + i }))]) reject(r => { r.assertions = value; });
  reject(r => { r.assertions.push({ ...r.assertions[0] }); });
  reject(r => { r.assertions[0].kind = 'executable'; });
  for (const [field, values] of [['subjects', [null, true, []]], ['actions', [null, true, []]], ['assertions', [null, true, []]], ['observation_scopes', [null, true, []]]]) for (const value of values) reject(r => { r[field] = [value]; });
});

test('enforces all budget ranges and aggregate ticks across both action lists', () => {
  for (const [field, min, max] of [['time_budget_ms', 1, 120000], ['max_actions', 0, 32], ['max_captures', 0, 16]]) for (const value of [min - 1, max + 1, true, 1.5, '1', null]) reject(r => { r.budgets[field] = value; });
  reject(r => { r.budgets.max_actions = 0; });
  reject(r => { r.budgets.time_budget_ms = 249; });
  accept(r => { r.budgets.time_budget_ms = 250; });
  reject(r => { r.initial_state = [useItem()]; r.budgets.max_actions = 2; r.budgets.time_budget_ms = 299; });
  accept(r => { r.initial_state = [useItem()]; r.budgets.max_actions = 2; r.budgets.time_budget_ms = 300; });
  accept(r => { r.actions = []; r.budgets = { time_budget_ms: 1, max_actions: 0, max_captures: 16 }; });
});

test('rejects non-JSON, cyclic, sparse and oversized inputs with TypeError', () => {
  for (const value of [null, true, [], 'request', undefined, new Map()]) assert.throws(() => validate(value), TypeError);
  for (const value of [undefined, () => {}, 1n, Symbol('value'), new Date()]) reject(r => { r.target.config_hash = value; });
  reject(r => { r.extra = r; });
  reject(r => { r.actions = Array(1); });
  reject(r => { r.experiment_id = 'x'.repeat(128 * 1024); });
  reject(r => { Object.defineProperty(r.target, '__proto__', { value: { command: true }, enumerable: true }); });
});
