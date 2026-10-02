import { createHash } from 'node:crypto';
import {
  COORDINATE_SYSTEM,
  EXPECTED_AUTHORITY,
  FORBIDDEN_AUTHORITATIVE_KEYS,
  MATERIALS_SCHEMA,
  RENDER_FRAME_SCHEMA,
  RENDER_MESH_SCHEMA,
  RENDER_PACK_SCHEMA,
  RUNTIME_FINAL_VERTEX_AUXILIARY_INPUTS,
  RUNTIME_FINAL_VERTEX_FORMAT,
  RUNTIME_FINAL_VERTEX_STRIDE_FLOATS,
  SOURCE_AUTHORITY,
  SOURCE_FIDELITY_RANK,
  SOURCE_TYPES,
  SUPPORTED_SCHEMA_MAJOR,
} from './constants.mjs';

const HASH_RE = /^sha256:[0-9a-f]{64}$/;
const UUID_LIKE_RE = /^[0-9a-fA-F-]{8,}$/;

export class ContractError extends Error {
  constructor(message, path = '$') {
    super(`${path}: ${message}`);
    this.name = 'ContractError';
    this.path = path;
  }
}

function fail(message, path) {
  throw new ContractError(message, path);
}

function isObject(v) {
  return v !== null && typeof v === 'object' && !Array.isArray(v);
}

function requiredObject(v, path) {
  if (!isObject(v)) fail('expected object', path);
  return v;
}

function requiredString(v, path) {
  if (typeof v !== 'string' || v.length === 0) fail('expected non-empty string', path);
  return v;
}

function requiredInteger(v, path, min = Number.MIN_SAFE_INTEGER) {
  if (!Number.isSafeInteger(v) || v < min) fail(`expected safe integer >= ${min}`, path);
  return v;
}

function requiredNumber(v, path) {
  if (typeof v !== 'number' || !Number.isFinite(v)) fail('expected finite number', path);
  return v;
}

function requiredArray(v, path) {
  if (!Array.isArray(v)) fail('expected array', path);
  return v;
}

function assertHash(v, path) {
  if (!HASH_RE.test(requiredString(v, path))) fail('expected sha256:<64 lowercase hex>', path);
}

function major(version) {
  const m = /^(\d+)\.(\d+)\.(\d+)(?:[-+].*)?$/.exec(requiredString(version, '$.schemaVersion'));
  if (!m) fail('expected semantic version', '$.schemaVersion');
  return Number(m[1]);
}

function assertSupportedVersion(version) {
  const m = major(version);
  if (m !== SUPPORTED_SCHEMA_MAJOR) {
    fail(`unsupported schema major ${m}; expected ${SUPPORTED_SCHEMA_MAJOR}`, '$.schemaVersion');
  }
}

function assertRelativePackPath(path, at) {
  requiredString(path, at);
  if (path.startsWith('/') || /^[A-Za-z]:[\\/]/.test(path)) fail('absolute path is forbidden', at);
  const parts = path.replaceAll('\\', '/').split('/');
  if (parts.includes('..')) fail('path traversal is forbidden', at);
  if (parts.includes('')) fail('empty path segment is forbidden', at);
}

function assertMatrix16(v, path) {
  const a = requiredArray(v, path);
  if (a.length !== 16) fail('expected 16 float values', path);
  a.forEach((x, i) => requiredNumber(x, `${path}[${i}]`));
}

function assertSizedVector(v, size, path) {
  const a = requiredArray(v, path);
  if (a.length !== size) fail(`expected ${size} float values`, path);
  a.forEach((x, i) => requiredNumber(x, `${path}[${i}]`));
}

