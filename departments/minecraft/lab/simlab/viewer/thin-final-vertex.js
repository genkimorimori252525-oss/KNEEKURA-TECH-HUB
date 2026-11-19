export const FINAL_VERTEX_FORMAT = 'KNEEKURA_FINAL_VERTEX_V2';
export const FINAL_VERTEX_STRIDE_FLOATS = 24;
export const FINAL_VERTEX_STRIDE_BYTES = FINAL_VERTEX_STRIDE_FLOATS * 4;

export const FINAL_VERTEX_ATTRIBUTES = Object.freeze([
  { name: 'aPosition', offsetFloats: 0, components: 3 },
  { name: 'aUv', offsetFloats: 3, components: 2 },
  { name: 'aNormal', offsetFloats: 5, components: 3 },
  { name: 'aColor', offsetFloats: 8, components: 4 },
  { name: 'aOverlayColor', offsetFloats: 16, components: 4 },
  { name: 'aLightmapColor', offsetFloats: 20, components: 4 },
]);

export class ThinFinalVertexReplayError extends Error {
  constructor(message, path = '$') {
    super(`${path}: ${message}`);
    this.name = 'ThinFinalVertexReplayError';
    this.path = path;
  }
}

function fail(message, path = '$') { throw new ThinFinalVertexReplayError(message, path); }
function isObject(v) { return v !== null && typeof v === 'object' && !Array.isArray(v); }
function obj(v, path) { if (!isObject(v)) fail('expected object', path); return v; }
function arr(v, path, n = null) {
  if (!Array.isArray(v)) fail('expected array', path);
  if (n !== null && v.length !== n) fail(`expected ${n} values`, path);
  return v;
}
function finite(v, path) { if (typeof v !== 'number' || !Number.isFinite(v)) fail('expected finite number', path); return v; }
function str(v, path) { if (typeof v !== 'string' || !v) fail('expected non-empty string', path); return v; }
function int(v, path, min = 0) { if (!Number.isSafeInteger(v) || v < min) fail(`expected integer >= ${min}`, path); return v; }
function bool(v, path) { if (typeof v !== 'boolean') fail('expected boolean', path); return v; }
function vec(v, n, path) { const a = arr(v, path, n); a.forEach((x, i) => finite(x, `${path}[${i}]`)); return a; }
function clone(v) { return structuredClone(v); }

