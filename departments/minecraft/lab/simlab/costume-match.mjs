#!/usr/bin/env node
// =============================================================================
// costume-match.mjs — 霊夢の衣装プリセットを「実機が録った palette」で言い当てる
// =============================================================================
//
//   node simlab/costume-match.mjs <xxx.pal.json> [ysmPackDir]
//
// なぜ要るか (2026-08-25):
//   Viewer は v.roaming.* を全部 0 のまま描いていた (gl.js の ROAMING_DEFAULTS = {})。
//   実モデルには衣装プリセットの選択 UI (ysm.json の 衣服选择) があり、8 種それぞれが
//   shangyi / qunzi / shoutao / weijin / kouzhao / maozi / naian を同時に設定する。
//   0 は「短裙」であって、にーくらが実機で選んでいる衣装ではない。だから服が違い、
//   下地アニメが v.roaming.* を書き換えるたびに暴れる。
//
//   ではどのプリセットなのか。**訊くのではなく測る** (にーくら判断 2026-08-25)。
//
// 何を突き合わせるか:
//   服は scale = 0 で隠される。palette はボーンごとの TRS を運ぶので scale も持っている
//   (pal9[o+6..o+8]、ysm.js の matsFromPalette と同じ並び)。よって
//     (a) palette から「実機で隠れていたボーン集合」を出す
//     (b) 各プリセットで下地アニメの scale 式を評価し「隠れるボーン集合」を出す
//   の 2 つを比べれば、一致するものが答えになる。
//
//   **評価器は書かない。** ysm.js の sampleChannel をそのまま使う —— 同じ式を 2 通りに
//   解釈する実装をこのリポジトリに増やさないため (AGENT-01 と同じ思想)。
//
// 一致が 1 つに定まらなければ **答えを出さずに終わる**。曖昧なまま既定を決めない。
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, '..');

// palette-selftest.mjs と同じ既定 —— **記録した環境のパックを見る**。
// 解析だけ別環境を見るのは事故のもと (condition6.mjs のコメント)。
const PACK = process.argv[3]
  || 'C:/Users/genki/AppData/Roaming/.minecraft-simlab/config/yes_steve_model/custom/「博丽灵梦」2';
const PAL = process.argv[2];

function die(msg) { console.error('FAIL: ' + msg); process.exit(1); }
function must(p, what) { if (!fs.existsSync(p)) die(what + ' が無い -> ' + p); return p; }
if (!PAL) die('usage: node simlab/costume-match.mjs <xxx.pal.json> [ysmPackDir]');
must(PAL, 'palette 索引');
must(PACK, 'YSM パック');

// ---------------------------------------------------------------- 1. eval
(0, eval)(fs.readFileSync(must(path.join(REPO, 'simlab', 'viewer', 'ysm.js'), 'ysm.js'), 'utf8'));
(0, eval)(fs.readFileSync(must(path.join(REPO, 'simlab', 'viewer', 'palette.js'), 'palette.js'), 'utf8'));
const Y = globalThis.YSM;
const SimPalette = globalThis.SimPalette;
if (!Y || typeof Y.sampleChannel !== 'function') die('ysm.js に YSM.sampleChannel が無い');

// ---------------------------------------------------------------- 2. プリセットを読む
// ysm.json の extra_animation_buttons -> 衣服选择 (radio) の labels。
// **値をこのファイルに書かない。モデルが唯一の真実源。**
const man = JSON.parse(fs.readFileSync(must(path.join(PACK, 'ysm.json'), 'ysm.json'), 'utf8'));

function findCostumeLabels(node) {
  let found = null;
  (function walk(n) {
    if (found || !n || typeof n !== 'object') return;
    if (Array.isArray(n)) { for (const x of n) walk(x); return; }
    if (n.type === 'radio' && n.labels && typeof n.labels === 'object'
        && Object.values(n.labels).some((v) => typeof v === 'string' && v.includes('v.roaming.shangyi'))) {
      found = n.labels; return;
    }
    for (const v of Object.values(n)) walk(v);
  })(node);
  return found;
}
const labels = findCostumeLabels(man);
if (!labels) die('ysm.json に衣装プリセット (v.roaming.shangyi を設定する radio) が見つからない');

const PRESETS = [];
for (const [name, expr] of Object.entries(labels)) {
  const vars = {};
  for (const m of String(expr).matchAll(/(v\.[A-Za-z_.]+)\s*=\s*(-?\d+(?:\.\d+)?)/g)) {
    vars[m[1]] = Number(m[2]);
  }
  PRESETS.push({ name, aa: vars['v.aa'], vars });
}
PRESETS.sort((a, b) => (a.aa === undefined ? 99 : a.aa) - (b.aa === undefined ? 99 : b.aa));
console.log('プリセット: ' + PRESETS.length + ' 種 (ysm.json 由来)');

