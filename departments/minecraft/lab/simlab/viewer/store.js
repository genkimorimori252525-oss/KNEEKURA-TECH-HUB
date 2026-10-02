/* =============================================================================
   SimLab — 疎な変化点ストア (13-01/13-02: 水槽を実機の速さで見る)
   -----------------------------------------------------------------------------
   D-03(にーくら決定, 13-CONTEXT.md)「全履歴をブラウザに持つ。構造を疎にすることで
   成立させる」の実装。チャンネルは2種類に分かれる:

   - 状態(state): pos/vis/phys/anim。前方フィルする(欠測=直前値)。gone(明示的な
     イベント)以降はnullを返す(CR-01/CR-02, 13-01のコードレビューで確定した設計 ——
     entities.get(id).lastは死亡の代理指標にしない。理由はisAliveのコメント参照)。
     pos/visは数値をTypedArray(Int32Array tick列+Float32Array値列)に詰め、
     二分探索+前方フィルで返す。posだけ補間(entityInterpAt)し、visは補間しない。
     phys/animは霊夢1体ぶんの単一レーン(id-keyedではない) —— animはmolang文字列を
     含むので数値配列に入らず、変化点tickの配列+値(生オブジェクト)の素の配列で持つ
     (放置中の水槽ではanimの変化は94,260行中22行だけ、と実測されているので、
     オブジェクトで持っても件数が支配しない。phys もこれに揃える)。
   - 事象(event): ai/dmg/sound/proj/log。前方フィルしない —— その行が記録された
     tickにだけ属する。tick昇順の行配列+tick索引を持ち、frameAt(t)はその範囲だけを
     切り出す。取り込み時の重複除去(rowIsRedundant)は状態レーンにだけ適用する
     ——同じダメージが2回起きることは有り得るので、事象を「前と同じだから」で
     捨てたら記録を失う。
   - 索引(index): meta/spawn/gone/end。tickの系列ではない(1回だけ、またはentities
     の更新に使うだけ)。ingestLine内で専用に処理する。

   CHANNEL_LANESはこの分類の唯一の対応表。未知のチャンネルは'event'に落ちる
   (ingestLineのdefault節) —— 前方フィルは明示的に選ぶものであって、既定ではない
   (T-13-06: 未知チャンネルが状態レーンへ落ちて無限に前方フィルされることを防ぐ)。

   classic script として書く (IIFE, 依存ゼロ, ビルド無し) —— pick.js / gl.js と
   同じ流儀。node:vm がブラウザと同じこのファイルをそのまま読めるよう、
   `const`/`export` ではなく globalThis.SimStore へ代入する
   (store-selftest.mjs が pick-selftest.mjs と同じ node:vm ローダで読む)。
   ============================================================================= */
'use strict';

