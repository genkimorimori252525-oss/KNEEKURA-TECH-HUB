import {
  mkdir,
  open,
  readFile,
  readdir,
  rename,
  stat,
  writeFile,
} from 'node:fs/promises';
import path from 'node:path';
import { randomBytes } from 'node:crypto';
import { EvidenceStore } from './store.mjs';
import { EvidenceBroker } from './broker.mjs';
import { RawEvidenceIngestor } from './ingest.mjs';
import { persistPreRollCapture } from './capture.mjs';
import { TriggerCaptureController, persistTriggerWindow } from './trigger-capture.mjs';

function nowIso() {
  return new Date().toISOString();
}

async function exists(file) {
  try {
    await stat(file);
    return true;
  } catch {
    return false;
  }
}

async function writeJsonAtomic(file, value) {
  await mkdir(path.dirname(file), { recursive: true });
  const temp = file + '.tmp-' + randomBytes(6).toString('hex');
  await writeFile(temp, JSON.stringify(value, null, 2) + '\n', 'utf8');
  await rename(temp, file);
}

function fileIdentity(stats) {
  const dev = Number.isFinite(stats.dev) ? Number(stats.dev) : null;
  const ino = Number.isFinite(stats.ino) ? Number(stats.ino) : null;
  const birthtimeMs = Number.isFinite(stats.birthtimeMs) && stats.birthtimeMs > 0
    ? stats.birthtimeMs
    : null;
  return { dev, ino, birthtimeMs };
}

function sameFileIdentity(a, b) {
  if (!a || !b) return true;
  if (a.dev != null && a.ino != null && b.dev != null && b.ino != null) {
    return a.dev === b.dev && a.ino === b.ino;
  }
  if (a.birthtimeMs != null && b.birthtimeMs != null) {
    return Math.abs(a.birthtimeMs - b.birthtimeMs) < 1;
  }
  return true;
}

export class EvidenceRuntime {
  constructor(options) {
    this.runDir = options.runDir;
    this.debugSessionId = options.debugSessionId;
    this.runId = options.runId;
    this.processEpoch = options.processEpoch;
    this.runSnapshotId = options.runSnapshotId ?? null;

    this.store = new EvidenceStore({
      runDir: this.runDir,
      debugSessionId: this.debugSessionId,
      runId: this.runId,
      runSnapshotId: this.runSnapshotId,
      keyframeTicks: options.keyframeTicks ?? 100,
      ringMaxRecords: options.ringMaxRecords ?? 2000,
      ringMaxAgeMs: options.ringMaxAgeMs ?? 10000,
    });
    this.ingestor = new RawEvidenceIngestor(this.store, {
      processEpoch: this.processEpoch,
      runSnapshotId: this.runSnapshotId,
    });
    this.broker = new EvidenceBroker(this.store);

    this.cursorFile = path.join(
      this.runDir,
      'evidence',
      'ingest-state.json'
    );
    this.finalizationFile = path.join(
      this.runDir,
      'evidence',
      'finalization.json'
    );
    this.cursorState = null;
    this.finalized = false;
    this.triggerController = null;
  }

  async init() {
    const restored = await this.store.init();
    this.cursorState = await this.#loadCursorState();
    this.finalized = await exists(this.finalizationFile);
    return {
      restored,
      rawDir: this.rawDir(),
      cursorFile: this.cursorFile,
      finalized: this.finalized,
    };
  }

  rawDir() {
    return path.join(this.runDir, 'evidence', 'raw');
  }

  async #loadCursorState() {
    if (!(await exists(this.cursorFile))) {
      return {
        v: 1,
        debugSessionId: this.debugSessionId,
        runId: this.runId,
        runSnapshotId: this.runSnapshotId,
        processEpoch: this.processEpoch,
        files: {},
        updatedAt: null,
      };
    }

