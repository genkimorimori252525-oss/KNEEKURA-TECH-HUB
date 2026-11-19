#!/usr/bin/env node
/**
 * score-hold.mjs — メインハンドの握りを「自作合成」と「YSM の状態機械」で採点し比べる。
 *
 * 使い方:
 *   node simlab/viewer/score-hold.mjs [記録のstamp] [--pair=sorted|best|worst]
 *   (既定の stamp は 20260819-212842 = animsweep で 316 本のアニメを一巡した記録)
 *
 * ------------------------------------------------------------------------------------
 * なぜ要るか
 * ------------------------------------------------------------------------------------
 * 2026-08-20、夢想封印 (extra95) 中に霊夢の前腕が約72度折れる不具合が出た。真因は
 * gl.js の holdAnimFor が「メインハンドが剣 → hold_mainhand:sword1」と決め打ちして
 * いたこと。**sword1 は抜刀の一瞬のアニメで、剣を持った定常状態ではない。**
 * 実機のパックの状態機械 player.pre_hold は [sword] を q.all_animations_finished で
 * 必ず抜けて [sword_end] へ移る。前腕 RightForeArm への X 回転:
 *
 *     hold_mainhand:sword1    = -72.0 度   <- 旧既定が常時当てていた
 *     hold_mainhand:sword_end =  -1.6 度   <- 定常状態はこちら
 *     hold_mainhand:empty     =   0.0 度
 *
 * ------------------------------------------------------------------------------------
 * この採点器の限界 (先に書いておく。数字を過信しないため)
 * ------------------------------------------------------------------------------------
 * 1. **全身の中央値は鈍い。** 腕は 1,868 quad のうちの数十しかないので、全身の
 *    中央値には腕の違いがほとんど出ない。だから「腕のボーンとその子孫だけ」を
 *    主たる物差しにし、全身は退行の見張りに使う。
 * 2. **同じ UV 矩形を持つ quad の組み方には任意性がある。** 霊夢のモデルは左右の腕で
 *    UV を共有しているので (§下の対応付けの節)、どちらとどちらを組むかを決める必要がある。
 *    現行は座標順に添字で組む。**この任意性が結論を動かさないことは実測で確かめた** ——
 *    誤差が最大になる割り当てを総当たりで作っても (--pair=worst)、腕の数字は
 *    0.1794 -> 0.1478 (-17.6%)、extra95 は -63% で<b>1桁も動かない</b>。
 * 3. **実機の記録は正しいが、記録に無い量は測れない。** 記録は頂点だけで、
 *    どのアニメがどの重みで乗っていたかは入っていない。
 * 4. **これは再構成どうしの比較。** 実機の見た目が正しいかは目視でしか判らない。
 *
 * ------------------------------------------------------------------------------------
 * データの読み方 (WORKLOG-2026-08-19-ysm-animsweep.md の警告に従う)
 * ------------------------------------------------------------------------------------
 * - .pose.bin は約 8.1GB ある。**まるごと読んではいけない。**
 *   フレーム i のバイト位置は cumsum(lens[0..i-1]) * stride * 4、長さは lens[i]*stride*4。
 *   fs.readSync でその範囲だけ読む。
 * - animsweep の記録では **.pose.json の slots は使わず、.anims.json の from/to を使う**
 *   (slots[i]===i なので実害は無いが、意味の上で from/to が正しい索引)。
 */
import fs from 'node:fs';
import path from 'node:path';

const REPO = path.resolve(path.dirname(new URL(import.meta.url).pathname).replace(/^\/([A-Za-z]:)/, '$1'), '..', '..');
const PACK = 'C:/Users/genki/AppData/Roaming/.minecraft/config/yes_steve_model/custom/「博丽灵梦」2';
const POSES = 'C:/Users/genki/AppData/Roaming/.minecraft-simlab/simlab/poses';
const ARGV = process.argv.slice(2);
const STAMP = ARGV.find((a) => !a.startsWith('--')) || '20260819-212842';
/** 同じ UV 矩形の quad をどう組むか。`sorted` (既定) / `best` / `worst`。{@link pairUp} 参照。 */
const PAIR_MODE = (() => {
  const a = ARGV.find((x) => x.startsWith('--pair='));
  const v = a ? a.slice('--pair='.length) : 'sorted';
  if (['sorted', 'best', 'worst'].indexOf(v) < 0) {
    console.error('--pair は sorted / best / worst のいずれか (指定: ' + v + ')');
    process.exit(2);
  }
  return v;
})();
const P = path.join(POSES, STAMP);

