// =============================================================================
// stats.mjs — トレースの解析。**純関数だけ。I/O を書かないこと。**
// =============================================================================
//
// なぜ分けたか (AGENT-01):
//   人間向けの表と機械向けの JSON が**別々に集計していると、食い違ったときに
//   どちらが正しいか誰にも分からなくなる**。だから集計はここ 1 箇所に置き、
//   `analyze.mjs` の表も `--json` も Viewer も、**同じ関数の戻り値を読むだけ**にする。
//   表示のために再集計したら、この設計の意味が消える。
//
// 実際、2026-08-20 の時点で `simlab/viewer/index.html` は距離と phase を
// 独自の正規表現で計算していた —— AGENT-01 が禁じている食い違いが既に存在していた。
//
// このモジュールはブラウザからも Node からも読める素の ES モジュールにしておく
// (`ysm.js` が「ブラウザからも Node からも使える純粋計算モジュール」として機能している先例に倣う)。

// -----------------------------------------------------------------------------
// このモジュールが読むフィールドの自己申告 (AGENT-04)
// -----------------------------------------------------------------------------
//
// **手で書いて維持する。** コードから自動抽出しない —— 抽出は壊れやすく、
// 壊れたときに黙って通る（検出器が検出しなくなるのが最悪の壊れ方）。
//
// simlab/schema-check.mjs がこれと simlab/schema.json を突き合わせ、
// ここに在って schema に無いフィールドがあれば落ちる。
// つまり「Java が形を変えたのに解析側が古い形を読み続ける」を止める。

export const CONSUMED = {
  meta: ['scenario', 'seed', 'arena', 'duration', 'gameTime'],
  spawn: ['id', 'role', 'type', 'name', 'maxHp'],
  gone: ['id', 'reason'],
  pos: ['id', 'x', 'y', 'z', 'hp'],
  phys: ['id', 'air', 'onG', 'vel', 'y'],
  anim: ['id', 'anim'],
  ai: ['id', 'section', 'sec', 'dist', 'hp', 'maxHp', 'mode', 'target'],
  proj: ['ev', 'id', 'type', 'phase', 'owner'],
  dmg: ['victim', 'attacker', 'direct', 'amount', 'src', 'hpAfter', 'attrib', 'projType', 'phase'],
  vis: ['id'],
  sound: ['id'],
  end: ['reason', 'ticks'],
};

// -----------------------------------------------------------------------------
// トレースの読み取り
// -----------------------------------------------------------------------------

/** JSONL 1 本を { meta, events } へ。壊れた行は黙って捨てず broken に数える。 */
export function parseTrace(text) {
  const events = [];
  let broken = 0;
  let meta = null;
  for (const line of text.split('\n')) {
    if (!line.trim()) continue;
    try {
      const e = JSON.parse(line);
      if (e.ch === 'meta') meta = e;
      events.push(e);
    } catch {
      broken++;
    }
  }
  return { meta, events, broken };
}

// -----------------------------------------------------------------------------
// AI の debug section
// -----------------------------------------------------------------------------
//
// 実機が書く文字列の実物 (1 行):
//   phase=APPROACH ptimer=0  zone=BACKDASH(<=2m) dist=1.0m cd: atk=17 dash=0 slide=116
//   amuletShared=0 pendRanged=none pendMelee=false pendAmulet=NONE combo1=NONE
//   dash: back=false tgtDist=0.0 traveled=4.6
//
// 規則:
//   - `cd:` のように末尾が `:` のトークンは、**それ以降のキーに付く接頭辞**になる。
//     行の途中で何度でも切り替わり、**行が変わると空に戻る**
//   - `k=v` のトークンは `接頭辞 + 先頭大文字化した k` をキーにする
//     (接頭辞が空なら k のまま。`atk=17` は `cd:` の下で `cdAtk`)
//   - 値は boolean → 整数 → 小数 → 文字列 の順に試す。**推測で型を作らない**
//     (`dist=1.0m` は数値にならないので文字列のまま)
//   - 空文字/null は空のオブジェクト。**例外を投げない**
//
// **この規則は Java 側の `SimSection.parse` と一字一句同じでなければならない。**
// 片方だけ直すと、新トレース (`ai.sec`) と旧トレース (`ai.section` を後からパース) で
// 結果が食い違う。Phase 10-02 で golden ファイルによる相互検証を入れる。

const LABEL = /^[a-z][A-Za-z0-9]*:$/;
const KV = /^([A-Za-z][A-Za-z0-9_]*)=(.*)$/;

/** 値を boolean / 整数 / 小数 / 文字列 の順に解釈する。 */
function typed(raw) {
  if (raw === 'true') return true;
  if (raw === 'false') return false;
  if (/^-?\d+$/.test(raw)) {
    const n = Number(raw);
    if (Number.isSafeInteger(n)) return n;
  }
  if (/^-?\d*\.\d+$/.test(raw)) {
    const n = Number(raw);
    if (!Number.isNaN(n)) return n;
  }
  return raw;
}

const cap = (s) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : s);

/**
 * debug section の文字列を構造化する。
 * 挿入順を保つ（`Object` のキー順＝挿入順）。
 */
