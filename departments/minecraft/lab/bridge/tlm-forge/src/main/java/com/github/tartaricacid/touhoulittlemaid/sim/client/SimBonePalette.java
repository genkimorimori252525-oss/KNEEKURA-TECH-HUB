package com.github.tartaricacid.touhoulittlemaid.sim.client;

import java.lang.reflect.Field;
import java.lang.reflect.Modifier;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeSet;

/**
 * spike 004 — YSM のボーン配列を「形」で見つけ、bone 名 -&gt; palette slot を解決する。
 *
 * <p>{@link SimBoneCapture} から切り出した (2026-08-25、{@link SimBoneNoise} と同じ理由:
 * Minecraft を import しない部分をテスト可能にするため。ここは反射を使うため
 * {@code SimBoneNoise} ほど純粋ではないが、{@link #classifySlot} だけは反射型を一切
 * 取らない純関数として切り離してあり、golden データからオフラインで検算できる)。
 *
 * <h3>フィールドだけを読む —— メソッドは一切呼ばない</h3>
 * {@link SimBoneCapture} の javadoc、CLAUDE.md の弾幕規約と同じ理由: 難読化された
 * フィールド/メソッド名からは getter か状態変更かを外から区別できないため、
 * {@link Field#get} 以外の呼び出しをしない。
 */
public final class SimBonePalette {

    private SimBonePalette() {}

    private static final int MAX_DEPTH = 6;
    private static final int MAX_VISITED = 40000;

    /** 見つけたもの。{@code palette} は分解しない生の float 配列。 */
    public record Found(Map<?, ?> bones, float[] palette, float[] quats, String ownerClass, String path) {}

    /**
     * 「{@code Map}(size=N) と 長さ {@code N*12} の {@code float[]} を同じ持ち主が持つ」を探す。
     * N を先に決めない —— 1058 は今のモデル固有の値であって判定の基準にしてはいけない
     * (spike 004 受け入れ条件 1)。見つからなければ {@code null}
     * (呼び出し側が fail closed で扱う)。
     */
    public static Found find(Object root) {
        Map<Object, Boolean> seen = new IdentityHashMap<>();
        Deque<Object[]> queue = new ArrayDeque<>();
        queue.add(new Object[]{root, "root", 0});
        seen.put(root, Boolean.TRUE);
        int visited = 0;

        while (!queue.isEmpty() && visited < MAX_VISITED) {
            Object[] n = queue.poll();
            Object o = n[0];
            String path = (String) n[1];
            int depth = (Integer) n[2];
            visited++;

            Map<?, ?> bones = null;
            List<float[]> floats = new ArrayList<>();
            for (Field f : declaredFields(o.getClass())) {
                if (Modifier.isStatic(f.getModifiers())) {
                    continue;
                }
                Object v = read(f, o);
                if (v instanceof Map<?, ?> m && !m.isEmpty() && bones == null) {
                    bones = m;
                } else if (v instanceof float[] fa) {
                    floats.add(fa);
                }
            }
            if (bones != null) {
                int nb = bones.size();
                float[] palette = null;
                float[] quats = null;
                for (float[] fa : floats) {
                    if (fa.length == nb * 12) {
                        palette = fa;
                    } else if (fa.length == nb * 4) {
                        quats = fa;
                    }
                }
                if (palette != null) {
                    return new Found(bones, palette, quats, o.getClass().getName(), path);
                }
            }
            if (depth >= MAX_DEPTH) {
                continue;
            }
            for (Field f : declaredFields(o.getClass())) {
                if (Modifier.isStatic(f.getModifiers())) {
                    continue;
                }
                Object v = read(f, o);
                if (v == null || v instanceof String || v instanceof Number
                        || v instanceof Boolean || v.getClass().isEnum() || v.getClass().isArray()) {
                    continue;
                }
                if (seen.put(v, Boolean.TRUE) == null) {
                    queue.add(new Object[]{v, path + "." + f.getName(), depth + 1});
                }
            }
        }
        return null;
    }

    // =========================================================================
    // bone 名 -> palette slot
    // =========================================================================

    /** {@link #slotNames} の結果。成功なら {@code names} が非 null、失敗なら {@code reason} が非 null。 */
    public record SlotResult(String[] names, String reason) {
        public boolean ok() {
            return reason == null;
        }
    }

    /** {@link #classifySlot} の 1 ボーン分の結果。 */
    public record SlotClassification(int slot, String reason) {
        public boolean ok() {
            return reason == null;
        }
    }