function validateReplayMaterial(material, path) {
  const m = obj(material, path);
  if (m.replay?.status !== 'measured') fail('generic replay semantics are not measured', `${path}.replay.status`);
  const replay = obj(m.replay, `${path}.replay`);
  const lighting = obj(replay.vertexLighting, `${path}.replay.vertexLighting`);
  if (!['dualDirectionalDiffuse', 'none'].includes(lighting.mode)) fail('unsupported vertex lighting mode', `${path}.replay.vertexLighting.mode`);
  for (const key of ['power', 'ambient', 'clampMax']) finite(lighting[key], `${path}.replay.vertexLighting.${key}`);
  if (lighting.power < 0 || lighting.ambient < 0 || lighting.clampMax <= 0) fail('invalid lighting constants', `${path}.replay.vertexLighting`);
  if (!['modelViewInverseViewRotationShape', 'modelViewLength'].includes(replay.fogDistance)) fail('unsupported fog distance', `${path}.replay.fogDistance`);
  if (replay.textureCombine !== 'sample0TimesVertexTimesShaderColor') fail('unsupported texture combine', `${path}.replay.textureCombine`);
  if (!['none', 'sampler0Alpha'].includes(replay.alphaDiscardSource)) fail('unsupported alpha discard source', `${path}.replay.alphaDiscardSource`);
  if (!['none', 'rgbMixByOverlayAlpha'].includes(replay.overlayCombine)) fail('unsupported overlay combine', `${path}.replay.overlayCombine`);
  if (!['none', 'multiplyRgba'].includes(replay.lightmapCombine)) fail('unsupported lightmap combine', `${path}.replay.lightmapCombine`);
  if (!['colorMixPreserveAlpha', 'rgbaFade'].includes(m.fogMode)) fail('unsupported fog mode', `${path}.fogMode`);
  if (!['opaque', 'mask', 'blend'].includes(m.alphaMode)) fail('unsupported alpha mode', `${path}.alphaMode`);
  if (m.alphaCutoff != null) { finite(m.alphaCutoff, `${path}.alphaCutoff`); if (m.alphaCutoff < 0 || m.alphaCutoff > 1) fail('alpha cutoff out of range', `${path}.alphaCutoff`); }
  if (replay.alphaDiscardSource === 'sampler0Alpha' && m.alphaCutoff == null) fail('sample alpha discard requires alphaCutoff', `${path}.alphaCutoff`);
  if (replay.overlayCombine !== 'none' && m.overlay !== true) fail('overlay combine requires overlay participation', `${path}.overlay`);
  if (replay.lightmapCombine !== 'none' && m.lightmap !== true) fail('lightmap combine requires lightmap participation', `${path}.lightmap`);
  const sampler = obj(m.sampler, `${path}.sampler`);
  if (sampler.status !== 'measured') fail('base texture sampler state is not measured', `${path}.sampler.status`);
  bool(sampler.bilinear, `${path}.sampler.bilinear`);
  bool(sampler.mipmap, `${path}.sampler.mipmap`);
  const blend = obj(m.blend, `${path}.blend`); bool(blend.enabled, `${path}.blend.enabled`);
  const depth = obj(m.depth, `${path}.depth`); str(depth.testFunction, `${path}.depth.testFunction`); bool(depth.write, `${path}.depth.write`);
  str(m.cullMode, `${path}.cullMode`);
  return m;
}

function validateGlobalState(state, path) {
  const s = obj(state, path);
  if (s.matrixConvention !== 'JOML_COLUMN_MAJOR_COLUMN_VECTOR') fail('unsupported matrix convention', `${path}.matrixConvention`);
  vec(s.modelViewMatrix, 16, `${path}.modelViewMatrix`);
  vec(s.projectionMatrix, 16, `${path}.projectionMatrix`);
  vec(s.inverseViewRotationMatrix, 9, `${path}.inverseViewRotationMatrix`);
  const lights = arr(s.directionalLights, `${path}.directionalLights`, 2);
  lights.forEach((light, i) => vec(light, 3, `${path}.directionalLights[${i}]`));
  vec(s.shaderColor, 4, `${path}.shaderColor`);
  const fog = obj(s.fog, `${path}.fog`);
  if (fog.curve !== 'smoothstep') fail('unsupported fog curve', `${path}.fog.curve`);
  finite(fog.start, `${path}.fog.start`); finite(fog.end, `${path}.fog.end`); vec(fog.color, 4, `${path}.fog.color`);
  if (!['sphere', 'cylinder'].includes(fog.shape)) fail('unsupported fog shape', `${path}.fog.shape`);
  if (fog.distanceSpace !== 'modelView') fail('unsupported fog distance space', `${path}.fog.distanceSpace`);
  return s;
}

