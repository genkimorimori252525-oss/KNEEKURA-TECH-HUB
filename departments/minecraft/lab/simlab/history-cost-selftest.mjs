#!/usr/bin/env node
// =============================================================================
// history-cost-selftest.mjs — 「録画が伸びると重くなる」を数字で縛る。依存ゼロ。
// =============================================================================
//
// にーくら 2026-08-23:
//   「録画が進むと160あったfpsが20くらいまで下がってしまう」
//
// 真因は **「生きているもの」と「これまでに存在したもの」の取り違え**だった。
// `growWalk` は死んだモブを毎 ingest 触り続け、しかも 1 体 1 tick の速度を読むために
// `frameAt`(= これまでの全レーンを回す)を呼んでいた。費用は
//   (これまでのモブ数) × (新しい tick 数) × (これまでのレーン数)
// の積で、3 つとも録画とともに伸びる。実測: 弾 8,000・モブ 150 で 1 ingest 49.5ms
// —— 20 回/秒 走るので、これだけで CPU を 1 コア食い切る。
//
// **この手の欠陥は「動くか」の検査では捕まらない。** 動くし、答えも正しい。
// 伸び方だけが間違っている。だから伸び方を検査にする —— 履歴を 10 倍にしても
// 1 ingest の費用が 10 倍にならないこと。
//
// **暇な機械で回すこと。** ミリ秒未満を比べるので、ブラウザや水槽を走らせたまま回すと
// 取り合いで落ちることがある(2026-08-23 実測: Chrome + 偽の水槽と同時に回して 1 回落ちた。
// 同じ機械が暇になってから 3 回連続で通った)。
//
//   node simlab/history-cost-selftest.mjs

import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const STORE_JS = path.join(HERE, 'viewer', 'store.js');

function loadSimStore() {
  const sandbox = {};
  vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(STORE_JS, 'utf8'), sandbox, { filename: STORE_JS });
  if (!sandbox.SimStore) throw new Error('viewer/store.js が globalThis.SimStore を作らなかった');
  return sandbox.SimStore;
}
const SimStore = loadSimStore();

/**
 * 「戦闘が続いた水槽」を合成する。弾は湧いてすぐ死に(レーンだけ残る)、
 * モブも大半は既に死んでいる —— 実記録の形(弾 4.9 発/秒、死亡率 96%)に合わせる。
 */
function build(deadProj, mobsEver, aliveMobs, ticks) {
  const s = SimStore.create();
  const lines = [];
  let id = 1;
  lines.push(JSON.stringify({ t: 0, ch: 'meta', scenario: 'bench', arena: 0 }));
  for (let i = 0; i < deadProj; i++) {
    const t = 1 + (i % 50);
    lines.push(JSON.stringify({ t, ch: 'spawn', id, type: 'tlm:danmaku', role: 'projectile', w: 0.2, h: 0.2 }));
    lines.push(JSON.stringify({ t, ch: 'pos', id, x: i % 7, y: 64, z: i % 5, vx: 0.1, vz: 0.1 }));
    lines.push(JSON.stringify({ t: t + 1, ch: 'gone', id }));
    id++;
  }
  for (let i = 0; i < mobsEver; i++) {      // もう死んでいるモブ
    lines.push(JSON.stringify({ t: 55, ch: 'spawn', id, type: 'minecraft:husk', role: 'target', w: 0.6, h: 1.9 }));
    lines.push(JSON.stringify({ t: 56, ch: 'pos', id, x: i % 9, y: 64, z: i % 9, vx: 0.2, vz: 0.1, hp: 20 }));
    lines.push(JSON.stringify({ t: 57, ch: 'gone', id }));
    id++;
  }
  const alive = [];
  for (let i = 0; i < aliveMobs; i++) {     // 生きているモブ
    alive.push(id);
    lines.push(JSON.stringify({ t: 58, ch: 'spawn', id, type: 'minecraft:husk', role: 'target', w: 0.6, h: 1.9 }));
    id++;
  }
  s.append(lines);
  for (let t = 59; t < 59 + ticks; t++) {
    const b = [];
    for (const a of alive) b.push(JSON.stringify({ t, ch: 'pos', id: a, x: t * 0.1 + a, y: 64, z: a * 0.1, yaw: t % 360, vx: 0.2, vz: 0.1, hp: 20 }));
    s.append(b);
  }
  return { store: s, last: 58 + ticks };
}

