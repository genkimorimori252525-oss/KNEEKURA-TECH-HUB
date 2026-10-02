import { mkdir, open, opendir, rm, lstat, realpath } from 'node:fs/promises';
import path from 'node:path';
import { validateActionEnvelope } from './arena-contract.mjs';
import { decodeJson, sha256, stableJson, identifier, exactKeys, hashId, integer } from './json.mjs';
import { readRegisteredFile } from './materials.mjs';

const NEXT = {
  REQUESTED: ['ACCEPTED', 'NOT_RUN', 'FAILED'],
  ACCEPTED: ['APPLIED', 'FAILED', 'OUTCOME_UNKNOWN', 'PARTIAL_APPLY'],
  APPLIED: ['VERIFIED', 'PARTIAL_APPLY', 'OUTCOME_UNKNOWN', 'FAILED'],
};
const TERMINAL = new Set(['VERIFIED', 'FAILED', 'NOT_RUN', 'PARTIAL_APPLY', 'OUTCOME_UNKNOWN']);

async function baseDirectory(runDir, create = false) {
  if (!path.isAbsolute(runDir) || await realpath(runDir) !== path.resolve(runDir)) {
    throw new TypeError('UNSAFE_RUN_DIR');
  }
  let directory = runDir;
  for (const segment of ['control', 'actions']) {
    directory = path.join(directory, segment);
    if (create) await mkdir(directory, { recursive: true });
    if ((await lstat(directory)).isSymbolicLink()) throw new TypeError('SYMLINK_REJECTED');
  }
  return directory;
}

async function directoryFor(runDir, key, create = false) {
  return path.join(await baseDirectory(runDir, create), sha256(identifier(key)));
}

async function writeExclusive(file, value, raw = false) {
  const handle = await open(file, 'wx');
  try {
    await handle.writeFile(raw ? value : JSON.stringify(value) + '\n');
    await handle.sync();
  } finally {
    await handle.close();
  }
}

function identityMatches(action, identity) {
  for (const key of ['debugSessionId', 'runId', 'runSnapshotId', 'processEpoch', 'experimentId']) {
    if (action[key] !== identity[key]) throw new Error('ACTION_IDENTITY_MISMATCH');
  }
}

async function readState(directory, identity, expectedKey) {
  const request = decodeJson((await readRegisteredFile({
    root: directory, relativePath: 'request.json', maxBytes: 128 * 1024,
  })).bytes);
  exactKeys(request, ['schemaVersion', 'payloadHash', 'action'], 'JOURNAL_REQUEST');
  integer(request.schemaVersion, 1, 1); hashId(request.payloadHash);
  identityMatches(request.action, identity);
  if (request.action.idempotencyKey !== expectedKey) throw new Error('ACTION_IDENTITY_MISMATCH');
  if (sha256(stableJson(request.action)) !== request.payloadHash) throw new Error('ACTION_REQUEST_INTEGRITY');
  const names = []; let entries = 0;
  for await (const entry of await opendir(directory)) {
    if (++entries > 32) throw new Error('JOURNAL_ENTRY_LIMIT');
    if (entry.name.startsWith('receipt-')) {
      if (!/^receipt-\d{6}\.json$/.test(entry.name)) throw new Error('JOURNAL_GAP');
      names.push(entry.name);
    }
  }
  names.sort();
  if (names.length === 0 || names.length > 5) throw new Error('JOURNAL_INCOMPLETE');
  let last = null;
  let previousHash = request.payloadHash;
  for (let sequence = 0; sequence < names.length; sequence++) {
    if (names[sequence] !== `receipt-${String(sequence).padStart(6, '0')}.json`) {
      throw new Error('JOURNAL_GAP');
    }
    const receipt = decodeJson((await readRegisteredFile({
      root: directory, relativePath: names[sequence], maxBytes: 64 * 1024,
    })).bytes);
    exactKeys(receipt, ['receiptHash', 'sequence', 'previousHash', 'payloadHash', 'status', 'evidenceHashes'], 'JOURNAL_RECEIPT');
    integer(receipt.sequence, 0, 4);
    for (const key of ['receiptHash', 'previousHash', 'payloadHash']) hashId(receipt[key]);
    if (!Array.isArray(receipt.evidenceHashes) || receipt.evidenceHashes.length > 32) throw new TypeError('INVALID_EVIDENCE');
    receipt.evidenceHashes.forEach(hashId);
    if (['APPLIED', 'VERIFIED', 'PARTIAL_APPLY'].includes(receipt.status) && receipt.evidenceHashes.length === 0) throw new TypeError('OUTCOME_EVIDENCE_REQUIRED');
    const { receiptHash, ...body } = receipt;
    if (receiptHash !== sha256(stableJson(body)) || body.sequence !== sequence ||
        body.previousHash !== previousHash || body.payloadHash !== request.payloadHash) {
      throw new Error('JOURNAL_INTEGRITY');
    }
    if (sequence === 0 ? body.status !== 'REQUESTED' : !NEXT[last.status]?.includes(body.status)) {
      throw new Error('JOURNAL_TRANSITION');
    }
    last = body;
    previousHash = receiptHash;
  }
  return { request, last, count: names.length, previousHash };
}

