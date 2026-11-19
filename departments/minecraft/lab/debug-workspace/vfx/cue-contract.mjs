// VFX Cue Contract v1 (PLAN §4.2). A cue describes presentation only; the server owns attack
// state, hit detection and damage. Cues are sealed: cueId = sha256(stableJson(body)).
import {
  boundedList, byteLimit, contentRef, exactKeys, finite, identifier, integer, oneOf, require,
  resourceId, revision, same, sealed, uuid, vector, verifySeal,
} from './common.mjs';

export const CUE_KIND = 'kneekura_vfx_cue';
export const EVENT_KINDS = Object.freeze(['TELEGRAPH', 'START', 'HIT', 'CANCEL', 'END', 'UNLOAD']);
export const TERMINAL_EVENTS = Object.freeze(['CANCEL', 'END', 'UNLOAD']);
export const GAMEPLAY_AUTHORITY = 'SERVER_AUTHORITATIVE_VFX_IS_PRESENTATION_ONLY';

/** The only parameters an AI repair may touch (PLAN §4.5). Units are explicit. */
export const FX_PARAMETER_SCHEMA = Object.freeze({
  color: { kind: 'vector', size: 3, min: 0, max: 1, unit: 'linear RGB 0..1' },
  startOffsetTicks: { kind: 'integer', min: -20, max: 200, unit: 'server ticks relative to cue tick' },
  emitterLocalOffset: { kind: 'vector', size: 3, min: -8, max: 8, unit: 'blocks in attachment space' },
  lifetime: { kind: 'integer', min: 1, max: 200, unit: 'ticks' },
  spawnRate: { kind: 'number', min: 0, max: 2000, unit: 'particles per second' },
  trailWidth: { kind: 'number', min: 0, max: 4, unit: 'blocks' },
  intensity: { kind: 'number', min: 0, max: 4, unit: 'relative emissive multiplier' },
});

/** Hard ceilings; a cue may declare lower limits, never higher ones. */
export const LIMIT_CEILINGS = Object.freeze({
  maxConcurrentEffects: 8, maxParticles: 4096, maxTrailLength: 64, maxCumulativeGlow: 8,
  maxRecordedFrames: 600, maxCpuMillisPerFrame: 8, maxGpuMillisPerFrame: 8, maxMemoryBytes: 64 * 1024 * 1024,
});

const CUE_KEYS = ['cueId', 'schemaVersion', 'kind', 'effectId', 'providerId', 'providerSourceRevision', 'runtimeAssetHash',
  'profile', 'generation', 'attackInstanceId', 'eventKind', 'actorUuid', 'targetUuid', 'dimension', 'attachment',
  'timing', 'clockMapping', 'params', 'seed', 'limits', 'gameplayAuthority'];

export function validateFxParameter(name, value) {
  const spec = FX_PARAMETER_SCHEMA[name];
  require(Object.hasOwn(FX_PARAMETER_SCHEMA, name) && spec, 'FX_PARAMETER_NOT_ALLOWED');
  if (spec.kind === 'vector') vector(value, spec.size, Math.max(Math.abs(spec.min), Math.abs(spec.max)), 'INVALID_FX_PARAMETER');
  if (spec.kind === 'vector') value.forEach(n => finite(n, spec.min, spec.max, 'FX_PARAMETER_OUT_OF_RANGE'));
  else if (spec.kind === 'integer') integer(value, spec.min, spec.max, 'FX_PARAMETER_OUT_OF_RANGE');
  else finite(value, spec.min, spec.max, 'FX_PARAMETER_OUT_OF_RANGE');
  return value;
}

function attachment(a, cue) {
  require(a && typeof a === 'object', 'INVALID_ATTACHMENT');
  if (a.kind === 'WORLD') {
    exactKeys(a, ['kind', 'position'], 'WORLD_ATTACHMENT'); vector(a.position, 3);
  } else if (a.kind === 'ENTITY') {
    exactKeys(a, ['kind', 'entityUuid', 'localOffset'], 'ENTITY_ATTACHMENT');
    uuid(a.entityUuid); vector(a.localOffset, 3, 16);
  } else if (a.kind === 'BONE') {
    exactKeys(a, ['kind', 'entityUuid', 'bone', 'modelVersion', 'boneLayoutHash', 'localOffset'], 'BONE_ATTACHMENT');
    uuid(a.entityUuid); identifier(a.bone); identifier(a.modelVersion); contentRef(a.boneLayoutHash); vector(a.localOffset, 3, 16);
  } else throw new TypeError('INVALID_ATTACHMENT_KIND');
  if (a.kind !== 'WORLD') require(a.entityUuid === cue.actorUuid || a.entityUuid === cue.targetUuid, 'ATTACHMENT_ENTITY_NOT_IN_CUE');
}