    /**
     * bone 名 -&gt; palette slot を、各ボーンが自分で持つ添字ペアから解決する
     * (spike 004 第3段階: 各ボーンオブジェクトが自分の palette 配列への添字を int
     * フィールドとして持つ。{@code p % 12 == 0 && q % 4 == 0 && p / 12 == q / 4} を満たす
     * 組がそのボーンの slot)。
     *
     * <p><b>fail closed。</b> map の反復順を slot 順として決して使わない —— map は
     * {@code Int2ReferenceMap} で YSM 自身のボーン id をキーにしており、その反復順に
     * palette slot との関係は無い。1 本でも解決に失敗すれば、あるいは解決した slot が
     * 過不足なく {@code 0..N-1} を覆わなければ、理由付きで失敗を返す。
     */
    public static SlotResult slotNames(Found found) {
        int boneCount = found.bones().size();
        String[] names = new String[boneCount];
        int distinctFilled = 0;

        for (Map.Entry<?, ?> e : found.bones().entrySet()) {
            Object v = e.getValue();
            if (v == null) {
                return new SlotResult(null, "key " + e.getKey() + ": bone value is null");
            }
            String name = null;
            List<Integer> ints = new ArrayList<>();
            List<float[]> arrays = new ArrayList<>();
            for (Field f : declaredFields(v.getClass())) {
                if (Modifier.isStatic(f.getModifiers())) {
                    continue;
                }
                Object fv = read(f, v);
                if (fv instanceof String s && name == null) {
                    name = s;
                } else if (fv instanceof Integer i) {
                    ints.add(i);
                } else if (fv instanceof float[] fa) {
                    arrays.add(fa);
                }
            }
            if (name == null) {
                return new SlotResult(null, "key " + e.getKey() + ": bone has no String name field");
            }

            // 1 本の bone 自身の int 集合が曖昧なら、ここで即座に失敗する
            // (rejectsAmbiguousBones: 複数の k 候補が食い違う場合)。
            SlotClassification c = classifySlot(name, ints, boneCount);
            if (!c.ok()) {
                return new SlotResult(null, "key " + e.getKey() + " ('" + name + "'): " + c.reason());
            }

            // クロスチェック: この bone が自分で持つ配列は found.palette()/quats() と
            // 参照同一 (==) でなければならない。そうでなければ、探索が見つけた object graph は
            // spike が測ったものと別物 — 黙って解決しない。
            boolean paletteRefOk = found.palette() == null;
            boolean quatsRefOk = found.quats() == null;
            for (float[] fa : arrays) {
                if (fa.length == boneCount * 12) {
                    paletteRefOk = fa == found.palette();
                } else if (fa.length == boneCount * 4) {
                    quatsRefOk = fa == found.quats();
                }
            }
            if (!paletteRefOk) {
                return new SlotResult(null, "key " + e.getKey() + " ('" + name
                        + "'): palette array is not reference-identical to Found.palette() — object graph mismatch");
            }
            if (!quatsRefOk) {
                return new SlotResult(null, "key " + e.getKey() + " ('" + name
                        + "'): quats array is not reference-identical to Found.quats() — object graph mismatch");
            }

            // 複数の bone が同じ slot へ解決した場合、ここでは即座に失敗しない —— pigeonhole
            // により「重複が1件でもあれば、必ずどこかの slot が未使用のまま残る」ので、
            // 下の最終カバレッジ判定 (distinctFilled != boneCount) が必ず捕まえる
            // (rejectsIncompleteSlotCover: 一様に「distinct 本数」で失敗を報告するため)。
            int slot = c.slot();
            if (names[slot] == null) {
                names[slot] = name;
                distinctFilled++;
            }
        }

        if (distinctFilled != boneCount) {
            return new SlotResult(null, "incomplete slot cover: " + distinctFilled + "/" + boneCount
                    + " distinct slots resolved (0.." + (boneCount - 1) + " is not covered exactly once each)");
        }
        return new SlotResult(names, null);
    }

    /**
     * 反射型を一切取らない純関数 —— golden JSON からオフラインで検算できるのはこれがあるから。
     *
     * <p>{@code ints} の中から {@code p % 12 == 0 && q % 4 == 0 && p / 12 == q / 4 &&
     * 0 &lt;= p/12 &lt; boneCount} を満たす {@code (p, q)} の組をすべて数え上げ、
     * 導出される k の集合を得る。k がちょうど1通りなら成功、0通りなら「見つからない」、
     * 2通り以上で食い違えば「曖昧」として失敗する —— どちらも silent には解決しない。
     */
    public static SlotClassification classifySlot(String name, List<Integer> ints, int boneCount) {
        TreeSet<Integer> candidates = new TreeSet<>();
        for (int i = 0; i < ints.size(); i++) {
            int p = ints.get(i);
            if (p % 12 != 0) {
                continue;
            }
            int k = p / 12;
            if (k < 0 || k >= boneCount) {
                continue;
            }
            for (int j = 0; j < ints.size(); j++) {
                if (j == i) {
                    continue;
                }
                int q = ints.get(j);
                if (q % 4 != 0) {
                    continue;
                }
                if (q / 4 == k) {
                    candidates.add(k);
                }
            }
        }
        if (candidates.isEmpty()) {
            return new SlotClassification(-1, "no valid (p,q) slot pair for '" + name + "' among ints " + ints);
        }
        if (candidates.size() > 1) {
            return new SlotClassification(-1, "ambiguous slot for '" + name + "': candidate slots " + candidates);
        }
        return new SlotClassification(candidates.first(), null);
    }

    // =========================================================================
    // 反射の配管 ({@link SimBoneCapture} から移動、内容は無改変)
    // =========================================================================

    static List<Field> declaredFields(Class<?> cls) {
        List<Field> out = new ArrayList<>();
        for (Class<?> c = cls; c != null && c != Object.class; c = c.getSuperclass()) {
            for (Field f : c.getDeclaredFields()) {
                try {
                    f.setAccessible(true);
                    out.add(f);
                } catch (Throwable ignored) {
                    // モジュールに閉じられているものは諦める
                }
            }
        }
        return out;
    }

    static Object read(Field f, Object o) {
        try {
            return f.get(o);
        } catch (Throwable t) {
            return null;
        }
    }
}
