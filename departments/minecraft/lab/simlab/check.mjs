#!/usr/bin/env node
// SimLab 姿勢 companion — 機械チェック (依存ゼロ)。
//
//   node simlab/check.mjs [rootDir]     # 既定 run/sim/traces を走査し、トレースごとに
//                                        # 姿勢 companion の有無・重なり tick 数・
//                                        # 相異なるフレーム数を表で出す
//   node simlab/check.mjs --selftest    # pose.mjs の findPoseFor を合成データで検証
//
// このスクリプトが機械的に守れるのは「スキーマと突き合わせ」だけ。
// 描画が実機と一致することの証明にはならない (09-VALIDATION.md の明記どおり)。

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { poseRoots, readTraceIdentity, findPoseFor, findPoseLibrary, findPaletteFor } from './pose.mjs';

// =============================================================================
// 既定モード: トレース x 姿勢 companion の突き合わせ表
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

/**
 * palette (14-03) の突き合わせ行を作る。`findPoseFor` とは別に呼ぶ (別 companion なので
 * overlap/frames が pose と一致するとは限らない —— 14-02 は palette の recording を
 * self-cap で早期に打ち切ることがある)。bytes-per-tick は「実測 overlap で割った bytes」
 * —— これが live rate ceiling をコマンドラインだけで検算する数字 (14-03-PLAN Task 1)。
 */
function checkPalette(identity) {
  const { match, rejected } = findPaletteFor(identity, poseRoots());
  if (!match) {
    return {
      palFound: false, palFrames: 0, palBytes: 0, palBytesPerTick: 0,
      palNote: rejected.length ? `弾いた ${rejected.length} 件: ${rejected[0].reason}` : '未取得',
    };
  }
  const lens = Array.isArray(match.index.lens) ? match.index.lens : [];
  const bytes = lens.reduce((a, b) => a + b, 0);
  const overlap = match.overlap || 0;
  return {
    palFound: true,
    palFrames: match.index.frames || 0,
    palBytes: bytes,
    palBytesPerTick: overlap > 0 ? bytes / overlap : 0,
    palNote: `${match.name} (${match.trust})`,
  };
}

function checkTraces(root) {
  const files = findTraces(root);
  const rows = [];
  for (const file of files) {
    const identity = readTraceIdentity(file);
    if (!identity || identity.gameTime == null) {
      rows.push({
        file, scenario: '?', found: false, overlapTicks: 0, distinctFrames: 0, note: 'meta 未取得',
        palFound: false, palFrames: 0, palBytes: 0, palBytesPerTick: 0, palNote: 'meta 未取得',
      });
      continue;
    }
    const pal = checkPalette(identity);
    const { match, rejected } = findPoseFor(identity, poseRoots());
    if (!match) {
      // **なぜ出ないのかを表に出す。** 「未取得」と「別 run のものを弾いた」は
      // 対処が違う (録り直す / 何も要らない) ので、区別できないと役に立たない。
      rows.push(Object.assign({
        file, scenario: identity.scenario, found: false, overlapTicks: 0, distinctFrames: 0,
        note: rejected.length
          ? `弾いた ${rejected.length} 件: ${rejected[0].reason}`
          : '未取得 (/tlmsim posetrace start で録る)',
      }, pal));
      continue;
    }
    rows.push(Object.assign({
      file, scenario: identity.scenario, found: true,
      overlapTicks: match.overlap, distinctFrames: match.index.frames,
      note: `${match.name} (${match.trust})`,
    }, pal));
  }
  return rows;
}

const pad = (s, w) => String(s).padEnd(w);
const rpad = (s, w) => String(s).padStart(w);

