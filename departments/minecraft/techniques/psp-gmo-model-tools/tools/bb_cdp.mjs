// Blockbench(Electron)に CDP で接続して JS を評価する小道具。
// 使い方: node bb_cdp.mjs <port> <評価するjsファイル> [結果を書くjsonファイル] [--screenshot out.png]
// 評価するjsは「式」または async 関数本体ではなく、最後の式の値を返す（awaitPromise=true）。
import fs from 'node:fs';

const [port, jsFile, outFile] = process.argv.slice(2);
const shotIdx = process.argv.indexOf('--screenshot');
const shot = shotIdx > 0 ? process.argv[shotIdx + 1] : null;

async function findTarget() {
  for (let i = 0; i < 240; i++) {
    try {
      const all = await (await fetch(`http://127.0.0.1:${port}/json`, { signal: AbortSignal.timeout(2000) })).json();
      const t = all.filter(x => x.type === 'page' && x.webSocketDebuggerUrl && /index\.html$/.test(new URL(x.url).pathname));
      if (t.length === 1) return t[0];
    } catch (_) {}
    await new Promise(r => setTimeout(r, 500));
  }
  throw new Error('Blockbench のデバッグ対象が見つからない');
}

const target = await findTarget();
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = () => rej(new Error('ws error')); });
let seq = 0;
const pending = new Map();
ws.onmessage = ev => {
  const m = JSON.parse(String(ev.data));
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
};
const send = (method, params = {}) => new Promise((res, rej) => {
  const id = ++seq;
  const t = setTimeout(() => { pending.delete(id); rej(new Error('timeout ' + method)); }, Number(process.env.BB_TIMEOUT_MS || 120000));
  pending.set(id, m => { clearTimeout(t); m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result); });
  ws.send(JSON.stringify({ id, method, params }));
});

await send('Runtime.enable');
for (let i = 0; i < 240; i++) {
  const r = await send('Runtime.evaluate', {
    expression: `typeof Blockbench!=='undefined' && Blockbench.setup_successful===true && typeof Preview!=='undefined' && !!Preview.selected`,
    returnByValue: true });
  if (r.result.value === true) break;
  await new Promise(r => setTimeout(r, 500));
}
const code = fs.readFileSync(jsFile, 'utf8');
const r = await send('Runtime.evaluate', { expression: code, awaitPromise: true, returnByValue: true });
if (r.exceptionDetails) {
  console.error('JS例外:', JSON.stringify(r.exceptionDetails.exception?.description || r.exceptionDetails.text).slice(0, 2000));
  process.exitCode = 2;
} else {
  const v = r.result.value;
  const text = typeof v === 'string' ? v : JSON.stringify(v, null, 1);
  if (outFile && !outFile.startsWith('--')) fs.writeFileSync(outFile, text ?? '');
  console.log((text ?? '').slice(0, 1500));
}
if (shot) {
  await new Promise(r => setTimeout(r, 1500));
  const s = await send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(shot, Buffer.from(s.data, 'base64'));
  console.log('screenshot ->', shot);
}
ws.close();
process.exit(process.exitCode ?? 0);
