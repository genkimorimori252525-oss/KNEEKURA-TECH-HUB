package com.github.tartaricacid.touhoulittlemaid.sim.trace;

import java.util.Arrays;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * SimLab トレース (JSONL) のチャンネル定義 —— <b>この空間の唯一の共有形式</b>。
 *
 * <p>1 行 = 1 イベント。全行が最低限 {@code {"t":<tick>,"ch":"<channel>"}} を持ち、
 * 残りはチャンネル毎のペイロード。にーくら(Viewer) と Claude(Analyzer) は
 * <b>同じ 1 本のファイル</b>をそれぞれの目で読む。
 *
 * <p><b>スキーマは最初から全チャンネル分をここに固定する。</b>
 * 書き出しの実装は段階的でよいが、形を後から変えるとトレース資産が全部無効になるため
 * 「まだ書いていないチャンネル」もここに定義だけしておく。
 *
 * <h3>チャンネル一覧</h3>
 * <pre>
 * meta   run 開始時に 1 行。scenario/seed/mod一覧/EntityType毎の hitbox 実サイズ表
 *          {"t":0,"ch":"meta","scenario":"smoke","seed":1234,"arena":0,
 *           "mods":["touhou_little_maid",...],
 *           "types":{"minecraft:zombie":{"w":0.6,"h":1.95},...}}
 * pos    エンティティ位置。毎 tick、追跡中の全 entity (弾を含む)
 *          {"t":42,"ch":"pos","id":314,"x":0.0,"y":64.0,"z":0.0,"yaw":90.0,"pitch":0.0,
 *           "vx":0.0,"vy":-0.08,"vz":0.0,"hp":20.0}
 * spawn  追跡対象が現れた。type/name/hitbox/役割 (actor/projectile)
 *          {"t":0,"ch":"spawn","id":314,"type":"touhou_little_maid:reimu","role":"reimu","w":0.6,"h":1.8}
 * gone   追跡対象が消えた (死亡/despawn)
 *          {"t":300,"ch":"gone","id":315,"reason":"dead"}
 * ai     霊夢の意思決定。<b>「何を選んだか」ではなく「なぜ選んだか」を残すのが目的</b>
 *          {"t":42,"ch":"ai","id":314,"mode":"GROUND","section":"...","anim":"...","combat":"..."}
 * proj   弾のライフサイクル。spawn/hit/gone。移動は pos に相乗りする
 *          {"t":42,"ch":"proj","ev":"spawn","id":900,"type":"...:hakurei_ofuda","owner":314,
 *           "vx":0.0,"vy":0.0,"vz":1.4,"w":0.25,"h":0.25}
 * sound  鳴った音。ServerLevel#playSeededSound を 1 箇所で押さえて全部拾う
 *          {"t":42,"ch":"sound","id":"minecraft:entity.arrow.shoot","src":"HOSTILE",
 *           "x":0.0,"y":64.0,"z":0.0,"vol":1.0,"pitch":1.2}
 * dmg    与ダメ/被ダメ。誰が誰にどの弾で何ダメージ
 *          {"t":42,"ch":"dmg","victim":315,"attacker":314,"direct":900,"amount":4.0,"src":"magic","hpAfter":96.0}
 * phys   物理サマリ。<b>見た目バグを数値で検出するためのチャンネル</b>
 *          {"t":42,"ch":"phys","id":314,"onG":false,"embed":false,"noGrav":true,"vel":0.31,"y":64.0}
 * anim   再生を要求した YSM アニメ / 送信 molang。ヘッドレスに描画は無いが
 *        「何を命令したか」は残る (実機の見た目バグと突き合わせる材料)
 *          {"t":42,"ch":"anim","id":314,"anim":"extra43","pend":"-","molang":"v.no_hold=1",
 *           "face":"(v.Ryanxs=1.2);(v.Lyanxs=1.2);(v.Lmeixuan=-5);(v.Rmeixuan=5);(v.roaming.zui=1)"}
 *          face は表情の molang 式 (平常/戦闘)。molang が「送った」ものなのに対し、
 *          face は「今の face 状態が意味する」もの —— 実際に撃つのは client なので
 *          server の送信履歴には現れない。Viewer はこれを読んで表情を再現する。
 * log    runner 自身の進行メモ (人間向け自由テキスト)
 *          {"t":0,"ch":"log","msg":"arena 0 ready: 2 actors"}
 * end    アリーナ終了サマリ
 *          {"t":600,"ch":"end","reason":"duration","ticks":600,"actors":{...}}
 * pose   (ドキュメント上の宣言のみ。本体 trace には書き込まれない) 姿勢 companion への
 *        参照チャンネル。<b>書き手が本体 trace (サーバ) とは異なりクライアント</b>である
 *        ため、実データは別プロセスが書く<b>別ファイル</b> ({@code <stamp>.pose.json} /
 *        {@code .pose.bin}、{@link com.github.tartaricacid.touhoulittlemaid.sim.client.SimPoseCodec}
 *        が読み書きする) に分離する。tick の突き合わせは companion 索引の {@code gt0} と
 *        この trace の {@code meta} チャンネルが持つ {@code gameTime} —— サーバではなく
 *        クライアントの {@code gameTime} だが、どちらも同じサーバ権威値が同期されたもの
 *        なので {@code t = gameTime - gt0} で機械的に対応づく (companion のスキーマ詳細は
 *        {@link com.github.tartaricacid.touhoulittlemaid.sim.client.SimPoseCodec} の javadoc)。
 * </pre>
 */
