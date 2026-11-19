package com.github.tartaricacid.touhoulittlemaid.sim.client;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import com.github.tartaricacid.touhoulittlemaid.entity.passive.EntityMaid;
import com.github.tartaricacid.touhoulittlemaid.geckolib3.geo.IGeoEntity;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.network.chat.Component;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.api.distmarker.OnlyIn;

import java.lang.reflect.Array;
import java.lang.reflect.Field;
import java.lang.reflect.Modifier;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.text.SimpleDateFormat;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Date;
import java.util.Deque;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * spike 004 — <b>YSM の全ボーンへ届く経路があるかを「発見する」ための探り針</b>。
 * {@code /tlmsim boneprobe} で 1 フレームだけ動く。
 *
 * <h3>解析器ではなく探り針である理由</h3>
 * YSM 2.6.2 の内部クラスは<b>難読化されている</b>（{@code o0oOoOoOOo0OOoo0O0OoO000} の形）。
 * 何がどこに在るか判らないままパーサを書くと、<b>当たっていないのに「それらしい」値を読んで
 * 通ってしまう</b>。最初の一手は「到達できたものを列挙して書き出すだけ」にする。
 * <b>値に名前を付けない。</b>
 *
 * <h3>【重要】メソッドを一切呼ばない —— フィールドだけを読む</h3>
 * 最初の実装は「引数なし public メソッド」も呼び、危険そうな名前
 * ({@code set*}/{@code remove*}/{@code tick*} 等) を除外していた。
 * <b>これは機能しない。</b> 難読化された YSM のメソッド名は
 * {@code Ooo0oOo0oo0ooO0OO0oo000o()} の形なので、getter なのか状態変更なのか
 * native 解放なのかを<b>名前からは判別できない</b>。
 * {@link Throwable} で囲んでも、呼び出しが成功して状態を変えた・native を壊した・
 * 無限に待った・JVM ごと落ちた場合は<b>元に戻せない</b>。
 *
 * <p>そこで<b>反射による呼び出しを全廃した</b>。JAR 調査では目的のモデルは
 * {@code Int2ReferenceMap} を<b>フィールドとして</b>保持しているので、
 * 第一段階の「map が在るか・何要素か」の確認に呼び出しは要らない。
 * フィールドだけで届かなかったときに初めて、JAR の SHA-256 と完全なクラス名・
 * メソッド名を固定した allowlist を作る。
 *
 * <h3>採る場所</h3>
 * {@code EntityMaidRenderer} の {@code geoRender} <b>直後</b>（{@link
 * com.github.tartaricacid.touhoulittlemaid.client.debug.ReimuBoneSampler} と同じ点）。
 * そこが「当フレームのアニメ適用後」の唯一確実な瞬間 —— 別の呼び出しで採ると
 * controller が 1 フレーム進むだけで、後の頂点との突き合わせが壊れる。
 *
 * <h3>何を根拠に始めたか</h3>
 * spike 002 の verdict は <b>REJECTED（公開APIでは全ボーンに到達できない）</b>だが、
 * 同 spike 自身が「却下したのは<b>Java 側からボーンを取り出す経路</b>であって、
 * ボーンで姿勢を表す着想ではない」と明記している。実測 (2026-08-24、
 * {@code ysm-2.6.2-forge+mc1.20.1-release.jar} / 929 クラス): 13 クラスが
 * {@code Int2ReferenceMap} を保持し、うち {@code o0oOoOoOOo0OOoo0O0OoO000} は
 * {@code ILocationModel} にも触れる。<b>「経路が無い」ではなく「まだ見ていない」だった。</b>
 */
@OnlyIn(Dist.CLIENT)
public final class SimBoneProbe {

    private SimBoneProbe() {}

    /** 次に<b>霊夢が</b>描かれた 1 フレームだけ採る。コマンドが立て、採り終えたら自分で下ろす。 */
    private static volatile boolean armed = false;

    /** フィールドを辿る深さの上限。深追いするとオブジェクトグラフ全体を歩いてしまう。 */
    private static final int MAX_DEPTH = 5;

    /** 1 つのマップから中身を覗く要素数。全部出すと 1058 行になり、形を見るには多すぎる。 */
    private static final int SAMPLE_ENTRIES = 3;

    /** 走査したオブジェクトの上限。難読化されたグラフは循環しうるので必ず止める。 */
    private static final int MAX_VISITED = 40000;

    public static String arm() {
        if (Minecraft.getInstance().level == null) {
            return "ワールドに入ってから実行すること";
        }
        armed = true;
        return "[SIM] boneprobe: 次に霊夢が描かれた 1 フレームで採取する (フィールドのみ、呼び出しはしない)";
    }

