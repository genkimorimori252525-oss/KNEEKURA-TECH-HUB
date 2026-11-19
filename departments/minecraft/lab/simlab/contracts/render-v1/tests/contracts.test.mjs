import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import {
  ContractError,
  assertFrameCompatible,
  assertMaterialsIR,
  assertRenderFrameIR,
  assertRenderMeshIR,
  assertRenderPackManifest,
  canonicalPackIdentityPayload,
  compareSourcePriority,
  computePackHash,
} from '../validator.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const fixture = async (name) => JSON.parse(await readFile(join(here, '..', 'fixtures', name), 'utf8'));

function clone(v) { return structuredClone(v); }
const ID3 = [1, 0, 0, 0, 1, 0, 0, 0, 1];

function configureRuntimeFinalVertex(frame, { includeGlobalShaderState = true } = {}) {
  frame.source = {
    type: 'runtimeFinalVertex',
    authority: 'authoritative',
    fidelityTier: 0,
    auxiliarySamplerInputs: 'resolved-per-vertex-rgba',
  };
  frame.deformation = {
    type: 'finalVertices',
    bufferRef: 'frames/final.bin',
    vertexCount: 1,
    strideFloats: 24,
    format: 'KNEEKURA_FINAL_VERTEX_V2',
  };
  if (includeGlobalShaderState) frame.globalShaderState = clone(GLOBAL_SHADER_STATE);
  frame.modelNormalToWorldMatrix = [...ID3];
  frame.visibility.bones = [];
  frame.visibility.bonesResolvedInFinalVertices = true;
  for (const drawState of Object.values(frame.drawStates)) {
    drawState.vertexColorInBuffer = true;
    drawState.overlayCoordinatesInBuffer = true;
    drawState.lightCoordinatesInBuffer = true;
    drawState.resolvedOverlayColorInBuffer = true;
    drawState.resolvedLightmapColorInBuffer = true;
  }
  return frame;
}