// ---------------------------------------------------------------- 3. 服で切り替わるボーン
// 下地 (parallel 系) だけを見る —— collectHidden と同じ規約。
const COSTUME_VARS = ['shangyi', 'qunzi', 'shoutao', 'weijin', 'kouzhao', 'maozi', 'naian'];
const anims = {};
for (const rel of Object.values((man.files && man.files.player && man.files.player.animation) || {})) {
  try { Object.assign(anims, JSON.parse(fs.readFileSync(path.join(PACK, rel), 'utf8')).animations || {}); }
  catch (e) { /* パックに無いだけ */ }
}
const gated = [];   // { an, bone, scale }
for (const [an, a] of Object.entries(anims)) {
  if (!/^(pre_)?parallel/.test(an)) continue;
  for (const [bone, ch] of Object.entries((a && a.bones) || {})) {
    if (ch.scale === undefined) continue;
    const s = JSON.stringify(ch.scale);
    if (COSTUME_VARS.some((v) => s.includes('roaming.' + v))) gated.push({ an, bone, scale: ch.scale });
  }
}
const gatedBones = [...new Set(gated.map((g) => g.bone))];
console.log('服で切り替わるボーン: ' + gatedBones.length + ' 本 (下地 parallel 系 ' + gated.length + ' チャンネル)');
if (!gatedBones.length) die('服で切り替わるボーンが 1 本も見つからない');

const isZero = (v) => v && Math.abs(v[0]) < 1e-6 && Math.abs(v[1]) < 1e-6 && Math.abs(v[2]) < 1e-6;

function hiddenForPreset(p) {
  const out = new Set();
  for (const g of gated) {
    let v;
    try { v = Y.sampleChannel(g.scale, 0, null, p.vars); } catch (e) { continue; }
    if (isZero(v)) out.add(g.bone);
  }
  return out;
}

// ---------------------------------------------------------------- 4. palette の実測
const index = JSON.parse(fs.readFileSync(PAL, 'utf8'));
const binPath = path.join(path.dirname(PAL), index.bin);
must(binPath, 'palette の bin (' + index.bin + ')');
const binBuf = fs.readFileSync(binPath);
const fetchRecord = (from, len) => Promise.resolve(new Uint8Array(binBuf.subarray(from, from + len)));
const inflate = (b) => Promise.resolve(new Uint8Array(zlib.inflateSync(Buffer.from(b))));
const stream = SimPalette.makeStream(index, fetchRecord, inflate);
const slotOf = new Map(index.names.map((n, i) => [n, i]));

const COMPS = 9;
const covered = [];
for (let t = 0; t < index.slots.length; t++) if (index.slots[t] >= 0) covered.push(t);
if (!covered.length) die('palette に記録された tick が 1 つも無い');
// 端と中央から採る。**1 枚だけで決めない** —— 戦闘中に一時的に消える部位と、
// 衣装で常に消えている部位を分けたいので、全標本で一貫して 0 のものだけを採る。
const SAMPLES = [0, 0.25, 0.5, 0.75, 1]
  .map((f) => covered[Math.min(covered.length - 1, Math.floor(f * (covered.length - 1)))]);

