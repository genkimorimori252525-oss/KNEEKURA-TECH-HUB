import { createHash } from 'node:crypto';
import {
  mkdir,
  lstat,
  readFile,
  readdir,
  realpath,
  stat,
  writeFile,
} from 'node:fs/promises';
import path from 'node:path';
import { evidenceRuntimeFromCurrent } from './runtime.mjs';
import { ObservationRingBuffer } from './ring-buffer.mjs';
import { readRawVisualImage, validateVisualIdentity, validateVisualManifest } from './visual-capture.mjs';
import { TriggerCaptureController } from './trigger-capture.mjs';
import { decodeJson, exactKeys, identifier } from '../bridge/json.mjs';
import { readRegisteredFile } from '../bridge/materials.mjs';
import { sealMobPovArtifacts } from '../bridge/mob-pov.mjs';

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

async function sha256File(file) {
  const bytes = await readFile(file);
  return {
    path: file,
    size: bytes.length,
    sha256: 'sha256:' + createHash('sha256').update(bytes).digest('hex'),
  };
}

async function collectArtifacts(runDir) {
  const candidates = [
    path.join(runDir, 'run-snapshot.json'),
    path.join(runDir, 'ready.json'),
    path.join(runDir, 'timeline.jsonl'),
    path.join(runDir, 'process.log'),
    path.join(runDir, 'evidence', 'observations.jsonl'),
    path.join(runDir, 'evidence', 'findings.jsonl'),
    path.join(runDir, 'evidence', 'lane-health.jsonl'),
    path.join(runDir, 'evidence', 'ingest-state.json'),
  ];

  const rawDir = path.join(runDir, 'evidence', 'raw');
  try {
    const entries = await readdir(rawDir, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.isFile()) {
        candidates.push(path.join(rawDir, entry.name));
      }
    }
  } catch (error) {
    if (error?.code !== 'ENOENT') throw error;
  }

  const captureDir = path.join(runDir, 'evidence', 'captures');
  try {
    const entries = await readdir(captureDir, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.isFile() && entry.name.endsWith('.json')) {
        candidates.push(path.join(captureDir, entry.name));
      }
    }
  } catch (error) {
    if (error?.code !== 'ENOENT') throw error;
  }

  const unique = [...new Set(candidates)].sort();
  const artifacts = [];
  for (const file of unique) {
    if (await exists(file)) {
      artifacts.push(await sha256File(file));
    }
  }
  return artifacts;
}

async function sealDerivedVisualArtifacts(runDir, artifacts) {
  if (artifacts.length > 1024) throw new TypeError('FINALIZATION_INVENTORY_LIMIT');
  let directory = runDir;
  try {
    for (const part of ['evidence', 'derived', 'visual']) {
      directory = path.join(directory, part);
      const info = await lstat(directory);
      if (info.isSymbolicLink() || !info.isDirectory() || await realpath(directory) !== path.resolve(directory)) {
        throw new TypeError('UNSAFE_DERIVED_DIRECTORY');
      }
    }
  } catch (error) {
    if (error.code === 'ENOENT') return;
    throw error;
  }
  const entries = await readdir(directory, { withFileTypes: true });
  if (artifacts.length + entries.length > 1024) throw new TypeError('FINALIZATION_INVENTORY_LIMIT');
  for (const entry of entries) {
    if (!entry.isFile() || !/^[a-f0-9]{64}\.(png|svg|json|html)$/.test(entry.name)) {
      throw new TypeError('UNSAFE_DERIVED_ARTIFACT');
    }
    const file = await readRegisteredFile({ root: runDir, relativePath: 'evidence/derived/visual/' + entry.name,
      expectedSha256: entry.name.slice(0, 64), maxBytes: 32 * 1024 * 1024, retainBytes: false });
    artifacts.push({ path: path.join(directory, entry.name), size: file.sizeBytes, sha256: 'sha256:' + file.sha256 });
  }
}

