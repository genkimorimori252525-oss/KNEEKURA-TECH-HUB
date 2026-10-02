import { createHash } from 'node:crypto';
import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import {
  lstat,
  mkdtemp,
  readFile,
  realpath,
  rm,
  stat,
  writeFile,
} from 'node:fs/promises';
import { tmpdir } from 'node:os';
import {
  dirname,
  isAbsolute,
  join,
  resolve,
  sep,
} from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  assertFrameCompatible,
  assertRenderFrameIR,
} from '../contracts/render-v1/validator.mjs';
import { loadRealClientGoldenBundle } from '../golden/capture-bundle.mjs';
import { assertGoldenFrameBound } from '../golden/bound-oracle.mjs';
import { decodePng, encodePngRgba } from '../golden/png.mjs';
import { loadRenderPack } from '../renderpack/loader.mjs';
import {
  buildFinalVertexReplayPlan,
  validateFinalVertexBuffer,
} from './thin-final-vertex.js';

export const HEADLESS_RENDER_SCHEMA = 'kneekura.thin-viewer-headless-render';
export const HEADLESS_RENDER_VERSION = 1;

export class HeadlessFinalVertexError extends Error {
  constructor(message) {
    super(message);
    this.name = 'HeadlessFinalVertexError';
  }
}

function fail(message) {
  throw new HeadlessFinalVertexError(message);
}

function sha256(bytes) {
  return 'sha256:' + createHash('sha256').update(bytes).digest('hex');
}

async function regularFile(path, label) {
  const info = await lstat(path);
  if (info.isSymbolicLink()) fail(label + ' must not be a symbolic link');
  if (!info.isFile()) fail(label + ' must be a regular file');
  return readFile(path);
}

function safeRelative(relative, label) {
  if (typeof relative !== 'string' || relative.length === 0) fail(label + ' is empty');
  if (isAbsolute(relative) || /^[A-Za-z]:[\\/]/.test(relative)) fail(label + ' must be relative');
  const clean = relative.replaceAll('\\', '/');
  const parts = clean.split('/');
  if (parts.some((part) => part === '' || part === '.' || part === '..')) {
    fail(label + ' is unsafe');
  }
  return clean;
}

async function readInside(root, relative, label) {
  const clean = safeRelative(relative, label);
  const rootReal = await realpath(root);
  const path = resolve(rootReal, clean);
  if (path !== rootReal && !path.startsWith(rootReal + sep)) fail(label + ' escapes root');
  const info = await lstat(path);
  if (info.isSymbolicLink()) fail(label + ' must not be a symbolic link');
  if (!info.isFile()) fail(label + ' must be a regular file');
  const fileReal = await realpath(path);
  if (fileReal !== rootReal && !fileReal.startsWith(rootReal + sep)) {
    fail(label + ' resolves outside root');
  }
  return readFile(fileReal);
}

export function flipRgbaRows(rgba, width, height) {
  const src = rgba instanceof Uint8Array ? rgba : new Uint8Array(rgba);
  if (!Number.isInteger(width) || width <= 0 || !Number.isInteger(height) || height <= 0) {
    fail('invalid RGBA dimensions');
  }
  if (src.length !== width * height * 4) fail('RGBA byte length does not match dimensions');
  const row = width * 4;
  const out = new Uint8Array(src.length);
  for (let y = 0; y < height; y++) {
    out.set(src.subarray(y * row, (y + 1) * row), (height - 1 - y) * row);
  }
  return out;
}

function encodeDepthF32Le(values, width, height) {
  if (!(values instanceof Float32Array) || values.length !== width * height) {
    fail('depth values do not match framebuffer dimensions');
  }
  const out = Buffer.alloc(values.length * 4);
  for (let i = 0; i < values.length; i++) {
    const value = values[i];
    if (!Number.isFinite(value) || value < 0 || value > 1) fail('invalid depth value');
    out.writeFloatLE(value, i * 4);
  }
  return out;
}

async function existsFile(path) {
  try {
    return (await stat(path)).isFile();
  } catch {
    return false;
  }
}

