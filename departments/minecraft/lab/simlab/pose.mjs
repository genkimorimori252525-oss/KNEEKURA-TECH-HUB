// SimLab 姿勢 companion — 依存ゼロの純関数群 (サーバは起動しない)。
//
// companion 形式 v1 (Java 側の唯一の読み書き場所: SimPoseCodec と同じ契約):
//   <stamp>.pose.json — { v, gt0, id, type, texture, stride, verts, quant, idempotent,
//                          frames, bin, slots[] }
//   <stamp>.pose.bin  — float32 リトルエンディアン (frames × verts × stride を連結)
//
// serve.mjs (配信) と check.mjs (機械チェック) の両方がここを import する。
// ルート決定の規則をここ 1 箇所にまとめ、2 箇所で書き分けないこと (09-01-PLAN Task 2 §1)。

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const APPDATA_BASE = process.env.APPDATA || path.join(process.env.HOME || '', '.config');
const DOT_MC = path.join(APPDATA_BASE, '.minecraft');
const DOT_MC_SIMLAB = path.join(APPDATA_BASE, '.minecraft-simlab');

/**
 * 姿勢 companion (poses ディレクトリ) を探す 5 ルート。
 * serve.mjs の /api/model 系 (models ディレクトリ) と同じ 5 箇所の `poses` 版。
 * `.minecraft-simlab` は YSM mod が入っている唯一の実機インスタンスであり、
 * 姿勢キャプチャ・モデルダンプはそこでしか行えない。
 */
export function poseRoots() {
  return [
    path.join(ROOT, 'simlab', 'poses'),
    path.join(ROOT, 'run', 'client_a', 'simlab', 'poses'),
    path.join(ROOT, 'run', 'client_b', 'simlab', 'poses'),
    path.join(DOT_MC, 'simlab', 'poses'),
    path.join(DOT_MC_SIMLAB, 'simlab', 'poses'),
  ];
}

/**
 * トレース (JSONL) の ch:meta 行だけを読んで { gameTime, duration, scenario } を返す。
 * ファイル全体は読まない (774KB〜1.3MB を毎回読むのは無駄)。
 *
 * meta は先頭付近 (arena セットアップの log 行の直後) にあるが、必ずしも 1 行目とは
 * 限らないので、先頭のチャンク (既定 8KB、見つからなければ倍々に広げる) から
 * "ch":"meta" を含む行を探す。
 */
export function readTraceMeta(file) {
  let fd;
  try {
    fd = fs.openSync(file, 'r');
  } catch {
    return null;
  }
  try {
    const size = fs.fstatSync(fd).size;
    let chunkSize = 8192;
    while (chunkSize < size + chunkSize) {
      const want = Math.min(chunkSize, size);
      const buf = Buffer.alloc(want);
      const n = fs.readSync(fd, buf, 0, want, 0);
      const text = buf.toString('utf8', 0, n);
      const lines = text.split('\n');
      // 末尾行は途中で切れている可能性があるので、末尾チャンクでない限り無視する。
      const complete = n < want ? lines : lines.slice(0, -1);
      for (const line of complete) {
        if (!line.includes('"ch":"meta"')) continue;
        try {
          const e = JSON.parse(line);
          if (e.ch === 'meta') {
            return { gameTime: e.gameTime, duration: e.duration, scenario: e.scenario };
          }
        } catch {
          // 壊れた行は無視して次の候補を探す
        }
      }
      if (n < want) break; // ファイル全体を読み切った
      chunkSize *= 4;
    }
    return null;
  } catch {
    return null;
  } finally {
    fs.closeSync(fd);
  }
}

/**
 * その `.pose.json` が<b>アニメライブラリ</b>か。
 *
 * <p><b>同じファイル形式に2種類の別物が入っている。</b>
 * <ul>
 *   <li><b>run 録画</b> (`SimPoseTrace`) —— tick → 頂点。<b>その run でしか意味を持たない</b>。
 *       `slots[tick + base]` で引く。</li>
 *   <li><b>アニメライブラリ</b> (`SimAnimSweep` = `/tlmsim animsweep`) —— YSM パックの全アニメを
 *       1 本ずつ強制再生して録ったもの (実測 316 アニメ × 20 フレーム = 6320)。
 *       <b>どの run でも使える</b>。引くのは tick ではなく `.anims.json` の from/to。</li>
 * </ul>
 *
 * <p>索引自身は種別を名乗らない (どちらも `SimPoseCodec.writeIndex` が書く同じ形)。
 * 見分けは<b>隣に `.anims.json` があるか</b>で行う —— `viewer/score-hold.mjs` が既にこの判定を
 * しており、<b>索引にフィールドを足すより小さく、しかも 8.1GB の既存ライブラリを
 * 録り直さずに効く</b>。
 *
 * <p><b>ライブラリを時間で突き合わせてはいけない。</b> ライブラリに run の身元は原理的に無く、
 * `gt0` は sweep を回した時刻でしかない。2026-08-24 まで `findPoseFor` はこれを区別せず、
 * ライブラリをタイムラインとして吸着させて `base=-104869` を出していた。
 */