public final class SimCh {
    /**
     * run 開始時に1行だけ書かれるメタデータ。
     *
     * <p>Phase 13-04 で追加: {@code delta} と {@code keyframe}。この2つが読み側の
     * 「欠測 = 前の値」(前方フィル)という契約を宣言する。{@code delta} は行単位デルタの
     * 方式名(値は {@code "row"}、{@link SimDelta#DELTA_MODE})。{@code keyframe} は
     * 必ず書き直す tick 間隔({@link SimDelta#KEYFRAME_TICKS}、既定100)。対象チャンネルは
     * {@code pos}/{@code phys}/{@code anim} の3つ({@code ai} はこの2フィールドの新設以前
     * から既にデルタ化済み)。
     *
     * <p>この2フィールドは {@code required} には入れない —— この meta を持たない旧トレース
     * も読めなければならず(旧トレースは常に密=毎tick行がある、という1変種として扱われる)、
     * 書かれていなければ読み側は「無条件で毎tick書く」旧来の解釈のままでよい。**弱めたのは
     * 行そのものが在るか無いかであって、行が在るときに持つフィールド(例えば
     * {@code pos.required})は1つも動かしていない。**
     */
    public static final String META = "meta";
    public static final String POS = "pos";
    public static final String SPAWN = "spawn";
    public static final String GONE = "gone";
    /**
     * 霊夢の判断。<b>判断が変わった tick だけ</b>書かれる（毎 tick ではない）ので、
     * 「その phase に何 tick 居たか」を出すには次の観測まで保持する必要がある。
     *
     * <p>フィールド: {@code id mode hp maxHp target targetType dist form formMode
     * amuletCd houju gensou musouTp section} と、<b>Phase 10 で追加した {@code sec}</b>。
     *
     * <p>{@code section} は人が読む文字列、{@code sec} は<b>その同じ文字列</b>を
     * {@link SimSection#parse} で構造化したもの。供給点で 1 回だけパースするので
     * 表示と統計が食い違えない（AGENT-01）。Phase 10 より前のトレースは {@code sec} を持たず、
     * 解析側が {@code section} を同一アルゴリズムでパースして補う。
     */
    public static final String AI = "ai";
    /**
     * 弾。{@code ev} が {@code "spawn"} か {@code "gone"}。
     *
     * <p>Phase 10 で追加: {@code spawn} に <b>{@code phase}</b>（<b>その弾を撃った時点</b>の
     * 霊夢の技。着弾時ではない —— 追尾・滞留する弾では発射から着弾までに phase が変わるため）、
     * {@code gone} に <b>{@code type}</b>（実測で type が欠けていたのは gone だけだった:
     * spawn 141件は type 有、gone 141件は type 無）。
     */
    public static final String PROJ = "proj";
    public static final String SOUND = "sound";
    /**
     * 被弾。フィールド: {@code victim attacker direct amount src hpAfter} と、
     * <b>Phase 10 で追加した {@code attrib} / {@code projType} / {@code phase}</b>。
     *
     * <p>{@code attrib} は<b>どうやって技へ帰属させたか</b>。
     * <b>4 値のいずれも推測ではなく、根拠を1つずつ持っている</b>:
     * <ul>
     *   <li>{@code "direct"} —— 根拠は<b>弾の id</b>。直接の当たり元が spawn 時に作った台帳に在る。
     *       {@code phase} は<b>その弾を撃った時点</b>の技（台帳が発射時の値を持っている）</li>
     *   <li>{@code "melee"} —— 根拠は<b>id の一致</b>。attacker と direct が両方とも霊夢自身。
     *       {@code phase} は被弾 tick の現在値（弾を介さないので発射時が無い）</li>
     *   <li>{@code "stack"} —— 根拠は<b>呼び出しスタック</b>。attacker も direct も持たない
     *       magic ソースで、スタック上に台帳登録済みの弾クラスのフレームが在った。
     *       {@code phase} は<b>被弾時</b>の値しか付けられない —— 発射時は辿れない。
     *       <b>追尾・滞留する弾（陰陽玉・拡散札・宝珠場）では、発射から着弾までに phase が
     *       変わっていれば別の技の行に載る。</b>{@code direct} と同じ精度ではない</li>
     *   <li>{@code "none"} —— 根拠が<b>1つも無い</b>。上のどれにも当たらなかった。
     *       <b>捏造せず、数えて表に出す</b></li>
     * </ul>
     *
     * <p><b>命中率の精度は一様ではない。</b> {@code direct} は発射時の技に正しく紐づくが、
     * {@code stack} は着弾時の技にしか紐づかず、{@code none} の分は技別命中率に載らない。
     * 表と JSON は帰属できなかった件数を必ず併記する。
     *
     * <p><b>壊れ方が見える設計にしてある</b>: {@code stack} の経路が届かなくなっても
     * {@code none} が増えるだけで、<b>誤った数字にはならない</b>。
     */
    public static final String DMG = "dmg";
    public static final String PHYS = "phys";
    public static final String ANIM = "anim";
    public static final String LOG = "log";
    public static final String END = "end";
    /**
     * 「時間は進んでいる」とだけ言う行。**中身は t と ch だけ。**
     *
     * <p>行デルタ化 (2026-08-22) 以降、静かな水槽は行を 1 つも書かない。すると記録の上で
     * <b>「水槽が固まった」と「何も起きていない」が区別できない</b>。実測 (2026-08-23、
     * にーくらの 2 本の記録): <b>時間の 38〜57% が完全に無音で、最長 18.6 秒</b>。
     * Viewer の時計はその間「データが尽きた」と判断してブレーキを踏み、底に触れ、
     * 緩衝の目標を 18.8 tick まで膨らませていた —— 画が止まり、戦闘が再開すると
     * 1 秒遅れて追いかける。にーくらの「多くのモブと戦った後に重くなる」の正体。
     *
     * <p>他の行が何も出なかったときだけ出す (下の {@code SimArena.TICK_MARK_EVERY})。
     * 賑やかなときは 1 行も増えない。
     */
    public static final String TICK = "tick";
    /**
     * 見た目パラメータ。弾は「カメラ正対の板 1 枚 + テクスチャ + 加算合成」で描かれ、
     * 大きさ/不透明度/色/自転がすべて {@code getSyncXxx()} で同期されている
     * (例: {@code MusouMyoujuBulletRenderer})。位置だけでは実機の見た目を再現できないので、
     * これらを別チャンネルで残す。
     * <pre>{"t":42,"ch":"vis","id":900,"age":12,"scale":1.0,"alpha":0.8,"color":0,"spin":45.0}</pre>
     */
    public static final String VIS = "vis";
    /**
     * 姿勢 companion への参照チャンネル (ドキュメント上の宣言のみ)。<b>本体 trace には
     * 書き込まれない</b> —— 書き手がサーバではなくクライアントであるため、実データは
     * {@code <stamp>.pose.json}/{@code .pose.bin} という<b>別ファイル</b>に分離される
     * ({@link com.github.tartaricacid.touhoulittlemaid.sim.client.SimPoseCodec} が読み書き)。
     * tick の突き合わせは companion の {@code gt0} と、この trace の {@code meta.gameTime}
     * を使う ({@code t = gameTime - gt0})。09-01-PLAN Q4 の結論: 書き手がプロセスをまたいでも
     * スキーマ定義は {@link SimCh} に一元集約し、companion を契約の例外扱いにしない。
     */
    public static final String POSE = "pose";
    /**
     * palette companion への参照チャンネル (ドキュメント上の宣言のみ)。{@link #POSE} と同じく
     * <b>本体 trace には書き込まれない</b> —— 書き手がサーバではなくクライアントであるため、
     * 実データは {@code <stamp>.pal.json}/{@code .pal.bin} という<b>別ファイル</b>に分離される
     * ({@link com.github.tartaricacid.touhoulittlemaid.sim.client.SimPaletteCodec} が読み書き、
     * ワイヤ形式 {@code palmask-deflate-v1}: 1 レコード = 変化したボーンだけの mask + 9
     * float/ボーン、K は全ゼロ基準、D は直前デコード状態からの差分、zlib deflate で圧縮)。
     * tick の突き合わせは companion の {@code gt0} と、この trace の {@code meta.gameTime}
     * を使う ({@code t = gameTime - gt0}) —— {@link #POSE} と同じ規則、同じ companion の
     * stamp/gt0/target を共有する ({@code SimPaletteTrace} が {@code SimPoseTrace} に相乗り)。
     * {@code names[]} が palette slot と Viewer 側のボーン番号を繋ぐ橋である
     * (実測 1058/1058 disagreement、{@link com.github.tartaricacid.touhoulittlemaid.sim.client.SimBonePalette}
     * が解決する)。09-01-PLAN Q4 の結論 (companion は契約の例外扱いにしない) は palette にも
     * そのまま適用される —— {@link #POSE} と同様、この定数を {@link #SCHEMA} には加えない
     * (書かれない行の形を宣言する意味が無い)。
     */
    public static final String PALETTE = "palette";

