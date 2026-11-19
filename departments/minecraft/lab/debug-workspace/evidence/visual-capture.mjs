import { createHash } from 'node:crypto';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { decodeJson, exactKeys, hashId, identifier, integer, stableJson } from '../bridge/json.mjs';
import { decodePng } from '../../simlab/golden/png.mjs';
import { readRegisteredFile } from '../bridge/materials.mjs';

export const CARDINAL_VIEWS = Object.freeze(['north', 'east', 'south', 'west']);
const COMMON = ['schemaVersion', 'kind', 'captureId', 'rig', 'identity', 'subjects', 'controlledStateHash', 'sameFrame'];
const IDENTITY = ['debugSessionId', 'runId', 'runSnapshotId', 'processEpoch', 'experimentId',
  'generation', 'requestHash', 'arenaId', 'arenaEpoch', 'arenaRevision', 'baselineHash'];
const FRAME = ['view', 'frameIndex', 'renderFrame', 'clientTick', 'serverTick', 'serverGameTime',
  'partialTick', 'imageHash', 'imageBytes', 'artifactRole', 'captureStage', 'imagePath', 'captureDurationNanos', 'camera'];
const PERTURBATIONS = ['SERVER_TICK_HOLD', 'CLIENT_PAUSE', 'CAMERA_TAKEOVER', 'RENDER_ELIGIBILITY_CHANGED'];
function require(value, reason) { if (!value) throw new TypeError(reason); }
function list(value, max) { require(Array.isArray(value) && value.length <= max, 'BOUNDED_LIST_REQUIRED'); }
function finite(value, min, max) { require(typeof value === 'number' && Number.isFinite(value) && value >= min && value <= max, 'FINITE_NUMBER_REQUIRED'); }
function vector(value, size) {
  require(Array.isArray(value) && value.length === size, 'INVALID_VECTOR');
  value.forEach(n => finite(n, -30000000, 30000000));
}
function same(a, b) { return stableJson(a) === stableJson(b); }
export function validateVisualIdentity(value) {
  exactKeys(value, IDENTITY, 'VISUAL_IDENTITY');
  for (const key of ['debugSessionId', 'runId', 'runSnapshotId', 'experimentId', 'arenaId']) identifier(value[key]);
  integer(value.processEpoch, 1, 2147483647); integer(value.generation, 1, 1000000);
  for (const key of ['arenaEpoch', 'arenaRevision']) integer(value[key], 0, Number.MAX_SAFE_INTEGER);
  hashId(value.requestHash); hashId(value.baselineHash);
  return structuredClone(value);
}
function common(value) {
  integer(value.schemaVersion, 1, 1); identifier(value.captureId);
  require(/^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/.test(value.captureId), 'SAFE_CAPTURE_ID_REQUIRED');
  require(value.rig === 'cardinal-4-snapshot-v1' && value.sameFrame === false, 'SEQUENTIAL_CARDINAL_RIG_REQUIRED');
  validateVisualIdentity(value.identity);
  list(value.subjects, 16); require(value.subjects.length > 0, 'SUBJECTS_REQUIRED');
  value.subjects.forEach(uuid => require(typeof uuid === 'string' && /^[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}$/.test(uuid), 'EXACT_SUBJECT_UUID_REQUIRED'));
  require(new Set(value.subjects).size === value.subjects.length, 'DUPLICATE_SUBJECT');
  if (value.controlledStateHash != null) hashId(value.controlledStateHash);
}
export function validateRawFrame(input) {
  const f = structuredClone(input);
  exactKeys(f, [...COMMON, ...FRAME], 'RAW_FRAME'); common(f);
  require(f.kind === 'cardinal4_raw_frame' && CARDINAL_VIEWS.includes(f.view) &&
    f.frameIndex === CARDINAL_VIEWS.indexOf(f.view), 'INVALID_CARDINAL_FRAME');
  hashId(f.controlledStateHash); hashId(f.imageHash);
  for (const key of ['renderFrame', 'clientTick', 'serverTick', 'serverGameTime', 'captureDurationNanos']) integer(f[key], 0, Number.MAX_SAFE_INTEGER);
  integer(f.imageBytes, 1, 4 * 1024 * 1024); finite(f.partialTick, 0, 1);
  require(f.artifactRole === 'RAW_SCENE_RGB' && f.captureStage === 'AFTER_LEVEL_BEFORE_HAND_HUD' &&
    f.imagePath === `evidence/raw/visual/${f.imageHash}.png`, 'RAW_ARTIFACT_BINDING_MISMATCH');
  const c = f.camera;
  exactKeys(c, ['position', 'quaternion', 'yaw', 'pitch', 'fov', 'projection', 'projectionMatrix', 'viewMatrix', 'matrixConvention', 'viewport'], 'CAMERA');
  vector(c.position, 3); vector(c.quaternion, 4); vector(c.projectionMatrix, 16); vector(c.viewMatrix, 16);
  finite(c.yaw, -360, 360); finite(c.pitch, -90, 90); finite(c.fov, 29.999, 100.001);
  require(c.matrixConvention === 'JOML_COLUMN_MAJOR_CAMERA_RELATIVE', 'INVALID_MATRIX_CONVENTION');
  require(c.projection === 'PERSPECTIVE', 'UNSUPPORTED_PROJECTION');
  require(Array.isArray(c.viewport) && c.viewport.length === 2, 'INVALID_VIEWPORT');
  c.viewport.forEach(n => integer(n, 64, 2048));
  return f;
}
export function validateVisualManifest(input) {
  const m = structuredClone(input);
  // Missing nullable producer fields are normalized; status still explicitly names every missing view.
  m.controlledStateHash ??= null; m.structuredState ??= null;
  exactKeys(m, [...COMMON, 'result', 'frames', 'structuredState', 'renderFrameStart', 'renderFrameEnd',
    'clientTickStart', 'clientTickEnd', 'barrierDurationMs', 'restorationProof', 'runtimeAttestation', 'visualVerdict', 'behaviorVerdict'], 'VISUAL_MANIFEST');
  common(m); require(m.kind === 'cardinal4_capture_manifest', 'INVALID_VISUAL_MANIFEST');
  require(m.runtimeAttestation === 'OWNER_GATE_REQUIRED_NOT_INFERRED_FROM_CAPTURE' &&
    m.visualVerdict === 'NOT_RUN' && m.behaviorVerdict === 'INCONCLUSIVE_CAPTURE_PERTURBATION', 'FALSE_CAPTURE_VERDICT');
  for (const key of ['renderFrameStart', 'renderFrameEnd', 'clientTickStart', 'clientTickEnd', 'barrierDurationMs']) integer(m[key], 0, Number.MAX_SAFE_INTEGER);
  require(m.renderFrameEnd >= m.renderFrameStart && m.clientTickEnd >= m.clientTickStart, 'INVALID_CAPTURE_INTERVAL');
  const r = m.result;
  exactKeys(r, ['status', 'sameFrame', 'restoration', 'perturbations', 'invalidatedAssertions', 'frames', 'gaps'], 'CAPTURE_RESULT');
  require(['COMPLETE', 'PARTIAL', 'UNKNOWN'].includes(r.status) && r.sameFrame === false &&
    ['RESTORED', 'UNKNOWN'].includes(r.restoration) && same(r.perturbations, PERTURBATIONS), 'INVALID_CAPTURE_OUTCOME');
  list(r.invalidatedAssertions, 32); r.invalidatedAssertions.forEach(identifier);
  require(new Set(r.invalidatedAssertions).size === r.invalidatedAssertions.length, 'DUPLICATE_ASSERTION');
  list(r.gaps, 32); r.gaps.forEach(identifier); list(r.frames, 4);
  require(r.frames.length === 4, 'FOUR_EXPLICIT_VIEW_STATUSES_REQUIRED');
  list(m.frames, 4); m.frames = m.frames.map(validateRawFrame);
  let previous = -1;
  for (const f of m.frames) {
    require(same(f.identity, m.identity) && same(f.subjects, m.subjects) && f.captureId === m.captureId &&
      f.controlledStateHash === m.controlledStateHash && f.frameIndex === m.frames.indexOf(f) &&
      f.renderFrame > previous, 'FRAME_IDENTITY_OR_ORDER_MISMATCH');
    require(f.renderFrame >= m.renderFrameStart && f.renderFrame <= m.renderFrameEnd &&
      f.clientTick >= m.clientTickStart && f.clientTick <= m.clientTickEnd, 'FRAME_OUTSIDE_INTERVAL');
    if (m.frames.length) require(f.serverTick === m.frames[0].serverTick &&
      f.serverGameTime === m.frames[0].serverGameTime, 'CONTROLLED_STATE_DRIFT');
    previous = f.renderFrame;
  }
  r.frames.forEach((f, i) => {
    f.renderFrame ??= null; f.imageHash ??= null; f.observationHash ??= null;
    exactKeys(f, ['view', 'status', 'renderFrame', 'imageHash', 'observationHash'], 'VIEW_STATUS');
    require(f.view === CARDINAL_VIEWS[i] && ['PRESENT', 'WRITE_UNKNOWN', 'MISSING'].includes(f.status), 'INVALID_VIEW_STATUS');
    const raw = m.frames[i];
    if (f.status === 'MISSING') require(!raw && f.imageHash === null && f.observationHash === null && f.renderFrame === null, 'MISSING_FRAME_HAS_IMAGE');
    else {
      require(raw && raw.view === f.view && raw.imageHash === f.imageHash && raw.renderFrame === f.renderFrame, 'VIEW_ARTIFACT_MISMATCH');
      if (f.status === 'PRESENT') hashId(f.observationHash);
      else require(f.observationHash === null, 'UNKNOWN_WRITE_HAS_DURABLE_CLAIM');
    }
  });
  if (m.structuredState !== null) {
    const state = m.structuredState;
    exactKeys(state, ['dimension', 'gameTime', 'subjects', 'arenaBounds'], 'STRUCTURED_STATE');
    require(typeof state.dimension === 'string' && /^[a-z0-9_]+:[a-z0-9_./-]+$/.test(state.dimension), 'INVALID_DIMENSION');
    integer(state.gameTime, 0, Number.MAX_SAFE_INTEGER);
    exactKeys(state.arenaBounds, ['min', 'max'], 'ARENA_BOUNDS');
    vector(state.arenaBounds.min, 3); vector(state.arenaBounds.max, 3);
    state.arenaBounds.min.forEach((n, i) => {
      integer(n, -30000000, 30000000); integer(state.arenaBounds.max[i], -30000000, 30000000);
      require(state.arenaBounds.max[i] > n && state.arenaBounds.max[i] - n <= 64, 'INVALID_ARENA_BOUNDS');
    });
    require(state.arenaBounds.min[1] >= -64 && state.arenaBounds.max[1] <= 320, 'INVALID_ARENA_HEIGHT');
    list(state.subjects, 16);
    require(same(state.subjects.map(subject => subject.uuid), m.subjects), 'STRUCTURED_SUBJECT_IDENTITY_MISMATCH');
    for (const subject of state.subjects) {
      exactKeys(subject, ['uuid', 'position', 'velocity', 'yaw', 'pitch', 'bounds'], 'SUBJECT_FACT');
      vector(subject.position, 3); vector(subject.velocity, 3); vector(subject.bounds, 6);
      finite(subject.yaw, -360000, 360000); finite(subject.pitch, -90, 90);
      require(subject.bounds.slice(0, 3).every((n, i) => n <= subject.bounds[i + 3]), 'INVALID_SUBJECT_BOUNDS');
    }
    if (m.frames.length) require(state.gameTime === m.frames[0].serverGameTime, 'STRUCTURED_STATE_TIME_MISMATCH');
  }
  const proof = m.restorationProof;
  if (proof?.expected == null) delete proof.expected;
  if (proof?.observed == null) delete proof.observed;
  exactKeys(proof, ['basis', ...(proof.expected == null ? [] : ['expected']), ...(proof.observed == null ? [] : ['observed'])], 'RESTORATION_PROOF');
  require(proof.basis === 'MINECRAFT_API_READBACK', 'RESTORATION_BASIS_REQUIRED');
  const stateFields = ['cameraUuid', 'cameraType', 'hideGui', 'bob', 'fov', 'paused', 'mouseGrabbed', 'screen', 'x', 'y', 'z', 'yaw', 'pitch'];
  for (const state of [proof.expected, proof.observed]) if (state != null) {
    exactKeys(state, stateFields, 'PRESENTATION_STATE'); identifier(state.cameraUuid); identifier(state.cameraType);
    for (const key of ['hideGui', 'bob', 'paused', 'mouseGrabbed']) require(typeof state[key] === 'boolean', 'PRESENTATION_BOOLEAN_REQUIRED');
    integer(state.fov, 1, 179); require(['NONE', 'OTHER'].includes(state.screen), 'INVALID_SCREEN_STATE');
    for (const key of ['x', 'y', 'z', 'yaw', 'pitch']) finite(state[key], -30000000, 30000000);
  }
  if (r.restoration === 'RESTORED') require(proof.expected && proof.observed && same(proof.expected, proof.observed) &&
    proof.observed.paused === false && proof.observed.screen === 'NONE', 'RESTORATION_NOT_OBSERVED');
  if (r.status === 'COMPLETE') require(r.restoration === 'RESTORED' && !r.gaps.length &&
    m.controlledStateHash !== null && m.frames.length === 4 && r.frames.every(f => f.status === 'PRESENT') &&
    m.structuredState !== null && m.barrierDurationMs <= 2000, 'FALSE_COMPLETE_CAPTURE');
  if (r.restoration === 'UNKNOWN') require(r.status === 'UNKNOWN', 'RESTORATION_UNCERTAINTY_LOST');
  require(Buffer.byteLength(JSON.stringify(m)) <= 64 * 1024, 'VISUAL_MANIFEST_TOO_LARGE');
  return m;
}
export async function readRawVisualImage(runDir, frame) {
  const f = validateRawFrame(frame);
  const file = await readRegisteredFile({ root: runDir, relativePath: f.imagePath,
    expectedSha256: f.imageHash, maxBytes: 4 * 1024 * 1024 });
  const bytes = file.bytes;
  require(bytes.length === f.imageBytes && bytes.length >= 24 &&
    bytes.subarray(0, 8).equals(Buffer.from('89504e470d0a1a0a', 'hex')) &&
    bytes.readUInt32BE(16) === f.camera.viewport[0] && bytes.readUInt32BE(20) === f.camera.viewport[1], 'PNG_DIMENSIONS_OR_HASH_MISMATCH');
  // Strict framing precedes the existing bounded CRC/filter decoder. Unsupported transparency is never ignored.
  let offset = 8; let header = false; let ended = false; let sawData = false; let dataEnded = false;
  while (offset < bytes.length) {
    require(offset + 12 <= bytes.length, 'TRUNCATED_PNG');
    const length = bytes.readUInt32BE(offset); const kind = bytes.toString('ascii', offset + 4, offset + 8);
    const end = offset + 12 + length; require(end <= bytes.length, 'TRUNCATED_PNG');
    if (kind === 'IHDR') {
      require(!header && offset === 8 && length === 13 && [2, 6].includes(bytes[offset + 17]), 'INVALID_PNG_HEADER');
      header = true;
    } else if (kind === 'IDAT') { require(header && !dataEnded, 'PNG_DATA_ORDER'); sawData = true; }
    else if (kind === 'IEND') { require(length === 0 && end === bytes.length && sawData, 'PNG_TRAILING_OR_MISSING_DATA'); ended = true; }
    else {
      require(/^[a-z]/.test(kind) && kind !== 'tRNS', 'UNSUPPORTED_PNG_CHUNK');
      if (sawData) dataEnded = true;
    }
    offset = end;
  }
  require(ended, 'PNG_MISSING_END');
  decodePng(bytes);
  return bytes;
}
export async function retainVisualManifest(runtime, sourceBytes, observationId) {
  identifier(observationId);
  require(Buffer.isBuffer(sourceBytes) && sourceBytes.length <= 64 * 1024, 'BOUNDED_RAW_MANIFEST_REQUIRED');
  const manifest = validateVisualManifest(decodeJson(sourceBytes));
  for (const key of ['debugSessionId', 'runId', 'runSnapshotId', 'processEpoch'])
    require(manifest.identity[key] === runtime[key], 'FOREIGN_VISUAL_RUN');
  const canonicalSource = runtime.store.observationById?.get(observationId);
  require(typeof canonicalSource === 'string' &&
    same(validateVisualManifest(JSON.parse(canonicalSource).payload), manifest), 'CANONICAL_MANIFEST_BINDING_REQUIRED');
  await runtime.store.assertMutable();
  for (const frame of manifest.frames)
    if (manifest.result.frames[frame.frameIndex].status === 'PRESENT') await readRawVisualImage(runtime.runDir, frame);
  const dir = path.join(runtime.runDir, 'evidence', 'captures');
  await mkdir(dir, { recursive: true });
  const file = path.join(dir, `visual-${manifest.captureId}.json`);
  await writeFile(file, sourceBytes, { flag: 'wx' });
  return { file, manifest, sourceObservationId: observationId,
    rawManifestHash: createHash('sha256').update(sourceBytes).digest('hex') };
}
