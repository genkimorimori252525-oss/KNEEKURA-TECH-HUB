#!/usr/bin/env node
// SimLab local server — Viewer を配信し、トレース / 音 / テクスチャ / YSM モデルを返す。
//
//   node simlab/serve.mjs            → http://localhost:8777
//   node simlab/serve.mjs --port 9000
//
// WebGL 版 Viewer はテクスチャを取りに来るので、必ずこのサーバ経由で開くこと
// (file:// だとテクスチャも音も読めない)。

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import { fileURLToPath } from 'node:url';
import { poseRoots, readTraceIdentity, findPoseFor, findPoseLibrary, findPaletteFor } from './pose.mjs';
import { spawn, execFileSync } from 'node:child_process';
import { analyze } from './analyze.mjs';
import { rcon } from './rcon.mjs';
import { parseTrace } from './stats.mjs';
import { createLivePaletteHub } from './live-palette.mjs';

/**
 * 走っている runSim。**同時に1本だけ。**
 * 2本目を起動してもワールドが掴まれていて立ち上がらない（2026-08-20 実測）ので、
 * 受け付けずに 409 を返す方が正直。
 */
let simRun = null;

/** /api/analyze の結果を mtime を鍵に1件だけ持つ。返す値は常に analyze() の出力。 */
let analyzeCache = { file: null, mtime: 0, json: '' };

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const VIEWER = path.join(HERE, 'viewer');
const TRACES = path.join(ROOT, 'run', 'sim', 'traces');
const FIXTURES = path.join(HERE, 'fixtures');
// palette (14-01) の fixture 名 -> ファイル basename の固定 allow-list (T-14-02)。
// クエリの ?fixture= をそのままパスに使わない —— 必ずこの表を経由する。
const PAL_FIXTURES = { golden: 'palette-golden' };
const MOD_ASSETS = path.join(ROOT, 'src', 'main', 'resources', 'assets');
const DOT_MC = path.join(process.env.APPDATA || path.join(process.env.HOME || '', '.config'), '.minecraft');
const DOT_MC_SIMLAB = path.join(process.env.APPDATA || path.join(process.env.HOME || '', '.config'), '.minecraft-simlab');
const YSM_DIR = path.join(DOT_MC, 'config', 'yes_steve_model', 'custom');

const argPort = process.argv.indexOf('--port');
const PORT = argPort > 0 ? Number(process.argv[argPort + 1]) : 8777;
const argPalettePort = process.argv.indexOf('--palette-port');
const rawPalettePort = argPalettePort > 0 ? Number(process.argv[argPalettePort + 1]) : 8778;
const PALETTE_PORT = Number.isInteger(rawPalettePort) && rawPalettePort > 0 && rawPalettePort <= 65535
  ? rawPalettePort : 8778;
const livePaletteHub = createLivePaletteHub({ host: '127.0.0.1', port: PALETTE_PORT });
livePaletteHub.start()
  .then((address) => console.log(`  palette: tcp://127.0.0.1:${address.port} (memory only)`))
  .catch((error) => console.error(`[palette] loopback receiver を開始できない: ${error.message}`));

// =============================================================================
// client jar (zip) の最小リーダ
// =============================================================================
// バニラのブロック/モブのテクスチャは .minecraft の client jar の中にしかない。
// Node に zip 展開は無いので、中央ディレクトリを読んで inflateRaw する分だけ自前で持つ。

function findClientJar() {
  const dir = path.join(DOT_MC, 'versions');
  if (!fs.existsSync(dir)) return null;
  // 素の 1.20.1 を最優先 (forge/optifine 版も中身のアセットは同じ)
  const prefer = ['1.20.1'];
  const names = fs.readdirSync(dir);
  for (const p of prefer) {
    const j = path.join(dir, p, p + '.jar');
    if (fs.existsSync(j)) return j;
  }
  for (const n of names) {
    if (!n.startsWith('1.20.1')) continue;
    const j = path.join(dir, n, n + '.jar');
    if (fs.existsSync(j)) return j;
  }
  return null;
}

class Zip {
  constructor(file) {
    this.buf = fs.readFileSync(file);
    this.index = new Map();
    this.#readCentralDirectory();
  }
  #readCentralDirectory() {
    const b = this.buf;
    // EOCD (0x06054b50) を末尾から探す
    let eocd = -1;
    for (let i = b.length - 22; i >= Math.max(0, b.length - 66000); i--) {
      if (b.readUInt32LE(i) === 0x06054b50) { eocd = i; break; }
    }
    if (eocd < 0) throw new Error('zip: EOCD not found');
    const count = b.readUInt16LE(eocd + 10);
    let p = b.readUInt32LE(eocd + 16);
    for (let i = 0; i < count; i++) {
      if (b.readUInt32LE(p) !== 0x02014b50) break;
      const method = b.readUInt16LE(p + 10);
      const csize = b.readUInt32LE(p + 20);
      const size = b.readUInt32LE(p + 24);
      const nameLen = b.readUInt16LE(p + 28);
      const extraLen = b.readUInt16LE(p + 30);
      const commentLen = b.readUInt16LE(p + 32);
      const local = b.readUInt32LE(p + 42);
      const name = b.toString('utf8', p + 46, p + 46 + nameLen);
      this.index.set(name, { method, csize, size, local });
      p += 46 + nameLen + extraLen + commentLen;
    }
  }
  read(name) {
    const e = this.index.get(name);
    if (!e) return null;
    const b = this.buf;
    if (b.readUInt32LE(e.local) !== 0x04034b50) return null;
    const nameLen = b.readUInt16LE(e.local + 26);
    const extraLen = b.readUInt16LE(e.local + 28);
    const start = e.local + 30 + nameLen + extraLen;
    const raw = b.subarray(start, start + e.csize);
    if (e.method === 0) return raw;
    if (e.method === 8) return zlib.inflateRawSync(raw);
    return null;
  }
}

let clientZip = null, clientZipTried = false;
function client() {
  if (!clientZipTried) {
    clientZipTried = true;
    const j = findClientJar();
    if (j) {
      try {
        clientZip = new Zip(j);
        console.log(`  client jar: ${j}  (${clientZip.index.size} entries)`);
      } catch (e) { console.warn('  client jar read failed:', e.message); }
    } else {
      console.warn('  client jar: 見つからない → バニラのテクスチャは出ない');
    }
  }
  return clientZip;
}

// =============================================================================
// テクスチャ解決
// =============================================================================
// id の形:
//   touhou_little_maid:textures/entity/reimu/myouju/red.png  -> repo の assets/
//   minecraft:textures/block/stone.png                       -> client jar
//   ysm:textures/texture2.png                                -> .minecraft/config/yes_steve_model/custom/<pack>/

const ysmPackDir = (() => {
  if (!fs.existsSync(YSM_DIR)) return null;
  const dirs = fs.readdirSync(YSM_DIR).filter((d) => {
    try { return fs.statSync(path.join(YSM_DIR, d)).isDirectory(); } catch { return false; }
  });
  // ysm.json を持つものを採る。複数あれば最初の 1 つ (霊夢用の想定)。
  for (const d of dirs) if (fs.existsSync(path.join(YSM_DIR, d, 'ysm.json'))) return path.join(YSM_DIR, d);
  return null;
})();

function resolveTexture(id) {
  const i = id.indexOf(':');
  const ns = i < 0 ? 'minecraft' : id.slice(0, i);
  const rel = i < 0 ? id : id.slice(i + 1);

  if (ns === 'ysm') {
    if (!ysmPackDir) return null;
    const f = path.join(ysmPackDir, ...rel.split('/'));
    return fs.existsSync(f) ? fs.readFileSync(f) : null;
  }
  if (ns !== 'minecraft') {
    const f = path.join(MOD_ASSETS, ns, ...rel.split('/'));
    if (fs.existsSync(f)) return fs.readFileSync(f);
    // 組み込み TLM custom pack の資産は
    // assets/<ns>/tlm_custom_pack/<pack>/assets/<ns>/... に入っている。
    // モデルdumpは通常の ResourceLocationを返すため、直下だけを見ると404になっていた。
    const packs = path.join(MOD_ASSETS, ns, 'tlm_custom_pack');
    if (fs.existsSync(packs)) {
      for (const pack of fs.readdirSync(packs)) {
        const nested = path.join(packs, pack, 'assets', ns, ...rel.split('/'));
        if (fs.existsSync(nested)) return fs.readFileSync(nested);
      }
    }
    return null;
  }
  // バニラ: まず repo の assets(上書きがあれば)、無ければ client jar
  const over = path.join(MOD_ASSETS, 'minecraft', ...rel.split('/'));
  if (fs.existsSync(over)) return fs.readFileSync(over);
  const z = client();
  return z ? z.read(`assets/minecraft/${rel}`) : null;
}

// =============================================================================
// 音の解決 — soundId (イベント名) -> 実ファイル
// =============================================================================
const soundIndex = { mod: null, vanilla: null };