function assertGlobalShaderState(v, path) {
  const state = requiredObject(v, path);
  if (state.matrixConvention !== 'JOML_COLUMN_MAJOR_COLUMN_VECTOR') {
    fail('unexpected matrix convention', `${path}.matrixConvention`);
  }
  assertMatrix16(state.modelViewMatrix, `${path}.modelViewMatrix`);
  assertMatrix16(state.projectionMatrix, `${path}.projectionMatrix`);
  assertSizedVector(state.inverseViewRotationMatrix, 9, `${path}.inverseViewRotationMatrix`);

  const lights = requiredArray(state.directionalLights, `${path}.directionalLights`);
  if (lights.length !== 2) fail('expected exactly 2 directional lights', `${path}.directionalLights`);
  lights.forEach((light, i) => assertSizedVector(light, 3, `${path}.directionalLights[${i}]`));
  assertSizedVector(state.shaderColor, 4, `${path}.shaderColor`);

  const fog = requiredObject(state.fog, `${path}.fog`);
  if (fog.curve !== 'smoothstep') fail("fog.curve must be 'smoothstep'", `${path}.fog.curve`);
  requiredNumber(fog.start, `${path}.fog.start`);
  requiredNumber(fog.end, `${path}.fog.end`);
  assertSizedVector(fog.color, 4, `${path}.fog.color`);
  if (!['sphere', 'cylinder'].includes(fog.shape)) fail('unsupported fog shape', `${path}.fog.shape`);
  if (fog.distanceSpace !== 'modelView') {
    fail("fog.distanceSpace must be 'modelView'", `${path}.fog.distanceSpace`);
  }
  return state;
}


function assertExactArrayEqual(actual, expected, path) {
  const a = requiredArray(actual, path);
  if (!Array.isArray(expected) || a.length !== expected.length) fail('array length mismatch', path);
  for (let i = 0; i < a.length; i++) {
    requiredNumber(a[i], `${path}[${i}]`);
    if (!Object.is(a[i], expected[i])) fail('value does not exactly match bound frame state', `${path}[${i}]`);
  }
}

function assertGoldenBinding(binding, frame) {
  const b = requiredObject(binding, '$.goldenBinding');
  if (b.schema !== 'kneekura.golden-frame-binding') fail('unexpected Golden binding schema', '$.goldenBinding.schema');
  if (b.schemaVersion !== 1) fail('unexpected Golden binding version', '$.goldenBinding.schemaVersion');
  const identity = requiredObject(b.identity, '$.goldenBinding.identity');
  for (const key of ['runId', 'entityUuid']) {
    requiredString(identity[key], `$.goldenBinding.identity.${key}`);
    if (identity[key] !== frame[key]) fail(`Golden binding ${key} mismatch`, `$.goldenBinding.identity.${key}`);
  }
  for (const key of ['renderSequence', 'gameTime']) {
    requiredInteger(identity[key], `$.goldenBinding.identity.${key}`);
    if (identity[key] !== frame[key]) fail(`Golden binding ${key} mismatch`, `$.goldenBinding.identity.${key}`);
  }
  requiredNumber(identity.partialTick, '$.goldenBinding.identity.partialTick');
  if (!Object.is(identity.partialTick, frame.partialTick)) fail('Golden binding partialTick mismatch', '$.goldenBinding.identity.partialTick');
  requiredInteger(b.renderTick, '$.goldenBinding.renderTick', 1);

  const fb = requiredObject(b.framebuffer, '$.goldenBinding.framebuffer');
  for (const key of ['width','height','viewportWidth','viewportHeight','windowWidth','windowHeight','guiScaledWidth','guiScaledHeight']) {
    requiredInteger(fb[key], `$.goldenBinding.framebuffer.${key}`, 1);
  }
  const camera = requiredObject(b.camera, '$.goldenBinding.camera');
  assertSizedVector(camera.position, 3, '$.goldenBinding.camera.position');
  requiredNumber(camera.xRot, '$.goldenBinding.camera.xRot');
  requiredNumber(camera.yRot, '$.goldenBinding.camera.yRot');
  assertSizedVector(camera.rotationQuaternion, 4, '$.goldenBinding.camera.rotationQuaternion');
  assertMatrix16(camera.projectionMatrix, '$.goldenBinding.camera.projectionMatrix');
  if (camera.matrixConvention !== 'JOML_COLUMN_MAJOR_COLUMN_VECTOR') {
    fail('unexpected Golden binding matrix convention', '$.goldenBinding.camera.matrixConvention');
  }
  assertExactArrayEqual(camera.projectionMatrix, frame.globalShaderState.projectionMatrix,
    '$.goldenBinding.camera.projectionMatrix');

  const depth = requiredObject(b.backgroundDepth, '$.goldenBinding.backgroundDepth');
  if (depth.encoding !== 'FLOAT32_LE') fail('unexpected bound depth encoding', '$.goldenBinding.backgroundDepth.encoding');
  if (depth.origin !== 'bottom-left') fail('unexpected bound depth origin', '$.goldenBinding.backgroundDepth.origin');
  if (depth.range !== 'OPENGL_DEPTH_0_1') fail('unexpected bound depth range', '$.goldenBinding.backgroundDepth.range');
  requiredInteger(depth.width, '$.goldenBinding.backgroundDepth.width', 1);
  requiredInteger(depth.height, '$.goldenBinding.backgroundDepth.height', 1);
  if (depth.width !== fb.width || depth.height !== fb.height) {
    fail('bound depth dimensions do not match framebuffer', '$.goldenBinding.backgroundDepth');
  }
  return b;
}

