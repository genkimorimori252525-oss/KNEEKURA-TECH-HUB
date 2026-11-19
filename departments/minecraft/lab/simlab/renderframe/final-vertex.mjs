import { createHash } from 'node:crypto';
import { lstat, mkdir, mkdtemp, readFile, realpath, rename, rm, writeFile } from 'node:fs/promises';
import { dirname, isAbsolute, join, resolve, sep } from 'node:path';
import { assertFrameCompatible } from '../contracts/render-v1/validator.mjs';
import { validateGoldenCaptureJson } from '../golden/capture-bundle.mjs';
import {
  COORDINATE_SYSTEM,
  RENDER_FRAME_SCHEMA,
  RUNTIME_FINAL_VERTEX_AUXILIARY_INPUTS,
  RUNTIME_FINAL_VERTEX_FORMAT,
  RUNTIME_FINAL_VERTEX_STRIDE_FLOATS,
  SCHEMA_VERSION,
} from '../contracts/render-v1/constants.mjs';
import { loadRenderPack } from '../renderpack/loader.mjs';

export const RAW_FINAL_VERTEX_SCHEMA = 'kneekura.runtime-final-vertex-capture';
export const RAW_FINAL_VERTEX_VERSION = 2;
export const FINAL_VERTEX_STRIDE_FLOATS = RUNTIME_FINAL_VERTEX_STRIDE_FLOATS;
export const FINAL_VERTEX_FORMAT = RUNTIME_FINAL_VERTEX_FORMAT;

const OVERLAY_COLOR_OFFSET = 16;
const LIGHTMAP_COLOR_OFFSET = 20;

const SAFE_PRIMITIVE_MODES = new Set([
  'LINES',
  'LINE_STRIP',
  'DEBUG_LINES',
  'DEBUG_LINE_STRIP',
  'TRIANGLES',
  'TRIANGLE_STRIP',
  'TRIANGLE_FAN',
  'QUADS',
]);

export class FinalVertexFrameError extends Error {
  constructor(message, path = '$') {
    super(`${path}: ${message}`);
    this.name = 'FinalVertexFrameError';
    this.path = path;
  }
}

function fail(message, path = '$') {
  throw new FinalVertexFrameError(message, path);
}

function isObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function reqObject(value, path) {
  if (!isObject(value)) fail('expected object', path);
  return value;
}

function reqArray(value, path) {
  if (!Array.isArray(value)) fail('expected array', path);
  return value;
}

function reqString(value, path) {
  if (typeof value !== 'string' || value.length === 0) fail('expected non-empty string', path);
  return value;
}

function reqInteger(value, path, min = 0) {
  if (!Number.isSafeInteger(value) || value < min) fail(`expected safe integer >= ${min}`, path);
  return value;
}

function reqNumber(value, path) {
  if (typeof value !== 'number' || !Number.isFinite(value)) fail('expected finite number', path);
  return value;
}

function safeRelative(path, at) {
  reqString(path, at);
  if (isAbsolute(path) || /^[A-Za-z]:[\\/]/.test(path)) fail('absolute path forbidden', at);
  const clean = path.replaceAll('\\', '/');
  const parts = clean.split('/');
  if (parts.some((part) => part === '' || part === '.' || part === '..')) fail('unsafe relative path', at);
  return clean;
}

function inside(root, relative, at) {
  const clean = safeRelative(relative, at);
  const absRoot = resolve(root);
  const abs = resolve(absRoot, clean);
  if (abs !== absRoot && !abs.startsWith(absRoot + sep)) fail('path escapes capture root', at);
  return abs;
}

async function readRegularInside(root, relative, at) {
  const abs = inside(root, relative, at);
  const stat = await lstat(abs);
  if (stat.isSymbolicLink()) fail('symbolic-link input forbidden', at);
  if (!stat.isFile()) fail('expected regular file', at);
  const rootReal = await realpath(root);
  const fileReal = await realpath(abs);
  if (fileReal !== rootReal && !fileReal.startsWith(rootReal + sep)) fail('resolved path escapes capture root', at);
  return readFile(fileReal);
}

function sha256(bytes) {
  return `sha256:${createHash('sha256').update(bytes).digest('hex')}`;
}