export function parseSection(rawSection) {
  const out = {};
  if (rawSection == null) return out;
  const text = String(rawSection);
  if (!text.trim()) return out;

  for (const line of text.split('\n')) {
    let prefix = '';                       // 行が変わると接頭辞は空に戻る
    for (const tok of line.split(/\s+/)) {
      if (!tok) continue;
      if (LABEL.test(tok)) { prefix = tok.slice(0, -1); continue; }
      const m = KV.exec(tok);
      if (!m) continue;                    // 拾えないトークンは黙って捨てる
      const key = prefix ? prefix + cap(m[1]) : m[1];
      out[key] = typed(m[2]);
    }
  }
  return out;
}

/**
 * `ai` イベントから構造化 section を取り出す。
 *
 * <p>新トレースは Java 側で構造化済みの `sec` を持つ。**そちらを優先する** ——
 * パースは実機の供給点で 1 回だけ行うのが設計で、ここでのパースは
 * **Phase 10 より前に録られたトレースのための互換経路**でしかない。
 */
export function sectionOf(aiEvent) {
  if (!aiEvent) return {};
  if (aiEvent.sec && typeof aiEvent.sec === 'object') return aiEvent.sec;
  return parseSection(aiEvent.section);
}

// -----------------------------------------------------------------------------
// 技ごとの集計 (MEAS-01)
// -----------------------------------------------------------------------------

const median = (a) => {
  if (!a.length) return null;
  const s = a.slice().sort((x, y) => x - y);
  const m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
};

/**
 * `ai` イベントを phase 単位に畳む。
 *
 * <p>`count` は「phase が直前と変わった回数」で、**最初の観測を 1 回目に数える**。
 * `intervalMedianTicks` は同じ phase の**再発開始 tick の差**の中央値
 * (再発が 1 回も無ければ null)。
 *
 * <p><b>注意</b>: `ai` は「判断が変わった tick だけ」書かれる (620件/900tick の実測)。
 * つまりここで出るのは**回数と間隔**であって、滞在時間ではない。
 * 滞在時間は Phase 10-02 で「次の観測まで保持する」形で復元する。
 */
/**
 * phase ごとの滞在 tick を返す。
 *
 * <p><b>なぜ復元が要るか</b>: `ai` は「判断が変わった tick だけ」書かれる
 * （実測 620件/900tick）。つまり「その phase に何 tick 居たか」はトレースに**書かれていない**。
 * 各観測を<b>次の観測まで保持</b>すれば復元できる。
 *
 * <p>最後の区間は `end.ticks`（無ければ最大 tick）まで伸ばす。
 * 合計が観測範囲と一致することは呼び出し側で自己検査できる（取りこぼしが無いことの証拠）。
 *
 * @returns phase -> 滞在 tick 数
 */
export function dwell(events) {
  const obs = [];
  let endTick = 0;
  for (const e of events) {
    if (!e) continue;
    if (typeof e.t === 'number' && e.t > endTick) endTick = e.t;
    if (e.ch === 'end' && typeof e.ticks === 'number') endTick = Math.max(endTick, e.ticks);
    if (e.ch !== 'ai') continue;
    const phase = sectionOf(e).phase;
    if (phase === undefined || phase === null || phase === '') continue;
    obs.push({ t: e.t, phase });
  }
  const out = {};
  for (let i = 0; i < obs.length; i++) {
    const until = i + 1 < obs.length ? obs[i + 1].t : endTick;
    const d = Math.max(0, until - obs[i].t);
    out[obs[i].phase] = (out[obs[i].phase] || 0) + d;
  }
  return out;
}

export function techniques(events) {
  const starts = new Map();     // phase -> [開始 tick, ...]
  const first = new Map();
  const last = new Map();
  let prev = null;

  for (const e of events) {
    if (!e || e.ch !== 'ai') continue;
    const phase = sectionOf(e).phase;
    if (phase === undefined || phase === null || phase === '') continue;
    if (!first.has(phase)) first.set(phase, e.t);
    last.set(phase, e.t);
    if (phase !== prev) {
      if (!starts.has(phase)) starts.set(phase, []);
      starts.get(phase).push(e.t);
      prev = phase;
    }
  }

  // 発射数 —— proj spawn が持つ phase（**発射時**の技）で数える
  const shots = new Map();
  for (const e of events) {
    if (!e || e.ch !== 'proj' || e.ev !== 'spawn') continue;
    const p = e.phase;
    if (p === undefined || p === null || p === '' || p === '-') continue;
    shots.set(p, (shots.get(p) || 0) + 1);
  }

  // 命中と与ダメ —— 帰属できたものだけ。**できなかった分は別に数えて必ず併記する**
  const hits = new Map();
  const dmgSum = new Map();
  let unattributedHits = 0;
  let unattributedDmg = 0;
  for (const a of attribute(events)) {
    if (a.how === 'none' || a.phase === undefined || a.phase === null || a.phase === '' || a.phase === '-') {
      unattributedHits++;
      unattributedDmg += a.amount || 0;
      continue;
    }
    hits.set(a.phase, (hits.get(a.phase) || 0) + 1);
    dmgSum.set(a.phase, (dmgSum.get(a.phase) || 0) + (a.amount || 0));
  }

  const dw = dwell(events);
  const dwTotal = Object.values(dw).reduce((a, b) => a + b, 0);

  // phase は ai / proj / dmg のどこに現れてもよい（弾だけ出て ai に残らない技があり得る）
  const allPhases = new Set([...starts.keys(), ...shots.keys(), ...hits.keys()]);

  const rows = [];
  for (const phase of allPhases) {
    const ts = starts.get(phase) || [];
    const gaps = [];
    for (let i = 1; i < ts.length; i++) gaps.push(ts[i] - ts[i - 1]);
    const sh = shots.get(phase) || 0;
    const hi = hits.get(phase) || 0;
    rows.push({
      phase,
      count: ts.length,
      intervalMedianTicks: median(gaps),
      firstTick: first.get(phase),
      lastTick: last.get(phase),
      shots: sh,
      hits: hi,
      dmgSum: round2(dmgSum.get(phase) || 0),
      // 0 除算で 0 を出さない。撃っていない技の命中率は「無い」のであって「0%」ではない
      hitRatePct: sh > 0 ? round2((100 * hi) / sh) : null,
      dwellTicks: dw[phase] || 0,
      dwellPct: dwTotal > 0 ? round2((100 * (dw[phase] || 0)) / dwTotal) : null,
    });
  }
  rows.sort((a, b) => b.count - a.count || b.shots - a.shots
    || String(a.phase).localeCompare(String(b.phase)));

  // 帰属できなかった分は、行に配れないので**全行が持つ**（表の脚注に出すため）
  for (const r of rows) {
    r.unattributedHits = unattributedHits;
    r.unattributedDmg = round2(unattributedDmg);
  }
  return rows;
}

