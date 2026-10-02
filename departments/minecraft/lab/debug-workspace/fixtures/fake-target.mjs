#!/usr/bin/env node
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';

const readyFile = process.env.KNEEKURA_DEBUG_READY_FILE;
const buildMarkerFile = process.env.KNEEKURA_DEBUG_BUILD_MARKER;
const shutdownRequestFile = process.env.KNEEKURA_DEBUG_SHUTDOWN_REQUEST_FILE;
const shutdownAckFile = process.env.KNEEKURA_DEBUG_SHUTDOWN_ACK_FILE;
if (!readyFile) throw new Error('KNEEKURA_DEBUG_READY_FILE missing');
if (!buildMarkerFile) throw new Error('KNEEKURA_DEBUG_BUILD_MARKER missing');
if (!shutdownRequestFile) throw new Error('KNEEKURA_DEBUG_SHUTDOWN_REQUEST_FILE missing');
if (!shutdownAckFile) throw new Error('KNEEKURA_DEBUG_SHUTDOWN_ACK_FILE missing');

const now = new Date().toISOString();

const buildMarker = {
  debugSessionId: process.env.KNEEKURA_DEBUG_SESSION_ID,
  runId: process.env.KNEEKURA_DEBUG_RUN_ID,
  handshakeNonce: process.env.KNEEKURA_DEBUG_HANDSHAKE_NONCE,
  builtAt: now
};
await mkdir(path.dirname(buildMarkerFile), { recursive: true });
await writeFile(buildMarkerFile, JSON.stringify(buildMarker, null, 2) + '\n', 'utf8');
const manifest = {
  protocolVersion: 'KNEEKURA_DEBUG_READY_V1',
  debugSessionId: process.env.KNEEKURA_DEBUG_SESSION_ID,
  runId: process.env.KNEEKURA_DEBUG_RUN_ID,
  runSnapshotId: process.env.KNEEKURA_DEBUG_RUN_SNAPSHOT_ID,
  worldName: process.env.KNEEKURA_DEBUG_WORLD_NAME,
  processEpoch: Number(process.env.KNEEKURA_DEBUG_PROCESS_EPOCH),
  handshakeNonce: process.env.KNEEKURA_DEBUG_HANDSHAKE_NONCE,
  status: 'DEBUG_READY',
  pid: process.pid,
  gates: {
    probeHandshake: true,
    debugWorldReady: true,
    runtimeAttested: true
  },
  milestones: {
    jvmStartedAt: now,
    forgeInitializedAt: now,
    clientWorldAvailableAt: now,
    playerJoinedAt: now,
    probeReadyAt: now,
    debugWorldReadyAt: now
  },
  runtime: {
    kind: 'fake-debug-target',
    node: process.version,
    processCommandHint: path.basename(process.execPath)
  }
};

await mkdir(path.dirname(readyFile), { recursive: true });
await writeFile(readyFile, JSON.stringify(manifest, null, 2) + '\n', 'utf8');

let shutdownAcked = false;
setInterval(async () => {
  if (shutdownAcked) return;
  try {
    const request = JSON.parse(await readFile(shutdownRequestFile, 'utf8'));
    const identityMatches =
      request.v === 1 &&
      request.debugSessionId === process.env.KNEEKURA_DEBUG_SESSION_ID &&
      request.runId === process.env.KNEEKURA_DEBUG_RUN_ID &&
      request.runSnapshotId === process.env.KNEEKURA_DEBUG_RUN_SNAPSHOT_ID &&
      request.processEpoch === Number(process.env.KNEEKURA_DEBUG_PROCESS_EPOCH);
    if (!identityMatches) {
      throw new Error('fake shutdown request identity mismatch');
    }

    const ack = {
      v: 1,
      debugSessionId: request.debugSessionId,
      runId: request.runId,
      runSnapshotId: request.runSnapshotId,
      processEpoch: request.processEpoch,
      status: 'CLEAN_EVIDENCE_SHUTDOWN',
      clean: true,
      ackedAt: new Date().toISOString(),
      finalWriterSeq: 0,
      writerDroppedTotal: 0,
      remainingQueue: 0
    };
    await mkdir(path.dirname(shutdownAckFile), { recursive: true });
    await writeFile(
      shutdownAckFile,
      JSON.stringify(ack, null, 2) + '\n',
      { encoding: 'utf8', flag: 'wx' }
    );
    shutdownAcked = true;
  } catch (error) {
    if (error?.code !== 'ENOENT' && error?.code !== 'EEXIST') {
      process.stderr.write('[fake-target] ' + error.message + '\n');
    }
  }
}, 50);