function safeSegment(value, at) {
  const raw = reqString(value, at);
  const clean = raw.replace(/[^A-Za-z0-9._-]+/g, '_').replace(/^_+|_+$/g, '');
  if (!clean || clean === '.' || clean === '..') fail('cannot derive safe path segment', at);
  return clean.slice(0, 120);
}

function validateMatrix16(value, at) {
  const a = reqArray(value, at);
  if (a.length !== 16) fail('expected 16 values', at);
  a.forEach((x, i) => reqNumber(x, `${at}[${i}]`));
  return a;
}

function validateSizedVector(value, size, at) {
  const a = reqArray(value, at);
  if (a.length !== size) fail(`expected ${size} values`, at);
  a.forEach((x, i) => reqNumber(x, `${at}[${i}]`));
  return a;
}

function validateAuxiliarySamplerEvidence(value, at) {
  const evidence = reqObject(value, at);
  if (evidence.status !== 'resolved-per-vertex-rgba') {
    fail("auxiliary sampler evidence must be 'resolved-per-vertex-rgba'", `${at}.status`);
  }
  if (evidence.componentEncoding !== 'UNORM8_RGBA_TO_FLOAT32') {
    fail('unexpected auxiliary sampler component encoding', `${at}.componentEncoding`);
  }

  const overlay = reqObject(evidence.overlay, `${at}.overlay`);
  reqInteger(overlay.width, `${at}.overlay.width`, 1);
  reqInteger(overlay.height, `${at}.overlay.height`, 1);
  if (overlay.coordinateRule !== 'directIntegerTexel') {
    fail('unexpected overlay coordinate rule', `${at}.overlay.coordinateRule`);
  }

  const lightmap = reqObject(evidence.lightmap, `${at}.lightmap`);
  reqInteger(lightmap.width, `${at}.lightmap.width`, 1);
  reqInteger(lightmap.height, `${at}.lightmap.height`, 1);
  if (lightmap.coordinateRule !== 'integerDivide16Texel') {
    fail('unexpected lightmap coordinate rule', `${at}.lightmap.coordinateRule`);
  }
  return evidence;
}

function validateFinalVertexBuffer(bytes, vertexCount, at) {
  const expectedFloats = vertexCount * FINAL_VERTEX_STRIDE_FLOATS;
  if (bytes.length !== expectedFloats * 4) {
    fail(`vertex buffer byteLength ${bytes.length} does not equal expected ${expectedFloats * 4}`, at);
  }

  for (let vertex = 0; vertex < vertexCount; vertex++) {
    const base = vertex * FINAL_VERTEX_STRIDE_FLOATS;
    for (let component = 0; component < FINAL_VERTEX_STRIDE_FLOATS; component++) {
      const value = bytes.readFloatLE((base + component) * 4);
      if (!Number.isFinite(value)) {
        fail('final-vertex buffer contains non-finite float', `${at}#vertex[${vertex}][${component}]`);
      }
    }

    for (let component = 12; component < 16; component++) {
      const value = bytes.readFloatLE((base + component) * 4);
      if (!Number.isInteger(value)) {
        fail('captured auxiliary sampler coordinates must remain integers',
          `${at}#vertex[${vertex}][${component}]`);
      }
    }

    for (const start of [OVERLAY_COLOR_OFFSET, LIGHTMAP_COLOR_OFFSET]) {
      for (let component = 0; component < 4; component++) {
        const value = bytes.readFloatLE((base + start + component) * 4);
        if (value < 0 || value > 1) {
          fail('resolved auxiliary sampler color must be normalized to [0,1]',
            `${at}#vertex[${vertex}][${start + component}]`);
        }
      }
    }
  }
  return bytes;
}

