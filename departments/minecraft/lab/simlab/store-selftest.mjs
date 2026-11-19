#!/usr/bin/env node
// =============================================================================
// store-selftest.mjs — viewer/store.js (SimStore) の自己検査。依存ゼロ。ブラウザ不要。
// =============================================================================
//
// 使い方: node simlab/store-selftest.mjs
//
// 何を測るか(13-01 Task 1 <behavior>):
//   - 密トレース(simlab/fixtures/combat-60t.jsonl)を「元の密な読み方」で自前に
//     forward-fill してground truthを作り、SimStore.stateAt が全tick・全entityで
//     同じ値を返すか(往復一致)。
//   - 冗長行(前tickと全フィールド一致のpos行)を落とした版でも同じ答えになるか
//     (後方互換の核心 —— 13-04でjar側がdelta化しても既存トレースは読めるままという主張の検査)。
//   - 二分探索の境界(最初の変化点そのもの/直前=null/最後の変化点より後=forward-fill)。
//   - 補間(partial 0/1が両端一致、0.5が中間、yawの最短弧、テレポートのスナップ、
//     末尾で外挿しないこと)。
//   - 追記の等価性(1回でappendした結果と10分割でappendした結果が一致)。
//   - ケース数が0で「合格」しないこと(pick-selftest.mjsと同じ下限ガード)。
//
// ---- 数値許容誤差について ----
// store.js はFloat32Array(単精度)に値を詰める。fixtureの座標はJava側で既にr3/r2に
// 丸められている(小数点以下2-3桁)ため、単精度往復の誤差(この座標範囲では絶対誤差
// 1e-5未満)はその丸め粒度より2桁以上小さい。厳密一致(===)ではなく許容誤差
// NUM_TOL で比較する—実測の最悪値を実行時に出力し、コメントで根拠を残す(pick-selftest.mjs
// と同じ作法)。実測: 最悪 4.578e-5(このfixtureで)。10倍の余裕を見て 1e-3 に設定。

import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

// WR-03(code review): new URL(import.meta.url).pathname はURLエンコードされたままなので
// スペースを含むパスで%20が残りENOENTになる。bench.mjs:42と同じfileURLToPathに揃える。
const HERE = path.dirname(fileURLToPath(import.meta.url));
const STORE_JS = path.join(HERE, 'viewer', 'store.js');
const FIXTURE = path.join(HERE, 'fixtures', 'combat-60t.jsonl');

const NUM_TOL = 1e-3; // 実測 worst 4.578e-5 の約22倍の余裕(単精度往復 + r3丸めの粒度から)

function loadSimStore() {
  const src = fs.readFileSync(STORE_JS, 'utf8');
  const sandbox = {};
  vm.createContext(sandbox);
  vm.runInContext(src, sandbox, { filename: STORE_JS });
  if (!sandbox.SimStore) throw new Error('viewer/store.js が globalThis.SimStore を作らなかった');
  return sandbox.SimStore;
}

const SimStore = loadSimStore();

let failures = 0;
let cases = 0;
let worstNum = 0;
const fail = (msg) => { failures++; console.error('FAIL: ' + msg); };

// ===========================================================================
// ground truth: fixture を「元の密な読み方」で forward-fill する自前の最小パーサ。
// index.html の parse() には依存しない(store.js と同じくブラウザ非依存であるべき
// テストなので、node:vm 経由でも動く独立実装にする)。
// ===========================================================================
const rawText = fs.readFileSync(FIXTURE, 'utf8');
const rawLines = rawText.split('\n').filter((l) => l.trim().length > 0);