function assertMatrix16OrUnknown(v, authority, path) {
  if (v === null) {
    if (authority !== 'UNKNOWN') {
      fail("null matrix requires explicit authority 'UNKNOWN'", `${path}Authority`);
    }
    return;
  }
  assertMatrix16(v, path);
}

function assertBooleanOrUnknown(v, path) {
  if (typeof v !== 'boolean' && v !== 'UNKNOWN') fail("expected boolean or 'UNKNOWN'", path);
}

function assertNoForbiddenAuthoritativeKeys(frame) {
  if (frame?.source?.authority !== 'authoritative') return;
  const stack = [{ value: frame, path: '$' }];
  while (stack.length) {
    const { value, path } = stack.pop();
    if (!isObject(value) && !Array.isArray(value)) continue;
    if (isObject(value)) {
      for (const [key, child] of Object.entries(value)) {
        if (FORBIDDEN_AUTHORITATIVE_KEYS.includes(key)) {
          fail(`YSM/Bedrock reconstruction key '${key}' is forbidden in authoritative RenderFrameIR`, `${path}.${key}`);
        }
        stack.push({ value: child, path: `${path}.${key}` });
      }
    } else {
      value.forEach((child, i) => stack.push({ value: child, path: `${path}[${i}]` }));
    }
  }
}

export function assertRenderPackManifest(manifest) {
  requiredObject(manifest, '$');
  if (manifest.schema !== RENDER_PACK_SCHEMA) fail(`expected ${RENDER_PACK_SCHEMA}`, '$.schema');
  assertSupportedVersion(manifest.schemaVersion);
  requiredString(manifest.modelId, '$.modelId');
  assertHash(manifest.packHash, '$.packHash');
  assertHash(manifest.layoutHash, '$.layoutHash');
  if (manifest.coordinateSystem !== COORDINATE_SYSTEM) {
    fail(`expected ${COORDINATE_SYSTEM}`, '$.coordinateSystem');
  }
  const compiler = requiredObject(manifest.compiler, '$.compiler');
  requiredString(compiler.name, '$.compiler.name');
  requiredString(compiler.version, '$.compiler.version');
  const source = requiredObject(manifest.source, '$.source');
  requiredString(source.adapter, '$.source.adapter');
  requiredString(source.modVersion, '$.source.modVersion');
  assertHash(source.modJarHash, '$.source.modJarHash');
  assertHash(source.modelResourceHash, '$.source.modelResourceHash');

  const files = requiredArray(manifest.files, '$.files');
  const seen = new Set();
  files.forEach((entry, i) => {
    requiredObject(entry, `$.files[${i}]`);
    assertRelativePackPath(entry.path, `$.files[${i}].path`);
    assertHash(entry.sha256, `$.files[${i}].sha256`);
    if (seen.has(entry.path)) fail('duplicate file path', `$.files[${i}].path`);
    seen.add(entry.path);
  });
  const computedPackHash = computePackHash(manifest);
  if (manifest.packHash !== computedPackHash) {
    fail(`packHash does not match canonical manifest identity; expected ${computedPackHash}`, '$.packHash');
  }
  return manifest;
}