function limits(l, params) {
  exactKeys(l, Object.keys(LIMIT_CEILINGS), 'CUE_LIMITS');
  for (const [key, ceiling] of Object.entries(LIMIT_CEILINGS)) integer(l[key], key === 'maxCumulativeGlow' ? 0 : 1, ceiling, 'CUE_LIMIT_OVER_CEILING');
  // Steady-state particle estimate must fit the declared particle budget (A09).
  if (params.spawnRate !== undefined) {
    const life = params.lifetime ?? 1;
    require(Math.ceil(params.spawnRate * life / 20) <= l.maxParticles, 'PARTICLE_BUDGET_EXCEEDED');
  }
  if (params.intensity !== undefined) require(params.intensity <= l.maxCumulativeGlow, 'GLOW_BUDGET_EXCEEDED');
}

/** Validate a sealed cue. Returns a defensive copy. */
export function validateCue(input) {
  const cue = structuredClone(input);
  exactKeys(cue, CUE_KEYS, 'VFX_CUE');
  verifySeal(cue, 'cueId', 'VFX_CUE_INTEGRITY');
  require(cue.schemaVersion === 1 && cue.kind === CUE_KIND, 'INVALID_VFX_CUE_KIND');
  resourceId(cue.effectId); identifier(cue.providerId); revision(cue.providerSourceRevision); contentRef(cue.runtimeAssetHash);
  exactKeys(cue.profile, ['profileHash', 'buildHash', 'resourceHash', 'configHash'], 'CUE_PROFILE');
  Object.values(cue.profile).forEach(v => contentRef(v));
  integer(cue.generation, 1, 1000000, 'CUE_GENERATION');
  identifier(cue.attackInstanceId); oneOf(cue.eventKind, EVENT_KINDS, 'INVALID_EVENT_KIND');
  uuid(cue.actorUuid);
  if (cue.targetUuid !== null) { uuid(cue.targetUuid); require(cue.targetUuid !== cue.actorUuid, 'TARGET_IS_ACTOR'); }
  require(typeof cue.dimension === 'string' && /^[a-z0-9_]+:[a-z0-9_./-]+$/.test(cue.dimension), 'INVALID_DIMENSION');
  attachment(cue.attachment, cue);
  exactKeys(cue.timing, ['serverTick', 'serverGameTime', 'durationTicks'], 'CUE_TIMING');
  integer(cue.timing.serverTick, 0, Number.MAX_SAFE_INTEGER); integer(cue.timing.serverGameTime, 0, Number.MAX_SAFE_INTEGER);
  integer(cue.timing.durationTicks, 0, 200, 'CUE_DURATION');
  const terminal = TERMINAL_EVENTS.includes(cue.eventKind);
  require(terminal ? cue.timing.durationTicks === 0 : cue.timing.durationTicks > 0, terminal ? 'TERMINAL_CUE_HAS_DURATION' : 'UNBOUNDED_CUE_DURATION');
  const m = cue.clockMapping;
  if (m?.status === 'NOT_OBSERVED') exactKeys(m, ['status'], 'CLOCK_MAPPING');
  else {
    exactKeys(m, ['status', 'clientTick', 'renderFrame', 'partialTick', 'observationId'], 'CLOCK_MAPPING');
    require(m.status === 'OBSERVED', 'INVALID_CLOCK_MAPPING');
    integer(m.clientTick, 0, Number.MAX_SAFE_INTEGER); integer(m.renderFrame, 0, Number.MAX_SAFE_INTEGER);
    finite(m.partialTick, 0, 1); identifier(m.observationId);
  }
  require(cue.params && typeof cue.params === 'object' && !Array.isArray(cue.params) && Object.keys(cue.params).length <= 16, 'INVALID_FX_PARAMS');
  for (const [name, value] of Object.entries(cue.params)) validateFxParameter(name, value);
  if (!terminal) require(Number.isSafeInteger(cue.params.lifetime), 'FX_LIFETIME_REQUIRED');
  exactKeys(cue.seed, ['value', 'determinism'], 'CUE_SEED');
  if (cue.seed.value !== null) integer(cue.seed.value, -2147483648, 2147483647, 'CUE_SEED');
  // A seed never proves GPU determinism (A08). The only accepted claim is "not claimed".
  require(cue.seed.determinism === 'NOT_CLAIMED', 'DETERMINISM_OVERCLAIM');
  limits(cue.limits, cue.params);
  require(cue.gameplayAuthority === GAMEPLAY_AUTHORITY, 'VFX_GAMEPLAY_AUTHORITY_REJECTED');
  byteLimit(cue, 16 * 1024, 'VFX_CUE_TOO_LARGE');
  return cue;
}

