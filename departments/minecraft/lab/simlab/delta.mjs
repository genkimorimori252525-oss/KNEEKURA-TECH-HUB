#!/usr/bin/env node
// =============================================================================
// delta.mjs — 「前 tick と同じ行は書かない」のJS側の双子 (13-04 Task 1)
// =============================================================================
//
// 使い方:
//   node simlab/delta.mjs <入力.jsonl> [出力.jsonl]   既存トレースをデルタ化する。
//                                                      出力を省くと統計だけ表示する。
//   node simlab/delta.mjs --selftest                  golden一致・疎密一致・id再利用の
//                                                      3つの不変条件を検査する。
//
// 規則は src/main/java/.../sim/trace/SimDelta.java と**同一**
// (simlab/fixtures/delta-gate.golden.json が両実装の唯一の共通の物差し):
//   - 対象チャンネルは pos/phys/anim だけ。他は無条件で素通しする。
//   - 書くのは: 初めて見た(ch,id) / 前回書いた内容と違う / 前回書いてから
//     keyframeTicks(既定100)tick以上経った、のいずれか。
//   - gone を見たら、その id の台帳を忘れる (id再利用対策、T-13-12)。
//
// 「前と同じ行」の判定そのものは**ここで再実装しない**。simlab/viewer/store.js の
// rowIsRedundant を node:vm で読んで使う (JS側に2つ目の定義を作らない)。
//
// 依存は Node 標準ライブラリのみ。

import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
import { parseTrace } from './stats.mjs';
import { analyze } from './analyze.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const STORE_JS = path.join(HERE, 'viewer', 'store.js');

// SimDelta.KEYFRAME_TICKS (Java側)と同じ値。両言語に別々に持つしかない定数
// (JSからJavaのstatic finalは読めない)。schema.jsonのmeta.keyframeもこれと揃える(Task 2)。
const DEFAULT_KEYFRAME_TICKS = 100;

// 対象はpos/phys/animだけ。vis/ai/dmg/sound/proj/log/spawn/gone/meta/endは一切触らない
// (対象外チャンネルはdeltaEncode内で無条件に素通しする)。
const TARGET_CHANNELS = new Set(['pos', 'phys', 'anim']);

// -----------------------------------------------------------------------------
// store.js のロード (node:vm、pick-selftest.mjs / store-selftest.mjs と同じ流儀)
// -----------------------------------------------------------------------------

let _probe = null;
function getStoreProbe() {
  if (_probe) return _probe;
  const src = fs.readFileSync(STORE_JS, 'utf8');
  const sandbox = {};
  vm.createContext(sandbox);
  vm.runInContext(src, sandbox, { filename: STORE_JS });
  if (!sandbox.SimStore) throw new Error('viewer/store.js が globalThis.SimStore を作らなかった');
  // rowIsRedundantはcreate()が返すインスタンスのメソッド(トップレベルSimStoreには無い)。
  _probe = sandbox.SimStore.create();
  return _probe;
}

// -----------------------------------------------------------------------------
// ゲート — SimDelta.shouldWrite/forget のJS側の対応物
// -----------------------------------------------------------------------------

/**
 * (ch,id)ごとの「前回書いた行」台帳を持つゲートを作る。
 * 「同じ行か」の判定はrowIsRedundantに委譲する(2つ目の定義を作らない)。
 * keyframe間隔の判定と台帳の持ち回しだけがここの責務 —— SimDelta.javaと対称。
 */
function createGate(keyframeTicks) {
  const probe = getStoreProbe();
  const ledger = new Map(); // id -> Map(ch -> {row, tick})
  let written = 0, skipped = 0, keyframes = 0;

  function shouldWrite(ch, id, tick, row) {
    if (ch == null || row == null) { written++; return true; }
    let byCh = ledger.get(id);
    if (!byCh) { byCh = new Map(); ledger.set(id, byCh); }
    const prev = byCh.get(ch);
    if (!prev) {
      byCh.set(ch, { row, tick });
      written++;
      return true;
    }
    if (!probe.rowIsRedundant(prev.row, row)) {
      byCh.set(ch, { row, tick });
      written++;
      return true;
    }
    if (tick - prev.tick >= keyframeTicks) {
      // 内容は同じだが間隔が空きすぎたので keyframe として書き直す。
      byCh.set(ch, { row: prev.row, tick });
      written++;
      keyframes++;
      return true;
    }
    skipped++;
    return false;
  }

  function forget(id) {
    ledger.delete(id);
  }

  return {
    shouldWrite, forget,
    get written() { return written; },
    get skipped() { return skipped; },
    get keyframes() { return keyframes; },
  };
}