function validateGlobalShaderState(value, at) {
  const state = reqObject(value, at);
  if (state.matrixConvention !== 'JOML_COLUMN_MAJOR_COLUMN_VECTOR') {
    fail('unexpected matrix convention', `${at}.matrixConvention`);
  }
  validateMatrix16(state.modelViewMatrix, `${at}.modelViewMatrix`);
  validateMatrix16(state.projectionMatrix, `${at}.projectionMatrix`);
  validateSizedVector(state.inverseViewRotationMatrix, 9, `${at}.inverseViewRotationMatrix`);

  const lights = reqArray(state.directionalLights, `${at}.directionalLights`);
  if (lights.length !== 2) fail('expected exactly 2 directional lights', `${at}.directionalLights`);
  lights.forEach((light, i) => validateSizedVector(light, 3, `${at}.directionalLights[${i}]`));

  validateSizedVector(state.shaderColor, 4, `${at}.shaderColor`);

  const fog = reqObject(state.fog, `${at}.fog`);
  if (fog.curve !== 'smoothstep') fail("fog.curve must be 'smoothstep'", `${at}.fog.curve`);
  reqNumber(fog.start, `${at}.fog.start`);
  reqNumber(fog.end, `${at}.fog.end`);
  validateSizedVector(fog.color, 4, `${at}.fog.color`);
  if (!['sphere', 'cylinder'].includes(fog.shape)) fail('unsupported fog shape', `${at}.fog.shape`);
  if (fog.distanceSpace !== 'modelView') fail("fog.distanceSpace must be 'modelView'", `${at}.fog.distanceSpace`);
  return state;
}

function assertReplayCompleteMaterial(material, at) {
  reqObject(material, at);
  const alphaMode = reqString(material.alphaMode, `${at}.alphaMode`);
  if (alphaMode === 'UNKNOWN') fail('authoritative replay requires measured alphaMode', `${at}.alphaMode`);
  if (!['opaque', 'mask', 'blend'].includes(alphaMode)) fail('unsupported alphaMode', `${at}.alphaMode`);
  if (alphaMode === 'mask' && material.alphaCutoff == null) {
    fail('mask alphaMode requires measured alphaCutoff', `${at}.alphaCutoff`);
  }
  if (material.alphaCutoff != null) {
    const cutoff = reqNumber(material.alphaCutoff, `${at}.alphaCutoff`);
    if (cutoff < 0 || cutoff > 1) fail('alphaCutoff must be in [0,1]', `${at}.alphaCutoff`);
  }

  const blend = reqObject(material.blend, `${at}.blend`);
  if (typeof blend.enabled !== 'boolean') fail('authoritative replay requires measured blend.enabled', `${at}.blend.enabled`);
  if (blend.enabled) {
    for (const key of ['equation', 'srcFactor', 'dstFactor']) {
      const value = reqString(blend[key], `${at}.blend.${key}`);
      if (value === 'UNKNOWN') fail(`authoritative replay requires measured blend.${key}`, `${at}.blend.${key}`);
    }
  }

  const cullMode = reqString(material.cullMode, `${at}.cullMode`);
  if (cullMode === 'UNKNOWN') fail('authoritative replay requires measured cullMode', `${at}.cullMode`);

  const depth = reqObject(material.depth, `${at}.depth`);
  const depthTest = reqString(depth.testFunction, `${at}.depth.testFunction`);
  if (depthTest === 'UNKNOWN') fail('authoritative replay requires measured depth test', `${at}.depth.testFunction`);
  if (typeof depth.write !== 'boolean') fail('authoritative replay requires measured depth.write', `${at}.depth.write`);

  for (const key of ['emissive', 'fullbright', 'lightmap', 'overlay']) {
    if (typeof material[key] !== 'boolean') fail(`authoritative replay requires measured ${key}`, `${at}.${key}`);
  }

  const sampler = reqObject(material.sampler, `${at}.sampler`);
  if (sampler.status !== 'measured') {
    fail('authoritative replay requires measured sampler state', `${at}.sampler.status`);
  }
  if (typeof sampler.bilinear !== 'boolean') {
    fail('authoritative replay requires measured sampler.bilinear', `${at}.sampler.bilinear`);
  }
  if (typeof sampler.mipmap !== 'boolean') {
    fail('authoritative replay requires measured sampler.mipmap', `${at}.sampler.mipmap`);
  }

  const vertexTint = reqString(material.vertexTint, `${at}.vertexTint`);
  if (vertexTint === 'UNKNOWN') fail('authoritative replay requires measured vertexTint semantics', `${at}.vertexTint`);

  const fogMode = reqString(material.fogMode, `${at}.fogMode`);
  if (fogMode === 'UNKNOWN') fail('authoritative replay requires measured fogMode', `${at}.fogMode`);
  if (!['colorMixPreserveAlpha', 'rgbaFade'].includes(fogMode)) {
    fail('unsupported fogMode', `${at}.fogMode`);
  }
  const replay = reqObject(material.replay, `${at}.replay`);
  if (replay.status !== 'measured') {
    fail('authoritative replay requires measured generic replay semantics', `${at}.replay.status`);
  }
  const lighting = reqObject(replay.vertexLighting, `${at}.replay.vertexLighting`);
  if (!['dualDirectionalDiffuse', 'none'].includes(reqString(lighting.mode, `${at}.replay.vertexLighting.mode`))) {
    fail('unsupported replay vertex lighting mode', `${at}.replay.vertexLighting.mode`);
  }
  for (const key of ['power', 'ambient', 'clampMax']) reqNumber(lighting[key], `${at}.replay.vertexLighting.${key}`);
  if (lighting.power < 0 || lighting.ambient < 0 || lighting.clampMax <= 0) {
    fail('invalid replay lighting constants', `${at}.replay.vertexLighting`);
  }
  if (!['modelViewInverseViewRotationShape', 'modelViewLength'].includes(replay.fogDistance)) {
    fail('unsupported replay fog distance', `${at}.replay.fogDistance`);
  }
  if (replay.textureCombine !== 'sample0TimesVertexTimesShaderColor') {
    fail('unsupported replay texture combine', `${at}.replay.textureCombine`);
  }
  if (!['none', 'sampler0Alpha'].includes(replay.alphaDiscardSource)) {
    fail('unsupported replay alpha discard source', `${at}.replay.alphaDiscardSource`);
  }
  if (!['none', 'rgbMixByOverlayAlpha'].includes(replay.overlayCombine)) {
    fail('unsupported replay overlay combine', `${at}.replay.overlayCombine`);
  }
  if (!['none', 'multiplyRgba'].includes(replay.lightmapCombine)) {
    fail('unsupported replay lightmap combine', `${at}.replay.lightmapCombine`);
  }
  if (replay.overlayCombine === 'rgbMixByOverlayAlpha' && material.overlay !== true) {
    fail('replay overlay combine requires measured overlay participation', `${at}.replay.overlayCombine`);
  }
  if (replay.lightmapCombine === 'multiplyRgba' && material.lightmap !== true) {
    fail('replay lightmap combine requires measured lightmap participation', `${at}.replay.lightmapCombine`);
  }
  if (replay.lightmapCombine === 'multiplyRgba' && material.fullbright === true) {
    fail('fullbright material cannot multiply sampled lightmap in authoritative replay', `${at}.replay.lightmapCombine`);
  }
  if (replay.alphaDiscardSource === 'sampler0Alpha' && material.alphaCutoff == null) {
    fail('sampler0 alpha discard requires a measured alphaCutoff', `${at}.alphaCutoff`);
  }
  if (replay.alphaDiscardSource === 'none' && material.alphaMode === 'mask') {
    fail('mask alphaMode requires an explicit replay alpha discard source', `${at}.replay.alphaDiscardSource`);
  }
  return material;
}