// CR-02(code review): 元のground truthは`gone`チャンネルを一切見ておらず、SimStoreと
// 同じ「死後も forward-fill し続ける」前提で書かれていた(CR-01の不具合をsparse-vs-sparse
// の比較にすり替えてしまい、158,492件全green でも検出できなかった)。`gone`を追跡し、
// 見た後は null を返すよう直す —— これで CR-01 未修正の store.js に対しては即座に
// FAIL するはず(このコメントの下、fix適用前に実際にRED確認してからCR-01を直すこと)。
//
// 「最後にpos更新された tick」ではなく「明示的な gone を見たか」を境界にする
// (store.js の isAlive と同じ設計 —— 理由は2つ):
//   (1) この fixture 自体が t<=60 で切り出されているため、生きたまま記録が
//       途切れているだけの entity(例: reimu、gone を一度も受け取らない)を
//       「最後の更新」基準で判定すると t=61 以降すべて誤って「死亡」扱いになる。
//   (2) 13-04(jar側delta化)後は生存中でも無変化なら pos 行が来なくなりうる。
//       「更新が途絶えた」を死亡の代理指標にすると、静止した生存 entity まで
//       消してしまう。死亡は gone という明示的なイベントでしか判定しないほうが安全。
function denseGroundTruth(lines) {
  const byId = new Map();   // id -> Map(tick -> row)
  const goneAt = new Map(); // id -> gone を確認した tick(一度も無ければ未設定 = 生存扱い)
  let maxTick = 0;
  for (const line of lines) {
    let e; try { e = JSON.parse(line); } catch { continue; }
    const t = e.t | 0; if (t > maxTick) maxTick = t;
    if (e.ch === 'gone') { goneAt.set(e.id, t); continue; }
    if (e.ch !== 'pos') continue;
    if (!byId.has(e.id)) byId.set(e.id, new Map());
    byId.get(e.id).set(t, e);
  }
  return { byId, maxTick, goneAt };
}
function denseStateAt(byId, goneAt, id, t) {
  const g = goneAt.get(id);
  if (g !== undefined && t > g) return null; // gone より後は null(CR-01の核心)
  const rows = byId.get(id);
  if (!rows) return null;
  let best = null, bestT = -1;
  for (const [rt, row] of rows) { if (rt <= t && rt > bestT) { bestT = rt; best = row; } }
  return best;
}

const GT = denseGroundTruth(rawLines);
if (GT.byId.size < 5) fail(`fixture の pos entity 数が少なすぎる(${GT.byId.size}) — combat-60t.jsonl の中身を確認せよ`);
if (GT.goneAt.size < 1) fail(`fixture に gone イベントが1件も無い —— CR-01の検査(死亡後forward-fillしないこと)が成立しない`);

// ===========================================================================
// 数値フィールド比較。field の有無(undefined vs number)も検査する
// (欠測フィールドはNaN sentinel経由でundefinedへ戻す —— rowFromValuesの契約)。
// ===========================================================================
const NUM_FIELDS = ['x', 'y', 'z', 'yaw', 'pitch', 'vx', 'vy', 'vz', 'hp', 'hy'];
function rowsClose(dense, sparse) {
  if (!dense && !sparse) return null;
  if (!dense || !sparse) return `null 性が不一致 dense=${JSON.stringify(dense)} sparse=${JSON.stringify(sparse)}`;
  for (const f of NUM_FIELDS) {
    const dv = dense[f], sv = sparse[f];
    const dHas = typeof dv === 'number', sHas = typeof sv === 'number';
    if (dHas !== sHas) return `field ${f} 有無不一致 dense=${dv} sparse=${sv}`;
    if (dHas) {
      const diff = Math.abs(dv - sv);
      if (diff > worstNum) worstNum = diff;
      if (diff > NUM_TOL) return `field ${f} 値不一致 dense=${dv} sparse=${sv} diff=${diff}`;
    }
  }
  const dAgg = !!dense.agg, sAgg = !!sparse.agg;
  if (dAgg !== sAgg) return `field agg 有無不一致 dense=${dense.agg} sparse=${sparse.agg}`;
  return null;
}

// ===========================================================================
// 1. 往復一致: 密な読み方と SimStore.stateAt が全tick・全entityで同じ値
// ===========================================================================
function runRoundTrip(S, byId, goneAt, maxTick, label) {
  let n = 0;
  for (const id of byId.keys()) {
    for (let t = 0; t <= maxTick; t++) {
      const dense = denseStateAt(byId, goneAt, id, t);
      const sparse = S.stateAt('pos', id, t);
      const msg = rowsClose(dense, sparse);
      if (msg) fail(`[${label}] round-trip id=${id} t=${t}: ${msg}`);
      n++; cases++;
    }
  }
  return n;
}

