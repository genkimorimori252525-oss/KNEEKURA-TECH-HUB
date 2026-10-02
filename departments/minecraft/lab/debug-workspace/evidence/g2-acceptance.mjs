import { createHash, randomBytes } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';

const GLOBAL_REQUIRED_LANES = Object.freeze([
  'CLIENT_TICK',
  'SERVER_TICK',
]);

const CORE_REQUIRED_LANES = Object.freeze([
  'TARGET_TRACKED',
  'ENTITY_STATE',
  'SERVER_TARGET_TRACKED',
  'SERVER_ENTITY_STATE',
  'AI_TARGET',
  'BRAIN_MEMORY',
  'RUNNING_BEHAVIORS',
  'NAVIGATION',
  'TLM_STATE',
]);

const EXPECTED_SOURCE_SIDE = Object.freeze({
  CLIENT_TICK: 'CLIENT',
  SERVER_TICK: 'SERVER',
  TARGET_TRACKED: 'CLIENT',
  ENTITY_STATE: 'CLIENT',
  SERVER_TARGET_TRACKED: 'SERVER',
  SERVER_ENTITY_STATE: 'SERVER',
  AI_TARGET: 'SERVER',
  BRAIN_MEMORY: 'SERVER',
  RUNNING_BEHAVIORS: 'SERVER',
  NAVIGATION: 'SERVER',
  TLM_STATE: 'SERVER',
  REIMU_STATE: 'SERVER',
});

const DEFAULT_FRESH_MS = Object.freeze({
  CLIENT_TICK: 3000,
  SERVER_TICK: 3000,
  TARGET_TRACKED: 7000,
  ENTITY_STATE: 7000,
  SERVER_TARGET_TRACKED: 7000,
  SERVER_ENTITY_STATE: 7000,
  AI_TARGET: 7000,
  BRAIN_MEMORY: 7000,
  RUNNING_BEHAVIORS: 7000,
  NAVIGATION: 7000,
  TLM_STATE: 7000,
  REIMU_STATE: 7000,
});