(async () => {
  let alwaysHidden = null;
  let everSeen = 0;
  for (const t of SAMPLES) {
    const s9 = await stream.at(t);
    if (!s9) continue;
    everSeen++;
    const here = new Set();
    for (const bone of gatedBones) {
      const slot = slotOf.get(bone);
      if (slot === undefined) continue;
      const o = slot * COMPS;
      if (isZero([s9[o + 6], s9[o + 7], s9[o + 8]])) here.add(bone);
    }
    alwaysHidden = alwaysHidden === null ? here : new Set([...alwaysHidden].filter((b) => here.has(b)));
  }
  if (!everSeen) die('palette からフレームを 1 枚も復号できなかった');
  const unresolved = gatedBones.filter((b) => !slotOf.has(b));
  console.log('palette の標本: ' + everSeen + ' 枚 (tick ' + SAMPLES.join(', ') + ')');
  if (unresolved.length) {
    console.log('  palette に無いボーン: ' + unresolved.length + ' 本 (比較から除外) 例: '
      + unresolved.slice(0, 5).join(', '));
  }
  console.log('  実機で常に隠れていた: ' + alwaysHidden.size + ' / '
    + (gatedBones.length - unresolved.length) + ' 本');
  console.log('');

  // ------------------------------------------------------------ 5. 突き合わせ
  const cmp = [];
  for (const p of PRESETS) {
    const h = new Set([...hiddenForPreset(p)].filter((b) => slotOf.has(b)));
    let miss = 0, extra = 0;
    for (const b of alwaysHidden) if (!h.has(b)) miss++;
    for (const b of h) if (!alwaysHidden.has(b)) extra++;
    cmp.push({ p, hidden: h.size, miss, extra, diff: miss + extra });
  }
  cmp.sort((a, b) => a.diff - b.diff);
  console.log('  v.aa  名前          隠す   実機は出す   実機は隠す   差分');
  for (const c of cmp) {
    console.log('  ' + String(c.p.aa === undefined ? '?' : c.p.aa).padStart(4) + '  '
      + c.p.name.padEnd(12)
      + String(c.hidden).padStart(5)
      + String(c.extra).padStart(12)
      + String(c.miss).padStart(13)
      + String(c.diff).padStart(7)
      + (c.diff === 0 ? '   <= 完全一致' : ''));
  }
  console.log('');

  // ---------------------------------------------------------- 5b. 今の Viewer 既定
  // **測って決めた値が、実際に Viewer へ入っているか。** ここを見ないと、
  // 「測定器は正しい答えを出すが Viewer は別の値で描いている」状態に黙って戻れる。
  // gl.js の 1 行を正規表現で読む —— 行が動いたら found=false で落ちるので気づける。
  const glSrc = fs.readFileSync(path.join(REPO, 'simlab', 'viewer', 'gl.js'), 'utf8');
  const mDef = glSrc.match(/const ROAMING_DEFAULTS = (\{[^}]*\});/);
  if (!mDef) {
    console.log('  [注意] gl.js の ROAMING_DEFAULTS を読めなかった (行が動いた?)。既定の検査を飛ばす');
  } else {
    let cur = null;
    try { cur = (0, eval)('(' + mDef[1] + ')'); } catch (e) { /* 読めなければ下で落とす */ }
    if (!cur) {
      console.log('  [注意] gl.js の ROAMING_DEFAULTS を評価できなかった。既定の検査を飛ばす');
    } else {
      const hid = new Set();
      for (const g of gated) {
        let v;
        try { v = Y.sampleChannel(g.scale, 0, null, cur); } catch (e) { continue; }
        if (isZero(v) && slotOf.has(g.bone)) hid.add(g.bone);
      }
      let miss = 0, extra = 0;
      for (const b of alwaysHidden) if (!hid.has(b)) miss++;
      for (const b of hid) if (!alwaysHidden.has(b)) extra++;
      const label = Object.keys(cur).length ? JSON.stringify(cur) : '{} (全部 0)';
      if (miss + extra === 0) {
        console.log('  今の Viewer 既定 ' + label + ' -> 差分 0 (実機と一致)');
      } else {
        console.log('  **今の Viewer 既定 ' + label + ' -> 差分 ' + (miss + extra) + '**');
        console.log('    Viewer は実機と違う服を描いている。gl.js の ROAMING_DEFAULTS を直すこと。');
        process.exitCode = 4;
      }
    }
  }
  console.log('');
  // ------------------------------------------------------------ 6. 報告
  // **プリセットの一致は「参考」。** 実機が必ずプリセットのどれかである保証は無い ——
  // 実際 2026-08-25 の答えは『プリセット未選択 + mod の shangyi=2』で、8 種のどれでも
  // なかった。だからここで exit を決めない。決めるのは上の「今の Viewer 既定」のほう。
  const exact = cmp.filter((c) => c.diff === 0);
  if (exact.length === 1) {
    const w = exact[0].p;
    console.log('プリセットの一致: v.aa=' + w.aa + ' (' + w.name + ')');
    console.log('  ' + Object.entries(w.vars).map(([k, v]) => k + '=' + v).join(' '));
  } else if (exact.length > 1) {
    console.log('プリセットの一致: **一意でない** —— '
      + exact.map((c) => 'v.aa=' + c.p.aa + '(' + c.p.name + ')').join(', '));
    console.log('  同じボーンを隠すプリセットは palette では区別できない。');
  } else {
    console.log('プリセットの一致: 無し (最小差分 ' + cmp[0].diff
      + ' = v.aa=' + cmp[0].p.aa + ' ' + cmp[0].p.name + ')');
    console.log('  実機はプリセットを選んでいないか、mod が一部だけ上書きしている。');
    console.log('  上の「今の Viewer 既定」が差分 0 なら、それが答え。');
  }
})();