function loadModSounds(ns) {
  const f = path.join(MOD_ASSETS, ns, 'sounds.json');
  if (!fs.existsSync(f)) return null;
  try { return JSON.parse(fs.readFileSync(f, 'utf8')); } catch { return null; }
}

function loadVanillaIndex() {
  const dir = path.join(DOT_MC, 'assets', 'indexes');
  if (!fs.existsSync(dir)) return null;
  const files = fs.readdirSync(dir).filter((f) => f.endsWith('.json'))
    .map((f) => ({ f, m: fs.statSync(path.join(dir, f)).mtimeMs }))
    .sort((a, b) => b.m - a.m);
  if (!files.length) return null;
  try {
    const idx = JSON.parse(fs.readFileSync(path.join(dir, files[0].f), 'utf8')).objects;
    const objects = path.join(DOT_MC, 'assets', 'objects');
    const h = idx['minecraft/sounds.json']?.hash;
    let sounds = null;
    if (h) {
      const p = path.join(objects, h.slice(0, 2), h);
      if (fs.existsSync(p)) sounds = JSON.parse(fs.readFileSync(p, 'utf8'));
    }
    return { idx, objects, sounds };
  } catch { return null; }
}

function resolveSound(soundId) {
  const [ns, ev] = soundId.includes(':') ? soundId.split(':') : ['minecraft', soundId];
  if (ns !== 'minecraft') {
    if (!soundIndex.mod) soundIndex.mod = loadModSounds(ns) || {};
    const first = soundIndex.mod[ev]?.sounds?.[0];
    const name = typeof first === 'string' ? first : first && first.name;
    if (!name) return null;
    const rel = name.includes(':') ? name.split(':')[1] : name;
    const f = path.join(MOD_ASSETS, ns, 'sounds', ...rel.split('/')) + '.ogg';
    return fs.existsSync(f) ? f : null;
  }
  if (!soundIndex.vanilla) soundIndex.vanilla = loadVanillaIndex() || { idx: {}, objects: '', sounds: {} };
  const v = soundIndex.vanilla;
  const first = v.sounds?.[ev]?.sounds?.[0];
  const name = typeof first === 'string' ? first : first && first.name;
  if (!name) return null;
  const rel = name.includes(':') ? name.split(':')[1] : name;
  const hash = v.idx[`minecraft/sounds/${rel}.ogg`]?.hash;
  if (!hash) return null;
  const f = path.join(v.objects, hash.slice(0, 2), hash);
  return fs.existsSync(f) ? f : null;
}

// =============================================================================
// server
// =============================================================================
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css', '.json': 'application/json', '.jsonl': 'text/plain; charset=utf-8',
  '.ogg': 'audio/ogg', '.png': 'image/png',
  '.mjs': 'text/javascript; charset=utf-8' };

/**
 * 前回の水槽 (だけ) を落とす。**この機械の java を全部殺してはいけない。**
 *
 * 以前は `taskkill /F /IM java.exe` だった。実測 (2026-08-23) では、その一撃で
 * **VSCode の Java 言語サーバ 2 つと Gradle デーモン 2 つも道連れ**になっていた。
 * 巻き添えは黙って起きるので気付きにくい (にーくらの編集環境が突然固まる)。
 *
 * 水槽の JVM だけを名指しできる: ForgeGradle の dev サーバは起動引数に
 * `--launchTarget forgeserveruserdev` と `-Dtlm.sim.*` を持つ (前者は run/sim/logs の
 * ModLauncher 行、後者は build.gradle の sim 実行設定)。どちらも実機の Minecraft にも
 * runClient にも Gradle デーモンにも付かない。2 つ見るのは、片方が引数ファイル経由で
 * コマンドラインに出ない可能性へ備えるため。
 *
 * デーモンを残すのは 2026-08-23 に runSim をデーモン付きで起動するようにしたため ——
 * 毎回殺していたら 10.7 秒の設定時間が縮まらない。
 *
 * PowerShell が使えない環境では**何もしない** (従来の全部殺しへは落とさない)。
 * 落とし損ねたときは新しい水槽が RCON ポートを取れずに目に見えて失敗するので、
 * 巻き添えの被害より復旧がやさしい。
 */
function killTankJava() {
  if (process.platform !== 'win32') return 'win32 以外なので何もしない';
  try {
    const out = execFileSync('powershell', ['-NoProfile', '-NonInteractive', '-Command',
      "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'java.exe' -and ($_.CommandLine -like '*forgeserveruserdev*' -or $_.CommandLine -like '*tlm.sim.*') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue; 'killed ' + $_.ProcessId }"], { encoding: 'utf8' });
    const n = (out.match(/killed /g) || []).length;
    return n ? ('前回の水槽を落とした (' + n + ' プロセス)') : '前回の水槽は居なかった';
  } catch (e) {
    return '前回の水槽を落とせなかった: ' + (e.message || e);
  }
}

/**
 * `gradlew runSim` を起動し、<b>新しいトレースのディレクトリが出来たら</b>完了とみなす。
 *
 * <p><b>ログの "DONE" では判定しない。</b> latest.log には前回の DONE が残っており、
 * それに一致して誤検出する（2026-08-20 に実際に踏んだ）。
 *
 * <p><b>runSim は仕事を終えても JVM が居座る</b>（45秒で DONE を出したのに70分残留した実測）。
 * ワールドが掴まれたままだと次が起動できないので、<b>起動前に前回の残りを終了させる</b>。
 * 実機 Minecraft は `javaw` なので `java.exe` を落としても巻き込まない。
 */