    /**
     * {@code geoRender} 直後に呼ばれる。
     *
     * <p><b>霊夢でなければ何もしない（armed も下ろさない）。</b> 別の YSM メイドが
     * 画面に居ると、そちらのモデルで探り針を消費してしまう —— 目的は霊夢のスケルトンなので、
     * 判定を通ってから初めて下ろす。
     */
    public static void sampleIfArmed(EntityMaid maid, IGeoEntity geoEntity) {
        if (!armed || maid == null || geoEntity == null) {
            return;
        }
        if (!(maid.isReimuMaid() || maid.isNamedReimu())) {
            return;
        }
        armed = false;
        try {
            Object root = geoEntity.getGeoModel();
            if (root == null) {
                say(ChatFormatting.RED, "[SIM] boneprobe: getGeoModel() が null");
                return;
            }
            List<String> out = new ArrayList<>();
            header(out, maid, root);
            walk(root, out);
            Path f = write(out);
            say(ChatFormatting.GREEN, "[SIM] boneprobe: " + out.size() + " 行 -> " + f);
            TouhouLittleMaid.LOGGER.info("[SIM] boneprobe wrote {}", f);
        } catch (Throwable t) {
            // Throwable —— 反射は Error も投げうる。描画を巻き込むより握って報告する。
            TouhouLittleMaid.LOGGER.error("[SIM] boneprobe failed", t);
            say(ChatFormatting.RED, "[SIM] boneprobe 失敗: " + t);
        }
    }

    /**
     * <b>どの個体・どのモデル・どの JAR から採ったのかを必ず書く。</b>
     * 後で結果ファイルを見比べるとき、これが無いと突き合わせられない
     * (姿勢 companion が run を名乗らずに別 run へ吸着した件と同じ轍)。
     */
    private static void header(List<String> out, EntityMaid maid, Object root) {
        out.add("# spike 004 boneprobe — 到達できたものの列挙");
        out.add("# **値の意味は推測しない。フィールドのみを読み、メソッドは一切呼ばない。**");
        out.add("#");
        out.add("# entity.uuid   = " + maid.getUUID());
        out.add("# entity.id     = " + maid.getId());
        out.add("# entity.type   = " + net.minecraft.world.entity.EntityType.getKey(maid.getType()));
        out.add("# gameTime      = " + maid.level().getGameTime());
        out.add("# tickCount     = " + maid.tickCount);
        out.add("# maid.modelId  = " + safe(maid::getModelId));
        out.add("# root class    = " + root.getClass().getName());
        out.add("# tlm.version   = " + tlmVersion());
        for (String line : modJarHashes()) {
            out.add("# " + line);
        }
        out.add("");
    }

    /**
     * root から深さ {@link #MAX_DEPTH} まで<b>フィールドだけ</b>を辿る。
     * マップと配列を見つけたら、そこで大きさと中身の型を書き出す（それが探している形）。
     */
    private static void walk(Object root, List<String> out) {
        Map<Object, Boolean> seen = new IdentityHashMap<>();
        Deque<Node> queue = new ArrayDeque<>();
        queue.add(new Node(root, "root", 0));
        seen.put(root, Boolean.TRUE);
        int visited = 0;

        while (!queue.isEmpty() && visited < MAX_VISITED) {
            Node n = queue.poll();
            visited++;
            Object o = n.value;
            Class<?> cls = o.getClass();

            // マップらしきもの: 大きさと中身を書く。**ここが探しているもの。**
            // fastutil の Int2ReferenceMap は java.util.Map を実装するのでここで捕まる。
            if (o instanceof Map<?, ?> m) {
                out.add(n.path + " : " + cls.getName() + "  Map size=" + m.size());
                describeEntries(m, out);
                continue;
            }
            if (cls.isArray()) {
                int len = Array.getLength(o);
                out.add(n.path + " : " + cls.getSimpleName() + "  length=" + len);
                if (!cls.getComponentType().isPrimitive() && len > 0) {
                    Object e0 = Array.get(o, 0);
                    if (e0 != null) {
                        out.add("    [0] -> " + e0.getClass().getName() + describeShallow(e0));
                    }
                }
                continue;
            }
            if (n.depth >= MAX_DEPTH) {
                continue;
            }

            for (Field fld : declaredFields(cls)) {
                if (Modifier.isStatic(fld.getModifiers())) {
                    continue;
                }
                Object v = readField(fld, o);
                if (v == null || isBoring(v)) {
                    continue;
                }
                String path = n.path + "." + fld.getName();
                if (interesting(v)) {
                    out.add(path + " : " + v.getClass().getName() + describeShallow(v));
                }
                if (seen.put(v, Boolean.TRUE) == null) {
                    queue.add(new Node(v, path, n.depth + 1));
                }
            }
        }
        out.add("");
        out.add("# 走査したオブジェクト: " + visited + (visited >= MAX_VISITED ? " (上限で打ち切り)" : ""));
    }