function stableJson(value) {
  if (Array.isArray(value)) {
    return '[' + value.map(stableJson).join(',') + ']';
  }
  if (value && typeof value === 'object') {
    const keys = Object.keys(value).sort();
    return '{' + keys.map(
      (key) => JSON.stringify(key) + ':' + stableJson(value[key])
    ).join(',') + '}';
  }
  return JSON.stringify(value);
}

function sha256Text(value) {
  return 'sha256:' +
    createHash('sha256').update(value, 'utf8').digest('hex');
}

function prefixProof(observations, count) {
  if (!Number.isInteger(count) || count < 0 || count > observations.length) {
    throw new Error('capture canonicalCut.count out of range');
  }
  const prefix = observations.slice(0, count);
  const ids = prefix.map((row) => row.observationId);
  const idInput = ids.length ? ids.join('\n') + '\n' : '';
  const recordInput = prefix.length
    ? prefix.map(stableJson).join('\n') + '\n'
    : '';

  return {
    prefix,
    proof: {
      count,
      lastObservationId: ids.length ? ids[ids.length - 1] : null,
      observationIdsSha256: sha256Text(idInput),
      canonicalRecordsSha256: sha256Text(recordInput),
    },
  };
}

function captureFilter(filter) {
  if (filter == null) {
    return {
      normalized: { entityUuid: null, lanes: null },
      predicate: () => true,
    };
  }
  if (typeof filter !== 'object' || Array.isArray(filter)) {
    throw new Error('capture filter invalid');
  }

  const entityUuid =
    filter.entityUuid == null
      ? null
      : String(filter.entityUuid);
  let lanes = null;
  if (filter.lanes != null) {
    if (!Array.isArray(filter.lanes) ||
        filter.lanes.some((lane) => typeof lane !== 'string' || !lane)) {
      throw new Error('capture filter lanes invalid');
    }
    lanes = [...new Set(filter.lanes)];
    if (lanes.length !== filter.lanes.length) {
      throw new Error('capture filter lanes contain duplicates');
    }
  }

  return {
    normalized: { entityUuid, lanes },
    predicate: (record) => {
      if (entityUuid &&
          (record.scope?.kind !== 'ENTITY_UUID' ||
           record.scope.entityUuid !== entityUuid)) {
        return false;
      }
      if (lanes && !lanes.includes(record.lane)) {
        return false;
      }
      return true;
    },
  };
}

function laneCounts(records) {
  const out = {};
  for (const record of records) {
    out[record.lane] = (out[record.lane] ?? 0) + 1;
  }
  return out;
}

function writerSequenceRanges(records) {
  const out = {};
  for (const record of records) {
    const current = out[record.writerId] ?? {
      first: record.writerSeq,
      last: record.writerSeq,
      count: 0,
    };
    current.first = Math.min(current.first, record.writerSeq);
    current.last = Math.max(current.last, record.writerSeq);
    current.count += 1;
    out[record.writerId] = current;
  }
  return out;
}

function assertStableEqual(actual, expected, message) {
  if (stableJson(actual) !== stableJson(expected)) {
    throw new Error(message);
  }
}