const round2 = (v) => Math.round(v * 100) / 100;

// -----------------------------------------------------------------------------
// tick 軸の時系列 (MEAS-02)
// -----------------------------------------------------------------------------

/**
 * tick を添字にした系列。**Viewer と CLI が同じ配列を読む** (AGENT-01)。
 *
 * <p><b>Viewer から移植したのではなく書き直した。</b> Viewer 側の実装は Viewer 内部の
 * tick 別インデックスに依存しており、そのままでは `stats.mjs` の「I/O にも
 * ブラウザにも依存しない純関数」という条件を満たせない。ここでは `events` から直接組む。
 *
 * <p>戻り値は**素の配列**にしてある（型付き配列は JSON で運べない）。
 * 全レーンの長さは `end.ticks + 1`、`end` が無ければ最大 tick + 1 で揃う。
 *
 * <p>`phase` は必ず {@link sectionOf} 経由で取る —— **section を読む処理を
 * このモジュールの外に作らない**。2026-08-20 の時点で Viewer は自前の正規表現で
 * phase を抜いており、AGENT-01 が禁じている食い違いが既に存在していた。
 *
 * <p><b>13-03: 追記できる形に分解した（実装は1本のまま）。</b> ライブは毎秒「新着行だけ」
 * しか渡さないので、毎秒 O(履歴長) で全部を作り直す {@link series} をそのまま毎秒呼ぶわけには
 * いかない。そこで内部状態({@link seriesState})を持ち回し、新着 events だけを差分処理する
 * {@link seriesFeed} を実装の本体にした。{@link series} はこの2つ({@link seriesState} +
 * {@link seriesFeed})と {@link seriesLanes} を呼ぶだけの薄い包みに縮めてある——**2つ目の
 * 集計実装を作らない**(AGENT-01)。
 *
 * <p>状態ハンドルは呼び出し側の外に漏らさない。{@link seriesLanes} が返すのは
 * レーン配列(`{dist, y, ...}`)だけで、carry(直前値・reimuId・goneAt 等)は含まない
 * ——`analyze()` が `series: series(events)` をそのまま `--json` で吐くため
 * (`analyze.mjs:116`)、carry が混ざると出力そのものが変わってしまう。
 *
 * @returns {{dist:number[], y:number[], hpR:number[], hpT:number[], vel:number[],
 *   onG:number[], air:number[], embed:number[], proj:number[], dmg:number[],
 *   snd:number[], ai:number[], pose:number[], phase:(string|null)[]}}
 */
export function series(events) {
  const state = seriesState();
  seriesFeed(state, events, { final: true });  // バッチ呼び出し = もう続きは来ない
  return seriesLanes(state);
}

// 各レーンの初期値。**この Object の key 順が出力の key 順になる**(旧 `out` リテラルの
// 宣言順と一字一句揃えてある) —— 呼び出し側(plan本文の verify や本モジュールの
// 自己検査)が `JSON.stringify` で新旧を突き合わせるため、順序がずれるとバイトが変わる。
//
// onG/air/embed だけ NaN を初期値にしている(旧実装は 0)。理由は下の seriesFeed 内、
// 「onG/air/embed の前方フィル」の節を参照 —— NaN は「まだこの tick を解決していない」
// ことを示す内部専用の一時的な印であり、seriesFeed が同じ呼び出しの中で必ず 0/1 へ
// 解決し切る(呼び出しが返る時点で NaN が残ることはない。残っていたら実装のバグ)。
const LANE_DEFAULTS = {
  dist: NaN, y: NaN, hpR: NaN, hpT: NaN, vel: NaN,
  onG: NaN, air: NaN, embed: NaN,
  proj: 0, dmg: 0, snd: 0, ai: 0, pose: 0,
  phase: null,
};