    /**
     * マップの中身を数件だけ覗く。<b>フィールドだけ</b>を読む ——
     * getter らしき名前でも、難読化されている以上それが getter である保証は無い。
     */
    private static void describeEntries(Map<?, ?> m, List<String> out) {
        int i = 0;
        for (Map.Entry<?, ?> e : m.entrySet()) {
            if (i++ >= SAMPLE_ENTRIES) {
                break;
            }
            Object v = e.getValue();
            if (v == null) {
                continue;
            }
            // key も shortValue を通す —— Int2ReferenceMap なら Integer だが、
            // 難読化されたキー型の toString が何をするかは判らない。
            out.add("    key=" + shortValue(e.getKey()) + " -> " + v.getClass().getName());
            for (Field f : declaredFields(v.getClass())) {
                if (Modifier.isStatic(f.getModifiers())) {
                    continue;
                }
                out.add("        ." + f.getName() + " : " + f.getType().getSimpleName()
                        + " = " + shortValue(readField(f, v)));
            }
        }
    }

    // =========================================================================

    private record Node(Object value, String path, int depth) {}

    private static List<Field> declaredFields(Class<?> cls) {
        List<Field> out = new ArrayList<>();
        for (Class<?> c = cls; c != null && c != Object.class; c = c.getSuperclass()) {
            for (Field f : c.getDeclaredFields()) {
                try {
                    f.setAccessible(true);
                    out.add(f);
                } catch (Throwable ignored) {
                    // モジュールに閉じられているものは諦める (握って続ける)
                }
            }
        }
        return out;
    }

    private static Object readField(Field f, Object o) {
        try {
            return f.get(o);
        } catch (Throwable t) {
            return null;
        }
    }

    /** 追っても意味の無いもの (文字列・数・列挙) は辿らない。 */
    private static boolean isBoring(Object v) {
        return v instanceof String || v instanceof Number || v instanceof Boolean
                || v instanceof Character || v.getClass().isEnum();
    }

    /** 行に書く価値があるか。マップ・配列・コレクション・YSM のクラスだけ出す。 */
    private static boolean interesting(Object v) {
        String n = v.getClass().getName();
        return v instanceof Map || v instanceof Iterable || v.getClass().isArray()
                || n.startsWith("com.elfmcys") || n.contains("Int2Reference") || n.contains("Int2Object");
    }

    private static String describeShallow(Object v) {
        if (v instanceof Map<?, ?> m) {
            return "  size=" + m.size();
        }
        if (v instanceof java.util.Collection<?> c) {
            return "  size=" + c.size();
        }
        if (v.getClass().isArray()) {
            return "  length=" + Array.getLength(v);
        }
        return "";
    }

    private static String shortValue(Object v) {
        if (v == null) {
            return "null";
        }
        // **toString も呼ばない相手が居る。** 難読化されたクラスの toString が
        // 何をするかは判らないので、既知の安全な型だけ値を出し、他は型名で済ませる。
        if (v instanceof Number || v instanceof Boolean || v instanceof Character) {
            return String.valueOf(v);
        }
        if (v instanceof String s) {
            return s.length() > 80 ? '"' + s.substring(0, 80) + "…\"" : '"' + s + '"';
        }
        if (v.getClass().getName().startsWith("org.joml.")) {
            return String.valueOf(v);   // Vector3f/Quaternionf は素の値クラス
        }
        return "<" + v.getClass().getName() + ">";
    }

    private static String safe(java.util.function.Supplier<String> s) {
        try {
            return s.get();
        } catch (Throwable t) {
            return "(取得失敗: " + t + ")";
        }
    }

    private static String tlmVersion() {
        try {
            return net.minecraftforge.fml.ModList.get()
                    .getModContainerById(TouhouLittleMaid.MOD_ID)
                    .map(c -> c.getModInfo().getVersion().toString()).orElse("unknown");
        } catch (Throwable t) {
            return "unknown";
        }
    }

    /** @see SimBoneProbeHashes — 2 箇所に同じ実装を置かない。 */
    private static List<String> modJarHashes() {
        return SimBoneProbeHashes.modJarHashes();
    }

    private static Path write(List<String> lines) throws Exception {
        Path dir = SimModelDump.outDir().resolveSibling("spike004");
        Files.createDirectories(dir);
        String stamp = new SimpleDateFormat("yyyyMMdd-HHmmss", Locale.ROOT).format(new Date());
        Path f = dir.resolve(stamp + "-boneprobe.txt");
        Files.write(f, String.join("\n", lines).getBytes(StandardCharsets.UTF_8));
        return f;
    }

    private static void say(ChatFormatting color, String msg) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player != null) {
            mc.player.displayClientMessage(Component.literal(msg).withStyle(color), false);
        }
    }
}
