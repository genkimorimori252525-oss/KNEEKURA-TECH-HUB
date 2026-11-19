import assert from 'node:assert/strict';
import os from 'node:os';
import path from 'node:path';
import { mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import {
  assessProcessOwnership,
  doctor,
  expandTemplate,
  inspectGitWorkspace,
  launchDebugRun,
  readCurrent,
  readStartupTimeline,
  stopCurrent,
  validateBuildMarker,
  writeG1Acceptance,
  validateReadyManifest
} from './core.mjs';
import {
  clearTargetControl,
  normalizeTargetUuid,
  readTargetControl,
  setTargetControl
} from './evidence/target-control.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const FIXTURE = path.join(HERE, 'fixtures', 'fake-target.mjs');

function stopAssertionDiagnostics(stopped) {
  return JSON.stringify({
    status: stopped.status,
    live: stopped.live,
    cleanup: {
      status: stopped.cleanup?.status ?? null,
      elapsedMs: Number.isFinite(stopped.cleanup?.elapsedMs) ? stopped.cleanup.elapsedMs : null,
      observations: (stopped.cleanup?.observations ?? []).map(observed => ({
        exists: observed?.exists === true,
        inspectionError: Boolean(observed?.inspectionError),
      })),
    },
    evidenceShutdownStatus: stopped.evidenceShutdown?.status ?? null,
  });
}

const temp = await mkdtemp(path.join(os.tmpdir(), 'kneekura-debug-'));

try {
  const gitVersion = spawnSync('git', ['--version'], { encoding: 'utf8' });
  if (!gitVersion.error && gitVersion.status === 0) {
    const scopeRepo = path.join(temp, 'scope-repo');
    const labScope = path.join(scopeRepo, 'departments', 'minecraft', 'lab');
    await mkdir(labScope, { recursive: true });
    await writeFile(path.join(labScope, 'observer.txt'), 'observer-v1\n', 'utf8');
    await writeFile(path.join(scopeRepo, 'unrelated.txt'), 'unrelated-v1\n', 'utf8');

    const git = (args) => {
      const result = spawnSync('git', args, { cwd: scopeRepo, encoding: 'utf8' });
      assert.equal(result.status, 0, result.stderr || result.stdout || args.join(' '));
    };
    git(['init']);
    git(['config', 'user.email', 'selftest@example.invalid']);
    git(['config', 'user.name', 'KNEEKURA selftest']);
    git(['add', '.']);
    git(['commit', '-m', 'fixture']);

    const labBefore = await inspectGitWorkspace(labScope);
    assert.equal(labBefore.available, true, JSON.stringify(labBefore));
    assert.equal(labBefore.dirty, false);

    await writeFile(path.join(scopeRepo, 'unrelated.txt'), 'unrelated-v2\n', 'utf8');
    const labAfterUnrelated = await inspectGitWorkspace(labScope);
    assert.equal(labAfterUnrelated.dirty, false, JSON.stringify(labAfterUnrelated));
    assert.equal(labAfterUnrelated.fingerprintSha256, labBefore.fingerprintSha256);

    await writeFile(path.join(labScope, 'observer.txt'), 'observer-v2\n', 'utf8');
    const labAfterObserver = await inspectGitWorkspace(labScope);
    assert.equal(labAfterObserver.dirty, true, JSON.stringify(labAfterObserver));
    assert.notEqual(labAfterObserver.fingerprintSha256, labBefore.fingerprintSha256);
  }

  const config = {
    schemaVersion: 1,
    workspaceId: 'selftest',
    workspaceDir: temp,
    runtimeRoot: path.join(temp, 'runtime'),
    readyTimeoutMs: 5000,
    launch: {
      command: process.execPath,
      args: [FIXTURE],
      shell: false,
      env: {}
    }
  };

  const d = await doctor(config, ROOT);
  assert.equal(d.ok, true, JSON.stringify(d));

  const integrationConfig = {
    ...config,
    workspaceChecks: [
      { path: 'build.gradle', contains: ['KNEEKURA_DEBUG_FORGE_BRIDGE_SRC'] },
      { path: 'gradlew.bat' }
    ]
  };
  await writeFile(path.join(temp, 'build.gradle'), 'plugins {}\n', 'utf8');
  await writeFile(path.join(temp, 'gradlew.bat'), '@echo off\n', 'utf8');

  const staleWorkspace = await doctor(integrationConfig, ROOT);
  assert.equal(staleWorkspace.ok, false);
  assert.ok(staleWorkspace.checks.some(
    (x) => x.name === 'workspaceCheck:build.gradle' && x.ok === false
  ));

  await writeFile(
    path.join(temp, 'build.gradle'),
    '// KNEEKURA_DEBUG_FORGE_BRIDGE_SRC\n',
    'utf8'
  );
  const compatibleWorkspace = await doctor(integrationConfig, ROOT);
  assert.equal(compatibleWorkspace.ok, true, JSON.stringify(compatibleWorkspace));

  const worldAwareConfig = {
    ...config,
    gameDir: path.join(temp, 'game'),
    worldName: 'KNEEKURA_DEBUG_WORLD',
    requireExistingWorld: true
  };
  await mkdir(path.join(temp, 'game', 'saves'), { recursive: true });
  const missingWorld = await doctor(worldAwareConfig, ROOT);
  assert.equal(missingWorld.ok, false);
  assert.ok(missingWorld.checks.some((x) => x.name === 'debugWorld' && x.ok === false));

  await mkdir(path.join(temp, 'game', 'saves', 'KNEEKURA_DEBUG_WORLD'), { recursive: true });
  const presentWorld = await doctor(worldAwareConfig, ROOT);
  assert.equal(presentWorld.ok, true, JSON.stringify(presentWorld));

  assert.equal(
    expandTemplate('x-${runId}-${runSnapshotId}-${processEpoch}-${runDir}', {
      runId: 'run-1',
      runSnapshotId: 'snapshot-1',
      processEpoch: '7',
      runDir: 'C:/debug/run-1'
    }),
    'x-run-1-snapshot-1-7-C:/debug/run-1'
  );

  const owned = assessProcessOwnership({
    pid: 1234,
    spawnedAtEpochMs: 10_000,
    launchCommand: 'gradlew.bat'
  }, {
    exists: true,
    pid: 1234,
    startedAtEpochMs: 10_250,
    commandLine: 'cmd.exe /c gradlew.bat runClient'
  });
  assert.equal(owned.owned, true, JSON.stringify(owned));

  const reusedPid = assessProcessOwnership({
    pid: 1234,
    spawnedAtEpochMs: 10_000,
    launchCommand: 'gradlew.bat'
  }, {
    exists: true,
    pid: 1234,
    startedAtEpochMs: 500_000,
    commandLine: 'cmd.exe /c gradlew.bat runClient'
  });
  assert.equal(reusedPid.owned, false);
  assert.equal(reusedPid.reason, 'start-time-mismatch');

  const wrongCommand = assessProcessOwnership({
    pid: 1234,
    spawnedAtEpochMs: 10_000,
    launchCommand: 'gradlew.bat'
  }, {
    exists: true,
    pid: 1234,
    startedAtEpochMs: 10_250,
    commandLine: 'java.exe -jar unrelated.jar'
  });
  assert.equal(wrongCommand.owned, false);
  assert.equal(wrongCommand.reason, 'launch-command-mismatch');

  const targetCurrent = {
    debugSessionId: 'sess-target',
    runId: 'run-target',
    runSnapshotId: 'snapshot-target',
    processEpoch: 3,
    runDir: path.join(temp, 'target-run')
  };

  const canonicalTarget = normalizeTargetUuid(
    'AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE'
  );
  assert.equal(
    canonicalTarget,
    'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
  );

  let invalidTargetRejected = false;
  try {
    normalizeTargetUuid('not-a-uuid');
  } catch (error) {
    invalidTargetRejected = /canonical UUID/.test(error.message);
  }
  assert.equal(invalidTargetRejected, true);

  const target1 = await setTargetControl(targetCurrent, canonicalTarget);
  assert.equal(target1.revision, 1);
  assert.equal(target1.targetUuid, canonicalTarget);

  const targetStatus1 = await readTargetControl(targetCurrent);
  assert.equal(targetStatus1.targetUuid, canonicalTarget);
  assert.equal(targetStatus1.revision, 1);

  const target2 = await clearTargetControl(targetCurrent);
  assert.equal(target2.revision, 2);
  assert.equal(target2.targetUuid, null);

  const staleTargetFile = target2.file;
  await writeFile(
    staleTargetFile,
    JSON.stringify({
      v: 1,
      debugSessionId: 'sess-other',
      runId: 'run-target',
      runSnapshotId: 'snapshot-other',
      processEpoch: 3,
      revision: 3,
      targetUuid: canonicalTarget,
      updatedAt: '2026-09-18T00:00:00Z'
    }) + '\n',
    'utf8'
  );
  let staleTargetRejected = false;
  try {
    await readTargetControl(targetCurrent);
  } catch (error) {
    staleTargetRejected = /identity mismatch/.test(error.message);
  }
  assert.equal(staleTargetRejected, true);

  const validBuild = validateBuildMarker({
    debugSessionId: 'sess-a',
    runId: 'run-a',
    handshakeNonce: 'nonce-a',
    builtAt: '2026-09-18T00:00:00Z'
  }, {
    debugSessionId: 'sess-a',
    runId: 'run-a',
    handshakeNonce: 'nonce-a'
  });
  assert.equal(validBuild.ok, true, JSON.stringify(validBuild));

  const staleBuild = validateBuildMarker({
    debugSessionId: 'sess-old',
    runId: 'run-old',
    handshakeNonce: 'nonce-old',
    builtAt: '2026-09-18T00:00:00Z'
  }, {
    debugSessionId: 'sess-new',
    runId: 'run-new',
    handshakeNonce: 'nonce-new'
  });
  assert.equal(staleBuild.ok, false);
  assert.ok(staleBuild.errors.some((x) => x.includes('debugSessionId mismatch')));
  assert.ok(staleBuild.errors.some((x) => x.includes('runId mismatch')));
  assert.ok(staleBuild.errors.some((x) => x.includes('handshakeNonce mismatch')));

  const stale = validateReadyManifest({
    protocolVersion: 'KNEEKURA_DEBUG_READY_V1',
    debugSessionId: 'old',
    runId: 'old',
    runSnapshotId: 'snapshot-old',
    worldName: 'OLD_WORLD',
    processEpoch: 1,
    handshakeNonce: 'old',
    status: 'DEBUG_READY',
    gates: { probeHandshake: true, debugWorldReady: true, runtimeAttested: true },
    runtime: {}
  }, {
    debugSessionId: 'new',
    runId: 'new',
    runSnapshotId: 'snapshot-new',
    worldName: 'KNEEKURA_DEBUG_WORLD',
    processEpoch: 1,
    handshakeNonce: 'new'
  });
  assert.equal(stale.ok, false);
  assert.ok(stale.errors.some((x) => x.includes('debugSessionId mismatch')));
  assert.ok(stale.errors.some((x) => x.includes('runId mismatch')));
  assert.ok(stale.errors.some((x) => x.includes('runSnapshotId mismatch')));
  assert.ok(stale.errors.some((x) => x.includes('worldName mismatch')));
  assert.ok(stale.errors.some((x) => x.includes('handshakeNonce mismatch')));

  const started = await launchDebugRun(config, ROOT);
  assert.equal(started.ok, true);
  assert.equal(started.status, 'DEBUG_READY');
  assert.equal(started.ready.runtime.kind, 'fake-debug-target');
  assert.ok(started.runSnapshotId);
  assert.ok(started.runSnapshotHash?.startsWith('sha256:'));
  assert.equal(started.ready.runSnapshotId, started.runSnapshotId);

  const snapshot = JSON.parse(
    await readFile(started.runSnapshotFile, 'utf8')
  );
  assert.equal(snapshot.snapshotId, started.runSnapshotId);
  assert.equal(snapshot.snapshotHash, started.runSnapshotHash);
  assert.equal(snapshot.runId, started.runId);
  assert.equal(snapshot.runtime.attestation.kind, 'fake-debug-target');

  const current = await readCurrent(config, ROOT);
  assert.equal(current.status, 'DEBUG_READY');
  assert.equal(current.live, true);
  assert.equal(current.runId, started.runId);
  assert.equal(current.debugSessionId, started.debugSessionId);
  assert.equal(current.runSnapshotId, started.runSnapshotId);
  assert.equal(current.runSnapshotHash, started.runSnapshotHash);

  let doubleStartRejected = false;
  try {
    await launchDebugRun(config, ROOT);
  } catch (error) {
    doubleStartRejected = /already active/.test(String(error.message));
  }
  assert.equal(doubleStartRejected, true, 'second launch must be rejected while runtime is live');

  const timeline = await readFile(path.join(started.runDir, 'timeline.jsonl'), 'utf8');
  const stages = timeline.trim().split('\n').map((line) => JSON.parse(line).stage);
  assert.ok(stages.includes('T0_RESTART_REQUESTED'));
  assert.ok(stages.includes('LAUNCHER_PROCESS_STARTED'));
  assert.ok(stages.includes('T1_BUILD_COMPLETE'));
  assert.ok(stages.includes('T2_JVM_STARTED'));
  assert.ok(stages.includes('T3_FORGE_INITIALIZED'));
  assert.ok(stages.includes('T6_PROBE_READY'));
  assert.ok(stages.includes('T7_DEBUG_WORLD_READY'));
  assert.ok(stages.includes('T8_DEBUG_READY'));

  const startup = await readStartupTimeline(config, ROOT);
  assert.equal(startup.ok, true, JSON.stringify(startup));
  assert.equal(startup.complete, true);
  assert.equal(startup.stages.length, 9);
  assert.ok(startup.totalStartupMs >= 0);

  const stopped = await stopCurrent(config, ROOT);
  assert.equal(stopped.ok, true, stopAssertionDiagnostics(stopped));
  assert.equal(stopped.status, 'STOPPED');
  assert.equal(stopped.evidenceShutdown?.clean, true);
  assert.equal(
    stopped.evidenceShutdown?.status,
    'CLEAN_EVIDENCE_SHUTDOWN'
  );
  assert.equal(stopped.evidenceShutdown?.ack?.remainingQueue, 0);

  const acceptance = await writeG1Acceptance(config, ROOT, {
    started,
    timeline: startup,
    status: current,
    stopped
  });
  assert.equal(acceptance.manifest.result, 'PASS');
  assert.equal(acceptance.manifest.runId, started.runId);
  assert.equal(acceptance.manifest.runSnapshotId, started.runSnapshotId);
  assert.equal(acceptance.manifest.runSnapshotHash, started.runSnapshotHash);
  const acceptanceOnDisk = JSON.parse(await readFile(acceptance.file, 'utf8'));
  assert.equal(acceptanceOnDisk.result, 'PASS');
  assert.equal(acceptanceOnDisk.timelineComplete, true);

  const afterStop = await readCurrent(config, ROOT);
  assert.equal(afterStop.live, false);
  assert.equal(afterStop.status, 'STOPPED');

  const restarted = await launchDebugRun(config, ROOT);
  assert.equal(restarted.status, 'DEBUG_READY');
  assert.notEqual(restarted.runId, started.runId);
  const stoppedAgain = await stopCurrent(config, ROOT);
  assert.equal(stoppedAgain.ok, true, stopAssertionDiagnostics(stoppedAgain));

  console.log('debug-workspace selftest OK');
} finally {
  await rm(temp, { recursive: true, force: true });
}
