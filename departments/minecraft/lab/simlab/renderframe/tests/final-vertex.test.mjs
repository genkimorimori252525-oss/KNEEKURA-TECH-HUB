import assert from 'node:assert/strict';
import { mkdir, mkdtemp, readFile, rm, symlink, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { compileRenderPack } from '../../renderpack/compiler.mjs';
import {
  compileFinalVertexRenderFrame,
  FinalVertexFrameError,
} from '../final-vertex.mjs';

const H = (c) => `sha256:${c.repeat(64)}`;
const ID = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
const ID3 = [1, 0, 0, 0, 1, 0, 0, 0, 1];

async function symlinkOrSkip(t, target, linkPath) {
  try {
    await symlink(target, linkPath);
    return true;
  } catch (error) {
    if (process.platform === 'win32' &&
        (error?.code === 'EPERM' || error?.code === 'EACCES')) {
      t.skip(
        'Windows runner cannot create symbolic links; symlink security check is not executable in this environment'
      );
      return false;
    }
    throw error;
  }
}

function measuredGlobalShaderState(shaderColor = [1, 0.75, 0.5, 0.25]) {
  return {
    matrixConvention: 'JOML_COLUMN_MAJOR_COLUMN_VECTOR',
    modelViewMatrix: [...ID],
    projectionMatrix: [...ID],
    inverseViewRotationMatrix: [...ID3],
    directionalLights: [[0.2, 1, -0.7], [-0.2, 1, 0.7]],
    shaderColor: [...shaderColor],
    fog: {
      curve: 'smoothstep',
      start: 0,
      end: 96,
      color: [0.5, 0.6, 0.7, 1],
      shape: 'sphere',
      distanceSpace: 'modelView',
    },
  };
}

function staticTriangle(x) {
  return [
    x, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1,
    x + 1, 0, 0, 1, 0, 0, 1, 0, 1, 1, 1,
    x, 1, 0, 0, 1, 0, 1, 0, 1, 1, 1,
  ];
}

function finalVertex(
  x, y, z, u, v,
  light = 15728880,
  overlayColor = [1, 1, 1, 1],
  lightmapColor = [0.75, 0.8, 0.85, 1],
) {
  const lightU = light & 0xffff;
  const lightV = (light >>> 16) & 0xffff;
  return [
    x, y, z,
    u, v,
    0, 1, 0,
    1, 1, 1, 1,
    0, 0,
    lightU, lightV,
    ...overlayColor,
    ...lightmapColor,
  ];
}

function quad(x) {
  return [
    ...finalVertex(x, 0, 0, 0, 0),
    ...finalVertex(x + 1, 0, 0, 1, 0),
    ...finalVertex(x + 1, 1, 0, 1, 1),
    ...finalVertex(x, 1, 0, 0, 1),
  ];
}

async function writeFloats(path, values) {
  const bytes = Buffer.alloc(values.length * 4);
  values.forEach((value, i) => bytes.writeFloatLE(value, i * 4));
  await writeFile(path, bytes);
}

function measuredMaterial() {
  return {
    alphaMode: 'opaque',
    blend: {
      enabled: false,
      equation: 'UNKNOWN',
      srcFactor: 'UNKNOWN',
      dstFactor: 'UNKNOWN',
    },
    cullMode: 'back',
    depth: { testFunction: '<=', write: true },
    emissive: false,
    fullbright: false,
    fogMode: 'colorMixPreserveAlpha',
    sampler: { status: 'measured', bilinear: false, mipmap: false },
    vertexTint: 'vertexColor',
    lightmap: true,
    overlay: true,
    replay: {
      status: 'measured',
      vertexLighting: { mode: 'dualDirectionalDiffuse', power: 0.6, ambient: 0.4, clampMax: 1 },
      fogDistance: 'modelViewInverseViewRotationShape',
      textureCombine: 'sample0TimesVertexTimesShaderColor',
      alphaDiscardSource: 'none',
      overlayCombine: 'rgbMixByOverlayAlpha',
      lightmapCombine: 'multiplyRgba',
    },
    captureStatus: 'measured',
    capture: { method: 'synthetic-measured-fixture' },
  };
}


function goldenEvidenceFor(raw) {
  return {
    schema: 'kneekura.real-client-golden-capture',
    schemaVersion: 2,
    backgroundFile: 'background-before-entities.png',
    backgroundDepthFile: 'background-before-entities.depth-f32le',
    goldenFile: 'golden-after-entities.png',
    preStage: 'AFTER_CUTOUT_BLOCKS',
    postStage: 'AFTER_ENTITIES',
    scope: 'main-render-target-before-vs-after-entity-stage',
    targetEntityUuid: raw.entityUuid,
    requiresIsolatedEntityScene: true,
    requiresYsmOnlyFallbackInactive: true,
    preYsmChatBubbleIncluded: false,
    postYsmFallbackEffectsIncluded: false,
    dispatcherShadowSuppressed: true,
    dispatcherHitboxSuppressed: true,
    dispatcherFireOverlayIncluded: false,
    glowingOutlineIncluded: false,
    guiIncluded: false,
    particlesIncluded: false,
    weatherIncluded: false,
    viewerComposition: 'draw matching RenderFrameIR over background-before-entities.png with captured depth',
    backgroundDepth: { encoding:'FLOAT32_LE', origin:'bottom-left', range:'OPENGL_DEPTH_0_1', width:2, height:2 },
    camera: {
      renderTick:9, partialTick:raw.partialTick, framebufferWidth:2, framebufferHeight:2,
      viewportWidth:2, viewportHeight:2, windowWidth:2, windowHeight:2, guiScaledWidth:2, guiScaledHeight:2,
      position:[1,2,3], xRot:5, yRot:6, rotationQuaternion:[0,0,0,1],
      projectionMatrix:[...raw.globalShaderState.projectionMatrix],
      matrixConvention:'JOML_COLUMN_MAJOR_COLUMN_VECTOR',
    },
  };
}
async function setup() {
  const captureRoot = await mkdtemp(join(tmpdir(), 'kneekura-prc-static-'));
  const packRoot = await mkdtemp(join(tmpdir(), 'kneekura-prc-pack-'));
  const rawRoot = await mkdtemp(join(tmpdir(), 'kneekura-prc-raw-'));
  const frameRoot = await mkdtemp(join(tmpdir(), 'kneekura-prc-frame-'));

  await mkdir(join(captureRoot, 'textures'), { recursive: true });
  await writeFile(join(captureRoot, 'textures', 'body.png'), Buffer.from([1, 2, 3, 4]));

  const staticCapture = {
    schema: 'kneekura.static-render-capture',
    schemaVersion: '1.0.0',
    modelId: 'test:reimu',
    coordinateSystem: 'KNEEKURA_RH_Y_UP_BLOCK',
    vertexStrideFloats: 11,
    topology: 'expandedTriangles',
    source: {
      adapter: 'fixture',
      classification: 'runtimeVertexSnapshot',
      modVersion: 'test',
      modJarHash: H('a'),
      modelResourceHash: H('b'),
    },
    bones: [{
      slot: 0,
      name: 'root',
      parentSlot: null,
      bindMatrix: null,
      bindMatrixAuthority: 'UNKNOWN',
      inverseBindMatrix: null,
      inverseBindMatrixAuthority: 'UNKNOWN',
    }],
    groups: [{
      groupId: 'body',
      order: 0,
      materialId: 'body',
      sourceRenderType: 'entityCutout(body)',
      texture: {
        sourcePath: 'textures/body.png',
        sourceResourceId: 'test:textures/body.png',
      },
      material: measuredMaterial(),
      vertices: staticTriangle(0),
    }],
  };

  const pack = await compileRenderPack({
    capture: staticCapture,
    captureRoot,
    outputRoot: packRoot,
  });

  await writeFloats(join(rawRoot, 'group-0000.f32le'), quad(0));
  const raw = {
    schema: 'kneekura.runtime-final-vertex-capture',
    schemaVersion: 2,
    runId: 'run-test-001',
    runBound: true,
    entityUuid: '00000000-0000-0000-0000-000000000001',
    renderSequence: 7,
    gameTime: 100,
    partialTick: 0.5,
    modelId: 'test:reimu',
    coordinateSystem: 'KNEEKURA_RH_Y_UP_BLOCK',
    matrixConvention: 'JOML_COLUMN_MAJOR_COLUMN_VECTOR',
    vertexFormat: 'KNEEKURA_FINAL_VERTEX_V2',
    strideFloats: 24,
    vertexCount: 4,
    source: {
      type: 'runtimeFinalVertex',
      authority: 'authoritative',
      fidelityTier: 0,
      capturePoint: 'same-geoRender-VertexConsumer-tee',
      outerPoseNormalization: 'inverse-observed-PoseStack',
      auxiliarySamplerInputs: 'resolved-per-vertex-rgba',
    },
    auxiliarySamplerEvidence: {
      status: 'resolved-per-vertex-rgba',
      componentEncoding: 'UNORM8_RGBA_TO_FLOAT32',
      overlay: { width: 16, height: 16, coordinateRule: 'directIntegerTexel' },
      lightmap: { width: 16, height: 16, coordinateRule: 'integerDivide16Texel' },
    },
    modelToWorldMatrix: ID,
    modelNormalToWorldMatrix: ID3,
    globalColorMultiplier: [1, 0.75, 0.5, 0.25],
    globalShaderState: measuredGlobalShaderState(),
    groups: [{
      groupId: 'body',
      order: 0,
      file: 'group-0000.f32le',
      strideFloats: 24,
      vertexCount: 4,
      primitiveMode: 'QUADS',
      sourceRenderType: 'entityCutout(body)',
      textureResourceId: 'test:textures/body.png',
      material: measuredMaterial(),
    }],
  };
  await writeFile(join(rawRoot, 'capture.json'), JSON.stringify(raw, null, 2));

  return { captureRoot, packRoot, rawRoot, frameRoot, pack, raw };
}

async function cleanup(state) {
  await Promise.all([
    state.captureRoot,
    state.packRoot,
    state.rawRoot,
    state.frameRoot,
  ].map((path) => rm(path, { recursive: true, force: true })));
}

test('authoritative final-vertex raw capture is bound to Render Pack without YSM reconstruction', async () => {
  const state = await setup();
  try {
    const result = await compileFinalVertexRenderFrame({
      captureDir: state.rawRoot,
      packDir: state.pack.packDir,
      outputRoot: state.frameRoot,
    });
    assert.equal(result.frame.source.type, 'runtimeFinalVertex');
    assert.equal(result.frame.source.authority, 'authoritative');
    assert.equal(result.frame.packHash, state.pack.manifest.packHash);
    assert.equal(result.frame.layoutHash, state.pack.manifest.layoutHash);
    assert.deepEqual(result.frame.drawOrder, ['body']);
    assert.deepEqual(result.frame.visibility.groups, [true]);
    assert.deepEqual(result.frame.visibility.bones, []);
    assert.equal(result.frame.visibility.bonesResolvedInFinalVertices, true);
    assert.equal(result.frame.deformation.type, 'finalVertices');
    assert.equal(result.frame.deformation.vertexCount, 4);
    assert.equal(result.frame.deformation.groups[0].primitiveMode, 'QUADS');
    assert.equal(result.frame.drawStates.body.textureResourceId, 'test:textures/body.png');
    assert.equal(result.frame.drawStates.body.material.cullMode, 'back');
    assert.equal(result.frame.drawStates.body.material.fogMode, 'colorMixPreserveAlpha');
    assert.deepEqual(result.frame.drawStates.body.colorMultiplier, [1, 0.75, 0.5, 0.25]);
    assert.deepEqual(result.frame.modelNormalToWorldMatrix, ID3);
    assert.deepEqual(result.frame.globalShaderState, state.raw.globalShaderState);
    assert.equal(result.frame.source.auxiliarySamplerInputs, 'resolved-per-vertex-rgba');
    assert.equal(result.frame.deformation.format, 'KNEEKURA_FINAL_VERTEX_V2');
    assert.equal(result.frame.deformation.strideFloats, 24);
    assert.equal(result.frame.drawStates.body.overlayCoordinatesInBuffer, true);
    assert.equal(result.frame.drawStates.body.lightCoordinatesInBuffer, true);
    assert.equal(result.frame.drawStates.body.resolvedOverlayColorInBuffer, true);
    assert.equal(result.frame.drawStates.body.resolvedLightmapColorInBuffer, true);
    assert.equal((await readFile(join(result.frameDir, 'frame.bin'))).length, 4 * 24 * 4);
  } finally {
    await cleanup(state);
  }
});

test('normalizer rejects unbound runtime capture instead of inventing run identity', async () => {
  const state = await setup();
  try {
    state.raw.runId = 'unbound';
    state.raw.runBound = false;
    await writeFile(join(state.rawRoot, 'capture.json'), JSON.stringify(state.raw));
    await assert.rejects(
      compileFinalVertexRenderFrame({
        captureDir: state.rawRoot,
        packDir: state.pack.packDir,
        outputRoot: state.frameRoot,
      }),
      (error) => error instanceof FinalVertexFrameError && /explicitly bound/.test(error.message),
    );
  } finally {
    await cleanup(state);
  }
});

test('normalizer rejects runtime texture mismatch rather than reading .minecraft at Viewer time', async () => {
  const state = await setup();
  try {
    state.raw.groups[0].textureResourceId = 'test:textures/other.png';
    await writeFile(join(state.rawRoot, 'capture.json'), JSON.stringify(state.raw));
    await assert.rejects(
      compileFinalVertexRenderFrame({
        captureDir: state.rawRoot,
        packDir: state.pack.packDir,
        outputRoot: state.frameRoot,
      }),
      (error) => error instanceof FinalVertexFrameError && /does not match Render Pack source/.test(error.message),
    );
  } finally {
    await cleanup(state);
  }
});

test('normalizer rejects unknown runtime group instead of silently dropping it', async () => {
  const state = await setup();
  try {
    state.raw.groups[0].groupId = 'unknown-layer';
    await writeFile(join(state.rawRoot, 'capture.json'), JSON.stringify(state.raw));
    await assert.rejects(
      compileFinalVertexRenderFrame({
        captureDir: state.rawRoot,
        packDir: state.pack.packDir,
        outputRoot: state.frameRoot,
      }),
      (error) => error instanceof FinalVertexFrameError && /does not exist in Render Pack/.test(error.message),
    );
  } finally {
    await cleanup(state);
  }
});

test('normalizer rejects unknown primitive mode because authoritative replay cannot guess topology', async () => {
  const state = await setup();
  try {
    state.raw.groups[0].primitiveMode = 'UNKNOWN';
    await writeFile(join(state.rawRoot, 'capture.json'), JSON.stringify(state.raw));
    await assert.rejects(
      compileFinalVertexRenderFrame({
        captureDir: state.rawRoot,
        packDir: state.pack.packDir,
        outputRoot: state.frameRoot,
      }),
      (error) => error instanceof FinalVertexFrameError && /unsupported\/unknown primitive mode/.test(error.message),
    );
  } finally {
    await cleanup(state);
  }
});

test('normalizer rejects truncated final-vertex buffer', async () => {
  const state = await setup();
  try {
    const bytes = await readFile(join(state.rawRoot, 'group-0000.f32le'));
    await writeFile(join(state.rawRoot, 'group-0000.f32le'), bytes.subarray(0, bytes.length - 4));
    await assert.rejects(
      compileFinalVertexRenderFrame({
        captureDir: state.rawRoot,
        packDir: state.pack.packDir,
        outputRoot: state.frameRoot,
      }),
      (error) => error instanceof FinalVertexFrameError && /byteLength/.test(error.message),
    );
  } finally {
    await cleanup(state);
  }
});

test('normalizer rejects symlinked final-vertex buffers', async (t) => {
  const state = await setup();
  const external = await mkdtemp(join(tmpdir(), 'kneekura-prc-external-'));
  try {
    const original = await readFile(join(state.rawRoot, 'group-0000.f32le'));
    await writeFile(join(external, 'group.bin'), original);
    await rm(join(state.rawRoot, 'group-0000.f32le'));
    if (!(await symlinkOrSkip(
      t,
      join(external, 'group.bin'),
      join(state.rawRoot, 'group-0000.f32le')
    ))) {
      return;
    }
    await assert.rejects(
      compileFinalVertexRenderFrame({
        captureDir: state.rawRoot,
        packDir: state.pack.packDir,
        outputRoot: state.frameRoot,
      }),
      (error) => error instanceof FinalVertexFrameError && /symbolic-link input forbidden/.test(error.message),
    );
  } finally {
    await rm(external, { recursive: true, force: true });
    await cleanup(state);
  }
});

test('normalizer rejects incomplete material state instead of promoting guessed authoritative replay', async () => {
  const state = await setup();
  try {
    state.raw.groups[0].material.alphaMode = 'UNKNOWN';
    await writeFile(join(state.rawRoot, 'capture.json'), JSON.stringify(state.raw));
    await assert.rejects(
      compileFinalVertexRenderFrame({
        captureDir: state.rawRoot,
        packDir: state.pack.packDir,
        outputRoot: state.frameRoot,
      }),
      (error) => error instanceof FinalVertexFrameError
        && /requires measured alphaMode/.test(error.message),
    );
  } finally {
    await cleanup(state);
  }
});

test('final-vertex capture path cannot re-render or execute YSM semantics', async () => {
  const captureSource = await readFile(
    'bridge/tlm-forge/src/main/java/com/github/tartaricacid/touhoulittlemaid/sim/client/SimFinalVertexCapture.java',
    'utf8',
  );
  const normalizerSource = await readFile('simlab/renderframe/final-vertex.mjs', 'utf8');

  assert.doesNotMatch(captureSource, /SimModelDump\.shoot\s*\(/);
  assert.doesNotMatch(captureSource, /\.geoRender\s*\(/);
  assert.doesNotMatch(captureSource, /renderer\.render\s*\(/);
  assert.doesNotMatch(normalizerSource, /matsFromPalette|stepControllers|runTimeline|molangStatements/);
  assert.doesNotMatch(normalizerSource, /viewer\/ysm|ysm\.js/);
  assert.match(captureSource, /same-geoRender-VertexConsumer-tee/);
});

test('normalizer rejects unmeasured sampler flags', async () => {
  const state = await setup();
  try {
    delete state.raw.groups[0].material.sampler.bilinear;
    await writeFile(join(state.rawRoot, 'capture.json'), JSON.stringify(state.raw));
    await assert.rejects(
      compileFinalVertexRenderFrame({
        captureDir: state.rawRoot,
        packDir: state.pack.packDir,
        outputRoot: state.frameRoot,
      }),
      (error) => error instanceof FinalVertexFrameError
        && /requires measured sampler\.bilinear/.test(error.message),
    );
  } finally {
    await cleanup(state);
  }
});

test('normalizer rejects unknown depth write even with a final-vertex stream', async () => {
  const state = await setup();
  try {
    state.raw.groups[0].material.depth.write = 'UNKNOWN';
    await writeFile(join(state.rawRoot, 'capture.json'), JSON.stringify(state.raw));
    await assert.rejects(
      compileFinalVertexRenderFrame({
        captureDir: state.rawRoot,
        packDir: state.pack.packDir,
        outputRoot: state.frameRoot,
      }),
      (error) => error instanceof FinalVertexFrameError
        && /requires measured depth\.write/.test(error.message),
    );
  } finally {
    await cleanup(state);
  }
});

test('normalizer accepts blend alpha with an explicit measured alpha discard cutoff', async () => {
  const state = await setup();
  try {
    const material = state.raw.groups[0].material;
    material.alphaMode = 'blend';
    material.alphaCutoff = 0.1;
    material.blend = {
      enabled: true,
      equation: 'add',
      srcFactor: 'srcAlpha',
      dstFactor: 'oneMinusSrcAlpha',
    };
    await writeFile(join(state.rawRoot, 'capture.json'), JSON.stringify(state.raw));
    const result = await compileFinalVertexRenderFrame({
      captureDir: state.rawRoot,
      packDir: state.pack.packDir,
      outputRoot: state.frameRoot,
    });
    assert.equal(result.frame.drawStates.body.material.alphaMode, 'blend');
    assert.equal(result.frame.drawStates.body.material.alphaCutoff, 0.1);
    assert.equal(result.frame.drawStates.body.material.blend.enabled, true);
  } finally {
    await cleanup(state);
  }
});

test('normalizer rejects missing globalShaderState for authoritative final-vertex capture', async () => {
  const state = await setup();
  try {
    delete state.raw.globalShaderState;
    await writeFile(join(state.rawRoot, 'capture.json'), JSON.stringify(state.raw));
    await assert.rejects(
      compileFinalVertexRenderFrame({
        captureDir: state.rawRoot,
        packDir: state.pack.packDir,
        outputRoot: state.frameRoot,
      }),
      (error) => error instanceof FinalVertexFrameError && /globalShaderState/.test(error.message),
    );
  } finally {
    await cleanup(state);
  }
});

test('normalizer rejects invalid global shader matrix length', async () => {
  const state = await setup();
  try {
    state.raw.globalShaderState.modelViewMatrix.pop();
    await writeFile(join(state.rawRoot, 'capture.json'), JSON.stringify(state.raw));
    await assert.rejects(
      compileFinalVertexRenderFrame({
        captureDir: state.rawRoot,
        packDir: state.pack.packDir,
        outputRoot: state.frameRoot,
      }),
      (error) => error instanceof FinalVertexFrameError && /expected 16 values/.test(error.message),
    );
  } finally {
    await cleanup(state);
  }
});

test('normalizer rejects non-finite global shader values encoded as an overflowing JSON number', async () => {
  const state = await setup();
  try {
    const json = JSON.stringify(state.raw).replace('"start":0', '"start":1e400');
    assert.match(json, /"start":1e400/);
    await writeFile(join(state.rawRoot, 'capture.json'), json);
    await assert.rejects(
      compileFinalVertexRenderFrame({
        captureDir: state.rawRoot,
        packDir: state.pack.packDir,
        outputRoot: state.frameRoot,
      }),
      (error) => error instanceof FinalVertexFrameError && /expected finite number/.test(error.message),
    );
  } finally {
    await cleanup(state);
  }
});

test('normalizer rejects unknown fog shape', async () => {
  const state = await setup();
  try {
    state.raw.globalShaderState.fog.shape = 'box';
    await writeFile(join(state.rawRoot, 'capture.json'), JSON.stringify(state.raw));
    await assert.rejects(
      compileFinalVertexRenderFrame({
        captureDir: state.rawRoot,
        packDir: state.pack.packDir,
        outputRoot: state.frameRoot,
      }),
      (error) => error instanceof FinalVertexFrameError && /unsupported fog shape/.test(error.message),
    );
  } finally {
    await cleanup(state);
  }
});

test('normalizer rejects unsupported fog curve rather than approximating it', async () => {
  const state = await setup();
  try {
    state.raw.globalShaderState.fog.curve = 'linear';
    await writeFile(join(state.rawRoot, 'capture.json'), JSON.stringify(state.raw));
    await assert.rejects(
      compileFinalVertexRenderFrame({
        captureDir: state.rawRoot,
        packDir: state.pack.packDir,
        outputRoot: state.frameRoot,
      }),
      (error) => error instanceof FinalVertexFrameError && /fog\.curve/.test(error.message),
    );
  } finally {
    await cleanup(state);
  }
});

test('normalizer rejects UNKNOWN fogMode for authoritative replay', async () => {
  const state = await setup();
  try {
    state.raw.groups[0].material.fogMode = 'UNKNOWN';
    await writeFile(join(state.rawRoot, 'capture.json'), JSON.stringify(state.raw));
    await assert.rejects(
      compileFinalVertexRenderFrame({
        captureDir: state.rawRoot,
        packDir: state.pack.packDir,
        outputRoot: state.frameRoot,
      }),
      (error) => error instanceof FinalVertexFrameError && /requires measured fogMode/.test(error.message),
    );
  } finally {
    await cleanup(state);
  }
});

test('normalizer rejects disagreement between legacy color multiplier and captured shaderColor', async () => {
  const state = await setup();
  try {
    state.raw.globalShaderState.shaderColor[2] = 0.25;
    await writeFile(join(state.rawRoot, 'capture.json'), JSON.stringify(state.raw));
    await assert.rejects(
      compileFinalVertexRenderFrame({
        captureDir: state.rawRoot,
        packDir: state.pack.packDir,
        outputRoot: state.frameRoot,
      }),
      (error) => error instanceof FinalVertexFrameError && /must exactly match captured shaderColor/.test(error.message),
    );
  } finally {
    await cleanup(state);
  }
});

test('normalizer requires resolved auxiliary sampler evidence instead of coordinate-only replay', async () => {
  const state = await setup();
  try {
    state.raw.source.auxiliarySamplerInputs = 'coordinates-only-unresolved';
    await writeFile(join(state.rawRoot, 'capture.json'), JSON.stringify(state.raw));
    await assert.rejects(
      compileFinalVertexRenderFrame({
        captureDir: state.rawRoot,
        packDir: state.pack.packDir,
        outputRoot: state.frameRoot,
      }),
      (error) => error instanceof FinalVertexFrameError
        && /resolved-per-vertex-rgba/.test(error.message),
    );

    state.raw.source.auxiliarySamplerInputs = 'resolved-per-vertex-rgba';
    delete state.raw.auxiliarySamplerEvidence;
    await writeFile(join(state.rawRoot, 'capture.json'), JSON.stringify(state.raw));
    await assert.rejects(
      compileFinalVertexRenderFrame({
        captureDir: state.rawRoot,
        packDir: state.pack.packDir,
        outputRoot: state.frameRoot,
      }),
      (error) => error instanceof FinalVertexFrameError
        && /auxiliarySamplerEvidence/.test(error.message),
    );
  } finally {
    await cleanup(state);
  }
});

test('global shader capture observes RenderSystem directly and never derives biome/weather semantics', async () => {
  const source = await readFile(
    'bridge/tlm-forge/src/main/java/com/github/tartaricacid/touhoulittlemaid/sim/client/SimGlobalShaderState.java',
    'utf8',
  );

  for (const getter of [
    'RenderSystem.getModelViewMatrix()',
    'RenderSystem.getProjectionMatrix()',
    'RenderSystem.getInverseViewRotationMatrix()',
    'RenderSystem.getShaderColor()',
    'RenderSystem.getShaderFogStart()',
    'RenderSystem.getShaderFogEnd()',
    'RenderSystem.getShaderFogColor()',
    'RenderSystem.getShaderFogShape()',
  ]) {
    assert.ok(source.includes(getter), `missing direct observation: ${getter}`);
  }
  const executable = source
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/\/\/.*$/gm, '');
  assert.doesNotMatch(executable, /biome|weather/i);
  assert.doesNotMatch(executable, /shaderLightDirections/);
  assert.match(source, /field\.getType\(\)\.isArray\(\)/);
  assert.match(source, /field\.getType\(\)\.getComponentType\(\) != Vector3f\.class/);
  assert.match(source, /candidates\.size\(\) != 1/);
  assert.match(source, /root\.add\("shaderColor", array\(this\.shaderColor\)\)/);
});


test('normalizer rejects non-finite final-vertex values before authoritative promotion', async () => {
  const state = await setup();
  try {
    const file = join(state.rawRoot, 'group-0000.f32le');
    const bytes = await readFile(file);
    bytes.writeFloatLE(Number.NaN, 0);
    await writeFile(file, bytes);
    await assert.rejects(
      compileFinalVertexRenderFrame({
        captureDir: state.rawRoot,
        packDir: state.pack.packDir,
        outputRoot: state.frameRoot,
      }),
      (error) => error instanceof FinalVertexFrameError
        && /non-finite float/.test(error.message),
    );
  } finally {
    await cleanup(state);
  }
});

test('normalizer rejects non-integer captured auxiliary sampler coordinates', async () => {
  const state = await setup();
  try {
    const file = join(state.rawRoot, 'group-0000.f32le');
    const bytes = await readFile(file);
    bytes.writeFloatLE(0.5, 12 * 4);
    await writeFile(file, bytes);
    await assert.rejects(
      compileFinalVertexRenderFrame({
        captureDir: state.rawRoot,
        packDir: state.pack.packDir,
        outputRoot: state.frameRoot,
      }),
      (error) => error instanceof FinalVertexFrameError
        && /coordinates must remain integers/.test(error.message),
    );
  } finally {
    await cleanup(state);
  }
});

test('normalizer rejects resolved auxiliary colors outside normalized range', async () => {
  const state = await setup();
  try {
    const file = join(state.rawRoot, 'group-0000.f32le');
    const bytes = await readFile(file);
    bytes.writeFloatLE(1.25, 16 * 4);
    await writeFile(file, bytes);
    await assert.rejects(
      compileFinalVertexRenderFrame({
        captureDir: state.rawRoot,
        packDir: state.pack.packDir,
        outputRoot: state.frameRoot,
      }),
      (error) => error instanceof FinalVertexFrameError
        && /normalized to \[0,1\]/.test(error.message),
    );
  } finally {
    await cleanup(state);
  }
});

test('auxiliary sampler capture reads live runtime textures structurally and never reconstructs semantics', async () => {
  const auxiliary = await readFile(
    'bridge/tlm-forge/src/main/java/com/github/tartaricacid/touhoulittlemaid/sim/client/SimAuxiliarySamplerState.java',
    'utf8',
  );
  const capture = await readFile(
    'bridge/tlm-forge/src/main/java/com/github/tartaricacid/touhoulittlemaid/sim/client/SimFinalVertexCapture.java',
    'utf8',
  );
  const recorder = await readFile(
    'bridge/tlm-forge/src/main/java/com/github/tartaricacid/touhoulittlemaid/sim/client/SimFinalVertexRecorder.java',
    'utf8',
  );

  for (const directObservation of [
    'mc.gameRenderer.overlayTexture()',
    'mc.gameRenderer.lightTexture()',
    'getPixels()',
    'getRedOrLuminance',
    'getGreenOrLuminance',
    'getBlueOrLuminance',
    'getLuminanceOrAlpha',
  ]) {
    assert.ok(auxiliary.includes(directObservation), `missing direct runtime observation: ${directObservation}`);
  }
  assert.match(auxiliary, /field\.getType\(\) != DynamicTexture\.class/);
  assert.match(auxiliary, /candidates\.size\(\) != 1/);
  assert.doesNotMatch(auxiliary, /getDeclaredField\s*\(/);
  assert.match(auxiliary, /sample\(u \/ 16, v \/ 16\)/);

  const executable = auxiliary
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/\/\/.*$/gm, '');
  assert.doesNotMatch(executable, /biome|weather|hurt|whiteOverlayProgress/i);

  assert.ok((capture.match(/SimAuxiliarySamplerState\.capture\(\)/g) ?? []).length >= 2);
  assert.match(capture, /auxiliarySamplerState\(\)\.sameBits\(auxiliaryAfter\)/);
  assert.match(capture, /"resolved-per-vertex-rgba"/);
  assert.match(capture, /KNEEKURA_FINAL_VERTEX_V2/);
  assert.match(recorder, /public static final int STRIDE = 24/);
  assert.match(recorder, /resolveOverlay\(this\.overlayU, this\.overlayV\)/);
  assert.match(recorder, /resolveLightmap\(this\.lightU, this\.lightV\)/);
});

test('normalizer rejects authoritative material with unresolved generic replay semantics', async () => {
  const state = await setup();
  try {
    state.raw.groups[0].material.replay = { status: 'UNKNOWN' };
    await writeFile(join(state.rawRoot, 'capture.json'), JSON.stringify(state.raw));
    await assert.rejects(
      compileFinalVertexRenderFrame({ captureDir: state.rawRoot, packDir: state.pack.packDir, outputRoot: state.frameRoot }),
      (error) => error instanceof FinalVertexFrameError && /measured generic replay semantics/.test(error.message),
    );
  } finally { await cleanup(state); }
});

test('normalizer rejects replay lightmap multiplication when material participation is false', async () => {
  const state = await setup();
  try {
    state.raw.groups[0].material.lightmap = false;
    await writeFile(join(state.rawRoot, 'capture.json'), JSON.stringify(state.raw));
    await assert.rejects(
      compileFinalVertexRenderFrame({ captureDir: state.rawRoot, packDir: state.pack.packDir, outputRoot: state.frameRoot }),
      (error) => error instanceof FinalVertexFrameError && /requires measured lightmap participation/.test(error.message),
    );
  } finally { await cleanup(state); }
});

test('normalizer rejects missing observed outer normal matrix instead of deriving one', async () => {
  const state = await setup();
  try {
    delete state.raw.modelNormalToWorldMatrix;
    await writeFile(join(state.rawRoot, 'capture.json'), JSON.stringify(state.raw));
    await assert.rejects(
      compileFinalVertexRenderFrame({ captureDir: state.rawRoot, packDir: state.pack.packDir, outputRoot: state.frameRoot }),
      (error) => error instanceof FinalVertexFrameError && /modelNormalToWorldMatrix/.test(error.message),
    );
  } finally { await cleanup(state); }
});

test('compiler propagates an exact Golden camera/depth binding and rejects projection drift', async () => {
  const state = await setup();
  try {
    state.raw.golden = goldenEvidenceFor(state.raw);
    await writeFile(join(state.rawRoot, 'capture.json'), JSON.stringify(state.raw));
    const result = await compileFinalVertexRenderFrame({
      captureDir: state.rawRoot, packDir: state.pack.packDir, outputRoot: state.frameRoot,
    });
    assert.equal(result.frame.goldenBinding.identity.runId, state.raw.runId);
    assert.equal(result.frame.goldenBinding.renderTick, 9);
    assert.deepEqual(result.frame.goldenBinding.backgroundDepth, state.raw.golden.backgroundDepth);

    const badRoot = await mkdtemp(join(tmpdir(), 'kneekura-prc-bad-golden-'));
    try {
      const bad = structuredClone(state.raw);
      bad.golden.camera.projectionMatrix[0] = 2;
      await writeFile(join(badRoot, 'capture.json'), JSON.stringify(bad));
      for (const group of bad.groups) {
        await writeFile(join(badRoot, group.file), await readFile(join(state.rawRoot, group.file)));
      }
      await assert.rejects(
        compileFinalVertexRenderFrame({ captureDir: badRoot, packDir: state.pack.packDir, outputRoot: state.frameRoot }),
        /Golden camera projection must exactly match captured global shader projection/,
      );
    } finally {
      await rm(badRoot, { recursive:true, force:true });
    }
  } finally {
    await cleanup(state);
  }
});
