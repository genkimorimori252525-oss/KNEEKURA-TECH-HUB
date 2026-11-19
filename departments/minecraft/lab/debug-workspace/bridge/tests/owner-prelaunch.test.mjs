import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, readFile, readdir, rm, symlink } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { sha256, stableJson } from '../json.mjs';
import { prepareOwnerControl, readPreparedOwnerControl, ownerLaunchEnvironment } from '../owner-prelaunch.mjs';
import { buildRunSnapshot, writeImmutableRunSnapshot, launchDebugRun, stopCurrent } from '../../core.mjs';

import { ownerPrelaunchFixture as fixture } from './owner-prelaunch-fixtures.mjs';
import { maintenance } from './owner-tank-rotation-fixtures.mjs';

test('prelaunch creates exact fixed owner closure without runtime attestation claims', async t => {
  const f = await fixture(t); const prepared = await prepareOwnerControl(f.options);
  const loaded = await readPreparedOwnerControl({ runDir: f.runDir, envelopeHash: prepared.envelopeHash });
  assert.equal(loaded.envelope.requestHash, f.bridgeContext.binding.request_hash);
  assert.equal(loaded.grant.handshakeNonce, f.identity.handshakeNonce);
  assert.equal(loaded.ownerControlIntent.fullTargetAttestation, 'NOT_ESTABLISHED');
  assert.deepEqual(await readFile(path.join(f.runDir, 'control/owner-experiment-request.json')), f.bridgeContext.bytes.request);
  assert.equal((await readFile(path.join(f.runDir, 'control/owner-materials/build.jar'))).toString(), 'build');
  await assert.rejects(prepareOwnerControl(f.options), /EXIST|IMMUTABLE|RESERVED/);
});
for (const fault of ['request', 'material', 'world', 'permission', 'extra', 'class', 'actions']) {
  test(`reject invalid private operator registration before owner file writes: ${fault}`, async t => {
    const f = await fixture(t); const bad = structuredClone(f.operator);
    if (fault === 'request') bad.requestHash = '0'.repeat(64);
    if (fault === 'material') bad.materialDescriptor.buildArtifactHash = '0'.repeat(64);
    if (fault === 'world') bad.worldRegistration.worldName = 'SURVIVAL';
    if (fault === 'permission') bad.worldRegistration.permissions = ['*'];
    if (fault === 'extra') bad.command = 'anything';
    if (fault === 'class') bad.materialDescriptor.classResources[0].className = '../secret';
    if (fault === 'actions') bad.selection.allowedActions = ['use_item'];
    f.options.operatorRegistration = await f.select(bad);
    await assert.rejects(prepareOwnerControl(f.options));
    assert.deepEqual(await readdir(f.runDir), []);
  });
}
test('private world registration must be an actual canonical directory', async t => {
  const f = await fixture(t); const alias = path.join(f.root, 'world-link');
  // Windows directory junctions exercise the same canonical-root rejection without symlink privilege.
  await symlink(f.operator.worldRegistration.canonicalWorldRoot, alias, process.platform === 'win32' ? 'junction' : 'dir');
  f.operator.worldRegistration.canonicalWorldRoot = alias; f.options.operatorRegistration = await f.select();
  await assert.rejects(prepareOwnerControl(f.options));
});
test('read-only prepared verifier rejects altered copied bytes without creating storage', async t => {
  const f = await fixture(t); const p = await prepareOwnerControl(f.options);
  await writeFile(path.join(f.runDir, 'control/owner-materials/config.bin'), 'changed');
  await assert.rejects(readPreparedOwnerControl({ runDir: f.runDir, envelopeHash: p.envelopeHash }));
  const absent = path.join(f.root, 'absent');
  await assert.rejects(readPreparedOwnerControl({ runDir: absent, envelopeHash: 'a'.repeat(64) }));
  await assert.rejects(readdir(absent), { code: 'ENOENT' });
});
test('owner environment is forcibly disabled unless preparation succeeded', async t => {
  const f = await fixture(t); const env = { KEEP: 'x', KNEEKURA_DEBUG_OWNER_ENVELOPE_FILE: 'foreign', KNEEKURA_DEBUG_OWNER_ENVELOPE_SHA256: 'foreign' };
  assert.deepEqual(ownerLaunchEnvironment(env, null), { KEEP: 'x' });
  const p = await prepareOwnerControl(f.options); const enabled = ownerLaunchEnvironment(env, p);
  assert.equal(enabled.KNEEKURA_DEBUG_OWNER_ENVELOPE_FILE, path.join(f.runDir, 'control/owner-envelope.json'));
  assert.equal(enabled.KNEEKURA_DEBUG_OWNER_ENVELOPE_SHA256, p.envelopeHash);
});
test('initial canonical sidecar hashes exact body before immutable snapshot marker', async t => {
  const f = await fixture(t); const p = await prepareOwnerControl(f.options);
  const body = buildRunSnapshot({ schemaVersion: 1, snapshotId: 'snap', debugSessionId: 's', runId: 'r', processEpoch: 1,
    worldName: 'KNEEKURA_DEBUG_WORLD', runtime: { pid: process.pid, attestation: { topology: 'INTEGRATED_SERVER' } },
    value: 1.25 }, { ...f.bridgeContext, ownerControlIntent: p.ownerControlIntent });
  const snapshot = await writeImmutableRunSnapshot(path.join(f.runDir, 'run-snapshot.json'), body);
  const bytes = await readFile(path.join(f.runDir, 'run-snapshot.canonical.json'));
  assert.equal(snapshot.snapshotHash, 'sha256:' + sha256(bytes)); assert.equal(bytes.toString(), stableJson(body));
  const read = await readPreparedOwnerControl({ runDir: f.runDir, envelopeHash: p.envelopeHash, requireSnapshot: true });
  assert.equal(read.snapshot.bridge.ownerControlIntent.envelopeHash, p.envelopeHash);
  await assert.rejects(writeImmutableRunSnapshot(path.join(f.runDir, 'run-snapshot.json'), body));
  await writeFile(path.join(f.runDir, 'run-snapshot.canonical.json'), '{}');
  await assert.rejects(readPreparedOwnerControl({ runDir: f.runDir, envelopeHash: p.envelopeHash, requireSnapshot: true }));
});

