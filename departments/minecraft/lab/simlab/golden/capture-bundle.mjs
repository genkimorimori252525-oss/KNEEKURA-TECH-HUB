import { lstat, readFile, realpath } from 'node:fs/promises';
import { isAbsolute, resolve, sep } from 'node:path';
import { decodePng } from './png.mjs';

export const REAL_CLIENT_GOLDEN_SCHEMA = 'kneekura.real-client-golden-capture';
export const REAL_CLIENT_GOLDEN_VERSION = 2;

export class GoldenBundleError extends Error {
  constructor(message, path = '$') {
    super(path + ': ' + message);
    this.name = 'GoldenBundleError';
    this.path = path;
  }
}

function fail(message, path) {
  throw new GoldenBundleError(message, path);
}

function object(value, path) {
  if (value == null || typeof value !== 'object' || Array.isArray(value)) fail('expected object', path);
  return value;
}

function string(value, path) {
  if (typeof value !== 'string' || value.length === 0) fail('expected non-empty string', path);
  return value;
}

function finite(value, path) {
  if (typeof value !== 'number' || !Number.isFinite(value)) fail('expected finite number', path);
  return value;
}

function positiveInt(value, path) {
  if (!Number.isSafeInteger(value) || value <= 0) fail('expected positive safe integer', path);
  return value;
}

function safeRelative(value, path) {
  string(value, path);
  if (isAbsolute(value) || /^[A-Za-z]:[\\/]/.test(value)) fail('absolute path forbidden', path);
  const clean = value.replaceAll('\\', '/');
  const parts = clean.split('/');
  if (parts.some((part) => part === '' || part === '.' || part === '..')) fail('unsafe relative path', path);
  return clean;
}

async function readRegularInside(root, relative, path) {
  const clean = safeRelative(relative, path);
  const absRoot = await realpath(root);
  const abs = resolve(absRoot, clean);
  if (abs !== absRoot && !abs.startsWith(absRoot + sep)) fail('path escapes bundle root', path);
  const stat = await lstat(abs);
  if (stat.isSymbolicLink()) fail('symbolic-link input forbidden', path);
  if (!stat.isFile()) fail('expected regular file', path);
  const fileReal = await realpath(abs);
  if (fileReal !== absRoot && !fileReal.startsWith(absRoot + sep)) fail('resolved path escapes bundle root', path);
  return readFile(fileReal);
}

function numberArray(value, length, path) {
  if (!Array.isArray(value) || value.length !== length) fail('expected array length ' + length, path);
  value.forEach((x, i) => finite(x, path + '[' + i + ']'));
  return value;
}

export function validateGoldenCaptureJson(root) {
  object(root, '$');
  if (root.schema !== 'kneekura.runtime-final-vertex-capture') {
    fail('expected runtime final-vertex raw capture', '$.schema');
  }
  if (root.runBound !== true || root.runId === 'unbound') {
    fail('Golden evidence requires bound run identity', '$.runId');
  }
  string(root.runId, '$.runId');
  string(root.entityUuid, '$.entityUuid');
  if (!Number.isSafeInteger(root.renderSequence) || root.renderSequence < 0) {
    fail('invalid renderSequence', '$.renderSequence');
  }
  finite(root.partialTick, '$.partialTick');

  const golden = object(root.golden, '$.golden');
  if (golden.schema !== REAL_CLIENT_GOLDEN_SCHEMA) fail('unexpected Golden schema', '$.golden.schema');
  if (golden.schemaVersion !== REAL_CLIENT_GOLDEN_VERSION) fail('unexpected Golden version', '$.golden.schemaVersion');
  if (golden.targetEntityUuid !== root.entityUuid) fail('target entity does not match raw frame', '$.golden.targetEntityUuid');
  if (golden.preStage !== 'AFTER_CUTOUT_BLOCKS') fail('unexpected pre stage', '$.golden.preStage');
  if (golden.postStage !== 'AFTER_ENTITIES') fail('unexpected post stage', '$.golden.postStage');
  if (golden.requiresIsolatedEntityScene !== true) fail('isolated entity scene must be explicit', '$.golden.requiresIsolatedEntityScene');
  if (golden.requiresYsmOnlyFallbackInactive !== true
      || golden.preYsmChatBubbleIncluded !== false
      || golden.postYsmFallbackEffectsIncluded !== false) {
    fail('YSM-only Golden evidence requires proven-inactive chat/fallback effects', '$.golden');
  }
  if (golden.dispatcherShadowSuppressed !== true
      || golden.dispatcherHitboxSuppressed !== true
      || golden.dispatcherFireOverlayIncluded !== false
      || golden.glowingOutlineIncluded !== false) {
    fail('YSM-only Golden evidence requires dispatcher extras to be excluded', '$.golden');
  }
  if (golden.guiIncluded !== false || golden.particlesIncluded !== false || golden.weatherIncluded !== false) {
    fail('Golden v1 target must exclude GUI/particles/weather', '$.golden');
  }
  safeRelative(golden.backgroundFile, '$.golden.backgroundFile');
  safeRelative(golden.backgroundDepthFile, '$.golden.backgroundDepthFile');
  safeRelative(golden.goldenFile, '$.golden.goldenFile');
  const depth = object(golden.backgroundDepth, '$.golden.backgroundDepth');
  if (depth.encoding !== 'FLOAT32_LE') fail('unexpected depth encoding', '$.golden.backgroundDepth.encoding');
  if (depth.origin !== 'bottom-left') fail('unexpected depth origin', '$.golden.backgroundDepth.origin');
  if (depth.range !== 'OPENGL_DEPTH_0_1') fail('unexpected depth range', '$.golden.backgroundDepth.range');
  positiveInt(depth.width, '$.golden.backgroundDepth.width');
  positiveInt(depth.height, '$.golden.backgroundDepth.height');

  const camera = object(golden.camera, '$.golden.camera');
  positiveInt(camera.renderTick, '$.golden.camera.renderTick');
  positiveInt(camera.framebufferWidth, '$.golden.camera.framebufferWidth');
  positiveInt(camera.framebufferHeight, '$.golden.camera.framebufferHeight');
  positiveInt(camera.viewportWidth, '$.golden.camera.viewportWidth');
  positiveInt(camera.viewportHeight, '$.golden.camera.viewportHeight');
  positiveInt(camera.windowWidth, '$.golden.camera.windowWidth');
  positiveInt(camera.windowHeight, '$.golden.camera.windowHeight');
  positiveInt(camera.guiScaledWidth, '$.golden.camera.guiScaledWidth');
  positiveInt(camera.guiScaledHeight, '$.golden.camera.guiScaledHeight');
  numberArray(camera.position, 3, '$.golden.camera.position');
  numberArray(camera.rotationQuaternion, 4, '$.golden.camera.rotationQuaternion');
  numberArray(camera.projectionMatrix, 16, '$.golden.camera.projectionMatrix');
  finite(camera.xRot, '$.golden.camera.xRot');
  finite(camera.yRot, '$.golden.camera.yRot');
  finite(camera.partialTick, '$.golden.camera.partialTick');
  if (camera.partialTick !== root.partialTick) {
    fail('camera partialTick does not match raw frame', '$.golden.camera.partialTick');
  }
  if (camera.matrixConvention !== 'JOML_COLUMN_MAJOR_COLUMN_VECTOR') {
    fail('unexpected matrix convention', '$.golden.camera.matrixConvention');
  }
  if (depth.width !== camera.framebufferWidth || depth.height !== camera.framebufferHeight) {
    fail('depth dimensions do not match camera framebuffer', '$.golden.backgroundDepth');
  }

  return root;
}