function startSim(scenario) {
  const before = new Set(listTraceDirs());

  // **シナリオが水槽かどうかを、シナリオ自身に訊く。** ここでサイトが判断しない ——
  // keepAlive は mod 側 (SimLab.java:121) が halt を止めるのに使う同じフラグで、
  // 「走らせっぱなしにする」の唯一の定義。サイトはそれを読むだけ。
  let keepAlive = false;
  try {
    const j = JSON.parse(fs.readFileSync(path.join(HERE, 'scenarios', scenario + '.json'), 'utf8'));
    keepAlive = j.keepAlive === true;
  } catch { /* 読めなければバッチ扱い。従来の動作へ倒す。 */ }

  simRun = {
    state: 'running', scenario, keepAlive,
    started: Date.now(), trace: null, error: null,
    tick: null, beatAt: null, stalledMs: null,
  };
  // **この起動が「今の」水槽かどうかを確かめる術。**
  // 立て直すと startSim が前の java を止めるので、古い child の exit が
  // 遅れて飛んでくる。その時点で simRun は既に新しい水槽へ差し替わっているため、
  // ガードしないと**古い後片付けが新しい水槽を error にする**（2026-08-20 実測）。
  const mine = simRun;
  const isMine = () => simRun === mine;

  // 前回の残骸を落とす。**結果を記録する** —— 落とせないと次が起動できない（実測）。
  simRun.killed = killTankJava();

  // **ログを捨てない。** 以前 stdio:'ignore' にしていたせいで、gradlew の起動失敗が
  // 一切見えず「581秒 running のまま新トレース 0」という無音の失敗になった。
  const logPath = path.join(ROOT, 'run', 'sim', 'runsim-last.log');
  fs.mkdirSync(path.dirname(logPath), { recursive: true });
  const logFd = fs.openSync(logPath, 'w');
  simRun.log = 'run/sim/runsim-last.log';

  // **絶対パスで渡す。** shell:true のとき、コマンド名は cwd ではなく PATH からしか
  // 探されない。'gradlew.bat' と書いていたせいで
  // 「'gradlew.bat' は…認識されていません」で exit 1 していた（2026-08-20 実測）。
  const gradlew = path.join(ROOT, process.platform === 'win32' ? 'gradlew.bat' : 'gradlew');
  // **detached: 水槽は Viewer サーバより長生きする。**
  // 子プロセスのままだと serve.mjs を止めた瞬間に水槽も死ぬ（2026-08-20 実測:
  // 再起動したら心拍が 172 秒前で止まっていた）。心拍という「状態の共有」を用意しても、
  // プロセスの寿命が親に縛られていては拾い上げようがない。
  // 水槽は実験の対象、Viewer はそれを覗く窓 —— 窓を閉じても水槽は在るべき。
  // 止まるのは明示的な操作 (/api/run/stop) か、水槽自身が終わったときだけ。
  /* **runSim のときだけ Gradle デーモンを使う。**
     実測 (2026-08-23): Gradle の設定だけで **10.7 秒** かかっており、水槽が動き出すまでの
     約 62 秒のうち 1/6 がここだった。デーモンを使うと 2 回目以降は **1.7 秒**。

     なぜ既定が false なのか (覆す前に読んだこと): gradle.properties:2 の
     org.gradle.daemon=false は初回スナップショット (3258f374, 2026-05-20) から、隣の
     org.gradle.vfs.watch=false と一緒に入っている Windows のファイル監視/ロック対策。
     ただし CLAUDE.md の 2026-08-21 の訂正のとおり、**実在するロックは「Minecraft 起動中に
     reobfShadowJar が .minecraft/mods へ jar をコピーする」ほう**で、デーモンが原因だという
     測定はリポジトリに残っていない。

     より小さい変更で同じ利益を得る: gradle.properties は触らない ——
     **この 1 箇所 (runSim の起動) だけ**を上書きする。reobfShadowJar を含む他のすべての
     gradlew 呼び出しは今までどおり daemon=false のまま。

     何が出たら撤回するか: 水槽を回した後に reobfShadowJar がロックで落ちる、または
     `gradlew --status` に BUSY が居座って次のビルドが待たされる。そのときはこの 2 行を戻す。 */
  const child = spawn(process.platform === 'win32' ? `"${gradlew}"` : gradlew,
    ['runSim', '-Pscenario=' + scenario, '--offline', '--console=plain',
      '-Dorg.gradle.daemon=true', '-Dorg.gradle.daemon.idletimeout=1800000'],
    { cwd: ROOT, stdio: ['ignore', logFd, logFd], shell: true, detached: true, windowsHide: true });
  // 親のイベントループを水槽に縛りつけない。exit は引き続き聞ける。
  child.unref();

  child.on('error', (e) => {
    if (!isMine()) return;
    simRun.state = 'error';
    simRun.error = 'gradlew を起動できなかった: ' + e;
  });
  // **exit を必ず聞く。** shell:true だと spawn 自体は成功するので、
  // 中で失敗しても error イベントは飛んでこない。ここを聞かないと永久に running になる。
  child.on('exit', (code) => {
    // **自分の run でなければ黙って去る。** 立て直しで殺された前の水槽の exit が、
    // 新しい水槽を error にしていた。
    if (!isMine()) return;
    simRun.exitCode = code;
    if (simRun.state === 'running' && code !== 0) {
      simRun.state = 'error';
      simRun.error = 'gradlew が exit ' + code + ' で終了した（' + simRun.log + ' を見る）';
    } else if (simRun.state === 'live') {
      // **水槽が勝手に死んだ。** これが一番確実な死亡判定 —— 脈より速く、確実。
      // にーくらが止めた場合は stopTank が先に state を 'stopped' にしているのでここへ来ない。
      // 実測 (2026-08-20): tank.json が弾かれて smoke が完走・halt したのに live のままだった。
      simRun.state = 'error';
      simRun.error = '水槽のプロセスが終了した (exit ' + code + ')。' + simRun.log + ' を見る';
      if (pulseTimer) { clearInterval(pulseTimer); pulseTimer = null; }
    }
  });

  // 新しいディレクトリの出現を待つ。runSim は終了しないので、プロセスの終了は待たない。
  const deadline = Date.now() + 10 * 60 * 1000;
  const tick = setInterval(() => {
    if (!isMine()) { clearInterval(tick); return; }
    if (simRun.state !== 'running') { clearInterval(tick); return; }
    const found = listTraceDirs().find((d) => !before.has(d));
    // **summary.json を待つ。** arena-0.jsonl は走り始めた時点で作られて育っていくので、
    // その存在で完了と判定すると途中の断片を掴む（2026-08-20 実測: 118行で「完了」と誤判定。
    // 完走したトレースは 5,000〜9,700行）。SimRunner は全アリーナが終わってから
    // summary を書くので、それが唯一の正しい終了印。
    // **水槽 (keepAlive) は arena-0.jsonl が出来た時点で「立った」。**
    // summary.json は「実験が終わった印」なので、終わらない水槽では永久に来ない。
    if (simRun.keepAlive && found && fs.existsSync(path.join(TRACES, found, 'arena-0.jsonl'))) {
      clearInterval(tick);
      simRun.state = 'live';
      simRun.trace = path.join(found, 'arena-0.jsonl').split(path.sep).join('/');
      simRun.tookMs = Date.now() - simRun.started;
      simRun.child = child;          // 止めるときに要る。**ここでは殺さない。**
      startPulse();
      return;
    }
    // バッチ (smoke/stairs) は従来どおり。**summary.json を待つ** ——
    // arena-0.jsonl は走り始めた時点で作られて育っていくので、その存在で完了と
    // 判定すると途中の断片を掴む（2026-08-20 実測: 118行で「完了」と誤判定。
    // 完走したトレースは 5,000〜9,700行）。
    if (!simRun.keepAlive && found && fs.existsSync(path.join(TRACES, found, 'summary.json'))
        && fs.existsSync(path.join(TRACES, found, 'arena-0.jsonl'))) {
      clearInterval(tick);
      simRun.state = 'done';
      simRun.trace = path.join(found, 'arena-0.jsonl').split(path.sep).join('/');
      simRun.tookMs = Date.now() - simRun.started;
      try { child.kill(); } catch { /* もう死んでいるかもしれない */ }
      killTankJava();   // 水槽の JVM だけ。VSCode の java や Gradle デーモンは巻き込まない
      return;
    }
    if (Date.now() > deadline) {
      clearInterval(tick);
      simRun.state = 'error';
      simRun.error = '10分待っても新しいトレースが出来なかった（' + simRun.log + ' を見る）';
    }
  }, 2000);
}

/**
 * 脈を打たせる。**水槽が生きていることを、中身とは別に示す。**
 *
 * <p>空の水槽では「誰もいない」と「壊れている」が同じ絵になる。だから脈が要る。
 * tick が進んでいれば生きている。止まれば {@code stalledMs} が伸びる。
 *
 * <p>ファイル全体は読まない —— 水槽は何時間も走り、トレースは際限なく育つ。
 * 末尾だけを読む。
 */
let pulseTimer = null;
function startPulse() {
  if (pulseTimer) clearInterval(pulseTimer);
  // **一度も心拍が来ていない場合の起点。** これが無いと stalledMs が null のままになり、
  // 「まだ来ていない」と「止まった」が区別できず、どちらも無音になる（実測で踏んだ穴）。
  const from = Date.now();
  pulseTimer = setInterval(() => {
    if (!simRun || simRun.state !== 'live') { clearInterval(pulseTimer); pulseTimer = null; return; }
    const hb = readHeartbeat();
    if (hb && hb.tick !== simRun.tick) {
      simRun.tick = hb.tick;
      simRun.beatAt = Date.now();
      simRun.stalledMs = 0;
    } else {
      simRun.stalledMs = Date.now() - (simRun.beatAt || from);
    }
  }, 1000);
}

/**
 * 心拍を読む。**水槽が生きているかの唯一の判定。**
 *
 * <p>mod 側の SimHeartbeat が outRoot 直下の固定パスへ 1 秒ごとに上書きする。
 * トレースではなくこれを見る理由: **空の水槽ではトレースが 1 行も育たない**
 * （誰も居なければ ch:pos も ch:ai も出ない。2026-08-20 実測）。
 *
 * <p>固定パスなので、**この Viewer サーバを再起動しても走っている水槽を見失わない**。
 *
 * @returns {{tick:number, scenario:string, trace:string, ageMs:number, alive:boolean}|null}
 */
const HEARTBEAT_DEAD_MS = 10_000;   // 10 秒来なければ死んだとみなす (心拍は 1 秒ごと)

/**
 * 水槽へコマンドを送ってよいか。**メモリ上の simRun だけで判断しない。**
 *
 * この Viewer サーバを再起動すると simRun は消えるが、水槽(Minecraft)は走ったままで、
 * 心拍はファイルに在る —— /api/run/status はその場合を拾う作りになっているのに、
 * 操作系(summon / kill / itemttl)は simRun だけを見ていたので、拾い直した水槽には
 * 何も送れなくなっていた(2026-08-23 に気付いた既存の穴)。判定をここ 1 つにする。
 */
function tankIsLive() {
  if (simRun && simRun.state === 'live') return true;
  const hb = readHeartbeat();
  return !!(hb && hb.alive);
}
function readHeartbeat() {
  try {
    const j = JSON.parse(fs.readFileSync(path.join(TRACES, 'heartbeat.json'), 'utf8'));
    if (typeof j.atMs !== 'number' || typeof j.tick !== 'number') return null;
    const ageMs = Date.now() - j.atMs;
    return { ...j, ageMs, alive: ageMs >= 0 && ageMs < HEARTBEAT_DEAD_MS };
  } catch {
    // 無い / 壊れている / 書き込みの最中。次の 1 秒で読み直せばよい。
    return null;
  }
}

/** 水槽を止める。**にーくらが押したときだけ。** */
function stopTank() {
  if (pulseTimer) { clearInterval(pulseTimer); pulseTimer = null; }
  if (simRun && simRun.child) { try { simRun.child.kill(); } catch { /* 既に死んでいるかも */ } }
  if (process.platform === 'win32') {
    killTankJava();   // 水槽の JVM だけ。VSCode の java や Gradle デーモンは巻き込まない
  }
  if (simRun) { simRun.state = 'stopped'; simRun.child = null; }
}