function validateFrameAndPack(frame, pack) {
  const f = obj(frame, '$.frame');
  const p = obj(pack, '$.pack');
  const manifest = obj(p.manifest, '$.pack.manifest');
  if (f.source?.type !== 'runtimeFinalVertex' || f.source?.authority !== 'authoritative') fail('only authoritative final-vertex frames are accepted', '$.frame.source');
  if (f.source.auxiliarySamplerInputs !== 'resolved-per-vertex-rgba') fail('resolved auxiliary colors are required', '$.frame.source.auxiliarySamplerInputs');
  if (f.modelId !== manifest.modelId || f.packHash !== manifest.packHash || f.layoutHash !== manifest.layoutHash) fail('frame/pack identity mismatch', '$.frame');
  vec(f.modelToWorldMatrix, 16, '$.frame.modelToWorldMatrix');
  vec(f.modelNormalToWorldMatrix, 9, '$.frame.modelNormalToWorldMatrix');
  validateGlobalState(f.globalShaderState, '$.frame.globalShaderState');
  const deformation = obj(f.deformation, '$.frame.deformation');
  if (deformation.type !== 'finalVertices' || deformation.format !== FINAL_VERTEX_FORMAT || deformation.strideFloats !== FINAL_VERTEX_STRIDE_FLOATS) fail('unsupported final-vertex layout', '$.frame.deformation');
  int(deformation.vertexCount, '$.frame.deformation.vertexCount', 1);
  const groups = arr(deformation.groups, '$.frame.deformation.groups');
  const drawOrder = arr(f.drawOrder, '$.frame.drawOrder');
  const drawStates = obj(f.drawStates, '$.frame.drawStates');
  const meshGroups = arr(p.mesh?.drawGroups, '$.pack.mesh.drawGroups');
  const materials = arr(p.materials?.materials, '$.pack.materials.materials');
  return { f, p, manifest, deformation, groups, drawOrder, drawStates, meshGroups, materials };
}

function primitivePlan(mode, vertexCount, path) {
  if (mode === 'TRIANGLES') { if (vertexCount % 3 !== 0) fail('triangle vertex count must be divisible by 3', path); return { mode: 'TRIANGLES', indices: null }; }
  if (mode === 'TRIANGLE_STRIP') { if (vertexCount < 3) fail('triangle strip needs at least 3 vertices', path); return { mode: 'TRIANGLE_STRIP', indices: null }; }
  if (mode === 'TRIANGLE_FAN') { if (vertexCount < 3) fail('triangle fan needs at least 3 vertices', path); return { mode: 'TRIANGLE_FAN', indices: null }; }
  if (mode === 'QUADS') {
    if (vertexCount % 4 !== 0) fail('quad vertex count must be divisible by 4', path);
    const indices = [];
    for (let base = 0; base < vertexCount; base += 4) indices.push(base, base + 1, base + 2, base + 2, base + 3, base);
    return { mode: 'TRIANGLES', indices };
  }
  fail(`primitive '${mode}' needs a separately proven raster path`, path);
}

function glslFloat(v) { const s = String(v); return /[.eE]/.test(s) ? s : `${s}.0`; }

