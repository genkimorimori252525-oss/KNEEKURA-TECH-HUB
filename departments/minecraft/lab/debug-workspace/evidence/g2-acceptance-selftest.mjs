import assert from 'node:assert/strict';
import os from 'node:os';
import path from 'node:path';
import {
  mkdtemp,
  readFile,
  rm,
} from 'node:fs/promises';

import { EvidenceRuntime } from './runtime.mjs';
import {
  G2_CORE_REQUIRED_LANES,
  G2_GLOBAL_REQUIRED_LANES,
  planG2CaptureWindow,
  waitForG2Evidence,
  writeG2Acceptance,
} from './g2-acceptance.mjs';

const entityUuid = '00000000-0000-0000-0000-000000000042';

function baseObservation({
  lane,
  side,
  seq,
  writerId,
  payload = {},
  level = 'L1',
  scope = {
    kind: 'ENTITY_UUID',
    entityUuid,
  },
}) {
  return {
    processEpoch: 1,
    arenaEpoch: 0,
    resourceEpoch: 0,
    writerId,
    writerSeq: seq,
    level,
    lane,
    observedAt: new Date().toISOString(),
    gameTime: 100 + seq,
    scope,
    source: {
      side,
      method: 'g2-acceptance-selftest',
    },
    epistemicStatus: 'OBSERVED',
    completeness: {
      complete: true,
    },
    payload,
  };
}

async function populateCore(runtime, options = {}) {
  let clientSeq = 0;
  let serverSeq = 0;

  for (const lane of G2_GLOBAL_REQUIRED_LANES) {
    const client = lane === 'CLIENT_TICK';
    const side =
      options.wrongSideLane === lane
        ? (client ? 'SERVER' : 'CLIENT')
        : (client ? 'CLIENT' : 'SERVER');
    const seq = client ? ++clientSeq : ++serverSeq;
    const writerId = client ? 'probe-client' : 'probe-server';

    await runtime.store.appendObservation(baseObservation({
      lane,
      side,
      seq,
      writerId,
      level: 'L0',
      scope: { kind: 'GLOBAL_HEALTH' },
      payload: {
        heartbeat: true,
        queueDepth: 0,
        droppedTotal: 0,
      },
    }));
  }

  for (const lane of G2_CORE_REQUIRED_LANES) {
    const client = lane === 'TARGET_TRACKED' || lane === 'ENTITY_STATE';
    const side =
      options.wrongSideLane === lane
        ? (client ? 'SERVER' : 'CLIENT')
        : (client ? 'CLIENT' : 'SERVER');

    const seq = client ? ++clientSeq : ++serverSeq;
    const writerId = client ? 'probe-client' : 'probe-server';
    const payload =
      lane === 'TARGET_TRACKED' || lane === 'SERVER_TARGET_TRACKED'
        ? { tracked: true, targetRevision: 1 }
        : { selftest: true, lane, targetRevision: 1 };

    await runtime.store.appendObservation(baseObservation({
      lane,
      side,
      seq,
      writerId,
      payload,
    }));
  }
}

const temp = await mkdtemp(path.join(os.tmpdir(), 'kneekura-g2-acceptance-'));

