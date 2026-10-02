import { appendFile, mkdir, readFile, stat } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import path from 'node:path';
import { ObservationRingBuffer } from './ring-buffer.mjs';
import {
  EVIDENCE_VERSION,
  assertValidFinding,
  assertValidObservation,
  normalizeCompleteness,
  validateLaneHealth,
  validateObservation,
} from './schema.mjs';

function nowIso() {
  return new Date().toISOString();
}

function stableJson(value) {
  if (Array.isArray(value)) return '[' + value.map(stableJson).join(',') + ']';
  if (value && typeof value === 'object') {
    const keys = Object.keys(value).sort();
    return '{' + keys.map((k) => JSON.stringify(k) + ':' + stableJson(value[k])).join(',') + '}';
  }
  return JSON.stringify(value);
}

function scopeKey(scope) {
  return stableJson(scope);
}

function writerOrderKeyFor(record) {
  // Producer rows already passed the producer's delta gate. Its physical writer
  // sequence spans arena/resource resets; only a new process starts a new stream.
  const identity = [record.writerId, record.processEpoch];
  if (record.producerDeltaApplied !== true) identity.push(record.arenaEpoch, record.resourceEpoch);
  return identity.join('|');
}

function deltaKey(record) {
  return record.lane + '|' + scopeKey(record.scope);
}

function comparablePayload(record) {
  return stableJson({
    payload: record.payload,
    epistemicStatus: record.epistemicStatus,
    completeness: normalizeCompleteness(record.completeness),
  });
}

function idPart(value) {
  return String(value).replace(/[^A-Za-z0-9._:-]/g, '_').slice(0, 120);
}

export class LaneRegistry {
  constructor(identity) {
    this.identity = identity;
    this.lanes = new Map();
  }

  #entry(lane) {
    let entry = this.lanes.get(lane);
    if (!entry) {
      entry = {
        v: EVIDENCE_VERSION,
        kind: 'lane_health',
        debugSessionId: this.identity.debugSessionId,
        runId: this.identity.runId,
        ...(this.identity.runSnapshotId != null
          ? { runSnapshotId: this.identity.runSnapshotId }
          : {}),
        lane,
        status: 'UNKNOWN',
        count: 0,
        lastAt: null,
        lastSequence: 0,
        dropped: 0,
        errors: 0,
      };
      this.lanes.set(lane, entry);
    }
    return entry;
  }

  observed(lane, sequence, observedAt = nowIso()) {
    const e = this.#entry(lane);
    e.status = 'HEALTHY';
    e.count += 1;
    e.lastAt = observedAt;
    e.lastSequence = Math.max(e.lastSequence, sequence ?? 0);
    return { ...e };
  }

  dropped(lane, count = 1) {
    const e = this.#entry(lane);
    e.dropped += count;
    e.status = 'DEGRADED';
    return { ...e };
  }

  error(lane, count = 1) {
    const e = this.#entry(lane);
    e.errors += count;
    e.status = 'DEGRADED';
    return { ...e };
  }

  mark(lane, status) {
    const e = this.#entry(lane);
    e.status = status;
    return { ...e };
  }

  snapshot() {
    return [...this.lanes.values()].map((e) => ({ ...e }));
  }
}

export class DeltaGate {
  constructor(options = {}) {
    this.keyframeTicks = options.keyframeTicks ?? 100;
    this.last = new Map();
    this.epochs = null;
  }

  resetEpochs(identity) {
    const next = [
      identity.processEpoch ?? 0,
      identity.arenaEpoch ?? 0,
      identity.resourceEpoch ?? 0,
    ].join(':');
    if (this.epochs !== next) {
      this.epochs = next;
      this.last.clear();
      return true;
    }
    return false;
  }

  forgetScope(scope) {
    const suffix = '|' + scopeKey(scope);
    for (const key of [...this.last.keys()]) {
      if (key.endsWith(suffix)) this.last.delete(key);
    }
  }