const S1 = SimStore.create();
{
  const r = S1.append(rawText);
  if (r.ingested <= 0) fail('S1.append が1行も取り込まなかった');
  if (!(S1.maxTick >= 60)) fail(`S1.maxTick が60未満: ${S1.maxTick}`);
}
const n1 = runRoundTrip(S1, GT.byId, GT.goneAt, GT.maxTick, 'dense');
console.log(`round-trip(dense): ${n1} 件 (entities=${GT.byId.size} x ticks=${GT.maxTick + 1})`);

// ===========================================================================
// 2. 冗長行を落としても同じ答え(後方互換の核心)
// ===========================================================================
function filterRedundantPos(lines, S) {
  const lastByI = new Map();
  const out = [];
  let dropped = 0;
  for (const line of lines) {
    let e; try { e = JSON.parse(line); } catch { out.push(line); continue; }
    if (e.ch !== 'pos') { out.push(line); continue; }
    const prev = lastByI.get(e.id);
    if (S.rowIsRedundant(prev, e)) { dropped++; } else { out.push(line); }
    lastByI.set(e.id, e);
  }
  return { out, dropped };
}
const { out: sparseLines, dropped } = filterRedundantPos(rawLines, S1);
if (dropped <= 0) fail('冗長行フィルタが1行も落とさなかった — fixtureに冗長な pos 行が無いか、フィルタが壊れている');
console.log(`redundant pos rows dropped: ${dropped} / ${rawLines.filter((l) => { try { return JSON.parse(l).ch === 'pos'; } catch { return false; } }).length}`);

const S2 = SimStore.create();
S2.append(sparseLines.join('\n'));
if (S1.stats.changePoints !== S2.stats.changePoints) {
  fail(`冗長行あり/なしで changePoints が不一致: dense=${S1.stats.changePoints} sparse=${S2.stats.changePoints}`);
}
const n2 = runRoundTrip(S2, GT.byId, GT.goneAt, GT.maxTick, 'redundancy-dropped');
console.log(`round-trip(redundancy-dropped): ${n2} 件`);

// ===========================================================================
// 3. 二分探索の境界: 最初の変化点そのもの/直前(null)/最後の変化点より後(forward-fill)
// ===========================================================================
{
  // 最初のpos行を持つentityを1つ選ぶ
  let pickId = null, firstTick = -1;
  for (const [id, rows] of GT.byId) {
    const ticks = [...rows.keys()].sort((a, b) => a - b);
    if (ticks.length >= 3) { pickId = id; firstTick = ticks[0]; break; }
  }
  if (pickId == null) fail('境界検査用の entity が見つからない');
  else {
    if (firstTick > 0) {
      const before = S1.stateAt('pos', pickId, firstTick - 1);
      if (before !== null) fail(`最初の変化点(t=${firstTick})の直前(t=${firstTick - 1})が null でない: ${JSON.stringify(before)}`);
      cases++;
    }
    const at = S1.stateAt('pos', pickId, firstTick);
    if (!at) fail(`最初の変化点そのもの(t=${firstTick})が null: id=${pickId}`);
    cases++;

    // 最後の変化点より後 —— entityのlast以降もforward-fillが続くこと
    const ticks = [...GT.byId.get(pickId).keys()].sort((a, b) => a - b);
    const lastTick = ticks[ticks.length - 1];
    if (lastTick < GT.maxTick) {
      const afterLast = S1.stateAt('pos', pickId, GT.maxTick);
      const atLast = S1.stateAt('pos', pickId, lastTick);
      const msg = rowsClose(atLast, afterLast);
      if (msg) fail(`最後の変化点(t=${lastTick})より後(t=${GT.maxTick})で forward-fill が効いていない: ${msg}`);
      cases++;
    }

    // 変化点そのものの「直前」も検査する(2番目以降の変化点があれば)
    let prevRow = null;
    for (const t of ticks) {
      const row = GT.byId.get(pickId).get(t);
      if (prevRow && !S1.rowIsRedundant(prevRow, row)) {
        // t は本物の変化点。t-1 は直前の値のまま(forward-fill)であるべき。
        const justBefore = S1.stateAt('pos', pickId, t - 1);
        const expectPrev = denseStateAt(GT.byId, GT.goneAt, pickId, t - 1);
        const msg = rowsClose(expectPrev, justBefore);
        if (msg) fail(`変化点 t=${t} の直前(t=${t - 1})が前の値のままでない: ${msg}`);
        cases++;
        break;
      }
      prevRow = row;
    }
  }
}

