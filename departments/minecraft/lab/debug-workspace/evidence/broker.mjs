import { evaluateBuiltInWatchpoints } from './watchpoints.mjs';
import {
  assertValidFinding,
  validateObservation,
} from './schema.mjs';

function scopeMatches(record, scope) {
  if (!scope) return true;
  if (!record?.scope) return false;
  if (scope.kind && record.scope.kind !== scope.kind) return false;
  if (scope.entityUuid && record.scope.entityUuid !== scope.entityUuid) return false;
  if (scope.experimentId && record.scope.experimentId !== scope.experimentId) return false;
  if (scope.subsystem && record.scope.subsystem !== scope.subsystem) return false;
  return true;
}

function identityKey(record) {
  return [
    record.debugSessionId,
    record.runId,
    record.runSnapshotId ?? 'NO_SNAPSHOT',
    record.processEpoch,
    record.arenaEpoch,
    record.resourceEpoch,
  ].join('|');
}

function observationTime(record) {
  const value = Date.parse(record.observedAt);
  return Number.isFinite(value) ? value : -Infinity;
}

export function buildEvidenceCut(records, options = {}) {
  const supportedModes = ['LATEST_PER_LANE', 'BEST_EFFORT', 'BOUNDED_SKEW', 'SAME_TICK_WHERE_AVAILABLE'];
  if (options.coherenceMode != null && !supportedModes.includes(options.coherenceMode)) {
    return { ok: false, reason: 'UNSUPPORTED_COHERENCE_MODE', records: [], writerLastSequence: {} };
  }
  const scoped = records.filter((record) =>
    record.kind === 'observation' &&
    scopeMatches(record, options.scope) &&
    (!options.lanes || options.lanes.includes(record.lane))
  );

  if (scoped.length === 0) {
    return {
      ok: false,
      reason: 'NO_EVIDENCE',
      coherenceMode: options.coherenceMode || 'BEST_EFFORT',
      records: [],
      writerLastSequence: {},
    };
  }

  const identities = new Set(scoped.map(identityKey));
  if (identities.size !== 1) {
    return {
      ok: false,
      reason: 'EVIDENCE_CONTEXT_CHANGED',
      identities: [...identities],
      coherenceMode: options.coherenceMode || 'BEST_EFFORT',
      records: [],
      writerLastSequence: {},
    };
  }

  const coherenceMode = options.coherenceMode || 'LATEST_PER_LANE';
  const maxSkewMs = options.maxSkewMs ?? 250;
  const sorted = [...scoped].sort((a, b) => observationTime(a) - observationTime(b));

  const latestByLane = new Map();
  for (const record of sorted) {
    latestByLane.set(record.lane, record);
  }

  const selected = [...latestByLane.values()].sort(
    (a, b) => observationTime(a) - observationTime(b)
  );

  const times = selected.map(observationTime).filter(Number.isFinite);
  const minMs = times.length ? Math.min(...times) : null;
  const maxMs = times.length ? Math.max(...times) : null;
  const skewMs = minMs == null || maxMs == null ? null : maxMs - minMs;

  if (coherenceMode === 'SAME_TICK_WHERE_AVAILABLE') {
    const ticks = selected
      .map((x) => x.gameTime)
      .filter((x) => Number.isInteger(x));
    if (ticks.length > 1 && new Set(ticks).size !== 1) {
      return {
        ok: false,
        reason: 'EVIDENCE_TICK_MISMATCH',
        coherenceMode,
        ticks,
        records: selected,
        writerLastSequence: writerCut(selected),
      };
    }
  }

  if (coherenceMode === 'BOUNDED_SKEW' &&
      skewMs != null &&
      skewMs > maxSkewMs) {
    return {
      ok: false,
      reason: 'EVIDENCE_SKEW_EXCEEDED',
      coherenceMode,
      maxSkewMs,
      skewMs,
      records: selected,
      writerLastSequence: writerCut(selected),
    };
  }

  return {
    ok: true,
    reason: null,
    coherenceMode,
    maxSkewMs: coherenceMode === 'BOUNDED_SKEW' ? maxSkewMs : null,
    skewMs,
    identity: identityKey(selected[0]),
    observedFrom: minMs == null ? null : new Date(minMs).toISOString(),
    observedTo: maxMs == null ? null : new Date(maxMs).toISOString(),
    records: selected,
    writerLastSequence: writerCut(selected),
    ordering: {
      perWriterSequenceAuthoritative: true,
      gameTimeRole: 'CORRELATION_ONLY_UNLESS_SHARED_TICK_IS_EXPLICITLY_REQUIRED',
      wallClockRole: 'CORRELATION_AND_SKEW_ONLY',
      crossWriterCausality: 'NOT_PROVEN_BY_TIMESTAMP',
    },
  };
}