/** gl.js の growWalk と**同じ形**で 1 ingest ぶんを回す(直した版)。 */
function growWalkNew(store, entities, from, to) {
  for (const e of entities.values()) {
    if (e.role === 'projectile') continue;
    if (e.goneAt !== undefined && e.goneAt < from) continue;   // 死んだものは凍らせる
    for (let t = from; t <= to; t++) store.stateAt('pos', e.id, t);
  }
}
/** 旧実装(比較用。これが 160fps → 20fps の主犯だった)。 */
function growWalkOld(store, entities, from, to) {
  let cache = null;
  const frameAt = (t) => { if (cache && cache.t === t) return cache.f; const f = store.frameAt(t, 0); cache = { t, f }; return f; };
  for (const e of entities.values()) {
    if (e.role === 'projectile') continue;
    for (let t = from; t <= to; t++) frameAt(t).pos.get(e.id);
  }
}

const ms = (fn) => { const a = process.hrtime.bigint(); fn(); return Number(process.hrtime.bigint() - a) / 1e6; };
/**
 * **20 回ぶんまとめて測って 1 回あたりに割る。** 直した後の 1 ingest は 0.03ms 前後で、
 * これは process.hrtime の分解能とスケジューラの揺れと同じ桁 —— そのまま比を取ると
 * 実測で 3.0〜8.1 倍の間で暴れた(倍率が変わったのではなく、分母が測れていなかった)。
 * 束ねれば両端がノイズ床から離れ、比が意味を持つ。さらに 5 回の中央値を採る。
 */
const REPEAT = 20;
const msMed = (fn) => { const r = []; for (let i = 0; i < 5; i++) r.push(ms(() => { for (let k = 0; k < REPEAT; k++) fn(); }) / REPEAT); r.sort((a, b) => a - b); return r[2]; };
const F = (v, n = 2) => v.toFixed(n);

// --- 検査本体 ---------------------------------------------------------------
console.log('履歴の伸びに対する費用 —— 「動くか」ではなく「伸び方」を縛る\n');

let fail = 0;
const CASES = [
  { name: '軽い戦闘 (弾 500 / モブ 20)', proj: 500, mobs: 20 },
  { name: '中くらい (弾 2,000 / モブ 60)', proj: 2000, mobs: 60 },
  { name: '長い戦闘 (弾 8,000 / モブ 150)', proj: 8000, mobs: 150 },
  { name: '1 時間ぶん (弾 20,000 / モブ 300)', proj: 20000, mobs: 300 },
];

console.log('                                    1 ingest (1 tick 追記) の費用');
console.log('場合                                  旧          新       倍率');
const results = [];
for (const c of CASES) {
  const { store, last } = build(c.proj, c.mobs, 6, 120);
  const ents = store.entities;
  const oldMs = ms(() => growWalkOld(store, ents, last - 1, last));
  const newMs = msMed(() => growWalkNew(store, ents, last - 1, last));
  results.push({ ...c, oldMs, newMs });
  console.log('  ' + c.name.padEnd(34) + (F(oldMs) + 'ms').padStart(9) + (F(newMs) + 'ms').padStart(11)
    + ('×' + F(oldMs / Math.max(newMs, 0.001), 0)).padStart(9));
}

// 合格条件 1: **どの規模でも 1 ingest は 1ms 未満。** 20 回/秒 走るので、
// 1ms なら CPU の 2%。旧実装は最大の場合で 229ms(= 459%)だった。
for (const r of results) {
  if (r.newMs >= 1.0) { console.log('  × ' + r.name + ': 1 ingest が ' + F(r.newMs) + 'ms (1ms 未満を期待)'); fail++; }
}

/* 合格条件 2: **「1 体あたりの費用」が、レーンが増えても悪化しないこと。**
 *
 * 直した後も線形項は残る —— growWalk は `entities`(= これまでの全 entity)を舐めて
 * 「死んでいるか」を見るので、そこだけ O(これまでの体数) が残る(実測: 20,300 体で
 * 0.30ms/ingest = 20回/秒 なら CPU の 0.6%)。だから**総費用の比**を縛るのは筋が悪い
 * —— 体数が 38 倍なら費用も概ね 38 倍になるのが正しい姿で、実測 12〜22 倍。
 *
 * 直したのは「1 体あたりの費用に**レーン数が掛かっていた**」ことのほう。だから
 * 縛るべきは体数で割った値。旧実装ではここがレーン数に比例して悪化する。
 * 体数そのものの上限は、直近2分の窓が別に与える。 */