// ===========================================================================
// 4. 補間: 両端一致 / 中間 / yawの最短弧 / テレポートのスナップ / 末尾で外挿しない
// ===========================================================================
{
  // 4a. 両端一致 + 中間 —— 実データから「動いている」瞬間を探す
  let found = false;
  outer:
  for (const [id, rows] of GT.byId) {
    const ticks = [...rows.keys()].sort((a, b) => a - b);
    for (let i = 0; i < ticks.length - 1; i++) {
      const t = ticks[i], tn = ticks[i + 1];
      if (tn !== t + 1) continue; // 連続tickのペアのみ
      const a0 = S1.frameAt(t, 0).pos.get(id);
      const b0 = S1.frameAt(t + 1, 0).pos.get(id);
      if (!a0 || !b0) continue;
      const moved = Math.hypot(b0.x - a0.x, b0.y - a0.y, b0.z - a0.z);
      if (moved < 0.05) continue; // ほぼ静止 —— 中間点の検査に向かない
      const p0 = S1.frameAt(t, 0).pos.get(id);
      const p1 = S1.frameAt(t, 1).pos.get(id);
      const pMid = S1.frameAt(t, 0.5).pos.get(id);
      cases++;
      const d0 = rowsClose(a0, p0); if (d0) fail(`partial=0 が t時点の値と不一致: ${d0}`);
      cases++;
      const d1x = Math.abs(p1.x - b0.x), d1y = Math.abs(p1.y - b0.y), d1z = Math.abs(p1.z - b0.z);
      if (d1x > NUM_TOL || d1y > NUM_TOL || d1z > NUM_TOL) fail(`partial=1 が t+1時点の値と不一致: p1=${JSON.stringify(p1)} b0=${JSON.stringify(b0)}`);
      cases++;
      const dMidA = Math.hypot(pMid.x - a0.x, pMid.y - a0.y, pMid.z - a0.z);
      if (!(dMidA > 1e-9 && dMidA < moved)) fail(`partial=0.5 が両端の中間にない: dMidA=${dMidA} moved=${moved} id=${id} t=${t}`);
      cases++;
      found = true;
      break outer;
    }
  }
  if (!found) fail('補間検査(実データの動いている瞬間)を1件も見つけられなかった');
}
{
  // 4b. yawの最短弧: 合成トレースで直接検査(170 -> -170 の partial=0.5 は絶対値180)
  const synth = [
    '{"t":0,"ch":"spawn","id":9001,"type":"minecraft:zombie","role":"target","w":0.6,"h":1.95}',
    '{"t":0,"ch":"pos","id":9001,"x":0,"y":64,"z":0,"yaw":170,"pitch":0}',
    '{"t":1,"ch":"pos","id":9001,"x":0,"y":64,"z":0,"yaw":-170,"pitch":0}',
  ].join('\n');
  const Sy = SimStore.create();
  Sy.append(synth);
  const mid = Sy.frameAt(0, 0.5).pos.get(9001);
  cases++;
  if (!mid || Math.abs(Math.abs(mid.yaw) - 180) > 1e-3) fail(`yaw最短弧: 170->-170 partial=0.5 は絶対値180のはずが ${mid && mid.yaw}`);
}
{
  // 4c. テレポートのスナップ: TELEPORT_M(8.0)を超える移動は partial のどこでも a のまま
  const synth = [
    '{"t":0,"ch":"spawn","id":9002,"type":"minecraft:zombie","role":"target","w":0.6,"h":1.95}',
    '{"t":0,"ch":"pos","id":9002,"x":0,"y":64,"z":0,"yaw":0,"pitch":0}',
    '{"t":1,"ch":"pos","id":9002,"x":50,"y":64,"z":0,"yaw":0,"pitch":0}',
  ].join('\n');
  const St = SimStore.create();
  St.append(synth);
  for (const partial of [0.25, 0.5, 0.75]) {
    const row = St.frameAt(0, partial).pos.get(9002);
    cases++;
    if (!row || row.x !== 0) fail(`テレポート検査 partial=${partial}: x=${row && row.x} (基準tickの0のはず)`);
  }
}
{
  // 4d. 末尾で外挿しない: S1.maxTickの partial>0 は partial=0 と厳密一致(x/z)
  const last = S1.frameAt(S1.maxTick, 0.9);
  const last0 = S1.frameAt(S1.maxTick, 0);
  let n = 0;
  for (const [id, v] of last.pos) {
    const w = last0.pos.get(id);
    cases++; n++;
    if (!w || v.x !== w.x || v.z !== w.z) fail(`末尾で外挿している: id=${id} partial0.9=${JSON.stringify(v)} partial0=${JSON.stringify(w)}`);
  }
  if (n === 0) fail('末尾外挿検査が0件のentityで終わった');
}