const GLOBAL_SHADER_STATE = {
  matrixConvention: 'JOML_COLUMN_MAJOR_COLUMN_VECTOR',
  modelViewMatrix: [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
  projectionMatrix: [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
  inverseViewRotationMatrix: [1, 0, 0, 0, 1, 0, 0, 0, 1],
  directionalLights: [[0, 1, 0], [0, -1, 0]],
  shaderColor: [1, 1, 1, 1],
  fog: {
    curve: 'smoothstep',
    start: 0,
    end: 96,
    color: [0.5, 0.6, 0.7, 1],
    shape: 'sphere',
    distanceSpace: 'modelView',
  },
};

function attachGoldenBinding(frame, overrides = {}) {
  frame.goldenBinding = {
    schema: 'kneekura.golden-frame-binding',
    schemaVersion: 1,
    identity: {
      runId: frame.runId, entityUuid: frame.entityUuid, renderSequence: frame.renderSequence,
      gameTime: frame.gameTime, partialTick: frame.partialTick,
    },
    renderTick: 9,
    framebuffer: {
      width: 2, height: 2, viewportWidth: 2, viewportHeight: 2,
      windowWidth: 2, windowHeight: 2, guiScaledWidth: 2, guiScaledHeight: 2,
    },
    camera: {
      position: [1,2,3], xRot: 5, yRot: 6, rotationQuaternion: [0,0,0,1],
      projectionMatrix: [...GLOBAL_SHADER_STATE.projectionMatrix],
      matrixConvention: 'JOML_COLUMN_MAJOR_COLUMN_VECTOR',
    },
    backgroundDepth: {
      encoding: 'FLOAT32_LE', origin: 'bottom-left', range: 'OPENGL_DEPTH_0_1', width: 2, height: 2,
    },
    ...overrides,
  };
  return frame;
}


test('valid manifest passes v1 contract', async () => {
  assertRenderPackManifest(await fixture('renderpack-manifest.valid.json'));
});


test('valid RenderMeshIR and MaterialIR pass v1 semantic contracts', async () => {
  assertRenderMeshIR(await fixture('render-mesh.valid.json'));
  assertMaterialsIR(await fixture('materials.valid.json'));
});

test('RenderMeshIR requires all canonical vertex stream descriptors', async () => {
  const m = await fixture('render-mesh.valid.json');
  delete m.attributes.weights;
  assert.throws(() => assertRenderMeshIR(m), /attributes\.weights/);
});

test('MaterialIR rejects pack path traversal for optional textures too', async () => {
  const m = await fixture('materials.valid.json');
  m.materials[0].emissiveTexture = '../outside.png';
  assert.throws(() => assertMaterialsIR(m), /path traversal/);
});

test('MaterialIR accepts explicit UNKNOWN render state without guessing', async () => {
  const m = await fixture('materials.valid.json');
  const material = m.materials[0];
  material.alphaMode = 'UNKNOWN';
  delete material.alphaCutoff;
  material.blend = { enabled: 'UNKNOWN', equation: 'UNKNOWN', srcFactor: 'UNKNOWN', dstFactor: 'UNKNOWN' };
  material.cullMode = 'UNKNOWN';
  material.depth = { testFunction: 'UNKNOWN', write: 'UNKNOWN' };
  material.emissive = 'UNKNOWN';
  material.fullbright = 'UNKNOWN';
  material.fogMode = 'UNKNOWN';
  material.sampler = { status: 'UNKNOWN' };
  material.vertexTint = 'UNKNOWN';
  material.lightmap = 'UNKNOWN';
  material.overlay = 'UNKNOWN';
  material.replay = { status: 'UNKNOWN' };
  assertMaterialsIR(m);
});

test('RenderMeshIR keeps unknown bind matrices explicit instead of inventing identity', async () => {
  const m = await fixture('render-mesh.valid.json');
  m.bones[0].bindMatrix = null;
  m.bones[0].bindMatrixAuthority = 'UNKNOWN';
  m.bones[0].inverseBindMatrix = null;
  m.bones[0].inverseBindMatrixAuthority = 'UNKNOWN';
  assertRenderMeshIR(m);
  const bad = clone(m);
  delete bad.bones[0].bindMatrixAuthority;
  assert.throws(() => assertRenderMeshIR(bad), /explicit authority 'UNKNOWN'/);
});

test('manifest packHash must equal canonical manifest identity', async () => {
  const m = await fixture('renderpack-manifest.valid.json');
  m.packHash = 'sha256:' + 'a'.repeat(64);
  assert.throws(() => assertRenderPackManifest(m), /packHash does not match canonical manifest identity/);
});

test('runtimeFinalVertex requires finalVertices deformation', async () => {
  const f = await fixture('render-frame.valid.json');
  f.source = { type: 'runtimeFinalVertex', authority: 'authoritative', fidelityTier: 0 };
  assert.throws(() => assertRenderFrameIR(f), /runtimeFinalVertex requires deformation.type 'finalVertices'/);
});

test('runtimeFinalVertex may omit bone mask only when final vertices already resolved it', async () => {
  const f = await fixture('render-frame.valid.json');
  configureRuntimeFinalVertex(f);
  delete f.visibility.bonesResolvedInFinalVertices;
  assert.throws(
    () => assertRenderFrameIR(f),
    /bonesResolvedInFinalVertices=true/,
  );
  f.visibility.bonesResolvedInFinalVertices = true;
  assert.equal(assertRenderFrameIR(f), f);
});

test('runtimeMatrix cannot masquerade as final-vertex capture', async () => {
  const f = await fixture('render-frame.valid.json');
  f.deformation = { type: 'finalVertices', bufferRef: 'frames/final.bin', vertexCount: 1 };
  assert.throws(() => assertRenderFrameIR(f), /runtimeMatrix requires deformation.type 'skinMatrices'/);
});

test('resolved draw order requires an explicit draw state for every group', async () => {
  const f = await fixture('render-frame.valid.json');
  delete f.drawStates.body;
  assert.throws(() => assertRenderFrameIR(f), /missing draw state for resolved draw group/);
});

test('manifest rejects path traversal', async () => {
  const m = await fixture('renderpack-manifest.valid.json');
  m.files[0].path = '../.minecraft/evil.json';
  assert.throws(() => assertRenderPackManifest(m), ContractError);
});

test('manifest rejects incompatible schema major', async () => {
  const m = await fixture('renderpack-manifest.valid.json');
  m.schemaVersion = '2.0.0';
  assert.throws(() => assertRenderPackManifest(m), /unsupported schema major/);
});

test('runtimeMatrix frame is compatible with matching pack', async () => {
  const m = await fixture('renderpack-manifest.valid.json');
  const f = await fixture('render-frame.valid.json');
  assert.equal(assertFrameCompatible(f, m), true);
});

test('frame rejects layout mismatch instead of silently falling back', async () => {
  const m = await fixture('renderpack-manifest.valid.json');
  const f = await fixture('render-frame.valid.json');
  f.layoutHash = 'sha256:9999999999999999999999999999999999999999999999999999999999999999';
  assert.throws(() => assertFrameCompatible(f, m), /layoutHash does not match/);
});

test('Offline YSM Emulator cannot claim authoritative', async () => {
  const f = await fixture('render-frame.valid.json');
  f.source = { type: 'offlineYsmEmulator', authority: 'authoritative', fidelityTier: 5 };
  assert.throws(() => assertRenderFrameIR(f), /requires authority 'predicted'/);
});

test('legacy palette is not a Thin Renderer deformation mode', async () => {
  const f = await fixture('render-frame.valid.json');
  f.source = { type: 'runtimePaletteConverted', authority: 'derived', fidelityTier: 2 };
  f.deformation = { type: 'legacyPalette', palette: [0,0,0] };
  assert.throws(() => assertRenderFrameIR(f), /legacyPalette is not a renderer input/);
});

test('authoritative frames reject YSM semantic reconstruction payload', async () => {
  const f = await fixture('render-frame.valid.json');
  f.molang = { expression: 'q.anim_time' };
  assert.throws(() => assertRenderFrameIR(f), /forbidden in authoritative RenderFrameIR/);
});

test('source priority prefers runtimeMatrix over emulator', async () => {
  const a = await fixture('render-frame.valid.json');
  const b = clone(a);
  b.source = { type: 'offlineYsmEmulator', authority: 'predicted', fidelityTier: 5 };
  assert.ok(compareSourcePriority(a, b) < 0);
});

test('pack identity is stable across file ordering and volatile generatedAt', async () => {
  const a = await fixture('renderpack-manifest.valid.json');
  const b = clone(a);
  a.generatedAt = '2026-08-28T00:00:00+09:00';
  b.generatedAt = '2030-01-01T00:00:00Z';
  b.files.reverse();
  assert.equal(canonicalPackIdentityPayload(a), canonicalPackIdentityPayload(b));
  assert.equal(computePackHash(a), computePackHash(b));
});

test('MaterialIR rejects unsupported fogMode but preserves explicit UNKNOWN', async () => {
  const m = await fixture('materials.valid.json');
  m.materials[0].fogMode = 'UNKNOWN';
  assertMaterialsIR(m);
  m.materials[0].fogMode = 'minecraftEntityFog';
  assert.throws(() => assertMaterialsIR(m), /invalid fogMode/);
});

test('runtimeFinalVertex contract requires complete generic global shader state', async () => {
  const f = await fixture('render-frame.valid.json');
  configureRuntimeFinalVertex(f, { includeGlobalShaderState: false });
  assert.throws(() => assertRenderFrameIR(f), /requires captured globalShaderState/);

  f.globalShaderState = clone(GLOBAL_SHADER_STATE);
  assert.equal(assertRenderFrameIR(f), f);

  f.globalShaderState.fog.shape = 'box';
  assert.throws(() => assertRenderFrameIR(f), /unsupported fog shape/);
});

test('runtimeFinalVertex contract rejects unresolved auxiliary inputs and incomplete v2 layout', async () => {
  const f = await fixture('render-frame.valid.json');
  configureRuntimeFinalVertex(f);

  f.source.auxiliarySamplerInputs = 'coordinates-only-unresolved';
  assert.throws(() => assertRenderFrameIR(f), /resolved-per-vertex-rgba/);
  f.source.auxiliarySamplerInputs = 'resolved-per-vertex-rgba';

  f.deformation.format = 'KNEEKURA_FINAL_VERTEX_V1';
  assert.throws(() => assertRenderFrameIR(f), /KNEEKURA_FINAL_VERTEX_V2/);
  f.deformation.format = 'KNEEKURA_FINAL_VERTEX_V2';

  f.deformation.strideFloats = 16;
  assert.throws(() => assertRenderFrameIR(f), /strideFloats 24/);
  f.deformation.strideFloats = 24;

  f.drawStates.body.resolvedLightmapColorInBuffer = false;
  assert.throws(() => assertRenderFrameIR(f), /resolvedLightmapColorInBuffer=true/);
});

test('MaterialIR validates measured generic replay semantics and rejects unknown formulas', async () => {
  const m = await fixture('materials.valid.json');
  assert.equal(m.materials[0].replay.status, 'measured');
  assertMaterialsIR(m);
  m.materials[0].replay.fogDistance = 'biomeDependent';
  assert.throws(() => assertMaterialsIR(m), /unsupported replay fog distance/);
});

test('runtimeFinalVertex requires observed outer normal matrix', async () => {
  const f = await fixture('render-frame.valid.json');
  configureRuntimeFinalVertex(f);
  delete f.modelNormalToWorldMatrix;
  assert.throws(() => assertRenderFrameIR(f), /modelNormalToWorldMatrix/);
});

test('runtimeFinalVertex Golden binding rejects stale frame identity and camera projection', async () => {
  const f = await fixture('render-frame.valid.json');
  configureRuntimeFinalVertex(f);
  attachGoldenBinding(f);
  assert.equal(assertRenderFrameIR(f), f);

  const stale = clone(f);
  stale.goldenBinding.identity.renderSequence += 1;
  assert.throws(() => assertRenderFrameIR(stale), /renderSequence mismatch/);

  const cameraMismatch = clone(f);
  cameraMismatch.goldenBinding.camera.projectionMatrix[0] = 2;
  assert.throws(() => assertRenderFrameIR(cameraMismatch), /does not exactly match bound frame state/);
});
