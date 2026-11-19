// Asset Method Manifest v1 (PLAN §10.3, §11.3). References only: blobs live in the existing CAS.
// Records which authoring/transfer/playback method produced each part, keeps switched-away candidates,
// and invalidates clips/emitters bound to a different rig layout instead of silently reusing them.
import {
  boundedList, byteLimit, contentRef, exactKeys, identifier, oneOf, require, resourceId, revision, sealed, verifySeal,
} from './common.mjs';

export const MANIFEST_KIND = 'kneekura_asset_method_manifest';
export const MODEL_METHODS = Object.freeze(['img2blockbench.direct', 'img2blockbench.mesh', 'img2blockbench.img2threejs',
  'mosaicary.gltf', 'blockbench.direct', 'blocksmith.experimental', 'manual']);
export const ANIMATION_METHODS = Object.freeze(['keyframes_direct', 'import_retarget', 'procedural_baked', 'runtime_procedural', 'manual']);
export const VFX_METHODS = Object.freeze(['photon_candidate', 'lodestone_candidate', 'custom_client_renderer', 'manual']);
/** Excluded by the user (PLAN §11). Never accepted, not even as a fallback. */
export const EXCLUDED_METHODS = Object.freeze(['kimodo', 'video2mocap']);
export const LOSS_KINDS = Object.freeze(['MATERIAL', 'TRANSPARENCY', 'UV', 'IK_CONSTRAINT', 'CURVE_EASING', 'EFFECT_KEYFRAME', 'ROOT_MOTION', 'OTHER']);
export const HUMAN_REVIEW = Object.freeze(['NOT_REQUESTED', 'PENDING', 'APPROVED', 'REJECTED', 'NOT_REVIEWED']);

function method(value, allowed) {
  require(typeof value === 'string', 'INVALID_METHOD');
  if (EXCLUDED_METHODS.some(x => value.toLowerCase().includes(x))) throw new TypeError('METHOD_EXCLUDED_BY_USER');
  return oneOf(value, allowed, 'UNKNOWN_METHOD');
}
function losses(list) {
  boundedList(list, 32);
  const kinds = new Set();
  for (const l of list) {
    exactKeys(l, ['kind', 'detail'], 'CONVERSION_LOSS'); oneOf(l.kind, LOSS_KINDS, 'INVALID_LOSS_KIND');
    require(typeof l.detail === 'string' && l.detail.trim().length > 0 && l.detail.length <= 512, 'INVALID_LOSS_DETAIL');
    require(!kinds.has(l.kind) || l.kind === 'OTHER', 'DUPLICATE_LOSS_KIND'); kinds.add(l.kind);
  }
  // Any recorded loss makes the conversion LOSSY; success never implies semantic preservation (A20/A34).
  return list.length ? 'LOSSY_CONVERSION' : 'NO_LOSS_RECORDED';
}
const stageName = /^(model|vfx|animation:[a-z0-9_]{1,32})$/;