function nowIso() {
  return new Date().toISOString();
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function latestPerLane(records) {
  const out = new Map();
  // readObservations() preserves canonical evidence-file order. Do not use
  // wall-clock timestamps as a causal total order here.
  for (const row of records) {
    out.set(row.lane, row);
  }
  return out;
}

function validateRow(
  row,
  lane,
  current,
  entityUuid,
  targetRevision,
  nowMs,
  freshMs
) {
  const errors = [];
  if (!row) {
    return { ok: false, lane, errors: ['MISSING_LANE'], row: null };
  }
  if (row.runSnapshotId !== current.runSnapshotId) {
    errors.push('RUN_SNAPSHOT_MISMATCH');
  }
  if (row.processEpoch !== current.processEpoch) {
    errors.push('PROCESS_EPOCH_MISMATCH');
  }
  if (row.scope?.kind !== 'ENTITY_UUID' ||
      row.scope?.entityUuid !== entityUuid) {
    errors.push('ENTITY_SCOPE_MISMATCH');
  }
  if (row.epistemicStatus !== 'OBSERVED') {
    errors.push('NOT_OBSERVED');
  }
  if (row.level !== 'L1') {
    errors.push('UNEXPECTED_OBSERVATION_LEVEL');
  }
  const expectedSide = EXPECTED_SOURCE_SIDE[lane] ?? null;
  if (expectedSide && row.source?.side !== expectedSide) {
    errors.push('SOURCE_AUTHORITY_MISMATCH');
  }
  if (row.completeness?.complete !== true) {
    errors.push('INCOMPLETE_OBSERVATION');
  }
  if (!Number.isInteger(targetRevision) || targetRevision <= 0) {
    errors.push('INVALID_EXPECTED_TARGET_REVISION');
  } else if (row.payload?.targetRevision !== targetRevision) {
    errors.push('TARGET_REVISION_MISMATCH');
  }
  const observedMs = Date.parse(row.observedAt);
  const ageMs = Number.isFinite(observedMs) ? Math.max(0, nowMs - observedMs) : null;
  if (ageMs == null) {
    errors.push('INVALID_OBSERVED_AT');
  } else if (ageMs > freshMs) {
    errors.push('STALE_OBSERVATION');
  }

  if ((lane === 'TARGET_TRACKED' || lane === 'SERVER_TARGET_TRACKED') &&
      row.payload?.tracked !== true) {
    errors.push('TARGET_NOT_TRACKED');
  }

  return {
    ok: errors.length === 0,
    lane,
    ageMs,
    freshMs,
    observationId: row.observationId,
    observedAt: row.observedAt,
    sourceSide: row.source?.side ?? null,
    errors,
    row,
  };
}

function validateGlobalRow(row, lane, current, nowMs, freshMs) {
  const errors = [];
  if (!row) {
    return { ok: false, lane, errors: ['MISSING_LANE'] };
  }
  if (row.runSnapshotId !== current.runSnapshotId) {
    errors.push('RUN_SNAPSHOT_MISMATCH');
  }
  if (row.processEpoch !== current.processEpoch) {
    errors.push('PROCESS_EPOCH_MISMATCH');
  }
  if (row.scope?.kind !== 'GLOBAL_HEALTH') {
    errors.push('GLOBAL_SCOPE_MISMATCH');
  }
  if (row.epistemicStatus !== 'OBSERVED') {
    errors.push('NOT_OBSERVED');
  }
  if (row.level !== 'L0') {
    errors.push('UNEXPECTED_OBSERVATION_LEVEL');
  }
  const expectedSide = EXPECTED_SOURCE_SIDE[lane] ?? null;
  if (expectedSide && row.source?.side !== expectedSide) {
    errors.push('SOURCE_AUTHORITY_MISMATCH');
  }
  if (row.completeness?.complete !== true) {
    errors.push('INCOMPLETE_OBSERVATION');
  }
  const observedMs = Date.parse(row.observedAt);
  const ageMs = Number.isFinite(observedMs)
    ? Math.max(0, nowMs - observedMs)
    : null;
  if (ageMs == null) {
    errors.push('INVALID_OBSERVED_AT');
  } else if (ageMs > freshMs) {
    errors.push('STALE_OBSERVATION');
  }

  return {
    ok: errors.length === 0,
    lane,
    ageMs,
    freshMs,
    observationId: row.observationId,
    observedAt: row.observedAt,
    sourceSide: row.source?.side ?? null,
    errors,
  };
}

export async function waitForG2Evidence(options) {
  const {
    runtime,
    current,
    entityUuid,
    targetRevision,
    requireReimu = false,
    timeoutMs = 15000,
    pollMs = 250,
  } = options;

  if (!runtime || !current || !entityUuid ||
      !Number.isInteger(targetRevision) || targetRevision <= 0) {
    throw new TypeError(
      'waitForG2Evidence requires runtime/current/entityUuid/targetRevision'
    );
  }

  const requiredLanes = [
    ...CORE_REQUIRED_LANES,
    ...(requireReimu ? ['REIMU_STATE'] : []),
  ];

  const deadline = Date.now() + timeoutMs;
  let last = null;

  while (Date.now() <= deadline) {
    const ingest = await runtime.ingestAvailable();
    const observations = await runtime.store.readObservations();
    const entityRows = observations.filter(
      (row) =>
        row.scope?.kind === 'ENTITY_UUID' &&
        row.scope.entityUuid === entityUuid
    );
    const latest = latestPerLane(entityRows);
    const latestAll = latestPerLane(observations);
    const nowMs = Date.now();

    const lanes = Object.fromEntries(
      requiredLanes.map((lane) => {
        const result = validateRow(
          latest.get(lane),
          lane,
          current,
          entityUuid,
          targetRevision,
          nowMs,
          DEFAULT_FRESH_MS[lane] ?? 7000
        );
        const { row, ...publicResult } = result;
        return [lane, publicResult];
      })
    );

    const globalLanes = Object.fromEntries(
      GLOBAL_REQUIRED_LANES.map((lane) => [
        lane,
        validateGlobalRow(
          latestAll.get(lane),
          lane,
          current,
          nowMs,
          DEFAULT_FRESH_MS[lane] ?? 3000
        ),
      ])
    );

    const status = await runtime.broker.status({ compact: true });
    const allRequiredLanes = [
      ...GLOBAL_REQUIRED_LANES,
      ...requiredLanes,
    ];
    const unhealthy = status.health.filter(
      (row) =>
        allRequiredLanes.includes(row.lane) &&
        ['STALE', 'DEGRADED', 'FAILED'].includes(row.effectiveStatus)
    );

    const ok =
      Object.values(globalLanes).every((row) => row.ok) &&
      Object.values(lanes).every((row) => row.ok) &&
      unhealthy.length === 0 &&
      status.overallHealth.totalDropped === 0 &&
      status.overallHealth.totalErrors === 0 &&
      status.overallHealth.maxWriterDroppedTotal === 0;

    last = {
      ok,
      checkedAt: nowIso(),
      debugSessionId: current.debugSessionId,
      runId: current.runId,
      runSnapshotId: current.runSnapshotId,
      processEpoch: current.processEpoch,
      entityUuid,
      targetRevision,
      requireReimu,
      globalRequiredLanes: GLOBAL_REQUIRED_LANES,
      requiredLanes,
      ingest,
      globalLanes,
      lanes,
      health: {
        overall: status.overallHealth,
        unhealthyRequiredLanes: unhealthy.map((row) => ({
          lane: row.lane,
          effectiveStatus: row.effectiveStatus,
          dropped: row.dropped,
          errors: row.errors,
          ageMs: row.ageMs,
        })),
      },
    };

    if (ok) return last;
    await sleep(pollMs);
  }

  return {
    ...(last || {
      checkedAt: nowIso(),
      debugSessionId: current.debugSessionId,
      runId: current.runId,
      runSnapshotId: current.runSnapshotId,
      processEpoch: current.processEpoch,
      entityUuid,
      targetRevision,
      requireReimu,
      globalRequiredLanes: GLOBAL_REQUIRED_LANES,
      requiredLanes,
      globalLanes: {},
      lanes: {},
      health: null,
    }),
    ok: false,
    timedOut: true,
    timeoutMs,
  };
}

function requiredTargetEvidenceRows(evidenceGate) {
  const lanes = Array.isArray(evidenceGate?.requiredLanes)
    ? evidenceGate.requiredLanes
    : [];
  return lanes.map((lane) => {
    const row = evidenceGate?.lanes?.[lane];
    if (!row?.observationId || !row?.observedAt || row.ok !== true) {
      throw new Error(
        'G2 capture plan requires a passing observation for lane ' + lane
      );
    }
    const observedMs = Date.parse(row.observedAt);
    if (!Number.isFinite(observedMs)) {
      throw new Error(
        'G2 capture plan found invalid observedAt for lane ' + lane
      );
    }
    return {
      lane,
      observationId: row.observationId,
      observedAt: row.observedAt,
      observedMs,
    };
  });
}

export function planG2CaptureWindow(
  evidenceGate,
  options = {}
) {
  const minimumPreRollMs =
    options.minimumPreRollMs == null ? 1000 : options.minimumPreRollMs;
  const maxPreRollMs =
    options.maxPreRollMs == null ? 10000 : options.maxPreRollMs;
  const nowMs =
    options.nowMs == null ? Date.now() : options.nowMs;

  if (!Number.isInteger(minimumPreRollMs) || minimumPreRollMs < 1) {
    throw new TypeError('minimumPreRollMs must be an integer >= 1');
  }
  if (!Number.isInteger(maxPreRollMs) ||
      maxPreRollMs < minimumPreRollMs) {
    throw new TypeError(
      'maxPreRollMs must be an integer >= minimumPreRollMs'
    );
  }
  if (!Number.isFinite(nowMs)) {
    throw new TypeError('nowMs must be finite');
  }

  const rows = requiredTargetEvidenceRows(evidenceGate);
  if (!rows.length) {
    throw new Error('G2 capture plan has no required target observations');
  }

  const earliestObservedMs = Math.min(...rows.map((row) => row.observedMs));
  const triggerMs = Math.max(
    nowMs,
    earliestObservedMs + minimumPreRollMs
  );
  const requestedPreRollMs = triggerMs - earliestObservedMs;

  if (requestedPreRollMs > maxPreRollMs) {
    throw new Error(
      'G2 required evidence exceeds ring pre-roll capacity: required=' +
      requestedPreRollMs + ' max=' + maxPreRollMs
    );
  }

  return {
    triggerAt: new Date(triggerMs).toISOString(),
    requestedPreRollMs,
    waitMs: Math.max(0, triggerMs - nowMs),
    earliestRequiredObservedAt:
      new Date(earliestObservedMs).toISOString(),
    requiredObservationIds: rows.map((row) => row.observationId),
    requiredLaneObservationIds: Object.fromEntries(
      rows.map((row) => [row.lane, row.observationId])
    ),
  };
}

async function writeJsonExclusive(file, value) {
  await mkdir(path.dirname(file), { recursive: true });
  await writeFile(
    file,
    JSON.stringify(value, null, 2) + '\n',
    { encoding: 'utf8', flag: 'wx' }
  );
}

async function hashFile(file) {
  const bytes = await readFile(file);
  return {
    size: bytes.length,
    sha256: 'sha256:' + createHash('sha256').update(bytes).digest('hex'),
  };
}

export async function writeG2Acceptance(options) {
  const {
    started,
    timeline,
    liveStatus,
    target,
    evidenceGate,
    capture,
    stopped,
    finalization,
  } = options;

  if (!started?.runDir || !started?.runSnapshotId) {
    throw new Error('G2 acceptance missing started run identity');
  }

  const sameIdentity =
    target?.debugSessionId === started.debugSessionId &&
    target?.runId === started.runId &&
    target?.runSnapshotId === started.runSnapshotId &&
    target?.processEpoch === started.processEpoch;

  const captureManifest = capture?.manifest ?? null;
  const finalManifest = finalization?.manifest ?? null;
  const expectedLanes = [
    ...CORE_REQUIRED_LANES,
    ...(evidenceGate?.requireReimu === true ? ['REIMU_STATE'] : []),
  ];
  const evidenceLaneContractBound =
    Array.isArray(evidenceGate?.globalRequiredLanes) &&
    GLOBAL_REQUIRED_LANES.every(
      (lane) =>
        evidenceGate.globalRequiredLanes.includes(lane) &&
        evidenceGate.globalLanes?.[lane]?.ok === true
    ) &&
    Array.isArray(evidenceGate?.requiredLanes) &&
    expectedLanes.every(
      (lane) =>
        evidenceGate.requiredLanes.includes(lane) &&
        evidenceGate.lanes?.[lane]?.ok === true
    );
  const requiredCaptureObservationIds = expectedLanes
    .map((lane) => evidenceGate?.lanes?.[lane]?.observationId)
    .filter((id) => typeof id === 'string' && id);
  const captureObservationIds = new Set(
    Array.isArray(captureManifest?.observationIds)
      ? captureManifest.observationIds
      : []
  );
  const captureEvidenceBound =
    requiredCaptureObservationIds.length === expectedLanes.length &&
    requiredCaptureObservationIds.every(
      (id) => captureObservationIds.has(id)
    );
  const captureLaneContractBound =
    Array.isArray(captureManifest?.filter?.lanes) &&
    expectedLanes.every(
      (lane) => captureManifest.filter.lanes.includes(lane)
    ) &&
    Number.isInteger(captureManifest?.requestedPreRollMs) &&
    captureManifest.requestedPreRollMs >= 1000 &&
    captureEvidenceBound;
  const evidenceIdentityBound =
    evidenceGate?.debugSessionId === started.debugSessionId &&
    evidenceGate?.runId === started.runId &&
    evidenceGate?.runSnapshotId === started.runSnapshotId &&
    evidenceGate?.processEpoch === started.processEpoch;
  const captureIdentityBound =
    captureManifest?.debugSessionId === started.debugSessionId &&
    captureManifest?.runId === started.runId &&
    captureManifest?.runSnapshotId === started.runSnapshotId &&
    captureManifest?.processEpoch === started.processEpoch;
  const finalizationIdentityBound =
    finalManifest?.debugSessionId === started.debugSessionId &&
    finalManifest?.runId === started.runId &&
    finalManifest?.runSnapshotId === started.runSnapshotId &&
    finalManifest?.processEpoch === started.processEpoch;
  const captureFinalized =
    typeof capture?.file === 'string' &&
    Array.isArray(finalManifest?.artifacts) &&
    finalManifest.artifacts.some(
      (artifact) => artifact.path === capture.file
    );
  const targetRevisionValid =
    Number.isInteger(target?.revision) &&
    target.revision > 0;
  const evidenceTargetRevisionBound =
    targetRevisionValid &&
    evidenceGate?.targetRevision === target.revision;
  const targetUuidBound =
    typeof target?.targetUuid === 'string' &&
    evidenceGate?.entityUuid === target.targetUuid &&
    captureManifest?.filter?.entityUuid === target.targetUuid;

  const passed =
    started.status === 'DEBUG_READY' &&
    timeline?.complete === true &&
    liveStatus?.live === true &&
    sameIdentity &&
    targetRevisionValid &&
    evidenceTargetRevisionBound &&
    evidenceIdentityBound &&
    evidenceLaneContractBound &&
    captureIdentityBound &&
    captureLaneContractBound &&
    captureEvidenceBound &&
    finalizationIdentityBound &&
    targetUuidBound &&
    evidenceGate?.ok === true &&
    captureManifest?.coverage?.truncated === false &&
    captureFinalized &&
    stopped?.ok === true &&
    stopped?.evidenceShutdown?.clean === true &&
    finalManifest?.status === 'EVIDENCE_COMPLETE' &&
    finalManifest?.runSnapshotId === started.runSnapshotId;

  const file = path.join(started.runDir, 'g2-acceptance.json');
  const manifest = {
    schemaVersion: 1,
    gate: 'G2_OBSERVATION_CORE',
    result: passed ? 'PASS' : 'FAIL',
    recordedAt: nowIso(),
    acceptanceId: 'g2-' + randomBytes(8).toString('hex'),
    debugSessionId: started.debugSessionId,
    runId: started.runId,
    runSnapshotId: started.runSnapshotId,
    runSnapshotHash: started.runSnapshotHash ?? null,
    processEpoch: started.processEpoch,
    entityUuid: target?.targetUuid ?? null,
    targetRevision: target?.revision ?? null,
    requireReimu: evidenceGate?.requireReimu === true,
    timelineComplete: timeline?.complete === true,
    runtimeWasLiveBeforeStop: liveStatus?.live === true,
    targetIdentityBound: sameIdentity,
    targetRevisionValid,
    evidenceTargetRevisionBound,
    evidenceIdentityBound,
    evidenceLaneContractBound,
    captureIdentityBound,
    captureLaneContractBound,
    captureEvidenceBound,
    requiredCaptureObservationIds,
    finalizationIdentityBound,
    targetUuidBound,
    captureFinalized,
    evidenceGate,
    preRoll: captureManifest
      ? {
          captureId: captureManifest.captureId,
          requestedPreRollMs: captureManifest.requestedPreRollMs,
          coverage: captureManifest.coverage,
          observationIds: captureManifest.observationIds,
          canonicalCut: captureManifest.canonicalCut ?? null,
        }
      : null,
    cleanEvidenceShutdown: stopped?.evidenceShutdown?.clean === true,
    evidenceFinalization: finalManifest
      ? {
          status: finalManifest.status,
          finalizedAt: finalManifest.finalizedAt,
          counts: finalManifest.counts,
          captures: finalManifest.captures,
        }
      : null,
  };

  await writeJsonExclusive(file, manifest);
  const integrity = await hashFile(file);

  return {
    file,
    manifest,
    integrity,
  };
}

export const G2_GLOBAL_REQUIRED_LANES = GLOBAL_REQUIRED_LANES;
export const G2_CORE_REQUIRED_LANES = CORE_REQUIRED_LANES;