/** レーン配列を長さ n まで伸ばす。**新しく増えた添字だけ**を埋める(追記のたび
 *  レーン全体を作り直すと、その時点で履歴長に比例する費用が戻ってしまうため)。 */
function growLanesTo(lanes, n) {
  for (const k of Object.keys(LANE_DEFAULTS)) {
    const arr = lanes[k];
    const def = LANE_DEFAULTS[k];
    for (let i = arr.length; i < n; i++) arr.push(def);
  }
}

/** 汎用の配列拡張(レーン以外の内部専用バッファ用)。 */
function growArrTo(arr, n, def) {
  for (let i = arr.length; i < n; i++) arr.push(def);
}

/** ch(dmg/proj)の t における「この行はもう加算したか」を**内容一致**で判定し、
 *  未了なら apply() を1回だけ呼ぶ(T-13-09)。tickの watermark(直近に見たtickより
 *  小さいtickを無視する、という素朴な案)ではなく内容一致にしたのは、**同一tick内の
 *  複数の正当な行がバッチ境界で分割されたときに、watermark方式だと後半の正当な行まで
 *  誤って捨ててしまう**ため——combat-60t.jsonl の10分割feedで実際に再現した
 *  (`proj[47]`が48件のはずが5件になった)。二重取り込み(再接続で先頭から送り直された分)
 *  は行の中身までバイト一致するはずなので、内容一致なら正しく1回だけ数えられる。 */
function applyOnce(seenByTick, t, e, apply) {
  let seen = seenByTick.get(t);
  if (!seen) { seen = new Set(); seenByTick.set(t, seen); }
  const sig = JSON.stringify(e);
  if (seen.has(sig)) return;
  seen.add(sig);
  apply();
}

/**
 * {@link seriesFeed} が持ち回る空の状態ハンドル。
 *
 * <p>2種類の carry を持つ: (1) 識別 carry(reimuId・targetIds・goneAt・end.ticks・
 * 見た最大tick) —— 一度確定したら以後の呼び出しでも変わらない。(2) 前方フィル carry
 * (各レーンの直前値) —— 2周目ループを `filledTo+1` から再開するために要る。
 * どちらも {@link seriesLanes} の戻り値には含めない(このファイル冒頭の docstring参照)。
 */
export function seriesState() {
  return {
    reimuId: null,
    targetIds: [],
    endTicks: null,
    maxT: 0,            // n の計算に使う最大tick(endイベント自身のtickも含む。旧実装のmaxTと同じ)
    everFed: false,     // 一度でも空でない events を seriesFeed へ渡したか。false のうちは
                         // 下の hold-back を適用しない——maxT は「一度も観測していない」ときも
                         // 初期値 0 のままなので(旧実装のmaxTと合わせるため。空トレースで n=1に
                         // なる仕様)、これを「進行中のtick」と誤認して不必要に保留すると、
                         // pass2が一度も走らずonG/air/embedの内部sentinel(NaN)がそのまま
                         // seriesLanesの戻り値へ漏れる(実測: 空配列でのseriesFeed(state,[])
                         // 直後、JSON.stringifyがonG[0]をnullで返した——13-03 Task 2、
                         // ライブを開いた瞬間の「まだ1行も来ていない」状態で実際に踏んだ)。
    lastDataTick: -1,   // 「観測できた最大tick、ただし end イベント自身は含めない」——
                         // posR/posT(→dist)の前方フィル境界(gone が無いとき)に使う。
                         // end.ticks はレーン長 n の計算にのみ使い、生存区間の境界には使わない
                         // (combat-60t.jsonl のように end.ticks だけが実データより先へ伸びている
                         // トレースで、無条件に埋めると出力が変わってしまうため——このファイルの
                         // 呼び出し元 PLAN の interface_context に実測根拠あり)。dist はここが
                         // やや広く取れていても実害が無い(下の <dist_bound_is_safe> 参照)。
    lastPhysObsTick: -1, // 「phys 行(reimu)を実際に見た最大tick」。onG/air/embed の前方フィル
                         // 境界(gone が無いとき)は**これ**を使う——lastDataTick(他チャンネル
                         // 込み)を使うと、実測の tank/20260820/20260821-031644 のように
                         // 「録画が途中で(サーバ強制終了等で)切れ、最後の phys 行だけが
                         // 壊れた JSON として捨てられたが、同じ tick の pos 行は書き切れていた」
                         // ケースで、phys 側に一切観測が無い tick まで前方フィルしてしまい
                         // 旧実装の出力(0のまま)と食い違う(27本の実トレース照合で実際に検出)。
    goneAt: new Map(),  // id -> gone を見た tick(store.js の isAlive と同じ「明示的な gone だけを
                         // 境界にする」設計をここでも踏襲する。理由は同じ: 「最後に見た tick」を
                         // 死亡の代理指標にすると、記録がただ途切れているだけの生存 entity や、
                         // 将来デルタ化で無変化行が省かれるようになった後の静止した生存 entity を
                         // 誤って消してしまう)。

    lastAnimKey: null,  // pose[] の変化点検出の carry(直前の anim キー)。
    animApplied: new Map(),  // tick -> 直近に適用した anim キー。dmg/proj の applyOnce と
                              // 同じ「tickごとに内容を覚えて一致したら1回だけ弾く」方式で
                              // 二重取り込みを検出する(下の seriesFeed 内、anim ケース参照)。

    // 加算レーン(dmg/proj)の二重加算防止(T-13-09)。tick -> 「もう加算した行の内容」の
    // 集合。内容一致で判定する理由は applyOnce() のコメントを参照。
    dmgApplied: new Map(),
    projApplied: new Map(),

    // dist 再計算用の生データ。**永続バッファ**(バッチをまたいで残る)にしてあるのが要——
    // pos(reimu/target)と ai(dist フォールバック)が同じ tick でも別バッチに分かれて届く
    // ことがあり、後から届いた側が「もう2周目が確定させた値」を知らずに上書きしてしまう
    // 回帰を combat-60t.jsonl の10分割feedで実際に踏んだ。2周目が消費したら null/NaN に
    // 戻す(その tick を二度と見ないので、行オブジェクトを持ち続ける理由が無い)。
    posRRaw: [], posTRaw: [], aiDistRaw: [],

    // 2周目(前方フィル)の carry。**onG/air/embed は "null" を「まだ一度も観測していない」
    // の印に使う**(0/1 という正当な観測値と区別するため)。
    lastDist: NaN, lastY: NaN, lastHpR: NaN, lastHpT: NaN, lastVel: NaN, lastPhase: null,
    lastOnG: null, lastAir: null, lastEmbed: null,
    lastPosRRow: null, lastPosTRow: null,  // dist再計算用。posR/posT自体は返り値に出さない。

    lanes: {
      dist: [], y: [], hpR: [], hpT: [], vel: [],
      onG: [], air: [], embed: [],
      proj: [], dmg: [], snd: [], ai: [], pose: [],
      phase: [],
    },
    filledTo: -1,  // 2周目が解決済みの添字の右端。-1 = まだ何も無い。
  };
}

