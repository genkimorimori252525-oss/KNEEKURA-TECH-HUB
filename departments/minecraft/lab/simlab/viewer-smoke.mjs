// Viewer を実際のブラウザで開いて、**例外とコンソールエラーを拾う**。
//
// なぜ要るか: 静的な構文検査(new Function)は「動くか」を何も言わない。
// index.html は 2,700 行の 1 枚ものなので、TDZ・未定義参照・型違いは
// 「開いてみるまで判らない」。にーくらの実機を壊す前に、こちらで開く。
//
//   node simlab/viewer-smoke.mjs [URL] [待つ秒数]
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const url = process.argv[2] || 'http://127.0.0.1:8777/';
const waitSec = Number(process.argv[3] || 14);
// 追加で調べたいことがあれば式で渡す(ページの中で評価して結果を出す)。
const extraExpr = process.argv[4] || null;
const CHROME = ['C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Microsoft/Edge/Application/msedge.exe'].find((p) => fs.existsSync(p));
if (!CHROME) { console.error('Chrome も Edge も見つからない'); process.exit(1); }

const PORT = 9334;
const child = spawn(CHROME, ['--headless=new', '--enable-unsafe-swiftshader',
  '--use-gl=angle', '--use-angle=swiftshader', '--hide-scrollbars',
  '--window-size=1840,900', '--remote-debugging-port=' + PORT,
  '--user-data-dir=' + path.join(os.tmpdir(), 'simlab-smoke-profile'),
  '--no-first-run', '--no-default-browser-check', url],
  { stdio: 'ignore', windowsHide: true });

let ws = null, msgId = 0;
const pending = new Map();
const errors = [], warns = [];
const cdp = (method, params) => new Promise((resolve, reject) => {
  const id = ++msgId; pending.set(id, { resolve, reject });
  ws.send(JSON.stringify({ id, method, params: params || {} }));
});
const done = (code) => { try { ws && ws.close(); } catch {} try { child.kill(); } catch {} process.exit(code); };

async function findPage() {
  for (let i = 0; i < 80; i++) {
    try {
      const list = await (await fetch('http://127.0.0.1:' + PORT + '/json')).json();
      const p = list.find((t) => t.type === 'page' && t.webSocketDebuggerUrl);
      if (p) return p;
    } catch { /* まだ */ }
    await new Promise((r) => setTimeout(r, 250));
  }
  throw new Error('Chrome の DevTools に繋がらない');
}

try {
  const page = await findPage();
  ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = () => rej(new Error('WebSocket に繋がらない')); });
  ws.onmessage = (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) {
      const p = pending.get(m.id); pending.delete(m.id);
      if (m.error) p.reject(new Error(m.error.message)); else p.resolve(m.result);
      return;
    }
    if (m.method === 'Runtime.exceptionThrown') {
      const d = m.params.exceptionDetails || {};
      errors.push('例外: ' + (d.exception && (d.exception.description || d.exception.value) || d.text)
        + ' @' + (d.url || '') + ':' + (d.lineNumber + 1));
    }
    if (m.method === 'Runtime.consoleAPICalled') {
      const txt = (m.params.args || []).map((a) => a.value !== undefined ? String(a.value) : (a.description || a.type)).join(' ');
      if (m.params.type === 'error') errors.push('console.error: ' + txt);
      else if (m.params.type === 'warning') warns.push(txt);
    }
  };
  await cdp('Runtime.enable');
  await cdp('Log.enable');
  // Runtime.enable より前に出た例外は拾えないので、そのぶん待ってから読み直す。
  await new Promise((r) => setTimeout(r, waitSec * 1000));

  const ev = async (expr) => JSON.parse((await cdp('Runtime.evaluate',
    { expression: expr, returnByValue: true })).result.value);

  const st = await ev(`JSON.stringify({
    clock: (typeof LIVE_CLOCK!=='undefined') ? LIVE_CLOCK.report() : null,
    followLive: (typeof T!=='undefined') ? T.followLive : null,
    tick: (typeof T!=='undefined') ? T.tick : null,
    maxTick: (typeof D!=='undefined') ? D.maxTick : null,
    dropped: (typeof T!=='undefined') ? (T.droppedRows||0) : null,
    perf: (document.getElementById('perf')||{}).textContent || '',
    msg: (document.getElementById('tankMsg')||{}).textContent || '',
    live: (document.getElementById('tankLiveTxt')||{}).textContent || '',
    entities: (typeof D!=='undefined'&&D.entities) ? D.entities.size : null,
    missStatus: (window.SimGL&&SimGL.missStatus)?SimGL.missStatus():'',
  })`);

  console.log('URL            : ' + url);
  console.log('perf 行        : ' + (st.perf || '(空)').trim());
  console.log('水槽バッジ     : ' + (st.live || '(出ていない)'));
  console.log('tankMsg        : ' + (st.msg || '(空)'));
  console.log('tick / maxTick : ' + st.tick + ' / ' + st.maxTick + '   entities=' + st.entities);
  console.log('取りこぼし     : ' + st.dropped + ' 行');
  console.log('描けていない   : ' + (st.missStatus || 'なし'));
  console.log('時計           : ' + (st.clock ? JSON.stringify(st.clock) : '(未定義)'));
  if (extraExpr) {
    const r = await cdp('Runtime.evaluate', { expression: extraExpr, returnByValue: true, awaitPromise: true });
    const v = r.exceptionDetails ? ('例外: ' + (r.exceptionDetails.exception && r.exceptionDetails.exception.description || r.exceptionDetails.text)) : r.result.value;
    console.log('追加の問い       : ' + (typeof v === 'string' ? v : JSON.stringify(v)));
  }
  if (warns.length) { console.log('\n警告 ' + warns.length + ' 件:'); warns.slice(0, 8).forEach((w) => console.log('  ! ' + w)); }
  if (errors.length) {
    console.log('\nエラー ' + errors.length + ' 件:');
    errors.slice(0, 12).forEach((e) => console.log('  × ' + e));
    console.log('\nviewer-smoke: FAILED');
    done(1);
  }
  if (st.clock === null) { console.log('\n× LIVE_CLOCK が未定義 —— 時計が読み込まれていない\nviewer-smoke: FAILED'); done(1); }
  if (st.dropped) { console.log('\n× 行を取りこぼしている\nviewer-smoke: FAILED'); done(1); }
  console.log('\nviewer-smoke: OK');
  done(0);
} catch (e) {
  console.error('viewer-smoke: ' + (e && e.message || e));
  done(1);
}
