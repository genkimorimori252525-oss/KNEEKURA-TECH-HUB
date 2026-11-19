import { createHash } from 'node:crypto';
import { lstat, mkdir, readFile, realpath, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { assertRenderFrameIR } from '../contracts/render-v1/validator.mjs';
import { loadRealClientGoldenBundle } from './capture-bundle.mjs';
import { compareGoldenOracle } from './oracle.mjs';

export const BOUND_GOLDEN_REPORT_SCHEMA = 'kneekura.bound-golden-oracle';
export const BOUND_GOLDEN_REPORT_VERSION = 1;

export class BoundGoldenOracleError extends Error {
  constructor(message, path = '$') {
    super(`${path}: ${message}`);
    this.name = 'BoundGoldenOracleError';
    this.path = path;
  }
}

function fail(message, path = '$') {
  throw new BoundGoldenOracleError(message, path);
}

function sha256(bytes) {
  return 'sha256:' + createHash('sha256').update(bytes).digest('hex');
}

function exact(actual, expected, path) {
  if (!Object.is(actual, expected)) fail('value does not match Golden capture', path);
}

function exactArray(actual, expected, path) {
  if (!Array.isArray(actual) || !Array.isArray(expected) || actual.length !== expected.length) {
    fail('array shape does not match Golden capture', path);
  }
  for (let i = 0; i < actual.length; i++) exact(actual[i], expected[i], `${path}[${i}]`);
}

async function readRegular(path, label) {
  const stat = await lstat(path);
  if (stat.isSymbolicLink()) fail(label + ' must not be a symbolic link');
  if (!stat.isFile()) fail(label + ' must be a regular file');
  return readFile(path);
}

export function assertGoldenFrameBound(capture, frame) {
  assertRenderFrameIR(frame);
  const binding = frame.goldenBinding;
  if (!binding) fail('RenderFrame is missing goldenBinding', '$.frame.goldenBinding');
  const camera = capture?.golden?.camera;
  if (!camera) fail('Golden capture is missing camera contract', '$.capture.golden.camera');

  for (const key of ['runId', 'entityUuid', 'renderSequence', 'gameTime']) {
    exact(frame[key], capture[key], `$.frame.${key}`);
  }
  exact(frame.partialTick, capture.partialTick, '$.frame.partialTick');

  for (const key of ['runId', 'entityUuid', 'renderSequence', 'gameTime', 'partialTick']) {
    exact(binding.identity[key], capture[key], `$.frame.goldenBinding.identity.${key}`);
  }
  exact(binding.renderTick, camera.renderTick, '$.frame.goldenBinding.renderTick');

  const pairs = [
    ['width', 'framebufferWidth'],
    ['height', 'framebufferHeight'],
    ['viewportWidth', 'viewportWidth'],
    ['viewportHeight', 'viewportHeight'],
    ['windowWidth', 'windowWidth'],
    ['windowHeight', 'windowHeight'],
    ['guiScaledWidth', 'guiScaledWidth'],
    ['guiScaledHeight', 'guiScaledHeight'],
  ];
  for (const [frameKey, cameraKey] of pairs) {
    exact(binding.framebuffer[frameKey], camera[cameraKey], `$.frame.goldenBinding.framebuffer.${frameKey}`);
  }

  exactArray(binding.camera.position, camera.position, '$.frame.goldenBinding.camera.position');
  exact(binding.camera.xRot, camera.xRot, '$.frame.goldenBinding.camera.xRot');
  exact(binding.camera.yRot, camera.yRot, '$.frame.goldenBinding.camera.yRot');
  exactArray(
    binding.camera.rotationQuaternion,
    camera.rotationQuaternion,
    '$.frame.goldenBinding.camera.rotationQuaternion',
  );
  exactArray(
    binding.camera.projectionMatrix,
    camera.projectionMatrix,
    '$.frame.goldenBinding.camera.projectionMatrix',
  );
  exactArray(
    frame.globalShaderState.projectionMatrix,
    camera.projectionMatrix,
    '$.frame.globalShaderState.projectionMatrix',
  );

  for (const key of ['encoding', 'origin', 'range', 'width', 'height']) {
    exact(
      binding.backgroundDepth[key],
      capture.golden.backgroundDepth[key],
      `$.frame.goldenBinding.backgroundDepth.${key}`,
    );
  }
  return true;
}

export async function compareBoundGoldenOracle(options) {
  const { captureDir, viewerPngPath, frameJsonPath, outputDir, thresholds = {} } = options || {};
  if (!captureDir || !viewerPngPath || !frameJsonPath || !outputDir) {
    fail('captureDir, viewerPngPath, frameJsonPath, and outputDir are required');
  }

  const captureRoot = await realpath(resolve(captureDir));
  const bundle = await loadRealClientGoldenBundle(captureRoot);
  const frameBytes = await readRegular(resolve(frameJsonPath), 'RenderFrame JSON');
  const frame = JSON.parse(frameBytes.toString('utf8'));
  assertGoldenFrameBound(bundle.capture, frame);

  const oracle = await compareGoldenOracle({
    goldenPngPath: resolve(captureRoot, bundle.capture.golden.goldenFile),
    viewerPngPath,
    frameJsonPath,
    outputDir,
    thresholds,
  });

  const binding = {
    schema: BOUND_GOLDEN_REPORT_SCHEMA,
    schemaVersion: BOUND_GOLDEN_REPORT_VERSION,
    pass: oracle.pass,
    identity: {
      runId: frame.runId,
      entityUuid: frame.entityUuid,
      renderSequence: frame.renderSequence,
      gameTime: frame.gameTime,
      partialTick: frame.partialTick,
      renderTick: frame.goldenBinding.renderTick,
    },
    framebuffer: structuredClone(frame.goldenBinding.framebuffer),
    camera: structuredClone(frame.goldenBinding.camera),
    inputs: {
      captureJsonSha256: sha256(await readRegular(resolve(captureRoot, 'capture.json'), 'capture JSON')),
      backgroundPngSha256: sha256(bundle.background.bytes),
      backgroundDepthSha256: sha256(bundle.depth.bytes),
      goldenPngSha256: sha256(bundle.golden.bytes),
      renderFrameJsonSha256: sha256(frameBytes),
    },
    oracleMetrics: oracle.metrics,
    oracleFailures: oracle.failures,
  };

  const out = resolve(outputDir);
  await mkdir(out, { recursive: true });
  await writeFile(resolve(out, 'binding.json'), JSON.stringify(binding, null, 2) + '\n', 'utf8');
  return { oracle, binding, bundle };
}