/**
 * 新着 events を state へ追記する。**既に食わせた行を再度渡してもよい**
 * ——同じ行は同じ結果を上書きするだけ(状態レーンは変化点なので冪等)。加算レーン
 * (dmg/proj)は内容一致の行を二重加算しない(T-13-09、`applyOnce` 参照)。
 *
 * <p>費用は **今回渡した events の量にだけ比例する**。2周目(前方フィル)の走査範囲を
 * `state.filledTo+1 .. (末尾付近)` に絞ってあるため、既に解決済みの区間を毎回舐め直さない
 * ——これが「毎秒の処理が履歴長に依存しない」の実体。
 *
 * <p><b>「直近に観測した tick」は既定では確定させない(hold-back)。</b> 1つの tick の
 * 複数チャンネル(reimu の pos・target の pos・ai の dist フォールバック等)が
 * **別々の feed 呼び出しに分かれて届くことがある**(ライブの1秒バッチ境界がちょうど
 * 1 tick の記録の途中を割る、または combat-60t.jsonl の10分割feedのように分割自体が
 * チャンネルをまたぐ場合)。まだ全チャンネルが揃っていないかもしれない tick を
 * 2周目が確定させてしまうと、次の呼び出しで残りのチャンネルが届いても
 * (2周目はその tick を二度と見ないので)取りこぼす——combat-60t.jsonl の10分割feedで
 * `dist[58]` が実際にこの形で壊れた(reimu の pos は先に届いたが target の pos は
 * 次のバッチだったため、直前 tick の position を保持したまま hypot を確定させてしまった)。
 * 「今見えている最大 tick はまだ他チャンネルの続きが来るかもしれない」とみなし、
 * その1つ前までしか確定させない。`opts.final`(既定 false)を true にすると、
 * これ以上データが来ないと判っている場合(バッチ `series()` の内部・トレース終端)に
 * 保留ぶんも含めて確定させる。
 */
