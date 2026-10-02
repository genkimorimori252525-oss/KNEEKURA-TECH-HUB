#!/usr/bin/env node
// =============================================================================
// trim-selftest.mjs — 履歴の切り捨て(SimStore.trimBefore)の自己検査。依存ゼロ。
// =============================================================================
//
// にーくら 2026-08-23:
//   「正直前にもどれるのは2分だけでいいよ。本当にさかのぼりたくなったら
//    録画ボタンを押しておくし、それに、切り捨てられるとはいっても、
//    デバッグログは残るだろう？」
//
// **不変条件（この検査の全て）**
//   1. trimBefore(w) の後、t >= w の問い合わせは**1ビットも変わらない**。
//      frameAt / stateAt / entityInterpAt / eventsAtTick / eventsInRange /
//      latestEvent のいずれも。
//   2. t < w は「知らない」(null / 空)を返す。
//      前方フィルするストアが、もう持っていない区間に自信満々で答えるのは、
//      黙って嘘をつくのと同じ。
//
// **なぜ許容誤差を使わないか**: 切っても同じ Float32 セルを同じ順序で読むので、
// 答えは厳密に一致するはず。ここで許容誤差を置くと、この設計が防ごうとしている
// バグ（境界で 1 点ずれる）をちょうど隠してしまう。=== で比べる。
//
//   node simlab/trim-selftest.mjs

import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const STORE_JS = path.join(HERE, 'viewer', 'store.js');
const FIXTURE = path.join(HERE, 'fixtures', 'combat-60t.jsonl');

function loadSimStore() {
  const sandbox = {};
  vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(STORE_JS, 'utf8'), sandbox, { filename: STORE_JS });
  if (!sandbox.SimStore) throw new Error('viewer/store.js が globalThis.SimStore を作らなかった');
  return sandbox.SimStore;
}
const SimStore = loadSimStore();

/** 実記録も 1 本混ぜる。合成だけだと「実際に起きる形」を外す。 */
function findRealTrace() {
  const root = path.join(path.dirname(HERE), 'run', 'sim', 'traces');
  const out = [];
  const walk = (d) => {
    let ents; try { ents = fs.readdirSync(d, { withFileTypes: true }); } catch { return; }
    for (const e of ents) {
      const p = path.join(d, e.name);
      if (e.isDirectory()) walk(p);
      else if (e.name.endsWith('.jsonl') && fs.statSync(p).size > 200000) out.push(p);
    }
  };
  walk(root);
  out.sort((a, b) => fs.statSync(b).size - fs.statSync(a).size);
  return out[0] || null;
}

let fail = 0, checks = 0;
const bad = (msg) => { fail++; if (fail <= 12) console.log('  × ' + msg); };

/** 深い比較。数値は === で。NaN は NaN と一致とみなす(Float32 の欠測表現)。 */
function same(a, b, where) {
  if (a === b) return true;
  if (typeof a === 'number' && typeof b === 'number') {
    if (Number.isNaN(a) && Number.isNaN(b)) return true;
    bad(where + ': ' + a + ' != ' + b); return false;
  }
  if (a === null || b === null || a === undefined || b === undefined) {
    bad(where + ': ' + JSON.stringify(a) + ' != ' + JSON.stringify(b)); return false;
  }
  if (a instanceof Map || b instanceof Map) {
    if (!(a instanceof Map) || !(b instanceof Map)) { bad(where + ': Map かどうかが違う'); return false; }
    if (a.size !== b.size) { bad(where + ': Map の大きさ ' + a.size + ' != ' + b.size); return false; }
    for (const [k, v] of a) { if (!b.has(k)) { bad(where + ': key ' + k + ' が無い'); return false; } if (!same(v, b.get(k), where + '[' + k + ']')) return false; }
    return true;
  }
  if (Array.isArray(a) || Array.isArray(b)) {
    if (!Array.isArray(a) || !Array.isArray(b)) { bad(where + ': 配列かどうかが違う'); return false; }
    if (a.length !== b.length) { bad(where + ': 配列の長さ ' + a.length + ' != ' + b.length); return false; }
    for (let i = 0; i < a.length; i++) if (!same(a[i], b[i], where + '[' + i + ']')) return false;
    return true;
  }
  if (typeof a === 'object' && typeof b === 'object') {
    const ks = new Set(Object.keys(a).concat(Object.keys(b)));
    for (const k of ks) if (!same(a[k], b[k], where + '.' + k)) return false;
    return true;
  }
  bad(where + ': ' + String(a) + ' != ' + String(b));
  return false;
}

