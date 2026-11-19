package com.github.tartaricacid.touhoulittlemaid.sim.tuning;

import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

/**
 * sim 実行時だけ定数を差し替える「ノブ」。既存コードの定数を
 * <pre>{@code SimTuning.d("reimu.amulet.spread_deg", SPREAD_DEG)}</pre>
 * のように通すと、シナリオ JSON の {@code overrides} から再ビルド無しで値を変えられる。
 *
 * <h3>本番の挙動を 1 ビットも変えないこと</h3>
 * {@link #apply} が呼ばれていない限り {@link #ACTIVE} は false で、
 * {@link #d}/{@link #i} は<b>引数の既定値をそのまま返す</b>。
 * sim を起動しない通常のゲームでは Map の参照すら発生しない。
 * これは {@code SimTuningGuardTest} で機械的に保証する。
 *
 * <p>{@code SimLab} を参照しないのは意図的 —— 本番コードから辿る依存を
 * このクラス 1 個で止め、sim のライフサイクルに巻き込まれないようにするため。
 */
public final class SimTuning {

    /** apply() 済みか。false の間はどの getter も即座に既定値を返す。 */
    private static volatile boolean ACTIVE = false;

    private static volatile Map<String, Double> OVERRIDES = Collections.emptyMap();

    private SimTuning() {}

    public static boolean active() {
        return ACTIVE;
    }

    /** シナリオの overrides を載せる。空 Map なら ACTIVE にしない (無駄な分岐を残さない)。 */
    public static void apply(Map<String, Double> overrides) {
        if (overrides == null || overrides.isEmpty()) {
            clear();
            return;
        }
        OVERRIDES = Collections.unmodifiableMap(new HashMap<>(overrides));
        ACTIVE = true;
    }

    public static void clear() {
        OVERRIDES = Collections.emptyMap();
        ACTIVE = false;
    }

    /** 上書きがあればその値、無ければ {@code def} をそのまま返す。 */
    public static double d(String key, double def) {
        if (!ACTIVE) {
            return def;
        }
        Double v = OVERRIDES.get(key);
        return v == null ? def : v;
    }

    /** {@link #d} の int 版。JSON の数値は double で来るので四捨五入する。 */
    public static int i(String key, int def) {
        if (!ACTIVE) {
            return def;
        }
        Double v = OVERRIDES.get(key);
        return v == null ? def : (int) Math.round(v);
    }

    /** {@link #d} の float 版。 */
    public static float f(String key, float def) {
        if (!ACTIVE) {
            return def;
        }
        Double v = OVERRIDES.get(key);
        return v == null ? def : v.floatValue();
    }

    /** 今載っているノブの一覧 (ログ/トレース用)。 */
    public static Map<String, Double> snapshot() {
        return OVERRIDES;
    }
}
