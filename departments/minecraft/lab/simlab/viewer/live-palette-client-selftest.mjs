import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';

const source = await readFile(new URL('./live-palette-client.js', import.meta.url), 'utf8');
const window = {};
vm.runInNewContext(source, {
  window, TextEncoder, BigInt, Uint8Array, Float32Array, DataView, Map, Date, Number, Array,
  atob,
}, { filename: 'live-palette-client.js' });
const Live = window.SimLivePalette;

const uuid = '01234567-89ab-cdef-0123-456789abcdef';
const names = ['root', 'body'];
const modelId = 'ysm:reimu';
const modelTexture = 'reimu/texture.png';
const geometryType = 'ysm.Model#root.renderer';
const raw = Buffer.alloc(names.length * Live.STRIDE * 4);
for (let i = 0; i < names.length * Live.STRIDE; i++) raw.writeFloatBE(i + 0.25, i * 4);
const payload = {
  sequence: '42', gameTime: '1234', partialTick: 0.5, receivedAt: Date.now(),
  uuid, modelId, modelTexture, geometryType, boneCount: names.length, boneNames: names,
  stride: Live.STRIDE, paletteEndian: 'be-f32', palette: raw.toString('base64'),
  layoutHash: Live.layoutHash(modelId, modelTexture, geometryType, names),
};
const decoded = Live.decode(payload, uuid, modelId);
assert.equal(decoded.state9.length, names.length * Live.COMPS);
assert.deepEqual(Array.from(decoded.state9.slice(0, 9)),
  [0.25, 1.25, 2.25, 3.25, 4.25, 5.25, 6.25, 7.25, 8.25]);
assert.deepEqual(Array.from(decoded.state9.slice(9, 18)),
  [12.25, 13.25, 14.25, 15.25, 16.25, 17.25, 18.25, 19.25, 20.25]);
assert.equal(decoded.slotOf.get('body'), 1);
assert.throws(() => Live.decode({ ...payload, uuid: '11111111-1111-1111-1111-111111111111' }, uuid),
  /UUID mismatch/);
assert.throws(() => Live.decode(payload, uuid, 'ysm:other'), /model ID mismatch/);
assert.throws(() => Live.decode({ ...payload, layoutHash: '0000000000000000' }, uuid),
  /identity mismatch/);
assert.throws(() => Live.decode({ ...payload, palette: raw.subarray(0, -4).toString('base64') }, uuid),
  /byte length/);

// 選択規則そのものも固定する。live branch がこの順序から外れたら、decoder が緑でも落とす。
const gl = await readFile(new URL('./gl.js', import.meta.url), 'utf8');
assert.match(gl, /model=' \+ encodeURIComponent\(modelId\)/,
  'live SSE subscription must include the YSM pack model id');
const poseStart = gl.indexOf('function poseYsm(D, T, p)');
const recordedPalette = gl.indexOf('// --- palette (14-01)', poseStart);
const liveBranch = gl.slice(poseStart, recordedPalette);
assert.ok(liveBranch.includes('if (traceIsLive)'));
assert.ok(liveBranch.includes('poseYsmLivePalette()'));
assert.ok(liveBranch.includes("ysmLastPoseSource = 'livePalette'"));
assert.ok(liveBranch.includes("ysmLastPoseSource = 'missing'"));
assert.ok(liveBranch.includes('return false;'));
assert.match(gl, /if \(recordingEnabled\(\) && !paletteCanServe\(T\)/);
assert.match(gl, /if \(!traceIsLive\) loadPalette\(tracePath\)/);
const genericLoop = gl.indexOf('const missed = []');
const genericModel = gl.indexOf('const m = model(e.type)', genericLoop);
const liveFailClosed = gl.indexOf("if (traceIsLive && e.role === 'reimu')", genericLoop);
assert.ok(genericLoop >= 0 && liveFailClosed > genericLoop && liveFailClosed < genericModel,
  'live Reimu must be rejected before the generic/static model fallback');
assert.match(gl, /YSMクライアント未接続（代替姿勢は使わない）/);

console.log('live-palette-client-selftest: OK (decode + live-only pose policy)');