function writerCut(records) {
  const out = {};
  for (const record of records) {
    const prev = out[record.writerId] ?? 0;
    out[record.writerId] = Math.max(prev, record.writerSeq ?? 0);
  }
  return out;
}

function latestPerLane(records) {
  const map = new Map();
  for (const record of records) {
    const previous = map.get(record.lane);
    if (!previous || observationTime(record) >= observationTime(previous)) {
      map.set(record.lane, record);
    }
  }
  return map;
}

const DEFAULT_STALE_AFTER_MS = new Map([
  ['CLIENT_TICK', 3000],
  ['SERVER_TICK', 3000],
  ['TARGET_TRACKED', 7000],
  ['ENTITY_STATE', 7000],
  ['SERVER_TARGET_TRACKED', 7000],
  ['SERVER_ENTITY_STATE', 7000],
  ['AI_TARGET', 7000],
  ['BRAIN_MEMORY', 7000],
  ['RUNNING_BEHAVIORS', 7000],
  ['NAVIGATION', 7000],
  ['TLM_STATE', 7000],
  ['REIMU_STATE', 7000],
]);

function staleThresholdForLane(lane, options = {}) {
  if (options.staleAfterMs != null) {
    return options.staleAfterMs;
  }
  return DEFAULT_STALE_AFTER_MS.get(lane) ?? null;
}

function healthSeverity(status) {
  switch (status) {
    case 'DEGRADED': return 5;
    case 'STALE': return 4;
    case 'UNKNOWN': return 3;
    case 'STOPPED': return 2;
    case 'IDLE': return 1;
    case 'HEALTHY': return 0;
    default: return 3;
  }
}

function compactObservationSummary(record) {
  return {
    observationId: record.observationId,
    lane: record.lane,
    level: record.level,
    observedAt: record.observedAt,
    gameTime: record.gameTime ?? null,
    scope: record.scope,
    epistemicStatus: record.epistemicStatus,
    completeness: record.completeness,
    writerId: record.writerId,
    writerSeq: record.writerSeq,
    clock: record.clock ?? null,
  };
}

function laneRates(observations, nowMs, windowMs) {
  const counts = new Map();
  const cutoff = Number.isFinite(nowMs) ? nowMs - windowMs : -Infinity;

  for (const record of observations) {
    const ms = observationTime(record);
    if (!Number.isFinite(ms) || ms < cutoff || ms > nowMs) continue;
    counts.set(record.lane, (counts.get(record.lane) ?? 0) + 1);
  }

  const seconds = windowMs / 1000;
  return Object.fromEntries(
    [...counts.entries()].map(([lane, count]) => [
      lane,
      {
        windowMs,
        count,
        rateHz: seconds > 0 ? count / seconds : 0,
      },
    ])
  );
}

function latestWriterTelemetry(observations) {
  const latest = new Map();

  for (const record of observations) {
    const previous = latest.get(record.writerId);
    if (!previous || observationTime(record) >= observationTime(previous)) {
      latest.set(record.writerId, record);
    }
  }

  return Object.fromEntries(
    [...latest.entries()].map(([writerId, record]) => [
      writerId,
      {
        writerId,
        lastSequence: record.writerSeq,
        lastAt: record.observedAt,
        queueDepth:
          Number.isInteger(record.writerQueueDepth)
            ? record.writerQueueDepth
            : null,
        droppedTotal:
          Number.isInteger(record.writerDroppedTotal)
            ? record.writerDroppedTotal
            : null,
        producerDeltaApplied: record.producerDeltaApplied === true,
        clock: record.clock ?? null,
      },
    ])
  );
}

function finiteNumber(value) {
  return typeof value === 'number' && Number.isFinite(value);
}

function vectorDistance(a, b, fields) {
  if (!a || !b || fields.some((field) => !finiteNumber(a[field]) || !finiteNumber(b[field]))) {
    return null;
  }
  let sum = 0;
  for (const field of fields) {
    const d = a[field] - b[field];
    sum += d * d;
  }
  return Math.sqrt(sum);
}

