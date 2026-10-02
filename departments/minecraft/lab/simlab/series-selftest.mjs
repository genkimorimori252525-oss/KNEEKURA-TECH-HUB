#!/usr/bin/env node
// =============================================================================
// series-selftest.mjs — stats.mjs の series()/seriesState()/seriesFeed()/seriesLanes()
// の自己検査。依存ゼロ。ブラウザ不要(stats.mjs は素の ES モジュールなので node:vm も不要)。
// =============================================================================
//
// 使い方: node simlab/series-selftest.mjs
//
// 何を測るか(13-03 Task 1 <behavior>):
//   0. 実装が1本(seriesState/seriesFeed/seriesLanesの3つ+薄い包みseries())であること。
//      戻り値に carry(reimuId・goneAt等の内部状態)が漏れていないこと。
//   1. golden一致: commit済み2fixtureのseries()が series-dense.golden.json
//      (stats.mjs を変える"前"に保存した基準)とdeep-equal。
//   2. 疎密一致: 各fixtureの冗長行(pos/phys/anim/vis、前tickと全フィールド一致)を
//      落とした版と落としていない版でseries()がdeep-equal(既存27本の後方互換の核心)。
//   3. 追記の等価性: 1回でまとめてfeedした状態と、複数分割(2/3/10分割、および
//      1イベントずつという最も細かい分割)でfeedした状態のseriesLanesがdeep-equal。
//   4. 二重取り込み: 同じ行を2度feedしても、加算レーン(dmg/proj)を含めて1度と同じ。
//   5. 実トレース27本(run/sim/traces/**/arena-*.jsonl)が在れば、着手前に保存した
//      ハッシュ表(run/sim/traces/.series-selftest-baseline.json、gitignore下・非commit)
//      と突き合わせる。無い機械では探した場所を出してskipする(それを合格とは書かない)。
//      commit済み2本(検査1)はこのファイル自体に埋め込まれているので、実トレースの
//      有無に関わらず必ず検査される——「1件も検査せずに合格するゲート」にはならない。
//
// ---- hold-back(保留)機構について ----
// seriesFeed(state, events) は既定で「直近に観測した tick」を確定させない。1つの
// tick の複数チャンネル(reimuのpos・targetのpos・aiのdistフォールバック等)が別々の
// feed呼び出しに分かれて届くことがあり、まだ全チャンネルが揃っていないtickを先に
// 確定させると、後から届く分を2周目が二度と見ずに取りこぼす——combat-60t.jsonlの
// 10分割feedで dist[58] が実際にこの形で壊れるのを見て特定した(stats.mjs の
// seriesFeed docstring 参照)。これ以上データが来ないと判っている場合(バッチ処理・
// トレースの末尾)は opts.final=true で保留ぶんも確定させる。series() 自身は内部で
// これを渡す(薄い包みなので中身は3行のまま)。このファイルで「1回でまとめてfeedする」
// 箇所は、単発の seriesFeed でも必ず final:true を明示する——省くと series() とは
// 異なる「末尾数tick未確定」の状態を比較することになり、意図と違う失敗を報告してしまう。
//
// ---- 実測に基づく1点の記録(次に stats.mjs へ触る人のための注記) ----
// onG/air/embed の前方フィル境界(gone が無いときのフォールバック)は、当初
// 「trace全体で観測できた最大tick(lastDataTick、他チャンネル込み)」にしていたが、
// 27本の実トレース照合で1本(tank/20260820/20260821-031644、サーバ強制終了で録画が
// 途中で切れ、reimuの最後のphys行だけが壊れたJSONとして捨てられたが同じtickのpos行は
// 書き切れていたケース)が旧実装と食い違った。onG/air/embed 専用に「phys行そのものの
// 最大tick(lastPhysObsTick)」へ絞ったことで解消した(stats.mjs の該当フィールド参照)。
// **既知の限界として記録する**: これは"phys が完全に沈黙した"区間の末尾(=まだ現在も
// 続いているライブの直近)をどこまで前方フィルするかという問題で、13-04がphysを
// delta化した後、reimuが極端に長時間(例: 数千tick)完全静止し続けると、その静止区間の
// 末尾付近では前方フィルの境界がその間ずっと更新されない(=フィルが一切効かない
// わけではなく、"最後の変化点"からの区間はこれまで通り正しく埋まるが、"現在"に
// 近づくにつれ埋める根拠が薄くなる、程度の話)。これは stats.mjs 単体では解決できない
// (トレースに信号が無ければ埋める根拠も無い)——13-04 が phys の完全な沈黙を許すなら、
// 一定間隔(例: Ntickごと)の keep-alive 行を書くことを検討する価値がある。