function replayAndValidateCapture(capture, file, observations) {
  if (capture.schemaVersion !== 1 ||
      capture.kind !== 'pre_roll_capture') {
    throw new Error('capture manifest schema mismatch: ' + file);
  }
  if (typeof capture.captureId !== 'string' ||
      path.basename(file) !== capture.captureId + '.json') {
    throw new Error('capture manifest filename/id mismatch: ' + file);
  }
  if (!capture.canonicalCut ||
      !capture.ringConfig ||
      !Number.isInteger(capture.ringConfig.maxRecords) ||
      capture.ringConfig.maxRecords < 1 ||
      !Number.isInteger(capture.ringConfig.maxAgeMs) ||
      capture.ringConfig.maxAgeMs < 1) {
    throw new Error('capture replay inputs missing/invalid: ' + file);
  }

  const { prefix, proof } = prefixProof(
    observations,
    capture.canonicalCut.count
  );
  assertStableEqual(
    capture.canonicalCut,
    proof,
    'capture canonical prefix proof mismatch: ' + file
  );

  const triggerMs = Date.parse(capture.triggerAt);
  if (!Number.isFinite(triggerMs) ||
      !Number.isInteger(capture.requestedPreRollMs) ||
      capture.requestedPreRollMs < 0) {
    throw new Error('capture trigger/pre-roll invalid: ' + file);
  }

  const filter = captureFilter(capture.filter);
  assertStableEqual(
    capture.filter ?? { entityUuid: null, lanes: null },
    filter.normalized,
    'capture filter normalization mismatch: ' + file
  );

  const ring = new ObservationRingBuffer({
    maxRecords: capture.ringConfig.maxRecords,
    maxAgeMs: capture.ringConfig.maxAgeMs,
  });
  for (const row of prefix) {
    ring.push(row);
  }

  const replay = ring.capturePreRoll({
    triggerAt: capture.triggerAt,
    requestedPreRollMs: capture.requestedPreRollMs,
    filter: filter.predicate,
  });

  const expectedIds = replay.records.map((row) => row.observationId);
  assertStableEqual(
    capture.observationIds,
    expectedIds,
    'capture observation selection mismatch: ' + file
  );

  const expectedCoverage = {
    requestedStartAt: replay.requestedStartAt,
    availablePreRollMs: replay.availablePreRollMs,
    truncated: replay.truncated,
    totalBufferedRecords: replay.totalBufferedRecords,
    selectedRecords: replay.records.length,
    droppedRecords: replay.droppedRecords,
    droppedInsideRequestedWindow: replay.droppedInsideRequestedWindow,
    bufferStartedTooLate: replay.bufferStartedTooLate,
    oldestSelectedAt: replay.oldestSelectedAt,
    newestSelectedAt: replay.newestSelectedAt,
  };
  assertStableEqual(
    capture.coverage,
    expectedCoverage,
    'capture coverage replay mismatch: ' + file
  );
  assertStableEqual(
    capture.laneCounts,
    laneCounts(replay.records),
    'capture lane counts mismatch: ' + file
  );
  assertStableEqual(
    capture.writerSequenceRanges,
    writerSequenceRanges(replay.records),
    'capture writer sequence ranges mismatch: ' + file
  );

  const expectedSemantics = {
    canonicalEvidenceReferencedById: true,
    recordsDuplicatedIntoCapture: false,
    wallClockRole: 'WINDOW_SELECTION_ONLY_NOT_CAUSAL_ORDER',
    bufferWindowCompleteness:
      replay.truncated
        ? 'PARTIAL_BUFFER_WINDOW'
        : 'FULL_BUFFER_WINDOW',
    selectedEvidencePresence:
      replay.records.length > 0 ? 'PRESENT' : 'NO_MATCHING_ROWS',
    selectedEvidenceContinuityClaimed: false,
  };
  assertStableEqual(
    capture.semantics,
    expectedSemantics,
    'capture semantics mismatch: ' + file
  );

  return replay;
}

function assertCaptureIdentity(actual, expected, file) {
  if (actual?.debugSessionId !== expected.debugSessionId ||
      actual?.runId !== expected.runId || actual?.processEpoch !== expected.processEpoch ||
      (actual?.runSnapshotId ?? null) !== (expected.runSnapshotId ?? null)) {
    throw new Error('capture manifest identity mismatch: ' + file);
  }
}

function assertCaptureFilename(capture, file, prefix) {
  if (typeof capture.captureId !== 'string' ||
      !/^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/.test(capture.captureId) ||
      path.basename(file) !== prefix + capture.captureId + '.json') {
    throw new Error('capture manifest filename/id mismatch: ' + file);
  }
}

function sameExperiment(left, right) {
  const a = { ...left }; const b = { ...right };
  delete a.arenaRevision; delete b.arenaRevision;
  return stableJson(a) === stableJson(b);
}