export function assertRenderMeshIR(mesh) {
  requiredObject(mesh, '$');
  if (mesh.schema !== RENDER_MESH_SCHEMA) fail(`expected ${RENDER_MESH_SCHEMA}`, '$.schema');
  assertSupportedVersion(mesh.schemaVersion);
  requiredString(mesh.modelId, '$.modelId');
  assertHash(mesh.layoutHash, '$.layoutHash');
  const buffers = requiredArray(mesh.buffers, '$.buffers');
  buffers.forEach((b, i) => {
    requiredObject(b, `$.buffers[${i}]`);
    requiredString(b.id, `$.buffers[${i}].id`);
    assertRelativePackPath(b.path, `$.buffers[${i}].path`);
    requiredInteger(b.byteLength, `$.buffers[${i}].byteLength`, 0);
    assertHash(b.sha256, `$.buffers[${i}].sha256`);
  });
  const attributes = requiredObject(mesh.attributes, '$.attributes');
  for (const name of ['position', 'normal', 'uv0', 'color0', 'joints', 'weights']) {
    requiredObject(attributes[name], `$.attributes.${name}`);
  }
  requiredObject(mesh.indexAccessor, '$.indexAccessor');
  const bones = requiredArray(mesh.bones, '$.bones');
  bones.forEach((b, i) => {
    requiredObject(b, `$.bones[${i}]`);
    if (b.slot !== i) fail('bone slot must equal array index in v1', `$.bones[${i}].slot`);
    requiredString(b.name, `$.bones[${i}].name`);
    if (b.parentSlot !== null) requiredInteger(b.parentSlot, `$.bones[${i}].parentSlot`, 0);
    assertMatrix16OrUnknown(b.bindMatrix, b.bindMatrixAuthority, `$.bones[${i}].bindMatrix`);
    assertMatrix16OrUnknown(b.inverseBindMatrix, b.inverseBindMatrixAuthority, `$.bones[${i}].inverseBindMatrix`);
  });
  const groups = requiredArray(mesh.drawGroups, '$.drawGroups');
  const ids = new Set();
  groups.forEach((g, i) => {
    requiredObject(g, `$.drawGroups[${i}]`);
    requiredString(g.groupId, `$.drawGroups[${i}].groupId`);
    if (ids.has(g.groupId)) fail('duplicate groupId', `$.drawGroups[${i}].groupId`);
    ids.add(g.groupId);
    requiredInteger(g.indexStart, `$.drawGroups[${i}].indexStart`, 0);
    requiredInteger(g.indexCount, `$.drawGroups[${i}].indexCount`, 0);
    requiredString(g.materialId, `$.drawGroups[${i}].materialId`);
    requiredInteger(g.order, `$.drawGroups[${i}].order`, 0);
  });
  return mesh;
}