export function decodeDepthF32Le(bytes, width, height) {
  positiveInt(width, '$depth.width');
  positiveInt(height, '$depth.height');
  const count = width * height;
  if (!Number.isSafeInteger(count)) fail('unsafe depth dimensions', '$depth');
  const buf = Buffer.isBuffer(bytes) ? bytes : Buffer.from(bytes);
  if (buf.length !== count * 4) fail(`depth byteLength ${buf.length} does not match ${width}x${height} float32`, '$depth');
  const values = new Float32Array(count);
  for (let i = 0; i < count; i++) {
    const value = buf.readFloatLE(i * 4);
    if (!Number.isFinite(value) || value < 0 || value > 1) fail('depth value must be finite in [0,1]', `$depth[${i}]`);
    values[i] = value;
  }
  return values;
}
export async function loadRealClientGoldenBundle(captureDir) {
  const dir = await realpath(resolve(captureDir));
  const captureBytes = await readRegularInside(dir, 'capture.json', '$.capture');
  const root = validateGoldenCaptureJson(JSON.parse(captureBytes.toString('utf8')));
  const [backgroundBytes, depthBytes, goldenBytes] = await Promise.all([
    readRegularInside(dir, root.golden.backgroundFile, '$.golden.backgroundFile'),
    readRegularInside(dir, root.golden.backgroundDepthFile, '$.golden.backgroundDepthFile'),
    readRegularInside(dir, root.golden.goldenFile, '$.golden.goldenFile'),
  ]);
  const background = decodePng(backgroundBytes);
  const depthValues = decodeDepthF32Le(depthBytes, root.golden.backgroundDepth.width, root.golden.backgroundDepth.height);
  const golden = decodePng(goldenBytes);

  const width = root.golden.camera.framebufferWidth;
  const height = root.golden.camera.framebufferHeight;
  if (background.width !== width || background.height !== height) {
    fail('background PNG dimensions do not match camera framebuffer', '$.golden.backgroundFile');
  }
  if (golden.width !== width || golden.height !== height) {
    fail('golden PNG dimensions do not match camera framebuffer', '$.golden.goldenFile');
  }

  let changed = false;
  for (let i = 0; i < background.rgba.length; i++) {
    if (background.rgba[i] !== golden.rgba[i]) {
      changed = true;
      break;
    }
  }
  if (!changed) {
    fail('background and golden PNG are identical; no entity framebuffer contribution was observed',
      '$.golden.goldenFile');
  }

  return {
    capture: root,
    background: { bytes: backgroundBytes, ...background },
    depth: { bytes: depthBytes, values: depthValues, ...root.golden.backgroundDepth },
    golden: { bytes: goldenBytes, ...golden },
  };
}