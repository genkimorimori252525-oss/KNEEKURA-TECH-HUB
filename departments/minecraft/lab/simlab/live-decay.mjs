#!/usr/bin/env node
// =============================================================================
// simlab/live-decay.mjs — ライブが時間とともに重くなるのかを、4 つの軸で同時に採る
// =============================================================================
//
// にーくら 2026-08-25 (第1報):「fps がやはり後半にかけて落ちていって、やがて…」
// にーくら 2026-08-25 (訂正):「複数の敵を出して戦闘が発生し、**終わったら**発生するんだ。
//                              つまり**時間は全く関係がない**。」
//
// **狙いが変わった。** 時間で劣化する形ではなく、**戦闘が終わった瞬間**に起きる形。
// だから --summon/--at で戦闘をこちらから起こし、--every を細かくして
// 「終わった瞬間」を跨げるようにする。粗い刻みでは一瞬の段差が見えない。
//
// **これは探索用の道具であって、合否を出す道具ではない。** 閾値はまだ書いていない ——
// 先に数字を見てから固定し、修正した後に**別の run** で判定する。同じ測定で閾値を
// 決めて合否も出すのは事後設定で、2026-08-25 に bench.mjs の (2b) で実際にそれをやって
// [NG] を誤報し、対照実験で撤回した。同じ形を繰り返さない。
//
// -----------------------------------------------------------------------------
// なぜ 4 軸を**同時に**採るのか
// -----------------------------------------------------------------------------
// 2026-08-25 の調査で、次の範囲は既に無罪が確定している (再調査しない):
//
//   録画トレースの再生      258,016 tick で 161.8fps (900 tick の fixture は 158.3fps)
//   ライブの毎秒追記(定常)  中身を固定した同じ tail を履歴 20 倍へ: 0.50 -> 0.50ms
//   seriesFeed / store.append / growDerived / renderAiLog / trimBefore / seriesTrim
//                          289,054 行で全部横ばい・合計 1ms 未満
//
// 残る手がかりは heap だけ (ライブで +160MB/水槽時間)。ただし usedJSHeapSize は
// **未回収のゴミを含む**ので、強制 GC を打ってから採らないと滞留とは言えない。
//
// そして**水槽の TPS を並べないと、Viewer の無罪を証明できない**。水槽が埋まって
// 20TPS を割れば、Viewer は正しく追従して見かけの滑らかさが落ちる —— そのとき直す
// 場所は世界の側で、Viewer ではない。この 2 つを分けずに fps だけ見ると読み違える。
//
// -----------------------------------------------------------------------------
// なぜ平均 fps では足りないのか
// -----------------------------------------------------------------------------
// live-clock-selftest.mjs の冒頭が自ら言っているとおり、**60fps のまま絵が停止したり
// 逆走したりする**症状は平均に出ない。だから rAF 間隔の分位点・最大停止・静止フレーム率・
// 逆走率まで採る。
//
//   node simlab/live-decay.mjs [--minutes=30] [--every=30] [--pal=1] [--url=...]
//
// --pal=0 との対照を必ず取ること: palette の採取・解凍・描画そのものが重い可能性を、
// 先に切り分ける必要がある。
// =============================================================================
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.dirname(HERE);
const HEARTBEAT = path.join(ROOT, 'run', 'sim', 'traces', 'heartbeat.json');

const arg = (k, d) => {
  const m = process.argv.find((a) => a.startsWith('--' + k + '='));
  return m ? m.slice(k.length + 3) : d;
};
if (process.argv.includes('--help') || process.argv.includes('-h')) {
  console.log(fs.readFileSync(fileURLToPath(import.meta.url), 'utf8')
    .split('\n').filter((l) => l.startsWith('//')).join('\n'));
  process.exit(0);
}
const MINUTES = Number(arg('minutes', 30));
const EVERY = Number(arg('every', 30));
const PAL = arg('pal', '1');
const BASE_URL = arg('url', 'http://127.0.0.1:8777/');
const URL_ = BASE_URL + (BASE_URL.includes('?') ? '&' : '?') + 'pal=' + PAL;
const PORT = Number(arg('port', 9342));
/** 戦闘をこちらから起こす: --summon=<数> --at=<秒>。0 なら何もしない。 */
const SUMMON = Number(arg('summon', 0));
const SUMMON_AT = Number(arg('at', 60));
const SUMMON_TYPE = arg('mob', 'minecraft:zombie');