export function assertMaterialsIR(materials) {
  requiredObject(materials, '$');
  if (materials.schema !== MATERIALS_SCHEMA) fail(`expected ${MATERIALS_SCHEMA}`, '$.schema');
  assertSupportedVersion(materials.schemaVersion);
  const list = requiredArray(materials.materials, '$.materials');
  const ids = new Set();
  list.forEach((m, i) => {
    requiredObject(m, `$.materials[${i}]`);
    requiredString(m.materialId, `$.materials[${i}].materialId`);
    if (ids.has(m.materialId)) fail('duplicate materialId', `$.materials[${i}].materialId`);
    ids.add(m.materialId);
    for (const key of ['baseTexture', 'normalTexture', 'emissiveTexture']) {
      if (m[key] !== null && m[key] !== undefined) {
        assertRelativePackPath(m[key], `$.materials[${i}].${key}`);
      }
    }
    if (!['opaque', 'mask', 'blend', 'UNKNOWN'].includes(m.alphaMode)) fail('invalid alphaMode', `$.materials[${i}].alphaMode`);
    if (m.alphaMode === 'mask') {
      requiredNumber(m.alphaCutoff, `$.materials[${i}].alphaCutoff`);
      if (m.alphaCutoff < 0 || m.alphaCutoff > 1) fail('expected alphaCutoff in [0, 1]', `$.materials[${i}].alphaCutoff`);
    }
    if (!['none', 'front', 'back', 'UNKNOWN'].includes(m.cullMode)) fail('invalid cullMode', `$.materials[${i}].cullMode`);
    const depth = requiredObject(m.depth, `$.materials[${i}].depth`);
    requiredString(depth.testFunction, `$.materials[${i}].depth.testFunction`);
    assertBooleanOrUnknown(depth.write, `$.materials[${i}].depth.write`);
    const blend = requiredObject(m.blend, `$.materials[${i}].blend`);
    assertBooleanOrUnknown(blend.enabled, `$.materials[${i}].blend.enabled`);
    requiredString(blend.equation, `$.materials[${i}].blend.equation`);
    requiredString(blend.srcFactor, `$.materials[${i}].blend.srcFactor`);
    requiredString(blend.dstFactor, `$.materials[${i}].blend.dstFactor`);
    assertBooleanOrUnknown(m.emissive, `$.materials[${i}].emissive`);
    assertBooleanOrUnknown(m.fullbright, `$.materials[${i}].fullbright`);
    requiredObject(m.sampler, `$.materials[${i}].sampler`);
    requiredString(m.vertexTint, `$.materials[${i}].vertexTint`);
    assertBooleanOrUnknown(m.lightmap, `$.materials[${i}].lightmap`);
    assertBooleanOrUnknown(m.overlay, `$.materials[${i}].overlay`);
    const fogMode = requiredString(m.fogMode, `$.materials[${i}].fogMode`);
    if (!['colorMixPreserveAlpha', 'rgbaFade', 'UNKNOWN'].includes(fogMode)) {
      fail('invalid fogMode', `$.materials[${i}].fogMode`);
    }

    const replay = requiredObject(m.replay, `$.materials[${i}].replay`);
    const replayStatus = requiredString(replay.status, `$.materials[${i}].replay.status`);
    if (!['measured', 'UNKNOWN'].includes(replayStatus)) {
      fail('invalid replay status', `$.materials[${i}].replay.status`);
    }
    if (replayStatus === 'measured') {
      const lighting = requiredObject(replay.vertexLighting, `$.materials[${i}].replay.vertexLighting`);
      if (!['dualDirectionalDiffuse', 'none'].includes(lighting.mode)) {
        fail('unsupported replay vertex lighting mode', `$.materials[${i}].replay.vertexLighting.mode`);
      }
      for (const key of ['power', 'ambient', 'clampMax']) {
        requiredNumber(lighting[key], `$.materials[${i}].replay.vertexLighting.${key}`);
      }
      if (lighting.power < 0 || lighting.ambient < 0 || lighting.clampMax <= 0) {
        fail('invalid replay lighting constants', `$.materials[${i}].replay.vertexLighting`);
      }
      if (!['modelViewInverseViewRotationShape', 'modelViewLength'].includes(replay.fogDistance)) {
        fail('unsupported replay fog distance', `$.materials[${i}].replay.fogDistance`);
      }
      if (replay.textureCombine !== 'sample0TimesVertexTimesShaderColor') {
        fail('unsupported replay texture combine', `$.materials[${i}].replay.textureCombine`);
      }
      if (!['none', 'sampler0Alpha'].includes(replay.alphaDiscardSource)) {
        fail('unsupported replay alpha discard source', `$.materials[${i}].replay.alphaDiscardSource`);
      }
      if (!['none', 'rgbMixByOverlayAlpha'].includes(replay.overlayCombine)) {
        fail('unsupported replay overlay combine', `$.materials[${i}].replay.overlayCombine`);
      }
      if (!['none', 'multiplyRgba'].includes(replay.lightmapCombine)) {
        fail('unsupported replay lightmap combine', `$.materials[${i}].replay.lightmapCombine`);
      }
    }
  });
  return materials;
}