// ysm.js は純粋計算モジュールなので Node からそのまま評価できる (ブラウザ専用 API を使わない)
(0, eval)(fs.readFileSync(path.join(REPO, 'simlab/viewer/ysm.js'), 'utf8'));
const Y = globalThis.YSM, M = Y.M;

// ---------------------------------------------------------------------------
// モデルとアニメ
// ---------------------------------------------------------------------------
const man = JSON.parse(fs.readFileSync(PACK + '/ysm.json', 'utf8'));
const model = JSON.parse(fs.readFileSync(path.join(PACK, man.files.player.model.main), 'utf8'));
const anims = {};
for (const rel of Object.values(man.files.player.animation || {})) {
  // 読めなかったファイルは黙って飛ばさない。hold_mainhand:sword1 / sword_end が
  // 入っているファイルを落とすと、握りが当たらないのに「改善した」ように見えてしまう。
  try {
    Object.assign(anims, JSON.parse(fs.readFileSync(path.join(PACK, rel), 'utf8')).animations || {});
  } catch (e) {
    console.error('警告: アニメファイルを読めなかった: ' + rel + ' (' + e.message + ')');
  }
}
for (const need of ['hold_mainhand:sword1', 'hold_mainhand:sword_end']) {
  if (!anims[need]) { console.error('FATAL: ' + need + ' がパックに無い。採点できない'); process.exit(2); }
}
const ctlJson = JSON.parse(fs.readFileSync(PACK + '/controller/parallel_controllers.json', 'utf8'));
const props = man.properties || {};
const geo = Y.buildGeometry(model['minecraft:geometry'][0], props.width_scale || 1,
  props.height_scale || 1, Y.collectHidden(anims));

// 下地は pre_ を先に積む (可視性の切替を、形の微調整で上書きさせないため)
const baseAll = Object.keys(anims).filter((n) => /^(pre_)?parallel/.test(n));
const ORDER = baseAll.filter((n) => /^pre_/.test(n)).sort()
  .concat(baseAll.filter((n) => !/^pre_/.test(n)).sort());

// gl.js の ROAMING_DEFAULTS と揃える
const ROAM = { 'v.roaming.yan': 4 };

/**
 * gl.js の {@code ctrlVarsAt()} が実機トレースから作る molang 変数のうち、
 * **animsweep の状況 (霊夢は静止したままアニメを1本ずつ再生した) に対応する値**。
 *
 * <p><b>ここを省くと採点が壊れる。</b> 最初この定数を入れ忘れて
 * {@code q.all_animations_finished} を与えなかったところ、状態機械が
 * {@code [sword]} 状態から抜けられず ({@code sword -> sword_end} の遷移条件がこれ)、
 * 定常状態の {@code sword_end} (-1.6°) ではなく抜刀の {@code sword1} (-72°) を
 * 重み 0.45 で当て続けた。結果 "腕 10.2% 悪化 / RESULT: FAIL" という
 * <b>採点器のほうが間違っている</b>数字が出た。
 *
 * <p>gl.js は {@code q.all_animations_finished} を無条件に 1 で入れているので、
 * 実際の Viewer は最初から {@code sword_end} に居る。採点器はそれに合わせる。
 */
const CTRL_VARS = {
  // 状態機械の遷移条件。gl.js の ctrlVarsAt() が入れているものと同じ
  'q.all_animations_finished': 1,
  'query.any_animation_finished': 1,
  // animsweep は霊夢を立たせたままアニメを再生しただけなので、移動系はすべて静止
  'ctrl.jump': 0,
  'ctrl.run': 0,
  'ctrl.walk': 0,
  'ctrl.idle': 1,
  'ctrl.fly': 0,
  'ctrl.sneak': 0,
  'ctrl.sneaking': 0,
  'ctrl.sit': 0,
  'ctrl.sleep': 0,
  // 霊夢は剣 (実機では御幣として描かれる) を持っている
  'ctrl.hold(mainhand,:sword)': 1,
  'ctrl.hold(mainhand,:bow)': 0,
};

// 腕のボーンとその子孫 (袖・手・指まで)
const SRC = model['minecraft:geometry'][0].bones;
const ARM = (() => {
  const out = new Set(['LeftArm', 'RightArm', 'LM', 'RM']);
  let changed = true;
  while (changed) {
    changed = false;
    for (const b of SRC) if (b.parent && out.has(b.parent) && !out.has(b.name)) { out.add(b.name); changed = true; }
  }
  return out;
})();