// -----------------------------------------------------------------------------
// deltaEncode — 行の配列を受け、書くべき行だけを返す
// -----------------------------------------------------------------------------

/**
 * @param {string[]} lines JSONLの行の配列(改行を含まない、1行=1イベント)
 * @param {{keyframeTicks?: number}} opts
 * @returns {{lines: string[], written: number, skipped: number, keyframes: number, total: number}}
 */
export function deltaEncode(lines, opts) {
  opts = opts || {};
  const keyframeTicks = opts.keyframeTicks != null ? opts.keyframeTicks : DEFAULT_KEYFRAME_TICKS;
  const gate = createGate(keyframeTicks);

  // 1周目: 各(ch,id)が「この入力の中で最後に現れる」添字を覚える。**ここがオフライン
  // 一括圧縮(このCLI)だけの特典** —— ライブ書き込み(ジャー側SimDelta/SimProbe)は
  // 未来を知らないので同じことはできない。
  //
  // これが無いと: 録画が正常終了(end有効)でも異常終了(recording crash、end無し)でも、
  // 末尾で冗長行が続いたままトレースが終わる場合に「最後に観測した行のtick」が
  // dense版より早まる。読み手側(simlab/stats.mjsのboundPhysReimu、simlab/analyze.mjsの
  // phys閉じ処理)はこの「最後に観測したtick」を前方フィルの境界に使うため、
  // dense/delta間でこの境界がずれると series()/analyze() の出力が食い違う
  // (実測: run/sim/traces/tank/20260820/20260821-031644(end無し、録画が
  // サーバ強制終了で途中に切れたケース)を含む27本の実トレース照合で検出。
  // gap=77tickはKEYFRAME_TICKS=100未満なのでkeyframeが発火せず、「前回書いてから
  // 100tick以上」という通常のゲート条件だけでは救えなかった)。
  //
  // 対策: 各(ch,id)の**最後の1行**は、ゲートが「冗長だから省略してよい」と判定しても
  // 強制的に書く。これで dense/delta 両方の「最後に観測したtick」が常に一致する
  // ——ライブ書き込み側は録画終了時(SimArena.finish())に別の手当てが要る(このCLIの
  // 圧縮対象になるのはあくまで**既に書き終わったファイル**なので、この特典が使える)。
  const parsed = [];
  const lastIndexOf = new Map(); // "ch#id" -> parsed配列内の添字
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (line == null || !String(line).trim()) { parsed.push(null); continue; }
    let e;
    try {
      e = JSON.parse(line);
    } catch {
      parsed.push(undefined); // 壊れた行の印(素通しする)
      continue;
    }
    parsed.push(e);
    if (TARGET_CHANNELS.has(e.ch) && typeof e.id === 'number') {
      lastIndexOf.set(e.ch + '#' + e.id, i);
    }
  }

  const out = [];
  let total = 0;
  let written = 0, skipped = 0;
  for (let i = 0; i < lines.length; i++) {
    const e = parsed[i];
    if (e === null) continue; // 空行
    total++;
    if (e === undefined) {
      out.push(lines[i]); // 壊れた行は判断できないので落とさず素通しする
      continue;
    }
    if (e.ch === 'gone') {
      // id再利用対策(T-13-12): goneを見たらその id の台帳を忘れる。
      gate.forget(e.id);
      out.push(lines[i]);
      continue;
    }
    if (!TARGET_CHANNELS.has(e.ch) || typeof e.id !== 'number') {
      out.push(lines[i]);
      continue;
    }
    const gateWrite = gate.shouldWrite(e.ch, e.id, e.t | 0, e);
    const isLastOccurrence = lastIndexOf.get(e.ch + '#' + e.id) === i;
    if (gateWrite || isLastOccurrence) {
      out.push(lines[i]);
      written++;
    } else {
      skipped++;
    }
  }
  return { lines: out, written, skipped, keyframes: gate.keyframes, total };
}