function summary(directory, state, extra = {}) {
  const rawStatus = state.last?.status ?? 'OUTCOME_UNKNOWN';
  return {
    directory,
    status: rawStatus === 'ACCEPTED' || rawStatus === 'APPLIED' ? 'OUTCOME_UNKNOWN' : rawStatus,
    recordedStatus: rawStatus,
    dispatchAllowed: false,
    runtimeAttestation: 'NOT_ESTABLISHED',
    scope: 'CONTRACT_ONLY',
    action: state.request.action,
    evidenceHashes: state.last?.evidenceHashes ?? [],
    ...extra,
  };
}

async function appendReceipt(directory, state, outcome) {
  const body = {
    sequence: state.count,
    payloadHash: state.request.payloadHash,
    previousHash: state.previousHash,
    status: outcome.status,
    evidenceHashes: [...outcome.evidenceHashes],
  };
  await writeExclusive(
    path.join(directory, `receipt-${String(state.count).padStart(6, '0')}.json`),
    { ...body, receiptHash: sha256(stableJson(body)) },
  );
}

export async function beginAction({ runDir, arena, identity, action }) {
  validateActionEnvelope(action, arena, identity);
  const directory = await directoryFor(runDir, action.idempotencyKey, true);
  const payloadHash = sha256(stableJson(action));
  try {
    await mkdir(directory);
  } catch (error) {
    if (error.code !== 'EEXIST') throw error;
    const state = await readState(directory, identity, action.idempotencyKey);
    if (state.request.payloadHash !== payloadHash) throw new Error('IDEMPOTENCY_CONFLICT');
    return summary(directory, state, { alreadyRecorded: true });
  }
  const request = { schemaVersion: 1, payloadHash, action: structuredClone(action) };
  await writeExclusive(path.join(directory, 'canonical-action.json'), stableJson(action), true);
  await writeExclusive(path.join(directory, 'request.json'), request);
  await appendReceipt(directory, { request, count: 0, previousHash: payloadHash }, {
    status: 'REQUESTED', evidenceHashes: [],
  });
  return summary(directory, await readState(directory, identity, action.idempotencyKey), { alreadyRecorded: false });
}

export async function readActionOutcome({ runDir, identity, idempotencyKey }) {
  let directory;
  try {
    directory = await directoryFor(runDir, idempotencyKey);
    await lstat(directory);
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
    return { status: 'NEVER_SEEN', dispatchAllowed: false, scope: 'CONTRACT_ONLY', runtimeAttestation: 'NOT_ESTABLISHED' };
  }
  try {
    return summary(directory, await readState(directory, identity, idempotencyKey));
  } catch (error) {
    if (/IDENTITY|SYMLINK|UNSAFE/.test(error.message)) throw error;
    return {
      directory, status: 'OUTCOME_UNKNOWN', dispatchAllowed: false,
      runtimeAttestation: 'NOT_ESTABLISHED', scope: 'CONTRACT_ONLY', error: error.message,
    };
  }
}

export async function recordActionOutcome({ runDir, identity, idempotencyKey, outcome }) {
  exactKeys(outcome, ['status', 'evidenceHashes'], 'OUTCOME');
  if (!Array.isArray(outcome.evidenceHashes) || outcome.evidenceHashes.length > 32) {
    throw new TypeError('INVALID_EVIDENCE');
  }
  outcome.evidenceHashes.forEach(hashId);
  if (['APPLIED', 'VERIFIED', 'PARTIAL_APPLY'].includes(outcome.status) && outcome.evidenceHashes.length === 0) {
    throw new TypeError('OUTCOME_EVIDENCE_REQUIRED');
  }
  const directory = await directoryFor(runDir, idempotencyKey);
  const lock = path.join(directory, '.writer-lock');
  try {
    await mkdir(lock);
  } catch (error) {
    if (error.code === 'EEXIST') throw new Error('ACTION_WRITE_IN_PROGRESS');
    throw error;
  }
  try {
    const state = await readState(directory, identity, idempotencyKey);
    if (!state.last || TERMINAL.has(state.last.status) || !NEXT[state.last.status]?.includes(outcome.status)) {
      throw new Error('INVALID_ACTION_TRANSITION');
    }
    await appendReceipt(directory, state, outcome);
    return summary(directory, await readState(directory, identity, idempotencyKey));
  } finally {
    await rm(lock, { recursive: true });
  }
}