import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.join(HERE, '..');
const STATS_MJS = path.join(HERE, 'stats.mjs');
const GOLDEN_PATH = path.join(HERE, 'fixtures', 'series-dense.golden.json');
const FIXTURES = {
  'combat-60t.jsonl': path.join(HERE, 'fixtures', 'combat-60t.jsonl'),
  'stairs-20260819-043053.ai-anim.jsonl': path.join(HERE, 'fixtures', 'stairs-20260819-043053.ai-anim.jsonl'),
};
const TRACES_ROOT = path.join(REPO_ROOT, 'run', 'sim', 'traces');
const BASELINE_PATH = path.join(TRACES_ROOT, '.series-selftest-baseline.json');

const stats = await import('file://' + STATS_MJS.replace(/\\/g, '/'));
const { parseTrace, series, seriesState, seriesFeed, seriesLanes } = stats;

let failures = 0;
let cases = 0;
const fail = (msg) => { failures++; console.error('FAIL: ' + msg); };

// ===========================================================================
// 比較ヘルパ。NaN 同士は等しいとみなす(素の配列に NaN が混ざるため、=== では
// 比較できない — pick-selftest.mjs/store-selftest.mjs と同じ配慮)。
// ===========================================================================
// NaN/null は同じ「値なし」として扱う。golden(series-dense.golden.json)は
// JSON.stringify を経由しており、NaN は JSON に存在しないため null に化ける
// (JSON.stringify(NaN) === 'null' は言語仕様)。読み戻した golden の NaN 相当は
// 素の null、フレッシュな series() 計算の NaN 相当は本物の NaN ——同じレーンの
// 「未観測」を指しているので、ここで揃えて比較する。
function isNoValue(v) { return v === null || (typeof v === 'number' && Number.isNaN(v)); }
function arraysDeepEqual(a, b) {
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) {
    const x = a[i], y = b[i];
    if (isNoValue(x) && isNoValue(y)) continue;
    if (x !== y) return false;
  }
  return true;
}
function seriesEqual(a, b) {
  const ka = Object.keys(a), kb = Object.keys(b);
  if (ka.length !== kb.length) return `key count ${ka.length} vs ${kb.length} (${ka.join(',')} vs ${kb.join(',')})`;
  for (const k of ka) {
    if (!Array.isArray(a[k]) || !Array.isArray(b[k])) return `lane ${k} は配列ではない`;
    if (!arraysDeepEqual(a[k], b[k])) return `lane ${k} が不一致`;
  }
  return null;
}

// ===========================================================================
// 0. 実装が1本であること: seriesState()+seriesFeed()+seriesLanes() === series()。
//    戻り値に carry(内部状態)が漏れていないこと。
// ===========================================================================
{
  for (const f of ['seriesState', 'seriesFeed', 'seriesLanes', 'series', 'parseTrace']) {
    cases++;
    if (typeof stats[f] !== 'function') fail(`stats.mjs is missing export: ${f}`);
  }
  const text = fs.readFileSync(FIXTURES['combat-60t.jsonl'], 'utf8');
  const { events } = parseTrace(text);
  const a = series(events);
  const st = seriesState();
  seriesFeed(st, events, { final: true }); // 単発でも「これで全部」と伝える(上のdocstring参照)
  const b = seriesLanes(st);
  cases++;
  const msg0 = seriesEqual(a, b);
  if (msg0) fail(`batch(series)と単発feed(seriesFeed+final)が不一致: ${msg0}`);
  cases++;
  if (JSON.stringify(a).includes('carry')) fail('series()の戻り値にcarry由来のキーが含まれている');
  console.log(`one implementation ok: seriesState/seriesFeed/seriesLanes/series, lanes=${Object.keys(a).length}`);
}

// ===========================================================================
// 1. golden一致: commit済み2fixtureのseries()が変更前の基準とdeep-equal
// ===========================================================================
if (!fs.existsSync(GOLDEN_PATH)) {
  fail(`golden が無い: ${GOLDEN_PATH}`);
} else {
  const golden = JSON.parse(fs.readFileSync(GOLDEN_PATH, 'utf8'));
  const goldenNames = Object.keys(golden);
  cases++;
  if (goldenNames.length < 2) fail(`golden が ${goldenNames.length} fixture しか無い(2本必要)`);
  for (const [name, fpath] of Object.entries(FIXTURES)) {
    cases++;
    if (!golden[name]) { fail(`golden に ${name} が無い`); continue; }
    const text = fs.readFileSync(fpath, 'utf8');
    const { events } = parseTrace(text);
    const out = series(events);
    const msg = seriesEqual(golden[name], out);
    if (msg) fail(`golden不一致 ${name}: ${msg}`);
    else console.log(`golden match: ${name} (${out.onG.length} ticks)`);
  }
}

