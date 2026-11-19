// Tank Frame Sequence v1 (PLAN §4.3, P2). One fixed camera, time-ordered real Minecraft frames.
// RECORD_REPLAY only: stepping shows recorded images; it never claims the world was rewound.
import { validateVisualIdentity, validateCamera } from '../evidence/visual-capture.mjs';
import {
  boundedList, byteLimit, contentRef, exactKeys, finite, hashId, identifier, integer, oneOf, require,
  resourceId, same, sealed, uuid, verifySeal,
} from './common.mjs';

export const SEQUENCE_KIND = 'kneekura_tank_frame_sequence';
export const CAPTURE_STAGE = 'AFTER_LEVEL_BEFORE_HAND_HUD';
export const FRAME_STATUS = Object.freeze(['PRESENT', 'MISSING', 'STALE', 'WRITE_UNKNOWN']);
export const VFX_TIME_STATUS = Object.freeze(['DIRECT_OBSERVED', 'DERIVED', 'NOT_EXPOSED']);
export const ORIGINS = Object.freeze(['REAL_CLIENT', 'SYNTHETIC_FIXTURE']);
export const MAX_FRAMES = 600;

const SEQUENCE_KEYS = ['sequenceId', 'schemaVersion', 'kind', 'mode', 'origin', 'identity', 'subjects', 'fx', 'cameraId',
  'captureStage', 'budget', 'frames', 'restoration', 'result'];
const FRAME_KEYS = ['index', 'status', 'serverTick', 'serverGameTime', 'clientTick', 'renderFrame', 'partialTick',
  'captureTimeNanos', 'vfxTime', 'camera', 'imageHash', 'imageBytes', 'imagePath', 'sourceObservationId'];

function vfxTime(t) {
  require(t && typeof t === 'object', 'INVALID_VFX_TIME');
  if (t.status === 'NOT_EXPOSED') exactKeys(t, ['status'], 'VFX_TIME');
  else {
    exactKeys(t, ['status', 'ticks'], 'VFX_TIME');
    oneOf(t.status, ['DIRECT_OBSERVED', 'DERIVED'], 'INVALID_VFX_TIME_STATUS');
    finite(t.ticks, -200, 100000);
  }
}

function frame(f, i, seq) {
  exactKeys(f, FRAME_KEYS, 'SEQUENCE_FRAME');
  require(f.index === i, 'FRAME_INDEX_ORDER');
  oneOf(f.status, FRAME_STATUS, 'INVALID_FRAME_STATUS');
  for (const key of ['serverTick', 'serverGameTime', 'clientTick', 'renderFrame', 'captureTimeNanos']) integer(f[key], 0, Number.MAX_SAFE_INTEGER, 'FRAME_CLOCK');
  finite(f.partialTick, 0, 1);
  vfxTime(f.vfxTime);
  validateCamera(f.camera);
  if (f.status === 'MISSING') {
    require(f.imageHash === null && f.imageBytes === null && f.imagePath === null && f.sourceObservationId === null, 'MISSING_FRAME_HAS_IMAGE');
  } else {
    hashId(f.imageHash); integer(f.imageBytes, 1, 4 * 1024 * 1024, 'FRAME_IMAGE_BYTES');
    require(f.imagePath === `evidence/raw/visual/${f.imageHash}.png`, 'RAW_ARTIFACT_BINDING_MISMATCH');
    if (f.status === 'WRITE_UNKNOWN') require(f.sourceObservationId === null, 'UNKNOWN_WRITE_HAS_DURABLE_CLAIM');
    else identifier(f.sourceObservationId);
  }
  require(same(f.camera.viewport, seq.frames[0].camera.viewport), 'VIEWPORT_CHANGED_MID_SEQUENCE');
}