/**
 * どの表示を見ながら測るか (real=3D / scope=計測器 / f3 / plan)。既定は Viewer と同じ 'real'。
 *
 * <p><b>タブによって毎フレームの仕事がまるで違う。</b> 2026-08-25 の実測で 'real' は
 * 10 分回して 163 -> 162fps とほぼ平坦だったが、それは drawScope が一度も呼ばれて
 * いなかったから (index.html:1102 の分岐)。どのタブで測ったかを言わない計測は、
 * 「症状が出ない」の根拠にならない。
 */
const MODE = arg('mode', 'real');

const CHROME_CANDIDATES = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
];
const CHROME = CHROME_CANDIDATES.find((p) => fs.existsSync(p));
if (!CHROME) { console.error('Chrome も Edge も見つからない'); process.exit(1); }

// **実 GPU を狙う。** ソフトウェアラスタライザで測ると GL の費用が過大に出て、
// 「描画が重い」という誤った結論を導く (bench.mjs の --gpu と同じ理由)。
const profile = path.join(os.tmpdir(), 'simlab-livedecay-' + process.pid);
const child = spawn(CHROME, ['--headless=new', '--use-gl=angle', '--use-angle=d3d11',
  '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
  '--disable-backgrounding-occluded-windows',
  '--hide-scrollbars', '--window-size=1400,900', '--remote-debugging-port=' + PORT,
  '--user-data-dir=' + profile, '--no-first-run', '--no-default-browser-check', URL_],
  { stdio: 'ignore', windowsHide: true });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function findPage() {
  for (let i = 0; i < 120; i++) {
    try {
      const l = await (await fetch('http://127.0.0.1:' + PORT + '/json')).json();
      const p = l.find((t) => t.type === 'page' && t.webSocketDebuggerUrl);
      if (p) return p;
    } catch { /* まだ立ち上がっていない */ }
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

/** 水槽の TPS。心拍 2 点の tick 差 / 実時間差。**Viewer の無罪を決める軸。** */
function readHeartbeat() {
  try {
    const hb = JSON.parse(fs.readFileSync(HEARTBEAT, 'utf8'));
    return { tick: hb.tick, atMs: hb.atMs, trace: hb.trace, ageSec: (Date.now() - hb.atMs) / 1000 };
  } catch { return null; }
}

// ページの中へ置く計測器。**別の rAF を回して間隔だけ採る** ——
// 本体のループを触らずに、同じ vsync とメインスレッドの詰まりを見られる。
const INSTALL = `(() => {
  if (window.__decay) return 'already';
  const d = { iv: [], last: 0, lastTick: -1, still: 0, back: 0, n: 0 };
  window.__decay = d;
  const loop = (t) => {
    if (d.last) {
      const dt = t - d.last;
      d.iv.push(dt);
      if (d.iv.length > 20000) d.iv.splice(0, 10000);
    }
    d.last = t;
    const tk = (window.T && typeof T.tick === 'number') ? T.tick : -1;
    if (d.lastTick >= 0 && tk >= 0) {
      if (tk === d.lastTick) d.still++;
      else if (tk < d.lastTick) d.back++;
    }
    if (tk >= 0) d.lastTick = tk;
    d.n++;
    requestAnimationFrame(loop);
  };
  requestAnimationFrame(loop);
  return 'installed';
})()`;

// 1 標本。**poseSourceCount は区間差分で採る** —— 累計だと後半の実態が薄まって消える。
const SAMPLE = `(() => {
  const d = window.__decay || { iv: [], still: 0, back: 0, n: 0 };
  const iv = d.iv.slice();
  d.iv.length = 0;
  const still = d.still; const back = d.back; const n = d.n;
  d.still = 0; d.back = 0; d.n = 0;
  iv.sort((a, b) => a - b);
  const q = (p) => (iv.length ? iv[Math.min(iv.length - 1, Math.floor(iv.length * p))] : null);
  const out = {
    frames: iv.length,
    fps: iv.length && iv.length > 1 ? 1000 / (iv.reduce((a, b) => a + b, 0) / iv.length) : null,
    p50: q(0.50), p95: q(0.95), p99: q(0.99), max: iv.length ? iv[iv.length - 1] : null,
    stillPct: n ? (100 * still / n) : null,
    backPct: n ? (100 * back / n) : null,
    vis: document.visibilityState,
  };
  try { out.tick = T.tick; out.maxTick = D.maxTick; out.lag = D.maxTick - T.tick; } catch (e) { /* 未初期化 */ }
  try { out.entities = D.entities ? D.entities.size : null; } catch (e) { /* 同上 */ }
  try { out.ingestMs = T.ingestMs; out.drawMs = T.drawMs; } catch (e) { /* 同上 */ }
  try { out.clockRate = (window.LIVE_CLOCK && LIVE_CLOCK.s) ? LIVE_CLOCK.s.rate : null; } catch (e) { /* 同上 */ }
  // **frameAt の費用は既に測られている** (store.js の frameAtMsEma)。新しく計測器を
  // 作らない。frameAt は毎フレーム全レーンを走査するので、戦闘で増えたレーンが
  // 死んだ後も 2 分窓で落ちるまで走査対象であり続ける —— そこを見る。
  try {
    const st = D.store.stats;
    out.frameAtMs = st.frameAtMs;
    out.changePoints = st.changePoints;
    out.trims = st.trims;
    out.trimmedEntities = st.trimmedEntities;
    out.storeMB = Math.round(st.bytes / 1048576 * 10) / 10;
  } catch (e) { /* 古い版には stats が無い */ }
  try {
    const s = SimGL.derivedStats();
    out.poseSource = s.poseSource;
    out.counts = Object.assign({}, s.poseSourceCount);
    out.walkKB = Math.round((s.walkBytes || 0) / 1024);
    // **アニメライブラリの読み込み数。** 霊夢が新しい技を出すと、そのアニメの実機頂点を
    // 取りに行ってキャッシュに載せる。戦闘で技の種類が増えるほど載り、**返らない** ——
    // 「戦闘で出て、時間には依らない」という症状の形と一致する。
    out.libLoaded = s.poseLibLoadedAnims;
    out.libMB = s.poseLibBytes == null ? null : Math.round(s.poseLibBytes / 1048576);
    out.libEvicted = s.poseLibEvicted;
    out.libHits = s.poseLibHits;
    out.animKB = Math.round((s.animBytes || 0) / 1024);
  } catch (e) { /* gl.js が居ない */ }
  return out;
})()`;

let ws = null;
async function main() {
  const page = await findPage();
  ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((r, j) => { ws.onopen = r; ws.onerror = () => j(new Error('DevTools の WebSocket に繋がらない')); });
  const cdp = makeCdp(ws);
  await cdp('HeapProfiler.enable').catch(() => { /* 無い版もある */ });

  const ev = async (expr, awaitPromise) => {
    const r = await cdp('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: !!awaitPromise });
    if (r.exceptionDetails) {
      throw new Error('page eval: ' + (r.exceptionDetails.text || '') + ' '
        + ((r.exceptionDetails.exception && r.exceptionDetails.exception.description) || ''));
    }
    return r.result ? r.result.value : undefined;
  };

  for (let i = 0; i < 120; i++) {
    if (await ev('!!(window.T && window.D && window.SimGL)').catch(() => false)) break;
    await sleep(500);
  }

  // **どのレンダラで測ったかを必ず出す。** ソフトウェアで測って「描画が重い」と
  // 結論する事故を防ぐ (bench.mjs が同じ理由で必ず印字している)。
  // **測る前にタブを合わせる。** ボタンを押した時と同じ状態にするため、T.mode を直接置いて
  // から draw() を 1 回呼ぶ (index.html:1338 のハンドラがやっているのと同じこと)。
  if (MODE !== 'real') {
    await ev('(() => { try { T.mode = ' + JSON.stringify(MODE) + '; draw(); return T.mode; } catch (e) { return String(e); } })()');
  }
  // **素の T を見る。** index.html の T はトップレベル const なので window には載らない
  // (window.T で見ると常に null になり、設定できているのに『当たっていない』と誤報する)。
  const modeNow = await ev("(typeof T !== 'undefined' && T.mode) || null");
  console.log('表示     : ' + modeNow + (modeNow === MODE ? '' : '  ** --mode=' + MODE + ' が当たっていない **'));
  const renderer = await ev(`(() => { const c = document.createElement('canvas');
    const g = c.getContext('webgl2') || c.getContext('webgl'); if (!g) return 'no-webgl';
    const x = g.getExtension('WEBGL_debug_renderer_info');
    return x ? g.getParameter(x.UNMASKED_RENDERER_WEBGL) : 'unknown'; })()`);
  console.log('renderer : ' + renderer);
  console.log('url      : ' + URL_);
  const hb0 = readHeartbeat();
  console.log('水槽     : ' + (hb0 ? (hb0.trace + '  (心拍 ' + hb0.ageSec.toFixed(1) + ' 秒前)')
    : '心拍が無い —— ライブではない。記録を開いて測っても症状は出ない'));
  console.log('');

  await ev(INSTALL);
  await sleep(2000);
  await ev(SAMPLE);   // 立ち上がりの外れ値を捨てる

  const rows = [];
  let summoned = false;
  const samples = Math.max(1, Math.floor((MINUTES * 60) / EVERY));
  if (SUMMON > 0) {
    console.log('負荷: ' + SUMMON_AT + ' 秒の時点で ' + SUMMON_TYPE + ' を ' + SUMMON + ' 体放つ');
  } else {
    console.log('負荷: 掛けない (--summon=<数> --at=<秒> で戦闘を起こせる)');
  }
  console.log('');
  console.log('    経過   fps   p50    p95    p99    最大  frameAt   体数   点数   heap  TPS trim anim   libMB 捨  出来事');
  let prevHb = readHeartbeat();
  let prevCounts = null;

  for (let i = 0; i < samples; i++) {
    await sleep(EVERY * 1000);

    // **強制 GC してから heap を採る。** usedJSHeapSize は未回収のゴミを含むので、
    // これをやらないと「滞留が伸びた」と「ゴミが溜まっただけ」を分けられない。
    await cdp('HeapProfiler.collectGarbage').catch(() => { /* 無い版もある */ });
    await sleep(250);
    const heapMB = await ev('(() => { try { return Math.round(performance.memory.usedJSHeapSize / 1048576); } catch (e) { return null; } })()');

    const s = await ev(SAMPLE);
    const hb = readHeartbeat();
    let tps = null;
    if (hb && prevHb && hb.atMs > prevHb.atMs) {
      tps = (hb.tick - prevHb.tick) / ((hb.atMs - prevHb.atMs) / 1000);
    }
    prevHb = hb || prevHb;

    let palDelta = null;
    if (s.counts) {
      if (prevCounts) {
        const tot = Object.keys(s.counts).reduce((a, k) => a + (s.counts[k] - (prevCounts[k] || 0)), 0);
        const pal = (s.counts.palette || 0) - (prevCounts.palette || 0);
        palDelta = tot > 0 ? (100 * pal / tot) : null;
      }
      prevCounts = Object.assign({}, s.counts);
    }

    // **掛けた負荷は出力に残す。** 何をしたか判らない測定は読み直せない。
    let mark = '';
    const elapsed = (i + 1) * EVERY;
    if (SUMMON > 0 && !summoned && elapsed >= SUMMON_AT) {
      summoned = true;
      let ok = 0;
      for (let k = 0; k < SUMMON; k++) {
        const x = -6 + (k % 4) * 4, z = -6 + Math.floor(k / 4) * 4;
        try {
          const r = await fetch(BASE_URL.replace(/\/$/, '') + '/api/summon?type='
            + encodeURIComponent(SUMMON_TYPE) + '&x=' + x + '&y=66&z=' + z);
          if (r.ok) ok++;
        } catch (e) { /* 水槽が居ない */ }
      }
      mark = '<- ' + SUMMON_TYPE + ' x' + ok + ' を放った';
    }
    const f = (v, w, d2) => (v == null ? '-' : Number(v).toFixed(d2 === undefined ? 1 : d2)).padStart(w);
    console.log(
      String(elapsed).padStart(7) + 's'
      + f(s.fps, 6) + f(s.p50, 7) + f(s.p95, 7) + f(s.p99, 7) + f(s.max, 7)
      + f(s.frameAtMs, 8, 3)
      + String(s.entities == null ? '-' : s.entities).padStart(7)
      + String(s.changePoints == null ? '-' : s.changePoints).padStart(7)
      + String(heapMB == null ? '-' : heapMB).padStart(6) + 'MB'
      + f(tps, 5)
      + String(s.trims == null ? '-' : s.trims).padStart(5)
      + String(s.libLoaded == null ? '-' : s.libLoaded).padStart(5)
      + String(s.libMB == null ? '-' : s.libMB).padStart(6) + 'MB'
      + String(s.libEvicted == null ? '-' : s.libEvicted).padStart(4)
      + '  ' + mark);

    rows.push(Object.assign({ at: elapsed, heapMB, tps, palDelta, mark }, s));
  }

  console.log('');
  if (rows.length >= 2) {
    const a = rows[0], b = rows[rows.length - 1];
    const rel = (x, y) => (x && y ? ((y / x) * 100).toFixed(0) + '%' : '-');
    console.log('fps   ' + f2(a.fps) + ' -> ' + f2(b.fps) + '  (' + rel(a.fps, b.fps) + ')');
    console.log('p99   ' + f2(a.p99) + 'ms -> ' + f2(b.p99) + 'ms');
    console.log('heap  ' + a.heapMB + 'MB -> ' + b.heapMB + 'MB  (強制GC後なので、これは滞留)');
    console.log('TPS   ' + f2(a.tps) + ' -> ' + f2(b.tps)
      + '   ← ここが落ちているなら Viewer は無罪。直す場所は世界の側');
    console.log('体数  ' + a.entities + ' -> ' + b.entities);
    const peak = rows.reduce((m, r) => (r.entities > (m.entities || 0) ? r : m), rows[0]);
    const worst = rows.reduce((m, r) => ((r.fps || 1e9) < (m.fps || 1e9) ? r : m), rows[0]);
    console.log('');
    console.log('体数の山 : ' + peak.at + 's  体数 ' + peak.entities + '  fps ' + f2(peak.fps)
      + '  frameAt ' + f2(peak.frameAtMs) + 'ms');
    console.log('fps の底 : ' + worst.at + 's  体数 ' + worst.entities + '  fps ' + f2(worst.fps)
      + '  frameAt ' + f2(worst.frameAtMs) + 'ms');
    console.log('');
    console.log('**読み方**: 戦闘が終わった後に fps が落ち、約 2 分後 (trimBefore の窓) に');
    console.log('  回復するなら、死んだレーンの走査が原因 (frameAt が全レーンを回る)。');
    console.log('  回復しないなら、窓で落ちないものが残っている —— trim の列を見ること。');
    console.log('  frameAt が伸びていないのに fps が落ちるなら、frameAt は無罪。');
  }
  const out = path.join(os.tmpdir(), 'live-decay-pal' + PAL + '.json');
  fs.writeFileSync(out, JSON.stringify(rows, null, 2));
  console.log('');
  console.log('生データ: ' + out);
  console.log('**対照を忘れない**: --pal=0 でもう一度回して、palette 自体の費用を切り分けること。');
}
function f2(v) { return v == null ? '-' : Number(v).toFixed(1); }

main().catch((e) => { console.error('FAILED: ' + e.message); process.exitCode = 1; })
  .finally(async () => {
    try { if (ws) ws.close(); } catch { /* もう閉じている */ }
    try { child.kill(); } catch { /* もう死んでいる */ }
    await sleep(300);
    try { fs.rmSync(profile, { recursive: true, force: true }); } catch { /* Windows のロック。実害なし */ }
  });