function report(rows, root) {
  const L = [];
  L.push(`姿勢 companion 突き合わせ  (traces: ${root})`);
  if (!rows.length) {
    L.push(`  トレースが無い (${root} 配下に .jsonl が無い)`);
    return L.join('\n');
  }
  L.push(pad('trace', 48) + pad('scenario', 10) + rpad('overlap', 9) + rpad('frames', 9)
    + rpad('pal', 5) + rpad('palF', 6) + rpad('palB', 9) + rpad('palB/t', 8) + '  companion / palette');
  for (const r of rows) {
    L.push(pad(r.file, 48) + pad(r.scenario, 10)
      + rpad(r.found ? r.overlapTicks + 'tick' : '-', 9)
      + rpad(r.found ? String(r.distinctFrames) : '-', 9)
      + rpad(r.palFound ? '○' : '-', 5)
      + rpad(r.palFound ? String(r.palFrames) : '-', 6)
      + rpad(r.palFound ? String(r.palBytes) : '-', 9)
      + rpad(r.palFound ? r.palBytesPerTick.toFixed(1) : '-', 8)
      + '  ' + r.note + (r.palNote ? ' / ' + r.palNote : ''));
  }
  return L.join('\n');
}

// =============================================================================
// --selftest: findPoseFor を合成データで検証
// =============================================================================

const UUID_A = '6b933a53-6ec6-4988-953b-b0d888317691';
const UUID_B = 'f84a73cc-56f2-40fb-98c8-67cd48cecb58';

/** テスト用の companion 索引を1本書く。 */
function writePose(dir, name, over) {
  fs.writeFileSync(path.join(dir, name), JSON.stringify(Object.assign({
    v: 1, gt0: 100, id: 1, type: 'touhou_little_maid:reimu', texture: null,
    stride: 11, verts: 1, quant: 0, idempotent: true, frames: 3,
    bin: name.replace('.json', '.bin'), slots: new Array(60).fill(0),
  }, over)));
}

/** テスト用の identity。実ファイルを作らずに findPoseFor だけを見たいとき用。 */
function identityOf(over) {
  return Object.assign({
    gameTime: 105, duration: 1728000, scenario: 'tank', lastTick: 49,
    reimu: { id: 1, uuid: UUID_A, type: 'touhou_little_maid:reimu' },
  }, over);
}

