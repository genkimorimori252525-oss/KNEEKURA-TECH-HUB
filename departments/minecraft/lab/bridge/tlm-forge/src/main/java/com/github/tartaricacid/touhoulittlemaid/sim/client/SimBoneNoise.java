package com.github.tartaricacid.touhoulittlemaid.sim.client;

/**
 * 「効いたか」判定の純関数だけを {@link SimBoneCapture} から切り出したもの
 * (2026-08-24、揺らぎのボーンごと化)。
 *
 * <p><b>Minecraft のクラスを一切 import しない</b> —— {@link SimPoseCodec} と同じ規約。
 * {@link SimBoneCapture} はクライアント限定クラスの private static な可変状態
 * ({@code baseline} / {@code noisePerBone}) に依存し<b>呼ぶ順番が意味を持つ</b>ため、
 * そこへ直接テストを当てると反射で private static を順番に叩くことになり、
 * テストが実装の内部順序に癒着する。ここへは<b>状態を渡す形</b>だけを出す。
 *
 * <p>揺らぎは 1058 本のボーンに 1 つのスカラーで代表しない —— <b>ボーンごと</b>に持つ
 * (旧実装は共有スカラーだったため、1 本の暴れたボーンが残り 1057 本の閾値を吊り上げ、
 * それらが動いても「効いていない」と誤判定していた)。
 */
public final class SimBoneNoise {

    private SimBoneNoise() {}

    /** 1 ボーンあたりの float 数 (4x3 のスキニング行列)。 */
    public static final int STRIDE = 12;

    /** 揺らぎの何倍動けば「効いた」とするか。 */
    public static final float TOOK_EFFECT_RATIO = 3.0F;

    /** 揺らぎが 0 のボーンでも閾値が 0 にならないようにする下駄。 */
    public static final float FLOOR = 1.0e-4F;

    /**
     * ボーンごとの揺らぎ配列を確保する。長さは {@code paletteFloats / STRIDE}
     * (割り切れない場合は端数を切り捨てる —— 末尾の欠けたボーンは読まない)。
     */
    public static float[] newPerBone(int paletteFloats) {
        return new float[paletteFloats / STRIDE];
    }

    /**
     * 基準標本 1 枚を {@code baseline} と突き合わせ、ボーンごとの最大差で
     * {@code noisePerBone} を <b>max 更新</b>する (下げない、複数枚の基準標本を積み重ねる用途)。
     *
     * <p>ループ境界は {@code b < noisePerBone.length} —— 現行の
     * {@code b * STRIDE < palette.length} ではなく、確保済みのボーン本数だけを読む。
     * 実データでは {@code palette.length} が {@code STRIDE} で割り切れる
     * (12696 / 12 = 1058) ので完全に同一だが、割り切れない {@code palette} が来たときに
     * 範囲外読みへ落ちないための境界。
     */
    public static void accumulate(float[] noisePerBone, float[] baseline, float[] palette) {
        for (int b = 0; b < noisePerBone.length; b++) {
            float m = noisePerBone[b];
            for (int k = 0; k < STRIDE; k++) {
                float d = Math.abs(palette[b * STRIDE + k] - baseline[b * STRIDE + k]);
                if (d > m) {
                    m = d;
                }
            }
            noisePerBone[b] = m;
        }
    }

    /**
     * {@code baseline} との差を、ボーンごとの揺らぎ {@code noisePerBone} を閾値にして判定する。
     *
     * @return {@code [変化したボーン数, 最大差]}
     */
    public static float[] takeUp(float[] baseline, float[] palette, float[] noisePerBone) {
        int changed = 0;
        float max = 0;
        for (int b = 0; b < noisePerBone.length; b++) {
            float thr = Math.max(noisePerBone[b] * TOOK_EFFECT_RATIO, FLOOR);
            float m = 0;
            for (int k = 0; k < STRIDE; k++) {
                float d = Math.abs(palette[b * STRIDE + k] - baseline[b * STRIDE + k]);
                if (d > m) {
                    m = d;
                }
            }
            if (m > thr) {
                changed++;
            }
            if (m > max) {
                max = m;
            }
        }
        return new float[]{changed, max};
    }

    /**
     * {@code noisePerBone} の中央値。{@code palette-semantics.mjs} と同じ分位規約 ——
     * 昇順コピーの index {@code floor(0.5 * (N-1))} (線形補間はしない)。
     */
    public static float median(float[] noisePerBone) {
        return quantile(noisePerBone, 0.5F);
    }

    /** {@code noisePerBone} の最大値。 */
    public static float max(float[] noisePerBone) {
        float m = 0;
        for (float v : noisePerBone) {
            if (v > m) {
                m = v;
            }
        }
        return m;
    }

    /** {@code median} と同じ分位規約の一般形。テストの p90/p99 確認にも使う。 */
    public static float quantile(float[] noisePerBone, float t) {
        float[] sorted = noisePerBone.clone();
        java.util.Arrays.sort(sorted);
        int i = (int) Math.floor(t * (sorted.length - 1));
        return sorted[i];
    }
}
