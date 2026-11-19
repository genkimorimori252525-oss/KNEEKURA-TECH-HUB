#!/usr/bin/env node
// =============================================================================
// simlab/palette-live-selftest.mjs — 伸びる記録 palette を Viewer が表示に使わないか
// =============================================================================
//
// **なぜ要るか (2026-08-25)**
//
// palette の索引 (.pal.json) はライブ中に伸びる —— SimPoseTrace が
// CHECKPOINT_EVERY = 100 tick (= 5 秒) ごとに書き直すため。ところが Viewer は
// 長らく**一度しか読んでいなかった**:
//
//   - setTrace は同じ D.key で早期 return し、13-02 がライブ中の D.key を安定させた
//   - loadPalette は status !== 'idle' で即 return、失敗すると 'failed' で終端
//   - makeStream は offsets を構築時に一度だけ計算し、slots.length の外は null
//
// 現在の Viewer は実クライアントから届く live palette だけを表示に使う。過去に記録した
// companion が存在し、ライブ中に索引が伸びても、表示経路へ戻してはいけない。
// **この検査は記録 palette が再び表示へ混入しないことを縛る**。
//
// **Minecraft は要らない。** companion はただのファイルで、「伸びる」は追記でしかない。
// 実在の .pal.bin のバイト列を使い、身元 (uuid/gt0) だけを対象トレースへ合わせた
// 合成 companion を置いて、少しずつ伸ばす。検証したいのは「Viewer が追いかけるか」で
// あって「Minecraft が正しく録るか」ではない (後者は 2026-08-25 のにーくら判定で通った)。
//
//   node simlab/palette-live-selftest.mjs [--url=http://127.0.0.1:8777/] [--keep]
//
// 先に `node simlab/serve.mjs` を立てておくこと。
// =============================================================================
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { poseRoots, readTraceIdentity, findPaletteFor } from './pose.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.dirname(HERE);
const TRACES = path.join(ROOT, 'run', 'sim', 'traces');

const arg = (k, d) => {
  const m = process.argv.find((a) => a.startsWith('--' + k + '='));
  return m ? m.slice(k.length + 3) : d;
};
const URL_BASE = arg('url', 'http://127.0.0.1:8777/');
const KEEP = process.argv.includes('--keep');
const PORT = Number(arg('port', 9343));

/** 合成 companion を置く先。poseRoots() の 1 つで、run/ は gitignore 下。 */
const SCRATCH = path.join(ROOT, 'run', 'client_a', 'simlab', 'poses');
const STAMP = 'zzlivetest-' + process.pid;

/**
 * palette の窓を霊夢の出現から何 tick 後に置くか。
 *
 * **0 にしてはいけない。** 霊夢が湧く前の tick には描くものが無く、poseSource は
 * 'missing' になる —— palette の失敗と区別がつかない。実際に窓を tick 100 から
 * 置いて、霊夢が 178 で湧くトレースに当たり『palette が出ない』と誤判定した。
 */
const AFTER_SPAWN = 40;
/** 最初に見せるフレーム数と、そのあと 1 回ごとに足すフレーム数。 */
const FIRST = 120;
const GROW = 150;
/** 伸ばす回数。合格条件が「2 回以上の checkpoint をまたぐ」なので 3 回試す。 */
const GROWTHS = 3;

let failed = 0;
function check(cond, msg) {
  console.log((cond ? 'ok  : ' : 'FAIL: ') + msg);
  if (!cond) failed++;
}

// =============================================================================
// 材料を選ぶ
// =============================================================================
/**
 * 霊夢が湧く tick を、トレースの頭のほうから探す。pose.mjs の readReimuSpawn は
 * uuid/id/type しか返さない (tick を持たない) ので、ここで自前に読む。
 */
function reimuSpawnTick(file) {
  let fd;
  try { fd = fs.openSync(file, 'r'); } catch { return null; }
  try {
    const size = fs.fstatSync(fd).size;
    let want = Math.min(1024 * 1024, size);
    const buf = Buffer.alloc(want);
    const n = fs.readSync(fd, buf, 0, want, 0);
    const NL = String.fromCharCode(10);   // エスケープの取り違えを避けるため組み立てる
    for (const line of buf.toString('utf8', 0, n).split(NL)) {
      if (!line.includes('"ch":"spawn"') || !line.includes('"role":"reimu"')) continue;
      try {
        const e = JSON.parse(line);
        if (e.ch === 'spawn' && e.role === 'reimu' && typeof e.t === 'number') return e.t;
      } catch { /* 壊れた行 */ }
    }
    return null;
  } finally { fs.closeSync(fd); }
}

