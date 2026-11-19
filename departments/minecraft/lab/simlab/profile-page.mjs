// Viewer の CPU プロファイルを取る。**「重い」を推測で潰さないための道具。**
//
// にーくら 2026-08-23:「やっぱり fps は下がるね。描画の重さも関係してる？」
//
// perf 行は draw と取り込みしか測っていない。1 フレーム 34ms のうち draw 11ms、
// 取り込み 4ms —— **残り 19ms がどこへ行っているか、画面のどの数字にも出ていない**。
// DOM の組み直し(tankWho / renderAiLog / updateHud)はどちらの計測にも入らないので、
// 「測っていないものは無い」ことになってしまう。V8 のプロファイラなら全部の関数に
// 自己時間が付くので、名指しできる。
//
//   node simlab/profile-page.mjs [URL] [測る秒数]
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const url = process.argv[2] || 'http://127.0.0.1:8777/';
const sec = Number(process.argv[3] || 20);
const warm = Number(process.argv[4] || 12);
const CHROME = ['C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Microsoft/Edge/Application/msedge.exe'].find((p) => fs.existsSync(p));
if (!CHROME) { console.error('Chrome も Edge も見つからない'); process.exit(1); }

const PORT = 9335;
const child = spawn(CHROME, ['--headless=new', '--enable-unsafe-swiftshader',
  '--use-gl=angle', '--use-angle=swiftshader', '--hide-scrollbars',
  '--window-size=1840,900', '--remote-debugging-port=' + PORT,
  '--user-data-dir=' + path.join(os.tmpdir(), 'simlab-prof-profile'),
  '--no-first-run', '--no-default-browser-check', url],
  { stdio: 'ignore', windowsHide: true });

let ws = null, msgId = 0;
const pending = new Map();
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