// ---------------------------------------------------------------------------
// 実機の記録
// ---------------------------------------------------------------------------
const pj = JSON.parse(fs.readFileSync(P + '.pose.json', 'utf8'));
const ranges = (() => { const a = JSON.parse(fs.readFileSync(P + '.anims.json', 'utf8')); return a.anims || a.ranges || a; })();
const OFF = []; { let o = 0; for (const n of pj.lens) { OFF.push(o); o += n * pj.stride * 4; } }
const binBytes = fs.statSync(P + '.pose.bin').size;
const expect = OFF[OFF.length - 1] + pj.lens[pj.lens.length - 1] * pj.stride * 4;
if (expect !== binBytes) {
  console.error('FATAL: .pose.bin のバイト数が合わない (期待 ' + expect + ' / 実際 ' + binBytes + ')');
  process.exit(2);
}
const fd = fs.openSync(P + '.pose.bin', 'r');
// 途中で落ちても閉じる (OS が回収するとはいえ、長く走らせる道具になったときに効く)
process.on('exit', () => { try { fs.closeSync(fd); } catch (e) {} });
function readFrame(i) {
  const n = pj.lens[i] * pj.stride;
  const buf = Buffer.allocUnsafe(n * 4);
  fs.readSync(fd, buf, 0, n * 4, OFF[i]);
  return new Float32Array(buf.buffer, buf.byteOffset, n);
}

// ---------------------------------------------------------------------------
// quad の対応付け — UV 矩形で引き合わせる
// ---------------------------------------------------------------------------
// 位置で対応を取ると循環する (位置こそ答え合わせしたい量なので)。UV は姿勢で変わらない。
//
// **同じ矩形が複数あるときの扱いが要点。** 以前は「曖昧だから両方捨てる」という規則に
// していたが、それでは腕がまるごと測れなかった:
//
//   - 霊夢のモデルは<b>左右の腕で UV 矩形を共有している</b>。1 フレームあたり
//     864 組の重複のうち <b>815 組が X 対称のペア</b> (左腕と右腕) だと実測した。
//   - そのため腕の矩形 474 種は毎フレーム捨てられ、8 枚のフレームのうち 2 枚で
//     126 種 (御幣の分) が拾えるだけ、残りは 0 種だった。
//   - 「同じ位置にある重複だけまとめる」(多方向撮影で2回撮れた分の吸収) では
//     +30 種しか増えず、焼け石に水だった。
//
// なので<b>両側を座標順に並べて順番に組む</b>。左は左と、右は右と組む。
// 並べ方は (x, y, z) の辞書順という固定規則で、**再構成側の答えを見て選ばない**ので
// 有利にも不利にも働かない。側を取り違えるような粗い誤りは、ちゃんと大きな誤差になる。
const rk = (a, b, c, d) => [a, b, c, d].map((x) => x.toFixed(4)).join(',');
const XF = (x, y, z) => [x, 1.501 - y, -z];   // gl.js の描画行列から導いた座標対応
const med = (a) => (a.length ? a[Math.floor(a.length / 2)] : NaN);
const byXYZ = (A, B) => (A.p[0] - B.p[0]) || (A.p[1] - B.p[1]) || (A.p[2] - B.p[2]);

/** UV 矩形をキーに、その矩形を持つ quad の重心を座標順に並べた配列を返す。 */
function quadsOf(arr, stride, xf, boneOf) {
  const m = new Map();
  for (let q = 0; q + 6 * stride <= arr.length; q += 6 * stride) {
    let u0 = Infinity, v0 = Infinity, u1 = -Infinity, v1 = -Infinity, cx = 0, cy = 0, cz = 0;
    for (let k = 0; k < 6; k++) {
      const o = q + k * stride, u = arr[o + 3], v = arr[o + 4];
      if (u < u0) u0 = u; if (u > u1) u1 = u;
      if (v < v0) v0 = v; if (v > v1) v1 = v;
      const p = xf ? xf(arr[o], arr[o + 1], arr[o + 2], o) : [arr[o], arr[o + 1], arr[o + 2]];
      cx += p[0]; cy += p[1]; cz += p[2];
    }
    const key = rk(u0, v0, u1, v1);
    if (!m.has(key)) m.set(key, []);
    m.get(key).push({ p: [cx / 6, cy / 6, cz / 6], bone: boneOf ? boneOf(q) : null });
  }
  for (const list of m.values()) list.sort(byXYZ);
  return m;
}