const CHANNELS = ['ai', 'dmg', 'sound', 'proj', 'log'];

function runCase(label, lines) {
  const build = () => { const s = SimStore.create(); s.append(lines.slice()); return s; };
  const ref = build();
  const maxTick = ref.maxTick;
  if (maxTick < 8) { console.log('  (' + label + ': tick が短すぎるので飛ばす)'); return; }
  const WS = [1, Math.floor(maxTick / 4), Math.floor(maxTick / 2), maxTick - 1].filter((w, i, a) => w > 0 && a.indexOf(w) === i);

  for (const w of WS) {
    // --- (a) 一度に切る / (b) 3 回に分けて切る(冪等性と重ね掛け) ---
    const one = build();
    one.trimBefore(w);
    const many = build();
    many.trimBefore(Math.max(1, Math.floor(w / 3)));
    many.trimBefore(Math.max(1, Math.floor((w * 2) / 3)));
    many.trimBefore(w);
    many.trimBefore(w);            // 同じ w の再呼び出しは何もしないこと
    many.trimBefore(w - 1);        // 小さい w も無視されること

    for (const [tag, cut] of [['一度に', one], ['3回に分けて', many]]) {
      if (cut.minTick !== w) bad(label + ' w=' + w + ' ' + tag + ': minTick が ' + cut.minTick);
      // --- 不変条件 1: 窓の中は 1 ビットも変わらない ---
      const step = Math.max(1, Math.floor((maxTick - w) / 40));
      for (let t = w; t <= maxTick; t += step) {
        for (const p of [0, 0.5, 0.99]) {
          checks++;
          same(cut.frameAt(t, p), ref.frameAt(t, p), label + ' w=' + w + ' ' + tag + ' frameAt(' + t + ',' + p + ')');
        }
        for (const ch of CHANNELS) {
          checks++;
          same(cut.latestEvent(ch, t), ref.latestEvent(ch, t), label + ' w=' + w + ' ' + tag + ' latestEvent(' + ch + ',' + t + ')');
        }
      }
      for (const ch of CHANNELS) {
        checks++;
        same(cut.eventsInRange(ch, w, maxTick), ref.eventsInRange(ch, w, maxTick),
          label + ' w=' + w + ' ' + tag + ' eventsInRange(' + ch + ')');
      }
      // --- 不変条件 2: 窓の外は「知らない」 ---
      if (w >= 2) {
        const t = w - 1;
        checks++;
        const f = cut.frameAt(t, 0);
        if (f.pos.size !== 0) bad(label + ' w=' + w + ' ' + tag + ': t=' + t + ' で pos が ' + f.pos.size + ' 件返った（窓の外は空のはず）');
        if (f.phys !== null) bad(label + ' w=' + w + ' ' + tag + ': t=' + t + ' で phys が返った');
        if (f.anim !== null) bad(label + ' w=' + w + ' ' + tag + ': t=' + t + ' で anim が返った');
      }
      // --- 切った後も普通に追記できること(単調性の罠) ---
      checks++;
      const dropBefore = cut.droppedRows;
      const id = [...ref.entities.keys()][0];
      cut.append([JSON.stringify({ t: maxTick + 1, ch: 'pos', id: id, x: 1, y: 64, z: 1 })]);
      if (cut.droppedRows !== dropBefore) bad(label + ' w=' + w + ' ' + tag + ': 切った後の追記が弾かれた（' + cut.stats.lastDropReason + '）');
    }
  }

  // --- 静止した entity が窓の中で消えないこと（デルタ記録の核心） ---
  {
    const s = SimStore.create();
    s.append([
      JSON.stringify({ t: 0, ch: 'meta', scenario: 'x', arena: 0 }),
      JSON.stringify({ t: 0, ch: 'spawn', id: 7, type: 'minecraft:husk', role: 'target', w: 0.6, h: 1.9 }),
      JSON.stringify({ t: 0, ch: 'pos', id: 7, x: 3, y: 64, z: 5 }),   // これ 1 点きり
      JSON.stringify({ t: 500, ch: 'spawn', id: 8, type: 'x', role: 'target', w: 1, h: 1 }),
      JSON.stringify({ t: 500, ch: 'pos', id: 8, x: 0, y: 64, z: 0 }),
    ]);
    s.trimBefore(400);
    checks++;
    const row = s.stateAt('pos', 7, 450);
    if (!row) bad('静止した entity が窓の中で消えた（変化点が窓より前に 1 点しか無い場合）');
    else if (row.x !== 3 || row.z !== 5) bad('静止した entity の座標が変わった: ' + row.x + ',' + row.z);
  }

  // --- 死んだ entity は消え、生きている entity は残ること ---
  {
    const s = SimStore.create();
    s.append([
      JSON.stringify({ t: 0, ch: 'meta', scenario: 'x', arena: 0 }),
      JSON.stringify({ t: 10, ch: 'spawn', id: 1, type: 'a', role: 'target', w: 1, h: 1 }),
      JSON.stringify({ t: 10, ch: 'pos', id: 1, x: 1, y: 64, z: 1 }),
      JSON.stringify({ t: 20, ch: 'gone', id: 1 }),                       // 窓より前に死ぬ
      JSON.stringify({ t: 10, ch: 'spawn', id: 2, type: 'b', role: 'target', w: 1, h: 1 }),
      JSON.stringify({ t: 10, ch: 'pos', id: 2, x: 2, y: 64, z: 2 }),     // 窓より前に湧いて生き続ける
      JSON.stringify({ t: 30, ch: 'spawn', id: 3, type: 'c', role: 'reimu', w: 1, h: 1 }),
      JSON.stringify({ t: 30, ch: 'pos', id: 3, x: 3, y: 64, z: 3 }),
      JSON.stringify({ t: 40, ch: 'phys', id: 3, y: 64, onG: true }),
      JSON.stringify({ t: 50, ch: 'gone', id: 3 }),                       // 霊夢も死ぬ
      JSON.stringify({ t: 200, ch: 'spawn', id: 9, type: 'z', role: 'target', w: 1, h: 1 }),
      JSON.stringify({ t: 200, ch: 'pos', id: 9, x: 9, y: 64, z: 9 }),
    ]);
    const r = s.trimBefore(100);
    checks += 4;
    if (s.entities.has(1)) bad('窓より前に死んだ entity が残っている');
    if (!r.forgot.includes(1)) bad('忘れた id が forgot に出ていない');
    if (!s.entities.has(2)) bad('窓より前に湧いて生きている entity が消えた');
    // 霊夢は死んでいても残す —— isAlive は未知 id を「通す」ので、消すと phys が復活する
    if (!s.entities.has(3)) bad('霊夢の記録が消えた（消すと死後の phys/anim が復活する）');
    checks++;
    if (s.frameAt(150, 0).phys !== null) bad('死んだ霊夢の phys が窓の中で復活した');
  }
}

console.log('履歴の切り捨て 自己検査 —— 「窓の中は 1 ビットも変わらない」\n');

const fixture = fs.readFileSync(FIXTURE, 'utf8').split('\n');
console.log('  fixtures/combat-60t.jsonl');
runCase('fixture', fixture);

const real = findRealTrace();
if (real) {
  console.log('  ' + path.relative(path.dirname(HERE), real).replace(/\\/g, '/'));
  runCase('実記録', fs.readFileSync(real, 'utf8').split('\n'));
} else {
  console.log('  （実記録が見つからないので合成のみ。run/sim/traces に 200KB 超の jsonl が無い）');
}

console.log('\n比較したケース: ' + checks);
if (checks < 500) { console.log('× ケース数が少なすぎる（検査が空回りしている）'); fail++; }
console.log('failures: ' + fail);
console.log('trim-selftest: ' + (fail ? 'FAILED' : 'OK'));
process.exit(fail ? 1 : 0);
