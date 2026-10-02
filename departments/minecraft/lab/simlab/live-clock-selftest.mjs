// ライブの時計(clock recovery)の自己検査。**ブラウザを立てずに制御則だけを回す。**
//
// なぜ要るか: にーくら 2026-08-23「まだ残像が残ってる／実機の感覚には程遠い」の真因は
// 「固定 20tick/秒 で消費し、データの先端で凍る」ことだった。凍る→溜まる→一気に進む
// という弛張発振で、静止フレームの割合は理論上 `1 − TPS/20`。
// **平均 fps ではこの欠陥が見えない**(60fps のまま画が止まる)ので、
// 「止まったフレームの割合」と「1フレームあたり再生速度の分布」で測る。
//   直っている = 分布が単峰 (送り手の速さの周り)
//   壊れている = 分布が二峰 (0 と 20 に山)
//
// index.html から時計の実装をそのまま切り出して回すので、**本番のコードを測っている**
// (写した式を測っているのではない)。
//
//   node simlab/live-clock-selftest.mjs

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const HTML = fs.readFileSync(path.join(HERE, 'viewer', 'index.html'), 'utf8');

// --- index.html から時計の実装を切り出す -------------------------------------
const START = HTML.indexOf('const lcClamp=');
const ENDMARK = '\nrequestAnimationFrame(loop);';
const END = HTML.indexOf(ENDMARK, START);
if (START < 0 || END < 0) {
  console.error('live-clock-selftest: index.html から時計の実装を切り出せない。');
  console.error('  目印: "const lcClamp=" と "requestAnimationFrame(loop);"');
  process.exit(2);
}
const SRC = HTML.slice(START, END + ENDMARK.length);

/** 切り出した時計を、外の世界を全部偽物にして動かせる形で返す。 */
function makeClock() {
  const D = { maxTick: 0, nTicks: 1 };
  const T = { tick: 0, playing: true, speed: 1, acc: 0, partial: 0, last: 0,
              followLive: true };
  const said = [];
  const factory = new Function(
    'D', 'T', 'liveOpen', 'playSounds', 'syncPlayBtn', 'draw', 'perfTick',
    'tankSay', 'requestAnimationFrame', 'performance',
    SRC + '\nreturn { LIVE_CLOCK, loop, liveBrake };');
  const api = factory(
    D, T, () => true, () => {}, () => {}, () => {}, () => {},
    (m) => said.push(m), () => {}, { now: () => 0 });
  return { D, T, said, ...api };
}

/** 旧実装(固定 20tick/秒 + 飽和リミッタ)。比較用にここへ写す。 */
function oldStep(D, T, dtMs) {
  T.acc += dtMs * (20 * T.speed) / 1000;
  const LIVE_LAG = 2;
  const limit = Math.max(0, D.maxTick - LIVE_LAG);
  const before = T.tick + T.partial;
  while (T.acc >= 1) {
    T.acc -= 1;
    if (T.tick < limit) T.tick++;
    else { T.acc = Math.min(T.acc, 0.999); break; }
  }
  T.partial = (T.tick < D.maxTick) ? Math.max(0, T.acc) : 0;
  return (T.tick + T.partial) - before;
}

/**
 * 1 本回す。
 * @param plan  経過秒 -> その瞬間の送り手の速さ [tick/秒] を返す関数
 */
function run(name, plan, seconds, useNew) {
  const FRAME = 1000 / 60;        // 60fps で描く
  const DELIVER = 50;             // 取り込みは 50ms 刻み (= Minecraft の 1 tick)
  const c = useNew ? makeClock() : null;
  const D = useNew ? c.D : { maxTick: 0, nTicks: 1 };
  const T = useNew ? c.T : { tick: 0, playing: true, speed: 1, acc: 0, partial: 0, last: 0, followLive: true };
  // 送り手: 実数で溜めて、50ms ごとに整数ぶんだけ maxTick へ渡す(粒を作る)
  let produced = 0, pending = 0, nextDeliver = DELIVER;
  let now = 0, lastAt = 0;
  const rates = [];
  const settled = [];   // 落ち着いてからの分。段差の直後を「ばらつき」に数えない
  let stopped = 0, frames = 0, back = 0;
  // 先に少し流しておく(起動直後の空っぽを測らない)
  const WARM = 3000;

  while (now < (seconds * 1000 + WARM)) {
    now += FRAME;
    const t = Math.max(0, (now - WARM) / 1000);
    const src = plan(t);
    produced += src * FRAME / 1000;
    if (now >= nextDeliver) {
      nextDeliver += DELIVER;
      const whole = Math.floor(produced) - pending;
      if (whole > 0) { pending += whole; D.maxTick += whole; D.nTicks = D.maxTick + 1; }
    }
    const before = T.tick + T.partial;
    if (useNew) { T.last = lastAt; c.loop(now); }
    else oldStep(D, T, now - lastAt);
    lastAt = now;
    if (now < WARM) continue;
    const adv = (T.tick + T.partial) - before;
    const rate = adv * 1000 / FRAME;
    rates.push(rate);
    if (t > seconds * 0.6) settled.push(rate);
    frames++;
    if (rate < 1) stopped++;
    if (rate < -0.5) back++;
  }
  rates.sort((a, b) => a - b);
  const sm = settled.reduce((a,b)=>a+b,0)/(settled.length||1);
  const ssd = Math.sqrt(settled.reduce((a,b)=>a+(b-sm)**2,0)/(settled.length||1));
  const mean = rates.reduce((a, b) => a + b, 0) / (rates.length || 1);
  const sd = Math.sqrt(rates.reduce((a, b) => a + (b - mean) ** 2, 0) / (rates.length || 1));
  const s = useNew ? c.LIVE_CLOCK.s : null;
  return {
    name, useNew,
    stoppedPct: 100 * stopped / (frames || 1),
    backPct: 100 * back / (frames || 1),
    scv: sm > 0 ? ssd / sm : 0,
    mean, sd, cv: mean > 0 ? sd / mean : 0,
    p05: rates[Math.floor(rates.length * 0.05)] || 0,
    p95: rates[Math.floor(rates.length * 0.95)] || 0,
    lag: s ? s.lagRaw : (D.maxTick - (T.tick + T.partial)),
    target: s ? s.target : 2,
    est: s ? s.rate : 20,
    floor: s ? s.floorTouches : 0,
    snaps: s ? s.snaps : 0,
    trimOut: s ? null : null,
    said: useNew ? c.said : [],
  };
}