export function seriesFeed(state, events, opts) {
  const S = state;
  const final = !!(opts && opts.final);

  // ---- 識別 carry の更新(旧実装の1周目=identity scanと同じ範囲・同じ順序) ----
  let batchMaxT = S.maxT;
  let batchDataMaxT = S.lastDataTick;
  if (events && events.length > 0) S.everFed = true;
  for (const e of events) {
    if (!e) continue;
    if (typeof e.t === 'number') {
      if (e.t > batchMaxT) batchMaxT = e.t;
      if (e.ch !== 'end' && e.t > batchDataMaxT) batchDataMaxT = e.t;
    }
    if (e.ch === 'end' && typeof e.ticks === 'number') S.endTicks = e.ticks;
    if (e.ch === 'spawn') {
      if (e.role === 'reimu' && S.reimuId === null) S.reimuId = e.id;
      if (e.role === 'target') S.targetIds.push(e.id);
    }
    if (e.ch === 'gone') S.goneAt.set(e.id, e.t);
  }
  S.maxT = batchMaxT;
  S.lastDataTick = batchDataMaxT;

  const n = (S.endTicks != null ? S.endTicks : S.maxT) + 1;
  growLanesTo(S.lanes, n);
  growArrTo(S.posRRaw, n, null);
  growArrTo(S.posTRaw, n, null);
  growArrTo(S.aiDistRaw, n, NaN);
  const L = S.lanes;

  // ---- 1周目: 今回の events ぶんの生観測を書く ----
  for (const e of events) {
    if (!e || typeof e.t !== 'number' || e.t < 0 || e.t >= n) continue;
    const t = e.t;
    switch (e.ch) {
      case 'pos':
        if (e.id === S.reimuId) {
          S.posRRaw[t] = e;
          if (typeof e.y === 'number') L.y[t] = e.y;
          if (typeof e.hp === 'number') L.hpR[t] = e.hp;
        } else if (S.targetIds.length && e.id === S.targetIds[0]) {
          S.posTRaw[t] = e;
          if (typeof e.hp === 'number') L.hpT[t] = e.hp;
        }
        break;
      case 'phys':
        if (e.id === S.reimuId || S.reimuId === null) {
          L.onG[t] = e.onG ? 1 : 0;
          L.air[t] = e.air ? 1 : 0;
          L.embed[t] = e.embed ? 1 : 0;
          if (typeof e.vel === 'number') L.vel[t] = e.vel;
          if (t > S.lastPhysObsTick) S.lastPhysObsTick = t;
        }
        break;
      case 'ai': {
        L.ai[t] = 1;
        const ph = sectionOf(e).phase;
        if (ph !== undefined && ph !== null && ph !== '') L.phase[t] = ph;
        // dist の ai フォールバックは、L.dist[t] へ直接書かず**永続バッファ**へ置く。
        // 2周目(このすぐ下)だけが L.dist[t] を書く唯一の場所——ここに直接書くと、
        // 既に2周目が確定させた(より精度の高い hypot 由来の)値を、別バッチで後から
        // 届いた ai 行が黙って上書きしてしまう(このコメントの上、posRRaw/aiDistRaw の
        // フィールド説明を参照。combat-60t.jsonl の10分割feedで実際に再現・特定した)。
        if (typeof e.dist === 'number' && e.dist >= 0) S.aiDistRaw[t] = e.dist;
        break;
      }
      case 'anim': {
        // 二重取り込み(SSE 再接続でトレースの先頭から送り直された分)だけを弾く。
        // **tick位置(filledTo等)ではなく「この tick で既に見た内容か」で判定する**——
        // 位置ベース(filledToより前は無視)の版は combat-60t.jsonl の10分割feedで
        // 誤検出した: tick 58 の anim 行が(他チャンネルの都合で)tick 58 自体が
        // 既に2周目へ届いた"あと"のバッチで届くと、**本物の新規データ**なのに
        // 「もう処理した過去」と誤判定して捨ててしまい、pose[58] が立たなくなっていた
        // (pend が "-" から "slashblade:run" へ変わる本物の変化点)。dmg/proj の
        // applyOnce と同じ「tick ごとに内容を覚えて一致したら1回だけ弾く」方式にすれば、
        // 同じtickに同じ中身の行が来た時だけ(=正真正銘の再送)スキップでき、
        // 届く順序(どのバッチに乗って来るか)には依存しない。
        const k = (e.anim || '') + '|' + (e.pend || '') + '|' + (e.molang || '');
        if (S.animApplied.get(t) !== k) {
          S.animApplied.set(t, k);
          if (S.lastAnimKey !== null && k !== S.lastAnimKey) L.pose[t] = 1;
          S.lastAnimKey = k;
        }
        break;
      }
      case 'proj':
        if (e.ev === 'spawn') applyOnce(S.projApplied, t, e, () => { L.proj[t] += 1; });
        break;
      case 'dmg':
        applyOnce(S.dmgApplied, t, e, () => { L.dmg[t] += (typeof e.amount === 'number' ? e.amount : 0); });
        break;
      case 'sound':
        L.snd[t] = 1;
        break;
      default:
        break;
    }
  }

  // ---- 2周目: filledTo+1 .. n-1 だけを前方フィルする(履歴を舐め直さない) ----
  // 「観測が無い」と「0 だった」を混同しないため、無いtickは直前値を保持する
  // (この原則は旧実装のコメントのまま——変えていない)。
  //
  // onG/air/embed/posR/posT は 13-03 で新たに前方フィルの対象にした。ただし
  // **エンティティの生存区間の内側にだけ**掛ける——区間の終端は、そのエンティティの
  // gone tick、無ければ「レーンの末尾」(=このトレースで実際に観測できた最大tick。
  // end.ticks 由来の見かけ上の長さではない)。密トレースはこの区間の内側に欠測が無いので、
  // この前方フィルは常に no-op になる(=既存トレースの series() 出力が変わらないことの根拠)。
  //
  // <dist_bound_is_safe> posR/posT(→dist)は lastDataTick(他チャンネル込みの最大tick)を
  // 使う。dist 自体は元々**無条件に**前方フィルされる(この2周目ループの最後、
  // L.dist[t]=S.lastDist の代入がそれ)ので、posR/posT をどこまで forward-fill するかで
  // 「hypot を再計算するか、既に確定した lastDist を保つか」が変わるだけであり、
  // **held の座標どうしの hypot は held の値そのものと数値上一致する**(座標が動かない
  // 間は距離も動かない)——27本の実トレース+2 fixture の照合でも dist の不一致は
  // 0 件だった。onG/air/embed はこの安全網を持たない(直接 0/1 を保持するだけの
  // レーンで、「保持するか、0 に戻すか」がそのまま出力を変える)ので、下の
  // boundPhysReimu のように**専用の境界**が要る。
  const boundReimu = S.goneAt.has(S.reimuId) ? S.goneAt.get(S.reimuId) : S.lastDataTick;
  const targetId0 = S.targetIds.length ? S.targetIds[0] : null;
  const boundTarget = (targetId0 !== null && S.goneAt.has(targetId0)) ? S.goneAt.get(targetId0) : S.lastDataTick;
  // onG/air/embed 専用の境界。**end イベントが有効かどうかで2通りに分かれる**(13-04で発覚、
  // 13-03がこの節の goneAt フィールド説明に残した「13-04設計時の検討事項」に対する回答)。
  // (1) end が無い(録画がサーバ強制終了等で途中に切れた) —— lastDataTick(他チャンネル込み)を
  //     使うと、実測の tank/20260820/20260821-031644(end イベント自体が無い)のように
  //     「最後のphys行だけが壊れたJSONとして捨てられたが、同じtickのpos行は書き切れていた」
  //     ケースで、phys側に一切観測が無いtickまで前方フィルしてしまい旧実装の出力(0のまま)と
  //     食い違う(27本の実トレース照合で13-03が検出)。この場合は lastPhysObsTick(phys行
  //     そのものの最大tick)に留める。
  // (2) end が有効(録画は正常に完了した) —— この場合、phys行が観測されなくなったのは
  //     「記録が途切れた」のではなく「13-04の行単位デルタ化で、変化の無い行を書かなくなった」
  //     ことを意味しうる(reimuは生きたまま、末尾まで状態が変わらなかった)。lastPhysObsTick の
  //     ままだと末尾の静止区間が前方フィルされず onG が 0 に化る(実測:
  //     smoke/20260814/20260820-175211、deltaEncode後の analyze() が dense 版と食い違った)。
  //     この場合は boundReimu/boundTarget と同じ lastDataTick まで前方フィルしてよい
  //     ——end が有効という事実そのものが「記録は正常に完了した(途中で切れていない)」の証拠になる。
  const boundPhysReimu = S.goneAt.has(S.reimuId) ? S.goneAt.get(S.reimuId)
    : (S.endTicks != null ? S.lastDataTick : S.lastPhysObsTick);

  // hold-back: 既定では S.maxT(このバッチも含め、これまでに観測した最大tick)自身は
  // 確定させない——このコメントの上のdocstringにある dist[58] の実例参照。
  // final:true のときだけ n-1 まで(=保留を持たない)確定させる。
  // まだ一度も events を受け取っていない(S.everFed===false)ときは保留しない——
  // maxT の初期値 0 を「進行中のtick」と誤認すると、pass2が一度も走らずonG/air/embed
  // の内部sentinelが漏れる(state.everFed のフィールド説明を参照)。
  const resolveUpTo = (final || !S.everFed) ? (n - 1) : Math.min(n - 1, S.maxT - 1);

  for (let t = S.filledTo + 1; t <= resolveUpTo; t++) {
    // posRRaw/posTRaw は永続バッファ(このバッチだけの索引ではない) —— pos(reimu/target)
    // と ai(dist フォールバック)が別バッチに分かれて届いても、先に届いた方の生データが
    // 消えずに残っている。消費(=carry へ取り込む)したらこの tick はもう見ないので null に戻す。
    if (S.posRRaw[t] !== null) { S.lastPosRRow = S.posRRaw[t]; S.posRRaw[t] = null; }
    else if (S.lastPosRRow !== null && t > boundReimu) S.lastPosRRow = null;
    if (S.posTRaw[t] !== null) { S.lastPosTRow = S.posTRaw[t]; S.posTRaw[t] = null; }
    else if (S.lastPosTRow !== null && t > boundTarget) S.lastPosTRow = null;

    if (S.lastPosRRow && S.lastPosTRow) {
      S.lastDist = Math.hypot(S.lastPosRRow.x - S.lastPosTRow.x, S.lastPosRRow.y - S.lastPosTRow.y, S.lastPosRRow.z - S.lastPosTRow.z);
    } else if (!Number.isNaN(S.aiDistRaw[t])) {
      S.lastDist = S.aiDistRaw[t];
    }
    S.aiDistRaw[t] = NaN;
    L.dist[t] = S.lastDist;
    if (!Number.isNaN(L.y[t])) S.lastY = L.y[t]; else L.y[t] = S.lastY;
    if (!Number.isNaN(L.hpR[t])) S.lastHpR = L.hpR[t]; else L.hpR[t] = S.lastHpR;
    if (!Number.isNaN(L.hpT[t])) S.lastHpT = L.hpT[t]; else L.hpT[t] = S.lastHpT;
    if (!Number.isNaN(L.vel[t])) S.lastVel = L.vel[t]; else L.vel[t] = S.lastVel;
    if (L.phase[t] !== null) S.lastPhase = L.phase[t]; else L.phase[t] = S.lastPhase;

    // onG/air/embed: 生存区間つきの前方フィル。NaN は「このtickにまだ生観測が無い」
    // (=1周目が書かなかった)ことを示す一時的な内部sentinelで、ここで必ず0/1へ解決する。
    if (!Number.isNaN(L.onG[t])) { S.lastOnG = L.onG[t]; }
    else if (S.lastOnG !== null && t <= boundPhysReimu) { L.onG[t] = S.lastOnG; }
    else { L.onG[t] = 0; }

    if (!Number.isNaN(L.air[t])) { S.lastAir = L.air[t]; }
    else if (S.lastAir !== null && t <= boundPhysReimu) { L.air[t] = S.lastAir; }
    else { L.air[t] = 0; }

    if (!Number.isNaN(L.embed[t])) { S.lastEmbed = L.embed[t]; }
    else if (S.lastEmbed !== null && t <= boundPhysReimu) { L.embed[t] = S.lastEmbed; }
    else { L.embed[t] = 0; }
  }
  if (resolveUpTo > S.filledTo) S.filledTo = resolveUpTo;
}