export function isPoseLibrary(poseJsonPath) {
  return fs.existsSync(animsPathFor(poseJsonPath));
}

/** `<stamp>.pose.json` → `<stamp>.anims.json`。 */
export function animsPathFor(poseJsonPath) {
  return poseJsonPath.replace(/\.pose\.json$/, '.anims.json');
}

/**
 * アニメライブラリを探す。**時間では突き合わせない** —— どの run でも使えるので、
 * 「一番新しいもの」を採る。
 *
 * @returns `{ file, root, name, index, anims }` または null。
 *          `anims` は `[{ anim, from, to, length }, …]`。
 */
export function findPoseLibrary(roots) {
  let best = null;
  for (const root of roots) {
    if (!fs.existsSync(root)) continue;
    let names;
    try {
      names = fs.readdirSync(root);
    } catch {
      continue;
    }
    for (const name of names) {
      if (!name.endsWith('.pose.json')) continue;
      const file = path.join(root, name);
      if (!isPoseLibrary(file)) continue;
      let index;
      let anims;
      try {
        index = JSON.parse(fs.readFileSync(file, 'utf8'));
        const raw = JSON.parse(fs.readFileSync(animsPathFor(file), 'utf8'));
        // 書き手の形ゆれを 1 箇所で吸収する (score-hold.mjs と同じ規則)。
        anims = raw.anims || raw.ranges || raw;
      } catch {
        continue;
      }
      if (!Array.isArray(anims) || !anims.length) continue;
      // 新しいほうを採る。名前は `<stamp>` なので辞書順 = 時刻順。
      if (!best || name > best.name) {
        best = { file, root, name, index, anims };
      }
    }
  }
  return best;
}

/**
 * トレースの「身元」を読む。{@link readTraceMeta} が返す meta に加えて、
 * **実測の最終 tick** と **霊夢 (role=reimu) の spawn 行** を拾う。
 *
 * <p><b>なぜ実測 tick が要るのか</b>: meta の `duration` は<b>シナリオが宣言した</b>長さで、
 * 実際に走った長さではない。tank は `duration: 1728000` (24 時間) を宣言するので、
 * 宣言でトレースの窓を取ると **1 .. 1,728,001** になり、**過去のあらゆる姿勢 companion を
 * 飲み込む**。2026-08-24 実測: `gameTime=1` のトレースに `gt0=104870` の companion が
 * 吸着し、`base=-104869` で実機頂点が 1 フレームも使われていなかった。
 *
 * <p><b>なぜ霊夢の spawn 行が要るのか</b>: `uuid` が run を一意に決める鍵だから
 * (2026-08-23 に spawn へ追加済み)。
 *
 * @returns `{ gameTime, duration, scenario, lastTick, reimu: { id, uuid, type } | null }`、
 *          または meta が読めなければ `null`
 */
export function readTraceIdentity(file) {
  const meta = readTraceMeta(file);
  if (!meta) return null;
  return Object.assign({}, meta, {
    lastTick: readLastTick(file),
    reimu: readReimuSpawn(file),
  });
}

/** 末尾チャンクだけを読んで、解釈できた行の最大 `t` を返す。読めなければ null。 */
function readLastTick(file) {
  const TAIL = 64 * 1024;
  let fd;
  try {
    fd = fs.openSync(file, 'r');
  } catch {
    return null;
  }
  try {
    const size = fs.fstatSync(fd).size;
    const want = Math.min(TAIL, size);
    const buf = Buffer.alloc(want);
    fs.readSync(fd, buf, 0, want, size - want);
    const text = buf.toString('utf8');
    const lines = text.split('\n');
    // 先頭行は途中から切れている可能性があるので、ファイル全体を読んだのでない限り捨てる。
    const complete = want === size ? lines : lines.slice(1);
    let last = null;
    for (const line of complete) {
      if (!line) continue;
      try {
        const e = JSON.parse(line);
        if (typeof e.t === 'number' && (last == null || e.t > last)) last = e.t;
      } catch {
        // 途中で切れた行は無視する
      }
    }
    return last;
  } catch {
    return null;
  } finally {
    fs.closeSync(fd);
  }
}