test('existing private launch config opts in explicitly and cannot conflict with call options', async t => {
  const { ownerLaunchSelection } = await import('../owner-prelaunch.mjs');
  const f = await fixture(t);
  const config = { ownerControl: { requestHash: f.bridgeContext.binding.request_hash, operatorRegistration: f.options.operatorRegistration } };
  assert.deepEqual(ownerLaunchSelection(config, {}), config.ownerControl);
  assert.deepEqual(ownerLaunchSelection({}, {}), { requestHash: null, operatorRegistration: null });
  assert.throws(() => ownerLaunchSelection(config, { bridgeRequestHash: '0'.repeat(64) }));
  assert.throws(() => ownerLaunchSelection({}, { ownerRegistration: f.options.operatorRegistration }));
});

test('snapshot sidecar cannot redefine the existing canonical snapshot hash with alternate JSON formatting', async t => {
  const f = await fixture(t); const p = await prepareOwnerControl(f.options);
  const body = buildRunSnapshot({ schemaVersion: 1, snapshotId: 'snap', debugSessionId: 's', runId: 'r', processEpoch: 1,
    worldName: 'KNEEKURA_DEBUG_WORLD', runtime: { pid: process.pid, attestation: { topology: 'INTEGRATED_SERVER' } } },
    { ...f.bridgeContext, ownerControlIntent: p.ownerControlIntent });
  const snapshot = await writeImmutableRunSnapshot(path.join(f.runDir, 'run-snapshot.json'), body);
  const alternate = Buffer.from(JSON.stringify(body, null, 2));
  await writeFile(path.join(f.runDir, 'run-snapshot.canonical.json'), alternate);
  snapshot.snapshotHash = 'sha256:' + sha256(alternate);
  await writeFile(path.join(f.runDir, 'run-snapshot.json'), JSON.stringify(snapshot));
  await assert.rejects(readPreparedOwnerControl({ runDir: f.runDir, envelopeHash: p.envelopeHash, requireSnapshot: true }), /CANONICAL/);
});

test('concurrent readers observe an absent or complete snapshot commit marker', async t => {
  const f = await fixture(t);
  const file = path.join(f.runDir, 'run-snapshot.json');
  let finished = false;
  let absentReads = 0;
  const writing = writeImmutableRunSnapshot(file,
    { schemaVersion: 1, snapshotId: 'snap', data: 'x'.repeat(1900000) })
    .finally(() => { finished = true; });
  const reading = (async () => {
    do {
      let raw;
      try { raw = await readFile(file); }
      catch (error) {
        assert.equal(error.code, 'ENOENT');
        absentReads++;
      }
      if (raw) {
        const snapshot = JSON.parse(raw);
        const canonicalBody = await readFile(path.join(f.runDir, 'run-snapshot.canonical.json'));
        assert.equal(snapshot.snapshotHash, 'sha256:' + sha256(canonicalBody));
        assert.equal(snapshot.data.length, 1900000);
      }
      await new Promise(resolve => setImmediate(resolve));
    } while (!finished);
  })();
  await Promise.all([writing, reading]);
  assert.ok(absentReads > 0);
  const committed = JSON.parse(await readFile(file, 'utf8'));
  assert.equal(committed.data.length, 1900000);
});