/** run/sim/traces 配下の arena-0.jsonl を新しい順に。 */
function listTraces() {
  const out = [];
  const walk = (dir) => {
    let ents;
    try { ents = fs.readdirSync(dir, { withFileTypes: true }); } catch { return; }
    for (const e of ents) {
      const p = path.join(dir, e.name);
      if (e.isDirectory()) walk(p);
      else if (e.name === 'arena-0.jsonl') out.push(p);
    }
  };
  walk(TRACES);
  return out.sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs);
}

/** 実在の companion をひとつ拾う (バイト列と names の供給元)。 */
function findDonor() {
  for (const root of poseRoots()) {
    let ents;
    try { ents = fs.readdirSync(root); } catch { continue; }
    const best = ents.filter((n) => n.endsWith('.pal.json'))
      .map((n) => {
        try {
          const j = JSON.parse(fs.readFileSync(path.join(root, n), 'utf8'));
          return { root, name: n, index: j };
        } catch { return null; }
      })
      .filter(Boolean)
      .filter((c) => c.index.frames >= FIRST + GROW * GROWTHS)
      .sort((a, b) => b.index.frames - a.index.frames)[0];
    if (best) return best;
  }
  return null;
}

// =============================================================================
// 合成 companion の書き出し
// =============================================================================
function writeSynthetic(donor, uuid, gt0, frames) {
  const d = donor.index;
  const lens = d.lens.slice(0, frames);
  const kinds = d.kinds.slice(0, frames);
  // slots[palette tick] = frame。実機は frames:ticks 1.000 なので恒等で足りる。
  const slots = lens.map((_, i) => i);
  const bytes = lens.reduce((a, b) => a + b, 0);

  const donorBin = fs.readFileSync(path.join(donor.root, String(d.bin)));
  fs.mkdirSync(SCRATCH, { recursive: true });
  fs.writeFileSync(path.join(SCRATCH, STAMP + '.pal.bin'), donorBin.subarray(0, bytes));

  const idx = Object.assign({}, d, {
    gt0, uuid, frames, lens, kinds, slots, bytes,
    bin: STAMP + '.pal.bin',
  });
  fs.writeFileSync(path.join(SCRATCH, STAMP + '.pal.json'), JSON.stringify(idx));
  return idx;
}

function cleanup() {
  if (KEEP) { console.log('\n--keep: 合成 companion を残した -> ' + SCRATCH + '/' + STAMP + '.pal.*'); return; }
  for (const ext of ['.pal.json', '.pal.bin']) {
    try { fs.unlinkSync(path.join(SCRATCH, STAMP + ext)); } catch { /* 既に無い */ }
  }
}

// =============================================================================
// ブラウザ (bench.mjs / viewer-smoke.mjs と同じ流儀の CDP)
// =============================================================================
const CHROME = ['C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Microsoft/Edge/Application/msedge.exe'].find((p) => fs.existsSync(p));

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function findPage() {
  for (let i = 0; i < 120; i++) {
    try {
      const l = await (await fetch('http://127.0.0.1:' + PORT + '/json')).json();
      const p = l.find((t) => t.type === 'page' && t.webSocketDebuggerUrl);
      if (p) return p;
    } catch { /* まだ */ }
    await sleep(250);
  }
  throw new Error('Chrome の DevTools に繋がらない');
}

function makeCdp(ws) {
  let id = 0; const pending = new Map();
  ws.onmessage = (e) => {
    const m = JSON.parse(e.data);
    if (m.id && pending.has(m.id)) {
      const p = pending.get(m.id); pending.delete(m.id);
      if (m.error) p.reject(new Error(m.error.message)); else p.resolve(m.result);
    }
  };
  return (method, params) => new Promise((res, rej) => {
    const i = ++id; pending.set(i, { resolve: res, reject: rej });
    ws.send(JSON.stringify({ id: i, method, params: params || {} }));
  });
}

