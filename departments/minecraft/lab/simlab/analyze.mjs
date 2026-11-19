#!/usr/bin/env node
// SimLab Analyzer — トレース (JSONL) から数値を出す。
//
//   node simlab/analyze.mjs run/sim/traces            # 配下の全 arena-*.jsonl
//   node simlab/analyze.mjs run/sim/traces --json     # 機械可読
//
// 解析ロジックは純関数 (parseTrace / analyze) にしてあるので、node が使えない状況でも
// 同じ関数をそのまま別ランタイムへ貼って回せる。

import fs from 'node:fs';
import path from 'node:path';

// =============================================================================
// 純関数部 — ここに I/O を混ぜないこと
// =============================================================================

import { parseTrace, techniques, series, seriesSummary } from './stats.mjs';

// 集計の本体は stats.mjs にある。**ここで再実装しないこと** ——
// 表示用と機械用で別々に集計すると、食い違ったときにどちらが正しいか分からなくなる (AGENT-01)。
// parseTrace は既存の import 互換のために再エクスポートしている。
export { parseTrace };

const pct = (n, d) => (d > 0 ? (100 * n) / d : 0);

/** events -> 統計。トレース 1 本分。 */
export function analyze({ meta, events, broken }) {
  const spawns = new Map();      // id -> {type, role, name, w, h, maxHp}
  const gone = new Map();        // id -> tick
  const projSpawnTick = new Map();
  const projByType = new Map();
  const soundCount = new Map();
  const sectionCount = new Map();

  let lastTick = 0;
  // end イベント自身の t を除いた観測最大tick。simlab/stats.mjs の S.lastDataTick と
  // 同じ理由(コメントは下の phys 閉じ処理を参照): combat-60t.jsonl のように end.t
  // だけが実データより先へ伸びているトレースがあるため、末尾の前方フィル境界には
  // これ(lastTick ではなく)を使う。
  let lastDataTick = 0;
  let reimuId = null;
  let end = null;

  // 13-04: physは行単位デルタ化(冗長行を書かない)の対象になったので、行を数える
  // (旧実装)のではなく tick 幅で数える。dwell()(このファイルの外、stats.mjs)が
  // ai チャンネルに対して既にやっている「観測と次の観測の間を、直前の観測の状態が
  // 続いていたとみなして加算する」のと同じ手法 —— 密トレース(毎tick1行)では
  // 加算の合計が旧来の行カウントと厳密に一致し(各行がちょうど1tickぶん寄与する)、
  // デルタ化トレース(冗長行を省略)でも「省略された行の間、直前の状態が続いていた」を
  // 正しく数えられる。physPrevT/physPrevRowで直前の観測を持ち回し、次の観測が来た時点で
  // [直前tick, 今回tick) の区間を直前の状態で加算し、ループを抜けたら最後の1行ぶんを
  // 追加で閉じる(下のaddPhysSpan呼び出し、"弾の寿命"コメントの直前)。
  let physTicks = 0, notOnGround = 0, embedded = 0, noGravity = 0, airTicks = 0;
  let physPrevT = null, physPrevRow = null;
  const addPhysSpan = (fromT, toT, row) => {
    const span = toT - fromT;
    if (span <= 0 || !row) return;
    physTicks += span;
    if (row.onG === false) notOnGround += span;
    if (row.embed === true) embedded += span;
    if (row.noGrav === true) noGravity += span;
    if (row.air === true) airTicks += span;
  };
  let aiChanges = 0;
  let dmgByReimu = 0, dmgToReimu = 0, hitsByReimu = 0, hitsOnReimu = 0;
  let voidRescues = 0;
  const ttk = new Map();         // victim id -> tick at which hp hit 0
  const hpTrack = new Map();     // entity id -> last known hp (pos イベント由来)
  const dmgToVictim = new Map(); // victim id -> {sum, hits}
  const dmgBySrc = new Map();    // damage source msgId -> {sum, hits, attributed}

  for (const e of events) {
    if (typeof e.t === 'number' && e.t > lastTick) lastTick = e.t;
    if (typeof e.t === 'number' && e.t > lastDataTick && e.ch !== 'end') lastDataTick = e.t;
    switch (e.ch) {
      case 'spawn':
        spawns.set(e.id, { type: e.type, role: e.role, name: e.name, w: e.w, h: e.h, maxHp: e.maxHp });
        if (e.role === 'reimu') reimuId = e.id;
        if (e.role === 'projectile') {
          projSpawnTick.set(e.id, e.t);
          projByType.set(e.type, (projByType.get(e.type) || 0) + 1);
        }
        break;
      case 'gone':
        gone.set(e.id, e.t);
        break;
      case 'phys':
        if (physPrevRow !== null) addPhysSpan(physPrevT, e.t, physPrevRow);
        physPrevT = e.t;
        physPrevRow = e;
        break;
      case 'ai': {
        aiChanges++;
        const key = (e.section || '').slice(0, 90);
        sectionCount.set(key, (sectionCount.get(key) || 0) + 1);
        break;
      }
      case 'pos':
        if (typeof e.hp === 'number') hpTrack.set(e.id, e.hp);
        break;
      case 'dmg': {
        if (reimuId != null && e.attacker === reimuId) { dmgByReimu += e.amount; hitsByReimu++; }
        if (reimuId != null && e.victim === reimuId) { dmgToReimu += e.amount; hitsOnReimu++; }
        const v = dmgToVictim.get(e.victim) || { sum: 0, hits: 0 };
        v.sum += e.amount; v.hits++; dmgToVictim.set(e.victim, v);
        const s = dmgBySrc.get(e.src) || { sum: 0, hits: 0, attributed: 0 };
        s.sum += e.amount; s.hits++; if (e.attacker >= 0) s.attributed++;
        dmgBySrc.set(e.src, s);
        if (e.hpAfter <= 0 && !ttk.has(e.victim)) ttk.set(e.victim, e.t);
        break;
      }
      case 'sound':
        soundCount.set(e.id, (soundCount.get(e.id) || 0) + 1);
        break;
      case 'log':
        if (typeof e.msg === 'string' && e.msg.startsWith('VOID RESCUE')) voidRescues++;
        break;
      case 'end':
        end = e;
        break;
      default:
        break;
    }
  }

  // physの最後の観測ぶんを閉じる。stats.mjsのboundPhysReimuと同じ判断
  // (simlab/stats.mjsのコード内コメント参照、実測: tank/20260820/20260821-031644で
  // end不在の場合を、smoke/20260814/20260820-175211でend有効の場合を、それぞれ確認した):
  //   - reimuがgone済みなら、そのtickまでを直前の状態で埋める(死後は数えない)。
  //   - goneが無くendが有効(録画は正常に完了した)なら、trace末尾(lastDataTick、
  //     end自身のtは除く——combat-60t.jsonlのようにend.tだけが実データより先へ
  //     伸びているtruncated fixtureがあるため。lastTickを使うとこの golden が壊れる、
  //     実測して確認した)まで直前の状態が続いたとみなしてよい(13-04のデルタ化で
  //     無変化行が省かれた結果、という可能性を信頼できる根拠がendの存在そのもの)。
  //   - どちらも無ければ(録画が途中で切れた)直前の1tickぶんだけに留める
  //     (旧実装=行カウントと同じ保守的な挙動)。
  if (physPrevRow !== null) {
    let closeAt = physPrevT;
    if (reimuId != null && gone.has(reimuId)) {
      closeAt = gone.get(reimuId);
    } else if (end !== null) {
      closeAt = lastDataTick;
    }
    addPhysSpan(physPrevT, closeAt + 1, physPrevRow);
  }

  // 弾の寿命
  let lifeSum = 0, lifeN = 0;
  for (const [id, t0] of projSpawnTick) {
    const t1 = gone.has(id) ? gone.get(id) : lastTick;
    lifeSum += t1 - t0;
    lifeN++;
  }

  const projTotal = projSpawnTick.size;
  const seconds = lastTick / 20;

  return {
    techniques: techniques(events),
    series: series(events),
    scenario: meta?.scenario ?? '?',
    seed: meta?.seed ?? null,
    arena: meta?.arena ?? null,
    ticks: lastTick,
    seconds,
    brokenLines: broken,
    reimuId,
    actors: [...spawns.entries()]
      .filter(([, s]) => s.role !== 'projectile')
      .map(([id, s]) => ({ id, ...s, alive: !gone.has(id), lastHp: hpTrack.get(id) ?? null })),
    danmaku: {
      total: projTotal,
      byType: [...projByType.entries()].sort((a, b) => b[1] - a[1]),
      avgLifetimeTicks: lifeN ? lifeSum / lifeN : 0,
      hitsByReimu,
      hitRatePct: pct(hitsByReimu, projTotal),
    },
    // バランスの主指標は「ターゲットが受けた総ダメージ」。
    // 霊夢の弾幕は attacker/directEntity を持たない `magic` DamageSource で飛ぶため、
    // 「霊夢が与えた」として機械的に帰属できる分は一部しかない。
    // 推測で埋めず、帰属できた分とできなかった分を分けて出す。
    damage: {
      byVictim: [...dmgToVictim.entries()].map(([id, v]) => ({
        id,
        type: spawns.get(id)?.type ?? '?',
        role: spawns.get(id)?.role ?? '?',
        sum: v.sum,
        hits: v.hits,
        dps: seconds > 0 ? v.sum / seconds : 0,
      })).sort((a, b) => b.sum - a.sum),
      bySource: [...dmgBySrc.entries()].map(([src, s]) => ({
        src, sum: s.sum, hits: s.hits, attributed: s.attributed,
      })).sort((a, b) => b.sum - a.sum),
      attributedToReimu: dmgByReimu,
      takenByReimu: dmgToReimu,
      hitsOnReimu,
      dps: seconds > 0 ? dmgByReimu / seconds : 0,
      ttk: [...ttk.entries()].map(([id, t]) => ({ id, tick: t, sec: t / 20 })),
    },
    ai: {
      changes: aiChanges,
      airTicks,
      groundTicks: physTicks - airTicks,
      airPct: pct(airTicks, physTicks),
      topSections: [...sectionCount.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8),
    },
    // 見た目バグ (浮き / めり込み) の数値検出。ヘッドレスに描画は無いが、
    // extra43 / extra93 の判例はどちらも最終的にこの手の数値で確定している。
    phys: {
      sampled: physTicks,
      notOnGround, notOnGroundPct: pct(notOnGround, physTicks),
      embedded, embeddedPct: pct(embedded, physTicks),
      noGravity, noGravityPct: pct(noGravity, physTicks),
      voidRescues,
    },
    sound: {
      total: [...soundCount.values()].reduce((a, b) => a + b, 0),
      byId: [...soundCount.entries()].sort((a, b) => b[1] - a[1]),
    },
    end,
  };
}