/** `<scenario>/<date>/<stamp>` の一覧。新しい run の検出に使う。 */
function listTraceDirs() {
  const out = [];
  if (!fs.existsSync(TRACES)) return out;
  for (const a of fs.readdirSync(TRACES, { withFileTypes: true })) {
    if (!a.isDirectory()) continue;
    for (const b of fs.readdirSync(path.join(TRACES, a.name), { withFileTypes: true })) {
      if (!b.isDirectory()) continue;
      for (const c of fs.readdirSync(path.join(TRACES, a.name, b.name), { withFileTypes: true })) {
        if (c.isDirectory()) out.push(path.join(a.name, b.name, c.name));
      }
    }
  }
  return out;
}

/** シナリオ名の一覧（Viewer の選択肢）。 */
function listScenarios() {
  const dir = path.join(HERE, 'scenarios');
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir).filter((f) => f.endsWith('.json')).map((f) => f.slice(0, -5)).sort();
}

function listTraces(dir, base = '') {
  const out = [];
  if (!fs.existsSync(dir)) return out;
  for (const name of fs.readdirSync(dir)) {
    const p = path.join(dir, name), rel = base ? `${base}/${name}` : name;
    const st = fs.statSync(p);
    if (st.isDirectory()) out.push(...listTraces(p, rel));
    else if (name.endsWith('.jsonl')) out.push({ path: rel, size: st.size, mtime: st.mtimeMs });
  }
  return out.sort((a, b) => b.mtime - a.mtime);
}

function send(res, code, body, type = 'text/plain; charset=utf-8', cache = 'no-store') {
  res.writeHead(code, { 'content-type': type, 'cache-control': cache });
  res.end(body);
}

