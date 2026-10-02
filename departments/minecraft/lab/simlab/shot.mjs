// Viewer の画面を撮る。
//
// にーくら 2026-08-20:
//   『白に白のフォントでみえないよ。また、スクロールもできない。
//     君が画面を見れるようにして、UIを調節してよ。被ってるし。』
//
// **見ずに UI を作っていたのが根本の問題。** 配色もはみ出しも、見れば 1 秒で判る。
// ここまで「動くはず」で押し切ってきたので、目を用意する。
//
// なぜ --screenshot ではなく DevTools プロトコルなのか:
//   Viewer は /api/live へ SSE を張りっぱなしにするので、ページは永遠に
//   「読み込み完了」にならない。chrome --screenshot は load を待つので返ってこない
//   （実測: 120 秒でタイムアウト）。CDP なら**こちらの好きな時点で**撮れる。
//
// WebGL について:
//   ヘッドレスには GPU が無いので --use-angle=swiftshader でソフトウェア描画させる。
//   遅いが、モデルが描けているか・UI が被っていないかを見るには足りる。
//
// 使い方:
//   node simlab/shot.mjs [出力パス] [待つ秒数] [URL]
//   node simlab/shot.mjs shot.png 10
//
// クリックしてから撮る (ドロップダウンの配色を見るときなど):
//   node simlab/shot.mjs shot.png 10 http://127.0.0.1:8777/ "#tankMod"
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const CHROME_CANDIDATES = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
];

const out = process.argv[2] || 'shot.png';
const waitSec = Number(process.argv[3] || 10);
const url = process.argv[4] || 'http://127.0.0.1:8777/';
const clickSel = process.argv[5] || null;

const chrome = CHROME_CANDIDATES.find((p) => fs.existsSync(p));
if (!chrome) {
  console.error('Chrome も Edge も見つからない');
  process.exit(1);
}

const PORT = 9333;
const profile = path.join(os.tmpdir(), 'simlab-shot-profile');

const child = spawn(chrome, [
  '--headless=new',
  '--enable-unsafe-swiftshader',
  '--use-gl=angle',
  '--use-angle=swiftshader',
  '--hide-scrollbars',
  '--window-size=1840,900',
  '--remote-debugging-port=' + PORT,
  '--user-data-dir=' + profile,
  '--no-first-run',
  '--no-default-browser-check',
  url,
], { stdio: 'ignore', windowsHide: true });

let ws = null;
let msgId = 0;
const pending = new Map();

function cdp(method, params) {
  const id = ++msgId;
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    ws.send(JSON.stringify({ id, method, params: params || {} }));
  });
}

async function findPage() {
  for (let i = 0; i < 80; i++) {
    try {
      const r = await fetch('http://127.0.0.1:' + PORT + '/json');
      const list = await r.json();
      const page = list.find((t) => t.type === 'page' && t.webSocketDebuggerUrl);
      if (page) return page;
    } catch { /* まだ立ち上がっていない */ }
    await new Promise((r) => setTimeout(r, 250));
  }
  throw new Error('Chrome の DevTools に繋がらない');
}

function done(code) {
  try { if (ws) ws.close(); } catch { /* もう閉じている */ }
  try { child.kill(); } catch { /* もう死んでいる */ }
  process.exit(code);
}

try {
  const page = await findPage();

  ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((res, rej) => {
    ws.onopen = res;
    ws.onerror = () => rej(new Error('DevTools の WebSocket に繋がらない'));
  });
  ws.onmessage = (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) {
      const p = pending.get(m.id);
      pending.delete(m.id);
      if (m.error) p.reject(new Error(m.error.message));
      else p.resolve(m.result);
    }
  };

  // ページの描画とライブ受信が始まるのを待つ。SSE を張るので load は待たない。
  await new Promise((r) => setTimeout(r, waitSec * 1000));

  // ブラウザ側のコンソールエラーを拾う（見えない不具合の手掛かり）。
  const errs = await cdp('Runtime.evaluate', {
    expression: `(function(){
      const el=document.getElementById('tankMsg');
      const beat=document.getElementById('tankBeat');
      const clock=document.getElementById('clock');
      return JSON.stringify({
        msg: el?el.textContent:null,
        beat: beat?beat.textContent:null,
        clock: clock?clock.textContent:null,
        panel: !!document.getElementById('tankPanel'),
      });
    })()`,
    returnByValue: true,
  });
  console.log('画面の状態: ' + (errs.result && errs.result.value));

  if (clickSel) {
    await cdp('Runtime.evaluate', {
      expression: `(function(){const e=document.querySelector(${JSON.stringify(clickSel)});
        if(e){e.focus();e.click();} return !!e;})()`,
      returnByValue: true,
    });
    await new Promise((r) => setTimeout(r, 800));
  }

  // 第 6 引数に JS を渡すと、撮る直前に実行する。
  // 例: カメラを霊夢の顔へ寄せる
  //   node simlab/shot.mjs face.png 12 http://127.0.0.1:8777/ "" "cam.dist=2.6;cam.ty=66.6;draw()"
  const evalJs = process.argv[6] || null;
  if (evalJs) {
    // awaitPromise: 渡された JS が async だったとき、Promise のまま返すと
    // `[object Object]` としか出ず何も確かめられない。UI の確認は「押してから
    // 読み込みを待って状態を見る」形になりがちなので、待てる方が既定として正しい。
    const r = await cdp('Runtime.evaluate', { expression: evalJs, returnByValue: true, awaitPromise: true });
    if (r.exceptionDetails) console.log('eval で例外: ' + r.exceptionDetails.text);
    else if (r.result && r.result.value !== undefined) console.log('eval → ' + r.result.value);
    await new Promise((r2) => setTimeout(r2, 1200));
  }

  const shot = await cdp('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(out, Buffer.from(shot.data, 'base64'));
  console.log('撮った: ' + out + ' (' + fs.statSync(out).size + ' bytes)');
  done(0);
} catch (e) {
  console.error('失敗: ' + e.message);
  done(1);
}