async function verifyVisualImages(runDir, manifest, artifacts) {
  for (const frame of manifest.frames) {
    // WRITE_UNKNOWN frames deliberately have no durable image claim.
    if (manifest.result.frames[frame.frameIndex].status !== 'PRESENT') continue;
    const bytes = await readRawVisualImage(runDir, frame);
    const file = path.join(runDir, frame.imagePath);
    const artifact = { path: file, size: bytes.length,
      sha256: 'sha256:' + createHash('sha256').update(bytes).digest('hex') };
    const previous = artifacts.find(item => item.path === file);
    if (previous) assertStableEqual(previous, artifact, 'capture image changed during finalization: ' + file);
    else artifacts.push(artifact);
  }
}

function assertVisualObservationSource(source, manifest, file) {
  if (source.arenaEpoch !== manifest.identity.arenaEpoch || source.scope?.kind !== 'EXPERIMENT' ||
      source.scope.experimentId !== manifest.identity.experimentId || source.epistemicStatus !== 'OBSERVED' ||
      source.completeness?.complete !== true) {
    throw new Error('visual observation source identity or completeness mismatch: ' + file);
  }
}

async function summarizeVisualCapture(capture, file, runDir, identity, observations, artifacts) {
  assertCaptureIdentity(capture.identity, identity, file);
  assertCaptureFilename(capture, file, 'visual-');
  const manifest = validateVisualManifest(capture);
  const sources = observations.filter(row => {
    if (row.payload?.kind !== manifest.kind || row.payload.captureId !== manifest.captureId) return false;
    return stableJson(validateVisualManifest(row.payload)) === stableJson(manifest);
  });
  if (!sources.length) throw new Error('visual canonical manifest binding missing: ' + file);
  for (const source of sources) {
    assertCaptureIdentity(source, identity, file);
    assertVisualObservationSource(source, manifest, file);
  }
  await verifyVisualImages(runDir, manifest, artifacts);
  return { status: manifest.result.status, restoration: manifest.result.restoration,
    sourceObservationIds: sources.map(row => row.observationId),
    canonicalManifestSha256: sha256Text(stableJson(manifest)),
    viewCounts: Object.fromEntries(['PRESENT', 'WRITE_UNKNOWN', 'MISSING'].map(status =>
      [status, manifest.result.frames.filter(frame => frame.status === status).length])),
    visualVerdict: manifest.visualVerdict, behaviorVerdict: manifest.behaviorVerdict };
}