// ===========================================================================
// 2. 疎密一致: 各fixtureの冗長行(pos/phys/anim/vis、前tickと全フィールド一致)を
//    落とした版と落としていない版でseries()がdeep-equal
// ===========================================================================
function rowIsRedundant(prev, row) {
  if (!prev || !row) return false;
  const keys = new Set(Object.keys(prev).concat(Object.keys(row)));
  keys.delete('t');
  for (const k of keys) { if (prev[k] !== row[k]) return false; }
  return true;
}
const SPARSIFY_CHANNELS = new Set(['pos', 'phys', 'anim', 'vis']);
function sparsifyEvents(events) {
  const lastByKey = new Map();
  const out = [];
  let dropped = 0;
  for (const e of events) {
    if (!e || !SPARSIFY_CHANNELS.has(e.ch)) { out.push(e); continue; }
    const key = e.ch + ':' + (e.id !== undefined ? e.id : '');
    const prev = lastByKey.get(key);
    if (rowIsRedundant(prev, e)) { dropped++; } else { out.push(e); }
    lastByKey.set(key, e);
  }
  return { out, dropped };
}
for (const [name, fpath] of Object.entries(FIXTURES)) {
  const text = fs.readFileSync(fpath, 'utf8');
  const { events } = parseTrace(text);
  const denseOut = series(events);
  const { out: sparseEvents, dropped } = sparsifyEvents(events);
  cases++;
  if (dropped <= 0) fail(`${name}: 冗長行フィルタが1行も落とさなかった(fixtureの中身を確認せよ)`);
  const sparseOut = series(sparseEvents);
  cases++;
  const msg = seriesEqual(denseOut, sparseOut);
  if (msg) fail(`疎密不一致 ${name}: ${msg}`);
  else console.log(`dense==sparse: ${name} (${dropped}/${events.length}行を落として一致)`);
}

// ===========================================================================
// 3. 追記の等価性: 1回でまとめてfeedした状態と、複数分割でfeedした状態の
//    seriesLanesがdeep-equal。境界の取り方に依存しないことを示すため、
//    分割数を変えたものに加えて「1イベントずつ」という最も細かい分割も検査する。
// ===========================================================================
function feedInChunks(events, chunkCount) {
  const state = seriesState();
  if (events.length === 0) { seriesFeed(state, [], { final: true }); return seriesLanes(state); }
  const per = Math.max(1, Math.ceil(events.length / chunkCount));
  for (let i = 0; i * per < events.length; i++) {
    const chunk = events.slice(i * per, (i + 1) * per);
    const isLast = (i + 1) * per >= events.length;
    if (chunk.length) seriesFeed(state, chunk, { final: isLast });
  }
  return seriesLanes(state);
}
for (const [name, fpath] of Object.entries(FIXTURES)) {
  const text = fs.readFileSync(fpath, 'utf8');
  const { events } = parseTrace(text);
  const batch = series(events);
  for (const chunkCount of [2, 3, 10]) {
    cases++;
    const inc = feedInChunks(events, chunkCount);
    const msg = seriesEqual(batch, inc);
    if (msg) fail(`追記等価性不一致 ${name} (${chunkCount}分割): ${msg}`);
  }
  cases++;
  const oneAtATime = feedInChunks(events, events.length);
  const msg2 = seriesEqual(batch, oneAtATime);
  if (msg2) fail(`追記等価性不一致 ${name} (1イベントずつ): ${msg2}`);
  console.log(`append-equivalence ok: ${name} (2/3/10分割 + 1イベントずつ、計${events.length}events)`);
}

