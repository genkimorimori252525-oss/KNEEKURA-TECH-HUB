export const RENDER_PACK_SCHEMA = 'kneekura.renderpack';
export const RENDER_MESH_SCHEMA = 'kneekura.rendermesh';
export const MATERIALS_SCHEMA = 'kneekura.materials';
export const RENDER_FRAME_SCHEMA = 'kneekura.renderframe';
export const SCHEMA_VERSION = '1.0.0';
export const SUPPORTED_SCHEMA_MAJOR = 1;
export const COORDINATE_SYSTEM = 'KNEEKURA_RH_Y_UP_BLOCK';

export const RUNTIME_FINAL_VERTEX_FORMAT = 'KNEEKURA_FINAL_VERTEX_V2';
export const RUNTIME_FINAL_VERTEX_STRIDE_FLOATS = 24;
export const RUNTIME_FINAL_VERTEX_AUXILIARY_INPUTS = 'resolved-per-vertex-rgba';

export const SOURCE_TYPES = Object.freeze([
  'runtimeFinalVertex',
  'runtimeMatrix',
  'runtimePaletteConverted',
  'recordedPose',
  'animationLibrary',
  'offlineYsmEmulator',
]);

export const SOURCE_AUTHORITY = Object.freeze([
  'authoritative',
  'derived',
  'predicted',
]);

export const SOURCE_FIDELITY_RANK = Object.freeze({
  runtimeFinalVertex: 0,
  runtimeMatrix: 1,
  runtimePaletteConverted: 2,
  recordedPose: 3,
  animationLibrary: 4,
  offlineYsmEmulator: 5,
});

export const EXPECTED_AUTHORITY = Object.freeze({
  runtimeFinalVertex: 'authoritative',
  runtimeMatrix: 'authoritative',
  runtimePaletteConverted: 'derived',
  recordedPose: 'derived',
  animationLibrary: 'derived',
  offlineYsmEmulator: 'predicted',
});

export const FORBIDDEN_AUTHORITATIVE_KEYS = Object.freeze([
  'bedrockGeometry',
  'molang',
  'animationController',
  'animationControllers',
  'legacyPalette',
  'ysmTrs',
]);