async function summarizeTriggerCapture(capture, file, runDir, identity, observations, artifacts) {
  exactKeys(capture, ['schemaVersion', 'kind', 'captureId', 'identity', 'triggerKind', 'triggerObservationId',
    'triggerAt', 'sameFrame', 'slots', 'outcome', 'config', 'ringCoverage', 'canonicalCut', 'semantics'], 'TRIGGER_MANIFEST');
  if (capture.schemaVersion !== 1) throw new Error('capture manifest schema mismatch: ' + file);
  assertCaptureIdentity(capture.identity, identity, file);
  assertCaptureFilename(capture, file, 'trigger-'); validateVisualIdentity(capture.identity);
  const { prefix, proof } = prefixProof(observations, capture.canonicalCut?.count);
  assertStableEqual(capture.canonicalCut, proof, 'trigger canonical prefix proof mismatch: ' + file);
  const ring = new ObservationRingBuffer({ maxRecords: capture.ringCoverage?.maxRecords,
    maxAgeMs: capture.ringCoverage?.maxAgeMs });
  for (const row of prefix) ring.push(row);
  assertStableEqual(capture.ringCoverage, ring.coverage(), 'trigger ring coverage replay mismatch: ' + file);
  const byId = new Map(prefix.map(row => [row.observationId, row]));
  // Construction validates the producer's exact config without triggering, polling, or dispatching.
  const validator = new TriggerCaptureController({ ...identity, store: { ring,
    observationById: new Map(prefix.map(row => [row.observationId, stableJson(row)])) } }, capture.config);
  const config = validator.config;
  assertStableEqual(config.identity, capture.identity, 'trigger config identity mismatch: ' + file);
  if (capture.sameFrame !== false || !config.triggerKinds.includes(capture.triggerKind) ||
      !['COMPLETE', 'PARTIAL'].includes(capture.outcome)) throw new Error('trigger manifest identity mismatch: ' + file);
  identifier(capture.triggerObservationId);
  const trigger = byId.get(capture.triggerObservationId);
  if (!trigger || trigger.observedAt !== capture.triggerAt ||
      stableJson(validateVisualIdentity(trigger.payload.identity)) !== stableJson(capture.identity)) {
    throw new Error('trigger source mismatch or missing: ' + file);
  }
  assertCaptureIdentity(trigger, identity, file);
  if (capture.triggerKind !== 'AI_EXPLICIT' && trigger.payload.triggerKind !== capture.triggerKind) {
    throw new Error('trigger kind mismatch: ' + file);
  }
  if (!Array.isArray(capture.slots) || capture.slots.length !== config.offsetsMs.length) {
    throw new Error('trigger slot count mismatch: ' + file);
  }
  const slotCounts = { PRESENT: 0, PRESENT_PARTIAL: 0, MISSING: 0, OUTCOME_UNKNOWN: 0 };
  const sourceIds = new Set([capture.triggerObservationId]);
  let unknown = false;
  for (const [i, slot] of capture.slots.entries()) {
    exactKeys(slot, ['offsetMs', 'at', 'status', 'reason', 'sourceObservationId', 'captureId', 'imageHashes', 'captureStatus', ...(Object.hasOwn(slot, 'dispatch') ? ['dispatch'] : []),
      ...(Object.hasOwn(slot, 'match') ? ['match'] : [])], 'TRIGGER_SLOT');
    if (slot.offsetMs !== config.offsetsMs[i] || slot.at !== Date.parse(capture.triggerAt) + slot.offsetMs ||
        !Object.hasOwn(slotCounts, slot.status)) throw new Error('trigger slot identity mismatch: ' + file);
    slotCounts[slot.status]++;
    if (slot.dispatch != null) {
      exactKeys(slot.dispatch, ['captureId', 'requestedAt', 'deadline'], 'TRIGGER_DISPATCH');
      identifier(slot.dispatch.captureId);
      if (slot.offsetMs < 0 || slot.dispatch.requestedAt !== slot.at ||
          slot.dispatch.deadline !== Date.parse(capture.triggerAt) + config.timeoutMs) {
        throw new Error('trigger dispatch window mismatch: ' + file);
      }
    }
    if (slot.status === 'PRESENT' || slot.status === 'PRESENT_PARTIAL') {
      identifier(slot.sourceObservationId);
      const source = byId.get(slot.sourceObservationId);
      if (!source) throw new Error('trigger frame source missing: ' + file);
      assertCaptureIdentity(source, identity, file);
      const observedAt = Date.parse(source.observedAt);
      if (!Number.isFinite(observedAt) || (slot.offsetMs < 0 && observedAt >= Date.parse(capture.triggerAt)) || (slot.dispatch
        ? slot.captureId !== slot.dispatch.captureId || observedAt < slot.at || observedAt > slot.dispatch.deadline
        : Math.abs(observedAt - slot.at) > config.toleranceMs)) {
        throw new Error('trigger frame time outside window: ' + file);
      }
      if (slot.match != null || slot.dispatch != null) {
        exactKeys(slot.match, ['basis', 'observedAt', 'offsetFromRequestedMs'], 'TRIGGER_MATCH');
        if (slot.match.observedAt !== source.observedAt || slot.match.offsetFromRequestedMs !== observedAt - slot.at ||
            slot.match.basis !== (slot.dispatch ? 'DISPATCHED_CAPTURE_ID_WITHIN_REQUEST_WINDOW' : 'RETAINED_MANIFEST_WITHIN_TOLERANCE')) {
          throw new Error('trigger actual time or match basis mismatch: ' + file);
        }
      }
      const visual = validateVisualManifest(source.payload);
      assertVisualObservationSource(source, visual, file);
      if (!sameExperiment(visual.identity, capture.identity) || visual.captureId !== slot.captureId ||
          visual.result.status !== slot.captureStatus || slot.reason !== null ||
          slot.status !== (visual.result.status === 'COMPLETE' ? 'PRESENT' : 'PRESENT_PARTIAL')) {
        throw new Error('trigger frame binding/status mismatch: ' + file);
      }
      assertStableEqual(slot.imageHashes, visual.result.frames.filter(frame => frame.status === 'PRESENT')
        .map(frame => frame.imageHash), 'trigger frame binding mismatch: ' + file);
      await verifyVisualImages(runDir, visual, artifacts);
      sourceIds.add(slot.sourceObservationId);
      if (visual.result.status === 'UNKNOWN') unknown = true;
    } else {
      if (slot.sourceObservationId !== null || slot.captureId !== null || slot.captureStatus !== null || slot.match != null ||
          !Array.isArray(slot.imageHashes) || slot.imageHashes.length !== 0 || typeof slot.reason !== 'string' || !slot.reason) {
        throw new Error('missing trigger frame has evidence: ' + file);
      }
      if (slot.status === 'OUTCOME_UNKNOWN') unknown = true;
    }
  }
  const outcome = capture.slots.every(slot => slot.status === 'PRESENT') ? 'COMPLETE' : 'PARTIAL';
  if (capture.outcome !== outcome) throw new Error('false trigger completion: ' + file);
  assertStableEqual(capture.semantics, { windowClock: 'WALL_CLOCK_CORRELATION_NOT_CAUSAL_ORDER',
    captureBudgetUnit: 'FOUR_FRAME_CAPTURE_SETS', automaticRetry: false, rawEvidenceDuplicated: false,
    visualVerdict: 'NOT_RUN', behaviorVerdict: 'NOT_RUN' }, 'false trigger semantics: ' + file);
  return { status: unknown ? 'UNKNOWN' : outcome, outcome, slotCounts,
    sourceObservationIds: [...sourceIds], canonicalCut: proof,
    visualVerdict: 'NOT_RUN', behaviorVerdict: 'NOT_RUN' };
}