function recordSkewMs(a, b) {
  if (!a || !b) return null;
  const ams = observationTime(a);
  const bms = observationTime(b);
  if (!Number.isFinite(ams) || !Number.isFinite(bms)) return null;
  return Math.abs(ams - bms);
}

export function summarizeClientServerConsistency(current, options = {}) {
  const maxCompareSkewMs = options.maxCompareSkewMs ?? 500;
  const positionWarnBlocks = options.positionWarnBlocks ?? 0.5;
  const velocityWarn = options.velocityWarn ?? 0.25;

  const clientTracked = current?.TARGET_TRACKED ?? null;
  const serverTracked = current?.SERVER_TARGET_TRACKED ?? null;
  const clientState = current?.ENTITY_STATE ?? null;
  const serverState = current?.SERVER_ENTITY_STATE ?? null;

  const warnings = [];
  const tracking = {
    available: Boolean(clientTracked && serverTracked),
    clientTracked: clientTracked?.payload?.tracked ?? null,
    serverTracked: serverTracked?.payload?.tracked ?? null,
    skewMs: recordSkewMs(clientTracked, serverTracked),
    agrees: null,
  };

  if (tracking.available &&
      typeof tracking.clientTracked === 'boolean' &&
      typeof tracking.serverTracked === 'boolean') {
    tracking.agrees = tracking.clientTracked === tracking.serverTracked;
    if (!tracking.agrees) {
      warnings.push('CLIENT_SERVER_TRACKING_DISAGREEMENT');
    }
  }

  const stateSkewMs = recordSkewMs(clientState, serverState);
  const comparable =
    Boolean(clientState && serverState) &&
    stateSkewMs != null &&
    stateSkewMs <= maxCompareSkewMs;

  const positionDistance = vectorDistance(
    clientState?.payload,
    serverState?.payload,
    ['x', 'y', 'z']
  );
  const velocityDistance = vectorDistance(
    clientState?.payload,
    serverState?.payload,
    ['vx', 'vy', 'vz']
  );

  const booleans = {};
  for (const field of ['onGround', 'alive', 'removed', 'noGravity']) {
    const clientValue = clientState?.payload?.[field];
    const serverValue = serverState?.payload?.[field];
    booleans[field] = {
      client: typeof clientValue === 'boolean' ? clientValue : null,
      server: typeof serverValue === 'boolean' ? serverValue : null,
      agrees:
        typeof clientValue === 'boolean' &&
        typeof serverValue === 'boolean'
          ? clientValue === serverValue
          : null,
    };
    if (comparable && booleans[field].agrees === false) {
      warnings.push('CLIENT_SERVER_' + field.toUpperCase() + '_DISAGREEMENT');
    }
  }

  if (comparable && positionDistance != null &&
      positionDistance > positionWarnBlocks) {
    warnings.push('CLIENT_SERVER_POSITION_DIVERGENCE');
  }
  if (comparable && velocityDistance != null &&
      velocityDistance > velocityWarn) {
    warnings.push('CLIENT_SERVER_VELOCITY_DIVERGENCE');
  }

  return {
    tracking,
    state: {
      available: Boolean(clientState && serverState),
      comparable,
      reason:
        !clientState || !serverState
          ? 'MISSING_CLIENT_OR_SERVER_STATE'
          : (stateSkewMs == null
              ? 'MISSING_OBSERVATION_TIME'
              : (stateSkewMs > maxCompareSkewMs
                  ? 'OBSERVATION_SKEW_EXCEEDED'
                  : null)),
      skewMs: stateSkewMs,
      maxCompareSkewMs,
      positionDistance,
      velocityDistance,
      thresholds: {
        positionWarnBlocks,
        velocityWarn,
      },
      booleans,
    },
    warnings,
  };
}