test('canonical sidecar preserves the existing snapshot integer-key ordering', async () => {
  const { canonicalRunSnapshotBytes } = await import('../json.mjs');
  assert.equal(canonicalRunSnapshotBytes({ z: { 10: 'ten', 2: 'two' }, a: [1.25, null] }).toString(),
    '{"a":[1.25,null],"z":{"2":"two","10":"ten"}}');
});

for (const fault of ['schema', 'world', 'pid', 'topology']) test(`prepared reader rejects self-consistent foreign runtime snapshot: ${fault}`, async t => {
  const { canonicalRunSnapshotBytes } = await import('../json.mjs');
  const f = await fixture(t); const prepared = await prepareOwnerControl(f.options);
  const body = buildRunSnapshot({ schemaVersion: 1, snapshotId: 'snap', debugSessionId: 's', runId: 'r', processEpoch: 1,
    worldName: 'KNEEKURA_DEBUG_WORLD', runtime: { pid: process.pid, attestation: { topology: 'INTEGRATED_SERVER' } } },
    { ...f.bridgeContext, ownerControlIntent: prepared.ownerControlIntent });
  if (fault === 'schema') body.schemaVersion = true;
  if (fault === 'world') body.worldName = 'OTHER';
  if (fault === 'pid') body.runtime.pid = 0;
  if (fault === 'topology') body.runtime.attestation.topology = 'REMOTE_SERVER';
  const raw = canonicalRunSnapshotBytes(body);
  await writeFile(path.join(f.runDir, 'run-snapshot.canonical.json'), raw);
  await writeFile(path.join(f.runDir, 'run-snapshot.json'), JSON.stringify({ ...body, snapshotHash: 'sha256:' + sha256(raw) }));
  await assert.rejects(readPreparedOwnerControl({ runDir: f.runDir, envelopeHash: prepared.envelopeHash, requireSnapshot: true }));
});