// ===========================================================================
// 5. 追記の等価性: 1回append と 10分割append が一致
// ===========================================================================
{
  const Sa = SimStore.create();
  Sa.append(rawText);
  const Sb = SimStore.create();
  const CHUNKS = 10;
  const per = Math.ceil(rawLines.length / CHUNKS);
  for (let i = 0; i < CHUNKS; i++) {
    const chunk = rawLines.slice(i * per, (i + 1) * per);
    if (chunk.length) Sb.append(chunk);
  }
  cases++;
  if (Sa.stats.changePoints !== Sb.stats.changePoints) {
    fail(`1回append(changePoints=${Sa.stats.changePoints}) と 10分割append(changePoints=${Sb.stats.changePoints}) が不一致`);
  }
  let checked = 0;
  for (const id of GT.byId.keys()) {
    for (let t = 0; t <= GT.maxTick; t += 5) { // 全tickだと重いので5間引き。全idは網羅する
      const va = Sa.stateAt('pos', id, t), vb = Sb.stateAt('pos', id, t);
      if ((va === null) !== (vb === null)) { fail(`分割append不一致(null性) id=${id} t=${t}`); continue; }
      if (va) {
        for (const f of NUM_FIELDS) {
          if (typeof va[f] === 'number' && va[f] !== vb[f]) {
            fail(`分割append不一致 id=${id} t=${t} field=${f} full=${va[f]} chunked=${vb[f]}`);
          }
        }
      }
      checked++; cases++;
    }
  }
  console.log(`append-equivalence: ${checked} 件のtick/id比較`);
}

// ===========================================================================
// 6. 状態レーンの拡張(13-02): phys/anim の往復一致(密な読み方 vs ストア)
//    fixtureに実データがある(phys/anim とも id=2=reimu で61行/60tick)。
//    vis はfixtureに0件なので、7番の合成トレースで別途検査する。
// ===========================================================================
function denseSingletonGroundTruth(lines, ch) {
  const byTick = new Map(); // t -> row(単一のオーナー前提。旧f.phys=e/f.anim=eと同じ)
  for (const line of lines) {
    let e; try { e = JSON.parse(line); } catch { continue; }
    if (e.ch !== ch) continue;
    byTick.set(e.t, e);
  }
  const ticks = [...byTick.keys()].sort((a, b) => a - b);
  return { byTick, ticks };
}
function denseSingletonAt(gt, goneAt, ownerId, t) {
  if (ownerId != null) {
    const g = goneAt.get(ownerId);
    if (g !== undefined && t > g) return null;
  }
  let best = null, bestT = -1;
  for (const rt of gt.ticks) { if (rt <= t && rt > bestT) { bestT = rt; best = gt.byTick.get(rt); } }
  return best;
}
/** phys/anim行の比較。t/ch/idは構造フィールドなので比較対象から外す —— 前方フィルで
 *  借用した行は問い合わせtickへ.tを上書きする実装(store.js singletonStateAt)なので、
 *  .t自体はstore側とdense側で一致するはずだが、値フィールドの一致こそが本質。 */