  shouldWrite(record) {
    this.resetEpochs(record);
    if (record.level !== 'L1') return { write: true, reason: 'not-l1' };

    const key = deltaKey(record);
    const current = comparablePayload(record);
    const previous = this.last.get(key);
    const tick = Number.isInteger(record.gameTime) ? record.gameTime : null;

    if (!previous) {
      this.last.set(key, { value: current, tick });
      return { write: true, reason: 'first' };
    }

    const changed = previous.value !== current;
    const keyframe =
      tick != null &&
      previous.tick != null &&
      tick - previous.tick >= this.keyframeTicks;

    if (changed || keyframe) {
      this.last.set(key, { value: current, tick });
      return { write: true, reason: changed ? 'changed' : 'keyframe' };
    }

    return { write: false, reason: 'unchanged' };
  }
}

export class EvidenceStore {
  constructor(options) {
    this.runDir = options.runDir;
    this.identity = {
      debugSessionId: options.debugSessionId,
      runId: options.runId,
      runSnapshotId: options.runSnapshotId ?? null,
    };
    this.evidenceFile = path.join(this.runDir, 'evidence', 'observations.jsonl');
    this.findingsFile = path.join(this.runDir, 'evidence', 'findings.jsonl');
    this.healthFile = path.join(this.runDir, 'evidence', 'lane-health.jsonl');
    this.finalizationFile = path.join(
      this.runDir,
      'evidence',
      'finalization.json'
    );
    this.delta = new DeltaGate({ keyframeTicks: options.keyframeTicks ?? 100 });
    this.ring = new ObservationRingBuffer({
      maxRecords: options.ringMaxRecords ?? 2000,
      maxAgeMs: options.ringMaxAgeMs ?? 10000,
    });
    this.lanes = new LaneRegistry(this.identity);
    this.writerSeq = new Map();
    this.lastAcceptedWriterSeq = new Map();
    this.observationById = new Map();
    this.lastWrittenAt = null;
    this.lastWrittenGameTime = null;
  }

  async init() {
    await mkdir(path.join(this.runDir, 'evidence'), { recursive: true });

    const existing = await this.readObservations();
    for (const record of existing) {
      const validation = validateObservation(record);
      if (!validation.ok) {
        throw new Error(
          'existing canonical observation invalid: ' +
          record?.observationId + ': ' + validation.errors.join('; ')
        );
      }
      if (record.debugSessionId !== this.identity.debugSessionId ||
          record.runId !== this.identity.runId ||
          (this.identity.runSnapshotId != null &&
           record.runSnapshotId !== this.identity.runSnapshotId)) {
        throw new Error(
          'existing canonical observation identity mismatch: ' +
          record.observationId
        );
      }

      const serialized = stableJson(record);
      const previous = this.observationById.get(record.observationId);
      if (previous && previous !== serialized) {
        throw new Error(
          'existing canonical observation ID conflict: ' + record.observationId
        );
      }
      this.observationById.set(record.observationId, serialized);

      const writerOrderKey = writerOrderKeyFor(record);
      const previousSeq = this.lastAcceptedWriterSeq.get(writerOrderKey) ?? 0;
      if (record.producerDeltaApplied === true &&
          record.writerSeq > previousSeq + 1) {
        this.lanes.dropped(
          'OBSERVATION_WRITTEN',
          record.writerSeq - previousSeq - 1
        );
      }
      this.lastAcceptedWriterSeq.set(
        writerOrderKey,
        Math.max(previousSeq, record.writerSeq)
      );
      this.writerSeq.set(
        record.writerId,
        Math.max(this.writerSeq.get(record.writerId) ?? 0, record.writerSeq)
      );

      this.delta.shouldWrite(record);
      this.ring.push(record);
      this.lanes.observed(record.lane, record.writerSeq, record.observedAt);
      this.lastWrittenAt = record.observedAt;
      if (Number.isInteger(record.gameTime)) {
        this.lastWrittenGameTime = record.gameTime;
      }
    }

    return {
      existingObservations: existing.length,
    };
  }