export function buildFinalVertexShaderPair(material) {
  const m = validateReplayMaterial(material, '$.material');
  const r = m.replay;
  const lighting = r.vertexLighting;
  const vertexLighting = lighting.mode === 'none'
    ? '  vVertexColor = aColor;'
    : [
      '  vec3 l0 = normalize(uLight0);',
      '  vec3 l1 = normalize(uLight1);',
      '  vec3 n = uModelNormalToWorld * aNormal;',
      '  float light0 = max(0.0, dot(l0, n));',
      '  float light1 = max(0.0, dot(l1, n));',
      `  float lightAccum = min(${glslFloat(lighting.clampMax)}, (light0 + light1) * ${glslFloat(lighting.power)} + ${glslFloat(lighting.ambient)});`,
      '  vVertexColor = vec4(aColor.rgb * lightAccum, aColor.a);',
    ].join('\n');
  const fogDistance = r.fogDistance === 'modelViewLength'
    ? '  vFogDistance = length((uModelView * worldPosition).xyz);'
    : [
      '  vec3 fogInput = uInverseViewRotation * worldPosition.xyz;',
      '  if (uFogShape == 0) {',
      '    vFogDistance = length((uModelView * vec4(fogInput, 1.0)).xyz);',
      '  } else {',
      '    float distXZ = length((uModelView * vec4(fogInput.x, 0.0, fogInput.z, 1.0)).xyz);',
      '    float distY = length((uModelView * vec4(0.0, fogInput.y, 0.0, 1.0)).xyz);',
      '    vFogDistance = max(distXZ, distY);',
      '  }',
    ].join('\n');
  const discard = r.alphaDiscardSource === 'sampler0Alpha'
    ? `  if (sample0.a < ${glslFloat(m.alphaCutoff)}) discard;`
    : '';
  const overlay = r.overlayCombine === 'rgbMixByOverlayAlpha'
    ? '  color.rgb = mix(vOverlayColor.rgb, color.rgb, vOverlayColor.a);'
    : '';
  const lightmap = r.lightmapCombine === 'multiplyRgba' ? '  color *= vLightmapColor;' : '';
  const fog = m.fogMode === 'rgbaFade'
    ? [
      '  float fogFade = 1.0;',
      '  if (vFogDistance > uFogStart) {',
      '    fogFade = vFogDistance >= uFogEnd ? 0.0 : smoothstep(uFogEnd, uFogStart, vFogDistance);',
      '  }',
      '  color *= fogFade;',
    ].join('\n')
    : [
      '  if (vFogDistance > uFogStart) {',
      '    float fogValue = vFogDistance < uFogEnd ? smoothstep(uFogStart, uFogEnd, vFogDistance) : 1.0;',
      '    color = vec4(mix(color.rgb, uFogColor.rgb, fogValue * uFogColor.a), color.a);',
      '  }',
    ].join('\n');
  const vertex = `#version 300 es
precision highp float;
layout(location=0) in vec3 aPosition;
layout(location=1) in vec2 aUv;
layout(location=2) in vec3 aNormal;
layout(location=3) in vec4 aColor;
layout(location=4) in vec4 aOverlayColor;
layout(location=5) in vec4 aLightmapColor;
uniform mat4 uModelToWorld;
uniform mat3 uModelNormalToWorld;
uniform mat4 uModelView;
uniform mat4 uProjection;
uniform mat3 uInverseViewRotation;
uniform vec3 uLight0;
uniform vec3 uLight1;
uniform int uFogShape;
out vec2 vUv;
out vec4 vVertexColor;
out vec4 vOverlayColor;
out vec4 vLightmapColor;
out float vFogDistance;
void main() {
  vec4 worldPosition = uModelToWorld * vec4(aPosition, 1.0);
  gl_Position = uProjection * uModelView * worldPosition;
${vertexLighting}
${fogDistance}
  vUv = aUv;
  vOverlayColor = aOverlayColor;
  vLightmapColor = aLightmapColor;
}`;
  const fragment = `#version 300 es
precision highp float;
uniform sampler2D uSampler0;
uniform vec4 uShaderColor;
uniform float uFogStart;
uniform float uFogEnd;
uniform vec4 uFogColor;
in vec2 vUv;
in vec4 vVertexColor;
in vec4 vOverlayColor;
in vec4 vLightmapColor;
in float vFogDistance;
out vec4 outColor;
void main() {
  vec4 sample0 = texture(uSampler0, vUv);
${discard}
  vec4 color = sample0 * vVertexColor * uShaderColor;
${overlay}
${lightmap}
${fog}
  outColor = color;
}`;
  return { vertex, fragment };
}

