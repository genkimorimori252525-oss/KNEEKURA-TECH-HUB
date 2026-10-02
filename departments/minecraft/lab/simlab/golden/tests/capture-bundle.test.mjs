import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm, symlink, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { encodePngRgba } from '../png.mjs';
import {
  GoldenBundleError,
  loadRealClientGoldenBundle,
  validateGoldenCaptureJson,
} from '../capture-bundle.mjs';
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


const IMAGE = Uint8Array.from([
  10, 20, 30, 255,
  40, 50, 60, 255,
  70, 80, 90, 255,
  100, 110, 120, 255,
]);

function captureJson() {
  return {
    schema: 'kneekura.runtime-final-vertex-capture',
    schemaVersion: 1,
    runId: 'golden-run-001',
    runBound: true,
    entityUuid: '00000000-0000-0000-0000-000000000001',
    renderSequence: 3,
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
      viewerComposition: 'draw matching RenderFrameIR over background-before-entities.png with captured depth',
      backgroundDepth: { encoding: 'FLOAT32_LE', origin: 'bottom-left', range: 'OPENGL_DEPTH_0_1', width: 2, height: 2 },
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
        position: [1, 2, 3],
        xRot: 5,
        yRot: 6,
        rotationQuaternion: [0, 0, 0, 1],
        projectionMatrix: [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
        matrixConvention: 'JOML_COLUMN_MAJOR_COLUMN_VECTOR',
      },
    },
  };
}

async function setup() {
  const dir = await mkdtemp(join(tmpdir(), 'kneekura-real-golden-'));
  const backgroundPng = encodePngRgba({ width: 2, height: 2, rgba: IMAGE });
  const goldenImage = Uint8Array.from(IMAGE);
  goldenImage[0] = goldenImage[0] + 1;
  const goldenPng = encodePngRgba({ width: 2, height: 2, rgba: goldenImage });
  await writeFile(join(dir, 'background-before-entities.png'), backgroundPng);
  const depth = Buffer.alloc(16);
  [0.1, 0.2, 0.3, 1].forEach((v, i) => depth.writeFloatLE(v, i * 4));
  await writeFile(join(dir, 'background-before-entities.depth-f32le'), depth);
  await writeFile(join(dir, 'golden-after-entities.png'), goldenPng);
  await writeFile(join(dir, 'capture.json'), JSON.stringify(captureJson(), null, 2));
  return dir;
}