const small = results[0], big = results[results.length - 1];
const per = (r, k) => r[k] / (r.proj + r.mobs + 6);   // 1 体(= entities の 1 件)あたり
const perGrow = per(big, 'newMs') / Math.max(per(small, 'newMs'), 1e-9);
const perOldGrow = per(big, 'oldMs') / Math.max(per(small, 'oldMs'), 1e-9);
console.log('');
console.log('  総費用の比 (履歴 40 倍): ' + F(big.newMs / Math.max(small.newMs, 0.001), 1) + ' 倍'
  + '   ← 体数が 38 倍なのでこれは正しい伸び方');
console.log('  **1 体あたりの費用の比: ' + F(perGrow, 2) + ' 倍**'
  + '   ← レーン数が掛かっていないことの証拠');
console.log('  （旧実装の同じ比: ' + F(perOldGrow, 1) + ' 倍 —— レーン数がそのまま乗っていた）');
if (perGrow > 2) { console.log('  × 1 体あたりの費用がレーン数とともに悪化している'); fail++; }
if (perOldGrow < 3) { console.log('  × 旧実装の再現が壊れている（対照になっていない）'); fail++; }

// --- frameAt 単体 -----------------------------------------------------------
// 窓(直近2分)を入れた後に何本のレーンが残るかで、frameAt が生存索引を要るかが決まる。
// 実記録の弾の湧く速さは最速 4.9 発/秒なので、2 分なら約 590 本。
console.log('\nframeAt 1 回の費用 —— 窓の長さを決める材料');
console.log('  死んだレーン        1 回     60fps 中');
for (const [dead, label] of [[590, '(2 分窓)'], [2900, '(10 分)'], [17600, '(60 分)']]) {
  const { store, last } = build(dead, 6, 6, 120);
  const t = ms(() => { for (let i = 0; i < 200; i++) store.frameAt(last - (i % 50), 0.5); }) / 200;
  console.log('  ' + (String(dead) + ' ' + label).padEnd(20) + (F(t, 3) + 'ms').padStart(9) + (F(t * 60, 1) + '%').padStart(11));
  if (dead === 590 && t * 60 > 10) { console.log('  × 2 分窓でも frameAt が 60fps の 10% を超える —— 生存索引が要る'); fail++; }
}

// --- 毎 ingest に走る「歴史全部を触る」ゲッタ -------------------------------
console.log('\n毎 ingest に走るゲッタ (弾 20,000 / モブ 300)');
{
  const { store } = build(20000, 300, 6, 120);
  const N = 20;
  void store.entities;   // **暖める。** 直後の 1 回は作り直しになるので平均に混ぜない
  const ent = ms(() => { for (let i = 0; i < N; i++) { const m = store.entities; void m.size; } }) / N;
  store.append([JSON.stringify({ t: 9998, ch: 'spawn', id: 999998, type: 'x', role: 'target', w: 1, h: 1 })]);
  const cold = ms(() => { const m = store.entities; void m.size; });   // 本当に作り直す 1 回
  const drop = ms(() => { for (let i = 0; i < N; i++) void store.droppedRows; }) / N;
  console.log('  entities (集合が変わらない間)  ' + (F(ent, 3) + 'ms').padStart(9));
  console.log('  entities (集合が変わった直後)  ' + (F(cold, 3) + 'ms').padStart(9)
    + '   ← 戦闘中は毎 tick 弾が湧くのでこちらが普通。窓で本数を抑えるのが本命');
  console.log('  droppedRows                    ' + (F(drop, 3) + 'ms').padStart(9));
  // 集合が変わらない限り作り直さないので、ほぼ 0 でなければ版番号が効いていない。
  if (ent > 0.01) { console.log('  × entities のコピーが毎回作り直されている (版番号が効いていない)'); fail++; }
  if (drop > 0.05) { console.log('  × droppedRows が全レーンを触っている'); fail++; }
  // 版番号が「変わったら作り直す」ほうも壊れていないこと ——
  // ここが壊れると、新しく湧いたモブが Viewer から見えなくなる(安全側に倒れない)。
  const before = store.entities;
  store.append([JSON.stringify({ t: 9999, ch: 'spawn', id: 999999, type: 'x', role: 'target', w: 1, h: 1 })]);
  const after = store.entities;
  if (after === before) { console.log('  × spawn しても entities のコピーが更新されない'); fail++; }
  else if (!after.has(999999)) { console.log('  × 新しい entity がコピーに現れない'); fail++; }
  else console.log('  版番号: spawn したら作り直される ✓');
}

console.log('\nfailures: ' + fail);
console.log('history-cost-selftest: ' + (fail ? 'FAILED' : 'OK'));
process.exit(fail ? 1 : 0);