const F = (v, n = 1) => (v === null || v === undefined ? '—' : v.toFixed(n));
function row(r) {
  return [r.name.padEnd(26), (r.useNew ? '新' : '旧'),
    ('静止 ' + F(r.stoppedPct, 1) + '%').padStart(11),
    ('逆走 ' + F(r.backPct, 1) + '%').padStart(11),
    ('速さ ' + F(r.mean, 1) + '±' + F(r.sd, 1)).padStart(18),
    ('5-95% ' + F(r.p05, 1) + '〜' + F(r.p95, 1)).padStart(20),
    ('遅れ ' + F(r.lag, 1) + '/' + F(r.target, 1)).padStart(16),
    ('推定 ' + F(r.est, 1)).padStart(11),
    ('底 ' + r.floor + ' 飛 ' + r.snaps).padStart(10),
  ].join(' ');
}

const CASES = [
  ['20 TPS (混んでいない)', () => 20, 40],
  ['13 TPS (戦闘中)', () => 13, 40],
  ['5 TPS (かなり重い)', () => 5, 40],
  ['20→10 の段差', (t) => (t < 20 ? 20 : 10), 40],
  ['18±3 の揺らぎ', (t) => 18 + 3 * Math.sin(t * 1.7), 40],
  ['3 秒止まって再開', (t) => (t > 10 && t < 13 ? 0 : 18), 40],
];

console.log('ライブの時計 自己検査 —— 「止まったフレームの割合」が唯一の指標\n');
console.log('  静止 = 再生が 1tick/秒 未満だったフレームの割合（旧実装の理論値は 1−TPS/20）');
console.log('  速さ = 1 フレームあたりの再生速度 [tick/秒] の平均±標準偏差');
console.log('         二峰（0 と 20 に山）だと sd が大きく出る。単峰なら小さい\n');

const results = [];
let fail = 0;
for (const [name, plan, sec] of CASES) {
  const oldR = run(name, plan, sec, false);
  const newR = run(name, plan, sec, true);
  results.push(oldR, newR);
  console.log(row(oldR));
  console.log(row(newR));
  console.log('');
  // --- 合否 -----------------------------------------------------------------
  // 止まって当然の「3 秒止まって再開」以外は、静止 0.5% 未満を要求する。
  const mayStop = name.includes('止まって');
  if (!mayStop && newR.stoppedPct >= 0.5) {
    console.log('  × ' + name + ': 静止フレームが ' + F(newR.stoppedPct, 2) + '% (< 0.5% を期待)');
    fail++;
  }
  // 送り手の速さに追随できているか(遅れが発散していないこと)。
  if (newR.lag > 30) { console.log('  × ' + name + ': 遅れが ' + F(newR.lag, 1) + ' tick まで開いた'); fail++; }
  // 揺れを追いかけていないこと。CV が大きいのは「速さがふらついている」の意。
  if (!mayStop && newR.scv > 0.12) {
    console.log('  × ' + name + ': 再生速度のばらつきが CV=' + F(newR.scv, 3) + ' (0.12 以下を期待)');
    fail++;
  }
}

// 旧実装の欠陥の形を確かめる。**凍るのではなく「逆走する」**のが実態だった ——
// 天井に当たると acc を 1 減らしてから T.tick を進めないので、tick+partial が
// 約 1tick 分だけ**戻る**。13TPS なら毎秒 20-13=7 回、60fps のフレームの 11.7%。
// 動くモブが 7回/秒 だけ後ろへ跳ぶ = にーくらの「動くモブが二重に見える」。
const bimodal = run('13 TPS', () => 13, 40, false);
const expectBack = 100 * (20 - 13) / 60;
console.log('前提の確認: 旧実装 @13TPS の逆走フレーム = ' + F(bimodal.backPct, 1)
  + '%（理論値 ' + F(expectBack, 1) + '% = 毎秒 20-13=7 回の巻き戻し）');
if (Math.abs(bimodal.backPct - expectBack) > 3) {
  console.log('  × 旧実装の測定が理論値と合わない —— この検査自体を疑うこと');
  fail++;
}

console.log('\nfailures: ' + fail);
console.log('live-clock-selftest: ' + (fail ? 'FAILED' : 'OK'));
process.exit(fail ? 1 : 0);