http.createServer((req, res) => {
  const u = new URL(req.url, 'http://localhost');
  try {
    /* fps が落ちた瞬間の計器一式を受け取って残す (2026-08-25)。
     *
     * **なぜ要るか**: にーくらの「戦闘が終わったら fps が落ちる」は、2026-08-25 の調査で
     * 再現できなかった —— 10 分の水槽 (tick 19,000) でも 163fps 平坦、258,016 tick の
     * 録画再生でも 161.8fps。条件が私の手元に無い (実クライアント・数時間の水槽)。
     *
     * 再現できない症状を推測で直すのが、このリポジトリで最も高くついた失敗なので、
     * **次に起きた瞬間の数字を自動で捕まえる**ほうを作る。Viewer が自分で気づいて
     * ここへ投げ、こちらはファイルに落とすだけ (解釈しない)。
     */
    if (u.pathname === '/api/perfdump' && req.method === 'POST') {
      const chunks = [];
      let bytes = 0;
      req.on('data', (c) => {
        bytes += c.length;
        // 上限を超えたら捨てる。**Viewer から来る JSON にサーバの寿命を預けない。**
        if (bytes <= 4 * 1024 * 1024) chunks.push(c);
      });
      req.on('end', () => {
        try {
          const dir = path.join(TRACES, "..", "perf");
          fs.mkdirSync(dir, { recursive: true });
          const stamp = new Date().toISOString().replace(/[:.]/g, "-");
          const file = path.join(dir, stamp + ".json");
          fs.writeFileSync(file, Buffer.concat(chunks));
          console.log("[perf] fps 低下の記録を受けた -> " + file + "  (" + bytes + " bytes)");
          send(res, 200, JSON.stringify({ ok: true, file: file }), "application/json");
        } catch (e) {
          send(res, 500, JSON.stringify({ error: String(e.message || e) }), "application/json");
        }
      });
      return;
    }
    if (u.pathname === '/api/scenarios') {
      return send(res, 200, JSON.stringify(listScenarios()), 'application/json');
    }
    if (u.pathname === '/api/traces') {
      return send(res, 200, JSON.stringify(listTraces(TRACES)), 'application/json');
    }
    if (u.pathname === '/api/trace') {
      const file = path.resolve(TRACES, u.searchParams.get('path') || '');
      if (!file.startsWith(TRACES) || !fs.existsSync(file)) return send(res, 404, 'not found');
      return send(res, 200, fs.readFileSync(file), MIME['.jsonl']);
    }
    // シナリオを走らせる —— **Viewer からトレースを「生ませる」**。
    // にーくらがトレースファイルの存在を意識せずに済むようにするのが目的
    // (Phase 12「サイクルを閉じる」の入口。ライブ観戦とシナリオ編集は Phase 12 本体)。
    if (u.pathname === '/api/run') {
      /* **既に水槽が在るなら、新しく立てない。**
         `running` だけを弾いていた頃は、水槽が `live` になった後の /api/run が素通りし、
         startSim() の `taskkill /F /IM java.exe` が**生きている水槽を殺していた**。
         2026-08-21 に実機で発生: にーくらがバッチの「スポーン」を押した瞬間、
         走っていた水槽が exit 1 で落ちた(runsim-last.log に ^C が残る)。
         手(/api/run)は押されたときだけ動くが、**押されても壊してよいわけではない**。
         たたむのは /api/run/stop の仕事。 */
      if (simRun && (simRun.state === 'running' || simRun.state === 'live' || simRun.state === 'stale')) {
        return send(res, 409, JSON.stringify({
          error: '既に水槽が在る。先に「水槽をたたむ」で止める',
          state: simRun.state,
          started: simRun.started,
        }), 'application/json');
      }
      const scenario = (u.searchParams.get('scenario') || 'stairs').replace(/[^a-zA-Z0-9_-]/g, '');
      const scenarioFile = path.join(HERE, 'scenarios', scenario + '.json');
      if (!fs.existsSync(scenarioFile)) {
        return send(res, 404, JSON.stringify({ error: 'シナリオが無い: ' + scenario }), 'application/json');
      }
      startSim(scenario);
      return send(res, 200, JSON.stringify({ ok: true, scenario, started: simRun.started }), 'application/json');
    }
    if (u.pathname === '/api/run/status') {
      // child は JSON にできない (循環参照) ので落とす。
      const { child, ...rest } = simRun || { state: 'idle' };
      const hb = readHeartbeat();
      // **この Viewer サーバを再起動しても、走っている水槽を拾う。**
      // simRun はメモリ上の状態なので再起動で消えるが、心拍はファイルに在る。
      // **simRun が「止まった run」のまま残っていても拾う。**
      // 以前は `!simRun` だけを見ていたので、サイトから一度水槽を立てて止めると、
      // その残骸が居座って**その後に立った水槽を永久に拾えなくなっていた**
      // (2026-08-23 実測: にーくらが 05:43 に立てて止めた run が simRun に残り、
      //  以降に立てた水槽が state:'stopped' と報告され続けた)。
      // 心拍が生きているなら、走っている水槽が在るという事実のほうが強い。
      if ((!simRun || simRun.state !== 'live') && hb && hb.alive) {
        return send(res, 200, JSON.stringify({
          state: 'live', scenario: hb.scenario,
          trace: hb.trace + '/arena-0.jsonl',
          tick: hb.tick, stalledMs: hb.ageMs, adopted: true, heartbeat: hb,
        }), 'application/json');
      }
      // **心拍が途絶えていたら live を名乗らせない。** 監視カメラが止まった絵を
      // 映し続けるのが最悪の壊れ方（2026-08-20 に実際に作った）。
      if (rest.state === 'live' && hb && !hb.alive) {
        rest.state = 'stale';
        rest.error = '心拍が ' + Math.round(hb.ageMs / 1000) + ' 秒来ていない';
      }
      return send(res, 200, JSON.stringify({ ...rest, heartbeat: hb }), 'application/json');
    }
    // 水槽を止める。**手を入れる操作なので、明示的に呼ばれたときだけ。**
    if (u.pathname === '/api/run/stop') {
      stopTank();
      return send(res, 200, JSON.stringify({ ok: true, state: simRun ? simRun.state : 'idle' }), 'application/json');
    }

    // 放てるモブの一覧。**jar が書いたものをそのまま返す。**
    // ここで絞り込みも並べ替えもしない —— サイトがモブについて判断を持たないため。
    // mods/ に mod を足せば内容が変わり、サイト側の対応は要らない (SimCatalog.java)。
    if (u.pathname === '/api/entities') {
      const f = path.join(TRACES, 'entities.json');
      if (!fs.existsSync(f)) {
        return send(res, 404, JSON.stringify({
          error: '一覧がまだ無い。水槽を一度起動すると jar が書き出す。',
        }), 'application/json');
      }
      return send(res, 200, fs.readFileSync(f, 'utf8'), 'application/json');
    }

    // 実クライアントの post-geoRender palette。トレース SSE とは混ぜず、UUID で fail closed に
    // 絞る。履歴は livePaletteHub の短いメモリ窓だけで、ファイル companion は読まない。
    if (u.pathname === '/api/live-palette/status') {
      const uuid = (u.searchParams.get('uuid') || '').toLowerCase();
      const modelId = u.searchParams.get('model') || '';
      if (uuid && !livePaletteHub.validUuid(uuid)) {
        return send(res, 400, JSON.stringify({ error: 'uuid が不正' }), 'application/json');
      }
      return send(res, 200, JSON.stringify(uuid
        ? livePaletteHub.statusFor(uuid, modelId) : livePaletteHub.status()), 'application/json');
    }
    if (u.pathname === '/api/live-palette') {
      const uuid = (u.searchParams.get('uuid') || '').toLowerCase();
      const modelId = u.searchParams.get('model') || '';
      if (!livePaletteHub.validUuid(uuid) || Buffer.byteLength(modelId, 'utf8') > 1024) {
        return send(res, 400, JSON.stringify({ error: 'valid uuid が必須（model は1024 byte以下）' }),
          'application/json');
      }
      res.writeHead(200, {
        'Content-Type': 'text/event-stream; charset=utf-8',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      });
      let closed = false;
      let blocked = false;
      let pendingFrame = null;
      let pendingStatus = false;
      const write = (event, data) => {
        if (closed) return;
        if (blocked) {
          if (event === 'frame') pendingFrame = data; // latest-only。遅いブラウザへ履歴を積まない。
          else pendingStatus = true;
          return;
        }
        blocked = !res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);
      };
      const status = () => write('status', livePaletteHub.statusFor(uuid, modelId));
      const unsubscribe = livePaletteHub.subscribe({ uuid, modelId }, (event) => {
        if (event.type === 'frame') write('frame', livePaletteHub.publicFrame(event.frame));
        else status();
      });
      res.on('drain', () => {
        blocked = false;
        if (pendingStatus) { pendingStatus = false; status(); }
        if (!blocked && pendingFrame) {
          const frame = pendingFrame; pendingFrame = null; write('frame', frame);
        }
      });
      const beat = setInterval(status, 1000);
      req.on('close', () => {
        closed = true;
        clearInterval(beat);
        unsubscribe();
      });
      return;
    }

    // 走っている水槽を追尾して流す。**カメラ —— 中を一切変えない。**
    //
    // 既定は「最初から」。水槽が立った瞬間からの全部を送ってから、
    // 以後は増えた分だけ送り続ける。ブラウザ側はこれを溜めるので、
    // **巻き戻しはブラウザの中で完結する**（にーくらの「1. 確かに必要だね」への答え）。
    if (u.pathname === '/api/live') {
      const hb = readHeartbeat();
      if (!hb || !hb.alive) {
        return send(res, 409, JSON.stringify({
          error: '水槽が生きていない', heartbeat: hb,
        }), 'application/json');
      }
      const file = path.join(TRACES, hb.trace, 'arena-0.jsonl');
      res.writeHead(200, {
        'Content-Type': 'text/event-stream; charset=utf-8',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      });

      /* **繋ぎ直しは「続きから」でなければならない。**
         EventSource は接続が切れると勝手に繋ぎ直す。以前ここは常に 0 から送り直して
         いたので、受け手の SimStore へ tick 0 の行が流れ込み、昇順の契約を破って例外 →
         その取り込みバッチが丸ごと失われていた。落ちた行に gone が混ざればモブは
         二度と死なず (死んだ位置に凍りついたまま描かれ続ける)、pos が混ざれば位置がずれる
         —— にーくら 2026-08-23「クリーパーが死んでも描画される」「描画がずれる」の親。
         実測 (8,014 行のトレースを 2 度流す):
           SimStore: ch=log の tick が非単調 (前回tick=483, 今回tick=0)

         SSE の標準の仕組みに乗る: 各行に id (= その行の末尾のバイト位置) を付けて送ると、
         ブラウザは繋ぎ直すときに Last-Event-ID ヘッダで最後に受けた id を返してくる。
         クライアントに覚えさせる仕掛けは要らない。?from= も従来どおり効かせる (手で叩く用)。 */
      // id は "<どの記録か>:<バイト位置>" の形。**どの記録か**を混ぜるのが要点 ——
      // 繋ぎ直しの合間に水槽を立て直すと、同じ位置が別のファイルの途中を指す。その場合は
      // 先頭から読み直さないと spawn 行を取りこぼす (= 素性の判らない箱が永久に残る)。
      const traceKey = String(hb.trace).replace(/[^0-9A-Za-z_-]/g, '');
      let pos = Number(u.searchParams.get('from') || 0);
      const resume = String(req.headers['last-event-id'] || '');
      if (resume) {
        const i = resume.lastIndexOf(':');
        const key = i < 0 ? '' : resume.slice(0, i);
        const off = Number(i < 0 ? resume : resume.slice(i + 1));
        pos = (key === traceKey && Number.isFinite(off) && off > 0) ? off : 0;
      }
      if (!Number.isFinite(pos) || pos < 0) pos = 0;
      // 覚えていた位置がファイルより後ろなら、その位置はもう意味を持たない。
      try { if (pos > fs.statSync(file).size) pos = 0; } catch { pos = 0; }
      let carry = '';           // 行の途中で切れた分を次へ持ち越す
      let closed = false;

      const pump = () => {
        if (closed) return;
        let size;
        try { size = fs.statSync(file).size; } catch { return; }   // まだ無い / 消えた
        if (size < pos) { pos = 0; carry = ''; }                   // 作り直された
        if (size === pos) return;
        const pos0 = pos - Buffer.byteLength(carry, 'utf8');  // carry が始まるバイト位置
        let fd = null;
        let buf;
        try {
          const want = size - pos;
          buf = Buffer.alloc(want);
          fd = fs.openSync(file, 'r');
          fs.readSync(fd, buf, 0, want, pos);
          pos = size;
        } catch {
          return;
        } finally {
          if (fd !== null) { try { fs.closeSync(fd); } catch { /* 続行 */ } }
        }
        // **最後の行は書き込み途中かもしれない。** 完全な行だけ送り、残りは持ち越す。
        const lines = (carry + buf.toString('utf8')).split('\n');
        carry = lines.pop();
        // id はその行までを含めた末尾のバイト位置。繋ぎ直しはここから読み直せばよい
        // (carry = まだ完全でない行 なので、その手前までを送った印になる)。
        let mark = pos0;
        for (const l of lines) {
          mark += Buffer.byteLength(l, 'utf8') + 1;
          if (l.trim()) res.write('id: ' + traceKey + ':' + mark + '\n' + 'data: ' + l + '\n\n');
        }
      };

      // 心拍も流す。**中身が動いていなくても、生きていることが届く。**
      // 空の水槽ではトレースに何も出ないので、これが無いと接続が沈黙して
      // 「繋がっているのか壊れているのか判らない」状態になる。
      const beat = () => {
        if (closed) return;
        const h = readHeartbeat();
        res.write('event: beat\ndata: ' + JSON.stringify(h || { alive: false }) + '\n\n');
      };

      // 100ms 刻み。**ここが「動きの粒」の上限を決める。** 250ms だと 5tick ぶんが
      // まとめて届き、クライアントがどれだけ滑らかに描いてもその粒より細かくは動けない
      // (2026-08-22: クライアント側の取り込みが 1 秒刻みで、1fps の紙芝居になっていた
      // 件を直した際に、サーバ側もこの粒を持っていることが判った)。
      // jar 側の flush は 2 秒→行数の早い方なので、100ms で空振りしても費用は
      // statSync 1 回ぶん。
      const t1 = setInterval(pump, 50);
      const t2 = setInterval(beat, 1000);
      pump();
      beat();
      req.on('close', () => { closed = true; clearInterval(t1); clearInterval(t2); });
      return;
    }

    // モブを放つ。**手を入れる操作。** 押されたときだけ動く。
    if (u.pathname === '/api/summon') {
      if (!tankIsLive()) {
        return send(res, 409, JSON.stringify({ error: '水槽が立っていない' }), 'application/json');
      }
      const type = u.searchParams.get('type') || '';
      // **厳格に検証する。** RCON は任意のコマンドを実行できるので、type に空白や
      // 改行を混ぜられると別のコマンドを走らせられる。EntityType の id が取りうる
      // 文字 (namespace:path) だけを通す。
      if (!/^[a-z0-9_.-]+:[a-z0-9_./-]+$/.test(type)) {
        return send(res, 400, JSON.stringify({
          error: 'type が EntityType の id の形をしていない: ' + type,
        }), 'application/json');
      }
      const num = (k, def) => {
        const v = u.searchParams.get(k);
        if (v === null || v === '') return def;
        const n = Number(v);
        return Number.isFinite(n) ? n : null;
      };
      const x = num('x', 0), y = num('y', 66), z = num('z', 8);
      if (x === null || y === null || z === null) {
        return send(res, 400, JSON.stringify({ error: '座標が数値でない' }), 'application/json');
      }
      // 組み立てるのはバニラの /summon。**Minecraft の構文であって、霊夢の知識ではない。**
      const cmd = 'summon ' + type + ' ' + x + ' ' + y + ' ' + z;
      return rcon(cmd)
        .then((reply) => send(res, 200, JSON.stringify({ ok: true, cmd, reply }), 'application/json'))
        .catch((e) => send(res, 502, JSON.stringify({ error: String(e.message || e), cmd }), 'application/json'));
    }
    // モブを片付ける。**放つ (/api/summon) の対になる操作。** 押されたときだけ動く。
    //
    // バニラの /kill は entity のネットワーク id を取らないので UUID で名指しする
    // (SimProbe.spawn が ch:spawn に uuid を書く。2026-08-23 に足した)。
    // にーくら 2026-08-23「選択したモブを消す方法もほしい」。
    // これは Minecraft の操作であって霊夢の判断ではないので、サイトが持ってよい側。
    if (u.pathname === '/api/kill') {
      if (!tankIsLive()) {
        return send(res, 409, JSON.stringify({ error: '水槽が立っていない' }), 'application/json');
      }
      const uuid = u.searchParams.get('uuid') || '';
      // **厳格に検証する。** RCON は任意のコマンドを実行できるので、空白や改行を
      // 混ぜられると別のコマンドを走らせられる (/api/summon の type 検証と同じ理由)。
      if (!/^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/.test(uuid)) {
        return send(res, 400, JSON.stringify({ error: 'uuid の形をしていない: ' + uuid }), 'application/json');
      }
      const cmd = 'kill ' + uuid;
      return rcon(cmd)
        .then((reply) => send(res, 200, JSON.stringify({ ok: true, cmd, reply }), 'application/json'))
        .catch((e) => send(res, 502, JSON.stringify({ error: String(e.message || e), cmd }), 'application/json'));
    }
    // 落ちた物の寿命。**水槽を実機と違わせる設定**なので、切り替えられる形で置く。
    // にーくら 2026-08-23:「水槽ではドロップアイテムを 1 秒で消すようにしないか？
    // もちろん、任意で ONOFF を切り替えられる方が好ましいかな。」
    if (u.pathname === '/api/tank/itemttl') {
      if (!tankIsLive()) {
        return send(res, 409, JSON.stringify({ error: '水槽が立っていない' }), 'application/json');
      }
      const raw = u.searchParams.get('ticks') || '';
      // /api/kill と同じ理由で厳格に。RCON は任意のコマンドを実行できる。
      if (!/^\d{1,4}$/.test(raw)) {
        return send(res, 400, JSON.stringify({ error: 'ticks は 0〜6000 の整数: ' + raw }), 'application/json');
      }
      const ticks = Number(raw);
      if (ticks > 6000) {
        return send(res, 400, JSON.stringify({ error: 'ticks が大きすぎる: ' + raw }), 'application/json');
      }
      const cmd = 'tlm sim itemttl ' + (ticks === 0 ? 'off' : ticks);
      return rcon(cmd)
        .then((reply) => send(res, 200, JSON.stringify({ ok: true, ticks, cmd, reply }), 'application/json'))
        .catch((e) => send(res, 502, JSON.stringify({ error: String(e.message || e), cmd }), 'application/json'));
    }
    // 解析モジュールそのものを配る。**Viewer は viewer/ の外にある stats.mjs を直接読む。**
    // viewer/ へコピーすると 2 つになり、その瞬間に「同じ計算から出す」(AGENT-01) が壊れる。
    if (u.pathname === '/stats.mjs') {
      return send(res, 200, fs.readFileSync(path.join(HERE, 'stats.mjs')), MIME['.mjs']);
    }
    // 解析結果 —— **CLI が出すものと同じ関数の出力をそのまま返す** (AGENT-01)。
    // サーバ側で数え直したら、その瞬間に Viewer と CLI が食い違いうる状態になる。
    // ガードは /api/trace と同じ path.resolve + startsWith(TRACES)。
    if (u.pathname === '/api/analyze') {
      const file = path.resolve(TRACES, u.searchParams.get('path') || '');
      if (!file.startsWith(TRACES) || !fs.existsSync(file)) return send(res, 404, 'not found');
      const mtime = fs.statSync(file).mtimeMs;
      if (analyzeCache.file === file && analyzeCache.mtime === mtime) {
        return send(res, 200, analyzeCache.json, 'application/json');
      }
      const json = JSON.stringify(analyze(parseTrace(fs.readFileSync(file, 'utf8'))));
      analyzeCache = { file, mtime, json };
      return send(res, 200, json, 'application/json');
    }
    // 姿勢 companion (SimPoseTrace が書いた <stamp>.pose.json / .pose.bin) の索引を返す。
    // トレース本体と同じ path クエリ規約 + ガードを通してから ch:meta の gameTime/duration
    // で companion を突き合わせる (09-01-PLAN Task 2)。
    if (u.pathname === '/api/pose') {
      const file = path.resolve(TRACES, u.searchParams.get('path') || '');
      if (!file.startsWith(TRACES) || !fs.existsSync(file)) return send(res, 404, 'not found');
      const identity = readTraceIdentity(file);
      if (!identity || identity.gameTime == null) return send(res, 404, 'trace meta 未取得 (ch:meta が読めない)');
      // allowV1: 明示したときだけ uuid 無しの旧 companion を候補に残す (手動指定の経路)。
      const allowV1 = u.searchParams.get('allowV1') === '1';
      const { match, rejected } = findPoseFor(identity, poseRoots(), { allowV1 });
      if (!match) {
        // **なぜ姿勢が出ないのかを言う。** 黙って 404 を返すと、Viewer 側は
        // 「録っていない」のか「別 run のものを弾いた」のか区別できない。
        return send(res, 404, JSON.stringify({
          error: 'usable pose companion not found',
          traceUuid: identity.reimu ? identity.reimu.uuid : null,
          lastTick: identity.lastTick,
          rejected,
          hint: rejected.length
            ? 'この run の姿勢がまだ無い。/tlmsim posetrace start で録り直す (allowV1=1 で旧 companion を手動採用できる)'
            : 'まだ姿勢を録っていない (/tlmsim posetrace start で録る)',
        }), 'application/json');
      }
      // ctrl companion (<stamp>.ctrl.jsonl) があれば一緒に返す。
      // YSM の animation controller の遷移条件 (ctrl.idle / ctrl.jump / ctrl.hold(...))
      // を Viewer 側が推測せずに済ませるための実測値 —— 特に onGround は
      // **クライアント側の値でなければならない** (霊夢は仕様上わずかに浮き、
      // サーバ側トレースの phys.onG とは食い違う)。無ければ null のまま。
      let ctrl = null;
      try {
        const cf = match.file.replace(/\.pose\.json$/, '.ctrl.jsonl');
        if (fs.existsSync(cf)) {
          ctrl = fs.readFileSync(cf, 'utf8').split(/\r?\n/)
            .filter((l) => l && l[0] === '{')
            .map((l) => { try { return JSON.parse(l); } catch { return null; } })
            .filter(Boolean);
        }
      } catch { /* 付帯情報なので落ちても本体は返す */ }
      const out = Object.assign({}, match.index, {
        base: match.base,
        ctrl,
        binUrl: '/api/poseframes?file=' + encodeURIComponent(match.index.bin),
        // trust: どうやって突き合わせたか。Viewer の信頼度表示 (S1b) がこれを読む。
        //   'uuid'       —— この run の霊夢の UUID と一致した (唯一の自動採用経路)
        //   'manual-v1'  —— allowV1=1 で人が旧 companion を選んだ
        //   'legacy'     —— トレース側に uuid が無い旧データ (type/id だけ一致)
        trust: match.trust,
        overlap: match.overlap,
        traceLastTick: match.span,
      });
      return send(res, 200, JSON.stringify(out), 'application/json');
    }
    // アニメライブラリ (/tlmsim animsweep が録った「全アニメ 1 本ずつ」の頂点)。
    //
    // **run 録画とは引き方が違う。** run 録画は slots[tick] だが、ライブラリは
    // .anims.json の from/to で「アニメ名 → フレーム範囲」を引く。ライブラリに run の身元は
    // 無いので、トレースとの時間の突き合わせは行わない —— どの run でも使える。
    //
    // Viewer はトレースの anim チャンネル (再生中のアニメ名) をこの表に当てることで、
    // **その run を録画していなくても実機頂点を出せる**。
    if (u.pathname === '/api/poselibrary') {
      const lib = findPoseLibrary(poseRoots());
      if (!lib) {
        return send(res, 404, JSON.stringify({
          error: 'no animation library',
          hint: '/tlmsim animsweep で全アニメを 1 回録ると、以後どの run でも実機頂点が出せる',
        }), 'application/json');
      }
      return send(res, 200, JSON.stringify({
        name: lib.name,
        header: Object.assign({}, lib.index, { slots: undefined, lens: undefined }),
        lens: lib.index.lens || null,
        anims: lib.anims,
        // **bin の URL は返さない。** ライブラリは 8.1GB あり、まるごと読むことは
        // サーバでも (Buffer の上限) ブラウザでも (メモリ) できない。
        // 必要なアニメの分だけ /api/poseanim で取りに来ること。
        animUrl: '/api/poseanim?anim=',
      }), 'application/json');
    }
    // アニメライブラリの**1 アニメ分だけ**を返す (float32 LE、フレーム連結)。
    //
    // **8.1GB をまるごと読まないための口。** フレーム i のバイト位置は
    // cumsum(lens[0..i-1]) * stride * 4、長さは lens[i]*stride*4 ——
    // `viewer/score-hold.mjs` の冒頭が同じ規則を書いている。ここでもその範囲だけ読む。
    // 1 アニメ = 20 フレーム ≒ 20MB なので、run が使う十数種だけ取れば足りる。
    if (u.pathname === '/api/poseanim') {
      const want = u.searchParams.get('anim') || '';
      const lib = findPoseLibrary(poseRoots());
      if (!lib) return send(res, 404, 'no animation library');
      const r = lib.anims.find((a) => a && a.anim === want);
      if (!r) return send(res, 404, 'unknown animation: ' + want);
      const lens = lib.index.lens;
      const stride = lib.index.stride;
      if (!Array.isArray(lens) || !stride) return send(res, 500, 'library index has no lens/stride');
      let start = 0;
      for (let i = 0; i < r.from; i++) start += lens[i];
      let count = 0;
      for (let i = r.from; i <= r.to; i++) count += lens[i];
      const byteStart = start * stride * 4;
      const byteLen = count * stride * 4;
      const binPath = path.join(lib.root, lib.index.bin);
      if (!fs.existsSync(binPath)) return send(res, 404, 'bin not found: ' + lib.index.bin);
      let buf;
      let fd;
      try {
        fd = fs.openSync(binPath, 'r');
        buf = Buffer.alloc(byteLen);
        fs.readSync(fd, buf, 0, byteLen, byteStart);
      } catch (e) {
        return send(res, 500, 'read failed: ' + e.message);
      } finally {
        if (fd !== undefined) fs.closeSync(fd);
      }
      // フレームごとの頂点数も返さないと切り分けられないので、ヘッダに載せる。
      res.setHeader('X-Sim-Lens', lens.slice(r.from, r.to + 1).join(','));
      return send(res, 200, buf, 'application/octet-stream', 'max-age=3600');
    }
    // 姿勢 companion の bin (float32 LE の頂点フレーム列)。file は basename のみを使い、
    // ディレクトリ成分を落としてからルート走査する (/api/trace のガードと同じ意図、T-09-02)。
    if (u.pathname === '/api/poseframes') {
      const name = path.basename(u.searchParams.get('file') || '');
      if (!name) return send(res, 404, 'missing file');
      for (const root of poseRoots()) {
        const f = path.join(root, name);
        if (fs.existsSync(f)) {
          return send(res, 200, fs.readFileSync(f), 'application/octet-stream', 'max-age=60');
        }
      }
      return send(res, 404, 'pose bin not found');
    }
    // palette (14-01) の索引。`?fixture=golden` は committed fixture、`?path=<trace>` は
    // 実機トレース由来の palette companion (14-02 が SimPaletteTrace で録る) を
    // /api/pose と同じ path クエリ規約 + uuid hard gate (findPaletteFor) で解決する (14-03)。
    // palette 索引の**軽い頭だけ**。ライブは 5 秒ごと (CHECKPOINT_EVERY=100 tick) に
    // 索引が伸びるので、Viewer はここを突いて「伸びたか」だけ見る。伸びていたときだけ
    // /api/palette で本体を取り直す —— names は 1058 本のボーン名で、毎回運ぶには重い。
    //
    // 候補の .pal.json は毎回パースし直す (2026-08-25 時点で 4 件 x 14KB、数 ms)。
    // 録画が増えて重くなったら、ここに解決結果のキャッシュを入れるのが第1ノブ。
    if (u.pathname === "/api/palette/head") {
      const file = path.resolve(TRACES, u.searchParams.get("path") || "");
      if (!file.startsWith(TRACES) || !fs.existsSync(file)) return send(res, 404, "not found");
      const identity = readTraceIdentity(file);
      if (!identity || identity.gameTime == null) return send(res, 404, "trace meta 未取得");
      const allowV1 = u.searchParams.get("allowV1") === "1";
      const { match } = findPaletteFor(identity, poseRoots(), { allowV1 });
      if (!match) {
        // **「まだ無い」と「壊れている」を混ぜない。** 呼び出し側はこれを見て
        // 静かに再試行する (録り始める前は 404 が正常)。
        return send(res, 404, JSON.stringify({ error: "no palette companion" }), "application/json");
      }
      const idx = match.index;
      let mtime = 0;
      try { mtime = fs.statSync(match.file).mtimeMs; } catch { /* 消えた直後。0 のままでよい */ }
      return send(res, 200, JSON.stringify({
        mtime,
        frames: idx.frames,
        ticks: Array.isArray(idx.slots) ? idx.slots.length : 0,
        gt0: idx.gt0,
        base: match.base,
      }), "application/json");
    }
    if (u.pathname === '/api/palette') {
      const fixture = u.searchParams.get('fixture') || '';
      if (fixture) {
        const base = PAL_FIXTURES[fixture];
        if (!base) return send(res, 404, JSON.stringify({ error: 'unknown fixture: ' + fixture }), 'application/json');
        const jsonPath = path.join(FIXTURES, path.basename(base) + '.pal.json');
        if (!fs.existsSync(jsonPath)) return send(res, 404, 'fixture index not found: ' + base);
        const idx = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
        idx.binUrl = '/api/palframes?fixture=' + encodeURIComponent(fixture);
        return send(res, 200, JSON.stringify(idx), 'application/json');
      }

      const file = path.resolve(TRACES, u.searchParams.get('path') || '');
      if (!file.startsWith(TRACES) || !fs.existsSync(file)) return send(res, 404, 'not found');
      const identity = readTraceIdentity(file);
      if (!identity || identity.gameTime == null) return send(res, 404, 'trace meta 未取得 (ch:meta が読めない)');
      const allowV1 = u.searchParams.get('allowV1') === '1';
      const { match, rejected } = findPaletteFor(identity, poseRoots(), { allowV1 });
      if (!match) {
        // /api/pose と同じ契約: 「まだ録っていない」のか「別 run のものを弾いた」のかを言う。
        return send(res, 404, JSON.stringify({
          error: 'usable palette companion not found',
          traceUuid: identity.reimu ? identity.reimu.uuid : null,
          lastTick: identity.lastTick,
          rejected,
          hint: rejected.length
            ? 'この run の palette がまだ無い (allowV1=1 で旧 companion を手動採用できる)'
            : 'まだ palette を録っていない (tlm.sim.palette=0 なら録っていない設定)',
        }), 'application/json');
      }

      // 索引を返す前に、Java 側 SimPaletteCodec.readIndex と同じ5つの不変条件を検査する。
      // クラッシュがファイル書き込みの途中で bin と json を裂くことがあるので、
      // 検査は両側に置く (T-14-16) —— 壊れた索引をそのままブラウザへ渡さない。
      const idx = match.index;
      const problems = [];
      const names = Array.isArray(idx.names) ? idx.names : null;
      if (!names || names.length !== idx.bones) {
        problems.push(`names.length(${names ? names.length : 'なし'}) !== bones(${idx.bones})`);
      }
      const frames = idx.frames;
      const lens = Array.isArray(idx.lens) ? idx.lens : null;
      const kinds = Array.isArray(idx.kinds) ? idx.kinds : null;
      if (!lens || !kinds || lens.length !== frames || kinds.length !== frames) {
        problems.push(`lens.length(${lens ? lens.length : 'なし'}) / kinds.length(${kinds ? kinds.length : 'なし'}) !== frames(${frames})`);
      }
      if (kinds && frames > 0 && kinds[0] !== 'K') {
        problems.push(`kinds[0](${kinds[0]}) !== "K"`);
      }
      const slots = Array.isArray(idx.slots) ? idx.slots : [];
      for (let t = 0; t < slots.length; t++) {
        const s = slots[t];
        if (s !== -1 && (s < 0 || s >= frames)) {
          problems.push(`slots[${t}]=${s} は -1 でも [0,${frames}) の範囲でもない`);
          break;
        }
      }
      let binBytes = -1;
      const binPath = path.join(match.root, String(idx.bin || ''));
      try { binBytes = fs.statSync(binPath).size; } catch { /* 下の分岐で not-found として扱う */ }
      if (binBytes < 0) {
        problems.push(`bin が見つからない: ${idx.bin}`);
      } else if (Array.isArray(lens)) {
        const sumLens = lens.reduce((a, b) => a + b, 0);
        if (sumLens !== binBytes) problems.push(`sum(lens)(${sumLens}) !== bin バイト長(${binBytes})`);
      }
      if (problems.length) {
        return send(res, 500, JSON.stringify({ error: 'broken palette index', problems }), 'application/json');
      }

      const out = Object.assign({}, idx, {
        binUrl: '/api/palframes?file=' + encodeURIComponent(idx.bin),
        trust: match.trust,
        overlap: match.overlap,
        // `slots` は palette 自身の tick 空間 (gt - gt0) で並んでいて、トレースの tick 空間
        // とは原点が違う。その差が `base` (= gameTime - gt0、pose.mjs が算出)。
        // /api/pose は最初からこれを返していた (serve.mjs:849) のに palette 側だけ落ちており、
        // ブラウザは slots[トレース tick] と生で引いていた —— 2026-08-25 実測で、
        // 再構成に落ちる tick (400/800) は T.tick >= slots.length(101) で必ず早期 return し、
        // palette が一度も適用されない原因になっていた。
        base: match.base,
        // 索引が伸びたかを Viewer が安く見分けるための札 (/api/palette/head と対)。
        mtime: (() => { try { return fs.statSync(match.file).mtimeMs; } catch { return 0; } })(),
      });
      return send(res, 200, JSON.stringify(out), 'application/json');
    }
    // palette の bin (圧縮済みレコード列)。?from=<byteOffset>&len=<byteLen> で範囲読みする
    // (/api/poseanim の range read と同じ流儀)。`?fixture=` は固定 allow-list 経由のみ
    // (T-14-02)。`?file=` は実機トレース由来の companion を basename のみで poseRoots() を
    // 走査して探す (/api/poseframes の T-09-02 と同じガード、14-03)。from/len は file size と
    // 索引の lens 最大値でクランプする (T-14-03/T-14-13)。
    if (u.pathname === '/api/palframes') {
      const fixture = u.searchParams.get('fixture') || '';
      let binPath = null;
      let maxLen;
      if (fixture) {
        const base = PAL_FIXTURES[fixture];
        if (!base) return send(res, 404, 'unknown fixture: ' + fixture);
        const safeBase = path.basename(base);
        binPath = path.join(FIXTURES, safeBase + '.pal.bin');
        if (!fs.existsSync(binPath)) return send(res, 404, 'fixture bin not found: ' + base);
        maxLen = fs.statSync(binPath).size;
        try {
          const idx = JSON.parse(fs.readFileSync(path.join(FIXTURES, safeBase + '.pal.json'), 'utf8'));
          if (Array.isArray(idx.lens) && idx.lens.length) maxLen = Math.max(...idx.lens);
        } catch { /* 索引が読めなければ file size でクランプ (安全側) */ }
      } else {
        const name = path.basename(u.searchParams.get('file') || '');
        if (!name) return send(res, 404, 'missing file');
        for (const root of poseRoots()) {
          const f = path.join(root, name);
          if (fs.existsSync(f)) { binPath = f; break; }
        }
        if (!binPath) return send(res, 404, 'palette bin not found');
        maxLen = fs.statSync(binPath).size;
        try {
          const idxPath = binPath.replace(/\.pal\.bin$/, '.pal.json');
          const idx = JSON.parse(fs.readFileSync(idxPath, 'utf8'));
          if (Array.isArray(idx.lens) && idx.lens.length) maxLen = Math.max(...idx.lens);
        } catch { /* 索引が読めなければ file size でクランプ (安全側) */ }
      }
      const size = fs.statSync(binPath).size;

      let from = parseInt(u.searchParams.get('from') || '0', 10);
      if (!Number.isFinite(from) || from < 0) from = 0;
      if (from > size) from = size;
      let len = parseInt(u.searchParams.get('len') || '0', 10);
      if (!Number.isFinite(len) || len <= 0) len = maxLen;
      if (len > maxLen) len = maxLen;
      if (from + len > size) len = size - from;

      let buf;
      let fd;
      try {
        fd = fs.openSync(binPath, 'r');
        buf = Buffer.alloc(len);
        fs.readSync(fd, buf, 0, len, from);
      } catch (e) {
        return send(res, 500, 'read failed: ' + e.message);
      } finally {
        if (fd !== undefined) fs.closeSync(fd);
      }
      return send(res, 200, buf, 'application/octet-stream', 'max-age=3600');
    }
    if (u.pathname === '/api/sound') {
      const f = resolveSound(u.searchParams.get('id') || '');
      if (!f) return send(res, 404, 'unresolved sound');
      return send(res, 200, fs.readFileSync(f), MIME['.ogg'], 'max-age=3600');
    }
    // /tlmsim dumpmodels が書き出した「MC 自身に描かせたモデル」を配る。
    // 開発クライアント / 実機クライアントのどちらで書き出しても拾えるよう複数箇所を探す。
    // `.minecraft-simlab` は YSM mod が入っている唯一の実機インスタンス。
    if (u.pathname.startsWith('/api/model') || u.pathname === '/api/blocks' || u.pathname === '/api/blockatlas' || u.pathname === '/api/poses') {
      const roots = [
        path.join(ROOT, 'simlab', 'models'),
        path.join(ROOT, 'run', 'client_a', 'simlab', 'models'),
        path.join(ROOT, 'run', 'client_b', 'simlab', 'models'),
        path.join(DOT_MC, 'simlab', 'models'),
        path.join(DOT_MC_SIMLAB, 'simlab', 'models'),
      ];
      let rel;
      if (u.pathname === '/api/models') rel = 'index.json';
      else if (u.pathname === '/api/blocks') rel = 'blocks.json';
      else if (u.pathname === '/api/blockatlas') rel = 'blocks_atlas.png';
      else if (u.pathname === '/api/poses') {
        const id = u.searchParams.get('type') || '';
        const i = id.indexOf(':');
        rel = i < 0 ? `minecraft/${id}.poses.json` : `${id.slice(0, i)}/${id.slice(i + 1)}.poses.json`;
      }
      else {
        const id = u.searchParams.get('type') || '';
        const i = id.indexOf(':');
        rel = i < 0 ? `minecraft/${id}.json` : `${id.slice(0, i)}/${id.slice(i + 1)}.json`;
      }
      for (const r of roots) {
        const f = path.join(r, ...rel.split('/'));
        if (fs.existsSync(f)) {
          return send(res, 200, fs.readFileSync(f),
            rel.endsWith('.png') ? MIME['.png'] : 'application/json', 'max-age=60');
        }
      }
      return send(res, 404, 'not dumped yet — run /tlmsim dumpmodels in the client');
    }

    if (u.pathname === '/api/tex') {
      const buf = resolveTexture(u.searchParams.get('id') || '');
      if (!buf) return send(res, 404, 'unresolved texture');
      return send(res, 200, buf, MIME['.png'], 'max-age=3600');
    }
    if (u.pathname === '/api/ysm') {
      // what = model | anim  /  name = ファイルキー
      if (!ysmPackDir) return send(res, 404, 'no ysm pack');
      const what = u.searchParams.get('what') || 'model';
      const ysm = JSON.parse(fs.readFileSync(path.join(ysmPackDir, 'ysm.json'), 'utf8'));
      let rel = null;
      if (what === 'manifest') {
        // YSM_MODEL_ID は ysm.json 内ではなく custom/ 直下の pack 名から決まる。
        // Viewer が live palette を UUID だけで購読すると、同じ個体のモデル切替時に
        // 一瞬でも別モデルの palette を受け得るため、配信用メタデータとして明示する。
        const manifest = { ...ysm, _simlab: { modelId: path.basename(ysmPackDir) } };
        return send(res, 200, JSON.stringify(manifest), 'application/json', 'max-age=60');
      }
      if (what === 'model') rel = ysm.files?.player?.model?.[u.searchParams.get('name') || 'main'];
      if (what === 'anim') rel = ysm.files?.player?.animation?.[u.searchParams.get('name') || 'main'];
      // animation controller の定義 (状態機械)。マニフェストは配列で持つので先頭を採る。
      // これが無いと Viewer は「mod が名指しした 1 本」しか再生できず、実機が状態に応じて
      // 重ねている層 (jump / hold_mainhand / idle など) を再現できない。
      if (what === 'controllers') {
        const list = ysm.files?.player?.animation_controllers;
        rel = Array.isArray(list) ? list[0] : list;
      }
      if (!rel) return send(res, 404, 'unknown ysm file');
      const f = path.join(ysmPackDir, ...rel.split('/'));
      if (!fs.existsSync(f)) return send(res, 404, 'missing ' + rel);
      return send(res, 200, fs.readFileSync(f), 'application/json', 'max-age=3600');
    }

    let rel = u.pathname === '/' ? 'index.html' : u.pathname.slice(1);
    const file = path.resolve(VIEWER, rel);
    if (!file.startsWith(VIEWER) || !fs.existsSync(file)) return send(res, 404, 'not found');
    send(res, 200, fs.readFileSync(file), MIME[path.extname(file)] || 'application/octet-stream');
  } catch (e) {
    send(res, 500, 'error: ' + e.message);
  }
}).listen(PORT, () => {
  console.log(`SimLab viewer  →  http://localhost:${PORT}`);
  console.log(`  traces : ${TRACES}  (${listTraces(TRACES).length} 本)`);
  console.log(`  mod    : ${MOD_ASSETS}`);
  console.log(`  ysm    : ${ysmPackDir || '見つからない → 霊夢のモデルは出ない'}`);
  client();
});
