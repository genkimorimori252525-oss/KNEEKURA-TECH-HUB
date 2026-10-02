function timeOf(record) {
  const value = Date.parse(record?.observedAt);
  return Number.isFinite(value) ? value : -Infinity;
}

function latestByLane(observations) {
  const map = new Map();
  for (const record of observations) {
    const previous = map.get(record.lane);
    if (!previous || timeOf(record) >= timeOf(previous)) {
      map.set(record.lane, record);
    }
  }
  return map;
}

function anomaly({
  watchpointId,
  version = 1,
  statement,
  status,
  observation,
  lane,
  limitations = [],
}) {
  return {
    kind: 'anomaly',
    anomalyId:
      'anomaly:' + watchpointId + ':' +
      (observation?.observationId || lane || 'unknown'),
    watchpointId,
    watchpointVersion: version,
    epistemicStatus: 'DERIVED',
    status,
    statement,
    evidenceIds: observation ? [observation.observationId] : [],
    lane: lane || observation?.lane || null,
    scope: observation?.scope || { kind: 'GLOBAL_HEALTH' },
    observedAt: observation?.observedAt || null,
    limitations,
  };
}

/**
 * Built-in L2 watchpoints.
 *
 * These are intentionally narrow. They report an abnormal observable state,
 * never a root cause. Cause hypotheses belong to Finding/Hypothesis records.
 */
export function evaluateBuiltInWatchpoints({
  observations,
  health = [],
}) {
  const latest = latestByLane(observations);
  const out = [];

  const target = latest.get('TARGET_TRACKED');
  if (target &&
      target.payload?.tracked === false &&
      target.payload?.reason !== 'target_cleared') {
    out.push(anomaly({
      watchpointId: 'TARGET_NOT_TRACKED',
      statement: 'The explicitly selected target is not currently tracked by the client.',
      status: 'TRIGGERED',
      observation: target,
      limitations: [
        'This does not distinguish despawn, unload, dimension change, network loss, or an invalid expectation.',
      ],
    }));
  }

  const entityState = latest.get('ENTITY_STATE');
  if (entityState && entityState.payload?.alive === false) {
    out.push(anomaly({
      watchpointId: 'TARGET_NOT_ALIVE',
      statement: 'The latest exact-target entity state reports alive=false.',
      status: 'TRIGGERED',
      observation: entityState,
      limitations: [
        'This is a state observation, not an explanation of why the entity became non-alive.',
      ],
    }));
  }

  if (entityState && entityState.payload?.removed === true) {
    out.push(anomaly({
      watchpointId: 'TARGET_REMOVED',
      statement: 'The latest exact-target entity state reports removed=true.',
      status: 'TRIGGERED',
      observation: entityState,
      limitations: [
        'Removal reason is not inferred by this watchpoint.',
      ],
    }));
  }

  for (const lane of ['CLIENT_TICK', 'SERVER_TICK']) {
    const h = health.find((row) => row.lane === lane);
    const evidence = latest.get(lane);
    const explicitlyPaused =
      lane === 'SERVER_TICK' &&
      latest.get('CLIENT_TICK')?.payload?.paused === true;

    if (h?.effectiveStatus === 'STALE' && evidence && !explicitlyPaused) {
      out.push(anomaly({
        watchpointId: lane + '_STALE',
        statement:
          lane + ' produced evidence previously but is now beyond its stale threshold.',
        status: 'TRIGGERED',
        observation: evidence,
        lane,
        limitations: [
          'A stale heartbeat does not by itself prove a crash; scheduling delay or observation failure remain possible.',
        ],
      }));
    }

    if (h && (h.dropped > 0 || h.errors > 0) && evidence) {
      out.push(anomaly({
        watchpointId: lane + '_EVIDENCE_DEGRADED',
        statement:
          lane + ' has recorded dropped evidence or writer errors.',
        status: 'TRIGGERED',
        observation: evidence,
        lane,
        limitations: [
          'The anomaly describes evidence quality, not target runtime behavior.',
        ],
      }));
    }
  }

  return out;
}