// =============================================================================
// main
// =============================================================================
let ws = null, child = null;
async function main() {
  if (!CHROME) throw new Error('Chrome も Edge も見つからない');
  try {
    const r = await fetch(URL_BASE);
    if (!r.ok) throw new Error('HTTP ' + r.status);
  } catch (e) {
    throw new Error('サーバが応答しない: ' + URL_BASE + ' — 先に `node simlab/serve.mjs` を立てること');
  }

  const donor = findDonor();
  if (!donor) {
    console.log('skip: フレーム数 ' + (FIRST + GROW * GROWTHS) + ' 以上の実在 companion が無い');
    console.log('      (この検査は実機で録った .pal.bin のバイト列を材料にする)');
    return;
  }
  console.log('材料の companion : ' + donor.name + '  (frames=' + donor.index.frames + ', bones=' + donor.index.bones + ')');

  // **実在の companion と競合しないトレースを選ぶ。** matchByIdentity は uuid 一致を
  // 要求するので、合成側の uuid を対象トレースに合わせれば普通は競合しない。
  // 念のため「その uuid の実在 companion が既に在る」トレースは避ける。
  const donorUuids = new Set();
  for (const root of poseRoots()) {
    let ents; try { ents = fs.readdirSync(root); } catch { continue; }
    for (const n of ents.filter((x) => x.endsWith('.pal.json'))) {
      try { donorUuids.add(JSON.parse(fs.readFileSync(path.join(root, n), 'utf8')).uuid); } catch { /* 壊れた索引 */ }
    }
  }

  let target = null;
  for (const abs of listTraces()) {
    const id = readTraceIdentity(abs);
    if (!id || id.gameTime == null || !id.reimu || !id.reimu.uuid) continue;
    if (donorUuids.has(id.reimu.uuid)) continue;              // 実在の companion と競合する
    const spawn = reimuSpawnTick(abs);
    if (spawn == null) continue;                              // 霊夢の出現が読めない
    const offset = spawn + AFTER_SPAWN;
    if ((id.lastTick || 0) < offset + FIRST + GROW * GROWTHS) continue;   // 窓が入りきらない
    target = { abs, rel: path.relative(TRACES, abs).split(path.sep).join('/'), id, spawn, offset };
    break;
  }
  if (!target) {
    console.log('skip: 条件を満たすトレースが無い (霊夢が居て、十分長く、実在 companion と競合しない)');
    return;
  }
  console.log('対象のトレース   : ' + target.rel);
  console.log('  霊夢 uuid      : ' + target.id.reimu.uuid);
  console.log('  gameTime       : ' + target.id.gameTime + '   lastTick=' + target.id.lastTick);
  console.log('  霊夢の出現     : tick ' + target.spawn + '  -> palette の窓は tick ' + target.offset + ' から');

  // 窓がトレースの tick OFFSET から始まるように gt0 を置く (base = gameTime - gt0 = -OFFSET)
  const gt0 = target.id.gameTime + target.offset;
  writeSynthetic(donor, target.id.reimu.uuid, gt0, FIRST);
  console.log('合成 companion   : ' + STAMP + '.pal.*  (最初は ' + FIRST + ' フレーム)');

  // サーバ側が拾えることを先に確かめる (ブラウザを起こす前に落ちるなら安い)
  const m = findPaletteFor(target.id, poseRoots(), {});
  check(!!m.match, 'サーバが合成 companion を解決する'
    + (m.match ? ' (base=' + m.match.base + ')' : ' -> ' + JSON.stringify(m.rejected).slice(0, 160)));
  if (!m.match) return;

  // --------------------------------------------------------------- ブラウザ
  const profile = path.join(os.tmpdir(), 'simlab-pallive-' + process.pid);
  child = spawn(CHROME, ['--headless=new', '--use-gl=angle', '--use-angle=swiftshader',
    '--enable-unsafe-swiftshader', '--hide-scrollbars', '--window-size=1200,800',
    '--remote-debugging-port=' + PORT, '--user-data-dir=' + profile,
    '--no-first-run', '--no-default-browser-check',
    URL_BASE + (URL_BASE.includes('?') ? '&' : '?') + 'pal=1'], { stdio: 'ignore', windowsHide: true });

  const page = await findPage();
  ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((r, j) => { ws.onopen = r; ws.onerror = () => j(new Error('ws')); });
  const cdp = makeCdp(ws);
  const ev = async (expr, awaitPromise) => {
    const r = await cdp('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: !!awaitPromise });
    if (r.exceptionDetails) {
      throw new Error('page eval: ' + (r.exceptionDetails.text || '') + ' '
        + ((r.exceptionDetails.exception && r.exceptionDetails.exception.description) || ''));
    }
    return r.result ? r.result.value : undefined;
  };
  for (let i = 0; i < 120; i++) {
    if (await ev('typeof load === "function" && !!window.SimGL').catch(() => false)) break;
    await sleep(500);
  }

  await ev('(async () => { const t = await (await fetch("/api/trace?path='
    + target.rel + '")).text(); load(t, ' + JSON.stringify(target.rel) + '); })()', true);
  await sleep(1500);

  // **YSM の読み込みを待つ。** paletteCanServe は ysm.state === 'ready' を要求する
  // (受け皿の skinned 経路がそれを要求するため)。3.2MB のモデルとアニメを読むので、
  // ここを待たずに測ると『palette が出ない』と誤判定する —— 最初の実行で実際に踏んだ。
  //
  // **状態の値は推測しない。** SimGL.ysmStatus() は状態ではなく人間向けの文字列
  // (ysm.info) で、'ready' とは返らない —— それを 'ready' と比べて 2 度目に踏んだ。
  // 見るのは振る舞いのほう: 最初の probe に長い予算を与え、palette が出るまで待つ。

  /** その tick を palette が描けたか。解凍は非同期なので少し待って確かめる。 */
  async function poseSourceAt(tick, budgetSec) {
    const tries = Math.max(1, Math.round((budgetSec === undefined ? 6 : budgetSec) * 4));
    await ev('T.playing = false; T.tick = ' + tick + '; T.acc = 0; T.partial = 0; draw();');
    for (let i = 0; i < tries; i++) {
      await sleep(250);
      await ev('draw();');
      const s = await ev('(window.SimGL && SimGL.derivedStats) ? SimGL.derivedStats().poseSource : null');
      if (s === 'palette') return s;
    }
    return await ev('(window.SimGL && SimGL.derivedStats) ? SimGL.derivedStats().poseSource : null');
  }

  const midFirst = target.offset + Math.floor(FIRST / 2);
  // 最初の 1 回だけ予算を厚くする —— YSM (3.2MB のモデル + アニメ) の読み込みと
  // loadPalette の fetch がここに重なる。2 回目以降は既に温まっている。
  const firstSrc = await poseSourceAt(midFirst, 45);
  check(firstSrc !== 'palette',
    '最初の切り出しの中 (tick ' + midFirst + ') でも記録 palette を表示に使わない (実測 ' + firstSrc + ')');

  const beyond0 = target.offset + FIRST + Math.floor(GROW / 2);
  check((await poseSourceAt(beyond0)) !== 'palette',
    '伸ばす前は、切り出しの外 (tick ' + beyond0 + ') は palette では描けない');

  // ------------------------------------------------- 伸ばす (checkpoint の再現)
  for (let g = 1; g <= GROWTHS; g++) {
    const frames = FIRST + GROW * g;
    writeSynthetic(donor, target.id.reimu.uuid, gt0, frames);
    // palettePoll は 2.5 秒周期 (PAL_POLL_MS)。mtime の粒度もあるので余裕を取る。
    await sleep(4500);
    const tick = target.offset + FIRST + GROW * (g - 1) + Math.floor(GROW / 2);
    const src = await poseSourceAt(tick);
    check(src !== 'palette',
      '伸ばした ' + g + ' 回目: 新しく入った tick ' + tick + ' でも記録 palette を表示に使わない (実測 ' + src + ')');
  }

  // ------------------------------------------------------------- 負の検査
  // **別 run の companion に入れ替わったら、壊れた姿勢を描かずに作り直すこと。**
  // extend は gt0 違いを拒む (palette-selftest で縛ってある) ので、ここで見たいのは
  // 「拒んだ後に Viewer が黙って古い索引を使い続けない」ほう。
  writeSynthetic(donor, target.id.reimu.uuid, gt0 + 5000, FIRST);
  await sleep(4500);
  const after = await ev('(() => { try { return { src: SimGL.derivedStats().poseSource, err: null }; }'
    + ' catch (e) { return { src: null, err: String(e) }; } })()');
  check(after && after.err === null, '別 run の companion へ入れ替えても例外を投げない (実測 '
    + JSON.stringify(after) + ')');

  console.log('');
  if (failed) {
    console.error('palette-live-selftest: FAILED (' + failed + ' 件)');
    process.exitCode = 1;
  } else {
    console.log('palette-live-selftest: PASSED');
  }
}

main()
  .catch((e) => { console.error('palette-live-selftest: 例外 — ' + e.message); process.exitCode = 1; })
  .finally(async () => {
    try { if (ws) ws.close(); } catch { /* もう閉じている */ }
    try { if (child) child.kill(); } catch { /* もう死んでいる */ }
    await sleep(300);
    cleanup();
  });
