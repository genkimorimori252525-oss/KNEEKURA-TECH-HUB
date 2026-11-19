#!/usr/bin/env node
// =============================================================================
// simlab/bench.mjs — 前後比較を再現可能にする計測ハーネス (13-01 Task 2)
// =============================================================================
//
// 使い方:
//   node simlab/bench.mjs [--url URL] [--trace PATH] [--help]
//
// 既定 URL: http://127.0.0.1:8777/ (先に `node simlab/serve.mjs` を立てておくこと)
// --trace PATH は run/sim/traces 配下の相対パス。省略時は既定の3本
// (fixtures/combat-60t.jsonl、stairs の45秒戦闘、tank の41.9MB放置)を使う。
//
// モードを続けて測る:
//   (1) 描画    — トレースを開き再生、3秒間の T.drawN 増分/3 が実効fps。前値17fpsと並べる。
//   (2) 取り込み — 旧来のライブの毎秒 load(全文) を模す(13-01/13-02当時の実装との比較用に
//                残してある。13-03以降のライブ経路はもう毎秒 load() を呼ばない)。
//                溜まった量(2.0/10.3/20.8/41.9MB)ごとにload() 1回の所要msを測り、
//                前値(209/926/2406/4173ms)と並べる。
//   (2b) 追記   — 13-03: ライブの毎秒処理が実際に呼ぶ appendLive(新着行だけ)の費用を、
//                溜まった量(2.0/10.3/20.8/41.9MB)ごとに測る。目標16ms未満、かつ
//                4水準すべて横ばい(履歴長に依存しない=CYCLE-05)であること。
//                続けて、同じ新着ぶんを2度appendLiveしても状態(changePoints/
//                frameAt().pos)が変わらないことも検査する(再接続で先頭から
//                送り直されても壊れないことの根拠)。
//   (3) 飛び込み — T.tick を無作為な20点へ動かして draw() を呼び、1回あたりのmsを出す。
//                疎構造化の代償(O(1)→O(log n))を隠さないための欄。
//
// なぜ --screenshot ではなく DevTools プロトコルなのか (shot.mjs と同じ理由):
//   Viewer は /api/live へ SSE を張りっぱなしにするので、ページは永遠に「読み込み完了」
//   にならない。chrome --screenshot は load を待つので返ってこない。CDP ならこちらの
//   好きな時点で触れる。
//
// なぜ atob だけで済ませないのか (13-01-PLAN.md の "newline trap" 注記と同種の罠):
//   fixtures/combat-60t.jsonl は run/sim/traces の外にあり /api/trace のパス制限
//   (run/sim/traces 配下限定、path.resolve+startsWith ガード) の対象外なので、CDP経由で
//   直接 load() する。atob() は Latin1 前提でUTF-8マルチバイトを壊しうるので、
//   Uint8Array + TextDecoder('utf-8') で確実に戻す。base64 payload 自体は改行を含まない
//   (base64アルファベットに \n は無い) ので、テンプレートリテラルの改行展開の罠は踏まない。
//
// WebGL について: ヘッドレスにGPUが無いので --use-angle=swiftshader でソフトウェア
// 描画させる。GLの費用はこれで過大に出る(下の出力先頭の断りを参照)。

import { spawn } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const TRACES_ROOT = path.join(ROOT, 'run', 'sim', 'traces');
const FIXTURE_PATH = path.join(ROOT, 'simlab', 'fixtures', 'combat-60t.jsonl');

const CHROME_CANDIDATES = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
];

// shot.mjs の 9333 とは別ポートにする(同時に両方走らせても衝突しないように、T-13-02)。
const PORT = 9334;

// =============================================================================
// CLI引数
// =============================================================================
function parseArgs(argv) {
  const a = { url: 'http://127.0.0.1:8777/', trace: null, help: false, gpu: false };
  // IN-02(code review 150d56a5): 値なしで --url/--trace が渡されると argv[++i] が
  // undefined になり、以前は a.url.endsWith('/') でスタックトレースだけの
  // 不親切な TypeError になっていた。値の有無を先に検査してエラーメッセージを出す。
  for (let i = 0; i < argv.length; i++) {
    const k = argv[i];
    if (k === '--help' || k === '-h') a.help = true;
    else if (k === '--url' || k === '--trace') {
      const v = argv[i + 1];
      if (v === undefined) { console.error(k + ' には値が必要 (--help を参照)'); process.exit(1); }
      if (k === '--url') a.url = v; else a.trace = v;
      i++;
    }
    else if (k === '--gpu') a.gpu = true;
  }
  if (!a.url.endsWith('/')) a.url += '/';
  return a;
}