function historyEvent(e) {
  exactKeys(e, ['eventId', 'stage', 'type', 'fromCandidate', 'toCandidate', 'method', 'provider', 'inputRef', 'outputRef',
    'reason', 'rejectedAlternatives', 'externalSend', 'measuredQuality', 'unverifiedAreas'], 'METHOD_EVENT');
  identifier(e.eventId);
  require(typeof e.stage === 'string' && stageName.test(e.stage), 'INVALID_METHOD_STAGE');
  oneOf(e.type, ['SELECT', 'SWITCH'], 'INVALID_METHOD_EVENT_TYPE');
  identifier(e.toCandidate);
  if (e.type === 'SELECT') require(e.fromCandidate === null, 'SELECT_HAS_PREVIOUS'); else identifier(e.fromCandidate);
  method(e.method, e.stage === 'model' ? MODEL_METHODS : e.stage === 'vfx' ? VFX_METHODS : ANIMATION_METHODS);
  exactKeys(e.provider, ['name', 'revision', 'license'], 'METHOD_PROVIDER');
  identifier(e.provider.name);
  // An allowed method name must not smuggle in an excluded tool as its provider.
  if (EXCLUDED_METHODS.some(x => e.provider.name.toLowerCase().includes(x))) throw new TypeError('METHOD_EXCLUDED_BY_USER');
  if (e.provider.revision !== null) revision(e.provider.revision);
  require(typeof e.provider.license === 'string' && e.provider.license.length > 0 && e.provider.license.length <= 64, 'METHOD_LICENSE_REQUIRED');
  contentRef(e.inputRef); contentRef(e.outputRef);
  require(typeof e.reason === 'string' && e.reason.trim().length > 0 && e.reason.length <= 1024, 'METHOD_REASON_REQUIRED');
  boundedList(e.rejectedAlternatives, 16);
  for (const r of e.rejectedAlternatives) {
    exactKeys(r, ['method', 'reason'], 'REJECTED_ALTERNATIVE');
    require(typeof r.method === 'string' && r.method.length <= 64 && typeof r.reason === 'string' && r.reason.length <= 512, 'INVALID_REJECTED_ALTERNATIVE');
  }
  exactKeys(e.externalSend, ['sent', 'destination', 'costEstimate', 'approvalRef'], 'EXTERNAL_SEND');
  require(typeof e.externalSend.sent === 'boolean', 'INVALID_EXTERNAL_SEND');
  if (e.externalSend.sent) {
    // Choosing a provider does not grant permission to send data or spend money (A17).
    require(typeof e.externalSend.destination === 'string' && /^[a-z0-9.-]+\.[a-z]{2,}$/.test(e.externalSend.destination), 'EXTERNAL_DESTINATION_REQUIRED');
    require(e.externalSend.approvalRef !== null, 'EXTERNAL_SEND_APPROVAL_REQUIRED');
    identifier(e.externalSend.approvalRef);
  } else require(e.externalSend.destination === null && e.externalSend.approvalRef === null, 'UNSENT_HAS_DESTINATION');
  require(e.externalSend.costEstimate === null || (typeof e.externalSend.costEstimate === 'string' && e.externalSend.costEstimate.length <= 64), 'INVALID_COST_ESTIMATE');
  oneOf(e.measuredQuality, ['NOT_MEASURED', 'PASS', 'FAIL', 'PARTIAL', 'UNKNOWN', 'INCONCLUSIVE'], 'INVALID_MEASURED_QUALITY');
  boundedList(e.unverifiedAreas, 32); e.unverifiedAreas.forEach(identifier);
}