export async function findHeadlessBrowser(explicit = process.env.KNEEKURA_HEADLESS_BROWSER) {
  const candidates = [];
  if (explicit) candidates.push(explicit);
  if (process.platform === 'win32') {
    for (const root of [
      process.env['ProgramFiles(x86)'],
      process.env.ProgramFiles,
      process.env.LOCALAPPDATA,
    ]) {
      if (!root) continue;
      candidates.push(join(root, 'Microsoft', 'Edge', 'Application', 'msedge.exe'));
      candidates.push(join(root, 'Google', 'Chrome', 'Application', 'chrome.exe'));
    }
  } else if (process.platform === 'linux') {
    candidates.push(
      '/usr/bin/microsoft-edge',
      '/usr/bin/microsoft-edge-stable',
      '/usr/bin/google-chrome',
      '/usr/bin/google-chrome-stable',
      '/usr/bin/chromium',
      '/usr/bin/chromium-browser',
    );
  } else if (process.platform === 'darwin') {
    candidates.push(
      '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
      '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    );
  }
  for (const candidate of [...new Set(candidates)]) {
    if (candidate && await existsFile(candidate)) return candidate;
  }
  fail('Edge/Chrome browser not found; set KNEEKURA_HEADLESS_BROWSER explicitly');
}

function collectBody(request, limit) {
  return new Promise((resolveBody, rejectBody) => {
    const chunks = [];
    let total = 0;
    request.on('data', (chunk) => {
      total += chunk.length;
      if (total > limit) {
        rejectBody(new HeadlessFinalVertexError('HTTP body exceeded safe limit'));
        request.destroy();
        return;
      }
      chunks.push(chunk);
    });
    request.on('end', () => resolveBody(Buffer.concat(chunks, total)));
    request.on('error', rejectBody);
  });
}

async function stopBrowser(child, profile) {
  if (process.platform === 'win32') {
    const escaped = String(profile).replaceAll("'", "''");
    const script = [
      "$needle = '" + escaped + "'",
      "$targets = Get-CimInstance Win32_Process | Where-Object {",
      "  $_.CommandLine -and $_.CommandLine.Contains($needle)",
      "}",
      "foreach ($p in $targets) {",
      "  & taskkill /PID $p.ProcessId /T /F 2>$null | Out-Null",
      "}",
    ].join('; ');
    await new Promise((resolveStop) => {
      const killer = spawn(
        'powershell',
        ['-NoProfile', '-NonInteractive', '-Command', script],
        { stdio: 'ignore', windowsHide: true },
      );
      const done = () => resolveStop();
      killer.on('exit', done);
      killer.on('error', done);
    });
    return;
  }
  if (child && !child.killed) {
    try { child.kill('SIGKILL'); } catch {}
  }
}

function defaultAngleBackend() {
  if (process.env.KNEEKURA_ANGLE_BACKEND) return process.env.KNEEKURA_ANGLE_BACKEND;
  return process.platform === 'win32' ? 'd3d11-warp-webgl' : '';
}

function browserArgs(profile, url, requestedAngleBackend, extraArgs = []) {
  return [
    '--headless=new',
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-background-networking',
    '--disable-component-update',
    '--disable-default-apps',
    '--disable-extensions',
    '--disable-sync',
    '--metrics-recording-only',
    '--disable-gpu-sandbox',
    '--disable-gpu-compositing',
    '--use-cmd-decoder=passthrough',
    '--remote-debugging-port=0',
    '--remote-allow-origins=*',
    ...(requestedAngleBackend ? ['--use-gl=angle', '--use-angle=' + requestedAngleBackend] : []),
    ...(requestedAngleBackend.startsWith('swiftshader') ? ['--enable-unsafe-swiftshader'] : []),
    '--window-size=800,600',
    '--hide-scrollbars',
    '--user-data-dir=' + profile,
    ...extraArgs,
    url,
  ];
}

function contentType(path) {
  if (path.endsWith('.js')) return 'text/javascript; charset=utf-8';
  if (path.endsWith('.json')) return 'application/json; charset=utf-8';
  return 'application/octet-stream';
}

async function runBrowserJob({
  job,
  frameBytes,
  backgroundBottomUp,
  depthBytes,
  textures,
  browserPath,
  angleBackend = defaultAngleBackend(),
  browserExtraArgs = [],
  timeoutMs = 60000,
}) {
  const pageSource = await readFile(
    fileURLToPath(new URL('./headless-final-vertex-page.js', import.meta.url)),
  );
  const thinSource = await readFile(
    fileURLToPath(new URL('./thin-final-vertex.js', import.meta.url)),
  );
  const textureByUrl = new Map(textures.map((texture, index) => [
    '/texture/' + index + '.rgba',
    texture.rgba,
  ]));
  job.textures = textures.map((texture, index) => ({
    path: texture.path,
    width: texture.width,
    height: texture.height,
    url: '/texture/' + index + '.rgba',
  }));

  let settle;
  const resultPromise = new Promise((resolveResult, rejectResult) => {
    settle = { resolve: resolveResult, reject: rejectResult };
  });
  let settled = false;
  const settleOnce = (kind, value) => {
    if (settled) return;
    settled = true;
    settle[kind](value);
  };

  const expectedResultBytes = job.framebuffer.width * job.framebuffer.height * 4;
  const requestTrace = [];
  const checkpoints = [];
  let aliveSeen = false;
  const server = createServer(async (request, response) => {
    try {
      const url = new URL(request.url || '/', 'http://127.0.0.1');
      requestTrace.push((request.method || 'GET') + ' ' + url.pathname);
      if (requestTrace.length > 64) requestTrace.shift();
      if (request.method === 'GET' && url.pathname === '/') {
        const html = '<!doctype html><meta charset="utf-8">'
          + '<title>KNEEKURA Headless Thin Viewer</title>'
          + '<script>fetch("/alive",{method:"POST"}).catch(()=>{});</script>'
          + '<script type="module" src="/headless-final-vertex-page.js"></script>';
        response.writeHead(200, { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' });
        response.end(html);
        return;
      }
      if (request.method === 'POST' && url.pathname === '/checkpoint') {
        const name = url.searchParams.get('name') || '';
        if (name) {
          checkpoints.push(name);
          console.log('[HEADLESS_CHECKPOINT] ' + name);
        }
        if (checkpoints.length > 64) checkpoints.shift();
        response.writeHead(204);
        response.end();
        return;
      }
      if (request.method === 'POST' && url.pathname === '/alive') {
        aliveSeen = true;
        response.writeHead(204);
        response.end();
        return;
      }
      const staticFiles = new Map([
        ['/headless-final-vertex-page.js', pageSource],
        ['/thin-final-vertex.js', thinSource],
        ['/job.json', Buffer.from(JSON.stringify(job), 'utf8')],
        ['/frame.bin', frameBytes],
        ['/background.rgba', backgroundBottomUp],
        ['/background.depth', depthBytes],
      ]);
      if (request.method === 'GET' && staticFiles.has(url.pathname)) {
        const body = staticFiles.get(url.pathname);
        response.writeHead(200, {
          'content-type': contentType(url.pathname),
          'content-length': body.length,
          'cache-control': 'no-store',
        });
        response.end(body);
        return;
      }
      if (request.method === 'GET' && textureByUrl.has(url.pathname)) {
        const body = textureByUrl.get(url.pathname);
        response.writeHead(200, {
          'content-type': 'application/octet-stream',
          'content-length': body.length,
          'cache-control': 'no-store',
        });
        response.end(body);
        return;
      }
      if (request.method === 'POST' && url.pathname === '/result') {
        const body = await collectBody(request, expectedResultBytes + 1);
        if (body.length !== expectedResultBytes) {
          throw new HeadlessFinalVertexError(
            'browser RGBA length ' + body.length + ' != ' + expectedResultBytes,
          );
        }
        const width = Number(url.searchParams.get('width'));
        const height = Number(url.searchParams.get('height'));
        if (width !== job.framebuffer.width || height !== job.framebuffer.height) {
          throw new HeadlessFinalVertexError('browser framebuffer dimensions changed');
        }
        response.writeHead(204);
        response.end();
        settleOnce('resolve', {
          rgbaBottomUp: new Uint8Array(body),
          angleBackend,
          gl: {
            vendor: url.searchParams.get('vendor') || '',
            renderer: url.searchParams.get('renderer') || '',
            version: url.searchParams.get('version') || '',
            shadingLanguage: url.searchParams.get('shadingLanguage') || '',
          },
        });
        return;
      }
      if (request.method === 'POST' && url.pathname === '/error') {
        const body = await collectBody(request, 1024 * 1024);
        response.writeHead(204);
        response.end();
        settleOnce(
          'reject',
          new HeadlessFinalVertexError('browser render failed:\n' + body.toString('utf8')),
        );
        return;
      }
      response.writeHead(404);
      response.end('not found');
    } catch (error) {
      response.writeHead(500);
      response.end(String(error));
      settleOnce('reject', error);
    }
  });

  await new Promise((resolveListen, rejectListen) => {
    server.once('error', rejectListen);
    server.listen(0, '127.0.0.1', resolveListen);
  });
  const address = server.address();
  if (!address || typeof address === 'string') {
    server.close();
    fail('cannot resolve local headless server address');
  }

  const profile = await mkdtemp(join(tmpdir(), 'kneekura-headless-browser-'));
  const url = 'http://127.0.0.1:' + address.port + '/';
  let stdout = '';
  let stderr = '';
  let launcherExit = null;
  const child = spawn(
    browserPath,
    browserArgs(profile, url, angleBackend, browserExtraArgs),
    { stdio: ['ignore', 'pipe', 'pipe'], windowsHide: true },
  );
  child.stdout?.on('data', (chunk) => {
    stdout += chunk.toString('utf8');
    if (stdout.length > 32768) stdout = stdout.slice(-32768);
  });
  child.stderr?.on('data', (chunk) => {
    stderr += chunk.toString('utf8');
    if (stderr.length > 32768) stderr = stderr.slice(-32768);
  });
  child.on('error', (error) => settleOnce('reject', error));
  child.on('exit', (code, signal) => {
    launcherExit = { code, signal };
    if (!settled && code !== 0) {
      settleOnce(
        'reject',
        new HeadlessFinalVertexError(
          'browser launcher failed: code=' + code + ', signal=' + signal
          + (stdout ? '\nstdout:\n' + stdout : '')
          + (stderr ? '\nstderr:\n' + stderr : ''),
        ),
      );
    }
  });

  const timer = setTimeout(() => {
    settleOnce(
      'reject',
      new HeadlessFinalVertexError(
        'headless browser render timed out after ' + timeoutMs + 'ms'
        + (launcherExit ? '\nlauncherExit=' + JSON.stringify(launcherExit) : '')
        + '\naliveSeen=' + aliveSeen
        + '\nrequestTrace=' + JSON.stringify(requestTrace)
        + '\ncheckpoints=' + JSON.stringify(checkpoints)
        + (stdout ? '\nstdout:\n' + stdout : '')
        + (stderr ? '\nstderr:\n' + stderr : ''),
      ),
    );
  }, timeoutMs);

  try {
    return await resultPromise;
  } finally {
    clearTimeout(timer);
    await stopBrowser(child, profile);
    if (typeof server.closeAllConnections === 'function') server.closeAllConnections();
    await new Promise((resolveClose) => {
      const force = setTimeout(resolveClose, 2000);
      server.close(() => {
        clearTimeout(force);
        resolveClose();
      });
    });
    await rm(profile, { recursive: true, force: true }).catch(() => {});
  }
}

export async function renderHeadlessFinalVertexBuffers(options) {
  const {
    frame,
    pack,
    frameBytes,
    background,
    depth,
    textureImages,
    framebuffer,
    browserPath = await findHeadlessBrowser(),
    angleBackend = defaultAngleBackend(),
    browserExtraArgs = [],
    timeoutMs = 60000,
  } = options || {};
  assertRenderFrameIR(frame);
  validateFinalVertexBuffer(frame, frameBytes);
  const plan = buildFinalVertexReplayPlan(frame, pack);

  if (!background || background.width !== framebuffer.width || background.height !== framebuffer.height) {
    fail('background dimensions do not match framebuffer');
  }
  if (!depth || depth.width !== framebuffer.width || depth.height !== framebuffer.height) {
    fail('depth dimensions do not match framebuffer');
  }
  if (!(depth.values instanceof Float32Array)) fail('depth.values must be Float32Array');

  const textureMap = textureImages instanceof Map
    ? textureImages
    : new Map(Object.entries(textureImages || {}));
  const textures = [];
  for (const path of [...new Set(plan.groups.map((group) => group.sampler0.texture))]) {
    const image = textureMap.get(path);
    if (!image) fail('missing decoded texture image ' + path);
    const rgba = image.rgba instanceof Uint8Array ? image.rgba : new Uint8Array(image.rgba);
    if (rgba.length !== image.width * image.height * 4) fail('invalid texture RGBA ' + path);
    textures.push({ path, width: image.width, height: image.height, rgba });
  }

  const job = {
    frame,
    pack: {
      manifest: pack.manifest,
      mesh: pack.mesh,
      materials: pack.materials,
    },
    framebuffer: {
      width: framebuffer.width,
      height: framebuffer.height,
      viewportWidth: framebuffer.viewportWidth,
      viewportHeight: framebuffer.viewportHeight,
    },
    textures: [],
  };
  const backgroundBottomUp = flipRgbaRows(
    background.rgba,
    background.width,
    background.height,
  );
  const depthBytes = encodeDepthF32Le(depth.values, depth.width, depth.height);

  const browser = await runBrowserJob({
    job,
    frameBytes: frameBytes instanceof Uint8Array ? frameBytes : new Uint8Array(frameBytes),
    backgroundBottomUp,
    depthBytes,
    textures,
    browserPath,
    angleBackend,
    browserExtraArgs,
    timeoutMs,
  });
  const rgbaTopDown = flipRgbaRows(
    browser.rgbaBottomUp,
    framebuffer.width,
    framebuffer.height,
  );
  return {
    width: framebuffer.width,
    height: framebuffer.height,
    rgba: rgbaTopDown,
    browserPath,
    angleBackend: browser.angleBackend,
    gl: browser.gl,
  };
}

async function verifiedPackTexture(pack, relative) {
  const clean = safeRelative(relative, 'texture path');
  const entry = pack.manifest.files.find((file) => file.path === clean);
  if (!entry) fail('texture is not listed in Render Pack manifest: ' + clean);
  const bytes = await readInside(pack.root, clean, 'texture ' + clean);
  const actual = sha256(bytes);
  if (actual !== entry.sha256) {
    fail('texture hash changed after Render Pack validation: ' + clean);
  }
  const decoded = decodePng(bytes);
  return { width: decoded.width, height: decoded.height, rgba: decoded.rgba };
}

export async function renderBoundGoldenFrame(options) {
  const {
    captureDir,
    packDir,
    frameJsonPath,
    outputPngPath,
    metadataPath = outputPngPath + '.json',
    browserPath,
    browserExtraArgs = [],
    timeoutMs = 60000,
  } = options || {};
  if (!captureDir || !packDir || !frameJsonPath || !outputPngPath) {
    fail('captureDir, packDir, frameJsonPath, and outputPngPath are required');
  }

  const bundle = await loadRealClientGoldenBundle(captureDir);
  const pack = await loadRenderPack(packDir);

  const resolvedFrameJson = await realpath(resolve(frameJsonPath));
  const frameJsonBytes = await regularFile(resolvedFrameJson, 'RenderFrame JSON');
  const frame = JSON.parse(frameJsonBytes.toString('utf8'));
  assertRenderFrameIR(frame);
  assertFrameCompatible(frame, pack.manifest);
  assertGoldenFrameBound(bundle.capture, frame);

  const frameRoot = dirname(resolvedFrameJson);
  const frameBytes = await readInside(
    frameRoot,
    frame.deformation.bufferRef,
    'RenderFrame buffer',
  );
  validateFinalVertexBuffer(frame, frameBytes);
  if (frame.deformation.sha256 && sha256(frameBytes) !== frame.deformation.sha256) {
    fail('RenderFrame buffer hash mismatch');
  }

  const plan = buildFinalVertexReplayPlan(frame, pack);
  const textureImages = new Map();
  for (const path of [...new Set(plan.groups.map((group) => group.sampler0.texture))]) {
    textureImages.set(path, await verifiedPackTexture(pack, path));
  }

  const fb = frame.goldenBinding.framebuffer;
  const rendered = await renderHeadlessFinalVertexBuffers({
    frame,
    pack,
    frameBytes,
    background: bundle.background,
    depth: {
      width: bundle.depth.width,
      height: bundle.depth.height,
      values: bundle.depth.values,
    },
    textureImages,
    framebuffer: fb,
    browserPath: browserPath || await findHeadlessBrowser(),
    browserExtraArgs,
    timeoutMs,
  });
  const png = encodePngRgba(rendered);
  await writeFile(resolve(outputPngPath), png);

  const metadata = {
    schema: HEADLESS_RENDER_SCHEMA,
    schemaVersion: HEADLESS_RENDER_VERSION,
    identity: {
      runId: frame.runId,
      entityUuid: frame.entityUuid,
      renderSequence: frame.renderSequence,
      gameTime: frame.gameTime,
      partialTick: frame.partialTick,
      renderTick: frame.goldenBinding.renderTick,
    },
    framebuffer: structuredClone(fb),
    browser: {
      executable: rendered.browserPath,
      gl: rendered.gl,
      requestedAngleBackend: rendered.angleBackend || 'platform-default',
    },
    inputs: {
      renderFrameJsonSha256: sha256(frameJsonBytes),
      renderFrameBufferSha256: sha256(frameBytes),
      backgroundPngSha256: sha256(bundle.background.bytes),
      backgroundDepthSha256: sha256(bundle.depth.bytes),
    },
    output: {
      viewerPngSha256: sha256(png),
    },
  };
  await writeFile(resolve(metadataPath), JSON.stringify(metadata, null, 2) + '\n', 'utf8');
  return { ...rendered, png, metadata };
}
