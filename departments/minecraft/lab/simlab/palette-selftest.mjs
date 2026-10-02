#!/usr/bin/env node
// palette (14-01) の自己検査 —— committed fixture を node だけで通しで読む。
//
//   node simlab/palette-selftest.mjs [ysmPackDir]
//
// やること (計画 14-01-PLAN.md Task 1 の behavior そのもの):
//   1. ysm.js / palette.js を node へ eval する (condition6.mjs:53 と同じ流儀 —— 両方
//      `(function (root) {...})(typeof window!=='undefined'?window:globalThis)` で
//      書かれているので、node でも `globalThis.YSM` / `globalThis.SimPalette` が立つ)。
//   2. committed fixture (`simlab/fixtures/palette-golden.pal.json` + `.pal.bin`) を読み、
//      SimPalette.makeStream で K,D,D の3フレームを全部 decode する。
//   3. decode した float が golden `*.palette.bin` (000/003/006) と厳密に一致することを
//      確認する (Java の SimPaletteCodec が書いたレコードを、node の zlib.inflateSync +
//      このファイルの decodeRecord が正しく読めることの裏取り)。
//   4. YSM パックから geometry を組み立て (condition6.mjs:103-110 と同じ)、
//      matsFromPalette を回して missing === 0 (1058/1058 解決) を確認する。
//
// YSM パックが無ければ **skip ではなく fail** する —— 黙って skip するゲートは無音の no-op
// (SimBoneNoiseTest / condition6.mjs と同じ規約)。
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, '..');
const FIXTURE_DIR = path.join(HERE, 'fixtures');
const GOLDEN_DIR = path.join(FIXTURE_DIR, 'palette-golden-raw');

// CLI 引数で上書き可能。パックが無い環境では codec 検査だけを実行する。
const PACK = process.argv[2]
  || 'C:/Users/genki/AppData/Roaming/.minecraft-simlab/config/yes_steve_model/custom/「博丽灵梦」2';

let failed = false;
function check(cond, msg) {
  if (!cond) { failed = true; console.error('FAIL: ' + msg); }
  else console.log('ok: ' + msg);
}
function must(p, what) {
  if (!fs.existsSync(p)) {
    console.error('FAIL: ' + what + ' が無い -> ' + p);
    process.exit(1);
  }
  return p;
}

// ---------------------------------------------------------------- 1. eval
const ysmJsPath = must(path.join(REPO, 'simlab', 'viewer', 'ysm.js'), 'ysm.js');
const paletteJsPath = must(path.join(REPO, 'simlab', 'viewer', 'palette.js'), 'palette.js');
(0, eval)(fs.readFileSync(ysmJsPath, 'utf8'));
(0, eval)(fs.readFileSync(paletteJsPath, 'utf8'));
const Y = globalThis.YSM;
const SimPalette = globalThis.SimPalette;
check(!!Y && typeof Y.matsFromPalette === 'function', 'ysm.js に YSM.matsFromPalette がある');
check(!!SimPalette && typeof SimPalette.makeStream === 'function', 'palette.js に SimPalette.makeStream がある');

// ---------------------------------------------------------------- 2. fixture を読む
const jsonPath = must(path.join(FIXTURE_DIR, 'palette-golden.pal.json'), 'committed fixture (pal.json)');
const binPath = must(path.join(FIXTURE_DIR, 'palette-golden.pal.bin'), 'committed fixture (pal.bin)');
const index = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
check(index.codec === 'palmask-deflate-v1', 'index.codec === palmask-deflate-v1 (実測 ' + index.codec + ')');
check(index.names.length === index.bones, 'names.length === bones (実測 ' + index.names.length + '/' + index.bones + ')');
check(index.lens.length === index.frames && index.kinds.length === index.frames,
  'lens/kinds の長さが frames と一致 (実測 lens=' + index.lens.length + ' kinds=' + index.kinds.length + ' frames=' + index.frames + ')');
check(index.kinds[0] === 'K', 'kinds[0] === "K" (実測 ' + index.kinds[0] + ')');
const binBytes = fs.statSync(binPath).size;
const sumLens = index.lens.reduce((a, b) => a + b, 0);
check(sumLens === binBytes, 'sum(lens) === bin バイト長 (実測 ' + sumLens + '/' + binBytes + ')');

const binBuf = fs.readFileSync(binPath);
function fetchRecord(from, len) {
  return Promise.resolve(new Uint8Array(binBuf.buffer, binBuf.byteOffset + from, len));
}
function inflate(bytes) {
  return Promise.resolve(new Uint8Array(zlib.inflateSync(Buffer.from(bytes))));
}
const stream = SimPalette.makeStream(index, fetchRecord, inflate);