function selftest() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'simlab-pose-selftest-'));
  let ok = true;
  let n = 0;
  const assert = (cond, msg) => {
    n++;
    if (!cond) { console.error('SELFTEST FAIL: ' + msg); ok = false; }
  };
  try {
    // --- 1. 素直に合う場合 -------------------------------------------------
    // a: gt0=100, slots長60 -> [100,160)。トレース [105, 105+49+1) = [105,155)。
    // overlap = min(155,160) - max(105,100) = 50。base = 105-100 = 5。
    writePose(dir, 'a.pose.json', { v: 2, uuid: UUID_A });
    let r = findPoseFor(identityOf(), [dir]);
    assert(!!r.match, 'overlap があるはずなのに match が null');
    assert(r.match && r.match.base === 5, `base 計算が違う (期待 5, 実際 ${r.match && r.match.base})`);
    assert(r.match && r.match.trust === 'uuid', `trust が uuid でない (${r.match && r.match.trust})`);

    // --- 2. **宣言 duration に釣られない** ---------------------------------
    // 本件そのものの再発防止。2026-08-24 の実データを写す: トレースは gameTime=1 /
    // 実測 1700 tick なのに、tank が duration=1,728,000 (24 時間) を宣言するせいで
    // 窓が [1, 1728001) になり、gt0=104870 の companion を飲み込んでいた。
    //
    // **uuid はわざと一致させる** —— そうしないと「uuid で弾いたのか、窓で弾いたのか」が
    // 区別できず、窓の検査になっていないのに緑になる。
    const farDir = fs.mkdtempSync(path.join(os.tmpdir(), 'simlab-pose-far-'));
    writePose(farDir, 'far.pose.json',
      { v: 2, uuid: UUID_A, gt0: 104870, slots: new Array(6320).fill(0) });
    r = findPoseFor(identityOf({ gameTime: 1, lastTick: 1700 }), [farDir]);
    assert(!r.match, '宣言 duration に釣られて遠い過去の companion を拾った (本件の再発)');
    assert(r.rejected.some((x) => /重ならない/.test(x.reason)), '窓外を理由付きで弾いていない');
    // 逆に、実測 tick がそこまで伸びていれば当然採用される (弾きすぎていないことの確認)。
    r = findPoseFor(identityOf({ gameTime: 104870, lastTick: 6000 }), [farDir]);
    assert(r.match && r.match.base === 0, '実測範囲が重なるのに採用されない (弾きすぎ)');
    fs.rmSync(farDir, { recursive: true, force: true });

    // --- 3. UUID は hard gate (type/id へ落ちない) -------------------------
    // 別 run の companion。type も id も一致するが uuid が違う -> 即拒否。
    writePose(dir, 'other-run.pose.json', { v: 2, uuid: UUID_B, gt0: 100 });
    r = findPoseFor(identityOf({ reimu: { id: 1, uuid: UUID_A, type: 'touhou_little_maid:reimu' } }), [dir]);
    assert(r.match && r.match.name === 'a.pose.json',
      `uuid 一致のほうを選ぶべき (実際 ${r.match && r.match.name})`);
    assert(r.rejected.some((x) => x.name === 'other-run.pose.json' && /uuid/.test(x.reason)),
      'uuid 不一致を理由付きで弾いていない');

    // --- 4. v1 (uuid 無し) は自動採用しない --------------------------------
    const v1dir = fs.mkdtempSync(path.join(os.tmpdir(), 'simlab-pose-v1-'));
    writePose(v1dir, 'legacy.pose.json', { v: 1 });    // uuid 無し
    r = findPoseFor(identityOf(), [v1dir]);
    assert(!r.match, 'uuid 無しの v1 を自動採用してしまった');
    assert(r.rejected.some((x) => /v1/.test(x.reason)), 'v1 を弾いた理由が出ていない');
    // allowV1 を明示したときだけ使える (手動指定の経路)
    r = findPoseFor(identityOf(), [v1dir], { allowV1: true });
    assert(r.match && r.match.trust === 'manual-v1', 'allowV1 でも v1 が使えない');
    fs.rmSync(v1dir, { recursive: true, force: true });

    // --- 5. 旧トレース (uuid 無し) は type/id 一致を要求 --------------------
    const legacyDir = fs.mkdtempSync(path.join(os.tmpdir(), 'simlab-pose-legacy-'));
    writePose(legacyDir, 'wrongtype.pose.json', { v: 1, type: 'minecraft:zombie' });
    r = findPoseFor(identityOf({ reimu: { id: 1, uuid: null, type: 'touhou_little_maid:reimu' } }), [legacyDir]);
    assert(!r.match, '旧トレースで type 違いの companion を拾った');
    assert(r.rejected.some((x) => /type/.test(x.reason)), 'type 違いの理由が出ていない');
    fs.rmSync(legacyDir, { recursive: true, force: true });

    // --- 6. 欠損した索引 / 壊れた JSON ------------------------------------
    fs.writeFileSync(path.join(dir, 'broken.pose.json'), '{ this is not json');
    writePose(dir, 'noslots.pose.json', { v: 2, uuid: UUID_A, slots: [] });
    r = findPoseFor(identityOf(), [dir]);
    assert(r.rejected.some((x) => x.name === 'broken.pose.json'), '壊れた JSON を理由付きで弾いていない');
    assert(r.rejected.some((x) => x.name === 'noslots.pose.json'), 'slots 空を弾いていない');
    assert(r.match && r.match.name === 'a.pose.json', '壊れた候補があると正しいものまで落ちる');

    // --- 6b. アニメライブラリは時間で突き合わせない -------------------------
    // ライブラリ (`/tlmsim animsweep` が録った全アニメ) には run の身元が原理的に無く、
    // gt0 は sweep を回した時刻でしかない。時間で吸着させると必ず嘘になる ——
    // それが base=-104869 の正体だった。**引くのは tick ではなくアニメ名。**
    const libDir = fs.mkdtempSync(path.join(os.tmpdir(), 'simlab-pose-lib-'));
    writePose(libDir, 'sweep.pose.json', { v: 1, gt0: 100 });    // 時間的にはぴったり重なる
    fs.writeFileSync(path.join(libDir, 'sweep.anims.json'), JSON.stringify([
      { anim: 'extra43', from: 0, to: 19, length: 0 },
      { anim: 'empty', from: 20, to: 39, length: 5 },
    ]));
    r = findPoseFor(identityOf(), [libDir]);
    assert(!r.match, 'アニメライブラリを run 録画として吸着してしまった (base=-104869 の正体)');
    assert(r.rejected.some((x) => /ライブラリ/.test(x.reason)), 'ライブラリを弾いた理由が出ていない');
    // 一方、ライブラリ経路では見つかること
    const lib = findPoseLibrary([libDir]);
    assert(lib && lib.name === 'sweep.pose.json', 'ライブラリが findPoseLibrary で見つからない');
    assert(lib && lib.anims.length === 2, 'anims 表が読めていない');
    assert(lib && lib.anims[0].anim === 'extra43', 'アニメ名が読めていない');
    // run 録画はライブラリとして拾わないこと (逆方向の取り違え)
    assert(!findPoseLibrary([dir]), 'run 録画をライブラリとして拾った');
    fs.rmSync(libDir, { recursive: true, force: true });

    // --- 7. readTraceIdentity: 実測 tick と霊夢の spawn ---------------------
    const tf = path.join(dir, 'synthetic.jsonl');
    fs.writeFileSync(tf, [
      JSON.stringify({ t: 0, ch: 'log', msg: 'arena' }),
      JSON.stringify({ t: 0, ch: 'meta', scenario: 'tank', seed: 1, arena: 0, duration: 1728000, gameTime: 7 }),
      JSON.stringify({ t: 133, ch: 'spawn', id: 2, role: 'reimu', type: 'touhou_little_maid:reimu', uuid: UUID_A }),
      JSON.stringify({ t: 1582, ch: 'pos', id: 2, x: 0, y: 64, z: 0 }),
    ].join('\n') + '\n');
    const id7 = readTraceIdentity(tf);
    assert(id7 && id7.gameTime === 7, 'meta.gameTime が読めていない');
    assert(id7 && id7.lastTick === 1582, `lastTick が違う (期待 1582, 実際 ${id7 && id7.lastTick})`);
    assert(id7 && id7.reimu && id7.reimu.uuid === UUID_A, '霊夢の spawn から uuid が取れていない');

    // --- 8. 壊れた末尾 (書き込み途中で切れたトレース) -----------------------
    // 最終行が途中で切れていても、その手前までで lastTick が出ること。
    const tf2 = path.join(dir, 'truncated.jsonl');
    fs.writeFileSync(tf2, [
      JSON.stringify({ t: 0, ch: 'meta', scenario: 'tank', seed: 1, arena: 0, duration: 100, gameTime: 7 }),
      JSON.stringify({ t: 40, ch: 'spawn', id: 2, role: 'reimu', type: 'touhou_little_maid:reimu', uuid: UUID_A }),
      JSON.stringify({ t: 90, ch: 'pos', id: 2, x: 0, y: 64, z: 0 }),
      '{"t":91,"ch":"pos","id":2,"x":0,"y"',      // 切れた行
    ].join('\n'));
    const id8 = readTraceIdentity(tf2);
    assert(id8 && id8.lastTick === 90, `壊れた末尾で lastTick が狂う (実際 ${id8 && id8.lastTick})`);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }

  if (!ok) {
    console.error('selftest FAILED');
    process.exit(1);
  }
  console.log(`selftest OK (${n} 件: base / 宣言duration非依存 / uuid hard gate / v1拒否`
    + ' / 旧トレースのtype一致 / 壊れた索引 / 実測tick / 壊れた末尾)');
}

// =============================================================================
// CLI
// =============================================================================

const isMain = process.argv[1] && import.meta.url.endsWith(path.basename(process.argv[1]));
if (isMain) {
  const args = process.argv.slice(2);
  if (args.includes('--selftest')) {
    selftest();
  } else {
    const root = args.find((a) => !a.startsWith('--')) ?? 'run/sim/traces';
    const rows = checkTraces(root);
    console.log(report(rows, root));
    // 姿勢 companion が 1 本も無くてもエラーにしない (キャプチャ前でも回せる、Task 3 の前提)。
    process.exit(0);
  }
}
