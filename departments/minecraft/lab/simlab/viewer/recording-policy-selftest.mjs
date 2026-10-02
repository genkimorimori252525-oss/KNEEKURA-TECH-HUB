import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';

const source = await readFile(new URL('./gl.js', import.meta.url), 'utf8');

function load(search = '') {
  const window = {};
  const sandbox = {
    window,
    location: { search },
    URLSearchParams,
    Map,
    Set,
    Float32Array,
    Uint8Array,
    ArrayBuffer,
    DataView,
    Math,
    Object,
    console,
    setInterval: () => 0,
  };
  vm.runInNewContext(source, sandbox, { filename: 'gl.js' });
  return window.SimGL;
}

function policy(gl) {
  const stats = gl.derivedStats();
  return { enabled: stats.recordedPoseEnabled, live: stats.liveTrace };
}

{
  const gl = load('');
  assert.deepEqual(policy(gl), { enabled: true, live: false },
    '通常の記録表示は既定で録画 pose を使う');

  // key=null なら GL 資産を作る前に setTrace の早期 return へ入る。ライブ判定は
  // その早期 return より先に更新されなければならない。
  gl.setTrace({ key: null, tracePath: 'scenario/run/arena-0.jsonl' });
  assert.deepEqual(policy(gl), { enabled: false, live: true },
    '水槽ライブは URL 指定なしで録画 pose を停止する');

  gl.setTrace({ key: null, tracePath: null });
  assert.deepEqual(policy(gl), { enabled: true, live: false },
    '記録表示へ戻ると既定の録画 pose 利用も戻る');
}

{
  const gl = load('?rec=0');
  assert.deepEqual(policy(gl), { enabled: false, live: false },
    '通常の記録比較では既存の ?rec=0 を維持する');
}

console.log('recording-policy-selftest: OK (4 checks)');
