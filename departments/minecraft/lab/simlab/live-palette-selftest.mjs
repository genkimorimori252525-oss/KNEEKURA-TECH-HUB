import assert from 'node:assert/strict';
import net from 'node:net';
import { spawn } from 'node:child_process';
import {
  LIVE_PALETTE_MAGIC,
  LIVE_PALETTE_STRIDE,
  LIVE_PALETTE_VERSION,
  createLivePaletteHub,
  decodeLivePaletteFrame,
  livePaletteLayoutHash,
} from './live-palette.mjs';

const UUID = '01234567-89ab-cdef-0123-456789abcdef';
const NAMES = ['root', 'body', 'qunzi'];

function i32(value) { const b = Buffer.alloc(4); b.writeInt32BE(value); return b; }
function u16(value) { const b = Buffer.alloc(2); b.writeUInt16BE(value); return b; }
function i64(value) { const b = Buffer.alloc(8); b.writeBigInt64BE(BigInt(value)); return b; }
function u64(value) { const b = Buffer.alloc(8); b.writeBigUInt64BE(BigInt.asUintN(64, value)); return b; }
function f32(value) { const b = Buffer.alloc(4); b.writeFloatBE(value); return b; }
function string(value) { const b = Buffer.from(value, 'utf8'); return Buffer.concat([i32(b.length), b]); }

function encode(sequence, overrides = {}) {
  const names = overrides.names || NAMES;
  const modelId = overrides.modelId ?? 'ysm:reimu';
  const modelTexture = overrides.modelTexture ?? 'reimu/texture.png';
  const geometryType = overrides.geometryType ?? 'ysm.Model#root.renderer';
  const palette = new Array(names.length * LIVE_PALETTE_STRIDE)
    .fill(0).map((_, i) => i / 16 + Number(sequence));
  const uuidHex = (overrides.uuid || UUID).replaceAll('-', '');
  const layoutHash = livePaletteLayoutHash(modelId, modelTexture, geometryType, names);
  const parts = [
    i32(LIVE_PALETTE_MAGIC), u16(LIVE_PALETTE_VERSION), u16(LIVE_PALETTE_STRIDE),
    i64(sequence), i64(overrides.gameTime ?? (1000n + BigInt(sequence))), f32(0.5), i32(77),
    Buffer.from(uuidHex, 'hex'), u64(layoutHash), string('touhou_little_maid:maid'),
    string(modelId), string(modelTexture), string(geometryType), i32(names.length),
    ...names.map(string), i32(palette.length), ...palette.map(f32),
  ];
  return Buffer.concat(parts);
}

function packet(body) { return Buffer.concat([i32(body.length), body]); }
function sleep(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }
async function waitFor(predicate, message, timeout = 3000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) {
    if (await predicate()) return;
    await sleep(10);
  }
  assert.fail(message);
}
async function connect(port) {
  const socket = net.createConnection({ host: '127.0.0.1', port });
  await new Promise((resolve, reject) => {
    socket.once('connect', resolve);
    socket.once('error', reject);
  });
  return socket;
}
async function freePort() {
  const server = net.createServer();
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen({ host: '127.0.0.1', port: 0 }, resolve);
  });
  const port = server.address().port;
  await new Promise((resolve) => server.close(resolve));
  return port;
}

const standalone = decodeLivePaletteFrame(encode(1));
assert.equal(livePaletteLayoutHash('ysm:reimu', 'reimu/texture.png',
  'ysm.Model#root.renderer', NAMES), 0xa0def8774c81cdd2n);
assert.equal(standalone.uuid, UUID);
assert.equal(standalone.modelId, 'ysm:reimu');
assert.deepEqual(standalone.boneNames, NAMES);
assert.equal(standalone.palette.length, NAMES.length * LIVE_PALETTE_STRIDE * 4);