export function assertRenderFrameIR(frame) {
  requiredObject(frame, '$');
  if (frame.schema !== RENDER_FRAME_SCHEMA) fail(`expected ${RENDER_FRAME_SCHEMA}`, '$.schema');
  assertSupportedVersion(frame.schemaVersion);
  requiredString(frame.runId, '$.runId');
  requiredString(frame.entityUuid, '$.entityUuid');
  if (!UUID_LIKE_RE.test(frame.entityUuid)) fail('expected UUID-like stable entity id', '$.entityUuid');
  requiredInteger(frame.renderSequence, '$.renderSequence', 0);
  requiredInteger(frame.gameTime, '$.gameTime');
  requiredNumber(frame.partialTick, '$.partialTick');
  if (frame.partialTick < 0 || frame.partialTick > 1) fail('expected partialTick in [0, 1]', '$.partialTick');
  requiredString(frame.modelId, '$.modelId');
  assertHash(frame.packHash, '$.packHash');
  assertHash(frame.layoutHash, '$.layoutHash');

  const source = requiredObject(frame.source, '$.source');
  if (!SOURCE_TYPES.includes(source.type)) fail('unknown source.type', '$.source.type');
  if (!SOURCE_AUTHORITY.includes(source.authority)) fail('unknown source.authority', '$.source.authority');
  if (source.authority !== EXPECTED_AUTHORITY[source.type]) {
    fail(`source '${source.type}' requires authority '${EXPECTED_AUTHORITY[source.type]}'`, '$.source.authority');
  }
  if (source.fidelityTier !== SOURCE_FIDELITY_RANK[source.type]) {
    fail(`source '${source.type}' requires fidelityTier ${SOURCE_FIDELITY_RANK[source.type]}`, '$.source.fidelityTier');
  }

  assertMatrix16(frame.modelToWorldMatrix, '$.modelToWorldMatrix');

  const deformation = requiredObject(frame.deformation, '$.deformation');
  if (deformation.type === 'skinMatrices') {
    const mats = requiredArray(deformation.matrices, '$.deformation.matrices');
    mats.forEach((m, i) => assertMatrix16(m, `$.deformation.matrices[${i}]`));
  } else if (deformation.type === 'finalVertices') {
    requiredString(deformation.bufferRef, '$.deformation.bufferRef');
    requiredInteger(deformation.vertexCount, '$.deformation.vertexCount', 0);
  } else {
    fail("deformation.type must be 'skinMatrices' or 'finalVertices'; legacyPalette is not a renderer input", '$.deformation.type');
  }

  if (source.type === 'runtimeFinalVertex' && deformation.type !== 'finalVertices') {
    fail("runtimeFinalVertex requires deformation.type 'finalVertices'", '$.deformation.type');
  }
  if (source.type === 'runtimeFinalVertex') {
    assertSizedVector(frame.modelNormalToWorldMatrix, 9, '$.modelNormalToWorldMatrix');
    if (source.auxiliarySamplerInputs !== RUNTIME_FINAL_VERTEX_AUXILIARY_INPUTS) {
      fail(`runtimeFinalVertex requires auxiliarySamplerInputs '${RUNTIME_FINAL_VERTEX_AUXILIARY_INPUTS}'`,
        '$.source.auxiliarySamplerInputs');
    }
    if (deformation.format !== RUNTIME_FINAL_VERTEX_FORMAT) {
      fail(`runtimeFinalVertex requires format '${RUNTIME_FINAL_VERTEX_FORMAT}'`, '$.deformation.format');
    }
    if (deformation.strideFloats !== RUNTIME_FINAL_VERTEX_STRIDE_FLOATS) {
      fail(`runtimeFinalVertex requires strideFloats ${RUNTIME_FINAL_VERTEX_STRIDE_FLOATS}`,
        '$.deformation.strideFloats');
    }
  }
  if (['runtimeMatrix', 'runtimePaletteConverted'].includes(source.type) && deformation.type !== 'skinMatrices') {
    fail(`${source.type} requires deformation.type 'skinMatrices'`, '$.deformation.type');
  }

  if (frame.globalShaderState !== undefined) {
    assertGlobalShaderState(frame.globalShaderState, '$.globalShaderState');
  } else if (source.type === 'runtimeFinalVertex') {
    fail('runtimeFinalVertex requires captured globalShaderState', '$.globalShaderState');
  }

  if (frame.goldenBinding !== undefined) {
    if (source.type !== 'runtimeFinalVertex' || source.authority !== 'authoritative') {
      fail('Golden binding is only valid for authoritative runtimeFinalVertex frames', '$.goldenBinding');
    }
    assertGoldenBinding(frame.goldenBinding, frame);
  }

  const visibility = requiredObject(frame.visibility, '$.visibility');
  const boneVisibility = requiredArray(visibility.bones, '$.visibility.bones');
  boneVisibility.forEach((v, i) => {
    if (typeof v !== 'boolean') fail('expected boolean', `$.visibility.bones[${i}]`);
  });
  if (source.type === 'runtimeFinalVertex' && boneVisibility.length === 0
      && visibility.bonesResolvedInFinalVertices !== true) {
    fail('empty bone visibility for runtimeFinalVertex requires bonesResolvedInFinalVertices=true',
      '$.visibility.bonesResolvedInFinalVertices');
  }
  requiredArray(visibility.groups, '$.visibility.groups').forEach((v, i) => {
    if (typeof v !== 'boolean') fail('expected boolean', `$.visibility.groups[${i}]`);
  });

  const drawOrder = requiredArray(frame.drawOrder, '$.drawOrder');
  drawOrder.forEach((v, i) => requiredString(v, `$.drawOrder[${i}]`));
  const drawStates = requiredObject(frame.drawStates, '$.drawStates');
  drawOrder.forEach((groupId) => {
    if (!Object.hasOwn(drawStates, groupId)) fail('missing draw state for resolved draw group', `$.drawStates.${groupId}`);
    const drawState = requiredObject(drawStates[groupId], `$.drawStates.${groupId}`);
    if (source.type === 'runtimeFinalVertex') {
      for (const key of [
        'vertexColorInBuffer',
        'overlayCoordinatesInBuffer',
        'lightCoordinatesInBuffer',
        'resolvedOverlayColorInBuffer',
        'resolvedLightmapColorInBuffer',
      ]) {
        if (drawState[key] !== true) {
          fail(`runtimeFinalVertex requires ${key}=true`, `$.drawStates.${groupId}.${key}`);
        }
      }
    }
  });
  assertNoForbiddenAuthoritativeKeys(frame);
  return frame;
}