/**
 * `role":"reimu"` の spawn 行を探して `{ id, uuid, type }` を返す。
 * 霊夢は走り出してすぐとは限らない (実測: t=133) ので、`readTraceMeta` と同じく
 * 先頭チャンクを倍々に広げながら探す。見つからなければ null。
 */
function readReimuSpawn(file) {
  let fd;
  try {
    fd = fs.openSync(file, 'r');
  } catch {
    return null;
  }
  try {
    const size = fs.fstatSync(fd).size;
    let chunkSize = 64 * 1024;
    while (true) {
      const want = Math.min(chunkSize, size);
      const buf = Buffer.alloc(want);
      const n = fs.readSync(fd, buf, 0, want, 0);
      const text = buf.toString('utf8', 0, n);
      const lines = text.split('\n');
      const complete = n < want || want === size ? lines : lines.slice(0, -1);
      for (const line of complete) {
        if (!line.includes('"ch":"spawn"') || !line.includes('"role":"reimu"')) continue;
        try {
          const e = JSON.parse(line);
          if (e.ch === 'spawn' && e.role === 'reimu') {
            return { id: e.id ?? null, uuid: e.uuid ?? null, type: e.type ?? null };
          }
        } catch {
          // 壊れた行は無視して次の候補を探す
        }
      }
      if (want >= size) return null;
      chunkSize *= 4;
    }
  } catch {
    return null;
  } finally {
    fs.closeSync(fd);
  }
}

/**
 * companion 突き合わせの共有コア。{@link findPoseFor} と {@link findPaletteFor}
 * (14-03) が両方これを呼ぶ —— **2つの独立したマッチャーを作らない**。uuid hard gate の
 * 理由 (`SimPoseTrace.java:658-664` の設計) は companion の種類に依らず同じ論拠なので、
 * ロジックを1箇所にまとめる。
 *
 * <p><b>UUID は優先順位ではなく hard gate</b> —— 「UUID が合わなければ type/id で代わりに
 * 合わせる」ことは<b>しない</b>。合わない companion は run が違うので、代わりに出せるものは無い。
 * 順序は次のとおりで、上で落ちたものは下へ回らない:
 *
 * <ol>
 *   <li>両方に uuid がある → <b>不一致なら即拒否</b></li>
 *   <li>トレースに uuid があり companion に無い (v1) → <b>自動採用しない</b>
 *       (`opts.allowV1` を明示したときだけ候補に残る = 手動指定の経路)</li>
 *   <li>トレースに uuid が無い (旧トレース) → `type`/`id` の一致を要求してから重なりを見る</li>
 *   <li>ここを通ったものだけ、<b>実測 tick 範囲</b>で重なりを計算し最大を採る</li>
 * </ol>
 *
 * @param identity {@link readTraceIdentity} の返り値
 * @param roots    探索するディレクトリの配列
 * @param opts     `{ allowV1 }` —— v1 companion を手動で使いたいときだけ true
 * @param cfg      `{ ext, label, skip(file) => reason|null, getGt0(idx), getSlotsLen(idx) }`
 *                 —— companion の種類ごとの拡張子・除外規則・索引からの読み方だけを渡す
 * @returns `{ match, rejected }`。`match` は見つからなければ null、`rejected` は
 *          `{ name, reason }` の配列 (Viewer が「なぜ出ないか」を言えるようにするため)
 */