test('real-client Golden bundle loader validates identity, stages and PNG dimensions', async () => {
  const dir = await setup();
  try {
    const bundle = await loadRealClientGoldenBundle(dir);
    assert.equal(bundle.capture.runId, 'golden-run-001');
    assert.equal(bundle.capture.golden.targetEntityUuid, bundle.capture.entityUuid);
    assert.equal(bundle.background.width, 2);
    assert.equal(bundle.depth.values.length, 4);
    assert.ok(Math.abs(bundle.depth.values[0] - 0.1) < 1e-6);
    assert.equal(bundle.golden.height, 2);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});

test('Golden bundle rejects entity mismatch instead of pairing unrelated frame evidence', () => {
  const root = captureJson();
  root.golden.targetEntityUuid = '00000000-0000-0000-0000-000000000099';
  assert.throws(
    () => validateGoldenCaptureJson(root),
    (error) => error instanceof GoldenBundleError && /target entity does not match/.test(error.message),
  );
});

test('Golden bundle rejects camera partialTick mismatch', () => {
  const root = captureJson();
  root.golden.camera.partialTick = 0.25;
  assert.throws(
    () => validateGoldenCaptureJson(root),
    (error) => error instanceof GoldenBundleError && /partialTick does not match/.test(error.message),
  );
});

test('Golden bundle rejects PNG dimensions that do not match captured framebuffer', async () => {
  const dir = await setup();
  try {
    await writeFile(
      join(dir, 'golden-after-entities.png'),
      encodePngRgba({ width: 1, height: 1, rgba: Uint8Array.from([1, 2, 3, 255]) }),
    );
    await assert.rejects(
      loadRealClientGoldenBundle(dir),
      (error) => error instanceof GoldenBundleError && /dimensions do not match/.test(error.message),
    );
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});

test('Golden bundle rejects symlinked screenshot evidence', async (t) => {
  const dir = await setup();
  const external = await mkdtemp(join(tmpdir(), 'kneekura-real-golden-ext-'));
  try {
    const target = join(external, 'golden.png');
    await writeFile(target, await readFile(join(dir, 'golden-after-entities.png')));
    await rm(join(dir, 'golden-after-entities.png'));
    if (!(await symlinkOrSkip(
      t,
      target,
      join(dir, 'golden-after-entities.png')
    ))) {
      return;
    }
    await assert.rejects(
      loadRealClientGoldenBundle(dir),
      (error) => error instanceof GoldenBundleError && /symbolic-link input forbidden/.test(error.message),
    );
  } finally {
    await rm(dir, { recursive: true, force: true });
    await rm(external, { recursive: true, force: true });
  }
});

test('Java Golden capture is stage-based and cannot force a second YSM render', async () => {
  const source = await readFile(
    'bridge/tlm-forge/src/main/java/com/github/tartaricacid/touhoulittlemaid/sim/client/SimGoldenFramebufferCapture.java',
    'utf8',
  );
  const finalVertex = await readFile(
    'bridge/tlm-forge/src/main/java/com/github/tartaricacid/touhoulittlemaid/sim/client/SimFinalVertexCapture.java',
    'utf8',
  );
  const commands = await readFile(
    'bridge/tlm-forge/src/main/java/com/github/tartaricacid/touhoulittlemaid/sim/client/SimClientCommands.java',
    'utf8',
  );

  assert.match(source, /AFTER_CUTOUT_BLOCKS/);
  assert.match(source, /AFTER_ENTITIES/);
  assert.match(source, /Screenshot\.takeScreenshot/);
  assert.match(source, /glReadPixels/);
  assert.match(source, /GL_DEPTH_COMPONENT/);
  assert.match(source, /BACKGROUND_DEPTH_FILE/);
  assert.match(source, /FLOAT32_LE/);
  assert.match(source, /requiresIsolatedEntityScene/);
  assert.match(source, /requiresYsmOnlyFallbackInactive/);
  assert.match(source, /dispatcherShadowSuppressed/);
  assert.match(source, /setRenderShadow\(false\)/);
  assert.match(source, /setRenderHitBoxes\(false\)/);
  assert.match(source, /setRenderHitBoxes\(previousHitBoxes\)/);
  assert.match(source, /setRenderShadow\(restoreEntityShadows\)/);
  assert.match(source, /restoreDispatcherExtras\(\)/);
  assert.match(source, /displayFireAnimation\(\)/);
  assert.match(source, /shouldEntityAppearGlowing\(target\)/);
  assert.match(source, /goldenYsmOnlySafe/);
  assert.match(source, /CameraType\.FIRST_PERSON/);
  assert.doesNotMatch(source, /\.geoRender\s*\(/);
  assert.doesNotMatch(source, /SimModelDump\.shoot\s*\(/);
  assert.doesNotMatch(source, /\.endBatch\s*\(/);
  assert.doesNotMatch(source, /renderer\.render\s*\(/);

  assert.match(finalVertex, /requestNextGolden/);
  assert.match(finalVertex, /SimGoldenFramebufferCapture\.attachRaw/);
  assert.doesNotMatch(finalVertex, /Screenshot\.takeScreenshot/);
  assert.match(commands, /Commands\.literal\("golden"\)/);
});

test('Golden bundle rejects identical pre/post framebuffer evidence', async () => {
  const dir = await setup();
  try {
    await writeFile(
      join(dir, 'golden-after-entities.png'),
      await readFile(join(dir, 'background-before-entities.png')),
    );
    await assert.rejects(
      loadRealClientGoldenBundle(dir),
      (error) => error instanceof GoldenBundleError
        && /no entity framebuffer contribution was observed/.test(error.message),
    );
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});

test('Golden bundle rejects missing YSM-only fallback proof', () => {
  const root = captureJson();
  delete root.golden.requiresYsmOnlyFallbackInactive;
  assert.throws(
    () => validateGoldenCaptureJson(root),
    (error) => error instanceof GoldenBundleError
      && /proven-inactive chat\/fallback effects/.test(error.message),
  );
});

test('Golden bundle rejects missing dispatcher-extra isolation proof', () => {
  const root = captureJson();
  root.golden.dispatcherShadowSuppressed = false;
  assert.throws(
    () => validateGoldenCaptureJson(root),
    (error) => error instanceof GoldenBundleError
      && /dispatcher extras to be excluded/.test(error.message),
  );
});
test('Golden bundle rejects malformed or out-of-range depth evidence', async () => {
  const dir = await setup();
  try {
    await writeFile(join(dir, 'background-before-entities.depth-f32le'), Buffer.alloc(3));
    await assert.rejects(loadRealClientGoldenBundle(dir), /depth byteLength/);
    const bad = Buffer.alloc(16);
    [0.1, 0.2, 1.5, 0.4].forEach((v, i) => bad.writeFloatLE(v, i * 4));
    await writeFile(join(dir, 'background-before-entities.depth-f32le'), bad);
    await assert.rejects(loadRealClientGoldenBundle(dir), /depth value must be finite in \[0,1\]/);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});