  canonicalPrefixProof() {
    const entries = [...this.observationById.entries()];
    const observationIds = entries.map(([id]) => id);
    const idDigestInput =
      observationIds.length > 0
        ? observationIds.join('\n') + '\n'
        : '';
    const recordDigestInput =
      entries.length > 0
        ? entries.map(([, serialized]) => serialized).join('\n') + '\n'
        : '';

    return {
      count: observationIds.length,
      lastObservationId:
        observationIds.length > 0
          ? observationIds[observationIds.length - 1]
          : null,
      observationIdsSha256:
        'sha256:' +
        createHash('sha256')
          .update(idDigestInput, 'utf8')
          .digest('hex'),
      canonicalRecordsSha256:
        'sha256:' +
        createHash('sha256')
          .update(recordDigestInput, 'utf8')
          .digest('hex'),
    };
  }

  async assertMutable() {
    try {
      await stat(this.finalizationFile);
      throw new Error(
        'EVIDENCE_FINALIZED_READ_ONLY: ' + this.finalizationFile
      );
    } catch (error) {
      if (error?.code === 'ENOENT') return;
      throw error;
    }
  }

  nextSequence(writerId) {
    const next = (this.writerSeq.get(writerId) ?? 0) + 1;
    this.writerSeq.set(writerId, next);
    return next;
  }

  async appendObservation(input) {
    await this.assertMutable();
    const record = {
      ...input,
      v: EVIDENCE_VERSION,
      kind: 'observation',
      debugSessionId: this.identity.debugSessionId,
      runId: this.identity.runId,
      ...(this.identity.runSnapshotId != null
        ? { runSnapshotId: this.identity.runSnapshotId }
        : {}),
      observationId:
        input.observationId ||
        'obs:' + idPart(input.writerId) + ':' + String(input.writerSeq),
      completeness: normalizeCompleteness(input.completeness),
    };
    assertValidObservation(record);

    const serialized = stableJson(record);
    const existingById = this.observationById.get(record.observationId);
    if (existingById != null) {
      if (existingById !== serialized) {
        this.lanes.error(record.lane, 1);
        throw new Error(
          'observationId conflict with different content: ' + record.observationId
        );
      }
      return {
        written: false,
        reason: 'duplicate',
        observationId: record.observationId,
      };
    }

    const writerOrderKey = writerOrderKeyFor(record);
    const previousSeq = this.lastAcceptedWriterSeq.get(writerOrderKey) ?? 0;
    if (record.writerSeq <= previousSeq) {
      this.lanes.error(record.lane, 1);
      throw new Error(
        'writer sequence must increase monotonically: writer=' + record.writerId +
        ' previous=' + previousSeq + ' current=' + record.writerSeq
      );
    }

    if (record.producerDeltaApplied === true &&
        record.writerSeq > previousSeq + 1) {
      this.lanes.dropped(
        'OBSERVATION_WRITTEN',
        record.writerSeq - previousSeq - 1
      );
    }

    const gate = record.producerDeltaApplied === true
      ? { write: true, reason: 'producer-delta' }
      : this.delta.shouldWrite(record);
    if (!gate.write) {
      this.lastAcceptedWriterSeq.set(writerOrderKey, record.writerSeq);
      this.writerSeq.set(
        record.writerId,
        Math.max(this.writerSeq.get(record.writerId) ?? 0, record.writerSeq)
      );
      return {
        written: false,
        reason: gate.reason,
        observationId: record.observationId,
      };
    }

    await appendFile(this.evidenceFile, JSON.stringify(record) + '\n', 'utf8');
    this.observationById.set(record.observationId, serialized);
    this.lastAcceptedWriterSeq.set(writerOrderKey, record.writerSeq);
    this.writerSeq.set(
      record.writerId,
      Math.max(this.writerSeq.get(record.writerId) ?? 0, record.writerSeq)
    );
    this.lastWrittenAt = record.observedAt;
    this.lastWrittenGameTime = Number.isInteger(record.gameTime)
      ? record.gameTime
      : this.lastWrittenGameTime;
    this.ring.push(record);
    this.lanes.observed(record.lane, record.writerSeq, record.observedAt);
    return {
      written: true,
      reason: gate.reason,
      observationId: record.observationId,
      record,
    };
  }