/** Build and seal a cue from an unsealed body, validating it. */
export function createCue(body) {
  return validateCue(sealed({ schemaVersion: 1, kind: CUE_KIND, gameplayAuthority: GAMEPLAY_AUTHORITY,
    clockMapping: { status: 'NOT_OBSERVED' }, seed: { value: null, determinism: 'NOT_CLAIMED' }, ...body }, 'cueId'));
}

/**
 * One attack instance must form a finite lifecycle (A12): optional TELEGRAPHs, at most one START,
 * HITs only while started, at most one terminal, nothing after it. A missing terminal is OPEN, never PASS.
 */
export function validateCueLifecycle(input) {
  boundedList(input, 256, 'CUE_LIFECYCLE_LIMIT');
  require(input.length > 0, 'CUE_LIFECYCLE_EMPTY');
  const cues = input.map(validateCue);
  const first = cues[0];
  const ids = new Set();
  let started = false; let terminal = null; let previousTick = -1; let hits = 0;
  for (const cue of cues) {
    require(!ids.has(cue.cueId), 'DUPLICATE_CUE'); ids.add(cue.cueId);
    require(cue.attackInstanceId === first.attackInstanceId && cue.actorUuid === first.actorUuid &&
      cue.dimension === first.dimension && same(cue.profile, first.profile), 'CUE_LIFECYCLE_IDENTITY_MISMATCH');
    require(cue.timing.serverTick >= previousTick, 'CUE_LIFECYCLE_OUT_OF_ORDER');
    previousTick = cue.timing.serverTick;
    require(terminal === null, 'CUE_AFTER_TERMINAL');
    if (cue.eventKind === 'TELEGRAPH') require(!started, 'TELEGRAPH_AFTER_START');
    else if (cue.eventKind === 'START') { require(!started, 'DUPLICATE_START'); started = true; }
    else if (cue.eventKind === 'HIT') { require(started, 'HIT_BEFORE_START'); hits++; }
    else terminal = cue.eventKind;
  }
  return { attackInstanceId: first.attackInstanceId, status: terminal ? 'TERMINATED' : 'OPEN',
    terminalKind: terminal, started, hits, cueIds: [...ids],
    residualRisk: terminal ? 'NONE_DECLARED_RUNTIME_RESIDUE_NOT_OBSERVED' : 'NO_TERMINAL_EVENT_RESIDUE_POSSIBLE' };
}

/**
 * Bone emitters are bound to a model layout hash, not a bone name (A19/A35).
 * A changed layout silently reusing an old emitter is rejected.
 */
export function bindCueToModel(cueInput, model) {
  const cue = validateCue(cueInput);
  exactKeys(model, ['entityUuid', 'modelVersion', 'boneLayoutHash', 'bones'], 'MODEL_LAYOUT');
  uuid(model.entityUuid); identifier(model.modelVersion); contentRef(model.boneLayoutHash);
  boundedList(model.bones, 512); model.bones.forEach(identifier);
  const a = cue.attachment;
  if (a.kind !== 'BONE') return { status: 'NOT_BONE_ATTACHED', cueId: cue.cueId };
  require(a.entityUuid === model.entityUuid, 'BONE_EMITTER_ENTITY_MISMATCH');
  require(a.boneLayoutHash === model.boneLayoutHash && a.modelVersion === model.modelVersion, 'STALE_BONE_EMITTER_LAYOUT');
  require(model.bones.includes(a.bone), 'BONE_NOT_IN_LAYOUT');
  return { status: 'BOUND', cueId: cue.cueId, bone: a.bone, boneLayoutHash: a.boneLayoutHash };
}