    /** {@code ch:spawn} の {@code role}: 検証の主役 (霊夢)。 */
    public static final String ROLE_REIMU = "reimu";
    /** {@code ch:spawn} の {@code role}: 弾を受ける側。 */
    public static final String ROLE_TARGET = "target";
    /** {@code ch:spawn} の {@code role}: owner 役の FakePlayer。 */
    public static final String ROLE_OPERATOR = "operator";
    /** {@code ch:spawn} の {@code role}: 追跡中の projectile。 */
    public static final String ROLE_PROJECTILE = "projectile";
    /**
     * {@code ch:spawn} の {@code role}: シナリオが置いたのでも弾でもない、
     * 戦闘の副産物 (経験値オーブ・ドロップ品など)。
     * これを {@code target} に混ぜると Analyzer の「ターゲットが受けたダメージ」が汚れる。
     */
    public static final String ROLE_OTHER = "other";

    // =========================================================================
    // スキーマ (AGENT-04) —— **形の単一の真実源**
    // =========================================================================
    //
    // 上の javadoc は人が読むためのもので、下の SCHEMA は機械が読むためのもの。
    // **食い違ったら SCHEMA 側が真実**であり、javadoc を直す。
    //
    // これを持つ理由: 解析コード (simlab/) が読むフィールドと、実機が書くフィールドが
    // 黙ってズレるのを止めるため。ズレは「表の数字が静かに 0 になる」形で現れ、
    // 気づくのが遅れる。schemaJson() を simlab/schema.json として書き出し、
    // Java 側は SimChSchemaTest が、JS 側は simlab/schema-check.mjs が両方向を見張る。