function singletonRowsClose(dense, sparse, fields) {
  if (!dense && !sparse) return null;
  if (!dense || !sparse) return `null性が不一致 dense=${JSON.stringify(dense)} sparse=${JSON.stringify(sparse)}`;
  for (const f of fields) {
    const dv = dense[f], sv = sparse[f];
    if (typeof dv === 'number' || typeof sv === 'number') {
      const dHas = typeof dv === 'number', sHas = typeof sv === 'number';
      if (dHas !== sHas) return `field ${f} 有無不一致 dense=${dv} sparse=${sv}`;
      if (dHas) {
        const diff = Math.abs(dv - sv);
        if (diff > worstNum) worstNum = diff;
        if (diff > NUM_TOL) return `field ${f} 数値不一致 dense=${dv} sparse=${sv} diff=${diff}`;
      }
    } else if (dv !== sv) {
      return `field ${f} 不一致 dense=${JSON.stringify(dv)} sparse=${JSON.stringify(sv)}`;
    }
  }
  return null;
}
{
  const PHYS_FIELDS = ['air', 'embed', 'noGrav', 'onG', 'vel', 'y'];
  const ANIM_FIELDS = ['anim', 'pend', 'molang', 'main', 'off', 'face'];
  const reimuId = S1.reimuId;
  if (reimuId == null) fail('fixture に reimu(role=reimu の spawn) が見つからない —— phys/anim往復検査の前提が崩れている');
  const physGT = denseSingletonGroundTruth(rawLines, 'phys');
  const animGT = denseSingletonGroundTruth(rawLines, 'anim');
  if (physGT.ticks.length < 5) fail(`fixture の phys 行が少なすぎる(${physGT.ticks.length})`);
  if (animGT.ticks.length < 5) fail(`fixture の anim 行が少なすぎる(${animGT.ticks.length})`);
  let physN = 0, animN = 0;
  for (let t = 0; t <= GT.maxTick; t++) {
    const dPhys = denseSingletonAt(physGT, GT.goneAt, reimuId, t);
    const sPhys = S1.frameAt(t, 0).phys;
    const mPhys = singletonRowsClose(dPhys, sPhys, PHYS_FIELDS);
    if (mPhys) fail(`[phys] round-trip t=${t}: ${mPhys}`);
    physN++; cases++;

    const dAnim = denseSingletonAt(animGT, GT.goneAt, reimuId, t);
    const sAnim = S1.frameAt(t, 0).anim;
    const mAnim = singletonRowsClose(dAnim, sAnim, ANIM_FIELDS);
    if (mAnim) fail(`[anim] round-trip t=${t}: ${mAnim}`);
    animN++; cases++;
  }
  console.log(`round-trip(phys): ${physN} 件 / round-trip(anim): ${animN} 件`);
}

// ===========================================================================
// 7. vis: 前方フィル・変化点・gone境界を合成トレースで検査(13-02)。
//    fixtureにvis行が0件のため(SimProbe.reimu()はphys/animのみ発行、visは弾の
//    エフェクト専用で combat-60t.jsonl のシナリオでは未使用と実測済み)、
//    4b/4c(yaw最短弧・テレポート)と同じ作法で合成する。
// ===========================================================================
{
  const synth = [
    '{"t":0,"ch":"spawn","id":9101,"type":"touhou_little_maid:yin_yang_orb","role":"projectile","w":0.4,"h":0.4}',
    '{"t":0,"ch":"vis","id":9101,"age":0,"scale":1.0,"alpha":0.9,"color":1,"spin":10}',
    '{"t":3,"ch":"vis","id":9101,"age":3,"scale":1.0,"alpha":0.9,"color":1,"spin":40}',
    '{"t":5,"ch":"gone","id":9101,"reason":"hit"}',
    // maxTickをgoneより先へ伸ばす行(t=10) —— これが無いとframeAt(6,0)のtがmaxTick=5へ
    // クランプされてしまい、「gone後」を実際には問い合わせられない(この合成トレース
    // 自身の限界であって実装の欠陥ではない。実fixtureはtrail全体がgoneよりずっと長い
    // ので普段は問題にならないが、合成トレースでは明示的に確保する必要がある)。
    '{"t":10,"ch":"log","msg":"trace continues past 9101 gone tick"}',
  ].join('\n');
  const Sv = SimStore.create();
  Sv.append(synth);

  cases++;
  const beforeChange = Sv.frameAt(1, 0).vis.get(9101);
  if (!beforeChange || beforeChange.spin !== 10) fail(`vis前方フィル: t=1(t=0の変化点の直後)はspin=10のはずが ${beforeChange && beforeChange.spin}`);

  cases++;
  const atChange = Sv.frameAt(3, 0).vis.get(9101);
  if (!atChange || atChange.spin !== 40) fail(`vis変化点: t=3はspin=40のはずが ${atChange && atChange.spin}`);

  cases++;
  const atGoneTick = Sv.frameAt(5, 0).vis.get(9101);
  if (!atGoneTick) fail('vis gone境界: gone tick自身(t=5)はまだ表示されるはず(isAliveはt<=goneAtで生存)');

  cases++;
  const afterGone = Sv.frameAt(6, 0).vis.get(9101);
  if (afterGone) fail(`vis gone境界: goneした(t=5)より後(t=6)にvisが残っている: ${JSON.stringify(afterGone)}`);

  cases++;
  // partialを渡しても補間しない(常にstateAt相当) —— vis はカテゴリ的な color を含むため
  // 13-02-PLAN.md の指示どおり lerp しない。
  const withPartial = Sv.frameAt(0, 0.9).vis.get(9101);
  if (!withPartial || withPartial.spin !== 10) fail(`vis補間しない: partial=0.9でもspin=10(直前値)のままのはずが ${withPartial && withPartial.spin}`);
}