// ===========================================================================
// 4. 二重取り込み: 同じ行を2度feedしても、加算レーン(dmg/proj)を含めて1度と同じ
//    (T-13-09。再接続でトレースの先頭から送り直された分を吸収できることの核心)
// ===========================================================================
for (const [name, fpath] of Object.entries(FIXTURES)) {
  const text = fs.readFileSync(fpath, 'utf8');
  const { events } = parseTrace(text);
  const once = series(events);
  const state = seriesState();
  seriesFeed(state, events);
  seriesFeed(state, events, { final: true }); // 同じ行をもう一度、最後に確定させる
  const twice = seriesLanes(state);
  cases++;
  const msg = seriesEqual(once, twice);
  if (msg) fail(`二重feed不一致 ${name}: ${msg}`);
  else console.log(`double-feed idempotent: ${name} (dmg/projを含め1度と同じ)`);
}

// ===========================================================================
// 4b. 空feedはsentinelを漏らさない: seriesFeed(state, [])(final無し)を、まだ一度も
//     events を渡していない状態で呼んでも、onG/air/embed の内部sentinel(NaN)が
//     seriesLanes の戻り値に残らない(Task 2 の appendLive([]) — 水槽を開いた直後、
//     まだ1行も来ていない状態で実際にこの形を通る。修正前は
//     JSON.stringify(onG)==='[null]' になっていた回帰)。
// ===========================================================================
{
  const state = seriesState();
  seriesFeed(state, []); // final を渡さない。events も空。
  const lanes = seriesLanes(state);
  cases++;
  const json = JSON.stringify(lanes.onG);
  if (json.includes('null')) fail(`空feed直後にonGへ内部sentinelが漏れている: ${json}`);
  cases++;
  if (lanes.onG.length !== 1 || lanes.onG[0] !== 0) fail(`空feed直後のonGは[0]のはずが: ${JSON.stringify(lanes.onG)}`);
  console.log('empty-feed sentinel leak check: ok');
}

// ===========================================================================
// 5. 実トレース27本: 変更前に保存したハッシュ表(.series-selftest-baseline.json)と
//    突き合わせる。無い機械では探した場所を出してskipする(合格したとは書かない)。
//    このセクションだけがskip可能——検査1(commit済み2本のgolden一致)は必須。
// ===========================================================================
function hashOf(obj) {
  return crypto.createHash('sha256').update(JSON.stringify(obj)).digest('hex');
}
function findTraces(dir) {
  const out = [];
  let entries;
  try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { return out; }
  for (const ent of entries) {
    const p = path.join(dir, ent.name);
    if (ent.isDirectory()) out.push(...findTraces(p));
    else if (ent.name.startsWith('arena-') && ent.name.endsWith('.jsonl')) out.push(p);
  }
  return out;
}
if (!fs.existsSync(BASELINE_PATH)) {
  console.log(`実トレース27本: baseline が見つからない(探した場所: ${BASELINE_PATH})。skip`);
  console.log('  (変更前のstats.mjsで series(parseTrace(text).events) を各トレースについて計算し、');
  console.log('   sha256(JSON.stringify(...)) を { "<run/からの相対パス>": "<hash>", ... } の形で');
  console.log('   run/sim/traces/.series-selftest-baseline.json へ保存すれば、次回以降ここが動く)');
} else {
  const baseline = JSON.parse(fs.readFileSync(BASELINE_PATH, 'utf8'));
  const found = findTraces(TRACES_ROOT).map((p) => path.relative(REPO_ROOT, p).replace(/\\/g, '/'));
  let matched = 0, mismatched = 0, skipped = 0;
  for (const rel of found) {
    const baseHash = baseline[rel];
    if (!baseHash) { skipped++; continue; }
    const abs = path.join(REPO_ROOT, rel);
    const text = fs.readFileSync(abs, 'utf8');
    const { events } = parseTrace(text);
    const out = series(events);
    const h = hashOf(out);
    cases++;
    if (h !== baseHash) { mismatched++; fail(`実トレース不一致: ${rel}`); }
    else matched++;
  }
  console.log(`実トレース27本: ${matched}件一致 / ${mismatched}件不一致 / ${skipped}件baseline無しでskip (ディスク上で見つかった${found.length}本)`);
  if (found.length > 0 && matched === 0 && mismatched === 0) {
    fail('実トレースは見つかったのにbaselineと1件も突き合わせられなかった(baselineのキー形式がずれている可能性)');
  }
}

// ===========================================================================
console.log(`\ncases: ${cases} (need >= 20)`);
console.log(`failures: ${failures}`);
if (cases < 20) fail(`only ${cases} cases ran (need >= 20) — a selftest that can pass on too few cases is not a selftest`);

if (failures > 0) {
  console.error(`series-selftest: ${failures} failure(s)`);
  process.exit(1);
}
console.log('series-selftest: OK');
process.exit(0);
