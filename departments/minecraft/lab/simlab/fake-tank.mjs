// **偽の水槽。** 既に録った記録を、指定した TPS で「今 走っているもの」として流す。
//
// なぜ要るか: ライブの時計(clock recovery)は「送り手が 20TPS を割ったとき」に効く
// 仕掛けだが、本物の水槽に好きな TPS を出させることはできない。記録を任意の速さで
// 流し直せば、serve.mjs の SSE も id も再開も**本物のまま**で、送り手の速さだけを
// こちらが決められる。
//
// 心拍(heartbeat.json)を書くので serve.mjs は「水槽が走っている」と見なす。
// 終わったら元の心拍に戻す —— にーくらの本物の記録を壊さない。
//
//   node simlab/fake-tank.mjs --rate=13 --seconds=40 [--from=940]
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.dirname(HERE);
const TRACES = path.join(ROOT, 'run', 'sim', 'traces');
const HB = path.join(TRACES, 'heartbeat.json');

const arg = (k, d) => {
  const m = process.argv.find((a) => a.startsWith('--' + k + '='));
  return m ? m.slice(k.length + 3) : d;
};
const RATE = Number(arg('rate', 13));
const SECONDS = Number(arg('seconds', 40));
const FROM = Number(arg('from', 0));
const LOOP = arg('loop', '0') !== '0';
// --marks=1 で「新しい jar が出すはずの ch:tick」を無音の tick へ挿す。
// 古い記録のまま新しい挙動を試すため(SimArena.TICK_MARK_EVERY と同じ 2 tick 刻み)。
const MARKS = arg('marks', '0') !== '0';   // 記録を使い切ったら tick と id をずらして繰り返す
const SRC = arg('src', path.join(TRACES, 'tank', '20260820', '20260823-010522', 'arena-0.jsonl'));

if (!fs.existsSync(SRC)) { console.error('元の記録が無い: ' + SRC); process.exit(2); }

// 元の記録を tick ごとにまとめる。meta 行(t が無いもの)は先頭に置く。
const head = [], byTick = new Map();
for (const line of fs.readFileSync(SRC, 'utf8').split('\n')) {
  if (!line.trim()) continue;
  let o; try { o = JSON.parse(line); } catch { continue; }
  if (typeof o.t !== 'number') { head.push(line); continue; }
  if (o.t < FROM) { if (o.ch === 'meta' || o.ch === 'spawn') head.push(line); continue; }
  if (!byTick.has(o.t)) byTick.set(o.t, []);
  byTick.get(o.t).push(line);
}
if (MARKS) {
  // 行の無い tick を 2 tick おきに埋める。中身は t と ch だけ。
  const have = byTick;
  const all = [...have.keys()].sort((a, b) => a - b);
  const lo = all[0], hi = all[all.length - 1];
  let lastSeen = lo;
  for (let t = lo; t <= hi; t++) {
    if (have.has(t)) { lastSeen = t; continue; }
    if (t - lastSeen >= 2) { have.set(t, [JSON.stringify({ t: t, ch: 'tick' })]); lastSeen = t; }
  }
}
const ticks = [...byTick.keys()].sort((a, b) => a - b);
if (!ticks.length) { console.error('流す行が無い'); process.exit(2); }

const RUN = 'faketank/' + new Date().toISOString().replace(/[^0-9]/g, '').slice(0, 14);
const dir = path.join(TRACES, RUN);
fs.mkdirSync(dir, { recursive: true });
const file = path.join(dir, 'arena-0.jsonl');
const out = fs.createWriteStream(file, { flags: 'w' });
for (const l of head) out.write(l + '\n');

const hbBackup = fs.existsSync(HB) ? fs.readFileSync(HB) : null;
const restore = () => { try { if (hbBackup) fs.writeFileSync(HB, hbBackup); else fs.unlinkSync(HB); } catch {} };
process.on('exit', restore);
process.on('SIGINT', () => { restore(); process.exit(130); });
process.on('SIGTERM', () => { restore(); process.exit(143); });

console.log('偽の水槽: ' + RATE + ' tick/秒 で ' + SECONDS + ' 秒 —— ' + RUN);
console.log('  元の記録: ' + path.relative(ROOT, SRC) + '  (tick ' + ticks[0] + '〜' + ticks[ticks.length - 1] + ')');

const t0 = Date.now();
let idx = 0, emitted = 0, tickShift = 0, idShift = 0;
const PUMP = 50;                       // 50ms = Minecraft の 1 tick。本物の flush と同じ刻み
const timer = setInterval(() => {
  const el = (Date.now() - t0) / 1000;
  if (el > SECONDS || (idx >= ticks.length && !LOOP)) {
    clearInterval(timer); out.end();
    console.log('偽の水槽: 終わり —— ' + emitted + ' tick 流した ('
      + (emitted / el).toFixed(1) + ' tick/秒 実測)');
    restore();
    process.exit(0);
  }
  const want = Math.floor(el * RATE);
  while (emitted < want && (idx < ticks.length || LOOP)) {
    if (idx >= ticks.length) {
      // **記録を使い切ったら、ずらして繰り返す。** 履歴の窓(2分)や 30 分の定常状態は
      // 45 秒の記録では試せない。tick は必ず前へ、id もずらして衝突させない。
      tickShift += (ticks[ticks.length - 1] - ticks[0]) + 1;
      idShift += 100000;
      idx = 0;
    }
    for (const l of byTick.get(ticks[idx])) {
      if (tickShift === 0) { out.write(l + String.fromCharCode(10)); continue; }
      let o; try { o = JSON.parse(l); } catch { continue; }
      o.t += tickShift;
      for (const k of ['id', 'victim', 'attacker', 'direct']) if (typeof o[k] === 'number' && o[k] >= 0) o[k] += idShift;
      out.write(JSON.stringify(o) + String.fromCharCode(10));
    }
    idx++; emitted++;
  }
  fs.writeFileSync(HB, JSON.stringify({
    tick: ticks[Math.min(idx, ticks.length - 1)] + tickShift, scenario: 'tank',
    trace: RUN, startedAtMs: t0, atMs: Date.now(),
  }));
}, PUMP);
