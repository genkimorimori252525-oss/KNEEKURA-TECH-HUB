import { randomBytes } from 'node:crypto';
import {
  mkdir,
  readFile,
  rename,
  writeFile,
} from 'node:fs/promises';
import path from 'node:path';

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function nowIso() {
  return new Date().toISOString();
}

function targetFile(current) {
  if (!current?.runDir) {
    throw new Error('current debug state has no runDir');
  }
  return path.join(current.runDir, 'control', 'target.json');
}

function assertCurrentIdentity(current) {
  if (!current?.debugSessionId ||
      !current?.runId ||
      !current?.runSnapshotId ||
      !Number.isInteger(current?.processEpoch)) {
    throw new Error(
      'current debug state lacks debugSessionId/runId/runSnapshotId/processEpoch'
    );
  }
}

export function normalizeTargetUuid(value) {
  if (value == null) return null;
  const uuid = String(value).trim().toLowerCase();
  if (!UUID_RE.test(uuid)) {
    throw new TypeError('target must be a canonical UUID');
  }
  return uuid;
}

export async function readTargetControl(current) {
  assertCurrentIdentity(current);
  const file = targetFile(current);

  try {
    const value = JSON.parse(await readFile(file, 'utf8'));
    if (value.debugSessionId !== current.debugSessionId ||
        value.runId !== current.runId ||
        value.runSnapshotId !== current.runSnapshotId ||
        value.processEpoch !== current.processEpoch) {
      throw new Error('target control identity mismatch: ' + file);
    }
    return {
      file,
      exists: true,
      ...value,
    };
  } catch (error) {
    if (error?.code === 'ENOENT') {
      return {
        file,
        exists: false,
        v: 1,
        debugSessionId: current.debugSessionId,
        runId: current.runId,
        runSnapshotId: current.runSnapshotId,
        processEpoch: current.processEpoch,
        revision: 0,
        targetUuid: null,
        updatedAt: null,
      };
    }
    throw error;
  }
}

export async function setTargetControl(current, targetUuid, { decisionSnapshot = false } = {}) {
  assertCurrentIdentity(current);
  const normalized = normalizeTargetUuid(targetUuid);
  if (typeof decisionSnapshot !== 'boolean') throw new TypeError('decisionSnapshot must be boolean');
  if (decisionSnapshot && normalized === null) throw new TypeError('decisionSnapshot requires a target');
  const existing = await readTargetControl(current);
  const file = existing.file;
  const revision = (existing.revision ?? 0) + 1;

  const value = {
    v: 1,
    debugSessionId: current.debugSessionId,
    runId: current.runId,
    runSnapshotId: current.runSnapshotId,
    processEpoch: current.processEpoch,
    revision,
    targetUuid: normalized,
    decisionSnapshot,
    updatedAt: nowIso(),
  };

  await mkdir(path.dirname(file), { recursive: true });
  const temp = file + '.tmp-' + randomBytes(6).toString('hex');
  await writeFile(temp, JSON.stringify(value, null, 2) + '\n', 'utf8');
  await rename(temp, file);

  return {
    file,
    ...value,
  };
}

export async function clearTargetControl(current) {
  return await setTargetControl(current, null);
}
