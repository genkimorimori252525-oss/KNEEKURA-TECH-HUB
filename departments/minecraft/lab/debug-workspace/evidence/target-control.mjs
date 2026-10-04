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

export function normalizeDecisionBurst(value) {
  if(value==null)return null;
  const limits={ticks:200,maxEvents:256,maxBytes:524288,maxNodes:64};
  if(typeof value!=='object'||Array.isArray(value)||Object.keys(value).some(k=>![...Object.keys(limits),'channels'].includes(k))||
      Object.entries(limits).some(([key,max])=>!Number.isSafeInteger(value[key])||value[key]<1||value[key]>max)||
      !Array.isArray(value.channels)||value.channels.length<1||value.channels.length>14||
      new Set(value.channels).size!==value.channels.length||value.channels.some(c=>!['goal','brain','path','control','malus','sensor','mod','projectile','neighbors','effective_malus','frontier','path_nodes','path_g','path_distance'].includes(c))){
    throw new TypeError('Invalid decisionBurst: require finite ticks/events/bytes/nodes and unique known channels');
  }
  return {...Object.fromEntries(Object.keys(limits).map(key=>[key,value[key]])),channels:[...value.channels]};
}

export function normalizeDecisionTerrain(value) {
  if(value==null)return null;
  if(typeof value!=='object'||Array.isArray(value)||Object.keys(value).sort().join(',')!=='maxCells,maxMillis,radius'||
      !Number.isSafeInteger(value.radius)||value.radius<0||value.radius>3||
      !Number.isSafeInteger(value.maxCells)||value.maxCells<1||value.maxCells>49||
      !Number.isSafeInteger(value.maxMillis)||value.maxMillis<1||value.maxMillis>50) {
    throw new TypeError('Invalid decisionTerrain: require radius 0..3, maxCells 1..49 and maxMillis 1..50');
  }
  return {radius:value.radius,maxCells:value.maxCells,maxMillis:value.maxMillis};
}

export async function setTargetControl(current, targetUuid, { decisionSnapshot = false,decisionBurst = null,decisionTerrain = null } = {}) {
  assertCurrentIdentity(current);
  const normalized = normalizeTargetUuid(targetUuid);
  if (typeof decisionSnapshot !== 'boolean') throw new TypeError('decisionSnapshot must be boolean');
  if (decisionSnapshot && normalized === null) throw new TypeError('decisionSnapshot requires a target');
  const burst=normalizeDecisionBurst(decisionBurst);
  if(burst&&normalized===null)throw new TypeError('decisionBurst requires a target');
  if(burst&&current.decisionHooksEnabled!==true)throw new TypeError('DECISION_HOOKS_NOT_ENABLED');
  const terrain=normalizeDecisionTerrain(decisionTerrain);
  if(terrain&&normalized===null)throw new TypeError('decisionTerrain requires a target');
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
    decisionBurst:burst,
    decisionTerrain:terrain,
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
