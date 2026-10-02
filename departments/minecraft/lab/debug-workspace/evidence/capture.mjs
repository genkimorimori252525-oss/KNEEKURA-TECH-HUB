import { mkdir, stat, writeFile } from 'node:fs/promises';
import path from 'node:path';

const CAPTURE_ID_RE = /^[A-Za-z0-9._-]{1,160}$/;

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
    const key = record.writerId;
    const current = out[key] ?? {
      first: record.writerSeq,
      last: record.writerSeq,
      count: 0,
    };
    current.first = Math.min(current.first, record.writerSeq);
    current.last = Math.max(current.last, record.writerSeq);
    current.count += 1;
    out[key] = current;
  }
  return out;
}

async function assertRunNotFinalized(runDir) {
  const finalizationFile = path.join(
    runDir,
    'evidence',
    'finalization.json'
  );
  try {
    await stat(finalizationFile);
    throw new Error(
      'EVIDENCE_FINALIZED_READ_ONLY: ' + finalizationFile
    );
  } catch (error) {
    if (error?.code === 'ENOENT') return;
    throw error;
  }
}

export async function persistPreRollCapture(options) {
  const {
    runDir,
    debugSessionId,
    runId,
    runSnapshotId = null,
    processEpoch,
    captureId,
    capture,
    canonicalCut,
    ringConfig,
    filter = null,
  } = options;

  if (!runDir || !debugSessionId || !runId ||
      !Number.isInteger(processEpoch)) {
    throw new TypeError(
      'pre-roll capture requires runDir/debugSessionId/runId/processEpoch'
    );
  }
  if (typeof captureId !== 'string' || !CAPTURE_ID_RE.test(captureId)) {
    throw new TypeError('invalid captureId');
  }
  if (!capture || typeof capture !== 'object' ||
      !Array.isArray(capture.records)) {
    throw new TypeError('invalid ring-buffer capture result');
  }
  if (!canonicalCut || !Number.isInteger(canonicalCut.count) ||
      canonicalCut.count < 0 ||
      typeof canonicalCut.observationIdsSha256 !== 'string' ||
      typeof canonicalCut.canonicalRecordsSha256 !== 'string' ||
      !(
        canonicalCut.lastObservationId == null ||
        typeof canonicalCut.lastObservationId === 'string'
      )) {
    throw new TypeError('invalid canonicalCut');
  }
  if (!ringConfig ||
      !Number.isInteger(ringConfig.maxRecords) ||
      ringConfig.maxRecords < 1 ||
      !Number.isInteger(ringConfig.maxAgeMs) ||
      ringConfig.maxAgeMs < 1) {
    throw new TypeError('invalid ringConfig');
  }

  await assertRunNotFinalized(runDir);

  const records = capture.records;
  const manifest = {
    schemaVersion: 1,
    kind: 'pre_roll_capture',
    captureId,
    createdAt: new Date().toISOString(),
    debugSessionId,
    runId,
    runSnapshotId,
    processEpoch,
    canonicalCut,
    ringConfig,
    triggerAt: capture.triggerAt,
    requestedPreRollMs: capture.requestedPreRollMs,
    coverage: {
      requestedStartAt: capture.requestedStartAt,
      availablePreRollMs: capture.availablePreRollMs,
      truncated: capture.truncated,
      totalBufferedRecords: capture.totalBufferedRecords,
      selectedRecords: records.length,
      droppedRecords: capture.droppedRecords,
      droppedInsideRequestedWindow: capture.droppedInsideRequestedWindow,
      bufferStartedTooLate: capture.bufferStartedTooLate,
      oldestSelectedAt: capture.oldestSelectedAt,
      newestSelectedAt: capture.newestSelectedAt,
    },
    filter,
    observationIds: records.map((record) => record.observationId),
    laneCounts: laneCounts(records),
    writerSequenceRanges: writerSequenceRanges(records),
    semantics: {
      canonicalEvidenceReferencedById: true,
      recordsDuplicatedIntoCapture: false,
      wallClockRole: 'WINDOW_SELECTION_ONLY_NOT_CAUSAL_ORDER',
      bufferWindowCompleteness:
        capture.truncated
          ? 'PARTIAL_BUFFER_WINDOW'
          : 'FULL_BUFFER_WINDOW',
      selectedEvidencePresence:
        records.length > 0 ? 'PRESENT' : 'NO_MATCHING_ROWS',
      selectedEvidenceContinuityClaimed: false,
    },
  };

  const dir = path.join(runDir, 'evidence', 'captures');
  const file = path.join(dir, captureId + '.json');
  await mkdir(dir, { recursive: true });
  await writeFile(
    file,
    JSON.stringify(manifest, null, 2) + '\n',
    { encoding: 'utf8', flag: 'wx' }
  );

  return { file, manifest };
}