function printHelp() {
  console.log(`simlab/bench.mjs — 前後比較を再現可能にする計測ハーネス (13-01)

使い方:
  node simlab/bench.mjs [--url URL] [--trace PATH] [--gpu] [--help]

  --url URL    Viewer サーバの URL (既定 http://127.0.0.1:8777/)。
               先に \`node simlab/serve.mjs\` を立てておくこと。
  --trace PATH run/sim/traces 配下の相対パス。(1)(3)の追加候補・(2)の対象を差し替える。
  --gpu        (1)描画を、既定のswiftshader(ソフトウェアラスタライザ)ではなく
               実GPUで測る。--headless=newを保ったままANGLE d3d11を指定して起動し、
               検出したレンダラ文字列(WEBGL_debug_renderer_infoのUNMASKED_RENDERER_WEBGL)
               を必ず印字する。それでもソフトウェアレンダラだった場合だけ、
               可視ウィンドウ(短時間・自動で閉じる)へ切り替えて再挑戦する。

モードを続けて測る(--gpuは(1)描画にのみ影響する):

  (1) 描画   — simlab/fixtures/combat-60t.jsonl と、実トレース
               stairs/20260814/20260820-153927/arena-0.jsonl(あれば --trace も追加)を
               それぞれ開いて3秒再生し、T.drawN の増分/3 を実効fpsとして出す。
               前値 17fps と並べて印字する。実際に使ったレンダラも必ず印字する。

  (2) 取り込み — 旧来のライブの毎秒 load(全文) を模す(13-01/13-02当時との比較用)。
               既定は tank/20260820/20260821-054755/arena-0.jsonl(41.9MB、gitignore下、
               無ければ --trace で差し替え)を2.0/10.3/20.8/41.9MB相当まで切り出し、
               load() 1回ずつの所要msを前値(209/926/2406/4173ms)と並べて出す。

  (2b) 追記  — 13-03: ライブの毎秒処理が実際に呼ぶ appendLive(新着行だけ)の費用を
               同じ4水準で測る。目標16ms未満・4水準とも横ばい(履歴長に依存しない)。
               続けて、同じ新着ぶんを2度appendLiveしても状態が変わらないことも検査する。

  (3) 飛び込み — 読み込み済みのトレースで T.tick を無作為な20点へ動かして draw() を呼び、
               1回あたりのmsを出す(平均/中央値/最大)。疎構造化の代償を隠さないための欄。

トレースが見つからないモード・トレースはその場でskipする(探した絶対パスを出す)。
skipは失敗ではないが、**全モードがskipされたときだけ終了コードを1にする**。
`);
}

// =============================================================================
// サーバ確認
// =============================================================================
async function serverUp(url) {
  try { await fetch(url); return true; } catch { return false; }
}

// =============================================================================
// Chrome + CDP (shot.mjs の起動オプション・findPage/cdp の型をそのまま写す)
// =============================================================================
function findChrome() {
  return CHROME_CANDIDATES.find((p) => fs.existsSync(p));
}

async function findPage(port) {
  for (let i = 0; i < 80; i++) {
    try {
      const r = await fetch('http://127.0.0.1:' + port + '/json');
      const list = await r.json();
      const page = list.find((t) => t.type === 'page' && t.webSocketDebuggerUrl);
      if (page) return page;
    } catch { /* まだ立ち上がっていない */ }
    await new Promise((r) => setTimeout(r, 250));
  }
  throw new Error('Chrome の DevTools に繋がらない');
}

function makeCdp(ws) {
  let msgId = 0;
  const pending = new Map();
  ws.onmessage = (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) {
      const p = pending.get(m.id);
      pending.delete(m.id);
      if (m.error) p.reject(new Error(m.error.message));
      else p.resolve(m.result);
    }
  };
  return function cdp(method, params) {
    const id = ++msgId;
    return new Promise((resolve, reject) => {
      pending.set(id, { resolve, reject });
      ws.send(JSON.stringify({ id, method, params: params || {} }));
    });
  };
}