// ===========================================================================
// 8. 事象は t の外へ漏れない(13-02): fixture の全 dmg/sound/proj/log/ai 行が
//    自分のtickのframeAtにだけ現れ、前後のtickには現れない。
//    行の.tがそのまま内容に含まれるので、JSON文字列一致は自動的にtickも区別する
//    (別tickの同一内容の行と誤って一致することはない)。
// ===========================================================================
{
  const EVENT_CHANNELS = ['dmg', 'sound', 'proj', 'log', 'ai'];
  let checked = 0;
  for (const line of rawLines) {
    let e; try { e = JSON.parse(line); } catch { continue; }
    if (!EVENT_CHANNELS.includes(e.ch)) continue;
    const wantStr = JSON.stringify(e);
    const here = S1.frameAt(e.t, 0)[e.ch].some((x) => JSON.stringify(x) === wantStr);
    cases++;
    if (!here) fail(`event isolation: ${e.ch} 行(t=${e.t})が自分のtickのframeAtに見つからない: ${line.slice(0, 160)}`);
    if (e.t > 0) {
      const before = S1.frameAt(e.t - 1, 0)[e.ch].some((x) => JSON.stringify(x) === wantStr);
      cases++;
      if (before) fail(`event isolation: ${e.ch} 行(t=${e.t})が t-1=${e.t - 1} に漏れている`);
    }
    if (e.t < S1.maxTick) {
      const after = S1.frameAt(e.t + 1, 0)[e.ch].some((x) => JSON.stringify(x) === wantStr);
      cases++;
      if (after) fail(`event isolation: ${e.ch} 行(t=${e.t})が t+1=${e.t + 1} に漏れている`);
    }
    checked++;
  }
  if (checked < 50) fail(`event isolation: 検査できた事象行が${checked}件しかない(fixtureが小さすぎる可能性)`);
  console.log(`event isolation: ${checked} 件の事象行(${EVENT_CHANNELS.join('/')})を検査`);
}

// ===========================================================================
// 9. 未知チャンネルは事象レーンへ落ちる(13-02, T-13-06): 合成した1行で確認。
//    CHANNEL_LANESに無いチャンネル名でも、eventsInRange/eventCount経由で見える
//    (前方フィルされる状態レーンには絶対に落ちない、という既定の裏付け)。
// ===========================================================================
{
  const Su = SimStore.create();
  const r = Su.append('{"t":7,"ch":"totally_unknown_channel","id":1,"foo":"bar"}');
  cases++;
  if (r.ingested !== 1) fail(`未知チャンネル: 取り込み失敗として扱われている(ingested=${r.ingested})`);
  cases++;
  const viaRange = Su.eventsInRange('totally_unknown_channel', 0, 7);
  if (viaRange.length !== 1 || viaRange[0].foo !== 'bar') fail(`未知チャンネル: eventsInRangeで1件取れるはずが ${JSON.stringify(viaRange)}`);
  cases++;
  if (Su.eventCount('totally_unknown_channel') !== 1) fail(`未知チャンネル: eventCountが1のはずが ${Su.eventCount('totally_unknown_channel')}`);
  cases++;
  if (SimStore.CHANNEL_LANES.totally_unknown_channel !== undefined) fail('未知チャンネル: CHANNEL_LANESに事前登録されていないことがこの検査の前提');
  console.log('unknown channel -> event lane: ok');
}