const GOLDEN_BINDING_SCHEMA = 'kneekura.golden-frame-binding';
const GOLDEN_BINDING_VERSION = 1;

function exactNumberArrayEqual(a, b) {
  return Array.isArray(a) && Array.isArray(b) && a.length === b.length
    && a.every((value, i) => Object.is(value, b[i]));
}

function buildGoldenBinding(raw) {
  if (raw.golden == null) return null;
  validateGoldenCaptureJson(raw);
  const camera = raw.golden.camera;
  if (!exactNumberArrayEqual(camera.projectionMatrix, raw.globalShaderState.projectionMatrix)) {
    fail('Golden camera projection must exactly match captured global shader projection',
      '$.golden.camera.projectionMatrix');
  }
  return {
    schema: GOLDEN_BINDING_SCHEMA,
    schemaVersion: GOLDEN_BINDING_VERSION,
    identity: {
      runId: raw.runId,
      entityUuid: raw.entityUuid,
      renderSequence: raw.renderSequence,
      gameTime: raw.gameTime,
      partialTick: raw.partialTick,
    },
    renderTick: camera.renderTick,
    framebuffer: {
      width: camera.framebufferWidth,
      height: camera.framebufferHeight,
      viewportWidth: camera.viewportWidth,
      viewportHeight: camera.viewportHeight,
      windowWidth: camera.windowWidth,
      windowHeight: camera.windowHeight,
      guiScaledWidth: camera.guiScaledWidth,
      guiScaledHeight: camera.guiScaledHeight,
    },
    camera: {
      position: structuredClone(camera.position),
      xRot: camera.xRot,
      yRot: camera.yRot,
      rotationQuaternion: structuredClone(camera.rotationQuaternion),
      projectionMatrix: structuredClone(camera.projectionMatrix),
      matrixConvention: camera.matrixConvention,
    },
    backgroundDepth: structuredClone(raw.golden.backgroundDepth),
  };
}