export function summarizeAiConsistency(current, options = {}) {
  const maxCompareSkewMs = options.maxAiCompareSkewMs ?? 500;
  const ai = current?.AI_TARGET ?? null;
  const brain = current?.BRAIN_MEMORY ?? null;
  const navigation = current?.NAVIGATION ?? null;

  const warnings = [];
  const attackSkewMs = recordSkewMs(ai, brain);
  const attackComparable =
    Boolean(ai && brain) &&
    attackSkewMs != null &&
    attackSkewMs <= maxCompareSkewMs;

  const mobTargetPresent =
    typeof ai?.payload?.present === 'boolean'
      ? ai.payload.present
      : null;
  const brainTargetPresent =
    typeof brain?.payload?.attackTargetPresent === 'boolean'
      ? brain.payload.attackTargetPresent
      : null;
  const mobTargetUuid =
    typeof ai?.payload?.targetUuid === 'string'
      ? ai.payload.targetUuid
      : null;
  const brainTargetUuid =
    typeof brain?.payload?.attackTargetUuid === 'string'
      ? brain.payload.attackTargetUuid
      : null;

  let attackPresenceAgrees = null;
  let attackUuidAgrees = null;
  if (attackComparable &&
      mobTargetPresent != null &&
      brainTargetPresent != null) {
    attackPresenceAgrees = mobTargetPresent === brainTargetPresent;
    if (!attackPresenceAgrees) {
      warnings.push('MOB_BRAIN_ATTACK_TARGET_PRESENCE_MISMATCH');
    }

    if (mobTargetPresent && brainTargetPresent &&
        mobTargetUuid != null && brainTargetUuid != null) {
      attackUuidAgrees = mobTargetUuid === brainTargetUuid;
      if (!attackUuidAgrees) {
        warnings.push('MOB_BRAIN_ATTACK_TARGET_UUID_MISMATCH');
      }
    }
  }

  const movementSkewMs = recordSkewMs(brain, navigation);
  const movementComparable =
    Boolean(brain && navigation) &&
    movementSkewMs != null &&
    movementSkewMs <= maxCompareSkewMs;

  const walkTargetPresent =
    typeof brain?.payload?.walkTargetPresent === 'boolean'
      ? brain.payload.walkTargetPresent
      : null;
  const brainPathPresent =
    typeof brain?.payload?.pathMemoryPresent === 'boolean'
      ? brain.payload.pathMemoryPresent
      : null;
  const navigationPathPresent =
    typeof navigation?.payload?.pathPresent === 'boolean'
      ? navigation.payload.pathPresent
      : null;
  const navigationDone =
    typeof navigation?.payload?.navigationDone === 'boolean'
      ? navigation.payload.navigationDone
      : null;

  if (movementComparable &&
      walkTargetPresent === true &&
      navigationPathPresent === false &&
      navigationDone === true) {
    warnings.push('WALK_TARGET_WITHOUT_ACTIVE_NAVIGATION_PATH');
  }

  if (movementComparable &&
      brainPathPresent === true &&
      navigationPathPresent === false) {
    warnings.push('BRAIN_PATH_WITHOUT_NAVIGATION_PATH');
  }

  return {
    attackTarget: {
      available: Boolean(ai && brain),
      comparable: attackComparable,
      reason:
        !ai || !brain
          ? 'MISSING_AI_TARGET_OR_BRAIN_MEMORY'
          : (attackSkewMs == null
              ? 'MISSING_OBSERVATION_TIME'
              : (attackSkewMs > maxCompareSkewMs
                  ? 'OBSERVATION_SKEW_EXCEEDED'
                  : null)),
      skewMs: attackSkewMs,
      maxCompareSkewMs,
      mobTargetPresent,
      brainTargetPresent,
      mobTargetUuid,
      brainTargetUuid,
      presenceAgrees: attackPresenceAgrees,
      uuidAgrees: attackUuidAgrees,
    },
    movement: {
      available: Boolean(brain && navigation),
      comparable: movementComparable,
      reason:
        !brain || !navigation
          ? 'MISSING_BRAIN_MEMORY_OR_NAVIGATION'
          : (movementSkewMs == null
              ? 'MISSING_OBSERVATION_TIME'
              : (movementSkewMs > maxCompareSkewMs
                  ? 'OBSERVATION_SKEW_EXCEEDED'
                  : null)),
      skewMs: movementSkewMs,
      maxCompareSkewMs,
      walkTargetPresent,
      brainPathPresent,
      navigationPathPresent,
      navigationDone,
    },
    warnings,
  };
}

function observationSummary(record) {
  return {
    observationId: record.observationId,
    lane: record.lane,
    level: record.level,
    observedAt: record.observedAt,
    gameTime: record.gameTime ?? null,
    scope: record.scope,
    epistemicStatus: record.epistemicStatus,
    completeness: record.completeness,
    payload: record.payload,
    source: record.source,
    writerId: record.writerId,
    writerSeq: record.writerSeq,
  };
}