    const state = JSON.parse(await readFile(this.cursorFile, 'utf8'));
    if (state.v !== 1 ||
        state.debugSessionId !== this.debugSessionId ||
        state.runId !== this.runId ||
        (state.runSnapshotId ?? null) !== this.runSnapshotId ||
        state.processEpoch !== this.processEpoch ||
        !state.files ||
        typeof state.files !== 'object') {
      throw new Error(
        'ingest cursor identity/schema mismatch: ' + this.cursorFile
      );
    }
    return state;
  }

  async #saveCursorState() {
    this.cursorState.updatedAt = nowIso();
    await writeJsonAtomic(this.cursorFile, this.cursorState);
  }

  async listRawFiles() {
    try {
      const entries = await readdir(this.rawDir(), { withFileTypes: true });
      return entries
        .filter((entry) => entry.isFile() && entry.name.endsWith('.jsonl'))
        .map((entry) => path.join(this.rawDir(), entry.name))
        .sort();
    } catch (error) {
      if (error?.code === 'ENOENT') return [];
      throw error;
    }
  }

  async #ingestIncrementalFile(file) {
    if (!this.cursorState) {
      throw new Error('EvidenceRuntime.init() must be called before ingestion');
    }

    const name = path.basename(file);
    const stats = await stat(file);
    const currentIdentity = fileIdentity(stats);
    const previous = this.cursorState.files[name] || null;
    const offset = previous?.offset ?? 0;

    if (stats.size < offset) {
      throw new Error(
        'RAW_FILE_TRUNCATED file=' + file +
        ' previousOffset=' + offset +
        ' currentSize=' + stats.size
      );
    }

    if (previous?.identity &&
        !sameFileIdentity(previous.identity, currentIdentity)) {
      throw new Error(
        'RAW_FILE_REPLACED file=' + file
      );
    }

    const availableBytes = stats.size - offset;
    if (availableBytes === 0) {
      return {
        file,
        parsed: 0,
        written: 0,
        suppressed: 0,
        trailingPartial: false,
        bytesRead: 0,
        bytesConsumed: 0,
        offsetBefore: offset,
        offsetAfter: offset,
      };
    }

    const handle = await open(file, 'r');
    let buffer;
    try {
      buffer = Buffer.allocUnsafe(availableBytes);
      const { bytesRead } = await handle.read(
        buffer,
        0,
        availableBytes,
        offset
      );
      buffer = buffer.subarray(0, bytesRead);
    } finally {
      await handle.close();
    }

    const lastNewline = buffer.lastIndexOf(0x0a);
    if (lastNewline < 0) {
      this.cursorState.files[name] = {
        offset,
        identity: currentIdentity,
        lastSeenSize: stats.size,
        updatedAt: nowIso(),
      };
      await this.#saveCursorState();
      return {
        file,
        parsed: 0,
        written: 0,
        suppressed: 0,
        trailingPartial: true,
        bytesRead: buffer.length,
        bytesConsumed: 0,
        offsetBefore: offset,
        offsetAfter: offset,
      };
    }

    const complete = buffer.subarray(0, lastNewline + 1);
    const text = complete.toString('utf8');
    const result = await this.ingestor.ingestText(text, {
      source: file,
      allowTrailingPartial: false,
    });

    const nextOffset = offset + complete.length;
    this.cursorState.files[name] = {
      offset: nextOffset,
      identity: currentIdentity,
      lastSeenSize: stats.size,
      updatedAt: nowIso(),
    };
    await this.#saveCursorState();

    return {
      file,
      ...result,
      trailingPartial: complete.length < buffer.length,
      bytesRead: buffer.length,
      bytesConsumed: complete.length,
      offsetBefore: offset,
      offsetAfter: nextOffset,
    };
  }

  async ingestAvailable() {
    const files = await this.listRawFiles();
    if (this.finalized || await exists(this.finalizationFile)) {
      this.finalized = true;
      return {
        files: files.length,
        parsed: 0,
        written: 0,
        suppressed: 0,
        trailingPartialFiles: 0,
        bytesRead: 0,
        bytesConsumed: 0,
        results: [],
        finalizedReadOnly: true,
      };
    }
    const results = [];
    let parsed = 0;
    let written = 0;
    let suppressed = 0;
    let trailingPartialFiles = 0;
    let bytesRead = 0;
    let bytesConsumed = 0;

    for (const file of files) {
      const result = await this.#ingestIncrementalFile(file);
      results.push(result);
      parsed += result.parsed;
      written += result.written;
      suppressed += result.suppressed;
      bytesRead += result.bytesRead ?? 0;
      bytesConsumed += result.bytesConsumed ?? 0;
      if (result.trailingPartial) trailingPartialFiles++;
    }

    return {
      files: files.length,
      parsed,
      written,
      suppressed,
      trailingPartialFiles,
      bytesRead,
      bytesConsumed,
      results,
    };
  }

  async capturePreRoll(options = {}) {
    if (this.finalized || await exists(this.finalizationFile)) {
      this.finalized = true;
      throw new Error(
        'EVIDENCE_FINALIZED_READ_ONLY: ' + this.finalizationFile
      );
    }
    const ingest = await this.ingestAvailable();
    const requestedPreRollMs =
      Number.isInteger(options.requestedPreRollMs)
        ? options.requestedPreRollMs
        : 5000;
    const triggerAt = options.triggerAt || nowIso();
    const entityUuid =
      typeof options.entityUuid === 'string' && options.entityUuid
        ? options.entityUuid
        : null;
    const lanes =
      Array.isArray(options.lanes) && options.lanes.length
        ? [...new Set(options.lanes.map(String))]
        : null;

    const filter = (record) => {
      if (entityUuid &&
          (record.scope?.kind !== 'ENTITY_UUID' ||
           record.scope.entityUuid !== entityUuid)) {
        return false;
      }
      if (lanes && !lanes.includes(record.lane)) {
        return false;
      }
      return true;
    };

    const canonicalCut = this.store.canonicalPrefixProof();
    const ringConfig = {
      maxRecords: this.store.ring.maxRecords,
      maxAgeMs: this.store.ring.maxAgeMs,
    };

    const capture = this.store.ring.capturePreRoll({
      triggerAt,
      requestedPreRollMs,
      filter,
    });

    const stamp = new Date(triggerAt)
      .toISOString()
      .replace(/[-:.]/g, '');
    const captureId =
      options.captureId ||
      ('capture-' + stamp + '-' + randomBytes(4).toString('hex'));

    const persisted = await persistPreRollCapture({
      runDir: this.runDir,
      debugSessionId: this.debugSessionId,
      runId: this.runId,
      runSnapshotId: this.runSnapshotId,
      processEpoch: this.processEpoch,
      captureId,
      capture,
      canonicalCut,
      ringConfig,
      filter: {
        entityUuid,
        lanes,
      },
    });

    return {
      ingest,
      ...persisted,
    };
  }

  armTriggerCapture(config, requestCapture = null, acceptTrigger = null) {
    if (this.finalized || this.triggerController) throw new Error('TRIGGER_OWNER_NOT_AVAILABLE');
    this.triggerController = new TriggerCaptureController(this, config, requestCapture, acceptTrigger);
    return { enabled: true, continuousRecording: false };
  }

  triggerCapture(kind, sourceObservationId, captureId) {
    if (!this.triggerController || this.finalized) throw new Error('TRIGGER_NOT_CONFIGURED');
    return this.triggerController.trigger(kind, sourceObservationId, captureId);
  }

  async pollTriggerCaptures(nowMs = Date.now()) {
    if (!this.triggerController) return [];
    if (this.finalized || await exists(this.finalizationFile)) {
      this.triggerController.close(); this.finalized = true;
      throw new Error('EVIDENCE_FINALIZED_READ_ONLY');
    }
    this.triggerController.observeDeclaredTriggers();
    const windows = await this.triggerController.poll(nowMs);
    const retained = [];
    for (const window of windows) retained.push(await persistTriggerWindow(this, window));
    return retained;
  }

  async refresh() {
    const ingest = await this.ingestAvailable();
    const triggerCaptures = await this.pollTriggerCaptures();
    return {
      ingest,
      status: await this.broker.status(),
      ...(triggerCaptures.length ? { triggerCaptures } : {}),
    };
  }
}

export function evidenceRuntimeFromCurrent(current, options = {}) {
  if (!current || typeof current !== 'object') {
    throw new TypeError('current debug state is required');
  }
  if (!current.runDir ||
      !current.debugSessionId ||
      !current.runId ||
      !Number.isInteger(current.processEpoch)) {
    throw new Error(
      'current debug state lacks runDir/debugSessionId/runId/processEpoch'
    );
  }

  return new EvidenceRuntime({
    runDir: current.runDir,
    debugSessionId: current.debugSessionId,
    runId: current.runId,
    processEpoch: current.processEpoch,
    runSnapshotId: current.runSnapshotId ?? null,
    keyframeTicks: options.keyframeTicks,
    ringMaxRecords: options.ringMaxRecords,
    ringMaxAgeMs: options.ringMaxAgeMs,
  });
}