function validateRaw(raw) {
  reqObject(raw, '$');
  if (raw.schema !== RAW_FINAL_VERTEX_SCHEMA) fail(`expected ${RAW_FINAL_VERTEX_SCHEMA}`, '$.schema');
  if (raw.schemaVersion !== RAW_FINAL_VERTEX_VERSION) fail(`expected schemaVersion ${RAW_FINAL_VERTEX_VERSION}`, '$.schemaVersion');
  reqString(raw.runId, '$.runId');
  if (raw.runBound !== true || raw.runId === 'unbound') {
    fail('authoritative final-vertex capture requires an explicitly bound tlm.sim.run', '$.runId');
  }
  reqString(raw.entityUuid, '$.entityUuid');
  reqInteger(raw.renderSequence, '$.renderSequence', 0);
  reqInteger(raw.gameTime, '$.gameTime', 0);
  reqNumber(raw.partialTick, '$.partialTick');
  if (raw.partialTick < 0 || raw.partialTick > 1) fail('partialTick must be in [0,1]', '$.partialTick');
  reqString(raw.modelId, '$.modelId');
  if (raw.coordinateSystem !== COORDINATE_SYSTEM) fail(`expected ${COORDINATE_SYSTEM}`, '$.coordinateSystem');
  if (raw.matrixConvention !== 'JOML_COLUMN_MAJOR_COLUMN_VECTOR') fail('unexpected matrix convention', '$.matrixConvention');
  if (raw.vertexFormat !== FINAL_VERTEX_FORMAT) fail(`expected ${FINAL_VERTEX_FORMAT}`, '$.vertexFormat');
  if (raw.strideFloats !== FINAL_VERTEX_STRIDE_FLOATS) fail(`expected stride ${FINAL_VERTEX_STRIDE_FLOATS}`, '$.strideFloats');
  validateMatrix16(raw.modelToWorldMatrix, '$.modelToWorldMatrix');
  validateSizedVector(raw.modelNormalToWorldMatrix, 9, '$.modelNormalToWorldMatrix');
  const globalColorMultiplier = reqArray(raw.globalColorMultiplier, '$.globalColorMultiplier');
  if (globalColorMultiplier.length !== 4) fail('expected RGBA multiplier with 4 values', '$.globalColorMultiplier');
  globalColorMultiplier.forEach((value, i) => reqNumber(value, `$.globalColorMultiplier[${i}]`));

  const globalShaderState = validateGlobalShaderState(raw.globalShaderState, '$.globalShaderState');
  for (let i = 0; i < 4; i++) {
    if (!Object.is(globalColorMultiplier[i], globalShaderState.shaderColor[i])) {
      fail('globalColorMultiplier must exactly match captured shaderColor',
        `$.globalShaderState.shaderColor[${i}]`);
    }
  }

  const source = reqObject(raw.source, '$.source');
  if (source.type !== 'runtimeFinalVertex') fail("source.type must be 'runtimeFinalVertex'", '$.source.type');
  if (source.authority !== 'authoritative') fail("source.authority must be 'authoritative'", '$.source.authority');
  if (source.fidelityTier !== 0) fail('runtimeFinalVertex fidelityTier must be 0', '$.source.fidelityTier');
  if (source.capturePoint !== 'same-geoRender-VertexConsumer-tee') fail('unexpected capture point', '$.source.capturePoint');
  if (source.outerPoseNormalization !== 'inverse-observed-PoseStack') fail('unexpected outer pose normalization', '$.source.outerPoseNormalization');
  if (source.auxiliarySamplerInputs !== RUNTIME_FINAL_VERTEX_AUXILIARY_INPUTS) {
    fail(`authoritative capture requires auxiliarySamplerInputs = '${RUNTIME_FINAL_VERTEX_AUXILIARY_INPUTS}'`,
      '$.source.auxiliarySamplerInputs');
  }
  validateAuxiliarySamplerEvidence(raw.auxiliarySamplerEvidence, '$.auxiliarySamplerEvidence');
  if (raw.golden != null) validateGoldenCaptureJson(raw);

  const groups = reqArray(raw.groups, '$.groups');
  if (groups.length === 0) fail('at least one non-empty group required', '$.groups');
  const ids = new Set();
  let counted = 0;
  groups.forEach((group, i) => {
    const at = `$.groups[${i}]`;
    reqObject(group, at);
    const id = reqString(group.groupId, `${at}.groupId`);
    if (ids.has(id)) fail('duplicate groupId in one render invocation is not representable by RenderPack v1', `${at}.groupId`);
    ids.add(id);
    if (group.order !== i) fail('group order must be contiguous and preserve actual draw order', `${at}.order`);
    safeRelative(group.file, `${at}.file`);
    if (group.strideFloats !== FINAL_VERTEX_STRIDE_FLOATS) fail('group stride mismatch', `${at}.strideFloats`);
    counted += reqInteger(group.vertexCount, `${at}.vertexCount`, 1);
    const primitive = reqString(group.primitiveMode, `${at}.primitiveMode`);
    if (!SAFE_PRIMITIVE_MODES.has(primitive)) fail(`unsupported/unknown primitive mode '${primitive}'`, `${at}.primitiveMode`);
    reqString(group.sourceRenderType, `${at}.sourceRenderType`);
    reqString(group.textureResourceId, `${at}.textureResourceId`);
    assertReplayCompleteMaterial(group.material, `${at}.material`);
  });
  if (raw.vertexCount !== counted) fail(`vertexCount ${raw.vertexCount} does not equal group total ${counted}`, '$.vertexCount');
  return raw;
}

