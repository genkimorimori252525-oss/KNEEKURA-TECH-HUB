import assert from 'node:assert/strict';
import os from 'node:os';
import path from 'node:path';
import {
  mkdir,
  mkdtemp,
  rm,
  writeFile,
  appendFile,
  readFile,
} from 'node:fs/promises';
import {
  EvidenceStore,
  DeltaGate,
} from './store.mjs';
import { ObservationRingBuffer } from './ring-buffer.mjs';
import { EvidenceRuntime } from './runtime.mjs';
import { evaluateBuiltInWatchpoints } from './watchpoints.mjs';
import { finalizeEvidenceRun } from './finalize.mjs';
import {
  EvidenceBroker,
  buildEvidenceCut,
  summarizeClientServerConsistency,
  summarizeAiConsistency,
} from './broker.mjs';
import {
  validateFinding,
  validateObservation,
} from './schema.mjs';

function obs(overrides = {}) {
  return {
    v: 1,
    kind: 'observation',
    observationId: 'obs:test:1',
    debugSessionId: 'sess-test',
    runId: 'run-test',
    processEpoch: 1,
    arenaEpoch: 1,
    resourceEpoch: 1,
    writerId: 'probe-client',
    writerSeq: 1,
    level: 'L1',
    lane: 'TARGET_TRACKED',
    observedAt: '2026-09-18T12:00:00.000Z',
    gameTime: 100,
    scope: {
      kind: 'ENTITY_UUID',
      entityUuid: '00000000-0000-0000-0000-000000000001'
    },
    source: {
      side: 'CLIENT',
      method: 'selftest'
    },
    epistemicStatus: 'OBSERVED',
    completeness: {
      complete: true
    },
    payload: {
      tracked: true
    },
    ...overrides,
  };
}

const temp = await mkdtemp(path.join(os.tmpdir(), 'kneekura-evidence-'));