export function buildFinalVertexReplayPlan(frame, pack) {
  const { f, deformation, groups, drawOrder, drawStates, meshGroups, materials } = validateFrameAndPack(frame, pack);
  const meshById = new Map(meshGroups.map((g) => [g.groupId, g]));
  const materialById = new Map(materials.map((m) => [m.materialId, m]));
  const dynamicById = new Map(groups.map((g) => [g.groupId, g]));
  const planned = [];
  for (let order = 0; order < drawOrder.length; order++) {
    const groupId = str(drawOrder[order], `$.frame.drawOrder[${order}]`);
    const state = obj(drawStates[groupId], `$.frame.drawStates.${groupId}`);
    if (state.visible !== true) fail('authoritative drawOrder contains a non-visible group', `$.frame.drawStates.${groupId}.visible`);
    const dynamic = obj(dynamicById.get(groupId), `$.frame.deformation.groups.${groupId}`);
    const staticGroup = obj(meshById.get(groupId), `$.pack.mesh.drawGroups.${groupId}`);
    const staticMaterial = obj(materialById.get(staticGroup.materialId), `$.pack.materials.${staticGroup.materialId}`);
    const runtimeMaterial = validateReplayMaterial(state.material, `$.frame.drawStates.${groupId}.material`);
    if (state.textureResourceId !== staticMaterial.sourceTextureResourceId) fail('runtime texture identity does not match pack provenance', `$.frame.drawStates.${groupId}.textureResourceId`);
    const texture = str(staticMaterial.baseTexture, `$.pack.materials.${staticGroup.materialId}.baseTexture`);
    const vertexStart = int(dynamic.vertexStart, `$.frame.deformation.groups.${groupId}.vertexStart`);
    const vertexCount = int(dynamic.vertexCount, `$.frame.deformation.groups.${groupId}.vertexCount`, 1);
    if (vertexStart + vertexCount > deformation.vertexCount) fail('group vertex range exceeds frame buffer', `$.frame.deformation.groups.${groupId}`);
    const primitive = primitivePlan(str(dynamic.primitiveMode, `$.frame.deformation.groups.${groupId}.primitiveMode`), vertexCount, `$.frame.deformation.groups.${groupId}.primitiveMode`);
    planned.push({
      groupId, order, vertexStart, vertexCount, primitive,
      attributes: FINAL_VERTEX_ATTRIBUTES,
      sampler0: { texture, bilinear: runtimeMaterial.sampler.bilinear, mipmap: runtimeMaterial.sampler.mipmap },
      pipeline: { alphaMode: runtimeMaterial.alphaMode, blend: clone(runtimeMaterial.blend), cullMode: runtimeMaterial.cullMode, depth: clone(runtimeMaterial.depth) },
      shader: buildFinalVertexShaderPair(runtimeMaterial),
    });
  }
  return {
    format: FINAL_VERTEX_FORMAT, strideFloats: FINAL_VERTEX_STRIDE_FLOATS, strideBytes: FINAL_VERTEX_STRIDE_BYTES,
    modelToWorldMatrix: clone(f.modelToWorldMatrix), modelNormalToWorldMatrix: clone(f.modelNormalToWorldMatrix),
    globalShaderState: clone(f.globalShaderState), groups: planned,
  };
}

function byteView(bytes) {
  if (!(bytes instanceof Uint8Array)) fail('expected Uint8Array-compatible frame buffer', '$.buffer');
  return new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
}

export function validateFinalVertexBuffer(frame, bytes) {
  const deformation = obj(frame?.deformation, '$.frame.deformation');
  if (deformation.format !== FINAL_VERTEX_FORMAT || deformation.strideFloats !== FINAL_VERTEX_STRIDE_FLOATS) fail('unsupported frame buffer layout', '$.frame.deformation');
  const count = int(deformation.vertexCount, '$.frame.deformation.vertexCount', 1);
  const view = byteView(bytes);
  const expected = count * FINAL_VERTEX_STRIDE_BYTES;
  if (view.byteLength !== expected) fail(`buffer byteLength ${view.byteLength} does not equal ${expected}`, '$.buffer');
  for (let vertex = 0; vertex < count; vertex++) {
    for (let component = 0; component < FINAL_VERTEX_STRIDE_FLOATS; component++) {
      const value = view.getFloat32((vertex * FINAL_VERTEX_STRIDE_FLOATS + component) * 4, true);
      if (!Number.isFinite(value)) fail('non-finite final vertex component', `$.buffer[${vertex}][${component}]`);
      if (component >= 12 && component < 16 && !Number.isInteger(value)) fail('auxiliary evidence coordinate is not integer', `$.buffer[${vertex}][${component}]`);
      if (component >= 16 && (value < 0 || value > 1)) fail('resolved auxiliary color is outside [0,1]', `$.buffer[${vertex}][${component}]`);
    }
  }
  return true;
}

