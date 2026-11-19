package com.github.tartaricacid.touhoulittlemaid.sim.client;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import com.github.tartaricacid.touhoulittlemaid.capability.GeckoMaidEntityCapabilityProvider;
import com.github.tartaricacid.touhoulittlemaid.entity.passive.EntityMaid;
import com.github.tartaricacid.touhoulittlemaid.geckolib3.geo.IGeoEntity;
import com.google.gson.JsonArray;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import com.github.tartaricacid.touhoulittlemaid.client.renderer.entity.EntityMaidRenderer;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.api.distmarker.OnlyIn;

import javax.annotation.Nullable;
import java.lang.reflect.Field;
import java.lang.reflect.Modifier;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * モブの見た目を「MC 自身に描かせて」書き出す。
 *
 * <p>やっていることは 1 つだけ: 実際の {@code EntityRenderer} を呼び、
 * 頂点の行き先を {@link SimVertexRecorder} にすり替えて記録する。
 * これにより、バニラ (Java コードのモデル) も GeckoLib も YSM も<b>同じ 1 本の経路</b>で扱える。
 * Bedrock の座標規約や box UV の展開を SimLab 側で再実装する必要がない。
 *
 * <p>出力は 1 モブ 1 ファイル ({@code simlab/models/<namespace>/<path>.json})。
 * 全部を 1 ファイルにすると数十 MB になるので分けてある。
 *
 * <p><b>限界</b>: 記録できるのは「今このポーズで描かれた形」。装備・防具・目の発光などの
 * 追加レイヤは別の {@code RenderType} で流れてくる。{@link #shoot(Entity)} は
 * 実際に描画された<b>空でない全 RenderType グループを描画順に連結</b>して返す
 * (quick 260818-oq4。以前は最も頂点数の多いグループ (=本体) だけを採用し、残りを
 * 黙って捨てていた —— YSM のように複数 RenderType にまたがって描かれるモデルでは
 * パーツが欠けて見える不具合の真因だった)。{@link #renderPose} も Render Pack 移行のため
 * 空でない全グループを保持する。ただし legacy Viewer 互換の {@code frames/texture} は
 * 従来どおり最大グループを使い続け、新しい {@code renderGroups} を加算的に出力する。
 *
 * <p><b>限界その 2 — 視点依存の裏面欠落 (quick 260818-x0k)</b>: YSM native の
 * バックフェースカリングは「その瞬間に表を向いている面」しか吐かないため、
 * 1 方向からしか撮らないと裏面が<b>記録される前に</b>落ちる
 * (実測: cube あたり平均面数 3.37、描画された 508 cube のうち 377 件がちょうど 3 面で、
 * その 100% が直交 triple = 1 方向から見えている 3 面の定義そのもの)。
 * これは oq4 が直した「RenderType グループの取りこぼし」とは<b>独立した別機構</b>。
 * {@link #shoot(Entity)} は<b>同一呼び出し内で {@link #SHOT_YAWS_DEG} の各方向
 * (現在 yaw=0°/180°) を撮り</b>、180° 分を {@link SimPoseCodec#unrotateYaw}
 * (符号反転のみの厳密な逆回転) で yaw=0 の座標系へ戻して連結する。
 * <ul>
 *   <li><b>合成は同一 tick 内 (同一 {@code shoot()} 呼び出し) でしか行わない。</b>
 *       YSM の表情は 116 個の表情ボーンの出し入れで実現されており
 *       ({@code Face}/{@code Expression}/{@code OpenMouth2..14} 等。記録データ中で
 *       {@code OpenMouth2} の面が 44 件出たり消えたりしている実測あり)、別 tick の
 *       ショットを合成すると口を開けた顔と閉じた顔が重なる。</li>
 *   <li><b>方向Bが方向Aと完全一致したグループは合成から除外する</b>
 *       ({@link SimPoseCodec#mergeDirectionB})。YSM の実描画は本リポジトリ外の native
 *       ({@code geoRender()}) へ委譲されており、2 回目の render をキャッシュで潰す
 *       可能性をソースから否定できない。そのまま 180° 回して連結すると
 *       「鏡像の重複ジオメトリ」が増えるだけで絵が悪化するため
 *       (quick 260818-x0k plan-checker 指摘)。</li>
 * </ul>
 * {@link #renderPose} は単一方向のままだが、最大グループ互換値と全 RenderType group を両方返す。
 */
@OnlyIn(Dist.CLIENT)
public final class SimModelDump {

    private SimModelDump() {}

    /** RenderType 毎に記録先を分ける。本体とレイヤを取り違えないため。 */
    private static final class Sink implements MultiBufferSource {
        final Map<RenderType, SimVertexRecorder> byType = new LinkedHashMap<>();

        @Override
        public VertexConsumer getBuffer(RenderType type) {
            return this.byType.computeIfAbsent(type, t -> new SimVertexRecorder());
        }
    }

    /** 歩行サイクルを何コマに割るか。MC の歩行周期は limbSwing で約 9.4 なので 10 コマで 1 周に近い。 */
    private static final int WALK_FRAMES = 10;

    /**
     * {@link #shoot(Entity)} が 1 回の呼び出しで撮る向き (Y 軸まわり、度) の一覧
     * (quick 260818-x0k)。
     *
     * <p>YSM native のバックフェースカリングは「その瞬間に表を向いている面」しか吐かないので、
     * 1 方向だけでは裏面が記録前に落ちる。向きを変えて撮り直し、
     * {@link SimPoseCodec#unrotateYaw} で元の座標系へ戻して連結することで埋める。
     *
     * <p><b>90°/270° へ拡張する場合はここへ角度を足すだけでよい</b> ——
     * {@link SimPoseCodec#unrotateYaw} が既に一般式 (三角関数) パスを持っている。
     * ただし 0°/180° は符号反転のみの厳密パスを通るのに対し、拡張角度は丸め誤差が入る。
     */
    private static final float[] SHOT_YAWS_DEG = {0F, 180F};

    /**
     * {@link #shoot(Entity)} が {@code rawByTypeA} を「先頭の向きで埋めてから後続の向きと
     * 突き合わせる」構造になっているため、<b>先頭は必ず 0° (回転なし = 方向A) でなければ
     * ならない</b>。角度を足すとき順序を崩すと、比較相手の無いまま逆回転された配列が
     * 方向Aとして扱われ、沈黙して壊れる (quick 260818-x0k code-review WR-02)。
     * クラスロード時に落として、その事故をコンパイル後最初の1回で顕在化させる。
     */
    static {
        if (SHOT_YAWS_DEG.length == 0 || SHOT_YAWS_DEG[0] != 0F) {
            throw new IllegalStateException(
                    "SHOT_YAWS_DEG の先頭は 0F (方向A) でなければならない: "
                            + java.util.Arrays.toString(SHOT_YAWS_DEG));
        }
    }

    /**
     * 1 回の {@link #shoot(Entity)} で {@code Shot.collisionTypes} に載せる衝突グループ名の上限。
     * 呼び出し側が初回に 1 行出すためのサンプルなので、全件は要らない。
     */
    private static final int MAX_COLLISION_TYPES = 8;

    /**
     * 記録するポーズの一覧。<b>アニメの中身は書かない</b> ——
     * {@code setupAnim} に渡る入力 (歩行位相 / 歩行量 / 交戦態勢) を変えるだけで、
     * 姿勢の計算は MC が行う。だからモブごとの分岐が要らず、
     * ゾンビの腕上げもクモの脚もスケルトンの構えも同じ 1 本の経路で出てくる。
     */
    private record Pose(String name, int walk, boolean aggressive) {}

    private static List<Pose> poses() {
        List<Pose> list = new ArrayList<>();
        for (boolean agg : new boolean[]{false, true}) {
            String p = agg ? "aggro_" : "";
            list.add(new Pose(p + "idle", -1, agg));
            for (int i = 0; i < WALK_FRAMES; i++) {
                list.add(new Pose(p + "walk" + i, i, agg));
            }
        }
        return list;
    }

    /**
     * 歩行位相を進める。{@code update(1,1)} は speed を 1 にして position を 1 進めるので、
     * k 回呼べば limbSwing=k / limbSwingAmount=1 (フルスイング) になる。
     */
    private static void applyPose(Entity entity, Pose pose) {
        if (entity instanceof LivingEntity le) {
            le.walkAnimation.setSpeed(0.0F);
            if (pose.walk() >= 0) {
                for (int i = 0; i <= pose.walk(); i++) {
                    le.walkAnimation.update(1.0F, 1.0F);
                }
            }
        }
        if (entity instanceof net.minecraft.world.entity.Mob mob) {
            mob.setAggressive(pose.aggressive());
        }
    }

    /**
     * 実際に使われたテクスチャを {@code RenderType} から取り出す。
     *
     * <p>外側のレンダラの {@code getTextureLocation()} を信じてはいけない ——
     * {@code EntityMaidRenderer} は YSM 経路に入ると内部で YSM のレンダラへ委譲して early return するので、
     * 外側が返すのは TLM 側のテクスチャのままになる
     * (実際それで霊夢が「YSM の形 + TLM のテクスチャ」で記録されていた)。
     * 頂点が流れ込んだ {@code RenderType} が持っているものが真。
     *
     * <p>{@code TextureStateShard} のフィールドは private なので、
     * 名前に依存せず「到達可能な ResourceLocation を1つ探す」形で取る。
     */
    @Nullable
    private static ResourceLocation textureOf(Object o, int depth, java.util.Set<Object> seen) {
        if (o == null || depth > 4) {
            return null;
        }
        if (o instanceof ResourceLocation rl) {
            return rl;
        }
        if (o instanceof java.util.Optional<?> op) {
            return op.map(x -> textureOf(x, depth + 1, seen)).orElse(null);
        }
        Class<?> c = o.getClass();
        if (c.getName().startsWith("java.") || !seen.add(o)) {
            return null;
        }
        while (c != null && c != Object.class) {
            for (java.lang.reflect.Field f : c.getDeclaredFields()) {
                if (java.lang.reflect.Modifier.isStatic(f.getModifiers())) {
                    continue;
                }
                try {
                    f.setAccessible(true);
                    ResourceLocation r = textureOf(f.get(o), depth + 1, seen);
                    if (r != null) {
                        return r;
                    }
                } catch (Throwable ignored) {
                    // 触れないフィールドは飛ばす
                }
            }
            c = c.getSuperclass();
        }
        return null;
    }

    /**
     * 記録した見た目に対応するテクスチャ id を決める。
     *
     * <p>順に:
     * <ol>
     *   <li><b>YSM のメイド</b> — {@code getYsmModelTexture()} が持つ名前 (例 {@code texture2}) から
     *       パック内の {@code textures/<name>.png} を指す。外側のレンダラは YSM 経路でも
     *       TLM 側のテクスチャを返すため、ここを最優先しないと
     *       「YSM の形 + 別のテクスチャ」になる (実際そのせいで真っ白になった。
     *       TLM 側の {@code hakurei_reimu.png} は mod の assets に存在せず解決できない)。</li>
     *   <li>頂点が流れ込んだ {@code RenderType} が持つもの</li>
     *   <li>レンダラの {@code getTextureLocation}</li>
     * </ol>
     */
    @Nullable
    @SuppressWarnings("rawtypes")
    static String resolveTextureId(Entity entity, @Nullable RenderType type, @Nullable EntityRenderer renderer) {
        if (entity instanceof com.github.tartaricacid.touhoulittlemaid.entity.passive.EntityMaid maid) {
            try {
                if (maid.isYsmModel()) {
                    String t = maid.getYsmModelTexture();
                    if (t != null && !t.isBlank()) {
                        String name = t.endsWith(".png") ? t : t + ".png";
                        return "ysm:textures/" + name;
                    }
                }
            } catch (Throwable ignored) {
                // YSM 未使用のメイドなら下へ落ちる
            }
        }
        if (type != null) {
            try {
                ResourceLocation r = textureOf(type, 0,
                        java.util.Collections.newSetFromMap(new java.util.IdentityHashMap<>()));
                if (r != null) {
                    return r.toString();
                }
            } catch (Throwable ignored) {
                // 取れなければ下へ
            }
        }
        if (renderer != null) {
            try {
                ResourceLocation r = renderer.getTextureLocation(entity);
                if (r != null) {
                    return r.toString();
                }
            } catch (Throwable ignored) {
                // テクスチャなしのレンダラもある
            }
        }
        return null;
    }

    /** 1 回の pose render で実測した 1 RenderType group。挿入順が source draw order。 */
    private record RecordedGroup(SimVertexRecorder rec, @Nullable RenderType type) {}

    /**
     * legacy Viewer 互換の最大グループ ({@code rec/type}) と、Render Pack compiler 用の
     * 空でない全グループ ({@code groups}) を同時に保持する。
     */
    private record Recorded(SimVertexRecorder rec, @Nullable RenderType type, List<RecordedGroup> groups) {}

    /**
     * 1 つの RenderType グループ (quick 260818-oq4)。{@code verts} は<b>頂点数</b>であって
     * float 数ではない ({@code lens} / {@code glens} と単位を揃える)。{@code texture} は
     * このグループが解決したテクスチャ id ({@code null} もありうる)。{@code type} は
     * {@code RenderType} の文字列表現で、ログにそのまま出して「何を捨てていたのか」を
     * 人が読めるようにするためのもの。
     *
     * <p>{@code yawDeg} は<b>このグループを撮った向き</b> ({@link #SHOT_YAWS_DEG} のどれか。
     * quick 260818-x0k)。{@code 0} = 方向A、それ以外 = 方向B。呼び出し側
     * ({@code SimPoseTrace}) が dirA/dirB の verts/quads を突き合わせてログへ出すために持つ
     * —— <b>「正しく回った」と「壊れた重複が足されただけ」を実機で区別する唯一の識別子</b>。
     */
    public record Group(int verts, int quads, @Nullable String texture, String type, float yawDeg) {}

    /**
     * 「今この瞬間の見た目」1 枚。{@link SimPoseDump} が姿勢ごとに集める単位。
     *
     * <p>{@code verts} は<b>空でない全グループを {@code Sink.byType} の挿入順
     * (=実機の描画順) に連結</b>した配列 (quick 260818-oq4)。{@code texture} は
     * <b>最大グループ (quad 数最大) のテクスチャ</b> (旧 Viewer 互換のためこの意味を保つ、
     * {@code header.texture} に対応)。{@code quads} は<b>全グループの合計</b>。
     * {@code groups} は描画順のグループ一覧 (不変リスト。方向Aの全グループ →
     * 方向Bの全グループ の順、quick 260818-x0k)。
     *
     * <p>{@code collisionsDropped} は<b>方向Bの生配列が方向Aと完全一致したため合成から
     * 除外したグループ数</b> (quick 260818-x0k)。{@code 0} なら衝突なし。
     * {@code 0} より大きければ「向きを変えても YSM が同じ結果を返している」＝多方向撮影が
     * この経路では効いていない、という直接の証拠になる。{@code shoot()} 自体は状態を
     * 持たないユーティリティのままなので、「初回だけ人へ知らせる」といったゲートは
     * 呼び出し側 ({@code SimPoseTrace}) の責務。
     */
    public record Shot(float[] verts, @Nullable String texture, int quads, List<Group> groups,
                       int collisionsDropped, List<String> collisionTypes) {}

    /**
     * 実在するエンティティを<b>今の状態のまま</b> 1 枚録る。
     *
     * <p>ポーズは何も触らない —— YSM の molang で外から姿勢を作ってから呼ぶ用。
     * 向きだけは記録の都合で {@link #SHOT_YAWS_DEG} の各値へ倒し、
     * <b>全方向を撮り終わってから</b> {@code finally} で必ず元へ戻す
     * (画面上の個体を借りるため。復元は {@code finally} の 1 箇所に集約したままにする ——
     * 撮影ループの内側で個別に復元すると 2 枚目を撮る前に姿勢が戻ってしまい壊れる)。
     */
    @Nullable
    @SuppressWarnings({"unchecked", "rawtypes"})
    public static Shot shoot(Entity entity) {
        Minecraft mc = Minecraft.getInstance();
        if (entity == null || mc.level == null) {
            return null;
        }
        final float oy = entity.getYRot(), ox = entity.getXRot();
        final float oyo = entity.yRotO, oxo = entity.xRotO;
        final float obody = entity instanceof LivingEntity l ? l.yBodyRot : 0;
        final float ohead = entity instanceof LivingEntity l2 ? l2.yHeadRot : 0;
        try {
            // レンダラの取得は向きに依存しないので、撮影ループより前に 1 回だけ行う。
            EntityRenderer renderer = mc.getEntityRenderDispatcher().getRenderer(entity);
            if (renderer == null) {
                return null;
            }

            List<Group> parts = new ArrayList<>();
            List<float[]> arrays = new ArrayList<>();
            // 方向A (yaw=0) の「回転前の生配列」を RenderType 毎に控える。
            // 方向Bの衝突検出 (SimPoseCodec.mergeDirectionB) の比較相手になる。
            Map<RenderType, float[]> rawByTypeA = new LinkedHashMap<>();
            int collisionsDropped = 0;
            // 衝突したグループ名のサンプル。ログは出さずにここへ溜め、呼び出し側が初回だけ出す。
            List<String> collisionTypes = new ArrayList<>();
            int totalFloats = 0;
            int totalQuads = 0;
            SimVertexRecorder maxRec = null;
            String maxTexture = null;

            for (float yaw : SHOT_YAWS_DEG) {
                if (yaw != 0F && !(entity instanceof LivingEntity)) {
                    // yBodyRot/yHeadRot を持たない相手は 2 枚目を撮っても 1 枚目と同一に
                    // なるだけなので、無駄な重複データを作らずに 1 方向で終える。
                    continue;
                }
                // 向きに関わる 6 フィールドを全部同じ値へ揃える (quick 260818-x0k)。
                // EntityMaidRenderer は YSM 分岐で super.render() を呼ばず
                // ysmMaidRenderer.geoRender() へ委譲するため、バニラ LivingEntityRenderer が
                // yBodyRot を読む前提はここでは保証されない。setYRot / yBodyRot / yHeadRot の
                // どれを YSM 側が実際に読んでいてもこの 2 方向撮影が効くよう、全部揃える
                // (plan-checker 指摘の WARNING 対応)。head-body デルタは常に 0 のまま
                // = 同じポーズで、向きだけが変わる。
                entity.setYRot(yaw); entity.setXRot(0);
                entity.yRotO = yaw; entity.xRotO = 0;
                if (entity instanceof LivingEntity le) {
                    le.yBodyRot = yaw; le.yBodyRotO = yaw;
                    le.yHeadRot = yaw; le.yHeadRotO = yaw;
                }

                Sink sink = new Sink();
                renderer.render(entity, 0.0F, 1.0F, new PoseStack(), sink, 0x00F000F0);

                // 空でない全グループを Sink.byType の挿入順 (=実機の描画順) にたどり、
                // 並べ替え・再グループ化・重複除去を一切せずに連結する (quick 260818-oq4)。
                // 半透明の合成は描画順に依存するため、ここで順序を崩すと絵が壊れる。
                // この積み上げが方向ループの内側にあるので、自然に
                // 「方向Aの全グループ → 方向Bの全グループ」の順になり、方向をまたいで
                // 同じ RenderType が 1 グループへ畳まれることもない (方向ごとに新しい Sink)。
                for (Map.Entry<RenderType, SimVertexRecorder> e : sink.byType.entrySet()) {
                    SimVertexRecorder r = e.getValue();
                    if (r.isEmpty()) {
                        continue;
                    }
                    float[] rawArr = r.toArray();   // まだ回転していない生配列
                    float[] arr;
                    if (yaw == 0F) {
                        rawByTypeA.put(e.getKey(), rawArr);
                        arr = rawArr;               // 方向Aは従来どおり回転なし
                    } else {
                        float[] rawA = rawByTypeA.get(e.getKey());
                        if (rawA == null) {
                            // 方向Bにだけ現れた RenderType —— 比較相手が無く衝突判定できない。
                            arr = SimPoseCodec.unrotateYaw(rawArr, SimVertexRecorder.STRIDE, yaw);
                        } else {
                            arr = SimPoseCodec.mergeDirectionB(rawA, rawArr, SimVertexRecorder.STRIDE, yaw);
                            if (arr == null) {
                                // 方向Bが方向Aの複製 = YSM が 2 枚目の render をキャッシュで
                                // 潰している疑い。そのまま 180° 回して連結すると「鏡像の重複
                                // ジオメトリ」が増えて絵が悪化するので、このグループは捨てる。
                                collisionsDropped++;
                                // ここではログを出さず記録だけする (quick 260818-x0k code-review WR-01)。
                                // 衝突は決定論的に毎 tick・毎グループ起こりうるので、無条件に warn を
                                // 出すと 45 秒の記録で数百行のスパムになり、まさにその衝突を診断する
                                // ために読みたい latest.log を自分で埋めてしまう。Shot の javadoc の
                                // とおり「初回だけ人へ知らせる」ゲートは呼び出し側の責務。
                                if (collisionTypes.size() < MAX_COLLISION_TYPES) {
                                    String label = "yaw=" + yaw + " " + e.getKey();
                                    if (!collisionTypes.contains(label)) {
                                        collisionTypes.add(label);
                                    }
                                }
                                continue;
                            }
                        }
                    }
                    int verts = SimVertexRecorder.STRIDE > 0 ? arr.length / SimVertexRecorder.STRIDE : 0;
                    String texId = resolveTextureId(entity, e.getKey(), renderer);
                    parts.add(new Group(verts, r.quadCount(), texId, String.valueOf(e.getKey()), yaw));
                    arrays.add(arr);
                    totalFloats += arr.length;
                    totalQuads += r.quadCount();
                    if (maxRec == null || r.quadCount() > maxRec.quadCount()) {
                        maxRec = r;
                        maxTexture = texId;
                    }
                }
                // ここで向きを戻さない。全方向を撮り終わってから finally で 1 回だけ戻す。
            }
            if (parts.isEmpty()) {
                return null;
            }
            float[] merged = new float[totalFloats];
            int off = 0;
            for (float[] arr : arrays) {
                System.arraycopy(arr, 0, merged, off, arr.length);
                off += arr.length;
            }
            return new Shot(merged, maxTexture, totalQuads, List.copyOf(parts),
                    collisionsDropped, List.copyOf(collisionTypes));
        } catch (Throwable t) {
            return null;
        } finally {
            try {
                entity.setYRot(oy); entity.setXRot(ox);
                entity.yRotO = oyo; entity.xRotO = oxo;
                if (entity instanceof LivingEntity le) {
                    le.yBodyRot = obody; le.yBodyRotO = obody;
                    le.yHeadRot = ohead; le.yHeadRotO = ohead;
                }
            } catch (Exception ignored) {
                // 戻せなくても次 tick で本人が上書きする
            }
        }
    }

    /**
     * 1 ポーズ描画し、空でない全 RenderType group を source draw order のまま保持する。
     *
     * <p>{@code rec/type} は既存 {@code frames/texture} と {@link #solveHead} を壊さないため
     * 従来どおり最大 quad 数のグループを指す。新しい Render Pack capture は
     * {@code groups} を使う。つまり legacy の意味は変更せず、情報損失だけを止める。
     */
    @Nullable
    @SuppressWarnings({"unchecked", "rawtypes"})
    private static Recorded renderPose(EntityRenderer renderer, Entity entity, Pose pose) {
        try {
            applyPose(entity, pose);
            Sink sink = new Sink();
            renderer.render(entity, 0.0F, 1.0F, new PoseStack(), sink, 0x00F000F0);
            SimVertexRecorder best = null;
            RenderType bestType = null;
            List<RecordedGroup> groups = new ArrayList<>();
            for (Map.Entry<RenderType, SimVertexRecorder> e : sink.byType.entrySet()) {
                SimVertexRecorder r = e.getValue();
                if (r.isEmpty()) {
                    continue;
                }
                groups.add(new RecordedGroup(r, e.getKey()));
                if (best == null || r.quadCount() > best.quadCount()) {
                    best = r;
                    bestType = e.getKey();
                }
            }
            return best == null ? null : new Recorded(best, bestType, List.copyOf(groups));
        } catch (Throwable t) {
            return null;
        }
    }

    /**
     * Render Pack向けの stable bone slot/name を、既存の fail-closed runtime palette probeから取得する。
     *
     * <p>ここで証明できるのは slot と name だけ。parent relation / bind matrix / inverse bind matrix は
     * 取得根拠が無いので UNKNOWN のまま残し、identity や推測parentを作らない。
     */
    private static JsonObject captureSkeleton(Entity entity) {
        JsonObject out = new JsonObject();
        out.addProperty("schema", "kneekura.capture-skeleton");
        out.addProperty("schemaVersion", 1);
        out.addProperty("source", "runtimeBonePaletteSlotMap");
        JsonArray bones = new JsonArray();
        out.add("bones", bones);

        if (!(entity instanceof EntityMaid maid)) {
            out.addProperty("authority", "UNKNOWN");
            out.addProperty("reason", "entity is not EntityMaid; no YSM runtime root was probed");
            return out;
        }

        try {
            SimYsmRuntimeRoot.Result root = SimYsmRuntimeRoot.findForMaid(maid);
            if (!root.ok() || root.root() == null) {
                out.addProperty("authority", "UNKNOWN");
                out.addProperty("reason", root.message());
                return out;
            }
            SimBonePalette.Found found = SimBonePalette.find(root.root());
            if (found == null) {
                out.addProperty("authority", "UNKNOWN");
                out.addProperty("reason", "SimBonePalette.find found no Map(N)+float[N*12] palette owner");
                return out;
            }
            SimBonePalette.SlotResult slots = SimBonePalette.slotNames(found);
            if (!slots.ok() || slots.names() == null) {
                out.addProperty("authority", "UNKNOWN");
                out.addProperty("reason", slots.reason());
                return out;
            }

            String[] names = slots.names();
            for (int slot = 0; slot < names.length; slot++) {
                JsonObject bone = new JsonObject();
                bone.addProperty("slot", slot);
                bone.addProperty("name", names[slot]);
                bone.add("parentSlot", JsonNull.INSTANCE);
                bone.addProperty("parentSlotAuthority", "UNKNOWN");
                bone.add("bindMatrix", JsonNull.INSTANCE);
                bone.addProperty("bindMatrixAuthority", "UNKNOWN");
                bone.add("inverseBindMatrix", JsonNull.INSTANCE);
                bone.addProperty("inverseBindMatrixAuthority", "UNKNOWN");
                bones.add(bone);
            }
            out.addProperty("authority", "measuredSlotMap");
            out.addProperty("ownerClass", found.ownerClass());
            out.addProperty("objectPath", found.path());
            out.addProperty("runtimeRootRoute", root.route());
            out.addProperty("boneCount", names.length);
            return out;
        } catch (Throwable t) {
            out.addProperty("authority", "UNKNOWN");
            out.addProperty("reason", "skeleton capture failed: " + t.getClass().getSimpleName());
            return out;
        }
    }

    /** 頭の向きを与えて描く用。{@code LivingEntityRenderer} は yHeadRot-yBodyRot と xRot を使う。 */
    private static void setHead(Entity e, float yaw, float pitch) {
        e.setXRot(pitch);
        e.xRotO = pitch;
        if (e instanceof LivingEntity le) {
            le.yHeadRot = yaw; le.yHeadRotO = yaw;
            le.yBodyRot = 0; le.yBodyRotO = 0;
        }
    }

    /**
     * 「どの頂点が頭か」と「その回転中心」を割り出す。
     *
     * <p>モデルの構造を知らなくてよい: 頭を {@code probe} 度だけ振ってもう一度描き、
     * <b>動いた頂点が頭</b>。さらにその動き方は回転中心まわりの剛体回転なので、
     * 未知数 2 つの線形方程式が頂点ごとに 2 本立ち、最小二乗で中心が解ける。
     *
     * <p>こうしておけば Viewer 側で頭を<b>連続的に</b>向けられる
     * (角度を離散ポーズとして焼くとデータが角度の数だけ倍になる)。
     *
     * @return {@code [maskRanges, pivotX, pivotY, pivotZ]}、割り出せなければ null
     */
    @Nullable
    @SuppressWarnings({"unchecked", "rawtypes"})
    private static JsonObject solveHead(EntityRenderer renderer, Entity entity, float[] base) {
        final float probe = 30.0F;
        setHead(entity, probe, 0.0F);
        Recorded ry = renderPose(renderer, entity, new Pose("probe", -1, false));
        setHead(entity, 0.0F, probe);
        Recorded rp = renderPose(renderer, entity, new Pose("probe", -1, false));
        setHead(entity, 0.0F, 0.0F);
        if (ry == null || rp == null) {
            return null;
        }
        float[] vy = ry.rec().toArray(), vp = rp.rec().toArray();
        if (vy.length != base.length || vp.length != base.length) {
            return null;
        }

        int n = base.length / SimVertexRecorder.STRIDE;
        boolean[] head = new boolean[n];
        int count = 0;
        for (int i = 0; i < n; i++) {
            int b = i * SimVertexRecorder.STRIDE;
            double d = Math.abs(vy[b] - base[b]) + Math.abs(vy[b+1] - base[b+1]) + Math.abs(vy[b+2] - base[b+2]);
            if (d > 1.0e-4) { head[i] = true; count++; }
        }
        if (count == 0) {
            return null;
        }

        // yaw: Y 軸まわりの回転から (px, pz) を最小二乗で解く
        double th = -probe * Math.PI / 180.0;   // モデル空間は Y が下向きなので符号が反転する
        double c = Math.cos(th), s = Math.sin(th);
        double a11 = 0, a12 = 0, a22 = 0, b1 = 0, b2 = 0;
        // 各頂点から: (1-c)*px + s*pz = x1 - c*x0 + s*z0
        //             -s*px + (1-c)*pz = z1 - s*x0 - c*z0
        for (int i = 0; i < n; i++) {
            if (!head[i]) continue;
            int b = i * SimVertexRecorder.STRIDE;
            double x0 = base[b], z0 = base[b+2], x1 = vy[b], z1 = vy[b+2];
            double r1 = x1 - c*x0 + s*z0, r2 = z1 - s*x0 - c*z0;
            a11 += (1-c)*(1-c) + s*s;
            a12 += (1-c)*s + (-s)*(1-c);
            a22 += s*s + (1-c)*(1-c);
            b1 += (1-c)*r1 + (-s)*r2;
            b2 += s*r1 + (1-c)*r2;
        }
        double det = a11*a22 - a12*a12;
        if (Math.abs(det) < 1.0e-9) {
            return null;
        }
        double px = (b1*a22 - b2*a12) / det;
        double pz = (a11*b2 - a12*b1) / det;

        // pitch: X 軸まわりの回転から py を解く (pz は上で得たものを使う)
        double a = 0, bb = 0;
        for (int i = 0; i < n; i++) {
            if (!head[i]) continue;
            int b = i * SimVertexRecorder.STRIDE;
            double y0 = base[b+1], z0 = base[b+2], y1 = vp[b+1];
            // y1 = py + c*(y0-py) - s*(z0-pz)  ->  (1-c)*py = y1 - c*y0 + s*(z0-pz)
            a += (1-c)*(1-c);
            bb += (1-c) * (y1 - c*y0 + s*(z0 - pz));
        }
        double py = Math.abs(a) < 1.0e-9 ? 0 : bb / a;

        // --- 割り出した結果が妥当かを検算する ---
        // YSM のように「頭が単純な剛体回転ではない」モデルでは、probe に対して体の大半が動き、
        // 最小二乗が意味のない解を返す (実測: 霊夢で頭頂点4050 / 中心 y=3.296、身長 1.87 の遥か上)。
        // そのまま使うと Viewer で頭が変な軸で回るので、破綻を検出したら頭情報は載せない。
        double ratio = count / (double) n;
        double minY = Double.MAX_VALUE, maxY = -Double.MAX_VALUE;
        for (int i = 0; i < n; i++) {
            float y = base[i * SimVertexRecorder.STRIDE + 1];
            minY = Math.min(minY, y);
            maxY = Math.max(maxY, y);
        }
        if (ratio > 0.5 || py < minY - 0.5 || py > maxY + 0.5) {
            TouhouLittleMaid.LOGGER.info("[SIM] head solve rejected (verts {}%, pivotY {} outside {}..{})",
                    Math.round(ratio * 100), String.format(java.util.Locale.ROOT, "%.2f", py),
                    String.format(java.util.Locale.ROOT, "%.2f", minY),
                    String.format(java.util.Locale.ROOT, "%.2f", maxY));
            return null;
        }

        // マスクは連続した区間としてまとめる (頂点ごとに 0/1 を並べると無駄に大きい)
        JsonArray ranges = new JsonArray();
        int start = -1;
        for (int i = 0; i <= n; i++) {
            boolean h = i < n && head[i];
            if (h && start < 0) start = i;
            if (!h && start >= 0) {
                JsonArray r = new JsonArray();
                r.add(start); r.add(i);
                ranges.add(r);
                start = -1;
            }
        }
        JsonObject o = new JsonObject();
        o.add("ranges", ranges);
        JsonArray piv = new JsonArray();
        piv.add(Math.round(px * 10000.0) / 10000.0);
        piv.add(Math.round(py * 10000.0) / 10000.0);
        piv.add(Math.round(pz * 10000.0) / 10000.0);
        o.add("pivot", piv);
        o.addProperty("verts", count);
        return o;
    }

    private static boolean same(float[] a, float[] b) {
        if (a.length != b.length) {
            return false;
        }
        for (int i = 0; i < a.length; i++) {
            if (Math.abs(a[i] - b[i]) > 1.0e-4F) {
                return false;
            }
        }
        return true;
    }

    /**
     * 1 体をポーズ集つきで記録する。描画に失敗する型 (プレイヤー前提のもの等) は null を返す。
     *
     * <p><b>同じ形になったポーズは 1 本に畳む。</b> 歩行アニメを持たないモブ (スライム等) は
     * 全コマが同一になるので 1 本に、腕上げを持たないモブは交戦態勢の変種が生まれない。
     * これでデータ量は「本当に姿勢が変わるモブ」にだけ増える。
     */
    @Nullable
    @SuppressWarnings({"unchecked", "rawtypes"})
    private static JsonObject dumpOne(EntityType<?> type, @Nullable Entity liveEntity) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null) {
            return null;
        }
        // 実在する個体があればそれを優先する (ワードローブで着替えた状態など、
        // config の既定値と違う見た目になっている場合はそちらが正しいため)。
        final boolean borrowed = liveEntity != null;
        Entity entity = liveEntity;
        if (entity == null) {
            try {
                entity = type.create(mc.level);
            } catch (Exception e) {
                return null;
            }
        }
        if (entity == null) {
            return null;
        }

        // 「湧いたときに決まる見た目」を、湧かせずに再現する。
        //
        // EntityMaidRenderer の分岐は  isYsmModel() && ysmMaidRenderer != null  だけで、
        // モデル ID / テクスチャは getYsmModelId() / getYsmModelTexture() から読まれる。
        // それらを config から入れているのが applyConfigDefaults() で、通常は finalizeSpawn 経由で呼ばれる。
        // 新規生成した個体はそこを通っていないので isYsmModel() が false のままになり、
        // TLM の代替 Bedrock モデルが記録されてしまう (実際それで霊夢を取りこぼした)。
        //
        // ここで直接呼ぶことで、手で召喚しておく必要がなくなる。
        if (!borrowed && entity instanceof com.github.tartaricacid.touhoulittlemaid.entity.passive.reimu.EntityReimu r) {
            try {
                r.applyConfigDefaults();
            } catch (Throwable ignored) {
                // config が未設定なら代替モデルのまま録る (それが実機の見た目でもある)
            }
        }
        // 借り物は元の姿勢へ戻す (画面上の個体をいじるので)
        final float oy = entity.getYRot(), ox = entity.getXRot();
        final float oyo = entity.yRotO, oxo = entity.xRotO;
        final float obody = entity instanceof LivingEntity l ? l.yBodyRot : 0;
        final float ohead = entity instanceof LivingEntity l2 ? l2.yHeadRot : 0;
        try {
            // 向きは 0 に固定して記録する。実際の向きは Viewer 側で回す。
            entity.setYRot(0);
            entity.setXRot(0);
            entity.yRotO = 0;
            entity.xRotO = 0;
            if (entity instanceof LivingEntity le) {
                le.yBodyRot = 0; le.yBodyRotO = 0;
                le.yHeadRot = 0; le.yHeadRotO = 0;
            }
            EntityRenderer renderer = mc.getEntityRenderDispatcher().getRenderer(entity);
            if (renderer == null) {
                return null;
            }

            List<float[]> frames = new ArrayList<>();
            JsonObject poseIndex = new JsonObject();
            JsonObject renderGroupsByPose = new JsonObject();
            int quads = 0;
            RenderType usedType = null;
            for (Pose pose : poses()) {
                Recorded rr = renderPose(renderer, entity, pose);
                if (rr == null || rr.rec().isEmpty()) {
                    continue;
                }
                if (usedType == null) {
                    usedType = rr.type();
                }
                SimVertexRecorder rec = rr.rec();
                float[] v = rec.toArray();
                int slot = -1;
                for (int i = 0; i < frames.size(); i++) {
                    if (same(frames.get(i), v)) { slot = i; break; }
                }
                if (slot < 0) {
                    slot = frames.size();
                    frames.add(v);
                    quads = Math.max(quads, rec.quadCount());
                }
                poseIndex.addProperty(pose.name(), slot);

                // Render Pack 移行用: legacy の最大group frameとは別に、全groupを描画順で保持する。
                // MaterialIRの意味はここでは推測せず、texture + RenderType provenanceだけを記録する。
                JsonArray poseGroups = new JsonArray();
                int groupOrder = 0;
                for (RecordedGroup group : rr.groups()) {
                    SimVertexRecorder groupRec = group.rec();
                    float[] groupVerts = groupRec.toArray();
                    String sourceRenderType = String.valueOf(group.type());
                    JsonObject gj = new JsonObject();
                    gj.addProperty("groupId", sourceRenderType);
                    gj.addProperty("order", groupOrder++);
                    gj.addProperty("quads", groupRec.quadCount());
                    gj.addProperty("vertexCount",
                            SimVertexRecorder.STRIDE > 0 ? groupVerts.length / SimVertexRecorder.STRIDE : 0);
                    gj.addProperty("texture", resolveTextureId(entity, group.type(), renderer));
                    gj.addProperty("sourceRenderType", sourceRenderType);
                    gj.add("material", SimRenderTypeMaterialProbe.capture(group.type()));
                    JsonArray gv = new JsonArray();
                    for (float x : groupVerts) {
                        gv.add(Math.round(x * 10000.0F) / 10000.0F);
                    }
                    gj.add("vertices", gv);
                    poseGroups.add(gj);
                }
                renderGroupsByPose.add(pose.name(), poseGroups);
            }
            if (frames.isEmpty()) {
                return null;
            }

            // 頭がどの頂点で、どこを中心に回るかを割り出す (Viewer が連続的に頭を向けるため)。
            JsonObject head = null;
            try {
                Integer idleSlot = poseIndex.has("idle") ? poseIndex.get("idle").getAsInt() : 0;
                head = solveHead(renderer, entity, frames.get(idleSlot));
            } catch (Throwable ignored) {
                // 頭が割り出せないモデル (スライム等) は素直に諦める
            }

            String texId = resolveTextureId(entity, usedType, renderer);

            JsonObject o = new JsonObject();
            o.addProperty("type", String.valueOf(BuiltInRegistries.ENTITY_TYPE.getKey(type)));
            o.addProperty("texture", texId);
            o.addProperty("quads", quads);
            o.addProperty("walkFrames", WALK_FRAMES);
            o.addProperty("width", type.getWidth());
            o.addProperty("height", type.getHeight());
            o.add("poses", poseIndex);
            o.add("skeleton", captureSkeleton(entity));
            if (head != null) {
                o.add("head", head);
            }
            JsonArray arr = new JsonArray();
            for (float[] v : frames) {
                JsonArray f = new JsonArray();
                for (float x : v) {
                    f.add(Math.round(x * 10000.0F) / 10000.0F);
                }
                arr.add(f);
            }
            o.add("frames", arr);

            // Additive v1 extension. Existing Viewer ignores these fields and keeps using frames/texture.
            o.addProperty("renderGroupsVersion", 1);
            o.add("renderGroups", renderGroupsByPose);
            return o;
        } catch (Throwable t) {
            return null;
        } finally {
            try {
                if (borrowed) {
                    // 画面に映っている個体を借りたので、いじった姿勢を必ず戻す
                    entity.setYRot(oy); entity.setXRot(ox);
                    entity.yRotO = oyo; entity.xRotO = oxo;
                    if (entity instanceof LivingEntity le) {
                        le.yBodyRot = obody; le.yBodyRotO = obody;
                        le.yHeadRot = ohead; le.yHeadRotO = ohead;
                    }
                } else {
                    entity.discard();
                }
            } catch (Exception ignored) {
                // 記録用に作っただけなので後始末の失敗は無視してよい
            }
        }
    }

    /** 出力先。ゲームディレクトリ配下に置き、serve.mjs 側が探しに行く。 */
    public static Path outDir() {
        return Minecraft.getInstance().gameDirectory.toPath().resolve("simlab").resolve("models");
    }

    // =========================================================================
    // ブロック
    // =========================================================================
    /**
     * ブロックも同じ方法で書き出す。{@code BlockRenderDispatcher.renderSingleBlock} も
     * {@code VertexConsumer} へ流すので、<b>面ごとに違うテクスチャ (草ブロックの上/側面/底)、
     * 階段やハーフブロックのような非立方体、草・葉のバイオーム着色</b>が
     * すべて MC の計算結果として得られる。
     *
     * <p>UV はブロックアトラスを指すので、アトラス画像も一緒に書き出す。
     */
    public static int dumpBlocks(Path dir) {
        Minecraft mc = Minecraft.getInstance();
        var brd = mc.getBlockRenderer();
        JsonObject all = new JsonObject();
        int ok = 0;
        for (net.minecraft.world.level.block.Block block : BuiltInRegistries.BLOCK) {
            ResourceLocation id = BuiltInRegistries.BLOCK.getKey(block);
            if (id == null) {
                continue;
            }
            net.minecraft.world.level.block.state.BlockState st = block.defaultBlockState();
            if (st.getRenderShape() == net.minecraft.world.level.block.RenderShape.INVISIBLE) {
                continue;
            }
            try {
                Sink sink = new Sink();
                brd.renderSingleBlock(st, new PoseStack(), sink,
                        0x00F000F0, net.minecraft.client.renderer.texture.OverlayTexture.NO_OVERLAY);
                // ブロックは複数の RenderType にまたがることがある (cutout + translucent)。
                // どれも同じアトラスを指すので全部まとめてよい。
                List<Float> merged = new ArrayList<>();
                int quads = 0;
                for (SimVertexRecorder r : sink.byType.values()) {
                    if (r.isEmpty()) {
                        continue;
                    }
                    quads += r.quadCount();
                    for (float f : r.toArray()) {
                        merged.add(f);
                    }
                }
                if (merged.isEmpty()) {
                    continue;
                }
                JsonObject o = new JsonObject();
                o.addProperty("quads", quads);
                JsonArray verts = new JsonArray();
                for (float f : merged) {
                    verts.add(Math.round(f * 100000.0F) / 100000.0F);
                }
                o.add("verts", verts);
                all.add(id.toString(), o);
                ok++;
            } catch (Throwable ignored) {
                // 描けないブロックは飛ばす
            }
        }
        try {
            Files.createDirectories(dir);
            Files.writeString(dir.resolve("blocks.json"), all.toString(), StandardCharsets.UTF_8);
        } catch (Exception e) {
            TouhouLittleMaid.LOGGER.error("[SIM] blocks.json write failed", e);
        }
        dumpBlockAtlas(dir);
        return ok;
    }

    /** ブロックアトラスを PNG で吸い出す。ブロックの UV はこの 1 枚を指している。 */
    private static void dumpBlockAtlas(Path dir) {
        try {
            Minecraft mc = Minecraft.getInstance();
            var atlas = mc.getTextureManager().getTexture(net.minecraft.world.inventory.InventoryMenu.BLOCK_ATLAS);
            com.mojang.blaze3d.systems.RenderSystem.bindTexture(atlas.getId());
            int w = org.lwjgl.opengl.GL11.glGetTexLevelParameteri(
                    org.lwjgl.opengl.GL11.GL_TEXTURE_2D, 0, org.lwjgl.opengl.GL11.GL_TEXTURE_WIDTH);
            int h = org.lwjgl.opengl.GL11.glGetTexLevelParameteri(
                    org.lwjgl.opengl.GL11.GL_TEXTURE_2D, 0, org.lwjgl.opengl.GL11.GL_TEXTURE_HEIGHT);
            if (w <= 0 || h <= 0) {
                TouhouLittleMaid.LOGGER.warn("[SIM] block atlas size unknown ({}x{}), skipped", w, h);
                return;
            }
            try (com.mojang.blaze3d.platform.NativeImage img =
                         new com.mojang.blaze3d.platform.NativeImage(
                                 com.mojang.blaze3d.platform.NativeImage.Format.RGBA, w, h, false)) {
                img.downloadTexture(0, false);
                Files.createDirectories(dir);
                img.writeToFile(dir.resolve("blocks_atlas.png"));
            }
            TouhouLittleMaid.LOGGER.info("[SIM] block atlas dumped: {}x{}", w, h);
        } catch (Throwable t) {
            TouhouLittleMaid.LOGGER.error("[SIM] block atlas dump failed", t);
        }
    }

    /**
     * 指定した型 (空なら描画できる全型) を書き出す。
     *
     * @return [成功数, 失敗数, 出力先]
     */
    public static Object[] dump(List<EntityType<?>> types) {
        Path dir = outDir();
        int ok = 0, ng = 0;
        JsonArray index = new JsonArray();
        List<EntityType<?>> targets = types.isEmpty()
                ? new ArrayList<>(BuiltInRegistries.ENTITY_TYPE.stream().toList())
                : types;

        // ワールドに実在している個体を型ごとに拾っておく。実在するものはそれを録る
        // (湧き時に決まる見た目が入っているため。霊夢の YSM モデルはこれが無いと出ない)。
        Map<EntityType<?>, Entity> live = new LinkedHashMap<>();
        try {
            Minecraft mc = Minecraft.getInstance();
            if (mc.level != null) {
                for (Entity e : mc.level.entitiesForRendering()) {
                    live.putIfAbsent(e.getType(), e);
                }
            }
        } catch (Exception ignored) {
            // 拾えなくても新規生成で録れる
        }
        List<String> skipped = new ArrayList<>();

        for (EntityType<?> type : targets) {
            ResourceLocation id = BuiltInRegistries.ENTITY_TYPE.getKey(type);
            if (id == null) {
                continue;
            }
            JsonObject o = dumpOne(type, live.get(type));
            if (o == null) {
                ng++;
                skipped.add(id.toString());
                continue;
            }
            Path f = dir.resolve(id.getNamespace()).resolve(id.getPath() + ".json");
            try {
                Files.createDirectories(f.getParent());
                Files.writeString(f, o.toString(), StandardCharsets.UTF_8);
                JsonObject e = new JsonObject();
                e.addProperty("type", id.toString());
                e.addProperty("file", id.getNamespace() + "/" + id.getPath() + ".json");
                e.addProperty("quads", o.get("quads").getAsInt());
                index.add(e);
                ok++;
            } catch (Exception ex) {
                TouhouLittleMaid.LOGGER.error("[SIM] model dump write failed: {}", f, ex);
                ng++;
            }
        }

        // 個別指定のときはブロックまで舐めない (待たされるだけなので)
        int blocks = types.isEmpty() ? dumpBlocks(dir) : -1;

        try {
            Files.createDirectories(dir);
            JsonObject root = new JsonObject();
            root.addProperty("note", "generated by /tlmsim dumpmodels — MC 自身の VertexConsumer から記録");
            root.add("entities", index);
            // 録れなかった型も残す。「なぜ出ないのか」を後から追えるようにするため。
            JsonArray sk = new JsonArray();
            skipped.forEach(sk::add);
            root.add("skipped", sk);
            Files.writeString(dir.resolve("index.json"), root.toString(), StandardCharsets.UTF_8);
            if (!skipped.isEmpty()) {
                TouhouLittleMaid.LOGGER.info("[SIM] skipped {} types: {}", skipped.size(), String.join(", ", skipped));
            }
        } catch (Exception ex) {
            TouhouLittleMaid.LOGGER.error("[SIM] model index write failed", ex);
        }
        TouhouLittleMaid.LOGGER.info("[SIM] model dump: {} entities ok / {} skipped, {} blocks -> {}",
                ok, ng, blocks, dir);
        return new Object[]{ok, ng, dir, blocks};
    }

    // =========================================================================
    // 14-04 — YSM のスキニング前ローカル cube 座標を探る (/tlmsim dumpcubes)
    // =========================================================================
    // spike 004 第5段階: buildGeometry のcube展開(大きさ・形・面配置・scale・回転)は測れる範囲
    // すべて実機と一致するのに、同じボーン内で cube どうしをどこに置くかが 2.4cm ずれる。
    // JSON 側から試せる構造は全部潰した (README 参照) —— 次の証拠は実機側の生データしかない。
    //
    // ここは「探り針」であって解析器ではない: SimYsmGraphScan の候補をそのまま manifest + 生
    // float バイナリで書き出すだけで、どれが cube 頂点かは一切ここで決めない。意味づけは
    // buildGeometry と 1 対 1 で突き合わせるオフライン作業 (この plan の外)。

    /** {@link #dumpYsmLocalCubes} の結果。{@code negative=true} は候補0件、
     * {@code complete=true} は探索budgetによる未探索が無いことを表す。
     * negative でも complete=false なら「不在確定」ではない。 */
    public record DumpCubesResult(boolean ok, String message, @Nullable Path dir,
                                  boolean negative, boolean complete) {}

    private static final long DUMP_CUBES_MAX_TOTAL_BYTES = 256L * 1024 * 1024;

    /**
     * 霊夢の YSM モデルグラフを {@link SimYsmGraphScan} で走査し、cube 数・bone 数の倍数に
     * なる配列/Collection/Map を候補として manifest + 生 float バイナリ + bone 名テーブルへ
     * 書き出す。見つからなくても manifest は必ず書く (fail closed でも黙らない)。
     */
    public static DumpCubesResult dumpYsmLocalCubes(int cubeCount) {
        SimYsmRuntimeRoot.Result runtime = SimYsmRuntimeRoot.findNearestReimu();
        if (!runtime.ok() || runtime.root() == null) {
            return new DumpCubesResult(false, runtime.message(), null, false, false);
        }
        Object root = runtime.root();

        int cc = Math.max(1, cubeCount);
        SimBonePalette.Found found = SimBonePalette.find(root);
        int boneCount = found == null ? 0 : found.bones().size();
        SimBonePalette.SlotResult slots = found == null
                ? new SimBonePalette.SlotResult(null, "SimBonePalette.find が失敗 (形が見つからない: Map + N*12 float[])")
                : SimBonePalette.slotNames(found);

        SimYsmGraphScan.Report report = SimYsmGraphScan.scan(root, cc, boneCount);

        String stamp = new SimpleDateFormat("yyyyMMdd-HHmmss", Locale.ROOT).format(new Date());
        Path dir = outDir().resolveSibling("ysmcubes").resolve(stamp);
        try {
            Files.createDirectories(dir);
        } catch (Exception ex) {
            TouhouLittleMaid.LOGGER.error("[SIM] dumpcubes: 出力先の作成に失敗", ex);
            return new DumpCubesResult(false, "出力先の作成に失敗: " + ex, null, false, false);
        }

        writeBonesJson(dir, found, slots);

        long[] totalBytes = {0L};
        List<String> skippedForSize = new ArrayList<>();
        JsonArray exactArr = dumpCubesCandidatesToJson(report.exactMultiples(), dir, totalBytes, skippedForSize);
        JsonArray largeArr = dumpCubesCandidatesToJson(report.largeNonMultiples(), dir, totalBytes, skippedForSize);

        JsonObject manifest = new JsonObject();
        manifest.addProperty("note", "generated by /tlmsim dumpcubes (14-04) — 値の意味は推測しない。形と場所だけを書く");
        manifest.addProperty("spike", "004-stage6-dumpcubes");
        manifest.addProperty("rootRoute", runtime.route());
        manifest.addProperty("rootRouteNote", runtime.routeNote());
        manifest.addProperty("gameDir", String.valueOf(Minecraft.getInstance().gameDirectory));
        JsonArray jars = new JsonArray();
        for (String h : SimBoneProbeHashes.modJarHashes()) {
            jars.add(h);
        }
        manifest.add("jars", jars);
        manifest.addProperty("cubeCount", cc);
        manifest.addProperty("boneCount", boneCount);
        manifest.addProperty("boneResolutionOk", found != null);
        if (found == null) {
            manifest.addProperty("boneResolutionReason",
                    "SimBonePalette.find が失敗 (形が見つからない: Map + N*12 float[])");
        }
        manifest.addProperty("slotNamesOk", slots.ok());
        if (!slots.ok()) {
            manifest.addProperty("slotNamesReason", slots.reason());
        }
        manifest.addProperty("visited", report.visited());
        manifest.addProperty("depthReached", report.depthReached());
        manifest.addProperty("scanComplete", report.complete());
        manifest.addProperty("truncatedContainers", report.truncatedContainers());
        manifest.addProperty("depthBudgetExhausted", report.depthBudgetExhausted());
        manifest.addProperty("visitBudgetExhausted", report.visitBudgetExhausted());
        manifest.add("exactMultiples", exactArr);
        manifest.add("largeNonMultiples", largeArr);
        JsonArray skippedArr = new JsonArray();
        skippedForSize.forEach(skippedArr::add);
        manifest.add("skippedForSize", skippedArr);
        manifest.addProperty("totalBytesWritten", totalBytes[0]);
        boolean negative = report.negative();
        manifest.addProperty("negative", negative);
        manifest.addProperty("negativeConclusive", report.conclusiveNegative());

        try {
            Files.writeString(dir.resolve("manifest.json"), manifest.toString(), StandardCharsets.UTF_8);
        } catch (Exception ex) {
            TouhouLittleMaid.LOGGER.error("[SIM] dumpcubes: manifest.json 書き込み失敗", ex);
            return new DumpCubesResult(false, "manifest.json 書き込みに失敗: " + ex, dir, negative, report.complete());
        }

        String budget = "truncatedContainers=" + report.truncatedContainers()
                + ", depthBudget=" + report.depthBudgetExhausted()
                + ", visitBudget=" + report.visitBudgetExhausted();
        String msg;
        if (negative && report.complete()) {
            msg = "候補 0 件・探索完了 (cube=" + cc + " / bone=" + boneCount
                    + ", visited=" + report.visited() + ", depth=" + report.depthReached() + ")";
        } else if (negative) {
            msg = "候補 0 件だが探索不完全 — 不在確定ではない (" + budget + ")";
        } else {
            msg = "候補 " + (report.exactMultiples().size() + report.largeNonMultiples().size())
                    + " 件 (exact " + report.exactMultiples().size()
                    + " / large-non-multiple " + report.largeNonMultiples().size() + ")"
                    + (report.complete() ? "" : " / 探索不完全 (" + budget + ")");
        }
        TouhouLittleMaid.LOGGER.info("[SIM] dumpcubes: {} -> {}", msg, dir);
        return new DumpCubesResult(true, msg, dir, negative, report.complete());
    }

    /** {@code SimBonePalette.slotNames} の slot -> 名前に、bone オブジェクト自身が持つ id を
     * 添えて {@code bones.json} を書く。見つからない/解決できない場合も理由付きで必ず書く。 */
    private static void writeBonesJson(Path dir, @Nullable SimBonePalette.Found found, SimBonePalette.SlotResult slots) {
        JsonObject root = new JsonObject();
        if (found == null || !slots.ok()) {
            root.addProperty("ok", false);
            root.addProperty("reason", found == null
                    ? "SimBonePalette.find が失敗 (形が見つからない)"
                    : slots.reason());
            try {
                Files.writeString(dir.resolve("bones.json"), root.toString(), StandardCharsets.UTF_8);
            } catch (Exception ex) {
                TouhouLittleMaid.LOGGER.error("[SIM] dumpcubes: bones.json 書き込み失敗", ex);
            }
            return;
        }
        Map<String, Integer> nameToId = dumpCubesBoneNameToId(found);
        String[] names = slots.names();
        JsonArray bones = new JsonArray();
        for (int slot = 0; slot < names.length; slot++) {
            String name = names[slot];
            JsonObject b = new JsonObject();
            b.addProperty("name", name);
            Integer id = nameToId.get(name);
            b.addProperty("boneId", id == null ? -1 : id);
            b.addProperty("slot", slot);
            bones.add(b);
        }
        root.addProperty("ok", true);
        root.addProperty("boneCount", names.length);
        root.add("bones", bones);
        try {
            Files.writeString(dir.resolve("bones.json"), root.toString(), StandardCharsets.UTF_8);
        } catch (Exception ex) {
            TouhouLittleMaid.LOGGER.error("[SIM] dumpcubes: bones.json 書き込み失敗", ex);
        }
    }

    /** bone 名 -&gt; YSM bone id (= マップのキー)。slot は既に {@code SimBonePalette.slotNames}
     * が解決しているので、ここでは名前と id の対応だけを読む (反射はフィールドのみ)。 */
    private static Map<String, Integer> dumpCubesBoneNameToId(SimBonePalette.Found found) {
        Map<String, Integer> out = new LinkedHashMap<>();
        for (Map.Entry<?, ?> e : found.bones().entrySet()) {
            Object v = e.getValue();
            if (v == null) {
                continue;
            }
            String name = null;
            for (Field f : SimBonePalette.declaredFields(v.getClass())) {
                if (Modifier.isStatic(f.getModifiers())) {
                    continue;
                }
                Object fv = SimBonePalette.read(f, v);
                if (fv instanceof String s) {
                    name = s;
                    break;
                }
            }
            if (name != null && e.getKey() instanceof Number n) {
                out.put(name, n.intValue());
            }
        }
        return out;
    }

    /** 候補一覧を manifest 用 JSON へ変換しつつ、float[] 候補は 256MB 上限内で生バイナリへ書く。
     * 上限を超えた分は<b>切り詰めず</b>、manifest の {@code skippedForSize} へ長さとともに残す。 */
    private static JsonArray dumpCubesCandidatesToJson(List<SimYsmGraphScan.Candidate> list, Path dir,
                                                         long[] totalBytes, List<String> skippedForSize) {
        JsonArray arr = new JsonArray();
        int i = 0;
        for (SimYsmGraphScan.Candidate c : list) {
            JsonObject o = new JsonObject();
            o.addProperty("path", c.path());
            o.addProperty("ownerClass", c.ownerClass());
            o.addProperty("componentType", c.componentType());
            o.addProperty("length", c.length());
            o.addProperty("cubeMultiple", c.size().cubeMultiple());
            o.addProperty("cubeMultipleValue", c.size().cubeMultipleValue());
            o.addProperty("boneMultiple", c.size().boneMultiple());
            o.addProperty("boneMultipleValue", c.size().boneMultipleValue());
            o.addProperty("remainderVsCube", c.size().remainderVsCube());
            o.addProperty("remainderVsBone", c.size().remainderVsBone());
            if (c.elementInfo() != null) {
                o.addProperty("elementClass", c.elementInfo().className());
                JsonArray fields = new JsonArray();
                c.elementInfo().fieldNames().forEach(fields::add);
                o.add("elementFields", fields);
            }
            if (c.rawFloats() != null) {
                long bytes = (long) c.rawFloats().length * 4L;
                if (totalBytes[0] + bytes > DUMP_CUBES_MAX_TOTAL_BYTES) {
                    skippedForSize.add(c.path() + " (length=" + c.length() + ", bytes=" + bytes
                            + ") — 256MB 上限超過のためスキップ (切り詰めない)");
                    o.addProperty("binFile", (String) null);
                    o.addProperty("skippedForSize", true);
                } else {
                    String file = String.format(Locale.ROOT, "%02d.%s.bin", i, dumpCubesSanitizePath(c.path()));
                    try {
                        dumpCubesWriteFloats(dir.resolve(file), c.rawFloats());
                        totalBytes[0] += bytes;
                        o.addProperty("binFile", file);
                    } catch (Exception ex) {
                        TouhouLittleMaid.LOGGER.error("[SIM] dumpcubes: bin 書き込み失敗 {}", c.path(), ex);
                        o.addProperty("binFile", (String) null);
                        o.addProperty("writeError", String.valueOf(ex));
                    }
                }
            }
            arr.add(o);
            i++;
        }
        return arr;
    }

    private static String dumpCubesSanitizePath(String path) {
        return path.replaceAll("[^A-Za-z0-9_.-]", "_");
    }

    /** {@code SimBoneCapture.writeFloats} と同じ little-endian float32 の書き出し規約。
     * {@code SimBoneCapture.java} は files_modified に無いため、ここに複製している。 */
    private static void dumpCubesWriteFloats(Path f, float[] a) throws Exception {
        ByteBuffer bb = ByteBuffer.allocate(a.length * 4).order(ByteOrder.LITTLE_ENDIAN);
        for (float v : a) {
            bb.putFloat(v);
        }
        Files.write(f, bb.array(), StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
    }
}