  async appendFinding(input) {
    await this.assertMutable();
    const record = {
      ...input,
      v: EVIDENCE_VERSION,
      kind: 'finding',
      debugSessionId: this.identity.debugSessionId,
      runId: this.identity.runId,
      ...(this.identity.runSnapshotId != null
        ? { runSnapshotId: this.identity.runSnapshotId }
        : {}),
      createdAt: input.createdAt || nowIso(),
    };
    assertValidFinding(record);
    await appendFile(this.findingsFile, JSON.stringify(record) + '\n', 'utf8');
    return record;
  }

  async flushLaneHealth() {
    await this.assertMutable();
    const rows = this.lanes.snapshot();
    for (const row of rows) {
      const validation = validateLaneHealth(row);
      if (!validation.ok) {
        throw new TypeError('invalid lane health: ' + validation.errors.join('; '));
      }
      await appendFile(this.healthFile, JSON.stringify(row) + '\n', 'utf8');
    }
    return rows;
  }

  async maybeHeartbeat(input = {}) {
    const silenceTicks = Number.isInteger(input.silenceTicks) ? input.silenceTicks : 20;
    const silenceMs = Number.isInteger(input.silenceMs) ? input.silenceMs : 1000;
    const observedAt = input.observedAt || nowIso();
    const observedMs = Date.parse(observedAt);
    const lastMs = this.lastWrittenAt == null ? null : Date.parse(this.lastWrittenAt);

    const tickSilent =
      Number.isInteger(input.gameTime) &&
      Number.isInteger(this.lastWrittenGameTime)
        ? input.gameTime - this.lastWrittenGameTime >= silenceTicks
        : null;
    const timeSilent =
      Number.isFinite(observedMs) && Number.isFinite(lastMs)
        ? observedMs - lastMs >= silenceMs
        : null;

    const silentEnough =
      this.lastWrittenAt == null ||
      tickSilent === true ||
      (tickSilent == null && timeSilent === true);

    if (!silentEnough) {
      return {
        written: false,
        reason: 'not-silent',
      };
    }

    return await this.heartbeat({
      ...input,
      observedAt,
    });
  }

  async heartbeat(input) {
    const writerId = input.writerId || 'orchestrator';
    const seq = input.writerSeq ?? this.nextSequence(writerId);
    return await this.appendObservation({
      processEpoch: input.processEpoch ?? 0,
      arenaEpoch: input.arenaEpoch ?? 0,
      resourceEpoch: input.resourceEpoch ?? 0,
      writerId,
      writerSeq: seq,
      level: 'L0',
      lane: input.lane || 'CLIENT_TICK',
      observedAt: input.observedAt || nowIso(),
      gameTime: input.gameTime,
      scope: { kind: 'GLOBAL_HEALTH' },
      source: {
        side: input.side || 'ORCHESTRATOR',
        method: input.method || 'heartbeat',
      },
      epistemicStatus: 'OBSERVED',
      completeness: { complete: true },
      payload: {
        heartbeat: true,
        ...(input.payload || {}),
      },
    });
  }

  async readObservations() {
    try {
      const text = await readFile(this.evidenceFile, 'utf8');
      return text.split(/\r?\n/).filter(Boolean).map((line) => JSON.parse(line));
    } catch (error) {
      if (error?.code === 'ENOENT') return [];
      throw error;
    }
  }

  async readFindings() {
    try {
      const text = await readFile(this.findingsFile, 'utf8');
      return text.split(/\r?\n/).filter(Boolean).map((line) => JSON.parse(line));
    } catch (error) {
      if (error?.code === 'ENOENT') return [];
      throw error;
    }
  }
}