// -----------------------------------------------------------------------------
// --selftest — 不変条件を3つ検査する
// -----------------------------------------------------------------------------

function findArenaJsonl(root) {
  const out = [];
  const walk = (p) => {
    let st;
    try { st = fs.statSync(p); } catch { return; }
    if (st.isDirectory()) {
      for (const f of fs.readdirSync(p)) walk(path.join(p, f));
    } else if (path.basename(p).startsWith('arena-') && p.endsWith('.jsonl')) {
      out.push(p);
    }
  };
  walk(root);
  return out.sort();
}

/** dense版とdeltaEncode版で analyze() の --json 相当が byte一致すること。 */
function checkDenseDeltaAnalyzeEquivalence(file, keyframeTicks, fail) {
  const text = fs.readFileSync(file, 'utf8');
  const lines = text.split('\n');
  let denseJson, deltaJson;
  try {
    denseJson = JSON.stringify(analyze(parseTrace(text)));
  } catch (e) {
    fail(`${file}: dense版のanalyze()が例外: ${e.message}`);
    return false;
  }
  const { lines: deltaLines } = deltaEncode(lines, { keyframeTicks });
  try {
    deltaJson = JSON.stringify(analyze(parseTrace(deltaLines.join('\n'))));
  } catch (e) {
    fail(`${file}: delta版のanalyze()が例外: ${e.message}`);
    return false;
  }
  if (denseJson !== deltaJson) {
    fail(`${file}: analyze()の出力がdense版とdelta版で食い違う(byte不一致)`);
    return false;
  }
  return true;
}

/** id再利用(T-13-12): goneした id が同じ番号で戻ってきたとき、前の値を引き継がないこと。 */
function checkIdReuseDoesNotInheritSuppressedValue(fail) {
  const lines = [
    JSON.stringify({ t: 0, ch: 'spawn', id: 7, role: 'projectile', type: 'x' }),
    JSON.stringify({ t: 0, ch: 'pos', id: 7, x: 0, y: 64, z: 0 }),
    JSON.stringify({ t: 1, ch: 'pos', id: 7, x: 0, y: 64, z: 0 }), // 冗長 -> skipされるはず
    JSON.stringify({ t: 2, ch: 'gone', id: 7, reason: 'removed' }),
    JSON.stringify({ t: 3, ch: 'spawn', id: 7, role: 'projectile', type: 'y' }), // id再利用
    JSON.stringify({ t: 3, ch: 'pos', id: 7, x: 0, y: 64, z: 0 }), // 値は前と同じでも再利用後の初回は書くべき
  ];
  const { lines: out } = deltaEncode(lines, { keyframeTicks: 100 });
  const posTicks = out.map((l) => JSON.parse(l)).filter((e) => e.ch === 'pos').map((e) => e.t);
  if (posTicks.length !== 2 || posTicks[0] !== 0 || posTicks[1] !== 3) {
    fail(`id再利用: 残るべきpos行のtickは[0,3]のはずが[${posTicks.join(',')}] `
      + '(t=1は冗長で落ち、gone後に再利用されたt=3の初回行は残るべき)');
    return false;
  }
  return true;
}