function rgba(v, path) { return vec(v, 4, path).map(Number); }
function multiply4(a, b) { return a.map((x, i) => x * b[i]); }
function smoothstep(edge0, edge1, x) {
  if (edge0 === edge1) return x < edge0 ? 0 : 1;
  const t = Math.max(0, Math.min(1, (x - edge0) / (edge1 - edge0)));
  return t * t * (3 - 2 * t);
}

export function applyDirectionalVertexLighting(color, normal, directionalLights, lighting) {
  const c = rgba(color, '$.color');
  const n = vec(normal, 3, '$.normal');
  const lights = arr(directionalLights, '$.directionalLights', 2).map((v, i) => vec(v, 3, `$.directionalLights[${i}]`));
  if (lighting.mode === 'none') return c;
  if (lighting.mode !== 'dualDirectionalDiffuse') fail('unsupported vertex lighting mode', '$.lighting.mode');
  const normalize = (v, path) => { const len = Math.hypot(v[0], v[1], v[2]); if (!(len > 0)) fail('zero-length light direction', path); return v.map((x) => x / len); };
  const l0 = normalize(lights[0], '$.directionalLights[0]');
  const l1 = normalize(lights[1], '$.directionalLights[1]');
  const dot = (a, b) => a[0]*b[0] + a[1]*b[1] + a[2]*b[2];
  const accum = Math.min(lighting.clampMax, (Math.max(0, dot(l0, n)) + Math.max(0, dot(l1, n))) * lighting.power + lighting.ambient);
  return [c[0] * accum, c[1] * accum, c[2] * accum, c[3]];
}

export function shadeFinalVertexSample({ material, sampler0, vertexColor, overlayColor, lightmapColor, shaderColor, fogDistance, fog }) {
  const m = validateReplayMaterial(material, '$.material');
  const r = m.replay;
  const sample0 = rgba(sampler0, '$.sampler0');
  if (r.alphaDiscardSource === 'sampler0Alpha' && sample0[3] < m.alphaCutoff) return { discarded: true, color: null };
  let color = multiply4(multiply4(sample0, rgba(vertexColor, '$.vertexColor')), rgba(shaderColor, '$.shaderColor'));
  if (r.overlayCombine === 'rgbMixByOverlayAlpha') {
    const o = rgba(overlayColor, '$.overlayColor');
    color = [o[0]*(1-o[3]) + color[0]*o[3], o[1]*(1-o[3]) + color[1]*o[3], o[2]*(1-o[3]) + color[2]*o[3], color[3]];
  }
  if (r.lightmapCombine === 'multiplyRgba') color = multiply4(color, rgba(lightmapColor, '$.lightmapColor'));
  const fd = finite(fogDistance, '$.fogDistance');
  const fg = obj(fog, '$.fog'); finite(fg.start, '$.fog.start'); finite(fg.end, '$.fog.end'); const fogColor = rgba(fg.color, '$.fog.color');
  if (m.fogMode === 'colorMixPreserveAlpha' && fd > fg.start) {
    const fv = fd < fg.end ? smoothstep(fg.start, fg.end, fd) : 1;
    const t = fv * fogColor[3];
    color = [color[0]*(1-t)+fogColor[0]*t, color[1]*(1-t)+fogColor[1]*t, color[2]*(1-t)+fogColor[2]*t, color[3]];
  } else if (m.fogMode === 'rgbaFade' && fd > fg.start) {
    const fade = fd >= fg.end ? 0 : smoothstep(fg.end, fg.start, fd);
    color = color.map((x) => x * fade);
  }
  return { discarded: false, color };
}
