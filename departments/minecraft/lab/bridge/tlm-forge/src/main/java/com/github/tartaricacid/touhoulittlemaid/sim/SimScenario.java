package com.github.tartaricacid.touhoulittlemaid.sim;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 1 回の検証の定義。{@code simlab/scenarios/<name>.json} から読む。
 *
 * <p>ファイルが無ければ {@link #builtinSmoke()} が使われるので、
 * 何も用意しなくても {@code gradlew runSim} は動く (Phase 0 の縦串)。
 *
 * <h3>JSON 例</h3>
 * <pre>{@code
 * {
 *   "name": "amulet-vs-dummy",
 *   "seed": 20260814,
 *   "duration": 600,
 *   "arenas": 10,
 *   "spacing": 1024,
 *   "floor": { "block": "minecraft:barrier", "radius": 24, "y": 64 },
 *   "actors": [
 *     { "type": "touhou_little_maid:reimu", "role": "reimu",  "pos": [0, 65, 0] },
 *     { "type": "minecraft:zombie",         "role": "target", "pos": [0, 65, 12], "hp": 400, "noAi": true }
 *   ],
 *   "overrides": { "reimu.amulet.spread_deg": 18.0 }
 * }
 * }</pre>
 *
 * <p>{@code type} は {@code EntityType.byString()} で解決するので、
 * <b>{@code mods/} に jar を置いたそのmodのモブがそのまま書ける</b> ({@code "modid:your_mob"})。
 * 候補一覧は {@code /tlm sim entities} で吐ける。
 */
public final class SimScenario {
    private static final Gson GSON = new GsonBuilder().setLenient().create();

    /** トレースの出力先ディレクトリ名にもなる。 */
    public String name = "smoke";
    /**
     * トレース出力先の識別子。<b>現状これは run を再現可能にはしない</b> ——
     * 技抽選は各エンティティの {@code getRandom()} 由来で、そこへは種を入れていないため、
     * 同じ scenario / 同じ seed でも run 毎に結果はぶれる (実測で弾数 114〜115、
     * 与ダメージ 270〜347 の幅が出た)。
     *
     * <p>したがって<b>数値の信頼度は seed ではなく {@link #arenas} で稼ぐ</b>:
     * 同じ条件のアリーナを N 個並べて同時に走らせ、平均と散らばりを見る
     * (Analyzer が across-arenas 集計を出す)。
     */
    public long seed = 20260814L;
    /** 1 アリーナを何 tick 走らせるか (20 tick = 1 秒)。 */
    public int duration = 600;
    /** 同時に走らせるアリーナ数。1 ワールドに {@link #spacing} 間隔で並べる。 */
    public int arenas = 1;
    /** アリーナ間の距離 (ブロック)。互いの索敵半径 (40) / 弾の射程に干渉しない値にすること。 */
    public int spacing = 1024;

    /** 終了後もサーバを止めない。実クライアントを繋いで住まわせて眺めたいとき true。 */
    public boolean keepAlive = false;

    public FloorSpec floor = new FloorSpec();
    /** 床の上に置く構造物。階段・柱・段差・足場を作って移動/ジャンプを検証する。 */
    public List<BlockSpec> blocks = new ArrayList<>();
    public List<ActorSpec> actors = new ArrayList<>();
    /** {@code SimTuning} が読む定数上書き。Phase 3 で使う。 */
    public Map<String, Double> overrides = new HashMap<>();

    /**
     * 直方体 1 個ぶんのブロック充填。アリーナ原点からの相対座標で、{@code from}〜{@code to} を塗る。
     *
     * <p>階段は 1 段 = 1 個の box を並べて作る。「ブロックからブロックへ登れるか」の検証は
     * これで組んだ段差の上にターゲットを置き、霊夢が接敵のために登るかを見る。
     */
    public static final class BlockSpec {
        public String block = "minecraft:stone";
        public double[] from = {0, 65, 0};
        public double[] to = {0, 65, 0};
    }

    /** アリーナの床。void ワールドなので地上技にはこれが要る。飛行検証では {@code null} にする。 */
    public static final class FloorSpec {
        public String block = "minecraft:barrier";
        /** 床の半径 (ブロック)。バックステップ/ダッシュで場外へ落ちない広さが要る。 */
        public int radius = 24;
        public int y = 64;
        /**
         * 壁の高さ (ブロック)。{@code 0} で壁を置かない。
         *
         * <p><b>既定が 0 である理由</b>: Viewer は 2026-08-20 からチャンバーの枠
         * (床の格子と 4 面の壁) を高さ 16 で描いていたが、<b>世界の側には壁が 1 個も
         * 無かった</b> —— {@code SimArena} の {@code setBlock} は床の円盤と
         * シナリオの {@code blocks} の 2 箇所だけで、壁を置く経路が存在しなかった
         * (2026-08-25 実測)。つまり「絵にはあるが当たり判定は無い」状態で、
         * モブは端から落ち、{@code VOID RESCUE} で拾われていた。
         *
         * <p>ここを既定で 16 にすると、既に録った stairs / smoke の挙動まで変わって
         * しまう (場外へ落ちなくなる = ノックバックの結果が変わる)。だから
         * <b>既定は 0 のままにして、水槽 (tank.json) だけが明示的に 16 を指定する</b>。
         * 値は Viewer の {@code buildChamber} が描いていた高さ (H = 16) に合わせてある。
         */
        public int wallHeight = 0;
        /** 壁のブロック。既定は床と同じ barrier (見た目を邪魔しない)。 */
        public String wallBlock = "minecraft:barrier";
    }

    public static final class ActorSpec {
        /** {@code EntityType} の登録 id。例 {@code "minecraft:zombie"} / {@code "touhou_little_maid:reimu"}。 */
        public String type;
        /** {@code SimCh.ROLE_*}。{@code "reimu"} は AI トレースの対象になる。 */
        public String role = "target";
        /** アリーナ原点からの相対座標 {@code [x, y, z]}。 */
        public double[] pos = {0, 65, 0};
        /** 最大HPの上書き。null なら既定値のまま。 */
        public Double hp;
        /** true なら {@code setNoAi(true)}。動かない計測ダミーはこれ。 */
        public boolean noAi = false;
    }

    /**
     * Phase 0 の縦串用。<b>AI を無効にした高HPゾンビ</b>が計測ダミーになる ——
     * ゾンビは {@code EntityMaid.ENEMY_IDS} に載っているので、霊夢が owner もタスク設定も無しに
     * 自力で索敵してターゲットに選ぶ ({@code ReimuGroundAttackTask.findNearestEnemy})。
     * 専用のダミー EntityType を作る必要がない。
     */
    public static SimScenario builtinSmoke() {
        SimScenario s = new SimScenario();
        s.name = "smoke";
        s.duration = 600;
        s.arenas = 1;

        ActorSpec reimu = new ActorSpec();
        reimu.type = "touhou_little_maid:reimu";
        reimu.role = "reimu";
        reimu.pos = new double[]{0, 65, 0};

        ActorSpec dummy = new ActorSpec();
        dummy.type = "minecraft:zombie";
        dummy.role = "target";
        dummy.pos = new double[]{0, 65, 12};
        dummy.hp = 400.0D;
        dummy.noAi = true;

        s.actors = List.of(reimu, dummy);
        return s;
    }

    /**
     * {@code <dir>/scenarios/<name>.json} を読む。無ければ組み込みの smoke を返す
     * (「ファイルが無いから起動できない」で Phase 0 が止まらないようにする)。
     */
    public static SimScenario load(Path dir, String name) {
        Path f = dir.resolve("scenarios").resolve(name + ".json");
        if (!Files.isRegularFile(f)) {
            TouhouLittleMaid.LOGGER.info("[SIM] scenario file not found ({}), using builtin '{}'", f, name);
            return builtinSmoke();
        }
        try {
            String json = Files.readString(f, StandardCharsets.UTF_8);
            SimScenario s = GSON.fromJson(json, SimScenario.class);
            if (s == null) {
                throw new IllegalStateException("empty scenario json");
            }
            if (s.name == null || s.name.isBlank()) {
                s.name = name;
            }
            if (s.actors == null) {
                s.actors = new ArrayList<>();
            }
            // **空の水槽 (keepAlive) は actors が空なのが正常。**
            // にーくら 2026-08-20:「実験水槽に、検証したいモブを放って始めるかんじ。
            // 起動して開いたときには誰もいない感じだね」——立ち上げてから人が放つ。
            //
            // 一方 keepAlive でないシナリオは実験そのものなので、対象が居なければ設定ミス。
            // ここを一律に緩めると「actors を書き忘れた実験が、誰も居ないまま完走して
            // 空のトレースを残す」という気付きにくい嘘が生まれる。だから条件を付けて残す。
            if (s.actors.isEmpty() && !s.keepAlive) {
                throw new IllegalStateException("scenario has no actors (keepAlive でないシナリオには対象が要る)");
            }
            if (s.overrides == null) {
                s.overrides = new HashMap<>();
            }
            s.arenas = Math.max(1, s.arenas);
            s.duration = Math.max(1, s.duration);
            TouhouLittleMaid.LOGGER.info("[SIM] loaded scenario {} ({} actors, {} arenas, {} ticks)",
                    f, s.actors.size(), s.arenas, s.duration);
            return s;
        } catch (Exception e) {
            TouhouLittleMaid.LOGGER.error("[SIM] scenario load failed ({}), using builtin smoke", f, e);
            return builtinSmoke();
        }
    }
}