/**
 * state の現在のレーン配列を返す。**内部配列をそのまま返す(複製しない)**——
 * 次の {@link seriesFeed} 呼び出しで配列が伸びると、既にこの戻り値を持っている
 * 呼び出し側からも同じ配列が(伸びた分だけ)見える。carry は一切含まない。
 */
export function seriesLanes(state) {
  return state.lanes;
}

/**
 * 窓で切った後、もう二度と食わせない tick の**重複検出台帳**を捨てる。
 *
 * dmgApplied / projApplied / animApplied は「同じ tick を二度食わせても二重に数えない」
 * ためだけの Map で、値は行の JSON 文字列。**一度も刈られていなかった** ——
 * 戦闘中は毎秒 35 行ぶんの文字列が積まれ、実測で約 36MB/時 に育つ。
 *
 * 安全な理由: 切った後に w より前の tick を食わせ直すことは無い。ライブの取り込みは
 * バイト位置で前進のみ、繋ぎ直しは続きから、記録が変われば seriesState ごと作り直す。
 *
 * **レーン配列(絶対 tick 索引)には触れない。** filledTo と約40箇所の添字前提を
 * 崩すと帯が**黙って**壊れる。読む側を窓に限れば CPU は消えるので、そちらで足りる。
 */
export function seriesTrim(state, w) {
  if (!state || !(w > 0)) return 0;
  let dropped = 0;
  for (const m of [state.dmgApplied, state.projApplied, state.animApplied]) {
    if (!m) continue;
    for (const t of m.keys()) if (t < w) { m.delete(t); dropped++; }
  }
  return dropped;
}

