import assert from 'node:assert/strict';
import { mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { encodePngRgba } from '../png.mjs';
import {
  BoundGoldenOracleError,
  assertGoldenFrameBound,
  compareBoundGoldenOracle,
} from '../bound-oracle.mjs';

const ID = [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1];
const ID3 = [1,0,0, 0,1,0, 0,0,1];
const H = (c) => 'sha256:' + c.repeat(64);

function capture() {
  return {
    schema: 'kneekura.runtime-final-vertex-capture',
    schemaVersion: 2,
    runId: 'bound-run-1',
    runBound: true,
    entityUuid: '00000000-0000-0000-0000-000000000001',
    renderSequence: 7,
    gameTime: 100,
    partialTick: 0.5,
    modelId: 'test:reimu',
    golden: {
      schema: 'kneekura.real-client-golden-capture',
      schemaVersion: 2,
      backgroundFile: 'background-before-entities.png',
      backgroundDepthFile: 'background-before-entities.depth-f32le',
      goldenFile: 'golden-after-entities.png',
      preStage: 'AFTER_CUTOUT_BLOCKS',
      postStage: 'AFTER_ENTITIES',
      scope: 'main-render-target-before-vs-after-entity-stage',
      targetEntityUuid: '00000000-0000-0000-0000-000000000001',
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
      viewerComposition: 'bound',
      backgroundDepth: {
        encoding: 'FLOAT32_LE',
        origin: 'bottom-left',
        range: 'OPENGL_DEPTH_0_1',
        width: 2,
        height: 2,
      },
      camera: {
        renderTick: 9,
        partialTick: 0.5,
        framebufferWidth: 2,
        framebufferHeight: 2,
        viewportWidth: 2,
        viewportHeight: 2,
        windowWidth: 2,
        windowHeight: 2,
        guiScaledWidth: 2,
        guiScaledHeight: 2,
        position: [1,2,3],
        xRot: 5,
        yRot: 6,
        rotationQuaternion: [0,0,0,1],
        projectionMatrix: [...ID],
        matrixConvention: 'JOML_COLUMN_MAJOR_COLUMN_VECTOR',
      },
    },
  };
}

function frame() {
  return {
    schema: 'kneekura.renderframe',
    schemaVersion: '1.0.0',
    runId: 'bound-run-1',
    entityUuid: '00000000-0000-0000-0000-000000000001',
    renderSequence: 7,
    gameTime: 100,
    partialTick: 0.5,
    modelId: 'test:reimu',
    packHash: H('a'),
    layoutHash: H('b'),
    source: {
      type: 'runtimeFinalVertex',
      authority: 'authoritative',
      fidelityTier: 0,
      auxiliarySamplerInputs: 'resolved-per-vertex-rgba',
    },
    modelToWorldMatrix: [...ID],
    modelNormalToWorldMatrix: [...ID3],
    globalShaderState: {
      matrixConvention: 'JOML_COLUMN_MAJOR_COLUMN_VECTOR',
      modelViewMatrix: [...ID],
      projectionMatrix: [...ID],
      inverseViewRotationMatrix: [...ID3],
      directionalLights: [[0,1,0],[0,-1,0]],
      shaderColor: [1,1,1,1],
      fog: {
        curve: 'smoothstep',
        start: 0,
        end: 96,
        color: [0.5,0.6,0.7,1],
        shape: 'sphere',
        distanceSpace: 'modelView',
      },
    },
    goldenBinding: {
      schema: 'kneekura.golden-frame-binding',
      schemaVersion: 1,
      identity: {
        runId: 'bound-run-1',
        entityUuid: '00000000-0000-0000-0000-000000000001',
        renderSequence: 7,
        gameTime: 100,
        partialTick: 0.5,
      },
      renderTick: 9,
      framebuffer: {
        width: 2,
        height: 2,
        viewportWidth: 2,
        viewportHeight: 2,
        windowWidth: 2,
        windowHeight: 2,
        guiScaledWidth: 2,
        guiScaledHeight: 2,
      },
      camera: {
        position: [1,2,3],
        xRot: 5,
        yRot: 6,
        rotationQuaternion: [0,0,0,1],
        projectionMatrix: [...ID],
        matrixConvention: 'JOML_COLUMN_MAJOR_COLUMN_VECTOR',
      },
      backgroundDepth: {
        encoding: 'FLOAT32_LE',
        origin: 'bottom-left',
        range: 'OPENGL_DEPTH_0_1',
        width: 2,
        height: 2,
      },
    },
    deformation: {
      type: 'finalVertices',
      bufferRef: 'frame.bin',
      vertexCount: 1,
      strideFloats: 24,
      format: 'KNEEKURA_FINAL_VERTEX_V2',
    },
    visibility: {
      bones: [],
      bonesResolvedInFinalVertices: true,
      groups: [true],
    },
    drawOrder: ['body'],
    drawStates: {
      body: {
        visible: true,
        vertexColorInBuffer: true,
        overlayCoordinatesInBuffer: true,
        lightCoordinatesInBuffer: true,
        resolvedOverlayColorInBuffer: true,
        resolvedLightmapColorInBuffer: true,
      },
    },
  };
}

async function setup() {
  const dir = await mkdtemp(join(tmpdir(), 'kneekura-bound-oracle-'));
  const cap = join(dir, 'capture');
  const out = join(dir, 'out');
  await mkdir(cap);

  const bg = Uint8Array.from([
    10,20,30,255, 40,50,60,255,
    70,80,90,255, 100,110,120,255,
  ]);
  const gold = Uint8Array.from(bg);
  gold[0]++;

  await writeFile(
    join(cap, 'background-before-entities.png'),
    encodePngRgba({ width: 2, height: 2, rgba: bg }),
  );
  const depth = Buffer.alloc(16);
  [0.1,0.2,0.3,1].forEach((v, i) => depth.writeFloatLE(v, i * 4));
  await writeFile(join(cap, 'background-before-entities.depth-f32le'), depth);
  await writeFile(
    join(cap, 'golden-after-entities.png'),
    encodePngRgba({ width: 2, height: 2, rgba: gold }),
  );
  await writeFile(join(cap, 'capture.json'), JSON.stringify(capture()));

  const viewer = join(dir, 'viewer.png');
  await writeFile(viewer, encodePngRgba({ width: 2, height: 2, rgba: gold }));
  const frameJson = join(dir, 'frame.json');
  await writeFile(frameJson, JSON.stringify(frame()));

  return { dir, cap, out, viewer, frameJson };
}

test('bound oracle requires exact frame/camera/depth identity before comparing pixels', async () => {
  const state = await setup();
  try {
    const result = await compareBoundGoldenOracle({
      captureDir: state.cap,
      viewerPngPath: state.viewer,
      frameJsonPath: state.frameJson,
      outputDir: state.out,
    });
    assert.equal(result.oracle.pass, true);
    assert.equal(result.binding.identity.renderTick, 9);
    assert.match(result.binding.inputs.backgroundDepthSha256, /^sha256:/);
    assert.equal(JSON.parse(await readFile(join(state.out, 'binding.json'), 'utf8')).pass, true);
  } finally {
    await rm(state.dir, { recursive: true, force: true });
  }
});

test('cross-frame and cross-camera evidence are rejected before pixel comparison', () => {
  const cap = capture();
  const base = frame();

  const stale = structuredClone(base);
  stale.renderSequence++;
  assert.throws(() => assertGoldenFrameBound(cap, stale), /renderSequence mismatch/);

  const camera = structuredClone(base);
  camera.goldenBinding.camera.position[0] = 99;
  assert.throws(() => assertGoldenFrameBound(cap, camera), /does not match Golden capture/);

  const tick = structuredClone(base);
  tick.goldenBinding.renderTick = 10;
  assert.throws(() => assertGoldenFrameBound(cap, tick), /does not match Golden capture/);
});
