import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, readFile, rm, symlink, cp, readdir } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { sha256, stableJson } from '../json.mjs';
import { beginAction, recordActionOutcome } from '../action-journal.mjs';

async function api() { return import('../adapter.mjs'); }
async function fixture(t) {
  const root = await mkdtemp(path.join(os.tmpdir(), 'lab-adapter-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const inputRoot = path.join(root, 'inputs'), runtimeRoot = path.join(root, 'runtime');
  await mkdir(inputRoot); await mkdir(runtimeRoot);
  const target = { profile_id: 'a'.repeat(64), index_snapshot_id: 'b'.repeat(64), source_revision: 'c'.repeat(40), dirty_hash: 'd'.repeat(64), build_artifact_hash: sha256('build'), config_hash: sha256('config'), resource_hash: sha256('resource') };
  const request = { schema_version: 1, experiment_id: 'exp', generation: 1, target, arena: {arena_id: 'arena', baseline_hash: 'e'.repeat(64)}, subjects: [], initial_state: [], actions: [], observation_scopes: [], visual_rig: {mode:'none'}, assertions: [], budgets: {} };
  const bytes = stableJson(request), hash = sha256(bytes), directory = path.join(inputRoot, hash);
  await mkdir(directory);
  const binding = {schema_version:1, experiment_id:'exp', generation:1, request_hash:hash, target, arena_id:'arena', arena_baseline_hash:'e'.repeat(64), assertions_hash:sha256('[]')};
  for (const [name,value] of Object.entries({'request.json':bytes,'assertions.json':'[]','binding.json':stableJson(binding),'build.bin':'build','config.bin':'config','resource.bin':'resource'})) await writeFile(path.join(directory,name),value);
  return {root,directory,hash,owner:{schemaVersion:1,runtimeRoot,inputRoot,run:null}};
}
test('registered adapter writes only existing LAB registration and returns public summary', async t => {
  const f=await fixture(t), {invokeAdapter}=await api();
  const request={schemaVersion:1,operation:'register',requestHash:f.hash};
  const first=await invokeAdapter(f.owner,request), second=await invokeAdapter(f.owner,request);
  assert.deepEqual(first,second);
  assert.equal(first.requestHash,f.hash); assert.equal(first.execution,'NOT_RUN');
  assert.equal(first.runtimeAttestation,'NOT_ESTABLISHED');
  assert.equal(JSON.stringify(first).includes(f.root),false);
  assert.equal((await invokeAdapter(f.owner,{...request,operation:'inspect_registration'})).registrationHash,first.registrationHash);
});
test('never-seen inspection does not create state', async t => {
  const f=await fixture(t), {invokeAdapter}=await api();
  const result=await invokeAdapter(f.owner,{schemaVersion:1,operation:'inspect_registration',requestHash:'f'.repeat(64)});
  assert.equal(result.status,'NEVER_SEEN');
  await assert.rejects(readFile(path.join(f.owner.runtimeRoot,'bridge','registrations','f'.repeat(64),'registration.json')));
});
test('unsupported executable/mutation fields, bool versions, path hash and owner extensions reject', async t => {
  const f=await fixture(t), {invokeAdapter}=await api();
  const valid={schemaVersion:1,operation:'register',requestHash:f.hash};
  for (const request of [{...valid,operation:'execute'},{...valid,command:'secret'},{...valid,schemaVersion:true},{...valid,requestHash:'../else'}]) await assert.rejects(invokeAdapter(f.owner,request));
  await assert.rejects(invokeAdapter({...f.owner,executable:'anything'},valid));
  await assert.rejects(invokeAdapter({...f.owner,schemaVersion:true},valid));
});
test('tampered material and symlink input fail before registration', async t => {
  const f=await fixture(t), {invokeAdapter}=await api();
  await writeFile(path.join(f.directory,'build.bin'),'tampered');
  await assert.rejects(invokeAdapter(f.owner,{schemaVersion:1,operation:'register',requestHash:f.hash}));
  await writeFile(path.join(f.directory,'build.bin'),'build');
  await rm(path.join(f.directory,'config.bin')); await symlink(path.join(f.directory,'build.bin'),path.join(f.directory,'config.bin'));
  await assert.rejects(invokeAdapter(f.owner,{schemaVersion:1,operation:'register',requestHash:f.hash}));
});
test('reconciliation requires an exact configured run and never authorizes dispatch', async t => {
  const f=await fixture(t), {invokeAdapter}=await api();
  await assert.rejects(invokeAdapter(f.owner,{schemaVersion:1,operation:'reconcile_action',requestHash:f.hash,idempotencyKey:'a'}));
});

test('register rejects a different request in the selected hash directory before writes', async t => {
  const f = await fixture(t), { invokeAdapter } = await api();
  const requestedHash = 'f'.repeat(64);
  await cp(f.directory, path.join(f.owner.inputRoot, requestedHash), { recursive: true });
  await assert.rejects(invokeAdapter(f.owner, {
    schemaVersion: 1, operation: 'register', requestHash: requestedHash,
  }));
  assert.deepEqual(await readdir(f.owner.runtimeRoot), []);
});

async function recordedActionFixture(t) {
  const f = await fixture(t);
  const runDir = path.join(f.owner.runtimeRoot, 'run');
  await mkdir(runDir);
  const identity = { debugSessionId: 'session', runId: 'run', runSnapshotId: 'snapshot',
    processEpoch: 1, experimentId: 'exp', requestHash: f.hash };
  await writeFile(path.join(runDir, 'run-snapshot.json'), JSON.stringify({
    debugSessionId: identity.debugSessionId, runId: identity.runId,
    snapshotId: identity.runSnapshotId, processEpoch: identity.processEpoch,
    techHub: { experiment_id: identity.experimentId, request_hash: identity.requestHash },
  }));
  const arena = { schemaVersion: 1, arenaId: 'arena', arenaEpoch: 1, arenaRevision: 0,
    baselineHash: 'b'.repeat(64), bounds: { min: [0,64,0], max: [4,68,4] },
    allowedMutationBounds: { min: [0,64,0], max: [4,68,4] }, resetClasses: { blocks: 'RESETTABLE' } };
  const action = { schemaVersion: 1, debugSessionId: identity.debugSessionId, runId: identity.runId,
    runSnapshotId: identity.runSnapshotId, processEpoch: identity.processEpoch,
    experimentId: identity.experimentId, arenaId: 'arena', arenaEpoch: 1,
    expectedArenaRevision: 0, actionId: 'actual-action', idempotencyKey: 'actual-key',
    type: 'wait_ticks', args: { ticks: 1 } };
  const entry = await beginAction({ runDir, identity, arena, action });
  for (const status of ['ACCEPTED', 'APPLIED', 'VERIFIED']) {
    await recordActionOutcome({ runDir, identity, idempotencyKey: action.idempotencyKey,
      outcome: { status, evidenceHashes: ['c'.repeat(64)] } });
  }
  return { ...f, runDir, actionDirectory: entry.directory,
    owner: { ...f.owner, run: { runDir, identity } },
    query: { schemaVersion: 1, operation: 'reconcile_action', requestHash: f.hash,
      idempotencyKey: action.idempotencyKey } };
}

test('reconcile rejects a coherent journal copied under a different action key', async t => {
  const f = await recordedActionFixture(t), { invokeAdapter } = await api();
  await cp(f.actionDirectory, path.join(f.runDir, 'control', 'actions', sha256('other-key')),
    { recursive: true });
  await assert.rejects(invokeAdapter(f.owner, { ...f.query, idempotencyKey: 'other-key' }),
    /IDENTITY/);
  assert.equal((await invokeAdapter(f.owner, f.query)).status, 'VERIFIED');
});

test('reconcile rejects rehashed malformed evidence without publishing private values', async t => {
  for (const evidenceHashes of [
    ['/private/owner-secret-path'], '/private/owner-secret-path',
    { private: '/private/owner-secret-path' }, [], Array(33).fill('c'.repeat(64)),
  ]) {
    const f = await recordedActionFixture(t), { invokeAdapter } = await api();
    const file = path.join(f.actionDirectory, 'receipt-000003.json');
    const { receiptHash: ignored, ...body } = JSON.parse(await readFile(file));
    body.evidenceHashes = evidenceHashes;
    await writeFile(file, JSON.stringify({ ...body, receiptHash: sha256(stableJson(body)) }));
    const result = await invokeAdapter(f.owner, f.query);
    assert.equal(result.status, 'OUTCOME_UNKNOWN');
    assert.deepEqual(result.evidenceHashes, []);
    assert.equal(result.dispatchAllowed, false);
    assert.equal(JSON.stringify(result).includes('/private/'), false);
  }
});