// ===========================================================================
// 10. 派生物(13-02 Task 2): trackOf(弾の軌跡)とlatestEvent(AI索引)が、10分割append
//    と1回appendで同じ答えになる。walk/animTrackはgl.js側にありnode:vmではWebGL文脈が
//    無いため検査できない(検査できないものを検査したと書かない——bench.mjsの飛び込み
//    モードで実測してSUMMARYに数字で残す)。ここではストア側から取れる派生物
//    (trackOf/latestEvent)についてだけ検査する。
// ===========================================================================
{
  const Ta = SimStore.create();
  Ta.append(rawText);
  const Tb = SimStore.create();
  const CHUNKS = 10;
  const per = Math.ceil(rawLines.length / CHUNKS);
  for (let i = 0; i < CHUNKS; i++) {
    const chunk = rawLines.slice(i * per, (i + 1) * per);
    if (chunk.length) Tb.append(chunk);
  }

  // trackOf: 全projectile entityについて、t0/t1と全tickのat(t)が一致する。
  let trackChecked = 0;
  for (const [id, ent] of Ta.entities) {
    if (ent.role !== 'projectile') continue;
    const trA = Ta.trackOf(id), trB = Tb.trackOf(id);
    cases++;
    if ((trA === null) !== (trB === null)) { fail(`trackOf分割不一致(null性) id=${id}`); continue; }
    if (!trA) continue;
    cases++;
    if (trA.t0 !== trB.t0 || trA.t1 !== trB.t1) fail(`trackOf分割不一致(範囲) id=${id} A=[${trA.t0},${trA.t1}] B=[${trB.t0},${trB.t1}]`);
    for (let t = trA.t0; t <= trA.t1; t++) {
      const pa = trA.at(t), pb = trB.at(t);
      cases++;
      if ((pa === null) !== (pb === null)) { fail(`trackOf分割不一致(null性) id=${id} t=${t}`); continue; }
      if (pa && (pa.x !== pb.x || pa.y !== pb.y || pa.z !== pb.z)) {
        fail(`trackOf分割不一致(値) id=${id} t=${t} A=(${pa.x},${pa.y},${pa.z}) B=(${pb.x},${pb.y},${pb.z})`);
      }
      trackChecked++;
    }
  }
  if (trackChecked < 50) fail(`trackOf分割一致検査: 検査点が${trackChecked}件しかない(fixtureにprojectileが少なすぎる可能性)`);
  console.log(`trackOf split-append equivalence: ${trackChecked} 点 (projectile entities)`);

  // latestEvent('ai', t): 全tickで1回appendと10分割appendが同じ行を返す(内容比較)。
  let aiChecked = 0;
  for (let t = 0; t <= Ta.maxTick; t++) {
    const la = Ta.latestEvent('ai', t), lb = Tb.latestEvent('ai', t);
    cases++;
    if ((la === null) !== (lb === null)) { fail(`latestEvent('ai')分割不一致(null性) t=${t}`); continue; }
    if (la && JSON.stringify(la) !== JSON.stringify(lb)) {
      fail(`latestEvent('ai')分割不一致(値) t=${t} A=${JSON.stringify(la)} B=${JSON.stringify(lb)}`);
    }
    aiChecked++;
  }
  console.log(`latestEvent('ai') split-append equivalence: ${aiChecked} ticks`);
}

// ===========================================================================
console.log(`cases: ${cases} (need >= 300)`);
console.log(`worst numeric residual: ${worstNum.toExponential(3)} (tol ${NUM_TOL})`);
console.log(`failures: ${failures}`);

if (cases < 300) {
  fail(`only ${cases} cases ran (need >= 300) — a selftest that can pass on zero cases is not a selftest`);
}

if (failures > 0) {
  console.error(`store-selftest: ${failures} failure(s)`);
  process.exit(1);
}
console.log('store-selftest: OK');
process.exit(0);