    /** 1 チャンネルが持つフィールド。{@code required} が欠けていたらトレースが壊れている。 */
    public record ChannelSpec(String channel, List<String> required, List<String> optional) {
    }

    /**
     * チャンネル → その形。**追加したフィールドをここに書かないと契約が嘘になる。**
     * 挿入順を保つ（{@link #schemaJson()} の出力を安定させるため）。
     */
    public static final Map<String, ChannelSpec> SCHEMA = buildSchema();

    private static Map<String, ChannelSpec> buildSchema() {
        Map<String, ChannelSpec> m = new LinkedHashMap<>();
        // delta/keyframe は 13-04 で追加。required は動かしていない(META の javadoc参照)。
        put(m, META, list("scenario", "seed", "arena", "duration", "gameTime"),
                list("run", "originX", "originZ", "floorY", "floorRadius", "blocks", "types", "mods",
                        "delta", "keyframe"));
        // uuid: 走っている水槽のモブを名指しで消すために足した (2026-08-23)。
        // バニラの /kill は entity のネットワーク id を取らないので、UUID が要る。
        put(m, SPAWN, list("id", "role", "type"), list("name", "maxHp", "w", "h", "uuid"));
        put(m, GONE, list("id"), list("reason"));
        // agg: SimProbe が Mob.isAggressive() を書いていたのに、ここに無かった (2026-08-24)。
        // SimChSchemaTest は SimCh と schema.json の一致しか見ないので、両方が同じ間違いで
        // 揃っている間ずっと緑だった —— 実トレースに当てる schema-check.mjs で発覚。
        put(m, POS, list("id", "x", "y", "z"), list("yaw", "pitch", "hy", "vx", "vy", "vz", "hp", "agg"));
        put(m, PHYS, list("id"), list("air", "embed", "noGrav", "onG", "somer", "vel", "y"));
        // anim: 10-01 以前から不変
        put(m, ANIM, list("id"), list("anim", "pend", "molang", "main", "off", "face"));
        // ai: sec は 10-01 で追加。section (人向け文字列) と同じ 1 つの文字列から派生する
        put(m, AI, list("id", "section"),
                list("sec", "mode", "hp", "maxHp", "target", "targetType", "dist",
                        "form", "formMode", "amuletCd", "houju", "gensou", "musouTp"));
        // proj: phase は 10-01 で spawn に追加 (発射時の技)。type は gone にも付くようになった
        put(m, PROJ, list("ev", "id"),
                list("type", "phase", "owner", "vx", "vy", "vz", "w", "h"));
        // dmg: attrib/projType/phase は 10-01〜10-02 で追加
        put(m, DMG, list("victim", "attacker", "direct", "amount", "src"),
                list("hpAfter", "attrib", "projType", "phase"));
        put(m, VIS, list("id"), list("age", "scale", "alpha", "color", "spin"));
        put(m, SOUND, list("id", "src"), list("x", "y", "z", "vol", "pitch"));
        put(m, LOG, list("msg"), list());
        put(m, TICK, list(), list());
        put(m, END, list("reason", "ticks"),
                list("actors", "projSpawned", "hitsByReimu", "dmgByReimu", "dmgToReimu", "voidRescues"));
        return Collections.unmodifiableMap(m);
    }