/**
 * {@link series} の各レーンを 1 行で要約する（人向け出力用）。
 * **同じ series から計算する。別集計にしない。**
 */
export function seriesSummary(s) {
  const rows = [];
  for (const [k, arr] of Object.entries(s)) {
    if (!Array.isArray(arr) || !arr.length) continue;
    if (k === 'phase') {
      const uniq = new Set(arr.filter((v) => v !== null));
      rows.push({ lane: k, kinds: uniq.size, last: arr[arr.length - 1] });
      continue;
    }
    const nums = arr.filter((v) => typeof v === 'number' && !Number.isNaN(v));
    if (!nums.length) { rows.push({ lane: k, min: null, max: null, last: null }); continue; }
    rows.push({
      lane: k,
      min: round2(Math.min(...nums)),
      max: round2(Math.max(...nums)),
      last: round2(arr[arr.length - 1]),
    });
  }
  return rows;
}

/**
 * dmg 1 件ごとに「どうやって技へ帰属させたか」を返す。
 *
 * <p>新トレースは Java 側が判定済みの {@code attrib} を持つ。**そちらを優先する**。
 * 旧トレースにはそれが無いので、ここで同じ規則を当てる（互換経路）。
 *
 * <p><b>推測しない。</b> どちらでもないものは {@code how:"none"} として返し、
 * 呼び出し側が**隠さず数える**。帰属率を上げるために当て推量で配ると、
 * 技別命中率が静かに嘘になる。
 *
 * @returns 各 dmg の {tick, amount, victim, how, projType, phase}
 */
export function attribute(events) {
  // 旧トレース用: 弾 id → {type, phase}
  const proj = new Map();
  let reimuId = -1;
  for (const e of events) {
    if (!e) continue;
    if (e.ch === 'spawn' && e.role === 'reimu') reimuId = e.id;
    if (e.ch === 'proj' && e.ev === 'spawn') proj.set(e.id, { type: e.type, phase: e.phase });
  }

  const out = [];
  for (const e of events) {
    if (!e || e.ch !== 'dmg') continue;
    let how;
    let projType;
    let phase;
    if (e.attrib) {
      how = e.attrib;                    // Java が判定済み
      projType = e.projType;
      phase = e.phase;
    } else {
      const p = e.direct >= 0 ? proj.get(e.direct) : undefined;
      if (p) {
        how = 'direct';
        projType = p.type;
        phase = p.phase;
      } else if (reimuId >= 0 && e.attacker === reimuId && e.direct === reimuId) {
        how = 'melee';                   // 旧トレースは phase を持たないので付けられない
      } else {
        how = 'none';
      }
    }
    out.push({ tick: e.t, amount: e.amount, victim: e.victim, how, projType, phase });
  }
  return out;
}