const dist3 = (a, b) => Math.hypot(a.p[0] - b.p[0], a.p[1] - b.p[1], a.p[2] - b.p[2]);
function permutations(a) {
  if (a.length <= 1) return [a];
  const out = [];
  for (let i = 0; i < a.length; i++) {
    const rest = a.slice(0, i).concat(a.slice(i + 1));
    for (const p of permutations(rest)) out.push([a[i]].concat(p));
  }
  return out;
}

/**
 * 実機の記録と再構成を突き合わせ、対になった quad を `{truth, mine}` の配列で返す。
 * 同じ矩形の個数が食い違うときは<b>少ないほうの数だけ</b>組む (端は捨てる)。
 *
 * <p><b>組み方 (`PAIR_MODE`)</b>:
 * <ul>
 *   <li>`sorted` (既定) —— 両側を座標順に並べて添字で組む。相手側を見ないので
 *       どちらのモードにも有利不利が無い</li>
 *   <li>`best` / `worst` —— 誤差の合計が最小 / 最大になる割り当てを総当たりで探す
 *       (組の大きさ 4 まで)。<b>頑健性の検査用</b></li>
 * </ul>
 *
 * <p><b>なぜ `worst` を用意したか</b> (2026-08-20 の code-review MAJ-01):
 * 「左右の腕が UV を共有しているのに座標順で組むと、姿勢が大きくずれたとき
 * 左右を取り違えて誤差を過小評価しうる。しかもそれが起きるのは、まさに今回
 * 試験している状況ではないか」という指摘があった。もっともなので、
 * <b>誤差が最大になる組み方</b>でも結論が変わらないことを確かめられるようにした。
 * 実測 (20 本 x 2 フレーム、extra93/94/95 を含む):
 * <pre>
 *   組み方        腕: 旧 -> 新              全身: 旧 -> 新
 *   sorted        0.1794 -> 0.1478 (-17.6%)  0.1414 -> 0.1388 (-1.8%)
 *   best          0.1794 -> 0.1478 (-17.6%)  0.1413 -> 0.1385 (-2.0%)
 *   worst         0.1794 -> 0.1478 (-17.6%)  0.2415 -> 0.2395 (-0.8%)
 *   extra95 単独  どの組み方でも 0.2248 -> 0.0826 (-63%)
 * </pre>
 * <b>腕の数字は1桁も動かない。</b> 取り違えの余地は結論に影響しない。
 */
function pairUp(truth, mine) {
  const out = [];
  for (const [key, T] of truth) {
    const Mi = mine.get(key);
    if (!Mi) continue;
    const n = Math.min(T.length, Mi.length);
    if (PAIR_MODE === 'sorted' || n === 1 || n > 4) {
      for (let i = 0; i < n; i++) out.push({ truth: T[i], mine: Mi[i] });
      continue;
    }
    const idx = Array.from({ length: n }, (_, i) => i);
    let best = null;
    for (const p of permutations(idx)) {
      let cost = 0;
      for (let i = 0; i < n; i++) cost += dist3(T[i], Mi[p[i]]);
      if (best === null || (PAIR_MODE === 'worst' ? cost > best.cost : cost < best.cost)) best = { cost, p };
    }
    for (let i = 0; i < n; i++) out.push({ truth: T[i], mine: Mi[best.p[i]] });
  }
  return out;
}