try {
  const valid = validateObservation(obs());
  assert.equal(valid.ok, true, JSON.stringify(valid));

  const clocked = validateObservation(obs({
    clock: {
      domain: 'JVM_PROCESS_MONOTONIC',
      processId: 1234,
      processStartedAt: '2026-09-18T11:59:59.000Z',
      monotonicOriginWallClock: '2026-09-18T12:00:00.000Z',
      monotonicElapsedNanos: 123456,
      wallClockSample: '2026-09-18T12:00:00.000Z'
    }
  }));
  assert.equal(clocked.ok, true, JSON.stringify(clocked));

  const badClock = validateObservation(obs({
    clock: {
      domain: 'WALL_CLOCK_TOTAL_ORDER',
      processId: 0,
      monotonicOriginWallClock: 'not-a-time',
      monotonicElapsedNanos: -1,
      wallClockSample: 'not-a-time'
    }
  }));
  assert.equal(badClock.ok, false);
  assert.ok(
    badClock.errors.some((x) => x.includes('clock.domain invalid'))
  );

  const ring = new ObservationRingBuffer({
    maxRecords: 3,
    maxAgeMs: 10_000
  });
  ring.push(obs({
    observationId: 'obs:ring:1',
    writerSeq: 1,
    observedAt: '2026-09-18T12:00:00.000Z'
  }));
  ring.push(obs({
    observationId: 'obs:ring:2',
    writerSeq: 2,
    observedAt: '2026-09-18T12:00:01.000Z'
  }));
  ring.push(obs({
    observationId: 'obs:ring:3',
    writerSeq: 3,
    observedAt: '2026-09-18T12:00:02.000Z'
  }));

  const fullPreRoll = ring.capturePreRoll({
    triggerAt: '2026-09-18T12:00:02.000Z',
    requestedPreRollMs: 2000
  });
  assert.equal(fullPreRoll.truncated, false, JSON.stringify(fullPreRoll));
  assert.equal(fullPreRoll.availablePreRollMs, 2000);
  assert.equal(fullPreRoll.retainedRecords, 3);

  ring.push(obs({
    observationId: 'obs:ring:4',
    writerSeq: 4,
    observedAt: '2026-09-18T12:00:03.000Z'
  }));
  const truncatedPreRoll = ring.capturePreRoll({
    triggerAt: '2026-09-18T12:00:03.000Z',
    requestedPreRollMs: 3000
  });
  assert.equal(truncatedPreRoll.truncated, true);
  assert.equal(truncatedPreRoll.droppedRecords, 1);
  assert.equal(truncatedPreRoll.droppedInsideRequestedWindow, true);
  assert.equal(truncatedPreRoll.oldestSelectedAt, '2026-09-18T12:00:01.000Z');

  const outOfOrderRing = new ObservationRingBuffer({
    maxRecords: 5,
    maxAgeMs: 10_000
  });
  outOfOrderRing.push(obs({
    observationId: 'obs:ring:late-arrival-newer',
    writerSeq: 1,
    observedAt: '2026-09-18T12:00:02.000Z'
  }));
  outOfOrderRing.push(obs({
    observationId: 'obs:ring:late-arrival-older',
    writerSeq: 2,
    observedAt: '2026-09-18T12:00:01.000Z'
  }));
  const outOfOrderCoverage = outOfOrderRing.coverage();
  assert.equal(
    outOfOrderCoverage.oldestRetainedAt,
    '2026-09-18T12:00:01.000Z'
  );
  assert.equal(
    outOfOrderCoverage.newestRetainedAt,
    '2026-09-18T12:00:02.000Z'
  );
  assert.equal(outOfOrderCoverage.retainedRecords, 2);

  const targetLostWatchpoints = evaluateBuiltInWatchpoints({
    observations: [
      obs({
        observationId: 'obs:watch:target-lost',
        lane: 'TARGET_TRACKED',
        writerSeq: 10,
        payload: {
          tracked: false,
          reason: 'target_selected'
        }
      })
    ],
    health: []
  });
  assert.ok(
    targetLostWatchpoints.some((x) => x.watchpointId === 'TARGET_NOT_TRACKED')
  );

  const targetClearWatchpoints = evaluateBuiltInWatchpoints({
    observations: [
      obs({
        observationId: 'obs:watch:target-clear',
        lane: 'TARGET_TRACKED',
        writerSeq: 11,
        payload: {
          tracked: false,
          reason: 'target_cleared'
        }
      })
    ],
    health: []
  });
  assert.equal(
    targetClearWatchpoints.some((x) => x.watchpointId === 'TARGET_NOT_TRACKED'),
    false
  );

  const pausedHeartbeatWatchpoints = evaluateBuiltInWatchpoints({
    observations: [
      obs({
        observationId: 'obs:watch:client-paused',
        lane: 'CLIENT_TICK',
        writerSeq: 12,
        scope: { kind: 'GLOBAL_HEALTH' },
        payload: { heartbeat: true, paused: true }
      }),
      obs({
        observationId: 'obs:watch:server-stale',
        lane: 'SERVER_TICK',
        writerSeq: 13,
        scope: { kind: 'GLOBAL_HEALTH' },
        payload: { heartbeat: true }
      })
    ],
    health: [
      {
        lane: 'SERVER_TICK',
        effectiveStatus: 'STALE',
        dropped: 0,
        errors: 0
      }
    ]
  });
  assert.equal(
    pausedHeartbeatWatchpoints.some((x) => x.watchpointId === 'SERVER_TICK_STALE'),
    false
  );

  const liveClientStaleServer = evaluateBuiltInWatchpoints({
    observations: [
      obs({
        observationId: 'obs:watch:client-live',
        lane: 'CLIENT_TICK',
        writerSeq: 14,
        scope: { kind: 'GLOBAL_HEALTH' },
        payload: { heartbeat: true, paused: false }
      }),
      obs({
        observationId: 'obs:watch:server-stale-2',
        lane: 'SERVER_TICK',
        writerSeq: 15,
        scope: { kind: 'GLOBAL_HEALTH' },
        payload: { heartbeat: true }
      })
    ],
    health: [
      {
        lane: 'SERVER_TICK',
        effectiveStatus: 'STALE',
        dropped: 0,
        errors: 0
      }
    ]
  });
  assert.ok(
    liveClientStaleServer.some((x) => x.watchpointId === 'SERVER_TICK_STALE')
  );

  const badFinding = validateFinding({
    v: 1,
    kind: 'finding',
    findingId: 'finding-1',
    debugSessionId: 'sess-test',
    runId: 'run-test',
    statement: 'this must not pretend to be directly observed',
    epistemicStatus: 'OBSERVED',
    evidenceIds: ['obs:test:1'],
    createdAt: '2026-09-18T12:00:00Z'
  });
  assert.equal(badFinding.ok, false);
  assert.ok(badFinding.errors.some((x) => x.includes('cannot be OBSERVED')));

  const gate = new DeltaGate({ keyframeTicks: 100 });
  assert.equal(gate.shouldWrite(obs()).write, true);

  const same = gate.shouldWrite(obs({
    observationId: 'obs:test:2',
    writerSeq: 2,
    gameTime: 101,
    observedAt: '2026-09-18T12:00:00.050Z'
  }));
  assert.equal(same.write, false);
  assert.equal(same.reason, 'unchanged');

  const changed = gate.shouldWrite(obs({
    observationId: 'obs:test:3',
    writerSeq: 3,
    gameTime: 102,
    observedAt: '2026-09-18T12:00:00.100Z',
    payload: { tracked: false }
  }));
  assert.equal(changed.write, true);
  assert.equal(changed.reason, 'changed');

  const keyframeGate = new DeltaGate({ keyframeTicks: 100 });
  keyframeGate.shouldWrite(obs());
  const keyframe = keyframeGate.shouldWrite(obs({
    observationId: 'obs:test:k',
    writerSeq: 4,
    gameTime: 200,
    observedAt: '2026-09-18T12:00:05.000Z'
  }));
  assert.equal(keyframe.write, true);
  assert.equal(keyframe.reason, 'keyframe');

  const epochGate = new DeltaGate({ keyframeTicks: 100 });
  epochGate.shouldWrite(obs());
  const afterEpoch = epochGate.shouldWrite(obs({
    observationId: 'obs:test:e',
    writerSeq: 5,
    processEpoch: 2,
    gameTime: 101,
    observedAt: '2026-09-18T12:00:00.050Z'
  }));
  assert.equal(afterEpoch.write, true);
  assert.equal(afterEpoch.reason, 'first');

  const store = new EvidenceStore({
    runDir: temp,
    debugSessionId: 'sess-test',
    runId: 'run-test',
    keyframeTicks: 100
  });
  await store.init();

  const entityUuid = '00000000-0000-0000-0000-000000000001';

  const pinnedIdentity = await store.appendObservation({
    debugSessionId: 'sess-evil',
    runId: 'run-evil',
    processEpoch: 1,
    arenaEpoch: 1,
    resourceEpoch: 1,
    writerId: 'probe-pinned',
    writerSeq: store.nextSequence('probe-pinned'),
    level: 'L2',
    lane: 'IDENTITY_TEST',
    observedAt: '2026-09-18T11:59:59.000Z',
    gameTime: 99,
    scope: { kind: 'SUBSYSTEM', subsystem: 'identity' },
    source: { side: 'ORCHESTRATOR', method: 'selftest' },
    epistemicStatus: 'OBSERVED',
    completeness: { complete: true },
    payload: { test: true }
  });
  assert.equal(pinnedIdentity.record.debugSessionId, 'sess-test');
  assert.equal(pinnedIdentity.record.runId, 'run-test');

  const first = await store.appendObservation({
    processEpoch: 1,
    arenaEpoch: 1,
    resourceEpoch: 1,
    writerId: 'probe-client',
    writerSeq: store.nextSequence('probe-client'),
    level: 'L1',
    lane: 'TARGET_TRACKED',
    observedAt: '2026-09-18T12:00:00.000Z',
    gameTime: 100,
    scope: { kind: 'ENTITY_UUID', entityUuid },
    source: { side: 'CLIENT', method: 'tracker' },
    epistemicStatus: 'OBSERVED',
    completeness: { complete: true },
    payload: { tracked: true }
  });
  assert.equal(first.written, true);

  const suppressed = await store.appendObservation({
    processEpoch: 1,
    arenaEpoch: 1,
    resourceEpoch: 1,
    writerId: 'probe-client',
    writerSeq: store.nextSequence('probe-client'),
    level: 'L1',
    lane: 'TARGET_TRACKED',
    observedAt: '2026-09-18T12:00:00.050Z',
    gameTime: 101,
    scope: { kind: 'ENTITY_UUID', entityUuid },
    source: { side: 'CLIENT', method: 'tracker' },
    epistemicStatus: 'OBSERVED',
    completeness: { complete: true },
    payload: { tracked: true }
  });
  assert.equal(suppressed.written, false);

  const nav = await store.appendObservation({
    processEpoch: 1,
    arenaEpoch: 1,
    resourceEpoch: 1,
    writerId: 'probe-client',
    writerSeq: store.nextSequence('probe-client'),
    level: 'L1',
    lane: 'NAVIGATION',
    observedAt: '2026-09-18T12:00:00.100Z',
    gameTime: 102,
    scope: { kind: 'ENTITY_UUID', entityUuid },
    source: { side: 'CLIENT', method: 'navigation-summary' },
    epistemicStatus: 'OBSERVED',
    completeness: { complete: true },
    payload: { active: true, nextNode: [1, 64, 1] }
  });
  assert.equal(nav.written, true);

  await store.appendObservation({
    processEpoch: 1,
    arenaEpoch: 1,
    resourceEpoch: 1,
    writerId: 'probe-client',
    writerSeq: store.nextSequence('probe-client'),
    level: 'L2',
    lane: 'NAVIGATION_ANOMALY',
    observedAt: '2026-09-18T12:00:00.120Z',
    gameTime: 102,
    scope: { kind: 'ENTITY_UUID', entityUuid },
    source: { side: 'CLIENT', method: 'watchpoint:stuck' },
    epistemicStatus: 'OBSERVED',
    completeness: { complete: true },
    payload: { anomaly: true, status: 'DEGRADED', reason: 'speed_zero' }
  });

  const heartbeatTooSoon = await store.maybeHeartbeat({
    writerId: 'probe-client',
    writerSeq: store.nextSequence('probe-client'),
    processEpoch: 1,
    arenaEpoch: 1,
    resourceEpoch: 1,
    observedAt: '2026-09-18T12:00:00.150Z',
    gameTime: 103,
    silenceTicks: 20,
    silenceMs: 1000
  });
  assert.equal(heartbeatTooSoon.written, false);
  assert.equal(heartbeatTooSoon.reason, 'not-silent');

  const heartbeatAfterSilence = await store.maybeHeartbeat({
    writerId: 'probe-client',
    writerSeq: store.nextSequence('probe-client'),
    processEpoch: 1,
    arenaEpoch: 1,
    resourceEpoch: 1,
    observedAt: '2026-09-18T12:00:02.500Z',
    gameTime: 130,
    silenceTicks: 20,
    silenceMs: 1000
  });
  assert.equal(heartbeatAfterSilence.written, true);

  const sequenceStore = new EvidenceStore({
    runDir: path.join(temp, 'sequence-regression'),
    debugSessionId: 'sess-sequence',
    runId: 'run-sequence',
    keyframeTicks: 100
  });
  await sequenceStore.init();
  await sequenceStore.appendObservation({
    processEpoch: 1,
    arenaEpoch: 1,
    resourceEpoch: 1,
    observationId: 'obs:sequence-base:1',
    writerId: 'probe-sequence',
    writerSeq: 2,
    level: 'L1',
    lane: 'ENTITY_STATE',
    observedAt: '2026-09-18T12:00:02.500Z',
    gameTime: 130,
    scope: { kind: 'ENTITY_UUID', entityUuid },
    source: { side: 'CLIENT', method: 'sequence-base' },
    epistemicStatus: 'OBSERVED',
    completeness: { complete: true },
    payload: { x: 0 }
  });

  let sequenceRejected = false;
  try {
    await sequenceStore.appendObservation({
      processEpoch: 1,
      arenaEpoch: 1,
      resourceEpoch: 1,
      observationId: 'obs:sequence-regression:1',
      writerId: 'probe-sequence',
      writerSeq: 1,
      level: 'L2',
      lane: 'NAVIGATION',
      observedAt: '2026-09-18T12:00:02.600Z',
      gameTime: 131,
      scope: { kind: 'ENTITY_UUID', entityUuid },
      source: { side: 'CLIENT', method: 'bad-order' },
      epistemicStatus: 'OBSERVED',
      completeness: { complete: true },
      payload: { active: false }
    });
  } catch (error) {
    sequenceRejected = /sequence must increase monotonically/.test(error.message);
  }
  assert.equal(sequenceRejected, true);
  assert.equal(
    sequenceStore.lanes.snapshot().find(
      (x) => x.lane === 'NAVIGATION'
    ).errors,
    1
  );

  const producerStore = new EvidenceStore({
    runDir: path.join(temp, 'producer-gap'),
    debugSessionId: 'sess-producer',
    runId: 'run-producer',
    keyframeTicks: 100
  });
  await producerStore.init();

  await producerStore.appendObservation({
    processEpoch: 1,
    arenaEpoch: 0,
    resourceEpoch: 0,
    writerId: 'forge-runtime:42',
    writerSeq: 1,
    producerDeltaApplied: true,
    writerQueueDepth: 0,
    writerDroppedTotal: 0,
    level: 'L1',
    lane: 'ENTITY_STATE',
    observedAt: '2026-09-18T12:00:00.000Z',
    gameTime: 100,
    scope: { kind: 'ENTITY_UUID', entityUuid },
    source: { side: 'CLIENT', method: 'producer-gap-test' },
    epistemicStatus: 'OBSERVED',
    completeness: { complete: true },
    payload: { x: 0 }
  });

  await producerStore.appendObservation({
    processEpoch: 1,
    arenaEpoch: 0,
    resourceEpoch: 0,
    writerId: 'forge-runtime:42',
    writerSeq: 3,
    producerDeltaApplied: true,
    writerQueueDepth: 0,
    writerDroppedTotal: 1,
    level: 'L1',
    lane: 'ENTITY_STATE',
    observedAt: '2026-09-18T12:00:00.100Z',
    gameTime: 102,
    scope: { kind: 'ENTITY_UUID', entityUuid },
    source: { side: 'CLIENT', method: 'producer-gap-test' },
    epistemicStatus: 'OBSERVED',
    completeness: { complete: true },
    payload: { x: 1 }
  });

  const producerGapHealth = producerStore.lanes
    .snapshot()
    .find((x) => x.lane === 'OBSERVATION_WRITTEN');
  assert.ok(producerGapHealth);
  assert.equal(producerGapHealth.status, 'DEGRADED');
  assert.equal(producerGapHealth.dropped, 1);

  const producerRows = await producerStore.readObservations();
  assert.equal(producerRows.length, 2);
  assert.equal(producerRows[1].writerSeq, 3);

  const producerBroker = new EvidenceBroker(producerStore);
  const producerStatus = await producerBroker.status({
    now: '2026-09-18T12:00:00.200Z',
    rateWindowMs: 1000
  });
  assert.equal(producerStatus.overallHealth.status, 'DEGRADED');
  assert.equal(producerStatus.overallHealth.totalDropped, 1);
  assert.equal(
    producerStatus.writers['forge-runtime:42'].droppedTotal,
    1
  );
  assert.equal(
    producerStatus.health.find((x) => x.lane === 'ENTITY_STATE').rate.count,
    2
  );
  assert.equal(
    producerStatus.health.find((x) => x.lane === 'ENTITY_STATE').rate.rateHz,
    2
  );

  const broker = new EvidenceBroker(store);

  const current = await broker.entityCurrent(entityUuid, {
    coherenceMode: 'BOUNDED_SKEW',
    maxSkewMs: 250,
    lanes: ['TARGET_TRACKED', 'NAVIGATION']
  });
  assert.equal(current.ok, true, JSON.stringify(current));
  assert.equal(current.current.TARGET_TRACKED.payload.tracked, true);
  assert.equal(current.current.NAVIGATION.payload.active, true);
  assert.equal(current.skewMs, 100);

  const currentLatestDefault = await broker.entityCurrent(entityUuid, {
    lanes: ['TARGET_TRACKED', 'NAVIGATION'],
    now: '2026-09-18T12:00:06.500Z'
  });
  assert.equal(currentLatestDefault.ok, true);
  assert.equal(currentLatestDefault.coherenceMode, 'LATEST_PER_LANE');
  assert.equal(
    currentLatestDefault.current.TARGET_TRACKED.freshness.staleAfterMs,
    7000
  );
  assert.equal(
    currentLatestDefault.current.TARGET_TRACKED.freshness.fresh,
    true
  );

  const tooStrict = await broker.entityCurrent(entityUuid, {
    coherenceMode: 'BOUNDED_SKEW',
    maxSkewMs: 10,
    lanes: ['TARGET_TRACKED', 'NAVIGATION']
  });
  assert.equal(tooStrict.ok, false);
  assert.equal(tooStrict.reason, 'EVIDENCE_SKEW_EXCEEDED');

  const latestPerLane = buildEvidenceCut([
    obs({
      observationId: 'obs:latest-view:1',
      writerSeq: 50,
      lane: 'TARGET_TRACKED',
      observedAt: '2026-09-18T12:10:00.000Z'
    }),
    obs({
      observationId: 'obs:latest-view:2',
      writerSeq: 51,
      lane: 'NAVIGATION',
      observedAt: '2026-09-18T12:10:05.000Z'
    })
  ]);
  assert.equal(latestPerLane.ok, true, JSON.stringify(latestPerLane));
  assert.equal(latestPerLane.coherenceMode, 'LATEST_PER_LANE');
  assert.equal(latestPerLane.skewMs, 5000);
  assert.equal(
    latestPerLane.ordering.perWriterSequenceAuthoritative,
    true
  );
  assert.equal(
    latestPerLane.ordering.crossWriterCausality,
    'NOT_PROVEN_BY_TIMESTAMP'
  );
  assert.equal(
    latestPerLane.ordering.wallClockRole,
    'CORRELATION_AND_SKEW_ONLY'
  );

  const anomalies = await broker.anomalies({
    now: '2026-09-18T12:00:02.600Z'
  });
  assert.equal(anomalies.length, 1);
  assert.equal(anomalies[0].lane, 'NAVIGATION_ANOMALY');

  const finding = await broker.createFinding({
    findingId: 'finding:test:1',
    statement: 'navigation may be stalled after target tracking remained healthy',
    epistemicStatus: 'INFERRED',
    evidenceIds: [first.observationId, nav.observationId],
    limitations: ['No path-recompute event has been inspected yet']
  });
  assert.equal(finding.kind, 'finding');
  assert.equal(finding.epistemicStatus, 'INFERRED');

  let missingEvidenceRejected = false;
  try {
    await broker.createFinding({
      findingId: 'finding:test:bad',
      statement: 'bad finding',
      epistemicStatus: 'INFERRED',
      evidenceIds: ['obs:missing']
    });
  } catch (error) {
    missingEvidenceRejected = /missing observation IDs/.test(error.message);
  }
  assert.equal(missingEvidenceRejected, true);

  const consistencyAligned = summarizeClientServerConsistency({
    TARGET_TRACKED: {
      observedAt: '2026-09-18T12:20:00.000Z',
      payload: { tracked: true }
    },
    SERVER_TARGET_TRACKED: {
      observedAt: '2026-09-18T12:20:00.050Z',
      payload: { tracked: true }
    },
    ENTITY_STATE: {
      observedAt: '2026-09-18T12:20:00.000Z',
      payload: {
        x: 1.0, y: 64.0, z: 1.0,
        vx: 0.1, vy: 0.0, vz: 0.0,
        onGround: true, alive: true, removed: false, noGravity: false
      }
    },
    SERVER_ENTITY_STATE: {
      observedAt: '2026-09-18T12:20:00.100Z',
      payload: {
        x: 1.1, y: 64.0, z: 1.0,
        vx: 0.12, vy: 0.0, vz: 0.0,
        onGround: true, alive: true, removed: false, noGravity: false
      }
    }
  });
  assert.equal(consistencyAligned.tracking.agrees, true);
  assert.equal(consistencyAligned.state.comparable, true);
  assert.ok(consistencyAligned.state.positionDistance > 0);
  assert.equal(consistencyAligned.warnings.length, 0);

  const consistencySkewed = summarizeClientServerConsistency({
    TARGET_TRACKED: {
      observedAt: '2026-09-18T12:20:00.000Z',
      payload: { tracked: true }
    },
    SERVER_TARGET_TRACKED: {
      observedAt: '2026-09-18T12:20:00.050Z',
      payload: { tracked: false }
    },
    ENTITY_STATE: {
      observedAt: '2026-09-18T12:20:00.000Z',
      payload: { x: 0, y: 64, z: 0, vx: 0, vy: 0, vz: 0 }
    },
    SERVER_ENTITY_STATE: {
      observedAt: '2026-09-18T12:20:02.000Z',
      payload: { x: 10, y: 64, z: 0, vx: 4, vy: 0, vz: 0 }
    }
  });
  assert.equal(consistencySkewed.tracking.agrees, false);
  assert.equal(consistencySkewed.state.comparable, false);
  assert.equal(
    consistencySkewed.state.reason,
    'OBSERVATION_SKEW_EXCEEDED'
  );
  assert.ok(
    consistencySkewed.warnings.includes(
      'CLIENT_SERVER_TRACKING_DISAGREEMENT'
    )
  );
  assert.equal(
    consistencySkewed.warnings.includes(
      'CLIENT_SERVER_POSITION_DIVERGENCE'
    ),
    false
  );

  const aiAligned = summarizeAiConsistency({
    AI_TARGET: {
      observedAt: '2026-09-18T12:21:00.000Z',
      payload: {
        present: true,
        targetUuid: '00000000-0000-0000-0000-000000000099'
      }
    },
    BRAIN_MEMORY: {
      observedAt: '2026-09-18T12:21:00.100Z',
      payload: {
        attackTargetPresent: true,
        attackTargetUuid: '00000000-0000-0000-0000-000000000099',
        walkTargetPresent: true,
        pathMemoryPresent: true
      }
    },
    NAVIGATION: {
      observedAt: '2026-09-18T12:21:00.150Z',
      payload: {
        pathPresent: true,
        navigationDone: false
      }
    }
  });
  assert.equal(aiAligned.attackTarget.comparable, true);
  assert.equal(aiAligned.attackTarget.uuidAgrees, true);
  assert.equal(aiAligned.movement.comparable, true);
  assert.equal(aiAligned.warnings.length, 0);

  const aiMismatch = summarizeAiConsistency({
    AI_TARGET: {
      observedAt: '2026-09-18T12:22:00.000Z',
      payload: {
        present: true,
        targetUuid: '00000000-0000-0000-0000-000000000010'
      }
    },
    BRAIN_MEMORY: {
      observedAt: '2026-09-18T12:22:00.100Z',
      payload: {
        attackTargetPresent: true,
        attackTargetUuid: '00000000-0000-0000-0000-000000000011',
        walkTargetPresent: true,
        pathMemoryPresent: true
      }
    },
    NAVIGATION: {
      observedAt: '2026-09-18T12:22:00.120Z',
      payload: {
        pathPresent: false,
        navigationDone: true
      }
    }
  });
  assert.ok(
    aiMismatch.warnings.includes(
      'MOB_BRAIN_ATTACK_TARGET_UUID_MISMATCH'
    )
  );
  assert.ok(
    aiMismatch.warnings.includes(
      'WALK_TARGET_WITHOUT_ACTIVE_NAVIGATION_PATH'
    )
  );
  assert.ok(
    aiMismatch.warnings.includes(
      'BRAIN_PATH_WITHOUT_NAVIGATION_PATH'
    )
  );

  const aiSkewed = summarizeAiConsistency({
    AI_TARGET: {
      observedAt: '2026-09-18T12:23:00.000Z',
      payload: {
        present: true,
        targetUuid: '00000000-0000-0000-0000-000000000010'
      }
    },
    BRAIN_MEMORY: {
      observedAt: '2026-09-18T12:23:02.000Z',
      payload: {
        attackTargetPresent: true,
        attackTargetUuid: '00000000-0000-0000-0000-000000000011',
        walkTargetPresent: true,
        pathMemoryPresent: true
      }
    },
    NAVIGATION: {
      observedAt: '2026-09-18T12:23:04.000Z',
      payload: {
        pathPresent: false,
        navigationDone: true
      }
    }
  });
  assert.equal(aiSkewed.attackTarget.comparable, false);
  assert.equal(aiSkewed.movement.comparable, false);
  assert.equal(aiSkewed.warnings.length, 0);

  const crossRun = buildEvidenceCut([
    obs(),
    obs({
      observationId: 'obs:other:1',
      runId: 'run-other',
      writerSeq: 2,
      lane: 'NAVIGATION',
      observedAt: '2026-09-18T12:00:00.010Z'
    })
  ]);
  assert.equal(crossRun.ok, false);
  assert.equal(crossRun.reason, 'EVIDENCE_CONTEXT_CHANGED');

  store.lanes.dropped('NAVIGATION', 2);
  const gap = await broker.explainGap('NAVIGATION');
  assert.equal(gap.status, 'DEGRADED');
  assert.equal(gap.health.dropped, 2);

  const healthRows = await store.flushLaneHealth();
  assert.ok(healthRows.some((x) => x.lane === 'TARGET_TRACKED'));
  assert.ok(healthRows.some((x) => x.lane === 'NAVIGATION'));

  const status = await broker.status({
    now: '2026-09-18T12:00:02.600Z',
    staleAfterMs: 5000
  });
  assert.equal(status.observationCount, 5);
  assert.ok(status.lanes.TARGET_TRACKED);
  assert.ok(status.lanes.NAVIGATION);
  assert.ok(status.health.every((x) => x.effectiveStatus !== 'STALE'));
  assert.ok(
    status.health.some((x) =>
      x.lane === 'TARGET_TRACKED' &&
      x.rate.windowMs === 5000 &&
      x.rate.count >= 1
    )
  );
  assert.equal(status.overallHealth.maxWriterQueueDepth, 0);
  assert.equal(status.compact, true);
  assert.ok(status.ringCoverage);
  assert.equal(status.ringCoverage.maxRecords, 2000);
  assert.equal(status.ringCoverage.maxAgeMs, 10000);
  assert.equal(
    status.ringCoverage.retainedRecords,
    status.observationCount
  );
  assert.equal(
    Object.prototype.hasOwnProperty.call(status.lanes.TARGET_TRACKED, 'payload'),
    false
  );

  const stateCadenceStatus = await broker.status({
    now: '2026-09-18T12:00:06.500Z'
  });
  const targetCadenceHealth = stateCadenceStatus.health.find(
    (x) => x.lane === 'TARGET_TRACKED'
  );
  assert.ok(targetCadenceHealth);
  assert.equal(targetCadenceHealth.staleAfterMs, 7000);
  assert.notEqual(targetCadenceHealth.effectiveStatus, 'STALE');

  const stateCadenceStale = await broker.status({
    now: '2026-09-18T12:00:08.500Z'
  });
  assert.equal(
    stateCadenceStale.health.find(
      (x) => x.lane === 'TARGET_TRACKED'
    ).effectiveStatus,
    'STALE'
  );

  const staleStatus = await broker.status({
    now: '2026-09-18T12:00:20.000Z',
    staleAfterMs: 3000
  });
  assert.ok(staleStatus.health.some((x) => x.effectiveStatus === 'STALE'));

  const staleGap = await broker.explainGap('TARGET_TRACKED', {
    now: '2026-09-18T12:00:20.000Z',
    staleAfterMs: 3000
  });
  assert.equal(staleGap.status, 'STALE');

  // On-demand runtime uses persisted byte cursors. A fresh Node process
  // resumes at the last complete JSONL boundary without rereading old rows.
  const runtimeRunDir = path.join(temp, 'runtime-case');
  const rawDir = path.join(runtimeRunDir, 'evidence', 'raw');
  await mkdir(rawDir, { recursive: true });

  const raw1 = obs({
    observationId: 'obs:runtime:1',
    debugSessionId: 'sess-runtime',
    runId: 'run-runtime',
    runSnapshotId: 'snapshot-expected',
    writerId: 'forge-client:123',
    writerSeq: 1,
    observedAt: '2026-09-18T13:00:00.000Z',
    gameTime: 200,
    lane: 'CLIENT_TICK',
    level: 'L0',
    scope: { kind: 'GLOBAL_HEALTH' },
    source: { side: 'CLIENT', method: 'ClientTickEvent.END' },
    payload: { heartbeat: true }
  });
  const raw2 = obs({
    observationId: 'obs:runtime:2',
    debugSessionId: 'sess-runtime',
    runId: 'run-runtime',
    runSnapshotId: 'snapshot-expected',
    writerId: 'forge-client:123',
    writerSeq: 2,
    observedAt: '2026-09-18T13:00:01.000Z',
    gameTime: 220,
    lane: 'CLIENT_TICK',
    level: 'L0',
    scope: { kind: 'GLOBAL_HEALTH' },
    source: { side: 'CLIENT', method: 'ClientTickEvent.END' },
    payload: { heartbeat: true }
  });

  const rawFile = path.join(rawDir, 'forge-client-123.jsonl');
  await writeFile(
    rawFile,
    JSON.stringify(raw1) + '\n' +
    JSON.stringify(raw2) + '\n' +
    '{"v":1,"kind":"observation"',
    'utf8'
  );

  const runtime1 = new EvidenceRuntime({
    runDir: runtimeRunDir,
    debugSessionId: 'sess-runtime',
    runId: 'run-runtime',
    runSnapshotId: 'snapshot-expected',
    processEpoch: 1
  });
  await runtime1.init();
  const ingest1 = await runtime1.ingestAvailable();
  assert.equal(ingest1.parsed, 2);
  assert.equal(ingest1.written, 2);
  assert.equal(ingest1.trailingPartialFiles, 1);

  const runtime2 = new EvidenceRuntime({
    runDir: runtimeRunDir,
    debugSessionId: 'sess-runtime',
    runId: 'run-runtime',
    runSnapshotId: 'snapshot-expected',
    processEpoch: 1
  });
  const restored2 = await runtime2.init();
  assert.equal(restored2.restored.existingObservations, 2);
  const ingest2 = await runtime2.ingestAvailable();
  assert.equal(ingest2.parsed, 0);
  assert.equal(ingest2.written, 0);
  assert.equal(ingest2.suppressed, 0);
  assert.equal(ingest2.trailingPartialFiles, 1);
  assert.ok(ingest2.bytesRead > 0);
  assert.equal(ingest2.bytesConsumed, 0);

  const raw3 = obs({
    observationId: 'obs:runtime:3',
    debugSessionId: 'sess-runtime',
    runId: 'run-runtime',
    runSnapshotId: 'snapshot-expected',
    writerId: 'forge-client:123',
    writerSeq: 3,
    observedAt: '2026-09-18T13:00:02.000Z',
    gameTime: 240,
    lane: 'CLIENT_TICK',
    level: 'L0',
    scope: { kind: 'GLOBAL_HEALTH' },
    source: { side: 'CLIENT', method: 'ClientTickEvent.END' },
    payload: { heartbeat: true }
  });

  // Replace the previously partial last line with a complete third row.
  await writeFile(
    rawFile,
    JSON.stringify(raw1) + '\n' +
    JSON.stringify(raw2) + '\n' +
    JSON.stringify(raw3) + '\n',
    'utf8'
  );

  const runtime3 = new EvidenceRuntime({
    runDir: runtimeRunDir,
    debugSessionId: 'sess-runtime',
    runId: 'run-runtime',
    runSnapshotId: 'snapshot-expected',
    processEpoch: 1
  });
  await runtime3.init();
  const ingest3 = await runtime3.ingestAvailable();
  assert.equal(ingest3.parsed, 1);
  assert.equal(ingest3.written, 1);
  assert.equal(ingest3.suppressed, 0);
  assert.equal(ingest3.trailingPartialFiles, 0);
  assert.ok(ingest3.bytesConsumed > 0);

  // Cursor safety: append-only raw evidence must never shrink behind the
  // persisted offset. Truncation is treated as evidence corruption.
  const runtimeTruncate = new EvidenceRuntime({
    runDir: runtimeRunDir,
    debugSessionId: 'sess-runtime',
    runId: 'run-runtime',
    runSnapshotId: 'snapshot-expected',
    processEpoch: 1
  });
  await runtimeTruncate.init();
  await writeFile(rawFile, JSON.stringify(raw1) + '\n', 'utf8');
  let truncationRejected = false;
  try {
    await runtimeTruncate.ingestAvailable();
  } catch (error) {
    truncationRejected = /RAW_FILE_TRUNCATED/.test(error.message);
  }
  assert.equal(truncationRejected, true);

  // Restore the append-only file before testing a separate bad-identity file.
  await writeFile(
    rawFile,
    JSON.stringify(raw1) + '\n' +
    JSON.stringify(raw2) + '\n' +
    JSON.stringify(raw3) + '\n',
    'utf8'
  );

  let snapshotMismatchRejected = false;
  const snapshotBadFile = path.join(rawDir, 'forge-client-snapshot-bad.jsonl');
  const snapshotBad = obs({
    observationId: 'obs:runtime:snapshot-bad',
    debugSessionId: 'sess-runtime',
    runId: 'run-runtime',
    runSnapshotId: 'snapshot-wrong',
    writerId: 'forge-client:998',
    writerSeq: 1,
    observedAt: '2026-09-18T13:00:02.900Z',
    lane: 'CLIENT_TICK',
    level: 'L0',
    scope: { kind: 'GLOBAL_HEALTH' },
    source: { side: 'CLIENT', method: 'ClientTickEvent.END' },
    payload: { heartbeat: true }
  });
  await writeFile(
    snapshotBadFile,
    JSON.stringify(snapshotBad) + '\n',
    'utf8'
  );
  const snapshotRuntime = new EvidenceRuntime({
    runDir: runtimeRunDir,
    debugSessionId: 'sess-runtime',
    runId: 'run-runtime',
    runSnapshotId: 'snapshot-expected',
    processEpoch: 1
  });
  await snapshotRuntime.init();
  try {
    await snapshotRuntime.ingestAvailable();
  } catch (error) {
    snapshotMismatchRejected = /runSnapshotId mismatch/.test(error.message);
  }
  assert.equal(snapshotMismatchRejected, true);
  await rm(snapshotBadFile, { force: true });

  let badIdentityRejected = false;
  const badIdentity = obs({
    observationId: 'obs:runtime:bad',
    debugSessionId: 'sess-other',
    runId: 'run-runtime',
    runSnapshotId: 'snapshot-expected',
    writerId: 'forge-client:999',
    writerSeq: 1,
    observedAt: '2026-09-18T13:00:03.000Z',
    lane: 'CLIENT_TICK',
    level: 'L0',
    scope: { kind: 'GLOBAL_HEALTH' },
    source: { side: 'CLIENT', method: 'ClientTickEvent.END' },
    payload: { heartbeat: true }
  });
  await writeFile(
    path.join(rawDir, 'forge-client-bad.jsonl'),
    JSON.stringify(badIdentity) + '\n',
    'utf8'
  );
  const runtime4 = new EvidenceRuntime({
    runDir: runtimeRunDir,
    debugSessionId: 'sess-runtime',
    runId: 'run-runtime',
    runSnapshotId: 'snapshot-expected',
    processEpoch: 1
  });
  await runtime4.init();
  try {
    await runtime4.ingestAvailable();
  } catch (error) {
    badIdentityRejected = /debugSessionId mismatch/.test(error.message);
  }
  assert.equal(badIdentityRejected, true);

  const finalizeDir = path.join(temp, 'finalize-case');
  const finalizeStore = new EvidenceStore({
    runDir: finalizeDir,
    debugSessionId: 'sess-finalize',
    runId: 'run-finalize',
    runSnapshotId: 'snapshot-finalize',
    keyframeTicks: 100
  });
  await finalizeStore.init();
  await finalizeStore.appendObservation({
    processEpoch: 1,
    arenaEpoch: 0,
    resourceEpoch: 0,
    writerId: 'probe-finalize',
    writerSeq: 1,
    level: 'L0',
    lane: 'CLIENT_TICK',
    observedAt: '2026-09-18T14:00:00.000Z',
    gameTime: 300,
    scope: { kind: 'GLOBAL_HEALTH' },
    source: { side: 'CLIENT', method: 'selftest' },
    epistemicStatus: 'OBSERVED',
    completeness: { complete: true },
    payload: { heartbeat: true }
  });

  const finalized = await finalizeEvidenceRun({
    debugSessionId: 'sess-finalize',
    runId: 'run-finalize',
    runSnapshotId: 'snapshot-finalize',
    runSnapshotHash: 'sha256:test',
    processEpoch: 1,
    runDir: finalizeDir,
    status: 'STOPPED',
    live: false,
    stoppedPids: [123]
  }, {
    cleanShutdown: false,
    shutdownMode: 'FORCED_PROCESS_STOP'
  });
  assert.equal(finalized.manifest.status, 'EVIDENCE_PARTIAL');
  assert.equal(finalized.manifest.runSnapshotId, 'snapshot-finalize');
  assert.equal(finalized.manifest.shutdown.clean, false);
  assert.ok(
    finalized.manifest.limitations.some((x) =>
      x.includes('flush/close was not acknowledged')
    )
  );

  const finalizedAgain = await finalizeEvidenceRun({
    debugSessionId: 'sess-finalize',
    runId: 'run-finalize',
    runSnapshotId: 'snapshot-finalize',
    runSnapshotHash: 'sha256:test',
    processEpoch: 1,
    runDir: finalizeDir,
    status: 'STOPPED',
    live: false,
    stoppedPids: [123]
  }, {
    cleanShutdown: false,
    shutdownMode: 'FORCED_PROCESS_STOP'
  });
  assert.equal(finalizedAgain.alreadyFinalized, true);
  assert.equal(
    finalizedAgain.manifest.finalizedAt,
    finalized.manifest.finalizedAt
  );

  const cleanFinalizeDir = path.join(temp, 'finalize-clean-case');
  const cleanFinalizeStore = new EvidenceStore({
    runDir: cleanFinalizeDir,
    debugSessionId: 'sess-finalize-clean',
    runId: 'run-finalize-clean',
    runSnapshotId: 'snapshot-finalize-clean',
    keyframeTicks: 100
  });
  await cleanFinalizeStore.init();
  await cleanFinalizeStore.appendObservation({
    processEpoch: 1,
    arenaEpoch: 0,
    resourceEpoch: 0,
    writerId: 'probe-finalize-clean',
    writerSeq: 1,
    level: 'L0',
    lane: 'CLIENT_TICK',
    observedAt: '2026-09-18T14:10:00.000Z',
    gameTime: 400,
    scope: { kind: 'GLOBAL_HEALTH' },
    source: { side: 'CLIENT', method: 'selftest' },
    epistemicStatus: 'OBSERVED',
    completeness: { complete: true },
    payload: { heartbeat: true }
  });

  const cleanFinalized = await finalizeEvidenceRun({
    debugSessionId: 'sess-finalize-clean',
    runId: 'run-finalize-clean',
    runSnapshotId: 'snapshot-finalize-clean',
    runSnapshotHash: 'sha256:test-clean',
    processEpoch: 1,
    runDir: cleanFinalizeDir,
    status: 'STOPPED',
    live: false,
    stoppedPids: [124],
    evidenceShutdown: {
      clean: true,
      status: 'CLEAN_EVIDENCE_SHUTDOWN',
      ack: {
        writerDroppedTotal: 0,
        remainingQueue: 0
      }
    }
  }, {
    cleanShutdown: true,
    shutdownMode: 'PROBE_FLUSH_ACK_THEN_PROCESS_STOP'
  });
  assert.equal(cleanFinalized.manifest.status, 'EVIDENCE_COMPLETE');

  const droppedFinalizeDir = path.join(temp, 'finalize-dropped-case');
  const droppedFinalizeStore = new EvidenceStore({
    runDir: droppedFinalizeDir,
    debugSessionId: 'sess-finalize-dropped',
    runId: 'run-finalize-dropped',
    runSnapshotId: 'snapshot-finalize-dropped',
    keyframeTicks: 100
  });
  await droppedFinalizeStore.init();
  await droppedFinalizeStore.appendObservation({
    processEpoch: 1,
    arenaEpoch: 0,
    resourceEpoch: 0,
    writerId: 'probe-finalize-dropped',
    writerSeq: 1,
    level: 'L0',
    lane: 'CLIENT_TICK',
    observedAt: '2026-09-18T14:20:00.000Z',
    gameTime: 500,
    scope: { kind: 'GLOBAL_HEALTH' },
    source: { side: 'CLIENT', method: 'selftest' },
    epistemicStatus: 'OBSERVED',
    completeness: { complete: true },
    payload: { heartbeat: true }
  });

  const droppedFinalized = await finalizeEvidenceRun({
    debugSessionId: 'sess-finalize-dropped',
    runId: 'run-finalize-dropped',
    runSnapshotId: 'snapshot-finalize-dropped',
    runSnapshotHash: 'sha256:test-dropped',
    processEpoch: 1,
    runDir: droppedFinalizeDir,
    status: 'STOPPED',
    live: false,
    stoppedPids: [125],
    evidenceShutdown: {
      clean: true,
      status: 'CLEAN_EVIDENCE_SHUTDOWN',
      ack: {
        writerDroppedTotal: 1,
        remainingQueue: 0
      }
    }
  }, {
    cleanShutdown: true,
    shutdownMode: 'PROBE_FLUSH_ACK_THEN_PROCESS_STOP'
  });
  assert.equal(droppedFinalized.manifest.status, 'EVIDENCE_PARTIAL');
  assert.equal(droppedFinalized.manifest.counts.shutdownAckDropped, 1);

  const captureDir = path.join(temp, 'capture-runtime-case');
  const captureRuntime = new EvidenceRuntime({
    runDir: captureDir,
    debugSessionId: 'sess-capture',
    runId: 'run-capture',
    runSnapshotId: 'snapshot-capture',
    processEpoch: 1,
    ringMaxRecords: 100,
    ringMaxAgeMs: 10000
  });
  await captureRuntime.init();

  for (const [seq, at] of [
    [1, '2026-09-18T12:30:00.000Z'],
    [2, '2026-09-18T12:30:01.000Z'],
    [3, '2026-09-18T12:30:02.000Z']
  ]) {
    await captureRuntime.store.appendObservation({
      observationId: 'obs:capture:' + seq,
      processEpoch: 1,
      arenaEpoch: 0,
      resourceEpoch: 0,
      writerId: 'capture-writer',
      writerSeq: seq,
      level: 'L2',
      lane: 'BEHAVIOR_TRANSITION',
      observedAt: at,
      gameTime: 600 + seq,
      scope: { kind: 'ENTITY_UUID', entityUuid },
      source: { side: 'SERVER', method: 'capture-selftest' },
      epistemicStatus: 'OBSERVED',
      completeness: { complete: true },
      payload: { seq }
    });
  }

  let invalidCaptureIdRejected = false;
  try {
    await captureRuntime.capturePreRoll({
      captureId: 'capture:invalid',
      triggerAt: '2026-09-18T12:30:02.000Z',
      requestedPreRollMs: 2000,
      entityUuid
    });
  } catch (error) {
    invalidCaptureIdRejected = /invalid captureId/.test(error.message);
  }
  assert.equal(invalidCaptureIdRejected, true);

  const fullCapture = await captureRuntime.capturePreRoll({
    captureId: 'capture-full',
    triggerAt: '2026-09-18T12:30:02.000Z',
    requestedPreRollMs: 2000,
    entityUuid
  });
  assert.equal(fullCapture.manifest.coverage.truncated, false);
  assert.equal(fullCapture.manifest.coverage.availablePreRollMs, 2000);
  assert.deepEqual(
    fullCapture.manifest.observationIds,
    ['obs:capture:1', 'obs:capture:2', 'obs:capture:3']
  );
  const fullCaptureOnDisk = JSON.parse(
    await readFile(fullCapture.file, 'utf8')
  );
  assert.equal(fullCaptureOnDisk.runSnapshotId, 'snapshot-capture');
  assert.equal(
    fullCaptureOnDisk.semantics.canonicalEvidenceReferencedById,
    true
  );
  assert.equal(
    fullCaptureOnDisk.semantics.bufferWindowCompleteness,
    'FULL_BUFFER_WINDOW'
  );
  assert.equal(
    fullCaptureOnDisk.semantics.selectedEvidencePresence,
    'PRESENT'
  );
  assert.equal(
    fullCaptureOnDisk.semantics.selectedEvidenceContinuityClaimed,
    false
  );
  assert.equal(
    fullCaptureOnDisk.canonicalCut.count,
    3
  );
  assert.equal(
    fullCaptureOnDisk.canonicalCut.lastObservationId,
    'obs:capture:3'
  );
  assert.match(
    fullCaptureOnDisk.canonicalCut.canonicalRecordsSha256,
    /^sha256:[0-9a-f]{64}$/
  );
  assert.deepEqual(
    fullCaptureOnDisk.ringConfig,
    { maxRecords: 100, maxAgeMs: 10000 }
  );

  const restoredRuntime = new EvidenceRuntime({
    runDir: captureDir,
    debugSessionId: 'sess-capture',
    runId: 'run-capture',
    runSnapshotId: 'snapshot-capture',
    processEpoch: 1,
    ringMaxRecords: 100,
    ringMaxAgeMs: 10000
  });
  const restoredInit = await restoredRuntime.init();
  assert.equal(restoredInit.restored.existingObservations, 3);

  const restoredCapture = await restoredRuntime.capturePreRoll({
    captureId: 'capture-restored-runtime',
    triggerAt: '2026-09-18T12:30:02.000Z',
    requestedPreRollMs: 2000,
    entityUuid
  });
  assert.equal(restoredCapture.manifest.coverage.truncated, false);
  assert.deepEqual(
    restoredCapture.manifest.observationIds,
    ['obs:capture:1', 'obs:capture:2', 'obs:capture:3']
  );

  const partialCapture = await captureRuntime.capturePreRoll({
    captureId: 'capture-partial',
    triggerAt: '2026-09-18T12:30:02.000Z',
    requestedPreRollMs: 5000,
    entityUuid
  });
  assert.equal(partialCapture.manifest.coverage.truncated, true);
  assert.equal(
    partialCapture.manifest.coverage.bufferStartedTooLate,
    true
  );

  const capturedFinalization = await finalizeEvidenceRun({
    debugSessionId: 'sess-capture',
    runId: 'run-capture',
    runSnapshotId: 'snapshot-capture',
    runSnapshotHash: 'sha256:capture',
    processEpoch: 1,
    runDir: captureDir,
    status: 'STOPPED',
    live: false,
    stoppedPids: [126],
    evidenceShutdown: {
      clean: true,
      status: 'CLEAN_EVIDENCE_SHUTDOWN',
      ack: {
        writerDroppedTotal: 0,
        remainingQueue: 0
      }
    }
  }, {
    cleanShutdown: true,
    shutdownMode: 'PROBE_FLUSH_ACK_THEN_PROCESS_STOP'
  });
  assert.equal(
    capturedFinalization.manifest.status,
    'EVIDENCE_COMPLETE'
  );
  assert.equal(
    capturedFinalization.manifest.counts.captureManifests,
    3
  );
  assert.equal(
    capturedFinalization.manifest.counts.partialCaptures,
    1
  );
  assert.ok(
    capturedFinalization.manifest.artifacts.some(
      (artifact) => artifact.path.endsWith(
        path.join('evidence', 'captures', 'capture-full.json')
      )
    )
  );

  let finalizedObservationWriteRejected = false;
  try {
    await captureRuntime.store.appendObservation({
      observationId: 'obs:capture:after-finalization',
      processEpoch: 1,
      arenaEpoch: 0,
      resourceEpoch: 0,
      writerId: 'capture-writer',
      writerSeq: 4,
      level: 'L0',
      lane: 'CLIENT_TICK',
      observedAt: '2026-09-18T12:30:03.000Z',
      gameTime: 604,
      scope: { kind: 'GLOBAL_HEALTH' },
      source: { side: 'ORCHESTRATOR', method: 'after-finalization' },
      epistemicStatus: 'OBSERVED',
      completeness: { complete: true },
      payload: { heartbeat: true }
    });
  } catch (error) {
    finalizedObservationWriteRejected =
      /EVIDENCE_FINALIZED_READ_ONLY/.test(error.message);
  }
  assert.equal(finalizedObservationWriteRejected, true);

  let finalizedCaptureRejected = false;
  try {
    await captureRuntime.capturePreRoll({
      captureId: 'capture-after-finalization',
      triggerAt: '2026-09-18T12:30:02.000Z',
      requestedPreRollMs: 1000,
      entityUuid
    });
  } catch (error) {
    finalizedCaptureRejected =
      /EVIDENCE_FINALIZED_READ_ONLY/.test(error.message);
  }
  assert.equal(finalizedCaptureRejected, true);

  const finalizedReadOnlyRuntime = new EvidenceRuntime({
    runDir: captureDir,
    debugSessionId: 'sess-capture',
    runId: 'run-capture',
    runSnapshotId: 'snapshot-capture',
    processEpoch: 1,
    ringMaxRecords: 100,
    ringMaxAgeMs: 10000
  });
  const finalizedReadOnlyInit = await finalizedReadOnlyRuntime.init();
  assert.equal(finalizedReadOnlyInit.finalized, true);
  const finalizedReadOnlyIngest =
    await finalizedReadOnlyRuntime.ingestAvailable();
  assert.equal(finalizedReadOnlyIngest.finalizedReadOnly, true);
  assert.equal(finalizedReadOnlyIngest.written, 0);

  const tamperDir = path.join(temp, 'capture-tamper-case');
  const tamperRuntime = new EvidenceRuntime({
    runDir: tamperDir,
    debugSessionId: 'sess-tamper',
    runId: 'run-tamper',
    runSnapshotId: 'snapshot-tamper',
    processEpoch: 1,
    ringMaxRecords: 100,
    ringMaxAgeMs: 10000
  });
  await tamperRuntime.init();
  for (const [seq, at] of [
    [1, '2026-09-18T12:40:00.000Z'],
    [2, '2026-09-18T12:40:01.000Z']
  ]) {
    await tamperRuntime.store.appendObservation({
      observationId: 'obs:tamper:' + seq,
      processEpoch: 1,
      arenaEpoch: 0,
      resourceEpoch: 0,
      writerId: 'tamper-writer',
      writerSeq: seq,
      level: 'L2',
      lane: 'BEHAVIOR_TRANSITION',
      observedAt: at,
      gameTime: 700 + seq,
      scope: { kind: 'ENTITY_UUID', entityUuid },
      source: { side: 'SERVER', method: 'tamper-selftest' },
      epistemicStatus: 'OBSERVED',
      completeness: { complete: true },
      payload: { seq }
    });
  }

  const tamperCapture = await tamperRuntime.capturePreRoll({
    captureId: 'capture-tamper',
    triggerAt: '2026-09-18T12:40:01.000Z',
    requestedPreRollMs: 1000,
    entityUuid
  });
  const tamperedManifest = JSON.parse(
    await readFile(tamperCapture.file, 'utf8')
  );
  tamperedManifest.coverage.availablePreRollMs += 1;
  await writeFile(
    tamperCapture.file,
    JSON.stringify(tamperedManifest, null, 2) + '\n',
    'utf8'
  );

  let manifestTamperRejected = false;
  try {
    await finalizeEvidenceRun({
      debugSessionId: 'sess-tamper',
      runId: 'run-tamper',
      runSnapshotId: 'snapshot-tamper',
      runSnapshotHash: 'sha256:tamper',
      processEpoch: 1,
      runDir: tamperDir,
      status: 'STOPPED',
      live: false,
      evidenceShutdown: {
        clean: true,
        status: 'CLEAN_EVIDENCE_SHUTDOWN',
        ack: { writerDroppedTotal: 0, remainingQueue: 0 }
      }
    }, {
      cleanShutdown: true,
      shutdownMode: 'PROBE_FLUSH_ACK_THEN_PROCESS_STOP'
    });
  } catch (error) {
    manifestTamperRejected =
      /capture coverage replay mismatch/.test(error.message);
  }
  assert.equal(manifestTamperRejected, true);

  const contentTamperDir = path.join(temp, 'capture-content-tamper-case');
  const contentTamperRuntime = new EvidenceRuntime({
    runDir: contentTamperDir,
    debugSessionId: 'sess-content-tamper',
    runId: 'run-content-tamper',
    runSnapshotId: 'snapshot-content-tamper',
    processEpoch: 1,
    ringMaxRecords: 100,
    ringMaxAgeMs: 10000
  });
  await contentTamperRuntime.init();
  await contentTamperRuntime.store.appendObservation({
    observationId: 'obs:content-tamper:1',
    processEpoch: 1,
    arenaEpoch: 0,
    resourceEpoch: 0,
    writerId: 'content-tamper-writer',
    writerSeq: 1,
    level: 'L2',
    lane: 'BEHAVIOR_TRANSITION',
    observedAt: '2026-09-18T12:50:00.000Z',
    gameTime: 800,
    scope: { kind: 'ENTITY_UUID', entityUuid },
    source: { side: 'SERVER', method: 'content-tamper-selftest' },
    epistemicStatus: 'OBSERVED',
    completeness: { complete: true },
    payload: { value: 'before' }
  });
  await contentTamperRuntime.capturePreRoll({
    captureId: 'capture-content-tamper',
    triggerAt: '2026-09-18T12:50:00.000Z',
    requestedPreRollMs: 0,
    entityUuid
  });

  const canonicalFile = path.join(
    contentTamperDir,
    'evidence',
    'observations.jsonl'
  );
  const canonicalRows = (await readFile(canonicalFile, 'utf8'))
    .trim()
    .split(/\r?\n/)
    .map((line) => JSON.parse(line));
  canonicalRows[0].payload.value = 'after';
  await writeFile(
    canonicalFile,
    canonicalRows.map((row) => JSON.stringify(row)).join('\n') + '\n',
    'utf8'
  );

  let canonicalContentTamperRejected = false;
  try {
    await finalizeEvidenceRun({
      debugSessionId: 'sess-content-tamper',
      runId: 'run-content-tamper',
      runSnapshotId: 'snapshot-content-tamper',
      runSnapshotHash: 'sha256:content-tamper',
      processEpoch: 1,
      runDir: contentTamperDir,
      status: 'STOPPED',
      live: false,
      evidenceShutdown: {
        clean: true,
        status: 'CLEAN_EVIDENCE_SHUTDOWN',
        ack: { writerDroppedTotal: 0, remainingQueue: 0 }
      }
    }, {
      cleanShutdown: true,
      shutdownMode: 'PROBE_FLUSH_ACK_THEN_PROCESS_STOP'
    });
  } catch (error) {
    canonicalContentTamperRejected =
      /capture canonical prefix proof mismatch/.test(error.message);
  }
  assert.equal(canonicalContentTamperRejected, true);

  console.log('evidence selftest OK');
} finally {
  await rm(temp, { recursive: true, force: true });
}