async function evalPage(cdp, expression, awaitPromise) {
  const r = await cdp('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: !!awaitPromise });
  if (r.exceptionDetails) {
    const t = r.exceptionDetails.text || '';
    const desc = (r.exceptionDetails.exception && r.exceptionDetails.exception.description) || '';
    throw new Error('page eval failed: ' + t + ' ' + desc);
  }
  return r.result ? r.result.value : undefined;
}

/** url を開いた使い捨て Chrome を1つ立て、fn(cdp) を呼ぶ。終わったら必ず kill する
 *  (T-13-02: 127.0.0.1 のみ bind・使い捨てプロファイル・常駐させない)。 */
// swiftshaderを明示的に強制する既定の起動フラグ(ソフトウェアラスタライザ)。
const SWIFTSHADER_FLAGS = ['--enable-unsafe-swiftshader', '--use-gl=angle', '--use-angle=swiftshader'];
// --gpu: 実GPUを狙う。ANGLEのバックエンドをWindows上の実GPU経路(d3d11)へ明示する
// (実測: 何も指定しない既定でもこの機ではd3d11に落ちたが、Chromeのバージョンや機体に
// よって既定が変わりうるため、狙う経路を明示するほうが再現性が高い)。
const GPU_FLAGS = ['--use-gl=angle', '--use-angle=d3d11'];

// UNMASKED_RENDERER_WEBGL がこれらを含んでいたらソフトウェアラスタライザとみなす。
const SOFTWARE_RENDERER_MARKERS = ['swiftshader', 'llvmpipe', 'software rasterizer', 'microsoft basic render'];
function isSoftwareRenderer(rendererStr) {
  const s = String(rendererStr || '').toLowerCase();
  return SOFTWARE_RENDERER_MARKERS.some((m) => s.includes(m));
}

/** 実際に使われているWebGLレンダラを確かめる(UNMASKED_RENDERER_WEBGL)。
 *  「どのレンダラで測ったか」を実行結果から読み取れない状態を作らないための唯一の情報源。 */
async function detectRenderer(cdp) {
  const expr = `(function(){
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
    if (!gl) return {renderer:null, vendor:null, error:'no webgl context'};
    const ext = gl.getExtension('WEBGL_debug_renderer_info');
    return {
      renderer: ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER),
      vendor: ext ? gl.getParameter(ext.UNMASKED_VENDOR_WEBGL) : gl.getParameter(gl.VENDOR),
    };
  })()`;
  try { return await evalPage(cdp, expr); } catch (e) { return { renderer: null, vendor: null, error: e.message }; }
}

/** 1個のChromeを起動し、DevToolsに繋いでcdpハンドルを返す。呼び出し側が cleanup() を
 *  必ず呼ぶこと(finallyで)。使い捨てプロファイル・127.0.0.1のみbind(T-13-02)。 */
async function launchAndConnect(url, headless, glFlags) {
  const chrome = findChrome();
  if (!chrome) throw new Error('Chrome も Edge も見つからない');
  const profile = path.join(os.tmpdir(), 'simlab-bench-profile-' + process.pid + '-' + Date.now() + '-' + Math.random().toString(36).slice(2));
  const args = [
    ...(headless ? ['--headless=new'] : []),
    ...glFlags,
    '--hide-scrollbars',
    '--window-size=1200,800',
    '--remote-debugging-port=' + PORT,
    '--user-data-dir=' + profile,
    '--no-first-run',
    '--no-default-browser-check',
    url,
  ];
  const child = spawn(chrome, args, { stdio: 'ignore', windowsHide: headless });
  let ws = null;
  const cleanup = async () => {
    try { if (ws) ws.close(); } catch { /* もう閉じている */ }
    try { child.kill(); } catch { /* もう死んでいる */ }
    // 可視ウィンドウは閉じるまでにひと呼吸要ることがある — 短く待ってからプロファイルを消す。
    await new Promise((r) => setTimeout(r, 300));
    try { fs.rmSync(profile, { recursive: true, force: true }); } catch { /* Windowsのファイルロックで残ることがある。実害なし */ }
  };
  try {
    const page = await findPage(PORT);
    ws = new WebSocket(page.webSocketDebuggerUrl);
    await new Promise((res, rej) => {
      ws.onopen = res;
      ws.onerror = () => rej(new Error('DevTools の WebSocket に繋がらない'));
    });
    return { cdp: makeCdp(ws), cleanup };
  } catch (e) {
    await cleanup();
    throw e;
  }
}

/** url を開いたChromeでfn(cdp, rendererInfo)を呼ぶ。
 *  既定(gpu未指定)は今までどおりswiftshaderを強制する(headless、確実に軽い)。
 *  gpu:true のときは--headless=newを保ったまま実GPU(ANGLE d3d11)を狙い、検出した
 *  レンダラがソフトウェアラスタライザの特徴を持っていた場合だけ、可視ウィンドウへ
 *  切り替えて再挑戦する(にーくらのデスクトップに短時間だけウィンドウが出る。
 *  測定が終わればcleanup()がプロセスごと閉じる — 開けっぱなしにしない)。
 *  rendererInfoは常に検出して呼び出し側へ渡す・呼び出し側は必ず印字すること。 */
async function withChrome(url, fn, opts) {
  opts = opts || {};
  if (!opts.gpu) {
    const { cdp, cleanup } = await launchAndConnect(url, true, SWIFTSHADER_FLAGS);
    try {
      const renderer = await detectRenderer(cdp);
      return await fn(cdp, renderer);
    } finally {
      await cleanup();
    }
  }

  // --gpu: headless のまま実GPUを狙う
  let { cdp, cleanup } = await launchAndConnect(url, true, GPU_FLAGS);
  let renderer = await detectRenderer(cdp);
  if (renderer.renderer && !isSoftwareRenderer(renderer.renderer)) {
    console.log('  [renderer] ' + renderer.renderer + '  (headless)');
    try { return await fn(cdp, renderer); } finally { await cleanup(); }
  }
  console.log('  [renderer] headless では実GPUに届かなかった(' + JSON.stringify(renderer) + ') — 可視ウィンドウへ切り替える');
  await cleanup();

  // フォールバック: 可視ウィンドウ(短時間・測定後は自動で閉じる)
  ({ cdp, cleanup } = await launchAndConnect(url, false, GPU_FLAGS));
  renderer = await detectRenderer(cdp);
  console.log('  [renderer] ' + (renderer.renderer || JSON.stringify(renderer)) + '  (visible window)');
  try { return await fn(cdp, renderer); } finally { await cleanup(); }
}

// =============================================================================
// トレース本文をページへ渡す手段: run/sim/traces/.bench-tmp/ への一時ファイル書き出し
// + サーバの既存 /api/trace(?path=) 経由での fetch。
//
// なぜ base64 をJSソース文字列へ直接埋め込む方式を採らなかったか(最初はそれで書いて
// 実測して分かったこと): 41.9MBのトレースはbase64で~56MBになり、それを1個の
// Runtime.evaluate expression(=V8が構文解析するJSソース)に埋め込むと、その巨大な
// 文字列リテラルの構文解析自体に数秒〜十数秒かかり、しかも同一タブで連続実行すると
// GCの影響で非単調(小さいサイズより大きいサイズの方が速く見える逆転)なノイズが
// 乗った ——(2)取り込みの費用そのものではなく計測手段のオーバーヘッドを測ってしまう。
// run/(.gitignoreの29行目で無視されている)配下にサーバが既に安全に配信できる
// /api/trace(path.resolve+startsWith(TRACES)ガード付き)があるので、その上に乗る
// ほうが正しい。fixtures/combat-60t.jsonl は run/sim/traces の外にあるので、
// このヘルパで一時的に traces 配下へコピーしてから同じ経路で開く。
// =============================================================================
const BENCH_TMP_DIR = path.join(TRACES_ROOT, '.bench-tmp');

/** text を run/sim/traces/.bench-tmp/<name> へ書き、/api/trace が受け付ける相対パスを返す。 */
function writeTempTrace(text, name) {
  fs.mkdirSync(BENCH_TMP_DIR, { recursive: true });
  const safe = name.replace(/[^A-Za-z0-9._-]/g, '_');
  const abs = path.join(BENCH_TMP_DIR, safe);
  fs.writeFileSync(abs, text);
  const rel = path.relative(TRACES_ROOT, abs).split(path.sep).join('/');
  return { rel, abs };
}

function cleanupTempTrace(abs) {
  try { fs.rmSync(abs, { force: true }); } catch { /* 実害なし。.bench-tmp/ は gitignore 下 */ }
}

/** cond式(文字列)がtruthyを返すまでポーリングする。ページがまだ起動していない間は
 *  D/load 等への参照がReferenceErrorになるので、**ループの内側**でcatchする ——
 *  外側でcatchすると1回目の「まだ早い」失敗だけでリトライごと諦めてしまう
 *  (実測: fixture注入がload is not definedで即失敗する不具合の真因だった)。 */
async function waitForCondition(cdp, cond, timeoutMs) {
  const t0 = Date.now();
  while (Date.now() - t0 < timeoutMs) {
    try {
      const v = await evalPage(cdp, cond);
      if (v) return true;
    } catch { /* まだページ/スクリプトが起動していない。次のポーリングで再挑戦 */ }
    await new Promise((r) => setTimeout(r, 200));
  }
  return false;
}

/** load() 等のトップレベル関数が呼べる状態になった(スクリプト実行済み)ことを待つ。 */
async function waitForScriptsReady(cdp, timeoutMs) {
  return waitForCondition(cdp, 'typeof load === "function" && typeof D !== "undefined"', timeoutMs);
}

/** トレースが読み込まれた(D.nTicks>0)ことを待つ。 */
async function waitForLoaded(cdp, timeoutMs) {
  return waitForCondition(cdp, 'typeof D !== "undefined" && D.nTicks > 0', timeoutMs);
}

// =============================================================================
// (1) 描画: 実効fps
// =============================================================================
async function measureDrawFps(cdp) {
  const expr = `
(function(){
  return new Promise((resolve) => {
    T.tick = 0; T.playing = true; T.last = performance.now();
    const n0 = T.drawN || 0;
    const t0 = performance.now();
    // 短いトレース(例: 60tickのfixture)は3秒より先に末尾へ着いてplaybackが止まる ——
    // 止まったら先頭へ戻して再生を続け、測定窓いっぱい draw() を呼ばせ続ける。
    const watchdog = setInterval(() => {
      if (!T.playing) { T.tick = 0; T.playing = true; T.last = performance.now(); }
    }, 150);
    setTimeout(() => {
      clearInterval(watchdog);
      const n1 = T.drawN || 0;
      const elapsedSec = (performance.now() - t0) / 1000;
      // T-13-08(threat register, 13-02): walk/animTrackの常駐サイズを隠さない。
      // gl.jsが読み込めていない/derivedStatsが無い環境(2Dのみ等)ではnull。
      const derived = (window.SimGL && SimGL.derivedStats) ? SimGL.derivedStats() : null;
      resolve({ drawN0: n0, drawN1: n1, elapsedSec, drawMs: T.drawMs || null, maxTick: D.maxTick, nTicks: D.nTicks, derived });
    }, 3000);
  });
})()`;
  return await evalPage(cdp, expr, true);
}

// =============================================================================
// (2) 取り込み: 毎秒 load() の費用(溜まった量ごと)
// =============================================================================
const INGEST_TARGETS = [
  { label: '2.0MB', bytes: 2.0 * 1024 * 1024, baselineMs: 209 },
  { label: '10.3MB', bytes: 10.3 * 1024 * 1024, baselineMs: 926 },
  { label: '20.8MB', bytes: 20.8 * 1024 * 1024, baselineMs: 2406 },
  { label: '41.9MB', bytes: 41.9 * 1024 * 1024, baselineMs: 4173 },
];

/** lines(配列)の先頭から、累積バイト数が targetBytes に達する行までを切り出す。 */
function computePrefix(lines, targetBytes) {
  let acc = 0, idx = 0;
  for (; idx < lines.length; idx++) {
    acc += Buffer.byteLength(lines[idx], 'utf8') + 1; // +1 は結合時の'\n'
    if (acc >= targetBytes) { idx++; break; }
  }
  const capped = idx >= lines.length;
  const prefix = lines.slice(0, Math.min(idx, lines.length)).join('\n');
  return { prefix, capped, actualBytes: Buffer.byteLength(prefix, 'utf8') };
}

/** 1回の load() 呼び出しにかかった ms。ページ内の fetch() でサーバから取り、
 *  取得後だけを計測する(load()そのものの費用と、ネットワーク往復を混ぜない)。
 *  呼び出し側が cdp(=1ページ)を渡す —— **各水準は呼び出し側で新しいページを使うこと**
 *  (同じタブで4回連続 load() すると、前の呼び出しのゴミが次の測定へ GC 圧力として
 *  持ち越り、非単調な数字になる実害があった。実測: 同一タブ4連続だと 10.3MB が
 *  20.8MB より遅く出た — GC由来のノイズであって取り込み費用の実体ではない)。 */
async function measureIngestOne(cdp, relPath) {
  const expr = `
(async function(){
  const text = await (await fetch('/api/trace?path=' + encodeURIComponent(${JSON.stringify(relPath)}))).text();
  const t0 = performance.now();
  load(text, 'bench-ingest', {live:true});
  return performance.now() - t0;
})()`;
  return await evalPage(cdp, expr, true);
}

// =============================================================================
// (2b) 追記: ライブの毎秒 appendLive() の費用(溜まった量ごと、13-03/CYCLE-05)
// =============================================================================
// 13-01/13-02までの「毎秒 load(全文)」を測っていた(2)は、13-03でライブの毎秒処理が
// 「新着行だけの追記(appendLive)」に変わったので、もう毎秒の実処理を表していない。
// ここでは: prefix を load() で1回だけ読み込んで「これだけ溜まっている」状態を
// 下ごしらえし(計測しない)、その*後*で新着1秒ぶん(prefixの切れ目から次の約20tick
// ぶん、実データ由来)だけを appendLive() する費用を測る——CYCLE-05が閉じたかどうかは
// この数字が4水準とも履歴長に依存せず横ばいになることで示す。

/** prefixの切れ目(最後の行のtick)から、次の tickWindow tick ぶんの行を切り出す
 *  (「新着1秒ぶん」の実データ版。合成しない——実トレースの実際の行密度をそのまま使う)。 */
function computeTailByTicks(lines, prefixLineCount, tickWindow) {
  let boundaryTick = -1;
  for (let i = prefixLineCount - 1; i >= 0; i--) {
    try { const e = JSON.parse(lines[i]); if (typeof e.t === 'number') { boundaryTick = e.t; break; } } catch { /* skip broken line */ }
  }
  const tail = [];
  for (let i = prefixLineCount; i < lines.length; i++) {
    const line = lines[i];
    if (!line || !line.trim()) continue;
    let e; try { e = JSON.parse(line); } catch { continue; }
    if (typeof e.t !== 'number') continue;
    if (e.t > boundaryTick + tickWindow) break;
    tail.push(line);
  }
  return { tail, boundaryTick };
}

/** prefixRelPath(.bench-tmp/配下、/api/trace経由で取得)を1回だけload()で読み込んで
 *  (計測しない)「既に溜まっている」状態を作ってから、tailLines(新着1秒ぶん)だけを
 *  appendLive()する費用をms単位で返す。prefixはfetch()で取る——measureIngestOneと
 *  同じ理由(13-01 key-decision): 41.9MBをJSリテラルへ直接埋め込むとbase64換算~56MBの
 *  構文解析コストを測ってしまい、load()自体の費用と混ざる。 */
async function measureAppendLiveOne(cdp, prefixRelPath, tailLines) {
  const expr = `
(async function(){
  const prefixText = await (await fetch('/api/trace?path=' + encodeURIComponent(${JSON.stringify(prefixRelPath)}))).text();
  load(prefixText, 'bench-append', {live:true});   // 下ごしらえ(計測しない)
  const tail = ${JSON.stringify(tailLines)};
  // **1 回目と定常状態を分ける。** load() 直後の 1 回目には、溜まりすぎた分の
  // 初回 trim・DOM の作り直し・各種キャッシュの初期化という**一過性の費用**が乗る。
  // 本物のライブは毎秒同じことを繰り返しているので、CYCLE-05 が問うているのは定常状態のほう。
  // 2026-08-25: 1 回目だけを測っていたせいで、実際には横ばいなものを
  // 「履歴に依存して伸びている」と読み違えた (同じ tail を 3 回食わせる対照実験で反証)。
  const reps = [];
  for (let rep = 0; rep < 3; rep++) {
    const t0 = performance.now();
    appendLive(tail, {});
    reps.push(performance.now() - t0);
  }
  const first = reps[0];
  const sorted = reps.slice().sort(function (a, b) { return a - b; });
  const ms = sorted[Math.floor(sorted.length / 2)];   // 定常状態 = 中央値
  // **費用と一緒に「そのとき水槽に何が居たか」を持ち帰る。**
  // これが無いと、費用が伸びたときに「履歴が伸びたから」なのか
  // 「生きている entity が増えたから」なのかを分けられない ——
  // 2026-08-25 に実際に分けられず、履歴のせいだと読み違えかけた。
  let ents = null, storeTicks = null;
  try { ents = D.entities ? D.entities.size : null; } catch (e) { /* 無い版もある */ }
  try { storeTicks = D.store ? (D.store.maxTick - D.store.minTick + 1) : null; } catch (e) { /* 同上 */ }
  // **窓の切り出しを別に出す。** bench は prefix を load() してから 1 回だけ appendLive
  // するので、その 1 回に「溜まりすぎた分をまとめて捨てる初回 trim」が乗りうる。
  // 本物のライブは毎秒少しずつ捨てるので、混ぜたまま読むと費用を過大に見積もる ——
  // 「履歴に依存して伸びている」と言う前に、これを引いた値で言うこと。
  let trims = null, trimMs = null;
  try { trims = T.trims || 0; trimMs = T.trimMs || 0; } catch (e) { /* 無い版もある */ }
  // 取り込みと描画を分ける。appendLive は末尾で draw() を呼ぶので、
  // 全体の時間には描画が混ざっている。T.ingestMs は draw の直前で締めた値。
  let ingestMs = null;
  try { ingestMs = T.ingestMs; } catch (e) { /* 無い版もある */ }
  return { ms: ms, first: first, ents: ents, storeTicks: storeTicks, trims: trims, trimMs: trimMs, ingestMs: ingestMs };
})()`;
  return await evalPage(cdp, expr, true);
}

// =============================================================================
// (3) 飛び込み: 任意tickへのseek費用
// =============================================================================
async function measureScrub(cdp) {
  const expr = `
(function(){
  const n = 20;
  const out = [];
  for (let i = 0; i < n; i++) {
    const t = Math.floor(Math.random() * (D.maxTick + 1));
    const t0 = performance.now();
    T.tick = t; T.partial = 0; draw();
    out.push(performance.now() - t0);
  }
  return out;
})()`;
  return await evalPage(cdp, expr);
}

// =============================================================================
// main
// =============================================================================
async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) { printHelp(); process.exit(0); }

  // **実測をGPUの測定値だと装わない。** headless は swiftshader(ソフトウェアラスタライザ)
  // なので GL の費用は過大に出る。CPU側(取り込み費用)は実機と同オーダー。
  console.log('[注記] GL の費用はソフトウェアラスタライザ(swiftshader)で測っており、実GPUより過大に出る。CPU側(取り込み費用)は実機と同オーダー。');

  if (!(await serverUp(args.url))) {
    console.error('サーバが応答しない: ' + args.url);
    console.error('起動: node simlab/serve.mjs' + (args.url.includes(':8777') ? '' : '  (別ポートなら --port を指定)'));
    process.exit(1);
  }

  let anyRan = false;

  // ---- (1) 描画 ----
  console.log('\n=== (1) 描画: 実効fps (前値 17fps、3秒間の再生窓・末尾に着いたら先頭へ戻して継続)'
    + (args.gpu ? ' [--gpu: 実GPUを狙う]' : ' [swiftshader]') + ' ===');
  // fixture は run/sim/traces の外にあり /api/trace のパス制限の対象外なので、
  // .bench-tmp/(gitignore下)へ一時コピーしてから同じ ?trace= 経路で開く ——
  // 実トレースと同じ boot() 経由の読み込みにすることで、2本の測り方を揃える。
  let fixtureTmp = null;
  const drawTargets = [];
  if (fs.existsSync(FIXTURE_PATH)) {
    fixtureTmp = writeTempTrace(fs.readFileSync(FIXTURE_PATH, 'utf8'), 'combat-60t.jsonl');
    drawTargets.push({ rel: fixtureTmp.rel, label: 'combat-60t.jsonl (fixture, 60tick)' });
  } else {
    console.log('  skip: combat-60t.jsonl (fixture) — ' + FIXTURE_PATH + ' が見つからない');
  }
  drawTargets.push({ rel: 'stairs/20260814/20260820-153927/arena-0.jsonl', label: 'stairs 実トレース (900tick, 45秒戦闘)' });
  if (args.trace) drawTargets.push({ rel: args.trace, label: args.trace + ' (--trace)' });
  try {
    for (const tgt of drawTargets) {
      const abs = path.join(TRACES_ROOT, tgt.rel);
      if (!fs.existsSync(abs)) { console.log('  skip: ' + tgt.label + ' — ' + abs + ' が見つからない'); continue; }
      try {
        const url = args.url + '?trace=' + encodeURIComponent(tgt.rel);
        let usedRenderer = null;
        const r = await withChrome(url, async (cdp, renderer) => {
          usedRenderer = renderer;
          const ok = await waitForLoaded(cdp, 20000);
          if (!ok) throw new Error('トレースの読み込みがタイムアウトした');
          return await measureDrawFps(cdp);
        }, { gpu: args.gpu });
        anyRan = true;
        const fps = (r.drawN1 - r.drawN0) / r.elapsedSec;
        const rendererTxt = (usedRenderer && usedRenderer.renderer) ? usedRenderer.renderer : '(検出できなかった: ' + JSON.stringify(usedRenderer) + ')';
        console.log(`  ${tgt.label}: 実効 ${fps.toFixed(1)}fps (前値 17)   drawMs(EMA)=${r.drawMs != null ? r.drawMs.toFixed(2) : '?'}ms   ticks=${r.nTicks}`);
        console.log(`    renderer: ${rendererTxt}`);
        if (r.derived) {
          const walkKB = (r.derived.walkBytes / 1024).toFixed(1);
          const animKB = (r.derived.animBytes / 1024).toFixed(1);
          console.log(`    derived(walk/animTrack, T-13-08): walk=${walkKB}KB across ${r.derived.walkEntities} entities, anim=${animKB}KB (${r.derived.animTicks} ticks)`);
        }
      } catch (e) {
        console.log('  ERROR: ' + tgt.label + ': ' + e.message);
      }
    }
  } finally {
    if (fixtureTmp) cleanupTempTrace(fixtureTmp.abs);
  }

  // ---- (2) 取り込み ----
  console.log('\n=== (2) 取り込み: 毎秒 load() の費用(溜まった量ごと、前値と並べる) ===');
  const ingestPath = args.trace
    ? path.join(TRACES_ROOT, args.trace)
    : path.join(TRACES_ROOT, 'tank', '20260820', '20260821-054755', 'arena-0.jsonl');
  if (!fs.existsSync(ingestPath)) {
    console.log('  skip: ' + ingestPath + ' が見つからない (gitignore下、にーくらの機械にのみ存在)');
  } else {
    const lines = fs.readFileSync(ingestPath, 'utf8').split('\n');
    for (const t of INGEST_TARGETS) {
      const { prefix, capped, actualBytes } = computePrefix(lines, t.bytes);
      const tmp = writeTempTrace(prefix, 'ingest-' + t.label + '.jsonl');
      try {
        // **各水準は新しいページで測る**(前の呼び出しのGCゴミを持ち越さないため。上のコメント参照)。
        const ms = await withChrome(args.url, async (cdp) => {
          const ready = await waitForScriptsReady(cdp, 15000);
          if (!ready) throw new Error('ページのスクリプトが起動しない');
          return await measureIngestOne(cdp, tmp.rel);
        });
        anyRan = true;
        const mb = (actualBytes / 1024 / 1024).toFixed(1);
        console.log(`  ${mb}MB${capped ? ' (ファイル全体)' : ''}: ${ms.toFixed(0)}ms   (前値 ${t.baselineMs}ms)`);
      } catch (e) {
        console.log('  ERROR: ' + t.label + ': ' + e.message);
      } finally {
        cleanupTempTrace(tmp.abs);
      }
      if (capped) break; // ファイル全体に達した — これ以上大きい水準は測れない
    }
  }

  // ---- (2b) 追記(13-03): ライブの毎秒 appendLive() の費用(溜まった量ごと) ----
  console.log('\n=== (2b) 追記: 毎秒 appendLive() の費用(溜まった量ごと。目標 16ms未満、履歴長に依存しないこと) ===');
  if (!fs.existsSync(ingestPath)) {
    console.log('  skip: ' + ingestPath + ' が見つからない (gitignore下、にーくらの機械にのみ存在)');
  } else {
    const lines = fs.readFileSync(ingestPath, 'utf8').split('\n');
    const TICK_WINDOW = 20; // 実データは20tick/秒
    // 「16ms 未満」だけでは CYCLE-05 は守れない。**この見出しが謳っている不変条件は
    // 「履歴長に依存しない」ほうで、閾値ではない。** 2026-08-25 の実測で
    // 1.60 -> 9.70ms (同じ新着 60 行で 6 倍) と伸びていたのに、4 水準とも 16ms 未満
    // だったので全部 [OK] と出ていた —— 伸び方が誰にも見えないまま通っていた。
    // 標本を溜めて、最後に傾きを判定する。
    const appendSamples = [];
    for (const t of INGEST_TARGETS) {
      const { prefix, capped, actualBytes } = computePrefix(lines, t.bytes);
      const prefixLineCount = prefix.length ? prefix.split('\n').length : 0;
      const { tail, boundaryTick } = computeTailByTicks(lines, prefixLineCount, TICK_WINDOW);
      if (!tail.length) {
        console.log(`  ${t.label}: skip — prefixの切れ目(tick ${boundaryTick})より後に新着行が無い(ファイル末尾に近すぎる)`);
        continue;
      }
      const tmp = writeTempTrace(prefix, 'append-' + t.label + '.jsonl');
      try {
        const r = await withChrome(args.url, async (cdp) => {
          const ready = await waitForScriptsReady(cdp, 15000);
          if (!ready) throw new Error('ページのスクリプトが起動しない');
          return await measureAppendLiveOne(cdp, tmp.rel, tail);
        });
        anyRan = true;
        const ms = (r && typeof r === 'object') ? r.ms : r;
        const ents = (r && typeof r === 'object') ? r.ents : null;
        const mb = (actualBytes / 1024 / 1024).toFixed(1);
        const verdict = ms < 16 ? 'OK' : 'NG(目標16ms未満)';
        const trimMs = (r && typeof r === 'object' && typeof r.trimMs === 'number') ? r.trimMs : null;
        const ingestMs = (r && typeof r === 'object' && typeof r.ingestMs === 'number') ? r.ingestMs : null;
        const firstMs = (r && typeof r === 'object' && typeof r.first === 'number') ? r.first : null;
        appendSamples.push({ mb: Number(mb), ms: ms, ents: ents, lines: tail.length, trimMs: trimMs });
        const per = (ents && ents > 0) ? (ms / ents * 1000).toFixed(1) + 'µs/体' : '体数不明';
        console.log(`  ${mb}MB${capped ? ' (ファイル全体)' : ''} + 新着${tail.length}行(tick ${boundaryTick + 1}..${boundaryTick + TICK_WINDOW}): ${ms.toFixed(2)}ms  [${verdict}]  生存 ${ents == null ? '?' : ents} 体 (${per})  取り込み ${ingestMs == null ? '?' : ingestMs.toFixed(2)}ms / 1回目 ${firstMs == null ? '?' : firstMs.toFixed(2)}ms / 窓 ${trimMs == null ? '?' : trimMs.toFixed(2)}ms`);
      } catch (e) {
        console.log('  ERROR: ' + t.label + ': ' + e.message);
      } finally {
        cleanupTempTrace(tmp.abs);
      }
      if (capped) break;
    }

    // ---- 傾きの判定 (CYCLE-05 が本当に謳っていること) ----
    // **閾値ではなく伸び方を見る。** どちらの軸で伸びたのかまで言う ——
    // 履歴で伸びたなら CYCLE-05 が破れている。生存体数で伸びただけなら
    // 「水槽が埋まっている」ほうの話で、直す場所が違う。
    if (appendSamples.length >= 2) {
      const lo = appendSamples[0], hi = appendSamples[appendSamples.length - 1];
      const msR = hi.ms / (lo.ms || 1e-9);
      const mbR = hi.mb / (lo.mb || 1e-9);
      const entR = (lo.ents && hi.ents) ? (hi.ents / lo.ents) : null;
      const perR = (lo.ents && hi.ents) ? ((hi.ms / hi.ents) / (lo.ms / lo.ents)) : null;
      console.log('');
      console.log('  伸び方: 履歴 ×' + mbR.toFixed(1) + ' に対して 費用 ×' + msR.toFixed(1)
        + (entR ? ('、生存体数 ×' + entR.toFixed(1)) : '')
        + (perR ? ('、1体あたりの費用 ×' + perR.toFixed(2)) : ''));
      // **初回 trim を引いた値でも判定する。** bench は load() 直後に 1 回だけ
      // appendLive するので、溜まりすぎた分をまとめて捨てる費用がその 1 回に乗る。
      // 本物のライブは毎秒少しずつ捨てるため、この分は steady-state の費用ではない。
      const netLo = lo.trimMs == null ? lo.ms : Math.max(0, lo.ms - lo.trimMs);
      const netHi = hi.trimMs == null ? hi.ms : Math.max(0, hi.ms - hi.trimMs);
      const netR = netHi / (netLo || 1e-9);
      if (lo.trimMs != null && hi.trimMs != null) {
        console.log('  窓の切り出しを引くと: ' + netLo.toFixed(2) + 'ms -> ' + netHi.toFixed(2)
          + 'ms (×' + netR.toFixed(1) + ')');
      }
      const flat = netR < 2.0;
      const explainedByEntities = perR != null && perR < 1.5;
      if (flat) {
        console.log('  [OK] 履歴長に依存していない (費用の伸びが 2 倍未満)');
      } else if (explainedByEntities) {
        console.log('  [注意] 費用は伸びたが、1 体あたりでは横ばい —— 伸びたのは履歴ではなく**その瞬間に生きている体数**。CYCLE-05 は破れていないが、水槽が埋まり続けること自体は別途の問題');
      } else {
        console.log('  [NG] 履歴長に依存して伸びている。CYCLE-05 (ライブの毎秒処理が履歴長に依存しない) が破れている —— 16ms 未満でも、これは通してはいけない');
        // **この判定の限界を、判定と同じ場所に書いておく。**
        // 4 水準は履歴だけでなく**取り込む中身も違う** (prefix の切れ目が違うので、
        // tail は録画の別の瞬間から来る)。だから厳密には「履歴で伸びた」と「その瞬間の
        // 中身が重かった」を分けられない。2026-08-25 の調査ではここで詰まった ——
        // seriesFeed / store.append / growDerived / renderAiLog / trimBefore / seriesTrim を
        // 個別に測るとどれも 289,054 行で横ばい (合計 1ms 未満) なのに、appendLive 全体は
        // 取り込み側だけで 1.20 -> 7.60ms に伸びる。次に測る人はまず**同じ tail を**
        // 4 水準へ食わせて、伸びが再現するかを見ること。再現しなければ中身のせい。
        console.log('       注意: この 4 水準は tail の中身も違う。断定する前に、同じ tail を tick だけずらして 4 水準へ食わせ、再現するかを確かめること (2026-08-25 にそれで反証された)');
      }
    }

    // 二重取り込み(T-13-09/再接続時の先頭からの送り直しを吸収できること): 同じtailを
    // 2度appendLiveしても、changePointsと全tickのframeAt().posが1度だけの場合と一致する。
    // 対象は最小のprefix水準(2.0MB)で十分(ここが壊れていれば他の水準でも壊れているはず)。
    console.log('\n=== 二重取り込み: 同じ1秒ぶんを2度appendLiveしても状態が変わらないこと ===');
    const smallest = INGEST_TARGETS[0];
    const { prefix: dupPrefix } = computePrefix(lines, smallest.bytes);
    const dupPrefixLineCount = dupPrefix.length ? dupPrefix.split('\n').length : 0;
    const { tail: dupTail, boundaryTick: dupBoundary } = computeTailByTicks(lines, dupPrefixLineCount, TICK_WINDOW);
    if (!dupTail.length) {
      console.log('  skip: prefixの切れ目より後に新着行が無い');
    } else {
      const tmp = writeTempTrace(dupPrefix, 'dup-check.jsonl');
      try {
        const result = await withChrome(args.url, async (cdp) => {
          const ready = await waitForScriptsReady(cdp, 15000);
          if (!ready) throw new Error('ページのスクリプトが起動しない');
          const expr = `
(async function(){
  const prefixText = await (await fetch('/api/trace?path=' + encodeURIComponent(${JSON.stringify(tmp.rel)}))).text();
  load(prefixText, 'bench-dup', {live:true});
  const tail = ${JSON.stringify(dupTail)};
  appendLive(tail, {});
  const cp1 = D.store.stats.changePoints;
  const maxT1 = D.maxTick;
  const pos1 = [];
  for (let t = 0; t <= maxT1; t += Math.max(1, Math.floor(maxT1 / 30))) {
    const f = D.frameAt(t, 0);
    pos1.push([...f.pos.entries()].map(([id, p]) => [id, p.x, p.y, p.z]));
  }
  appendLive(tail, {}); // 同じ行をもう一度(再接続で先頭から送り直された想定)
  const cp2 = D.store.stats.changePoints;
  const maxT2 = D.maxTick;
  const pos2 = [];
  for (let t = 0; t <= maxT2; t += Math.max(1, Math.floor(maxT2 / 30))) {
    const f = D.frameAt(t, 0);
    pos2.push([...f.pos.entries()].map(([id, p]) => [id, p.x, p.y, p.z]));
  }
  return { cp1, cp2, maxT1, maxT2, posMatch: JSON.stringify(pos1) === JSON.stringify(pos2), sampled: pos1.length };
})()`;
          return await evalPage(cdp, expr, true);
        });
        anyRan = true;
        const cpOk = result.cp1 === result.cp2;
        const maxTOk = result.maxT1 === result.maxT2;
        console.log(`  changePoints: 1回目=${result.cp1} 2回目=${result.cp2}  [${cpOk ? 'OK' : 'NG'}]`);
        console.log(`  maxTick: 1回目=${result.maxT1} 2回目=${result.maxT2}  [${maxTOk ? 'OK' : 'NG'}]`);
        console.log(`  frameAt().pos (${result.sampled}点抽出): [${result.posMatch ? 'OK 一致' : 'NG 不一致'}]`);
        if (!cpOk || !maxTOk || !result.posMatch) {
          console.log('  ERROR: 二重取り込みで状態が変わった(再接続で先頭から送り直されると壊れる可能性)');
        }
      } catch (e) {
        console.log('  ERROR: 二重取り込み検査: ' + e.message);
      } finally {
        cleanupTempTrace(tmp.abs);
      }
    }
  }

  // ---- (3) 飛び込み ----
  console.log('\n=== (3) 飛び込み: 任意tickへのseek費用(疎構造化の代償、O(1)→O(log n)) ===');
  const scrubRel = args.trace || (fs.existsSync(ingestPath) ? path.relative(TRACES_ROOT, ingestPath).split(path.sep).join('/') : 'stairs/20260814/20260820-153927/arena-0.jsonl');
  const scrubAbs = path.join(TRACES_ROOT, scrubRel);
  if (!fs.existsSync(scrubAbs)) {
    console.log('  skip: ' + scrubAbs + ' が見つからない');
  } else {
    try {
      const url = args.url + '?trace=' + encodeURIComponent(scrubRel);
      const ms = await withChrome(url, async (cdp) => {
        const ok = await waitForLoaded(cdp, 20000);
        if (!ok) throw new Error('トレースの読み込みがタイムアウトした');
        return await measureScrub(cdp);
      });
      anyRan = true;
      const sorted = [...ms].sort((a, b) => a - b);
      const avg = ms.reduce((a, b) => a + b, 0) / ms.length;
      const median = sorted[Math.floor(sorted.length / 2)];
      const max = Math.max(...ms);
      console.log(`  ${ms.length}回 (T.tick=seek + draw()): avg ${avg.toFixed(2)}ms   median ${median.toFixed(2)}ms   max ${max.toFixed(2)}ms   (${scrubRel})`);
    } catch (e) {
      console.log('  ERROR: 飛び込み計測: ' + e.message);
    }
  }

  console.log('');
  if (!anyRan) {
    console.error('全モードがskipされた —— 1件も測っていない。トレースの在り処を確認せよ(上のskip行の絶対パス参照)。');
    process.exit(1);
  }
  process.exit(0);
}

main().catch((e) => { console.error('bench.mjs 失敗: ' + ((e && e.stack) || e)); process.exit(1); });