// ---------------------------------------------------------------------------
// 2 つのモードで姿勢を組む
// ---------------------------------------------------------------------------
//   'default' — CTL_LAYERS 既定 ON。握りは player.pre_hold 状態機械が選ぶ
//   'legacy'  — ?ctl=0。holdAnimFor が hold_mainhand:sword1 を重み 1.0 で当てる
function build(animName, relTick, mode) {
  // **両モードに同じ入力を与える。** ctrl 変数は「実機がその瞬間どうだったか」であって
  // モードの違いではない。片方だけに与えると比較が成立しない。
  const vars = Object.assign({}, ROAM, CTRL_VARS);
  for (const n of ORDER) Y.runTimeline(anims[n], vars, {});
  const layers = ORDER.map((n) => Y.sampleAnimation(anims[n], 0, vars));
  if (anims[animName]) layers.push(Y.sampleAnimation(anims[animName], relTick / 20, vars));

  if (mode === 'legacy') {
    const h = anims['hold_mainhand:sword1'];
    if (h) layers.push({ map: Y.sampleAnimation(h, 0, vars), weight: 1, scaleWeight: 1 });
  } else {
    // 状態機械は積分器なので、その tick まで回してから読む
    const ctl = Y.initControllers(ctlJson);
    let active = [];
    for (let i = 0; i <= relTick; i++) {
      active = Y.stepControllers(ctl, vars, 0.05, { weightScale: Y.CONTROLLER_WEIGHT_FIT });
    }
    for (const e of active) {
      const a = anims[e.anim];
      if (!a) continue;
      layers.push({
        map: Y.sampleAnimation(a, e.elapsed, vars),
        weight: e.weight === undefined ? 1 : e.weight,
        scaleWeight: e.scaleWeight === undefined ? 1 : e.scaleWeight,
      });
    }
  }

  const B = Y.poseBones(geo.bones, layers);
  const vv = geo.verts, bi = geo.boneIndex, S = 8;
  return quadsOf(vv, S,
    (x, y, z, o) => { const b = bi[o / S] | 0; const p = M.apply(B.subarray(b * 16, b * 16 + 16), [x, y, z]); return XF(p[0], p[1], p[2]); },
    (q) => { const b = bi[q / S] | 0; return geo.bones[b] ? geo.bones[b].name : null; });
}

// ---------------------------------------------------------------------------
// 採点する対象を選ぶ
// ---------------------------------------------------------------------------
// 夢想封印 (extra93/94/95) は今回の不具合そのものなので必ず入れる。
// 残りは「実際に動いているアニメ」から等間隔で拾う (静止アニメは差が出ないので無駄)。
const REPORTED = ['extra93', 'extra94', 'extra95'];
const MIN_RANGE = 14;   // rel=3 と rel=12 を読むので、これ未満の範囲は読み出しが範囲外へ出る
const movers = [];
for (const r of ranges) {
  const nm = r.anim || r.name;
  if (r.from == null || r.to == null || r.to - r.from < MIN_RANGE) continue;
  if (!anims[nm] || !anims[nm].bones) continue;
  const A = readFrame(r.from), B2 = readFrame(r.from + 10);
  if (A.length !== B2.length) { movers.push({ nm, from: r.from }); continue; }
  let moved = 0, total = 0;
  for (let i = 0; i + pj.stride <= A.length; i += pj.stride) {
    total++;
    const dx = A[i] - B2[i], dy = A[i + 1] - B2[i + 1], dz = A[i + 2] - B2[i + 2];
    if (dx * dx + dy * dy + dz * dz > 4e-4) moved++;
  }
  if (total && moved / total > 0.05) movers.push({ nm, from: r.from });
}
const picked = new Map();
for (const nm of REPORTED) {
  const r = ranges.find((x) => (x.anim || x.name) === nm);
  // 他のサンプルと同じ下限を課す。ここだけ素通りさせると、短い範囲のときに
  // 隣のアニメのフレームを読んで採点してしまう
  if (r && r.from != null && r.to != null && r.to - r.from >= MIN_RANGE) picked.set(nm, r.from);
  else console.error('警告: ' + nm + ' は範囲が短すぎるか見つからないので採点対象から外した');
}
const step = Math.max(1, Math.floor(movers.length / 30));
for (let i = 0; i < movers.length && picked.size < 32; i += step) picked.set(movers[i].nm, movers[i].from);
const SAMPLE = [...picked.entries()].map(([nm, from]) => ({ nm, from }));

// ---------------------------------------------------------------------------
// 採点
// ---------------------------------------------------------------------------
console.log('score-hold — 記録 ' + STAMP + ' (' + ranges.length + ' 本のアニメ / ' + pj.lens.length + ' フレーム / ' + (binBytes / 1e9).toFixed(1) + 'GB)');
console.log('対象 ' + SAMPLE.length + ' 本 x 2 フレーム。夢想封印 ' + REPORTED.filter((n) => picked.has(n)).join('/') + ' を明示的に含む'
  + (PAIR_MODE === 'sorted' ? '' : '   [組み方: ' + PAIR_MODE + ']'));
console.log('');