export function validateAssetManifest(input) {
  const m = structuredClone(input);
  exactKeys(m, ['manifestId', 'schemaVersion', 'kind', 'assetId', 'profileRef', 'model', 'animations', 'vfx', 'methodHistory', 'verificationRefs', 'humanReview'], 'ASSET_MANIFEST');
  verifySeal(m, 'manifestId', 'ASSET_MANIFEST_INTEGRITY');
  require(m.schemaVersion === 1 && m.kind === MANIFEST_KIND, 'INVALID_ASSET_MANIFEST_KIND');
  resourceId(m.assetId); contentRef(m.profileRef);
  exactKeys(m.model, ['method', 'candidate', 'sourceRef', 'bbmodelRef', 'geoRef', 'textureRefs', 'rigRef', 'losses'], 'MANIFEST_MODEL');
  method(m.model.method, MODEL_METHODS); identifier(m.model.candidate);
  for (const k of ['sourceRef', 'bbmodelRef', 'rigRef']) contentRef(m.model[k]);
  if (m.model.geoRef !== null) contentRef(m.model.geoRef);
  boundedList(m.model.textureRefs, 32); m.model.textureRefs.forEach(r => contentRef(r));
  const modelLoss = losses(m.model.losses);
  require(m.animations && typeof m.animations === 'object' && !Array.isArray(m.animations) && Object.keys(m.animations).length <= 64, 'INVALID_ANIMATIONS');
  const clipStatus = {};
  for (const [clip, a] of Object.entries(m.animations)) {
    require(/^[a-z0-9_]{1,32}$/.test(clip), 'INVALID_CLIP_NAME');
    exactKeys(a, ['method', 'candidate', 'clipRef', 'rigRef', 'losses'], 'MANIFEST_CLIP');
    method(a.method, ANIMATION_METHODS); identifier(a.candidate); contentRef(a.clipRef); contentRef(a.rigRef);
    // A clip authored against another rig layout is never silently reused (A19/A35).
    require(a.rigRef === m.model.rigRef, 'CLIP_BOUND_TO_DIFFERENT_RIG');
    clipStatus[clip] = losses(a.losses);
  }
  boundedList(m.vfx, 32);
  for (const v of m.vfx) {
    exactKeys(v, ['method', 'candidate', 'cueRef', 'boneLayoutRef'], 'MANIFEST_VFX');
    method(v.method, VFX_METHODS); identifier(v.candidate); contentRef(v.cueRef);
    if (v.boneLayoutRef !== null) { contentRef(v.boneLayoutRef); require(v.boneLayoutRef === m.model.rigRef, 'VFX_BOUND_TO_DIFFERENT_RIG'); }
  }
  boundedList(m.methodHistory, 256); require(m.methodHistory.length > 0, 'METHOD_HISTORY_REQUIRED');
  const ids = new Set(); const candidates = new Map(); const latest = new Map();
  for (const e of m.methodHistory) {
    historyEvent(e);
    require(!ids.has(e.eventId), 'DUPLICATE_METHOD_EVENT'); ids.add(e.eventId);
    const key = `${e.stage}\0${e.toCandidate}`;
    require(!candidates.has(key), 'CANDIDATE_ID_REUSED');
    if (e.type === 'SWITCH') {
      // The switched-away candidate must exist earlier and keep its output (rollback/comparison).
      require(candidates.has(`${e.stage}\0${e.fromCandidate}`) && latest.get(e.stage) === e.fromCandidate, 'SWITCH_FROM_UNKNOWN_CANDIDATE');
    } else require(!latest.has(e.stage), 'SECOND_SELECT_USE_SWITCH');
    candidates.set(key, e.outputRef); latest.set(e.stage, e.toCandidate);
  }
  require(latest.get('model') === m.model.candidate, 'MODEL_CANDIDATE_NOT_FINAL_IN_HISTORY');
  for (const [clip, a] of Object.entries(m.animations)) require(latest.get(`animation:${clip}`) === a.candidate, 'CLIP_CANDIDATE_NOT_FINAL_IN_HISTORY');
  if (m.vfx.length) require(m.vfx.every(v => candidates.has(`vfx\0${v.candidate}`)), 'VFX_CANDIDATE_NOT_IN_HISTORY');
  boundedList(m.verificationRefs, 64); m.verificationRefs.forEach(r => contentRef(r));
  oneOf(m.humanReview, HUMAN_REVIEW, 'INVALID_HUMAN_REVIEW');
  byteLimit(m, 256 * 1024, 'ASSET_MANIFEST_TOO_LARGE');
  return { manifest: m, conversion: { model: modelLoss, clips: clipStatus },
    retainedCandidates: [...candidates.entries()].map(([k, outputRef]) => { const [stage, candidate] = k.split('\0'); return { stage, candidate, outputRef }; }) };
}

export function createAssetManifest(body) {
  return validateAssetManifest(sealed({ schemaVersion: 1, kind: MANIFEST_KIND, ...body }, 'manifestId'));
}

/** What a rig replacement invalidates. Nothing is rebound automatically; each item needs re-verification. */
export function invalidateForRig(manifestInput, newRigRef) {
  const { manifest } = validateAssetManifest(manifestInput);
  contentRef(newRigRef);
  if (newRigRef === manifest.model.rigRef) return { status: 'UNCHANGED', invalidated: [] };
  return { status: 'RIG_CHANGED', fromRigRef: manifest.model.rigRef, toRigRef: newRigRef,
    invalidated: [
      ...Object.keys(manifest.animations).map(clip => ({ kind: 'CLIP', id: clip, state: 'INVALIDATED_REVERIFY_OR_RETARGET' })),
      ...manifest.vfx.filter(v => v.boneLayoutRef !== null).map(v => ({ kind: 'BONE_EMITTER', id: v.candidate, state: 'INVALIDATED_REVERIFY_OR_RETARGET' })),
    ] };
}