/** Validate a sealed sequence. Returns a defensive copy. */
export function validateFrameSequence(input) {
  const s = structuredClone(input);
  exactKeys(s, SEQUENCE_KEYS, 'FRAME_SEQUENCE');
  verifySeal(s, 'sequenceId', 'FRAME_SEQUENCE_INTEGRITY');
  require(s.schemaVersion === 1 && s.kind === SEQUENCE_KIND, 'INVALID_FRAME_SEQUENCE_KIND');
  // CONTROLLED_SEEK needs proven provider clock control; until then only RECORD_REPLAY exists (A08).
  require(s.mode === 'RECORD_REPLAY', 'ONLY_RECORD_REPLAY_SUPPORTED');
  oneOf(s.origin, ORIGINS, 'INVALID_SEQUENCE_ORIGIN');
  validateVisualIdentity(s.identity);
  boundedList(s.subjects, 16); require(s.subjects.length > 0, 'SUBJECTS_REQUIRED');
  s.subjects.forEach(v => uuid(v)); require(new Set(s.subjects).size === s.subjects.length, 'DUPLICATE_SUBJECT');
  exactKeys(s.fx, ['effectId', 'runtimeAssetHash', 'attackInstanceId', 'fxInstanceId', 'cueIds'], 'SEQUENCE_FX');
  resourceId(s.fx.effectId); contentRef(s.fx.runtimeAssetHash); identifier(s.fx.attackInstanceId); identifier(s.fx.fxInstanceId);
  boundedList(s.fx.cueIds, 64); s.fx.cueIds.forEach(hashId);
  identifier(s.cameraId);
  // The v1 stage matches Cardinal-4; post-process/hand/HUD capture is a separate P6 opt-in contract (A02).
  require(s.captureStage === CAPTURE_STAGE, 'CAPTURE_STAGE_NOT_ALLOWED_IN_V1');
  exactKeys(s.budget, ['maxFrames', 'maxTotalBytes', 'maxDurationTicks'], 'SEQUENCE_BUDGET');
  integer(s.budget.maxFrames, 1, MAX_FRAMES, 'SEQUENCE_BUDGET'); integer(s.budget.maxTotalBytes, 1, 512 * 1024 * 1024, 'SEQUENCE_BUDGET');
  integer(s.budget.maxDurationTicks, 1, 1200, 'SEQUENCE_BUDGET');
  boundedList(s.frames, s.budget.maxFrames, 'FRAME_BUDGET_EXCEEDED'); require(s.frames.length > 0, 'FRAMES_REQUIRED');
  s.frames.forEach((f, i) => frame(f, i, s));
  let bytes = 0; let previous = null;
  for (const f of s.frames) {
    bytes += f.imageBytes ?? 0;
    if (previous) require(f.renderFrame > previous.renderFrame && f.clientTick >= previous.clientTick &&
      f.serverTick >= previous.serverTick && f.captureTimeNanos >= previous.captureTimeNanos, 'FRAME_CLOCK_NOT_MONOTONIC');
    previous = f;
  }
  require(bytes <= s.budget.maxTotalBytes, 'BYTE_BUDGET_EXCEEDED');
  require(s.frames.at(-1).serverTick - s.frames[0].serverTick <= s.budget.maxDurationTicks, 'DURATION_BUDGET_EXCEEDED');
  oneOf(s.restoration, ['RESTORED', 'UNKNOWN'], 'INVALID_RESTORATION');
  exactKeys(s.result, ['status', 'gaps'], 'SEQUENCE_RESULT');
  oneOf(s.result.status, ['COMPLETE', 'PARTIAL', 'UNKNOWN'], 'INVALID_SEQUENCE_STATUS');
  boundedList(s.result.gaps, MAX_FRAMES); s.result.gaps.forEach(identifier);
  if (s.restoration === 'UNKNOWN') require(s.result.status === 'UNKNOWN', 'RESTORATION_UNCERTAINTY_LOST');
  if (s.result.status === 'COMPLETE') require(s.restoration === 'RESTORED' && !s.result.gaps.length &&
    s.frames.every(f => f.status === 'PRESENT'), 'FALSE_COMPLETE_SEQUENCE');
  byteLimit(s, 2 * 1024 * 1024, 'FRAME_SEQUENCE_TOO_LARGE');
  return s;
}

export function createFrameSequence(body) {
  return validateFrameSequence(sealed({ schemaVersion: 1, kind: SEQUENCE_KIND, mode: 'RECORD_REPLAY', captureStage: CAPTURE_STAGE, ...body }, 'sequenceId'));
}

/**
 * Derived replay index: per-frame gaps, drops and server/client skew made explicit.
 * `expectedRenderStride` is the planned capture stride (1 = every render frame).
 */