const arm = { legacy: [], default: [] }, whole = { legacy: [], default: [] };
const perAnim = [];
let armQuads = 0;   // 腕の比較点が実際に何個取れたか (少なすぎたら判定しない)
for (const s of SAMPLE) {
  const row = { nm: s.nm };
  for (const rel of [3, 12]) {
    const truth = quadsOf(readFrame(s.from + rel), pj.stride, null, null);
    for (const mode of ['legacy', 'default']) {
      const mine = build(s.nm, rel, mode);
      const ea = [], ew = [];
      for (const { truth: t, mine: y } of pairUp(truth, mine)) {
        const d = Math.hypot(t.p[0] - y.p[0], t.p[1] - y.p[1], t.p[2] - y.p[2]);
        ew.push(d);
        if (y.bone && ARM.has(y.bone)) ea.push(d);
      }
      ea.sort((a, b) => a - b); ew.sort((a, b) => a - b);
      armQuads += ea.length;
      if (ea.length) { arm[mode].push(med(ea)); row[mode] = Math.min(row[mode] === undefined ? Infinity : row[mode], med(ea)); }
      if (ew.length) whole[mode].push(med(ew));
    }
  }
  perAnim.push(row);
}
for (const g of [arm, whole]) for (const k of ['legacy', 'default']) g[k].sort((a, b) => a - b);

const aL = med(arm.legacy), aD = med(arm.default);
const wL = med(whole.legacy), wD = med(whole.default);
console.log('物差し              旧 (合成 sword1)   新 (状態機械)    比較点');
console.log('  腕のボーンのみ      ' + aL.toFixed(4) + '            ' + aD.toFixed(4) + '         ' + arm.legacy.length);
console.log('  全身                ' + wL.toFixed(4) + '            ' + wD.toFixed(4) + '         ' + whole.legacy.length);
console.log('');

// 判定。**2% の許容は「差が出ないこと」ではなく「悪化していないこと」を見るための幅**。
// 腕の実効果は 5% 程度 (extra95 単独なら 64%) なので、この幅は効果より小さく、
// ゆるすぎて素通りする心配は無い。逆に厳しすぎてサンプリングのゆらぎで落ちることも無い。
const TOL = 1.02;
// **比較点が少なすぎるときは判定しない。** 2026-08-20 に、腕の対応が毎フレーム
// 捨てられていて 64 通り中 8 通りしか値が出ていないのに "33.6% 悪化 / FAIL" という
// 数字が出た。母数を書かない採点は嘘をつく。
const MIN_ARM_SAMPLES = 24;   // (アニメ, フレーム) の組で、腕の値が取れた数
const armMeasurable = arm.legacy.length >= MIN_ARM_SAMPLES && arm.default.length >= MIN_ARM_SAMPLES;
const okArm = armMeasurable ? (aD <= aL * TOL) : null;
const okWhole = wD <= wL * TOL;
const dA = ((aD / aL - 1) * 100), dW = ((wD / wL - 1) * 100);
console.log('  腕  : ' + (armMeasurable
  ? ((dA <= 0 ? (-dA).toFixed(1) + '% 改善' : dA.toFixed(1) + '% 悪化') + '  -> ' + (okArm ? 'OK' : 'NG'))
  : ('比較点 ' + armQuads + ' 個 / 有効な組 ' + arm.legacy.length + ' (下限 ' + MIN_ARM_SAMPLES + ') -> **測定不能**。判定に使わない')));
console.log('  全身: ' + (dW <= 0 ? (-dW).toFixed(1) + '% 改善' : dW.toFixed(1) + '% 悪化') + '  -> ' + (okWhole ? 'OK (退行なし)' : 'NG (退行)'));
console.log('');

const wins = perAnim.filter((r) => r.default !== undefined && r.legacy !== undefined && r.default < r.legacy * 0.98);
if (wins.length) {
  console.log('状態機械が効いたアニメ:');
  for (const r of wins.sort((a, b) => (a.default / a.legacy) - (b.default / b.legacy)).slice(0, 8)) {
    console.log('  ' + r.nm.padEnd(14) + '旧 ' + r.legacy.toFixed(4) + ' -> 新 ' + r.default.toFixed(4)
      + '  (' + ((r.default / r.legacy - 1) * 100).toFixed(0) + '%)');
  }
  console.log('');
}

const pass = okWhole && (okArm === null || okArm);
console.log('RESULT: ' + (pass ? (armMeasurable ? 'PASS' : 'PASS (全身の退行なしのみ。腕は測定不能)') : 'FAIL'));
console.log('(これは再構成どうしの比較。**実機の見た目が正しいかはにーくらの目視判定**で、'
  + 'この採点は「腕が悪化していないこと」しか保証しない)');
process.exit(pass ? 0 : 1);