    /** {@code ai.sec} が必ず持つキー。ここが欠けると技別集計が黙って空になる。 */
    public static final List<String> AI_SEC_REQUIRED = list("phase");

    /** {@code dmg.attrib} の取り得る値。**この4つ以外を書かない**（根拠は上の javadoc）。 */
    public static final List<String> DMG_ATTRIB_VALUES = list("direct", "melee", "stack", "none");

    private static void put(Map<String, ChannelSpec> m, String ch, List<String> req, List<String> opt) {
        m.put(ch, new ChannelSpec(ch, req, opt));
    }

    private static List<String> list(String... a) {
        return Collections.unmodifiableList(Arrays.asList(a));
    }

    /**
     * {@link #SCHEMA} を安定した順序の JSON にする。
     * {@code simlab/schema.json} はこの出力をそのまま保存したもので、
     * {@code SimChSchemaTest} が文字列一致を見張る。
     */
    public static String schemaJson() {
        StringBuilder sb = new StringBuilder();
        sb.append("{\n");
        sb.append("  \"aiSecRequired\": ").append(arr(AI_SEC_REQUIRED)).append(",\n");
        sb.append("  \"dmgAttribValues\": ").append(arr(DMG_ATTRIB_VALUES)).append(",\n");
        sb.append("  \"channels\": {\n");
        int i = 0;
        for (ChannelSpec c : SCHEMA.values()) {
            sb.append("    \"").append(c.channel()).append("\": {\"required\": ")
                    .append(arr(c.required())).append(", \"optional\": ")
                    .append(arr(c.optional())).append("}");
            sb.append(++i < SCHEMA.size() ? ",\n" : "\n");
        }
        sb.append("  }\n}\n");
        return sb.toString();
    }

    private static String arr(List<String> a) {
        StringBuilder sb = new StringBuilder("[");
        for (int i = 0; i < a.size(); i++) {
            if (i > 0) {
                sb.append(", ");
            }
            sb.append('"').append(a.get(i)).append('"');
        }
        return sb.append(']').toString();
    }

    private SimCh() {}
}