const hub = createLivePaletteHub({ host: '127.0.0.1', port: 0, historyLimit: 3, identityLimit: 4 });
const address = await hub.start();
const frames = [];
const statuses = [];
const unsubscribe = hub.subscribe({ uuid: UUID, modelId: 'ysm:reimu' }, (event) => {
  if (event.type === 'frame') frames.push(event.frame);
  else statuses.push(hub.statusFor(UUID, 'ysm:reimu'));
});
let source = null;
let badSource = null;
try {
  source = await connect(address.port);
  const first = packet(encode(1));
  source.write(first.subarray(0, 3));
  source.write(first.subarray(3, 19));
  source.write(first.subarray(19));
  await waitFor(() => frames.length === 1, 'fragmented valid frame was not delivered');
  assert.equal(frames[0].gameTime, 1001n);

  for (let sequence = 2; sequence <= 5; sequence++) source.write(packet(encode(sequence)));
  await waitFor(() => frames.length === 5, 'valid frame sequence was not delivered');
  assert.equal(hub.status().accepted, 5);

  const replay = [];
  const stopReplay = hub.subscribe({ uuid: UUID, modelId: 'ysm:reimu' }, (event) => {
    if (event.type === 'frame') replay.push(Number(event.frame.sequence));
  });
  assert.deepEqual(replay, [3, 4, 5], 'memory history must be capped at the latest three frames');
  stopReplay();

  // 同じ接続で古い sequence は捨てる。履歴にも subscriber にも混ぜない。
  source.write(packet(encode(4, { gameTime: 1006n })));
  await waitFor(() => hub.status().outOfOrder === 1, 'out-of-order frame was not rejected');
  assert.equal(frames.length, 5);

  const mismatched = [];
  const stopMismatch = hub.subscribe({ uuid: UUID, modelId: 'ysm:other' }, (event) => {
    if (event.type === 'frame') mismatched.push(event.frame);
  });
  source.write(packet(encode(6)));
  await waitFor(() => frames.length === 6, 'latest valid frame was not delivered');
  assert.equal(mismatched.length, 0);
  assert.equal(hub.statusFor(UUID, 'ysm:other').identityMatches, false);
  stopMismatch();

  // layout hash を壊した frame は接続ごと閉じ、正常履歴を更新しない。
  badSource = await connect(address.port);
  const corrupt = encode(7);
  corrupt[48] ^= 0x01;
  badSource.write(packet(corrupt));
  await waitFor(() => hub.status().rejected === 1, 'invalid identity frame was not rejected');
  assert.equal(frames.length, 6);
  await waitFor(() => badSource.destroyed, 'invalid source connection was not closed');

  source.destroy();
  await waitFor(() => !hub.status().sourceConnected, 'disconnect state was not exposed');
  assert.ok(statuses.some((s) => s.sourceConnected), 'connected status was never emitted');
} finally {
  unsubscribe();
  if (source) source.destroy();
  if (badSource) badSource.destroy();
  await hub.close();
}

console.log('live-palette-selftest: OK (protocol, latest-only history, identity, disconnect)');

// serve.mjs の HTTP/SSE 配線も実 socket で通す。hub 単体が緑でも route が未配線なら落ちる。
const httpPort = await freePort();
let palettePort = await freePort();
while (palettePort === httpPort) palettePort = await freePort();
const child = spawn(process.execPath,
  ['simlab/serve.mjs', '--port', String(httpPort), '--palette-port', String(palettePort)],
  { stdio: ['ignore', 'pipe', 'pipe'] });
let serveLog = '';
child.stdout.on('data', (chunk) => { serveLog += chunk; });
child.stderr.on('data', (chunk) => { serveLog += chunk; });
let serveSource = null;
const abort = new AbortController();
try {
  await waitFor(async () => {
    try {
      const response = await fetch(`http://127.0.0.1:${httpPort}/api/live-palette/status`);
      return response.ok && (await response.json()).listening;
    } catch { return false; }
  }, `serve.mjs did not expose palette status: ${serveLog}`, 5000);
  const invalid = await fetch(`http://127.0.0.1:${httpPort}/api/live-palette?uuid=bad`);
  assert.equal(invalid.status, 400);
  const embeddedTexture = await fetch(`http://127.0.0.1:${httpPort}/api/tex?id=${
    encodeURIComponent('touhou_little_maid:textures/entity/hakurei_reimu.png')}`);
  assert.equal(embeddedTexture.status, 200, 'embedded TLM custom-pack texture must resolve');
  assert.match(embeddedTexture.headers.get('content-type') || '', /^image\/png/);
  assert.ok((await embeddedTexture.arrayBuffer()).byteLength > 0);

  const response = await fetch(
    `http://127.0.0.1:${httpPort}/api/live-palette?uuid=${UUID}&model=${encodeURIComponent('ysm:reimu')}`,
    { signal: abort.signal });
  assert.equal(response.status, 200);
  const reader = response.body.getReader();
  let text = '';
  const frameFromSse = (async () => {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) assert.fail('palette SSE closed before a frame');
      text += Buffer.from(value).toString('utf8');
      const events = text.split('\n\n');
      text = events.pop();
      for (const event of events) {
        if (!event.startsWith('event: frame\n')) continue;
        const line = event.split('\n').find((part) => part.startsWith('data: '));
        if (line) return JSON.parse(line.slice(6));
      }
    }
  })();

  serveSource = await connect(palettePort);
  serveSource.write(packet(encode(20)));
  const live = await Promise.race([
    frameFromSse,
    sleep(3000).then(() => assert.fail(`serve.mjs SSE did not deliver a frame: ${serveLog}`)),
  ]);
  assert.equal(live.uuid, UUID);
  assert.equal(live.modelId, 'ysm:reimu');
  assert.equal(live.boneCount, NAMES.length);
  assert.equal(Buffer.from(live.palette, 'base64').length,
    NAMES.length * LIVE_PALETTE_STRIDE * Float32Array.BYTES_PER_ELEMENT);
} finally {
  abort.abort();
  if (serveSource) serveSource.destroy();
  child.kill();
  await Promise.race([
    new Promise((resolve) => child.once('exit', resolve)),
    sleep(2000),
  ]);
}

console.log('live-palette-serve-selftest: OK (TCP -> memory hub -> filtered SSE)');