function matchByIdentity(identity, roots, opts, cfg) {
  const rejected = [];
  if (!identity || identity.gameTime == null) {
    return { match: null, rejected };
  }
  const gameTime = identity.gameTime;
  const traceUuid = identity.reimu ? identity.reimu.uuid : null;

  // **宣言 duration ではなく実測 tick 範囲**。lastTick が読めなければ 0 tick 幅として扱う
  // (宣言値へフォールバックしない —— それがこの関数を壊していた当のものだから)。
  const span = identity.lastTick != null ? identity.lastTick : 0;
  const traceStart = gameTime;
  const traceEnd = gameTime + span + 1;   // lastTick を含む半開区間

  let best = null;
  let bestOverlap = 0;
  for (const root of roots) {
    if (!fs.existsSync(root)) continue;
    let names;
    try {
      names = fs.readdirSync(root);
    } catch {
      continue;
    }
    for (const name of names) {
      if (!name.endsWith(cfg.ext)) continue;
      const file = path.join(root, name);
      if (cfg.skip) {
        const skipReason = cfg.skip(file);
        if (skipReason) {
          rejected.push({ name, reason: skipReason });
          continue;
        }
      }
      let idx;
      try {
        idx = JSON.parse(fs.readFileSync(file, 'utf8'));
      } catch {
        rejected.push({ name, reason: '索引が読めない (壊れた JSON)' });
        continue;
      }
      const gt0 = cfg.getGt0(idx);
      const slotsLen = cfg.getSlotsLen(idx);
      if (gt0 == null || slotsLen === 0) {
        rejected.push({ name, reason: 'gt0 か slots が無い' });
        continue;
      }

      let trust;
      if (traceUuid && idx.uuid) {
        if (idx.uuid !== traceUuid) {
          rejected.push({ name, reason: `別 run の${cfg.label} (uuid ${idx.uuid} ≠ ${traceUuid})` });
          continue;
        }
        trust = 'uuid';
      } else if (traceUuid && !idx.uuid) {
        if (!opts.allowV1) {
          rejected.push({
            name,
            reason: 'v1 (uuid 無し) はどの run のものか判らないので自動では使わない',
          });
          continue;
        }
        trust = 'manual-v1';
      } else {
        // 旧トレース (uuid が無い)。せめて誰を撮ったものかは合わせる。
        const wantType = identity.reimu ? identity.reimu.type : null;
        const wantId = identity.reimu ? identity.reimu.id : null;
        if (wantType && idx.type && idx.type !== wantType) {
          rejected.push({ name, reason: `type が違う (${idx.type} ≠ ${wantType})` });
          continue;
        }
        if (wantId != null && idx.id != null && idx.id !== wantId) {
          rejected.push({ name, reason: `entity id が違う (${idx.id} ≠ ${wantId})` });
          continue;
        }
        trust = 'legacy';
      }

      const cStart = gt0;
      const cEnd = gt0 + slotsLen;
      const overlap = Math.max(0, Math.min(traceEnd, cEnd) - Math.max(traceStart, cStart));
      if (overlap <= 0) {
        rejected.push({
          name,
          reason: `実測 tick 範囲と重ならない (trace [${traceStart},${traceEnd}) / ${cfg.label} [${cStart},${cEnd}))`,
        });
        continue;
      }
      if (overlap > bestOverlap) {
        bestOverlap = overlap;
        best = { file, root, name, index: idx, base: gameTime - gt0, overlap, span, trust };
      }
    }
  }
  return { match: bestOverlap > 0 ? best : null, rejected };
}

/**
 * トレースに対応する姿勢 companion (`<stamp>.pose.json`) を探す。
 * 突き合わせ本体は {@link matchByIdentity}。ここは pose 固有の2点
 * (拡張子・アニメライブラリの除外) だけを渡す。
 *
 * @param identity {@link readTraceIdentity} の返り値
 * @param roots    {@link poseRoots} の返り値
 * @param opts     `{ allowV1 }` —— v1 companion を手動で使いたいときだけ true
 * @returns `{ match, rejected }`
 */
export function findPoseFor(identity, roots, opts = {}) {
  return matchByIdentity(identity, roots, opts, {
    ext: '.pose.json',
    label: '姿勢',
    // **アニメライブラリは時間で突き合わせない。** run の身元を持たないので、
    // 時間で吸着させると必ず嘘になる (それが base=-104869 の正体)。
    // ライブラリは findPoseLibrary が別経路で扱い、アニメ名で引く。
    skip: (file) => (isPoseLibrary(file) ? 'アニメライブラリ (run 録画ではない) — アニメ名で引くもの' : null),
    getGt0: (idx) => idx.gt0,
    getSlotsLen: (idx) => (Array.isArray(idx.slots) ? idx.slots.length : 0),
  });
}

/**
 * トレースに対応する palette companion (`<stamp>.pal.json`) を探す (14-03)。
 * `SimPaletteTrace` は `gt0`/`uuid` を `SimPoseTrace` から借りる (14-02) ので、
 * pose と**同じ uuid hard gate**がそのまま成立する —— 時間窓フォールバックは無い。
 * palette にアニメライブラリの概念は無いので `skip` は無し。
 *
 * @param identity {@link readTraceIdentity} の返り値
 * @param roots    {@link poseRoots} の返り値 (palette companion も同じ `poses/` 系に置く)
 * @param opts     `{ allowV1 }` —— v1 companion を手動で使いたいときだけ true
 * @returns `{ match, rejected }`
 */
export function findPaletteFor(identity, roots, opts = {}) {
  return matchByIdentity(identity, roots, opts, {
    ext: '.pal.json',
    label: 'palette',
    skip: null,
    getGt0: (idx) => idx.gt0,
    getSlotsLen: (idx) => (Array.isArray(idx.slots) ? idx.slots.length : 0),
  });
}