globalThis.SimStore = (function () {

  // x,y,z,yaw,pitch,vx,vy,vz,hp,hy,agg の11個をこの順でFloat32Arrayに詰める。
  const STRIDE = 11;
  // vis: age,scale,alpha,color,spin の5個。posと違い補間しない(整数age・カテゴリ的
  // なcolorを含むため——13-PATTERNS.md/13-02-PLAN.mdの明示)。
  const VIS_STRIDE = 5;
  // 変化点配列(Int32Array/Float32Array)の初期容量。尽きたら2倍に伸ばしてコピーし直す。
  const CAP0 = 256;

  // 実測の1tick最大移動量 3.000m(stairs/20260820-153927 と stairs/20260818-034643の
  // 連続tickペア11,601件、いずれもprojectile、p50=0.381/0.115、p999=3.000/2.507、
  // PHASE13-INPUT-2026-08-21-viewer-perf.md 由来ではなく13-01-PLAN.md interface_contextの実測値)。
  // アリーナ半径24mの1/3、実測最速の2.7倍の位置に閾値を置く —— 正規の高速移動
  // (弾・突進)を誤ってスナップせず、真のテレポート(召喚/リスポーン/巻き戻し境界)だけを
  // 引き伸ばさずに捉える。
  const TELEPORT_M = 8.0;

  // 13-02: チャンネル分類の唯一の対応表。状態か事象かは、ここだけ見れば判る。
  // meta/spawn/gone/end はtickの系列ではなく索引/1回きりのイベントなので'index'。
  // ingestLineはmeta/spawn/gone/endを専用分岐で処理し(entities/metaの更新を伴うため)、
  // pos/vis/phys/animは専用分岐で状態レーンへ、それ以外(ai/dmg/sound/proj/logと
  // 未知の全チャンネル)はdefault節でひとまとめに事象レーンへ積む —— 新しいチャンネルを
  // 追加する人はこの表を更新するだけで済むようにするのが目的で、実際の分岐先は
  // ingestLine内のswitchが決める(表は分類のドキュメントであり、かつ以下で
  // state/eventの2値判定にも実際に使う)。
  const CHANNEL_LANES = Object.freeze({
    pos: 'state', vis: 'state', phys: 'state', anim: 'state',
    meta: 'index', spawn: 'index', gone: 'index', end: 'index',
    ai: 'event', dmg: 'event', sound: 'event', proj: 'event', log: 'event',
  });

  /** ticks[0..n) は昇順。t 以下で最大の index を二分探索で返す。無ければ -1
   *  (=最初の変化点より前。「まだ知らない」であって0ではない)。 */
  function findFloorIndex(ticks, n, t) {
    let lo = 0, hi = n - 1, ans = -1;
    while (lo <= hi) {
      const mid = (lo + hi) >> 1;
      if (ticks[mid] <= t) { ans = mid; lo = mid + 1; } else { hi = mid - 1; }
    }
    return ans;
  }

  /** [0,n) の添字空間で、key(i) が昇順である前提。key(i) >= t になる最初の index
   *  (下限)。事象レーンの「この tick 区間の [開始,終了) を切り出す」に使う。 */
  function lowerBoundBy(n, t, key) {
    let lo = 0, hi = n;
    while (lo < hi) { const mid = (lo + hi) >> 1; if (key(mid) < t) lo = mid + 1; else hi = mid; }
    return lo;
  }
  /** key(i) > t になる最初の index (上限)。 */
  function upperBoundBy(n, t, key) {
    let lo = 0, hi = n;
    while (lo < hi) { const mid = (lo + hi) >> 1; if (key(mid) <= t) lo = mid + 1; else hi = mid; }
    return lo;
  }

  function now() {
    return (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now();
  }

  /** 「同じ ch+id で、t 以外の全フィールドが等しい」の唯一の定義。チャンネルに
   *  依存しない汎用比較 —— pos/vis/phys/anim いずれの取り込み時デデュプにも使う。
   *  ストアの取り込み(append)と、将来(13-04)の jar 側 delta エンコーダの読み側
   *  検証が、同じこの1個を使う。 */
  function rowIsRedundant(prevRow, row) {
    if (!prevRow || !row) return false;
    const keys = new Set(Object.keys(prevRow).concat(Object.keys(row)));
    keys.delete('t');
    for (const k of keys) {
      if (prevRow[k] !== row[k]) return false;
    }
    return true;
  }

  function create() {
    const lanes = new Map();     // pos: id -> {ticks:Int32Array, values:Float32Array, n:number}
    const lastRow = new Map();   // pos: id -> 直前に取り込んだ生のpos行(冗長判定用)

    const visLanes = new Map();  // vis: id -> {ticks:Int32Array, values:Float32Array, n:number}
    const lastVisRow = new Map(); // vis: id -> 直前に取り込んだ生のvis行(冗長判定用)

    // phys/anim: 霊夢1体ぶんの単一レーン(id-keyedではない)。tick昇順の生行配列。
    // 「霊夢1体ぶん」なので、旧dense frameの f.phys=e / f.anim=e (直近1件を保持するだけ、
    // idで区別しない)と同じ前提を踏襲する。
    const physLane = [];
    let lastPhysRow = null;
    const animLane = [];
    let lastAnimRow = null;

    // event: ch -> {ticks:number[], rows:object[]}。ai/dmg/sound/proj/log と
    // 未知の全チャンネルがここに積まれる。前方フィルしない。
    const eventLanes = new Map();

    const entities = new Map();  // id -> {id,type,role,name,w,h,maxHp,first,last,goneAt}
    // entities ゲッタの防御的コピーを**集合が変わった時だけ**作り直すための版番号。
    // 旧実装は読むたび new Map(entities) しており、appendLive が毎 ingest(20回/秒)
    // 読むので、レーン 2 万本で 1.05ms/ingest を払っていた(2026-08-23 実測)。
    // 中身のオブジェクト(first/last/goneAt)は共有なので、値の更新では版は上げない
    // —— 上げる必要があるのは「どの id が居るか」が変わったときだけ。
    let entitiesVer = 0, entitiesView = null;
    const touchEntities = () => { entitiesVer++; entitiesView = null; };
    let meta = null, reimuId = null, maxTick = -1;
    let rows = 0, changePoints = 0, lastAppendMs = 0, appendMsEma = 0, frameAtMsEma = 0;
    // 取り込めなかった行。**0 でないことがそのまま「表示が信用できない」の意味になる**
    // ので、数を捨てずに持って呼び出し側へ出す (Viewer は右下に出す)。
    let droppedRows = 0, lastDropReason = null;
    // 履歴の切り捨て(ライブの直近2分)。minTick より前は「知らない」を返す。
    let minTick = 0, trims = 0, trimmedPoints = 0, trimmedEntities = 0, lastTrimMs = 0;

    // ---------------------------------------------------------------------
    // pos: 13-01からの既存実装。無改変(補間・テレポート判定・yaw最短弧を含む
    // 既にレビュー済みの挙動をここで壊さないため)。
    // ---------------------------------------------------------------------
    function ensureLane(id) {
      let lane = lanes.get(id);
      if (!lane) {
        lane = { ticks: new Int32Array(CAP0), values: new Float32Array(CAP0 * STRIDE), n: 0, syntheticAnchor: false };
        lanes.set(id, lane);
      }
      return lane;
    }
    function growLane(lane) {
      const cap2 = lane.ticks.length * 2;
      const nt = new Int32Array(cap2); nt.set(lane.ticks); lane.ticks = nt;
      const nv = new Float32Array(cap2 * STRIDE); nv.set(lane.values); lane.values = nv;
    }
    function pushChangePoint(id, t, row) {
      const lane = ensureLane(id);
      // WR-02(code review 150d56a5): findFloorIndexの二分探索はlane.ticksが昇順で
      // あることが前提。この契約(「呼び出し側が新着分だけ渡す」)を実行時に検査せずに
      // 破られると、二分探索はエラーを出さずに静かに間違った値を返す(壊れたことに
      // 気づけない方向に倒れる)。今のうちに検査を入れておく——13-03のライブ差分追記
      // 実装で間違って古いtickを渡してしまった場合に、大きな音を立てて止まるように。
      if (lane.n > 0 && t <= lane.ticks[lane.n - 1]) {
        throw new Error('SimStore: id=' + id + ' の pos が非単調 (前回tick=' + lane.ticks[lane.n - 1] + ', 今回tick=' + t + ')');
      }
      if (lane.n >= lane.ticks.length) growLane(lane);
      lane.ticks[lane.n] = t;
      const base = lane.n * STRIDE, v = lane.values;
      v[base + 0] = row.x; v[base + 1] = row.y; v[base + 2] = row.z;
      v[base + 3] = typeof row.yaw === 'number' ? row.yaw : NaN;
      v[base + 4] = typeof row.pitch === 'number' ? row.pitch : NaN;
      v[base + 5] = typeof row.vx === 'number' ? row.vx : NaN;
      v[base + 6] = typeof row.vy === 'number' ? row.vy : NaN;
      v[base + 7] = typeof row.vz === 'number' ? row.vz : NaN;
      v[base + 8] = typeof row.hp === 'number' ? row.hp : NaN;
      v[base + 9] = typeof row.hy === 'number' ? row.hy : NaN;
      v[base + 10] = row.agg ? 1 : 0;
      lane.n++;
      changePoints++;
    }
    /**
     * この id について覚えている全てを捨てる。
     *
     * <b>Minecraft の entity id は再利用される。</b> 水槽は何度も出し入れするので実際に
     * 起きる (jar 側は同じ理由で SimArena が delta.forget(id) を呼んでいる —— 
     * Viewer 側にその対になる処理が無かった)。忘れずに新しい entity の点列を
     * 同じレーンへ積むと、前の entity の位置と新しい位置の間を補間してしまい、
     * 「地面を貫通して飛んで、すぐ戻る」ように見える。
     */
    function forgetId(id) {
      lanes.delete(id); visLanes.delete(id);
      lastRow.delete(id); lastVisRow.delete(id);
    }

    /** 指定tickで有効なvalues(Float32Arrayのview, 長さ11)。無ければnull。 */
    function laneValuesAt(lane, t) {
      const idx = findFloorIndex(lane.ticks, lane.n, t);
      if (idx < 0) return null;
      const base = idx * STRIDE;
      return lane.values.subarray(base, base + STRIDE);
    }
    /** Float32Arrayの値列 -> 消費側が読む行オブジェクト。
     *  欠測フィールド(NaN sentinel)はキーごと省く —— typeof row.hp==='number' の
     *  ような既存の消費側チェックを壊さないため(undefinedであってNaNではない)。 */
    function rowFromValues(id, t, v) {
      const row = { id: id, t: t, x: v[0], y: v[1], z: v[2] };
      if (!Number.isNaN(v[3])) row.yaw = v[3];
      if (!Number.isNaN(v[4])) row.pitch = v[4];
      if (!Number.isNaN(v[5])) row.vx = v[5];
      if (!Number.isNaN(v[6])) row.vy = v[6];
      if (!Number.isNaN(v[7])) row.vz = v[7];
      if (!Number.isNaN(v[8])) row.hp = v[8];
      if (!Number.isNaN(v[9])) row.hy = v[9];
      if (v[10] === 1) row.agg = true;
      return row;
    }

    // ---------------------------------------------------------------------
    // vis: 13-02で新設。posと同じTypedArray+二分探索の型だが、補間はしない
    // (呼び出し側は常にstateAt相当=直前値そのまま)。エンティティごとのレーン。
    // ---------------------------------------------------------------------
    function ensureVisLane(id) {
      let lane = visLanes.get(id);
      if (!lane) {
        lane = { ticks: new Int32Array(CAP0), values: new Float32Array(CAP0 * VIS_STRIDE), n: 0 };
        visLanes.set(id, lane);
      }
      return lane;
    }
    function growVisLane(lane) {
      const cap2 = lane.ticks.length * 2;
      const nt = new Int32Array(cap2); nt.set(lane.ticks); lane.ticks = nt;
      const nv = new Float32Array(cap2 * VIS_STRIDE); nv.set(lane.values); lane.values = nv;
    }
    function pushVisChangePoint(id, t, row) {
      const lane = ensureVisLane(id);
      if (lane.n > 0 && t <= lane.ticks[lane.n - 1]) {
        throw new Error('SimStore: id=' + id + ' の vis が非単調 (前回tick=' + lane.ticks[lane.n - 1] + ', 今回tick=' + t + ')');
      }
      if (lane.n >= lane.ticks.length) growVisLane(lane);
      lane.ticks[lane.n] = t;
      const base = lane.n * VIS_STRIDE, v = lane.values;
      v[base + 0] = typeof row.age === 'number' ? row.age : NaN;
      v[base + 1] = typeof row.scale === 'number' ? row.scale : NaN;
      v[base + 2] = typeof row.alpha === 'number' ? row.alpha : NaN;
      v[base + 3] = typeof row.color === 'number' ? row.color : NaN;
      v[base + 4] = typeof row.spin === 'number' ? row.spin : NaN;
      lane.n++;
      changePoints++;
    }
    function visValuesAt(lane, t) {
      const idx = findFloorIndex(lane.ticks, lane.n, t);
      if (idx < 0) return null;
      const base = idx * VIS_STRIDE;
      return lane.values.subarray(base, base + VIS_STRIDE);
    }
    function visRowFromValues(id, t, v) {
      const row = { id: id, t: t };
      if (!Number.isNaN(v[0])) row.age = v[0];
      if (!Number.isNaN(v[1])) row.scale = v[1];
      if (!Number.isNaN(v[2])) row.alpha = v[2];
      if (!Number.isNaN(v[3])) row.color = v[3];
      if (!Number.isNaN(v[4])) row.spin = v[4];
      return row;
    }
    /** t時点のvis(前方フィル・補間なし)。CR-01と同じ生存期間ルールを共有する
     *  (goneした後はnull) —— visもpos同様、死んだentityの見た目を凍りつかせない。 */
    function visStateAt(id, t) {
      if (!isAlive(id, t)) return null;
      const lane = visLanes.get(id);
      if (!lane) return null;
      const v = visValuesAt(lane, t);
      if (!v) return null;
      return visRowFromValues(id, t, v);
    }

    // ---------------------------------------------------------------------
    // phys/anim: 13-02で新設。霊夢1体ぶんの単一レーン。animはmolang文字列を
    // 含むため数値配列に入らない —— 変化点tickを持つ生オブジェクトの配列として、
    // そのまま(コピーせず)積む。phys(全フィールド数値/真偽値)もこれに揃える
    // (件数が小さい: 放置1時間で高々百〜数千件、オブジェクトで持っても支配しない)。
    // ---------------------------------------------------------------------
    /** arr(t昇順のオブジェクト配列)からt以下で最後の要素のindexを二分探索。 */
    function floorIndexByRowTick(arr, t) {
      let lo = 0, hi = arr.length - 1, ans = -1;
      while (lo <= hi) {
        const mid = (lo + hi) >> 1;
        if (arr[mid].t <= t) { ans = mid; lo = mid + 1; } else { hi = mid - 1; }
      }
      return ans;
    }
    function pushSingletonChangePoint(arr, t, row) {
      if (arr.length > 0 && t <= arr[arr.length - 1].t) {
        throw new Error('SimStore: 単一レーンのtickが非単調 (前回tick=' + arr[arr.length - 1].t + ', 今回tick=' + t + ')');
      }
      arr.push(row);
      changePoints++;
    }
    /** t時点の値(前方フィル)。ownerIdが判れば生存期間(isAlive)も見る —— phys/anim
     *  は常にreimuの値なので、呼び出し側はreimuIdを渡す。見つかった行の.tは
     *  「記録されたtick」のまま残っているとposの慣習(常に問い合わせtickを返す)と
     *  食い違うので、前方フィルで借用したときだけ問い合わせtickへ上書きする
     *  (完全一致のときは新規オブジェクトを作らない=無駄な割り当てを避ける)。 */
    function singletonStateAt(arr, t, ownerId) {
      if (ownerId != null && !isAlive(ownerId, t)) return null;
      const idx = floorIndexByRowTick(arr, t);
      if (idx < 0) return null;
      const row = arr[idx];
      return row.t === t ? row : Object.assign({}, row, { t: t });
    }

    // ---------------------------------------------------------------------
    // event: 13-02で新設。ai/dmg/sound/proj/log と未知の全チャンネル。
    // 前方フィルしない —— 行はそれが記録されたtickにだけ属する。
    // ---------------------------------------------------------------------
    function ensureEventLane(ch) {
      let lane = eventLanes.get(ch);
      if (!lane) { lane = { ticks: [], rows: [] }; eventLanes.set(ch, lane); }
      return lane;
    }
    function pushEvent(ch, t, row) {
      const lane = ensureEventLane(ch);
      const n = lane.ticks.length;
      // 同一tickに複数行(例: 同tickの複数dmg/proj)は許すが、逆行は許さない
      // (pushChangePointのWR-02と同じ考え方。event側は同値を許すのでt<=ではなくt<)。
      if (n > 0 && t < lane.ticks[n - 1]) {
        throw new Error('SimStore: ch=' + ch + ' の tick が非単調 (前回tick=' + lane.ticks[n - 1] + ', 今回tick=' + t + ')');
      }
      lane.ticks.push(t);
      lane.rows.push(row);
      changePoints++;
    }
    /** ちょうどそのtickに属する行だけ(前方フィルしない)。frameAtが使う。 */
    function eventsAtTick(ch, t) {
      const lane = eventLanes.get(ch);
      if (!lane) return [];
      const n = lane.ticks.length;
      const lo = lowerBoundBy(n, t, (i) => lane.ticks[i]);
      const hi = upperBoundBy(n, t, (i) => lane.ticks[i]);
      return lane.rows.slice(lo, hi);
    }
    /** [t0,t1] の範囲の行(窓走査用。volleyMetricsが使う)。 */
    function eventsInRange(ch, t0, t1) {
      const lane = eventLanes.get(ch);
      if (!lane) return [];
      const n = lane.ticks.length;
      const lo = lowerBoundBy(n, t0, (i) => lane.ticks[i]);
      const hi = upperBoundBy(n, t1, (i) => lane.ticks[i]);
      return lane.rows.slice(lo, hi);
    }
    /** t以下で最後の事象(curAiが使う。「直近の判断」を二分探索で答える —— 2本目の
     *  レーンを作らず、事象レーン1本への問い合わせで済ませる、13-PLAN interface_context
     *  の指示どおり)。 */
    function latestEvent(ch, t) {
      const lane = eventLanes.get(ch);
      if (!lane) return null;
      const n = lane.ticks.length;
      const hi = upperBoundBy(n, t, (i) => lane.ticks[i]);
      return hi > 0 ? lane.rows[hi - 1] : null;
    }
    /** 総件数(表示上限の注記に使う)。 */
    function eventCount(ch) {
      const lane = eventLanes.get(ch);
      return lane ? lane.rows.length : 0;
    }

    function ingestLine(line) {
      let e; try { e = JSON.parse(line); } catch (err) { return false; }
      const t = e.t | 0;
      if (t > maxTick) maxTick = t;
      rows++;
      switch (e.ch) {
        case 'meta': meta = e; return true;
        case 'spawn': {
          const old = entities.get(e.id);
          // **同じ行の再送と、id の再利用を区別する。**
          // 再送 (配信を繋ぎ直した等) は既に持っている spawn なので、記録を作り直すと
          // goneAt が消えて**死んだモブが復活し、死んだ位置に凍りついたまま
          // 描かれ続ける**。逆に、既知の最終 tick より後の spawn は本物の id 再利用
          // なので、前の entity の点列を捨てないと 2 体ぶんが 1 レーンに混ざる。
          if (old && t <= old.last) return true;      // 再送: 何もしない
          if (old) forgetId(e.id);                    // 再利用: 前の entity を忘れる
          // uuid: 走っている水槽から名指しで消すために持つ (Viewer の「中にいる」の ×)。
          // 古いトレースには無いので undefined を許す —— 無ければ × を出さないだけ。
          entities.set(e.id, { id: e.id, type: e.type, role: e.role, name: e.name, uuid: e.uuid, w: e.w || 0.5, h: e.h || 0.5, maxHp: e.maxHp, first: t, last: t, goneAt: undefined });
          touchEntities();
          if (e.role === 'reimu') reimuId = e.id;
          return true;
        }
        // goneAt は「この id が明示的に gone した tick」専用。last(=最後にpos/gone
        // イベントを見たtick)と分けて持つのが重要 —— last は生存中も毎tick進むので
        // 死亡判定の代わりに使うと (a) このストアへ流し込まれたテキストの範囲が
        // 途中で終わっている場合(ブラウザで巻き戻して見ているだけ・トレースがまだ
        // 続き中)に生存中のentityまで「最後の更新から先は死亡」と誤判定し、
        // (b) 13-04で無変化のposが省略されるようになった後は静止した生存entityを
        // 誤って消してしまう。死亡は gone という明示的なイベントでしか判定しない
        // (store-selftest.mjs の denseGroundTruth と同じ設計 —— 13-03 が同じ
        // isAlive をそのまま再利用できるように、ここが唯一の生存期間ルールの定義)。
        case 'gone': {
          let en = entities.get(e.id);
          // **spawn を知らなくても、死は記録する。** 以前はここで黙って捨てていたので、
          // 何かの理由で spawn 行を取り込み損ねた id は isAlive の「判らないので通す」に
          // 落ちて**永久に生き続けた**。死を落とすほうが、知らない箱を描くより害が大きい。
          if (!en) {
            en = { id: e.id, type: '?', role: undefined, name: '#' + e.id, w: 0.5, h: 0.5, first: t, last: t };
            entities.set(e.id, en);
            touchEntities();
          }
          en.last = t; en.goneAt = t;
          return true;
        }
        // end: tickの系列としては消費しない(indexレーン)。取り込み失敗ではない。
        case 'end': return true;
        case 'pos': {
          const en = entities.get(e.id); if (en) en.last = t;
          const prev = lastRow.get(e.id);
          if (!rowIsRedundant(prev, e)) pushChangePoint(e.id, t, e);
          lastRow.set(e.id, e);
          return true;
        }
        case 'vis': {
          const prev = lastVisRow.get(e.id);
          if (!rowIsRedundant(prev, e)) pushVisChangePoint(e.id, t, e);
          lastVisRow.set(e.id, e);
          return true;
        }
        case 'phys': {
          if (!rowIsRedundant(lastPhysRow, e)) pushSingletonChangePoint(physLane, t, e);
          lastPhysRow = e;
          return true;
        }
        case 'anim': {
          if (!rowIsRedundant(lastAnimRow, e)) pushSingletonChangePoint(animLane, t, e);
          lastAnimRow = e;
          return true;
        }
        default:
          // ai/dmg/sound/proj/log と、未知のチャンネル全部がここに落ちる
          // (CHANNEL_LANESの既定'event' —— T-13-06: 前方フィルは明示的に選ぶもの)。
          pushEvent(e.ch, t, e);
          return true;
      }
    }

    /** JSONL(text または 行配列)を取り込む。既に取り込んだ行を再度渡してはならない
     *  (呼び出し側が新着分だけ渡す契約 —— 13-03のライブ差分追記が前提にする)。 */
    function append(input) {
      const t0 = now();
      const lines = Array.isArray(input) ? input : String(input).split('\n');
      let ingested = 0;
      const cp0 = changePoints;
      // **1 行の失敗でバッチ全体を落とさない。**
      // 以前は ingestLine の例外がそのまま append を抜け、呼び出し側 (ライブの
      // setInterval) ごと殺していた。livePending は既に空にした後なので、
      // **そのバッチの行が永久に失われる** —— gone が混ざればモブが死ななくなり、
      // pos が混ざれば位置がずれる (2026-08-23)。
      // 契約違反は「大きな音を立てる」ままにする (WR-02 の意図) が、音の出し方を
      // 例外の伝播から**数えて表に出す**へ変えた。黙って欠けるのが一番たちが悪い。
      let dropped = 0;
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        if (!line || !line.trim()) continue;
        try {
          if (ingestLine(line)) ingested++;
        } catch (err) {
          dropped++; droppedRows++;
          if (!lastDropReason) {
            lastDropReason = String(err && err.message || err);
            if (typeof console !== 'undefined') console.warn('[SimStore] 行を取り込めなかった:', lastDropReason);
          }
        }
      }
      const ms = now() - t0;
      lastAppendMs = ms;
      appendMsEma = appendMsEma ? appendMsEma * 0.85 + ms * 0.15 : ms;
      return { ingested: ingested, changePoints: changePoints - cp0, ms: ms, dropped: dropped };
    }

    /** CR-01(code review 150d56a5): t時点でこのidを表示してよいか。goneAt(明示的な
     *  gone tick)だけを境界にする —— entities.get(id).last(=最後にpos/goneを見たtick)
     *  ではない。last は生存中も毎tick進むので、これを死亡判定に使うと (a) このfixture
     *  自体がt<=60で切られているだけで実際は生きているentity(reimuなど、goneを
     *  一度も受け取らない)がt=61以降すべて誤って「死亡」扱いになり、(b) 13-04で
     *  無変化のpos行が省略されるようになった後は静止した生存entityまで消えてしまう。
     *  死亡は gone という明示的なイベントでしか判定しない
     *  (store-selftest.mjs の denseGroundTruth と同じ設計。13-03 が同じ生存期間
     *  ルールを再利用できるよう、公開API(S.isAlive)としても出す)。
     *  13-02: vis/phys/animも同じこの関数で生存判定する(状態チャンネルは全部
     *  「エンティティのlast tickで止める」という13-02-PLAN interface_contextの分類どおり)。 */
    function isAlive(id, t) {
      const ent = entities.get(id);
      if (!ent) return true; // spawn情報が無ければ判定できないので現状維持(通す)
      return ent.goneAt === undefined || t <= ent.goneAt;
    }

    /** t時点で有効な行(前方フィル)。最初の変化点より前はnull。gone後もnull。
     *  ch別に対応する状態レーンへ振り分ける。pos以外(vis/phys/anim)にも対応
     *  (13-02) —— phys/animはidを無視して常にreimuの単一レーンを見る
     *  (「霊夢1体ぶんのレーン」という設計どおり)。 */
    function stateAt(ch, id, t) {
      const tt = t | 0;
      if (ch === 'pos') {
        if (!isAlive(id, tt)) return null;
        const lane = lanes.get(id);
        if (!lane) return null;
        const v = laneValuesAt(lane, tt);
        if (!v) return null;
        return rowFromValues(id, tt, v);
      }
      if (ch === 'vis') return visStateAt(id, tt);
      if (ch === 'phys') return singletonStateAt(physLane, tt, reimuId);
      if (ch === 'anim') return singletonStateAt(animLane, tt, reimuId);
      return null;
    }

    /** 1entity分の、partial補間込みの行(posのみ)。tt/entities は呼び出し側で確定済みの前提。 */
    function entityInterpAt(id, tt, partial) {
      if (!isAlive(id, tt)) return null; // CR-01: partial<=0のfast pathより前で判定する
      const lane = lanes.get(id);
      if (!lane) return null;
      const av = laneValuesAt(lane, tt);
      if (!av) return null; // まだ知らない
      if (partial <= 0) return rowFromValues(id, tt, av);
      // **記録の先へは外挿しない。** 判定は maxTick だけで足りる。
      //
      // 以前はここに `|| tt >= ent.last` があったが、行デルタ化(2026-08-22)と
      // 噛み合わず**補間を全面的に殺していた**。ent.last は「最後に行が出た tick」で、
      // 毎 tick 行が出ていた頃は常に現在より先行していたので無害だった。行が
      // 変化時のみになると last は現在位置に張り付き、ライブ(tt=maxTick-1 で追従)では
      // `tt >= last` がほぼ常に真になって、この関数は毎回 fast path へ落ちていた。
      // 実測(にーくら報告→確認): partial を 0/0.5/0.99 と振っても座標が 1mm も動かず、
      // 「5fps の動画を 100fps で見ている」状態だった。
      //
      // エンティティの生存は先頭の isAlive(id,tt) が既に見ている。tt+1 に値が無い
      // ケースも下の `if (!bv)` が拾う。だから last による打ち切りは重複であり、
      // デルタ化後は有害なだけ。
      if (tt >= maxTick) return rowFromValues(id, tt, av);
      const bv = laneValuesAt(lane, tt + 1);
      if (!bv) return rowFromValues(id, tt, av);
      const dx = bv[0] - av[0], dy = bv[1] - av[1], dz = bv[2] - av[2];
      if (Math.sqrt(dx * dx + dy * dy + dz * dz) > TELEPORT_M) return rowFromValues(id, tt, av); // テレポートは引き伸ばさない
      const lerp = (a, b, p) => a + (b - a) * p;
      // 最短弧: 170->-170 の中間は絶対値180であって0ではない (Mth.rotLerp と同じ考え方)
      const angLerp = (a, b, p) => { const d = (((b - a + 180) % 360) + 360) % 360 - 180; return a + d * p; };
      const out = av.slice(); // Float32Array の独立コピー(元データは書き換えない)
      out[0] = lerp(av[0], bv[0], partial);
      out[1] = lerp(av[1], bv[1], partial);
      out[2] = lerp(av[2], bv[2], partial);
      if (!Number.isNaN(av[3]) && !Number.isNaN(bv[3])) out[3] = angLerp(av[3], bv[3], partial); // yaw: 最短弧
      if (!Number.isNaN(av[4]) && !Number.isNaN(bv[4])) out[4] = lerp(av[4], bv[4], partial);     // pitch: 素のlerp
      if (!Number.isNaN(av[9]) && !Number.isNaN(bv[9])) out[9] = angLerp(av[9], bv[9], partial); // hy: 最短弧
      // vx,vy,vz(5-7)・hp(8)・agg(10) は補間せずaを保つ(outはav.slice()済みなので既にa)
      return rowFromValues(id, tt, out);
    }

    /** 弾の点列(D.tracksの置き換え。13-02 Task 2)。複製を持たない —— posレーンへ
     *  そのまま委譲するだけの薄いビュー。t0/t1は変化点の範囲(この間はisAliveで
     *  自然に打ち切られる)。at(t)は毎回stateAt('pos',...)相当(二分探索1回)。 */
    function trackOf(id) {
      const lane = lanes.get(id);
      if (!lane || lane.n === 0) return null;
      return {
        t0: lane.ticks[0],
        t1: lane.ticks[lane.n - 1],
        at: (t) => stateAt('pos', id, t),
        /**
         * SampledMotionTrace v1 用の「保持されている点」だけを返す。
         *
         * at(t) は前方フィルされた状態なので、任意tickを「観測点」として扱ってはいけない。
         * samples() は pos レーンに実際に残っている変化点/ライブ窓アンカーだけを公開し、
         * 由来を明示した source_observation_id を付ける。二次的な軌跡生成側はこの入口を
         * 使うことで、前方フィルを生観測と取り違えない。
         */
        samples: (startTick, endTick, limit) => {
          const start = startTick == null ? lane.ticks[0] : (startTick | 0);
          const end = endTick == null ? lane.ticks[lane.n - 1] : (endTick | 0);
          const max = limit == null ? 4096 : (limit | 0);
          if (max < 1) throw new Error('SimStore.trackOf.samples: limit must be positive');
          if (end < start) return [];
          const lo = lowerBoundBy(lane.n, start, (i) => lane.ticks[i]);
          const hi = upperBoundBy(lane.n, end, (i) => lane.ticks[i]);
          if (hi - lo > max) {
            throw new Error('SimStore.trackOf.samples: retained sample count ' + (hi - lo) + ' exceeds limit ' + max);
          }
          const out = [];
          for (let i = lo; i < hi; i++) {
            // trimBefore() が状態継続のために左端へ移した合成アンカーは、
            // 位置問い合わせには必要でも「観測されたサンプル」ではない。
            if (i === 0 && lane.syntheticAnchor === true) continue;
            const tick = lane.ticks[i];
            const base = i * STRIDE;
            const row = rowFromValues(id, tick, lane.values.subarray(base, base + STRIDE));
            row.source_observation_id = 'simlab-pos:' + id + ':' + tick;
            row.source_kind = 'SIMLAB_POS_RETAINED_POINT';
            out.push(row);
          }
          return out;
        },
        /** 直近の保持点を二分探索で1件だけ返す。前方フィルした問い合わせ値ではない。 */
        sampleAtOrBefore: (tick) => {
          const i = findFloorIndex(lane.ticks, lane.n, tick | 0);
          if (i < 0 || (i === 0 && lane.syntheticAnchor === true)) return null;
          const sampleTick = lane.ticks[i];
          const base = i * STRIDE;
          const row = rowFromValues(id, sampleTick, lane.values.subarray(base, base + STRIDE));
          row.source_observation_id = 'simlab-pos:' + id + ':' + sampleTick;
          row.source_kind = 'SIMLAB_POS_RETAINED_POINT';
          return row;
        },
      };
    }

    /** 密フレームと同じ形のオブジェクトを返す唯一の入口。13-02でpos以外の全チャンネルも
     *  ここから返す(index.html側で密フレームから詰める必要がなくなった)。 */
    function frameAt(t, partial) {
      const t0 = now();
      const p = Math.max(0, Math.min(1, partial || 0));
      const tt = maxTick < 0 ? 0 : Math.max(0, Math.min(t | 0, maxTick));
      const pos = new Map();
      for (const id of lanes.keys()) {
        const row = entityInterpAt(id, tt, p);
        if (row) pos.set(id, row);
      }
      const vis = new Map();
      for (const id of visLanes.keys()) {
        const row = visStateAt(id, tt);
        if (row) vis.set(id, row);
      }
      const phys = singletonStateAt(physLane, tt, reimuId);
      const anim = singletonStateAt(animLane, tt, reimuId);
      const ms = now() - t0;
      frameAtMsEma = frameAtMsEma ? frameAtMsEma * 0.85 + ms * 0.15 : ms;
      return {
        t: tt, partial: p, pos: pos, vis: vis,
        ai: eventsAtTick('ai', tt), dmg: eventsAtTick('dmg', tt), sound: eventsAtTick('sound', tt),
        phys: phys, anim: anim,
        proj: eventsAtTick('proj', tt), log: eventsAtTick('log', tt),
      };
    }

    /* =======================================================================
       履歴の切り捨て（ライブの「直近2分」）

       にーくら 2026-08-23:
         「正直前にもどれるのは2分だけでいいよ。本当にさかのぼりたくなったら
          録画ボタンを押しておくし、それに、切り捨てられるとはいっても、
          デバッグログは残るだろう？」

       **不変条件: trimBefore(w) の後、t >= w の問い合わせは 1 ビットも変わらない。**
       そして t < w は「知らない」(null / 空)を返す ——
       前方フィルするストアが、もう持っていない区間に自信満々で答えるのは、
       黙って嘘をつくのと同じ。
       ======================================================================= */

    /**
     * 前方フィルするレーン(pos / vis)を w で切る。
     *
     * **「w 以下で最大の変化点」は捨てずに残し、その tick を w へ書き換える。**
     *   - 残す理由: jar は行デルタなので、w 時点の値は w よりずっと古い変化点から
     *     来ていることがある(静止したモブは変化点が 1 個しか無い)。捨てると
     *     そのモブは窓の中で丸ごと消える。
     *   - 書き換える理由: findFloorIndex は「ticks[i] <= t の最大 i」。k は
     *     ticks[k] <= w < ticks[k+1] で、しかも ticks[k+1] > w は**厳密**
     *     (等しければ findFloorIndex が k+1 を返していた)。だから w へ動かしても
     *     ticks[k+1] を越えず、t >= w の floor は同じ要素のまま = 答えは完全に同一。
     *     変わるのは t < w だけで、そこは -1(= まだ知らない)になる。
     *   - 単調性: 動かすのは先頭だけ、しかも前へのみ。ticks[n-1] に触れるのは
     *     n===1 のときだけで値は w <= maxTick。次の追記は必ず t > maxTick で来るので
     *     pushChangePoint の逆行検査は通る。
     */
    function trimStrided(lane, w, stride) {
      const k = findFloorIndex(lane.ticks, lane.n, w);
      if (k < 0) return 0;                       // 窓より前に変化点が無い。何もしない
      const sourceTick = lane.ticks[k];
      const sourceWasSynthetic = k === 0 && lane.syntheticAnchor === true;
      const keep = lane.n - k;
      if (k > 0) {
        lane.ticks.copyWithin(0, k, lane.n);
        lane.values.copyWithin(0, k * stride, lane.n * stride);
        lane.n = keep;
      }
      lane.ticks[0] = w;                          // アンカーを窓の左端へ寄せる
      // 状態問い合わせ用に tick を w へ寄せた点は「実際に w で観測した点」ではない。
      // Motion Trace がこの合成アンカーを生観測として扱わないよう印を保持する。
      lane.syntheticAnchor = sourceWasSynthetic || sourceTick < w;
      // 中身が容量の 1/4 を切ったらその 1 回だけ縮める。戦闘のピークで伸びたレーンが
      // 静かになった後も大きな Float32Array を握り続けるのを防ぐ。4 倍の余裕を残すので、
      // 伸ばし直しと縮め直しが交互に起きることはない。
      if (lane.ticks.length > CAP0 && keep * 4 <= lane.ticks.length) {
        let cap = CAP0; while (cap < keep * 2) cap *= 2;
        const nt = new Int32Array(cap); nt.set(lane.ticks.subarray(0, keep)); lane.ticks = nt;
        const nv = new Float32Array(cap * stride);
        nv.set(lane.values.subarray(0, keep * stride)); lane.values = nv;
      }
      return k;
    }

    /** phys / anim(生オブジェクトの単一レーン)。前方フィルするので pos と同じ規則。 */
    function trimSingleton(arr, w) {
      const k = floorIndexByRowTick(arr, w);
      if (k < 0) return 0;
      if (k > 0) arr.splice(0, k);
      // **共有オブジェクトを書き換えない。** arr[0] は singletonStateAt の fast path
      // (row.t === t なら生の参照を返す)で既に呼び出し側へ渡っている可能性がある。
      if (arr[0].t < w) arr[0] = Object.assign({}, arr[0], { t: w });
      return k;
    }

    /**
     * w より前の履歴を捨てる。**w 以降の答えは一切変わらない。**
     * maxTick / meta / reimuId / rows / changePoints には触れない
     * —— 呼び出し側が append の直後にこれを挟んでも、その後に読む値がずれないため。
     * 冪等: 同じか小さい w での再呼び出しは何もしない。
     */
    function trimBefore(w) {
      const t0 = now();
      w = w | 0;
      if (w <= minTick) return { minTick: minTick, points: 0, forgot: [], ms: 0 };
      // **全部は捨てない。** 窓が記録より長い/呼び出し側が間違えた場合でも各レーンに
      // 最低 1 点(= 今の姿)は残す —— 水槽が真っ白になる方が害が大きい。
      if (maxTick >= 0 && w > maxTick) w = maxTick;

      let points = 0;
      const forgot = [];

      // 1) entity ごと消せるものを先に消す(レーンを切る手間が丸ごと消える)。
      //    消してよい唯一の条件は「w 以降のどの tick でも isAlive が false」
      //    = goneAt < w。**last(最後に行を見た tick)では判定しない** ——
      //    静止した生存 entity を消してしまう(isAlive の CR-01 と同じ理由)。
      for (const ent of entities.values()) {
        if (ent.goneAt === undefined || ent.goneAt >= w) continue;
        // **霊夢だけは残す。** isAlive は未知の id に対して「判らないので通す」と
        // 開く方向へ倒れるので、記録を消すと singletonStateAt(physLane, t, reimuId) が
        // 生き返り、死んだ後の phys/anim が復活する。
        if (ent.id === reimuId) continue;
        const lane = lanes.get(ent.id); if (lane) points += lane.n;
        const vlane = visLanes.get(ent.id); if (vlane) points += vlane.n;
        forgetId(ent.id);
        forgot.push(ent.id);
      }
      for (const id of forgot) entities.delete(id);
      if (forgot.length) touchEntities();

      // 2) 残った前方フィルのレーンを切る(アンカーを 1 点残す)
      for (const lane of lanes.values()) points += trimStrided(lane, w, STRIDE);
      for (const lane of visLanes.values()) points += trimStrided(lane, w, VIS_STRIDE);
      points += trimSingleton(physLane, w);
      points += trimSingleton(animLane, w);

      // 3) 事象レーンは点。前方フィルしないので w 未満は捨てる。
      //    **ただし各チャンネル 1 行だけアンカーを残す** —— latestEvent(ch, t) は
      //    「t 以前で最も新しい行」を返す前方フィル的な問い合わせで、AI 表示が
      //    これを使っている。全部捨てると切った直後に表示が空白になる。
      //    アンカーの tick は**書き換えない**: eventsAtTick は「ちょうどその tick の行」
      //    なので、w へ動かすと過去のダメージが w で再発火する。
      for (const lane of eventLanes.values()) {
        const lo = lowerBoundBy(lane.ticks.length, w, (i) => lane.ticks[i]);
        const drop = Math.max(0, lo - 1);   // 1 行だけ残す
        if (drop > 0) { lane.ticks.splice(0, drop); lane.rows.splice(0, drop); points += drop; }
      }

      minTick = w;
      trims++; trimmedPoints += points; trimmedEntities += forgot.length;
      lastTrimMs = now() - t0;
      return { minTick: w, points: points, forgot: forgot, ms: lastTrimMs };
    }

    function reset() {
      minTick = 0; trims = 0; trimmedPoints = 0; trimmedEntities = 0; lastTrimMs = 0;
      lanes.clear(); lastRow.clear();
      visLanes.clear(); lastVisRow.clear();
      physLane.length = 0; lastPhysRow = null;
      animLane.length = 0; lastAnimRow = null;
      eventLanes.clear();
      entities.clear();
      meta = null; reimuId = null; maxTick = -1;
      rows = 0; changePoints = 0; lastAppendMs = 0; appendMsEma = 0; frameAtMsEma = 0;
      droppedRows = 0; lastDropReason = null;
      touchEntities();
    }

    return {
      append: append,
      rowIsRedundant: rowIsRedundant,
      stateAt: stateAt,
      frameAt: frameAt,
      isAlive: isAlive, // CR-01: 生存期間ルールの唯一の定義。13-03がこのまま再利用すること
      eventsInRange: eventsInRange,
      latestEvent: latestEvent,
      eventCount: eventCount,
      trackOf: trackOf,
      trimBefore: trimBefore,
      reset: reset,
      get minTick() { return minTick; },
      get maxTick() { return maxTick; },
      // IN-01(code review 150d56a5): 内部Mapを参照のまま返すと、呼び出し側の
      // .set()/.clear()でストアの内部状態が壊れうる。浅いコピーで防ぐ
      // (entityオブジェクト自体は共有だが、Map自体への書き込みはもう波及しない)。
      //
      // **ただし読むたびに作り直さない。** appendLive は毎 ingest(20回/秒)ここを読むので、
      // レーン 2 万本で 1.05ms/ingest を払っていた(2026-08-23 実測)。id の集合が
      // 変わった時だけ作り直す —— 中身のオブジェクトは元から共有なので、
      // first/last/goneAt の更新はコピーにもそのまま見える。
      get entities() { if (!entitiesView) entitiesView = new Map(entities); return entitiesView; },
      get entitiesVersion() { return entitiesVer; },
      // 取りこぼしだけを見るための安い口。stats は全レーンの byteLength を合計するので
      // (レーン 2 万本で 0.45ms)、毎 ingest の経路から踏ませない。
      get droppedRows() { return droppedRows; },
      get meta() { return meta; },
      get reimuId() { return reimuId; },
      get stats() {
        let bytes = 0;
        for (const lane of lanes.values()) bytes += lane.ticks.byteLength + lane.values.byteLength;
        for (const lane of visLanes.values()) bytes += lane.ticks.byteLength + lane.values.byteLength;
        return { rows: rows, changePoints: changePoints, bytes: bytes, lastAppendMs: lastAppendMs, appendMsEma: appendMsEma, frameAtMs: frameAtMsEma, droppedRows: droppedRows, lastDropReason: lastDropReason,
          minTick: minTick, trims: trims, trimmedPoints: trimmedPoints, trimmedEntities: trimmedEntities, lastTrimMs: lastTrimMs };
      },
    };
  }

  return { create: create, TELEPORT_M: TELEPORT_M, CHANNEL_LANES: CHANNEL_LANES };
})();