/** プロファイルを「自己時間の多い関数」に畳む。呼ばれた場所も 1 つ添える。 */
function fold(profile) {
  const byId = new Map();
  for (const n of profile.nodes) byId.set(n.id, n);
  const self = new Map();          // key -> {ms, node}
  const total = (profile.endTime - profile.startTime) / 1000;   // us -> ms
  // timeDeltas は samples と 1 対 1。サンプルの居た node に自己時間を足す。
  const acc = new Map();
  for (let i = 0; i < profile.samples.length; i++) {
    const id = profile.samples[i], dt = profile.timeDeltas[i] || 0;
    acc.set(id, (acc.get(id) || 0) + dt);
  }
  for (const [id, us] of acc) {
    const n = byId.get(id); if (!n) continue;
    const f = n.callFrame;
    const file = (f.url || '').split('/').pop() || '(なし)';
    const key = (f.functionName || '(無名)') + '  ' + file + ':' + (f.lineNumber + 1);
    const cur = self.get(key) || { ms: 0 };
    cur.ms += us / 1000;
    self.set(key, cur);
  }
  const rows = [...self.entries()].map(([k, v]) => ({ k, ms: v.ms }))
    .sort((a, b) => b.ms - a.ms);
  return { rows, totalMs: total };
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
    }
  };
  await cdp('Runtime.enable');
  await cdp('Profiler.enable');
  // **温めながら 30 秒ごとに数える。** 「多くのモブと戦った後に重くなる」を捕まえるには、
  // 重くなる前と後の両方が要る —— プロファイルだけでは「何が増えたか」が判らない。
  const SAMPLE_MS = 30000;
  const SAMPLE_EXPR = 'JSON.stringify({'
    + 'fps:Math.round(T.fps||0), draw:+(T.drawMs||0).toFixed(1), worst:Math.round(T.worstMs||0),'
    + 'ingest:+(T.ingestMs||0).toFixed(1), maxTick:D.maxTick, held:D.maxTick-(D.minTick||0)+1,'
    + 'trims:T.trims||0, ents:D.entities.size, lanes:D.store.stats.changePoints,'
    + 'storeMB:+(D.store.stats.bytes/1e6).toFixed(2),'
    + 'walkMB:(window.SimGL&&SimGL.derivedStats)?+((SimGL.derivedStats().walkBytes||0)/1e6).toFixed(2):0,'
    + 'animTicks:(window.SimGL&&SimGL.derivedStats)?SimGL.derivedStats().animTicks:0,'
    + 'seriesLen:(D.series&&D.series.dist)?D.series.dist.length:0,'
    + 'dom:document.getElementsByTagName("*").length,'
    + 'drawn:(function(){var f=D.frameAt(T.tick,T.partial);return f?f.pos.size:0;})(),'
    + 'bullets:(function(){var n=0,f=D.frameAt(T.tick,T.partial);if(f)for(var kv of f.pos){var e=D.entities.get(kv[0]);if(e&&e.role==="projectile")n++;}return n;})(),'
    + 'heapMB:performance.memory?+(performance.memory.usedJSHeapSize/1e6).toFixed(1):null'
    + '})';
  const samples = [];
  console.log('温めながら数えている（' + warm + ' 秒、30 秒ごと）…');
  for (let waited = 0; waited < warm * 1000; waited += SAMPLE_MS) {
    await new Promise((r) => setTimeout(r, Math.min(SAMPLE_MS, warm * 1000 - waited)));
    try {
      const v = JSON.parse((await cdp('Runtime.evaluate', { expression: SAMPLE_EXPR, returnByValue: true })).result.value);
      v.t = Math.round((waited + SAMPLE_MS) / 1000);
      samples.push(v);
      console.log('  ' + String(v.t).padStart(4) + 's  fps ' + String(v.fps).padStart(3)
        + '  draw ' + String(v.draw).padStart(5) + 'ms  最長 ' + String(v.worst).padStart(4) + 'ms'
        + '  描いた ' + String(v.drawn).padStart(3) + '(弾 ' + String(v.bullets).padStart(3) + ')'
        + '  保持 ' + String(v.held).padStart(5) + '  切 ' + String(v.trims).padStart(2)
        + '  store ' + String(v.storeMB).padStart(5) + 'MB  walk ' + String(v.walkMB).padStart(4) + 'MB'
        + '  series ' + String(v.seriesLen).padStart(6) + '  DOM ' + String(v.dom).padStart(5)
        + '  heap ' + String(v.heapMB).padStart(6) + 'MB');
    } catch (e) { console.log('  (標本が取れなかった: ' + e.message + ')'); }
  }
  await cdp('Profiler.setSamplingInterval', { interval: 200 });   // 0.2ms 刻み
  await cdp('Profiler.start');
  console.log('測っている（' + sec + ' 秒）…');
  await new Promise((r) => setTimeout(r, sec * 1000));
  const { profile } = await cdp('Profiler.stop');

  const st = JSON.parse((await cdp('Runtime.evaluate', {
    expression: `JSON.stringify({fps:T.fps,drawMs:T.drawMs,worst:T.worstMs,ingest:T.ingestMs,
      ents:D.entities.size,maxTick:D.maxTick,minTick:D.minTick,trims:T.trims||0,
      bullets:(function(){let n=0;const f=D.frameAt(T.tick,T.partial);if(f)for(const[id]of f.pos){const e=D.entities.get(id);if(e&&e.role==='projectile')n++;}return n;})(),
      drawn:(function(){const f=D.frameAt(T.tick,T.partial);return f?f.pos.size:0;})()})`,
    returnByValue: true,
  })).result.value);

  const { rows, totalMs } = fold(profile);
  if (samples.length >= 2) {
    const a = samples[0], b = samples[samples.length - 1], dtMin = (b.t - a.t) / 60;
    const sl = (k) => (dtMin > 0 ? ((b[k] - a[k]) / dtMin).toFixed(1) : '-');
    console.log('');
    console.log('1 分あたりの伸び: store ' + sl('storeMB') + 'MB  walk ' + sl('walkMB')
      + 'MB  series ' + sl('seriesLen') + '  DOM ' + sl('dom') + '  heap ' + sl('heapMB') + 'MB'
      + '   fps ' + a.fps + ' -> ' + b.fps);
  }
  console.log('\n画面の状態: ' + JSON.stringify(st));
  console.log('プロファイル ' + Math.round(totalMs) + 'ms 分\n');
  console.log('自己時間の多い順（上位 18）');
  console.log('   %      ms   関数');
  let shown = 0;
  for (const r of rows) {
    if (r.ms < totalMs * 0.005) break;
    console.log(('' + (100 * r.ms / totalMs).toFixed(1)).padStart(5) + '  '
      + ('' + Math.round(r.ms)).padStart(6) + '   ' + r.k);
    if (++shown >= 18) break;
  }
  const idle = rows.find((r) => r.k.startsWith('(idle)') || r.k.startsWith('(program)'));
  console.log('\n（(idle) は待っている時間。これが大きいなら CPU ではなく別の何かで詰まっている）');
  done(0);
} catch (e) {
  console.error('profile-page: ' + (e && e.message || e));
  done(1);
}