export class EvidenceBroker {
  constructor(store) {
    this.store = store;
  }

  async status(options = {}) {
    const observations = await this.store.readObservations();
    const latest = latestPerLane(observations);
    const compact = options.compact !== false;
    const lanes = {};

    for (const [lane, record] of latest) {
      lanes[lane] = compact
        ? compactObservationSummary(record)
        : observationSummary(record);
    }

    const nowMs =
      options.now == null
        ? Date.now()
        : (typeof options.now === 'number' ? options.now : Date.parse(options.now));
    const rateWindowMs = options.rateWindowMs ?? 5000;
    const rates = laneRates(observations, nowMs, rateWindowMs);

    const health = this.store.lanes.snapshot().map((row) => {
      const lastMs = row.lastAt == null ? null : Date.parse(row.lastAt);
      const ageMs =
        Number.isFinite(nowMs) && Number.isFinite(lastMs)
          ? Math.max(0, nowMs - lastMs)
          : null;
      const staleAfterMs = staleThresholdForLane(row.lane, options);
      const stale =
        staleAfterMs != null &&
        ageMs != null &&
        ageMs > staleAfterMs &&
        row.status !== 'STOPPED';

      return {
        ...row,
        effectiveStatus: stale ? 'STALE' : row.status,
        ageMs,
        staleAfterMs,
        rate: rates[row.lane] || {
          windowMs: rateWindowMs,
          count: 0,
          rateHz: 0,
        },
      };
    });

    const writers = latestWriterTelemetry(observations);
    const totalDropped = health.reduce((sum, row) => sum + row.dropped, 0);
    const totalErrors = health.reduce((sum, row) => sum + row.errors, 0);
    const maxWriterQueueDepth = Math.max(
      0,
      ...Object.values(writers)
        .map((writer) => writer.queueDepth)
        .filter(Number.isInteger)
    );
    const maxWriterDroppedTotal = Math.max(
      0,
      ...Object.values(writers)
        .map((writer) => writer.droppedTotal)
        .filter(Number.isInteger)
    );
    const worst = health.reduce(
      (selected, row) =>
        selected == null ||
        healthSeverity(row.effectiveStatus) > healthSeverity(selected.effectiveStatus)
          ? row
          : selected,
      null
    );

    return {
      debugSessionId: this.store.identity.debugSessionId,
      runId: this.store.identity.runId,
      runSnapshotId: this.store.identity.runSnapshotId,
      observationCount: observations.length,
      laneCount: latest.size,
      compact,
      overallHealth: {
        status: worst?.effectiveStatus || 'UNKNOWN',
        worstLane: worst?.lane || null,
        totalDropped,
        totalErrors,
        maxWriterQueueDepth,
        maxWriterDroppedTotal,
      },
      writers,
      lanes,
      health,
      ringCoverage: this.store.ring.coverage(),
    };
  }

  async entityCurrent(entityUuid, options = {}) {
    const observations = await this.store.readObservations();
    const entityRecords = observations.filter(
      (record) =>
        record.scope?.kind === 'ENTITY_UUID' &&
        record.scope.entityUuid === entityUuid
    );

    const cut = buildEvidenceCut(entityRecords, {
      scope: { kind: 'ENTITY_UUID', entityUuid },
      lanes: options.lanes,
      coherenceMode: options.coherenceMode || 'LATEST_PER_LANE',
      maxSkewMs: options.maxSkewMs ?? 250,
    });

    if (!cut.ok) return cut;

    const nowMs =
      options.now == null
        ? Date.now()
        : (typeof options.now === 'number' ? options.now : Date.parse(options.now));

    const current = Object.fromEntries(
      cut.records.map((record) => {
        const summary = observationSummary(record);
        const observedMs = observationTime(record);
        const ageMs =
          Number.isFinite(nowMs) && Number.isFinite(observedMs)
            ? Math.max(0, nowMs - observedMs)
            : null;
        const staleAfterMs = staleThresholdForLane(record.lane, options);
        return [
          record.lane,
          {
            ...summary,
            freshness: {
              ageMs,
              staleAfterMs,
              fresh:
                staleAfterMs == null ||
                ageMs == null ||
                ageMs <= staleAfterMs,
            },
          },
        ];
      })
    );

    return {
      ...cut,
      entityUuid,
      current,
      clientServer: summarizeClientServerConsistency(current, options),
      aiConsistency: summarizeAiConsistency(current, options),
    };
  }