// =============================================================================
// 表示
// =============================================================================

const n = (v, d = 1) => (v == null || Number.isNaN(v) ? '-' : v.toFixed(d));
const pad = (s, w) => String(s).padEnd(w);
const rpad = (s, w) => String(s).padStart(w);

function report(r, file) {
  const L = [];
  L.push(`\n\x1b[1m${path.basename(file)}\x1b[0m  —  ${r.scenario} / seed ${r.seed} / arena ${r.arena}`);
  L.push(`  ${r.ticks} ticks (${n(r.seconds)}s)` + (r.brokenLines ? `  \x1b[31m${r.brokenLines} broken lines\x1b[0m` : ''));

  L.push(`\n  \x1b[36mACTORS\x1b[0m`);
  for (const a of r.actors) {
    const hp = a.lastHp != null ? `hp ${n(a.lastHp)}/${n(a.maxHp)}` : (a.maxHp != null ? `hp ?/${n(a.maxHp)}` : '');
    L.push(`    #${pad(a.id, 5)} ${pad(a.type, 34)} ${pad(a.role, 11)} ${pad(hp, 18)} ${a.alive ? 'alive' : 'gone'}`);
  }

  // TECHNIQUES — 技(phase)ごとの発動回数と再発間隔 (MEAS-01)。
  // **r.techniques をそのまま並べるだけ。ここで再集計しない** (AGENT-01)。
  if (r.techniques && r.techniques.length) {
    L.push(`\n  \x1b[36mTECHNIQUES\x1b[0m`);
    L.push(`    ${pad('phase', 24)} ${rpad('回数', 5)} ${rpad('間隔', 8)} ${rpad('滞在t', 7)} ${rpad('滞在%', 7)} ${rpad('発射', 5)} ${rpad('命中', 5)} ${rpad('命中率', 8)} ${rpad('与ダメ', 8)}`);
    for (const t of r.techniques) {
      const iv = t.intervalMedianTicks == null ? '-' : `${t.intervalMedianTicks}t`;
      // 撃っていない技の命中率は「無い」のであって「0%」ではない
      const hr = t.hitRatePct == null ? '-' : `${t.hitRatePct}%`;
      const dp = t.dwellPct == null ? '-' : `${t.dwellPct}%`;
      L.push(`    ${pad(t.phase, 24)} ${rpad(t.count, 5)} ${rpad(iv, 8)} ${rpad(t.dwellTicks, 7)} ${rpad(dp, 7)} ${rpad(t.shots, 5)} ${rpad(t.hits, 5)} ${rpad(hr, 8)} ${rpad(n(t.dmgSum), 8)}`);
    }
    // 帰属できなかった分は**隠さない**。命中率の分母から漏れている量が見えないと、
    // 表の数字が実際より正確に見えてしまう。
    const u = r.techniques[0];
    if (u && u.unattributedHits) {
      L.push(`    \x1b[33m! 技へ帰属できなかった被弾 ${u.unattributedHits} 件 / ${n(u.unattributedDmg)} ダメージ\x1b[0m`);
      L.push(`      （attacker も direct も持たない magic ソース。上の命中率はこの分を含まない）`);
    }
  }

  // SERIES —— 900要素×十数本は読めないので、各レーンの min/max/last だけ出す。
  // **要約も同じ r.series から計算する。別集計にしない** (AGENT-01)。
  if (r.series) {
    L.push(`\n  \x1b[36mSERIES\x1b[0m  (tick 軸の系列。全量は --json で)`);
    for (const row of seriesSummary(r.series)) {
      if (row.kinds !== undefined) {
        L.push(`    ${pad(row.lane, 10)} 種類 ${rpad(row.kinds, 4)}  last ${row.last ?? '-'}`);
      } else {
        L.push(`    ${pad(row.lane, 10)} min ${rpad(n(row.min, 2), 9)} max ${rpad(n(row.max, 2), 9)} last ${rpad(n(row.last, 2), 9)}`);
      }
    }
  }

  const d = r.danmaku;
  L.push(`\n  \x1b[36mDANMAKU\x1b[0m`);
  L.push(`    projectiles spawned   ${rpad(d.total, 8)}`);
  for (const [t, c] of d.byType.slice(0, 10)) L.push(`      ${pad(t, 44)} ${rpad(c, 6)}`);
  L.push(`    avg lifetime          ${rpad(n(d.avgLifetimeTicks), 8)} ticks`);
  L.push(`    hits by reimu         ${rpad(d.hitsByReimu, 8)}`);
  L.push(`    hits / projectile     ${rpad(n(d.hitRatePct), 8)} %`);

  const g = r.damage;
  L.push(`\n  \x1b[36mDAMAGE\x1b[0m`);
  for (const v of g.byVictim) {
    L.push(`    -> #${pad(v.id, 4)} ${pad(v.role, 10)} ${rpad(n(v.sum), 8)}  ${rpad(v.hits, 4)} hits  ${n(v.dps, 2)} dps`);
  }
  if (g.bySource.length) {
    L.push(`    by damage source`);
    for (const s of g.bySource) {
      const attr = s.attributed === s.hits ? '' :
        `  \x1b[2m(${s.hits - s.attributed}/${s.hits} に攻撃者情報なし)\x1b[0m`;
      L.push(`      ${pad(s.src, 14)} ${rpad(n(s.sum), 8)}  ${rpad(s.hits, 4)} hits${attr}`);
    }
  }
  L.push(`    taken by reimu        ${rpad(n(g.takenByReimu), 8)}   (${g.hitsOnReimu} hits)`);
  L.push(`    kills (ttk)           ${g.ttk.length ? g.ttk.map((k) => `#${k.id}@${n(k.sec)}s`).join(', ') : 'none'}`);

  const a = r.ai;
  L.push(`\n  \x1b[36mAI\x1b[0m`);
  L.push(`    decision changes      ${rpad(a.changes, 8)}`);
  L.push(`    ground / air ticks    ${rpad(a.groundTicks, 8)} / ${a.airTicks}  (air ${n(a.airPct)} %)`);
  if (a.topSections.length) {
    L.push(`    most frequent decisions`);
    for (const [s, c] of a.topSections) L.push(`      ${rpad(c + 'x', 6)} ${s || '(empty)'}`);
  }

  const p = r.phys;
  L.push(`\n  \x1b[36mPHYS\x1b[0m  \x1b[2m(見た目バグの数値検出)\x1b[0m`);
  L.push(`    samples               ${rpad(p.sampled, 8)}`);
  L.push(`    onGround=false        ${rpad(p.notOnGround, 8)}   ${n(p.notOnGroundPct)} %`);
  L.push(`    embedded in block     ${rpad(p.embedded, 8)}   ${n(p.embeddedPct)} %`);
  L.push(`    noGravity=true        ${rpad(p.noGravity, 8)}   ${n(p.noGravityPct)} %`);
  if (p.voidRescues) L.push(`    \x1b[31mvoid rescues          ${rpad(p.voidRescues, 8)}   <- 場外落下。床が狭い可能性\x1b[0m`);

  L.push(`\n  \x1b[36mSOUND\x1b[0m   ${r.sound.total} total`);
  for (const [id, c] of r.sound.byId.slice(0, 12)) L.push(`      ${rpad(c + 'x', 6)} ${id}`);

  if (r.end) L.push(`\n  end: ${r.end.reason}`);
  return L.join('\n');
}

// =============================================================================
// CLI
// =============================================================================

function findTraces(root) {
  const out = [];
  const walk = (p) => {
    let st;
    try { st = fs.statSync(p); } catch { return; }
    if (st.isDirectory()) {
      for (const f of fs.readdirSync(p)) walk(path.join(p, f));
    } else if (p.endsWith('.jsonl')) {
      out.push(p);
    }
  };
  walk(root);
  return out.sort();
}

const isMain = process.argv[1] && import.meta.url.endsWith(path.basename(process.argv[1]));
if (isMain) {
  const args = process.argv.slice(2);
  const asJson = args.includes('--json');
  const root = args.find((a) => !a.startsWith('--')) ?? 'run/sim/traces';

  const files = findTraces(root);
  if (!files.length) {
    console.error(`no .jsonl traces under ${root}`);
    console.error(`hint: run \`gradlew runSim\` first`);
    process.exit(1);
  }

  const results = files.map((f) => ({ file: f, r: analyze(parseTrace(fs.readFileSync(f, 'utf8'))) }));

  if (asJson) {
    console.log(JSON.stringify(results, null, 2));
  } else {
    for (const { file, r } of results) console.log(report(r, file));
    if (results.length > 1) {
      const tot = results.reduce((acc, { r }) => {
        acc.proj += r.danmaku.total;
        acc.dmg += r.damage.byVictim.filter((v) => v.role === 'target').reduce((a, v) => a + v.sum, 0);
        acc.sec += r.seconds;
        return acc;
      }, { proj: 0, dmg: 0, sec: 0 });
      const nA = results.length;
      console.log(`\n\x1b[1mACROSS ${nA} ARENAS\x1b[0m  projectiles ${tot.proj} (avg ${n(tot.proj / nA)})`
        + `  dmg to targets ${n(tot.dmg)} (avg ${n(tot.dmg / nA)}, ${n(tot.dmg / tot.sec, 2)} dps)`);
    }
    console.log('');
  }
}