for(const mode of ['ordinary','tankRotation']) test(`existing launch flow prepares ${mode} owner files before the source-only fixture starts and seals its initial snapshot`, async t => {
  const exec = promisify(execFile);
  const root = await mkdtemp(path.join(tmpdir(), 'owner-launch-source-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const workspace = path.join(root, 'workspace');
  await mkdir(workspace);
  await exec('git', ['init', '-q', workspace]);
  await writeFile(path.join(workspace, 'source.txt'), 'source-only fixture');
  await exec('git', ['-C', workspace, 'add', 'source.txt']);
  await exec('git', ['-C', workspace, '-c', 'user.name=Source Test', '-c', 'user.email=source@example.invalid', 'commit', '-qm', 'source fixture']);
  const revision = (await exec('git', ['-C', workspace, 'rev-parse', 'HEAD'])).stdout.trim();
  const f = await (mode==='ordinary'?fixture:maintenance)(null, path.join(root, 'fixture'), revision);
  const repoRoot = fileURLToPath(new URL('../../../', import.meta.url));
  const target = path.join(root, 'source-only-target.mjs');
  const original = await readFile(path.join(repoRoot, 'debug-workspace/fixtures/fake-target.mjs'), 'utf8');
  assert.ok(original.includes("kind: 'fake-debug-target',"));
  const probe = `
const ownerEnvelope = process.env.KNEEKURA_DEBUG_OWNER_ENVELOPE_FILE;
const ownerHash = process.env.KNEEKURA_DEBUG_OWNER_ENVELOPE_SHA256;
// Test-owned process deadline prevents a fixture leak even if OS inspection is unavailable.
setTimeout(() => process.exit(0), 6000).unref();
const envelope = JSON.parse(await readFile(ownerEnvelope, 'utf8'));
await writeFile(path.join(path.dirname(path.dirname(ownerEnvelope)), 'fixture-observed.json'), JSON.stringify({ ownerHash, envelope }));
`;
  await writeFile(target, original.replace('const now =', probe + '\nconst now =')
    .replace("kind: 'fake-debug-target',", "kind: 'fake-debug-target', topology: 'INTEGRATED_SERVER',"));
  const config = {
    schemaVersion: 1, workspaceId: 'owner-source-test', workspaceDir: workspace,
    runtimeRoot: f.runtimeRoot, readyTimeoutMs: 5000, worldName: 'KNEEKURA_DEBUG_WORLD',
    ownerControl: { requestHash: f.bridgeContext.binding.request_hash, operatorRegistration: f.options.operatorRegistration },
    launch: { command: process.execPath, args: [target], shell: false, env: {} },
  };
  let started;
  try {
    started = await launchDebugRun(config, repoRoot);
    const observed = JSON.parse(await readFile(path.join(started.runDir, 'fixture-observed.json'), 'utf8'));
    const prepared = await readPreparedOwnerControl({ runDir: started.runDir,
      envelopeHash: observed.ownerHash, requireSnapshot: true });
    assert.equal(observed.envelope.runSnapshotId, started.runSnapshotId);
    assert.equal(prepared.snapshot.runtime.pid, started.runtimePid);
    assert.equal(prepared.snapshot.bridge.ownerControlIntent.fullTargetAttestation, 'NOT_ESTABLISHED');
    assert.equal(prepared.snapshot.bridge.runtimeAttestation, 'NOT_ESTABLISHED');
    assert.equal(Boolean(prepared.tankRotation),mode==='tankRotation');
    if(prepared.tankRotation){
      for(const key of ['debugSessionId','runId','runSnapshotId','processEpoch','handshakeNonce'])assert.equal(prepared.tankRotation[key],observed.envelope[key]);
      assert.notEqual(prepared.tankRotation.runSnapshotId,f.identity.runSnapshotId);
      assert.equal(prepared.grant.maxActions,0);assert.equal(prepared.grant.maxCaptures,0);
    }
  } finally {
    if (started) {
      const stopped = await stopCurrent(config, repoRoot);
      // Stop classification can legitimately remain uncertain during a process-exit race.
      // Keep that production receipt unchanged and independently observe this test fixture's exit.
      const exitDeadline = Date.now() + 8000;
      while (true) {
        try { process.kill(started.pid, 0); }
        catch (error) {
          if (error.code === 'ESRCH') break;
          throw error;
        }
        assert.ok(Date.now() < exitDeadline, 'source fixture did not exit: ' + JSON.stringify(stopped));
        await new Promise(resolve => setTimeout(resolve, 50));
      }
      if (stopped.live === null) {
        const diagnostics = JSON.stringify(stopped);
        assert.equal(stopped.ok, false, diagnostics);
        assert.ok(['STOP_INSPECTION_UNKNOWN', 'STOP_INCOMPLETE'].includes(stopped.status), diagnostics);
        assert.ok(['INSPECTION_UNKNOWN', 'OWNERSHIP_CHANGED'].includes(stopped.cleanup?.status), diagnostics);
      } else assert.equal(stopped.live, false, JSON.stringify(stopped));
    }
  }
});


for (const fault of ['criteria', 'scope']) {
  const mutate = request => {
    if (fault === 'criteria') request.assertions[0].expected = 'twenty';
    if (fault === 'scope') request.observation_scopes[0].kind = 'ALL_ENTITIES';
  };
  test(`prelaunch rejects manually registered malformed ${fault} before any owner writes`, async t => {
    const f = await fixture(t, null, 'c'.repeat(40), mutate);
    await assert.rejects(prepareOwnerControl(f.options), /EXPECTED_HEALTH|OBSERVATION_SCOPE/);
    assert.deepEqual(await readdir(f.runDir), []);
  });
  test(`prepared reader independently rejects hash-consistent malformed ${fault}`, async t => {
    const f = await fixture(t);
    const prepared = await prepareOwnerControl(f.options);
    const request = structuredClone(prepared.request);
    mutate(request);
    const requestBytes = Buffer.from(JSON.stringify(request));
    const requestHash = sha256(requestBytes);
    const grantBytes = Buffer.from(stableJson({ ...prepared.grant, requestHash }));
    const envelopeBytes = Buffer.from(stableJson({ ...prepared.envelope,
      requestHash, grantHash: sha256(grantBytes) }));
    for (const [name, bytes] of [['owner-experiment-request.json', requestBytes],
      ['owner-grant.json', grantBytes], ['owner-envelope.json', envelopeBytes]]) {
      await writeFile(path.join(f.runDir, 'control', name), bytes);
    }
    await assert.rejects(readPreparedOwnerControl({ runDir: f.runDir,
      envelopeHash: sha256(envelopeBytes) }), /EXPECTED_HEALTH|OBSERVATION_SCOPE/);
  });
}