export function assertFrameCompatible(frame, manifest) {
  assertRenderPackManifest(manifest);
  assertRenderFrameIR(frame);
  if (frame.modelId !== manifest.modelId) fail('frame modelId does not match Render Pack', '$.modelId');
  if (frame.packHash !== manifest.packHash) fail('frame packHash does not match Render Pack', '$.packHash');
  if (frame.layoutHash !== manifest.layoutHash) fail('frame layoutHash does not match Render Pack', '$.layoutHash');
  return true;
}

export function compareSourcePriority(a, b) {
  assertRenderFrameIR(a);
  assertRenderFrameIR(b);
  return SOURCE_FIDELITY_RANK[a.source.type] - SOURCE_FIDELITY_RANK[b.source.type];
}

function canonicalize(value) {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (!isObject(value)) return value;
  const out = {};
  for (const key of Object.keys(value).sort()) out[key] = canonicalize(value[key]);
  return out;
}

export function canonicalPackIdentityPayload(manifest) {
  const clone = structuredClone(manifest);
  delete clone.packHash;
  delete clone.generatedAt;
  if (Array.isArray(clone.files)) clone.files.sort((a, b) => String(a.path).localeCompare(String(b.path)));
  return JSON.stringify(canonicalize(clone));
}

export function computePackHash(manifestWithoutTrustedHash) {
  const payload = canonicalPackIdentityPayload(manifestWithoutTrustedHash);
  return `sha256:${createHash('sha256').update(payload).digest('hex')}`;
}