async function captureSummary(runDir, identity, observations, artifacts) {
  const captureDir = path.join(runDir, 'evidence', 'captures');
  const records = [];
  const byKind = { pre_roll_capture: 0, cardinal4_capture_manifest: 0, trigger_visual_window: 0 };
  let entries;
  try {
    entries = await readdir(captureDir, { withFileTypes: true });
  } catch (error) {
    if (error?.code !== 'ENOENT') throw error;
    entries = [];
  }

  const observationIds = new Set(observations.map((row) => row.observationId));
  for (const entry of entries.sort((a, b) => a.name.localeCompare(b.name))) {
    if (!entry.isFile() || !entry.name.endsWith('.json')) continue;
    const file = path.join(captureDir, entry.name);
    const bytes = await readFile(file);
    let capture = JSON.parse(bytes.toString('utf8'));
    if (!Object.hasOwn(byKind, capture?.kind)) throw new Error('unsupported capture manifest kind: ' + file);
    const artifact = artifacts.find(item => item.path === file);
    if (!artifact || artifact.sha256 !== 'sha256:' + createHash('sha256').update(bytes).digest('hex')) {
      throw new Error('capture manifest changed during finalization: ' + file);
    }
    let summary;
    if (capture.kind === 'pre_roll_capture') {
      assertCaptureIdentity(capture, identity, file);
      if (!Array.isArray(capture.observationIds)) {
        throw new Error('capture manifest observationIds missing: ' + file);
      }
      const missingObservationIds = capture.observationIds.filter(
        (id) => !observationIds.has(id)
      );
      if (missingObservationIds.length) {
        throw new Error(
          'capture manifest references missing canonical observations: ' +
          file + ' ids=' + missingObservationIds.join(',')
        );
      }
      const replay = replayAndValidateCapture(capture, file, observations);
      summary = { status: replay.truncated ? 'PARTIAL' : 'COMPLETE' };
    } else {
      capture = decodeJson(bytes, capture.kind === 'cardinal4_capture_manifest' ? 64 * 1024 : 128 * 1024);
      summary = await (capture.kind === 'cardinal4_capture_manifest' ? summarizeVisualCapture : summarizeTriggerCapture)(
        capture, file, runDir, identity, observations, artifacts);
    }
    byKind[capture.kind]++;
    records.push({ kind: capture.kind, captureId: capture.captureId, ...summary,
      path: file, sha256: artifact.sha256 });
  }
  const partialCaptureIds = records.filter(row => row.status !== 'COMPLETE').map(row => row.captureId);
  const unknownCaptureIds = records.filter(row => row.status === 'UNKNOWN').map(row => row.captureId);
  return {
    count: records.length,
    partialCount: partialCaptureIds.length,
    partialCaptureIds,
    unknownCount: unknownCaptureIds.length,
    unknownCaptureIds,
    coverageStatus: unknownCaptureIds.length ? 'UNKNOWN' : partialCaptureIds.length ? 'PARTIAL' : records.length ? 'COMPLETE' : 'NONE',
    byKind,
    records,
  };
}