function selftest() {
  let failures = 0;
  let checks = 0;
  const fail = (msg) => { failures++; console.error('SELFTEST FAIL: ' + msg); };

  // --- (a) golden一致 ---
  const goldenPath = path.join(HERE, 'fixtures', 'delta-gate.golden.json');
  let goldenCaseCount = 0;
  if (!fs.existsSync(goldenPath)) {
    fail('delta-gate.golden.json が無い: ' + goldenPath);
  } else {
    const golden = JSON.parse(fs.readFileSync(goldenPath, 'utf8'));
    const keyframeTicks = golden.keyframeTicks != null ? golden.keyframeTicks : DEFAULT_KEYFRAME_TICKS;
    const gcases = Array.isArray(golden) ? golden : golden.cases;
    if (!Array.isArray(gcases) || gcases.length < 12) {
      fail(`golden のケースが12件未満: ${gcases && gcases.length}`);
    } else {
      goldenCaseCount = gcases.length;
      const gate = createGate(keyframeTicks);
      const seenKinds = new Set();
      for (let i = 0; i < gcases.length; i++) {
        const c = gcases[i];
        checks++;
        seenKinds.add(c.kind || '');
        if (c.forget) gate.forget(c.id);
        const actual = gate.shouldWrite(c.ch, c.id, c.tick, c.body);
        if (actual !== c.expect) {
          fail(`golden[${i}] (${c.kind || ''}) ch=${c.ch} id=${c.id} tick=${c.tick}: `
            + `期待 ${c.expect}, 実際 ${actual}`);
        }
      }
      const requiredKinds = ['初回', '同一', '差分', 'keyframe直前', 'keyframeちょうど',
        'forget後', '対象外チャンネル', '丸め違い'];
      for (const k of requiredKinds) {
        if (!seenKinds.has(k)) fail(`golden に kind="${k}" のケースが無い(8種類の網羅漏れ)`);
      }
    }
  }

  // --- (b) 疎密一致: 2本のcommitted fixtureは必須。実トレース27本は在れば追加で検査する ---
  const committed = [
    path.join(HERE, 'fixtures', 'combat-60t.jsonl'),
    path.join(HERE, 'fixtures', 'stairs-20260819-043053.ai-anim.jsonl'),
  ];
  let checkedTraces = 0;
  for (const f of committed) {
    checks++;
    if (!fs.existsSync(f)) {
      fail('committed fixture が無い: ' + f);
      continue;
    }
    if (checkDenseDeltaAnalyzeEquivalence(f, DEFAULT_KEYFRAME_TICKS, fail)) checkedTraces++;
  }
  const realRoot = path.join(HERE, '..', 'run', 'sim', 'traces');
  const realTraces = findArenaJsonl(realRoot);
  if (realTraces.length === 0) {
    console.log(`(skip) 実トレース27本: ${realRoot} に arena-*.jsonl が見つからない`);
  } else {
    for (const f of realTraces) {
      checks++;
      if (checkDenseDeltaAnalyzeEquivalence(f, DEFAULT_KEYFRAME_TICKS, fail)) checkedTraces++;
    }
  }

  // --- (c) id再利用 ---
  checks++;
  checkIdReuseDoesNotInheritSuppressedValue(fail);

  if (failures > 0) {
    console.error(`selftest FAILED (${failures} failures / ${checks} checks)`);
    process.exit(1);
  }
  console.log(`selftest OK — golden ${goldenCaseCount} cases, `
    + `dense/delta analyze()一致 ${checkedTraces} traces (実トレース含む: ${realTraces.length > 0}), `
    + 'id再利用 1 case');
}

// -----------------------------------------------------------------------------
// CLI
// -----------------------------------------------------------------------------

const isMain = process.argv[1] && import.meta.url.endsWith(path.basename(process.argv[1]));
if (isMain) {
  const args = process.argv.slice(2);
  if (args.includes('--selftest')) {
    selftest();
  } else if (args.includes('--help') || args.length === 0) {
    console.log('使い方:');
    console.log('  node simlab/delta.mjs <入力.jsonl> [出力.jsonl]   既存トレースをデルタ化する。'
      + '出力を省くと統計だけ表示する');
    console.log('  node simlab/delta.mjs --selftest                  golden一致・疎密一致・id再利用の'
      + '3つの不変条件を検査する');
    process.exit(args.length === 0 ? 1 : 0);
  } else {
    const input = args[0];
    const output = args[1];
    if (!fs.existsSync(input)) {
      console.error(`入力が無い: ${input}`);
      process.exit(1);
    }
    const text = fs.readFileSync(input, 'utf8');
    const lines = text.split('\n');
    const result = deltaEncode(lines, {});
    if (output) {
      fs.writeFileSync(output, result.lines.length ? result.lines.join('\n') + '\n' : '');
    }
    const pct = (n, d) => (d > 0 ? ((100 * n) / d).toFixed(1) : '0.0');
    console.log(`${input}: ${result.total}行 -> written ${result.written} / skipped ${result.skipped} `
      + `(うち keyframe ${result.keyframes}) — 削減 ${pct(result.skipped, result.total)}%`
      + (output ? ` -> ${output}` : ' (出力なし、統計のみ)'));
  }
}