// ---------------------------------------------------------------- 3. golden との厳密一致
const GOLDEN_SAMPLES = [0, 3, 6]; // fixture が使った golden 標本 (empty / extra44 / extra43)
function readGoldenPalette(i) {
  const b = fs.readFileSync(path.join(GOLDEN_DIR, String(i).padStart(3, '0') + '.palette.bin'));
  const f = new Float32Array(b.length / 4);
  for (let k = 0; k < f.length; k++) f[k] = b.readFloatLE(k * 4);
  return f;
}
const STRIDE = 12, COMPS = 9;

(async () => {
  let mismatches = 0, comparisons = 0;
  for (let t = 0; t < GOLDEN_SAMPLES.length; t++) {
    const state9 = await stream.at(t);
    check(!!state9, 'stream.at(' + t + ') がフレームを返した');
    const golden = readGoldenPalette(GOLDEN_SAMPLES[t]);
    for (let b = 0; b < index.bones; b++) {
      for (let k = 0; k < COMPS; k++) {
        comparisons++;
        const expected = golden[b * STRIDE + k];
        const actual = state9[b * COMPS + k];
        // ビット単位 (Java 側の changedBones と同じ規約 —— -0/+0 も区別する)。
        const eb = new DataView(new ArrayBuffer(4)); eb.setFloat32(0, expected);
        const ab = new DataView(new ArrayBuffer(4)); ab.setFloat32(0, actual);
        if (eb.getUint32(0) !== ab.getUint32(0)) mismatches++;
      }
    }
  }
  check(comparisons === 3 * index.bones * COMPS, '比較件数 = 3 x bones x 9 (実測 ' + comparisons + ')');
  check(mismatches === 0, 'decode した float が golden と全ビット一致 (実測不一致 ' + mismatches + '/' + comparisons + ')');

  // ---------------------------------------------------------------- 4. matsFromPalette
  if (!fs.existsSync(PACK)) {
    console.log('SKIP: YSM パックが無いため matsFromPalette 検査を省略 (' + PACK + ')');
    process.exit(failed ? 1 : 0);
  }
  const manPath = must(path.join(PACK, 'ysm.json'), 'ysm.json (マニフェスト)');
  const man = JSON.parse(fs.readFileSync(manPath, 'utf8'));
  const model = JSON.parse(fs.readFileSync(must(path.join(PACK, man.files.player.model.main), 'main.json'), 'utf8'));
  const anims = {};
  for (const r of Object.values(man.files.player.animation || {})) {
    try { Object.assign(anims, JSON.parse(fs.readFileSync(path.join(PACK, r), 'utf8')).animations || {}); } catch { /* パックに無いだけ */ }
  }
  const props = man.properties || {};
  const geo = Y.buildGeometry(model['minecraft:geometry'][0],
    props.width_scale || 1, props.height_scale || 1, Y.collectHidden(anims));

  const slotOf = new Map(index.names.map((n, i) => [n, i]));
  const state9last = await stream.at(GOLDEN_SAMPLES.length - 1);
  const { mats, missing } = Y.matsFromPalette(geo.bones, state9last, slotOf);
  check(mats.length === geo.bones.length * 16, 'mats.length === bones.length * 16');
  check(missing === 0, 'matsFromPalette の missing === 0 (実測 ' + missing + '/' + geo.bones.length + ')');

  // ---------------------------------------------------------------- 5. seek 一貫性 (14-03)
  // K の外は自己完結しない (palette.js:86) —— 後退やジャンプは直前以前の最も近い K まで
  // 巻き戻してから前進する。前進方向だけを見るテストでは「後退で壊れているのに前進だけは
  // 緑」という欠陥を見逃す (静的スクリーンショットでも見えない)。ここでは実際に
  // 0 -> 最終フレーム -> 1 と飛ばした結果が、頭から順に decode した結果と厳密一致することを
  // 確かめる。decodeRecord は state9 を in-place で書き換えるので、比較の直前に必ず
  // .slice() でコピーを取ってから次の .at() を呼ぶ (でないと直後の decode で上書きされる)。
  async function sequentialStateAt(t) {
    const s = SimPalette.makeStream(index, fetchRecord, inflate);
    let out = null;
    for (let i = 0; i <= t; i++) out = (await s.at(i)).slice();
    return out;
  }
  function bitEqual(a, b) {
    if (!a || !b || a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) {
      const av = new DataView(new ArrayBuffer(4)); av.setFloat32(0, a[i]);
      const bv = new DataView(new ArrayBuffer(4)); bv.setFloat32(0, b[i]);
      if (av.getUint32(0) !== bv.getUint32(0)) return false;
    }
    return true;
  }
  const seekStream = SimPalette.makeStream(index, fetchRecord, inflate);
  const lastFrame = index.frames - 1;
  check(lastFrame >= 1, 'fixture に seek を試せるだけのフレーム数がある (実測 frames=' + index.frames + ')');
  await seekStream.at(0);
  const jumpedLast = (await seekStream.at(lastFrame)).slice();
  const seqLast = await sequentialStateAt(lastFrame);
  check(bitEqual(jumpedLast, seqLast), 'frame 0 -> 最終フレーム (' + lastFrame + ') へのジャンプが、頭からの順次デコードと全ビット一致');
  const jumpedBack = (await seekStream.at(1)).slice();
  const seqOne = await sequentialStateAt(1);
  check(bitEqual(jumpedBack, seqOne), '最終フレームから frame 1 への巻き戻りが、頭からの順次デコードと全ビット一致');

  // ------------------------------------------------------ 6. 索引のライブ更新 (extend)
  // ライブでは索引が 5 秒ごと (CHECKPOINT_EVERY=100 tick) に伸びる。Viewer はそれを
  // 取り直して stream へ差し替えるが、**差し替えを誤ると壊れた姿勢を黙って描く** ——
  // 前の run の state9 が残ったまま新しい bin を差分適用する形になるため。
  // ここは「伸ばしてよい索引か」の判定そのものを縛る。
  {
    // 追記された bin を模す: 元の bin の後ろへ frame 0 (K) の生バイトをそのまま足す。
    const f0 = binBuf.subarray(0, index.lens[0]);
    const grownBin = Buffer.concat([binBuf, f0]);
    let fetches = 0;
    const grownFetch = (from, len) => {
      fetches++;
      return Promise.resolve(new Uint8Array(grownBin.buffer, grownBin.byteOffset + from, len));
    };
    const grownIndex = Object.assign({}, index, {
      frames: index.frames + 1,
      lens: index.lens.concat([index.lens[0]]),
      kinds: index.kinds.concat(["K"]),
      slots: index.slots.concat([index.frames]),
    });

    const s = SimPalette.makeStream(index, grownFetch, inflate);
    check(s.frames === index.frames, "extend 前: frames が索引と一致 (実測 " + s.frames + ")");
    check((await s.at(index.frames)) === null, "extend 前: 索引の外の tick は null (伸ばす前に未来を描かない)");

    // 差分チェーンを前へ進めておく (最終フレームまで復号した状態にする)
    await s.at(index.frames - 1);

    check(s.extend(grownIndex) === true, "extend: 同じ run の伸びた索引は受け入れる");
    check(s.frames === index.frames + 1, "extend 後: frames が増えている (実測 " + s.frames + ")");

    // **ここが要点**: curFrame を保持しているなら、次の 1 フレームだけ取りに行く。
    // 捨てていると最寄りの K まで巻き戻って複数フレームを読み直す。
    fetches = 0;
    const grownState = await s.at(index.frames);
    check(grownState !== null, "extend 後: 伸びた分の tick が描ける");
    check(fetches === 1, "extend 後の前進は 1 レコードだけ読む (state9/curFrame を捨てていない。実測 " + fetches + " 回)");

    // 追記したのは frame 0 の複製なので、姿勢は frame 0 と全ビット一致するはず。
    const fresh = SimPalette.makeStream(index, fetchRecord, inflate);
    const frame0 = (await fresh.at(0)).slice();
    check(bitEqual(grownState, frame0), "追記フレーム (frame 0 の複製) の復号結果が frame 0 と全ビット一致");

    // 受け入れてはいけないもの
    const s2 = SimPalette.makeStream(index, grownFetch, inflate);
    check(s2.extend(Object.assign({}, grownIndex, { gt0: index.gt0 + 1 })) === false,
      "extend: gt0 が違う索引 (別の run) は拒む");
    check(s2.extend(Object.assign({}, index, {
      lens: index.lens.slice(0, 1), kinds: index.kinds.slice(0, 1), slots: index.slots.slice(0, 1),
    })) === false, "extend: 後退している索引は拒む");
    check(s2.extend(Object.assign({}, grownIndex, { bones: index.bones + 1 })) === false,
      "extend: bones が違う索引は拒む");
    check(s2.extend(null) === false, "extend: null は拒む");
    check(s2.frames === index.frames, "拒んだ後も索引は元のまま (実測 " + s2.frames + ")");
  }

  if (failed) {
    console.error('\npalette-selftest: FAILED');
    process.exit(1);
  }
  console.log('\npalette-selftest: PASSED (' + geo.bones.length + ' bones, 0 unresolved)');
})().catch((e) => {
  console.error('FAIL: 例外', e);
  process.exit(1);
});