function materialById(pack) {
  return new Map(pack.materials.materials.map((material) => [material.materialId, material]));
}

function groupById(pack) {
  return new Map(pack.mesh.drawGroups.map((group) => [group.groupId, group]));
}

export async function compileFinalVertexRenderFrame({ captureDir, packDir, outputRoot }) {
  reqString(captureDir, '$compile.captureDir');
  reqString(packDir, '$compile.packDir');
  reqString(outputRoot, '$compile.outputRoot');

  const captureRoot = await realpath(resolve(captureDir));
  const raw = validateRaw(JSON.parse((await readRegularInside(captureRoot, 'capture.json', '$.capture')).toString('utf8')));
  const pack = await loadRenderPack(packDir);

  if (raw.modelId !== pack.manifest.modelId) fail('raw capture modelId does not match Render Pack', '$.modelId');

  const packGroups = [...pack.mesh.drawGroups].sort((a, b) => a.order - b.order);
  const packGroupIds = new Set(packGroups.map((group) => group.groupId));
  const packGroupsById = groupById(pack);
  const materialsById = materialById(pack);
  const seen = new Set();

  const groupBuffers = [];
  const drawOrder = [];
  const drawStates = {};
  let totalVertices = 0;
  let totalBytes = 0;

  for (let i = 0; i < raw.groups.length; i++) {
    const group = raw.groups[i];
    const at = `$.groups[${i}]`;
    if (!packGroupIds.has(group.groupId)) fail('runtime group does not exist in Render Pack', `${at}.groupId`);
    const staticGroup = packGroupsById.get(group.groupId);
    const material = materialsById.get(staticGroup.materialId);
    if (!material) fail('Render Pack group references missing material', `${at}.groupId`);
    if (group.sourceRenderType !== staticGroup.sourceRenderType) {
      fail('runtime sourceRenderType does not match Render Pack group provenance', `${at}.sourceRenderType`);
    }

    const expectedTexture = material.sourceTextureResourceId ?? null;
    if (expectedTexture == null) {
      fail('Render Pack lacks sourceTextureResourceId evidence required for authoritative texture matching', `${at}.textureResourceId`);
    }
    if (group.textureResourceId !== expectedTexture) {
      fail(`runtime texture '${group.textureResourceId}' does not match Render Pack source '${expectedTexture}'`, `${at}.textureResourceId`);
    }

    const bytes = await readRegularInside(captureRoot, group.file, `${at}.file`);
    validateFinalVertexBuffer(bytes, group.vertexCount, `${at}.file`);

    groupBuffers.push(bytes);
    drawOrder.push(group.groupId);
    drawStates[group.groupId] = {
      visible: true,
      primitiveMode: group.primitiveMode,
      sourceRenderType: group.sourceRenderType,
      textureResourceId: group.textureResourceId,
      material: structuredClone(group.material),
      colorMultiplier: structuredClone(raw.globalColorMultiplier),
      vertexStart: totalVertices,
      vertexCount: group.vertexCount,
      vertexColorInBuffer: true,
      overlayCoordinatesInBuffer: true,
      lightCoordinatesInBuffer: true,
      resolvedOverlayColorInBuffer: true,
      resolvedLightmapColorInBuffer: true,
    };
    seen.add(group.groupId);
    totalVertices += group.vertexCount;
    totalBytes += bytes.length;
  }

  const combined = Buffer.concat(groupBuffers, totalBytes);
  const bufferHash = sha256(combined);
  const goldenBinding = buildGoldenBinding(raw);
  const visibilityGroups = packGroups.map((group) => seen.has(group.groupId));

  const frame = {
    schema: RENDER_FRAME_SCHEMA,
    schemaVersion: SCHEMA_VERSION,
    runId: raw.runId,
    entityUuid: raw.entityUuid,
    renderSequence: raw.renderSequence,
    gameTime: raw.gameTime,
    partialTick: raw.partialTick,
    modelId: raw.modelId,
    packHash: pack.manifest.packHash,
    layoutHash: pack.manifest.layoutHash,
    source: {
      ...structuredClone(raw.source),
      rawCaptureSchema: raw.schema,
      rawCaptureVersion: raw.schemaVersion,
    },
    modelToWorldMatrix: structuredClone(raw.modelToWorldMatrix),
    modelNormalToWorldMatrix: structuredClone(raw.modelNormalToWorldMatrix),
    globalShaderState: structuredClone(raw.globalShaderState),
    ...(goldenBinding == null ? {} : { goldenBinding }),
    deformation: {
      type: 'finalVertices',
      bufferRef: 'frame.bin',
      vertexCount: totalVertices,
      strideFloats: FINAL_VERTEX_STRIDE_FLOATS,
      format: FINAL_VERTEX_FORMAT,
      sha256: bufferHash,
      groups: raw.groups.map((group) => ({
        groupId: group.groupId,
        order: group.order,
        vertexStart: drawStates[group.groupId].vertexStart,
        vertexCount: group.vertexCount,
        primitiveMode: group.primitiveMode,
      })),
    },
    visibility: {
      bones: [],
      bonesResolvedInFinalVertices: true,
      groups: visibilityGroups,
    },
    drawOrder,
    drawStates,
  };

  assertFrameCompatible(frame, pack.manifest);

  const resolvedOutputRoot = resolve(outputRoot);
  await mkdir(resolvedOutputRoot, { recursive: true });
  const tempParent = await mkdtemp(join(resolvedOutputRoot, '.kneekura-renderframe-'));
  const tempDir = join(tempParent, 'frame');
  await mkdir(tempDir, { recursive: true });
  try {
    await writeFile(join(tempDir, 'frame.bin'), combined);
    await writeFile(join(tempDir, 'frame.json'), JSON.stringify(frame, null, 2) + '\n', 'utf8');

    const finalDir = join(
      resolvedOutputRoot,
      safeSegment(raw.runId, '$.runId'),
      safeSegment(raw.entityUuid, '$.entityUuid'),
      String(raw.renderSequence).padStart(12, '0'),
    );
    await mkdir(dirname(finalDir), { recursive: true });
    try {
      await rename(tempDir, finalDir);
    } catch (error) {
      if (error?.code !== 'EEXIST' && error?.code !== 'ENOTEMPTY') throw error;
      const existingJson = JSON.parse((await readFile(join(finalDir, 'frame.json'))).toString('utf8'));
      const existingBin = await readFile(join(finalDir, 'frame.bin'));
      if (JSON.stringify(existingJson) !== JSON.stringify(frame) || sha256(existingBin) !== bufferHash) {
        fail('deterministic frame destination already exists with different content', '$compile.outputRoot');
      }
    }

    return { frameDir: finalDir, frame, bufferHash };
  } finally {
    await rm(tempParent, { recursive: true, force: true });
  }
}