try {
  const passRunDir = path.join(temp, 'pass-run');
  const passRuntime = new EvidenceRuntime({
    runDir: passRunDir,
    debugSessionId: 'sess-g2-pass',
    runId: 'run-g2-pass',
    runSnapshotId: 'snapshot-g2-pass',
    processEpoch: 1,
  });
  await passRuntime.init();
  await populateCore(passRuntime);

  const passCurrent = {
    debugSessionId: 'sess-g2-pass',
    runId: 'run-g2-pass',
    runSnapshotId: 'snapshot-g2-pass',
    processEpoch: 1,
  };

  const gate = await waitForG2Evidence({
    runtime: passRuntime,
    current: passCurrent,
    entityUuid,
    targetRevision: 1,
    timeoutMs: 500,
    pollMs: 10,
  });
  assert.equal(gate.ok, true, JSON.stringify(gate, null, 2));
  assert.deepEqual(
    gate.globalRequiredLanes,
    G2_GLOBAL_REQUIRED_LANES
  );
  assert.deepEqual(gate.requiredLanes, G2_CORE_REQUIRED_LANES);
  assert.equal(gate.globalLanes.CLIENT_TICK.sourceSide, 'CLIENT');
  assert.equal(gate.globalLanes.SERVER_TICK.sourceSide, 'SERVER');
  assert.equal(gate.lanes.TARGET_TRACKED.sourceSide, 'CLIENT');
  assert.equal(gate.lanes.AI_TARGET.sourceSide, 'SERVER');

  const requiredGateObservationIds =
    G2_CORE_REQUIRED_LANES.map(
      (lane) => gate.lanes[lane].observationId
    );
  const gateObservedTimes =
    G2_CORE_REQUIRED_LANES.map(
      (lane) => Date.parse(gate.lanes[lane].observedAt)
    );
  const planNowMs = Math.max(...gateObservedTimes) + 500;
  const capturePlan = planG2CaptureWindow(gate, {
    minimumPreRollMs: 1000,
    maxPreRollMs: 10000,
    nowMs: planNowMs,
  });
  assert.ok(capturePlan.requestedPreRollMs >= 1000);
  assert.deepEqual(
    capturePlan.requiredObservationIds,
    requiredGateObservationIds
  );
  assert.equal(
    Date.parse(capturePlan.triggerAt) -
      capturePlan.requestedPreRollMs,
    Math.min(...gateObservedTimes)
  );

  const badRevisionRunDir = path.join(temp, 'bad-revision-run');
  const badRevisionRuntime = new EvidenceRuntime({
    runDir: badRevisionRunDir,
    debugSessionId: 'sess-g2-bad-revision',
    runId: 'run-g2-bad-revision',
    runSnapshotId: 'snapshot-g2-bad-revision',
    processEpoch: 1,
  });
  await badRevisionRuntime.init();
  await populateCore(badRevisionRuntime);

  const badRevisionGate = await waitForG2Evidence({
    runtime: badRevisionRuntime,
    current: {
      debugSessionId: 'sess-g2-bad-revision',
      runId: 'run-g2-bad-revision',
      runSnapshotId: 'snapshot-g2-bad-revision',
      processEpoch: 1,
    },
    entityUuid,
    targetRevision: 2,
    timeoutMs: 50,
    pollMs: 5,
  });
  assert.equal(badRevisionGate.ok, false);
  assert.equal(badRevisionGate.timedOut, true);
  assert.ok(
    badRevisionGate.lanes.ENTITY_STATE.errors.includes(
      'TARGET_REVISION_MISMATCH'
    )
  );

  const badRunDir = path.join(temp, 'bad-authority-run');
  const badRuntime = new EvidenceRuntime({
    runDir: badRunDir,
    debugSessionId: 'sess-g2-bad',
    runId: 'run-g2-bad',
    runSnapshotId: 'snapshot-g2-bad',
    processEpoch: 1,
  });
  await badRuntime.init();
  await populateCore(badRuntime, {
    wrongSideLane: 'AI_TARGET',
  });

  const badGate = await waitForG2Evidence({
    runtime: badRuntime,
    current: {
      debugSessionId: 'sess-g2-bad',
      runId: 'run-g2-bad',
      runSnapshotId: 'snapshot-g2-bad',
      processEpoch: 1,
    },
    entityUuid,
    targetRevision: 1,
    timeoutMs: 50,
    pollMs: 5,
  });
  assert.equal(badGate.ok, false);
  assert.equal(badGate.timedOut, true);
  assert.ok(
    badGate.lanes.AI_TARGET.errors.includes(
      'SOURCE_AUTHORITY_MISMATCH'
    )
  );

  const acceptanceDir = path.join(temp, 'acceptance-run');
  const started = {
    status: 'DEBUG_READY',
    runDir: acceptanceDir,
    debugSessionId: 'sess-acceptance',
    runId: 'run-acceptance',
    runSnapshotId: 'snapshot-acceptance',
    runSnapshotHash: 'sha256:snapshot',
    processEpoch: 7,
  };
  const target = {
    debugSessionId: started.debugSessionId,
    runId: started.runId,
    runSnapshotId: started.runSnapshotId,
    processEpoch: started.processEpoch,
    revision: 1,
    targetUuid: entityUuid,
  };

  const captureFile = path.join(
    acceptanceDir,
    'evidence',
    'captures',
    'capture-acceptance.json'
  );

  const acceptance = await writeG2Acceptance({
    started,
    timeline: {
      complete: true,
    },
    liveStatus: {
      live: true,
    },
    target,
    evidenceGate: {
      ok: true,
      debugSessionId: started.debugSessionId,
      runId: started.runId,
      runSnapshotId: started.runSnapshotId,
      processEpoch: started.processEpoch,
      entityUuid,
      targetRevision: target.revision,
      requireReimu: false,
      globalRequiredLanes: G2_GLOBAL_REQUIRED_LANES,
      requiredLanes: G2_CORE_REQUIRED_LANES,
      globalLanes: gate.globalLanes,
      lanes: gate.lanes,
      health: gate.health,
    },
    capture: {
      file: captureFile,
      manifest: {
        captureId: 'capture-acceptance',
        debugSessionId: started.debugSessionId,
        runId: started.runId,
        runSnapshotId: started.runSnapshotId,
        processEpoch: started.processEpoch,
        requestedPreRollMs: 1000,
        coverage: {
          truncated: false,
          availablePreRollMs: 1000,
        },
        observationIds: requiredGateObservationIds,
        filter: {
          entityUuid,
          lanes: G2_CORE_REQUIRED_LANES,
        },
        canonicalCut: {
          count: requiredGateObservationIds.length,
        },
      },
    },
    stopped: {
      ok: true,
      evidenceShutdown: {
        clean: true,
      },
    },
    finalization: {
      manifest: {
        status: 'EVIDENCE_COMPLETE',
        debugSessionId: started.debugSessionId,
        runId: started.runId,
        runSnapshotId: started.runSnapshotId,
        processEpoch: started.processEpoch,
        finalizedAt: new Date().toISOString(),
        counts: {
          observations: 10,
          dropped: 0,
          errors: 0,
        },
        captures: {
          count: 1,
          partialCount: 0,
        },
        artifacts: [
          {
            path: captureFile,
            size: 123,
            sha256: 'sha256:capture'
          }
        ],
      },
    },
  });

  assert.equal(acceptance.manifest.result, 'PASS');
  assert.equal(acceptance.manifest.entityUuid, entityUuid);
  assert.match(acceptance.integrity.sha256, /^sha256:[0-9a-f]{64}$/);

  const onDisk = JSON.parse(
    await readFile(acceptance.file, 'utf8')
  );
  assert.equal(onDisk.gate, 'G2_OBSERVATION_CORE');
  assert.equal(onDisk.runSnapshotId, started.runSnapshotId);

  const missingAcceptanceDir = path.join(
    temp,
    'acceptance-missing-capture-run'
  );
  const missingStarted = {
    ...started,
    runDir: missingAcceptanceDir,
    debugSessionId: 'sess-acceptance-missing',
    runId: 'run-acceptance-missing',
    runSnapshotId: 'snapshot-acceptance-missing',
  };
  const missingTarget = {
    ...target,
    debugSessionId: missingStarted.debugSessionId,
    runId: missingStarted.runId,
    runSnapshotId: missingStarted.runSnapshotId,
  };
  const missingEvidenceGate = {
    ok: true,
    debugSessionId: missingStarted.debugSessionId,
    runId: missingStarted.runId,
    runSnapshotId: missingStarted.runSnapshotId,
    processEpoch: missingStarted.processEpoch,
    entityUuid,
    targetRevision: missingTarget.revision,
    requireReimu: false,
    globalRequiredLanes: G2_GLOBAL_REQUIRED_LANES,
    requiredLanes: G2_CORE_REQUIRED_LANES,
    globalLanes: gate.globalLanes,
    lanes: gate.lanes,
    health: gate.health,
  };
  const missingCaptureFile = path.join(
    missingAcceptanceDir,
    'evidence',
    'captures',
    'capture-missing.json'
  );
  const missingAcceptance = await writeG2Acceptance({
    started: missingStarted,
    timeline: { complete: true },
    liveStatus: { live: true },
    target: missingTarget,
    evidenceGate: missingEvidenceGate,
    capture: {
      file: missingCaptureFile,
      manifest: {
        captureId: 'capture-missing',
        debugSessionId: missingStarted.debugSessionId,
        runId: missingStarted.runId,
        runSnapshotId: missingStarted.runSnapshotId,
        processEpoch: missingStarted.processEpoch,
        requestedPreRollMs: 1000,
        coverage: {
          truncated: false,
          availablePreRollMs: 1000,
        },
        observationIds: requiredGateObservationIds.slice(1),
        filter: {
          entityUuid,
          lanes: G2_CORE_REQUIRED_LANES,
        },
        canonicalCut: {
          count: requiredGateObservationIds.length,
        },
      },
    },
    stopped: {
      ok: true,
      evidenceShutdown: { clean: true },
    },
    finalization: {
      manifest: {
        status: 'EVIDENCE_COMPLETE',
        debugSessionId: missingStarted.debugSessionId,
        runId: missingStarted.runId,
        runSnapshotId: missingStarted.runSnapshotId,
        processEpoch: missingStarted.processEpoch,
        finalizedAt: new Date().toISOString(),
        counts: {
          observations: 10,
          dropped: 0,
          errors: 0,
        },
        captures: {
          count: 1,
          partialCount: 0,
        },
        artifacts: [
          {
            path: missingCaptureFile,
            size: 123,
            sha256: 'sha256:capture-missing',
          },
        ],
      },
    },
  });
  assert.equal(missingAcceptance.manifest.result, 'FAIL');
  assert.equal(
    missingAcceptance.manifest.captureEvidenceBound,
    false
  );
  assert.ok(
    missingAcceptance.manifest.requiredCaptureObservationIds.length > 1
  );

  await assert.rejects(
    () => writeG2Acceptance({
      started,
      timeline: { complete: true },
      liveStatus: { live: true },
      target,
      evidenceGate: {
        ok: true,
        debugSessionId: started.debugSessionId,
        runId: started.runId,
        runSnapshotId: started.runSnapshotId,
        processEpoch: started.processEpoch,
        entityUuid,
        targetRevision: target.revision,
        globalRequiredLanes: G2_GLOBAL_REQUIRED_LANES,
        requiredLanes: G2_CORE_REQUIRED_LANES,
        globalLanes: gate.globalLanes,
        lanes: gate.lanes
      },
      capture: {
        file: captureFile,
        manifest: {
          debugSessionId: started.debugSessionId,
          runId: started.runId,
          runSnapshotId: started.runSnapshotId,
          processEpoch: started.processEpoch,
          coverage: { truncated: false },
          filter: { entityUuid },
        },
      },
      stopped: {
        ok: true,
        evidenceShutdown: { clean: true },
      },
      finalization: {
        manifest: {
          status: 'EVIDENCE_COMPLETE',
          debugSessionId: started.debugSessionId,
          runId: started.runId,
          runSnapshotId: started.runSnapshotId,
          processEpoch: started.processEpoch,
          artifacts: [
            {
              path: captureFile,
              size: 123,
              sha256: 'sha256:capture'
            }
          ],
        },
      },
    }),
    /EEXIST/
  );

  console.log('g2 acceptance selftest OK');
} finally {
  await rm(temp, { recursive: true, force: true });
}