export function buildReplayIndex(input, { expectedRenderStride = 1 } = {}) {
  const s = validateFrameSequence(input);
  integer(expectedRenderStride, 1, 1000, 'RENDER_STRIDE');
  const base = s.frames[0];
  const rows = s.frames.map((f, i) => {
    const prev = s.frames[i - 1];
    const flags = [];
    if (f.status !== 'PRESENT') flags.push(f.status);
    if (prev) {
      const dropped = (f.renderFrame - prev.renderFrame) / expectedRenderStride - 1;
      if (dropped > 0) flags.push(`DROPPED_RENDER_FRAMES:${Math.ceil(dropped)}`);
      if (f.status === 'PRESENT' && prev.status === 'PRESENT' && f.imageHash === prev.imageHash && f.clientTick > prev.clientTick) flags.push('IDENTICAL_IMAGE_WHILE_TIME_ADVANCED');
    }
    if (f.vfxTime.status === 'NOT_EXPOSED') flags.push('VFX_TIME_NOT_EXPOSED');
    return {
      index: f.index, status: f.status, flags,
      serverTick: f.serverTick, clientTick: f.clientTick, renderFrame: f.renderFrame, partialTick: f.partialTick,
      // Skew is reported as a number, never as a causal claim.
      clientMinusServerTicks: (f.clientTick - base.clientTick) - (f.serverTick - base.serverTick),
      captureMillisFromStart: Number(f.captureTimeNanos - base.captureTimeNanos) / 1e6,
      vfxTime: structuredClone(f.vfxTime), imageHash: f.imageHash, imagePath: f.imagePath,
    };
  });
  return {
    schemaVersion: 1, kind: 'kneekura_replay_index', derived: true,
    semantics: 'RECORDED_IMAGE_REPLAY_NOT_WORLD_REWIND',
    sequenceId: s.sequenceId, origin: s.origin, status: s.result.status, restoration: s.restoration,
    frameCount: rows.length, presentCount: rows.filter(r => r.status === 'PRESENT').length,
    flaggedFrames: rows.filter(r => r.flags.length).map(r => r.index), rows,
  };
}

/** Bounded cursor stepping over a replay index. Returns the clamped index and whether it moved. */
export function step(index, cursor, delta) {
  integer(cursor, 0, index.frameCount - 1, 'REPLAY_CURSOR'); integer(delta, -index.frameCount, index.frameCount, 'REPLAY_DELTA');
  const next = Math.min(index.frameCount - 1, Math.max(0, cursor + delta));
  return { cursor: next, moved: next !== cursor, row: structuredClone(index.rows[next]) };
}

/** CONTROLLED_SEEK is explicitly unavailable until a provider proves clock control on a real client. */
export function controlledSeek(capabilities) {
  return capabilities?.controlledSeek === 'AVAILABLE'
    ? { status: 'NOT_IMPLEMENTED', reason: 'PROVIDER_REPORTS_SEEK_BUT_KNEEKURA_SEEK_PATH_NOT_BUILT' }
    : { status: 'UNAVAILABLE', reason: 'PROVIDER_CLOCK_CONTROL_NOT_PROVEN' };
}

/**
 * Label a sequential Cardinal-4 capture (A01). SAME_VFX_INSTANT requires directly observed VFX
 * clocks that are identical across all four frames; everything else is SEQUENTIAL_TIME_SKEW or UNKNOWN.
 */
export function labelCardinalTiming(frames, vfxClocks) {
  boundedList(frames, 4); require(frames.length === 4, 'FOUR_FRAMES_REQUIRED');
  boundedList(vfxClocks, 4); require(vfxClocks.length === 4, 'FOUR_VFX_CLOCKS_REQUIRED');
  vfxClocks.forEach(vfxTime);
  frames.forEach((f, i) => {
    integer(f?.renderFrame, 0, Number.MAX_SAFE_INTEGER, 'FRAME_CLOCK'); integer(f?.clientTick, 0, Number.MAX_SAFE_INTEGER, 'FRAME_CLOCK');
    if (i) require(f.renderFrame > frames[i - 1].renderFrame, 'FRAME_CLOCK_NOT_MONOTONIC');
  });
  const renderSpan = frames.at(-1).renderFrame - frames[0].renderFrame;
  const clientSpan = frames.at(-1).clientTick - frames[0].clientTick;
  if (vfxClocks.some(c => c.status !== 'DIRECT_OBSERVED'))
    return { label: 'UNKNOWN_VFX_CLOCK', sameFrame: false, renderSpan, clientSpan, vfxSpanTicks: null };
  const ticks = vfxClocks.map(c => c.ticks);
  const vfxSpanTicks = Math.max(...ticks) - Math.min(...ticks);
  return { label: vfxSpanTicks === 0 ? 'SAME_VFX_INSTANT' : 'SEQUENTIAL_TIME_SKEW', sameFrame: false, renderSpan, clientSpan, vfxSpanTicks };
}