function lastSequences(observations) {
  const perLane = {};
  const perWriter = {};

  for (const row of observations) {
    perLane[row.lane] = Math.max(perLane[row.lane] ?? 0, row.writerSeq ?? 0);
    perWriter[row.writerId] = Math.max(
      perWriter[row.writerId] ?? 0,
      row.writerSeq ?? 0
    );
  }

  return { perLane, perWriter };
}

export async function finalizeEvidenceRun(current, options = {}) {
  if (!current?.runDir ||
      !current?.debugSessionId ||
      !current?.runId ||
      !Number.isInteger(current?.processEpoch)) {
    throw new Error(
      'current run identity is incomplete for evidence finalization'
    );
  }

  if (current.live !== false && options.allowLive !== true) {
    throw new Error('cannot finalize evidence while debug runtime is live or unverified');
  }

  const finalFile = path.join(
    current.runDir,
    'evidence',
    'finalization.json'
  );
  if (await exists(finalFile)) {
    const existing = JSON.parse(await readFile(finalFile, 'utf8'));
    if (existing.debugSessionId !== current.debugSessionId ||
        existing.runId !== current.runId ||
        existing.processEpoch !== current.processEpoch ||
        (existing.runSnapshotId ?? null) !== (current.runSnapshotId ?? null)) {
      throw new Error(
        'existing evidence finalization identity mismatch: ' + finalFile
      );
    }
    return {
      file: finalFile,
      manifest: existing,
      alreadyFinalized: true,
    };
  }

  const runtime = evidenceRuntimeFromCurrent(current);
  await runtime.init();
  const ingest = await runtime.ingestAvailable();
  const status = await runtime.broker.status({ compact: true });
  const observations = await runtime.store.readObservations();
  const findings = await runtime.store.readFindings();
  const health = status.health;
  const sequences = lastSequences(observations);
  const artifacts = await collectArtifacts(current.runDir);
  const captures = await captureSummary(current.runDir, {
    debugSessionId: current.debugSessionId,
    runId: current.runId,
    runSnapshotId: current.runSnapshotId ?? null,
    processEpoch: current.processEpoch,
  }, observations, artifacts);
  await sealDerivedVisualArtifacts(current.runDir, artifacts);
  await sealMobPovArtifacts(current.runDir, observations, artifacts);
  artifacts.sort((a, b) => a.path.localeCompare(b.path));

  const laneDropped = health.reduce((sum, row) => sum + row.dropped, 0);
  const totalErrors = health.reduce((sum, row) => sum + row.errors, 0);
  const trailingPartialFiles = ingest.trailingPartialFiles ?? 0;
  const cleanShutdown = options.cleanShutdown === true;
  const shutdownAck = current.evidenceShutdown?.ack ?? null;
  const ackDropped =
    Number.isInteger(shutdownAck?.writerDroppedTotal)
      ? shutdownAck.writerDroppedTotal
      : 0;
  const ackRemainingQueue =
    Number.isInteger(shutdownAck?.remainingQueue)
      ? shutdownAck.remainingQueue
      : 0;
  const totalDropped = Math.max(laneDropped, ackDropped);
  const complete =
    cleanShutdown &&
    trailingPartialFiles === 0 &&
    totalDropped === 0 &&
    totalErrors === 0 &&
    ackRemainingQueue === 0;

  const manifest = {
    schemaVersion: 1,
    kind: 'evidence_finalization',
    status: complete ? 'EVIDENCE_COMPLETE' : 'EVIDENCE_PARTIAL',
    finalizedAt: nowIso(),
    debugSessionId: current.debugSessionId,
    runId: current.runId,
    processEpoch: current.processEpoch,
    runSnapshotId: current.runSnapshotId ?? null,
    runSnapshotHash: current.runSnapshotHash ?? null,
    runtimeStatusAtFinalization: current.status ?? null,
    shutdown: {
      clean: cleanShutdown,
      mode: options.shutdownMode ?? 'UNKNOWN',
      stoppedPids: Array.isArray(current.stoppedPids)
        ? [...current.stoppedPids]
        : [],
    },
    counts: {
      observations: observations.length,
      findings: findings.length,
      lanes: health.length,
      dropped: totalDropped,
      laneDropped,
      shutdownAckDropped: ackDropped,
      shutdownAckRemainingQueue: ackRemainingQueue,
      errors: totalErrors,
      trailingPartialFiles,
      captureManifests: captures.count,
      partialCaptures: captures.partialCount,
    },
    lastSequence: sequences,
    ingest: {
      files: ingest.files,
      parsed: ingest.parsed,
      written: ingest.written,
      suppressed: ingest.suppressed,
      trailingPartialFiles,
      bytesRead: ingest.bytesRead,
      bytesConsumed: ingest.bytesConsumed,
    },
    health,
    captures,
    artifacts,
    limitations: [
      ...(!cleanShutdown
        ? ['Probe writer flush/close was not acknowledged before process termination.']
        : []),
      ...(trailingPartialFiles > 0
        ? ['At least one raw JSONL file ended with an incomplete row.']
        : []),
      ...(totalDropped > 0
        ? ['Evidence loss was detected from producer sequence gaps, lane drop counters, or the Probe shutdown ACK.']
        : []),
      ...(ackRemainingQueue > 0
        ? ['The Probe shutdown ACK reported queued evidence remaining at seal time.']
        : []),
      ...(totalErrors > 0
        ? ['Evidence writer/store errors were recorded.']
        : []),
      ...(captures.records.some(row => row.kind === 'pre_roll_capture' && row.status === 'PARTIAL')
        ? ['At least one persisted pre-roll capture could not cover its full requested window.']
        : []),
      ...(captures.records.some(row => row.kind !== 'pre_roll_capture' && row.status !== 'COMPLETE')
        ? ['At least one persisted visual capture or trigger window has incomplete coverage; run evidence status does not imply complete captures.']
        : []),
      ...(captures.unknownCount > 0
        ? ['At least one visual restoration or trigger capture outcome remains unknown.']
        : []),
    ],
  };

  await mkdir(path.dirname(finalFile), { recursive: true });
  await writeFile(
    finalFile,
    JSON.stringify(manifest, null, 2) + '\n',
    { encoding: 'utf8', flag: 'wx' }
  );

  return {
    file: finalFile,
    manifest,
  };
}