  async changes(entityUuid, since) {
    const sinceMs = typeof since === 'number' ? since : Date.parse(since);
    const observations = await this.store.readObservations();

    return observations
      .filter(
        (record) =>
          record.scope?.kind === 'ENTITY_UUID' &&
          record.scope.entityUuid === entityUuid &&
          observationTime(record) >= sinceMs
      )
      .map(observationSummary);
  }

  async anomalies(options = {}) {
    const observations = await this.store.readObservations();
    const stored = observations
      .filter((record) =>
        record.level === 'L2' &&
        (record.lane.includes('ANOMALY') ||
         record.payload?.anomaly === true ||
         record.payload?.status === 'DEGRADED')
      )
      .map((record) => ({
        kind: 'observation_anomaly',
        ...observationSummary(record),
      }));

    const status = await this.status(options);
    const derived = evaluateBuiltInWatchpoints({
      observations,
      health: status.health,
    });

    return [...stored, ...derived];
  }

  async explainGap(lane, options = {}) {
    const health = this.store.lanes.snapshot().find((x) => x.lane === lane);
    if (!health) {
      return {
        lane,
        status: 'UNKNOWN',
        explanation: 'lane has not produced evidence in this run',
      };
    }

    if (health.dropped > 0 || health.errors > 0) {
      return {
        lane,
        status: 'DEGRADED',
        explanation: 'evidence loss or writer errors were recorded',
        health,
      };
    }

    if (health.status === 'STOPPED') {
      return {
        lane,
        status: 'STOPPED',
        explanation: 'lane was explicitly stopped',
        health,
      };
    }

    const nowMs =
      options.now == null
        ? Date.now()
        : (typeof options.now === 'number' ? options.now : Date.parse(options.now));
    const staleAfterMs = staleThresholdForLane(lane, options);
    const lastMs = health.lastAt == null ? null : Date.parse(health.lastAt);
    const ageMs =
      Number.isFinite(nowMs) && Number.isFinite(lastMs)
        ? Math.max(0, nowMs - lastMs)
        : null;

    if (staleAfterMs != null && ageMs != null && ageMs > staleAfterMs) {
      return {
        lane,
        status: 'STALE',
        explanation: 'lane produced evidence before, but no recent observation is available',
        ageMs,
        staleAfterMs,
        health,
      };
    }

    return {
      lane,
      status: health.status,
      explanation:
        health.count === 0
          ? 'lane exists but has no observations'
          : 'no explicit gap cause is recorded',
      ageMs,
      staleAfterMs,
      health,
    };
  }

  async createFinding(input) {
    const observations = await this.store.readObservations();
    const byId = new Map(observations.map((x) => [x.observationId, x]));
    const missing = (input.evidenceIds || []).filter((id) => !byId.has(id));
    if (missing.length) {
      throw new Error(
        'finding references missing observation IDs: ' + missing.join(', ')
      );
    }

    const selected = input.evidenceIds.map((id) => byId.get(id));
    const validationErrors = [];
    for (const record of selected) {
      const v = validateObservation(record);
      if (!v.ok) {
        validationErrors.push(record.observationId + ': ' + v.errors.join(', '));
      }
    }
    if (validationErrors.length) {
      throw new Error('finding source evidence invalid: ' + validationErrors.join('; '));
    }

    const identities = new Set(
      selected.map((x) =>
        x.debugSessionId + '|' +
        x.runId + '|' +
        (x.runSnapshotId ?? 'NO_SNAPSHOT')
      )
    );
    if (identities.size !== 1) {
      throw new Error('finding cannot combine evidence from different runs');
    }

    const finding = {
      v: 1,
      kind: 'finding',
      findingId: input.findingId,
      debugSessionId: this.store.identity.debugSessionId,
      runId: this.store.identity.runId,
      ...(this.store.identity.runSnapshotId != null
        ? { runSnapshotId: this.store.identity.runSnapshotId }
        : {}),
      statement: input.statement,
      epistemicStatus: input.epistemicStatus || 'INFERRED',
      evidenceIds: [...input.evidenceIds],
      limitations: Array.isArray(input.limitations) ? [...input.limitations] : [],
      createdAt: input.createdAt || new Date().toISOString(),
    };

    assertValidFinding(finding);
    return await this.store.appendFinding(finding);
  }
}
