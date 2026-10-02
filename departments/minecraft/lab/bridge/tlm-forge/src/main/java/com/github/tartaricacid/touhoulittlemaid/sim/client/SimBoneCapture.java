package com.github.tartaricacid.touhoulittlemaid.sim.client;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import com.github.tartaricacid.touhoulittlemaid.entity.passive.EntityMaid;
import com.github.tartaricacid.touhoulittlemaid.geckolib3.geo.IGeoEntity;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.network.chat.Component;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.api.distmarker.OnlyIn;

import java.lang.reflect.Field;
import java.lang.reflect.Modifier;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import java.util.Map;

/**
 * spike 004 第2段階 — <b>同じ 1 回の {@code geoRender} から、ボーン配列と頂点を同時に採る</b>。
 * {@code /tlmsim bonecapture [枚数] [間隔tick]}。
 *
 * <h3>なぜ同時でなければならないか</h3>
 * 別々に採ると animation controller が 1 フレーム進み、<b>行列と頂点が違う瞬間のものになる</b>。
 * そうなると誤差を測っても「変換式が違う」のか「フレームがずれている」のか区別できず、
 * <b>判定そのものが成立しない</b>（審査指摘 2026-08-24）。
 * {@link SimTeeBuffer} で描画の行き先を増やし、描画回数は増やさない。
 *
 * <h3>値を分解しない</h3>
 * {@code 1058 × 12} が最終スキニング行列なら、quaternion / position / scale へ<b>分解しない</b>。
 * 分解は負 scale・shear・非一様 scale を落としうる（審査指摘）。
 * <b>float 配列をそのままバイナリで書き出す。</b> 意味づけは後段（オフライン）で、
 * 複数の候補レイアウトを頂点と突き合わせて<b>誤差で決める</b>。
 *
 * <h3>探し方 —— 難読名を焼き込まない</h3>
 * フィールド名 {@code o0OoO0O0OoO0oOoOO0oOooO0} 等は YSM のバージョンが変われば変わる。
 * そこで<b>形で探す</b>: 「{@code Map} で、その {@code size} を N としたとき、
 * 同じ持ち主に長さ {@code N*12} の {@code float[]} が在る」もの。
 * 見つからなければ<b>黙って代替へ落ちず失敗を報告する</b>（fail closed）。
 * JAR の SHA-256 も毎回書き出すので、後から「どのビルドで採ったか」が判る。
 */
@OnlyIn(Dist.CLIENT)
public final class SimBoneCapture {

    private SimBoneCapture() {}

    /**
     * <b>採る姿勢は自分で作る。</b> にーくらに「霊夢を動かして」と頼まない
     * （審査の受け入れ条件 7 —— 状態機械で連続採取すれば、人がタイミングを合わせる必要が無い）。
     *
     * <h3>選び直した理由（2026-08-24、1 回目の採取を測った結果）</h3>
     * 最初は「宣言チャンネルを持つボーンが最多」で選び、{@code pre_parallel0} /
     * {@code pre_parallel1} / {@code parallel1} を入れた。<b>これは誤りだった。</b>
     * 実測すると宣言のごく一部しか残らない:
     * <pre>
     *   parallel1     : 宣言 276 本 → 実際に動いたのは 17 本 (6%)
     *   pre_parallel0 : 宣言  79 本 → 実際に動いたのは  1 本
     *   pre_parallel1 : 宣言  29 本 → ほぼゼロ
     *   extra44       : 宣言  95 本 → 位置10/回転5/scale6、回転は最大 33.1 度
     * </pre>
     * これらは {@code animation_length = 0} の静的ポーズ定義で、controller が層として
     * 合成する前提のもの。単体で {@code ysm play} に投げても大半は基底層に上書きされる。
     * <b>「データとして大きい」と「再生したら残る」は別のこと</b>を測り違えていた
     * （にーくら 2026-08-24「parallel が実機で極端に動いているようには見えなかった」）。
     *
     * <h3>選び直した基準 —— 実際に再生される証拠があるもの</h3>
     * 実 run のトレース（tank）に現れた＝実機で再生される証拠があるもの、および
     * CLAUDE.md が実機検証済みと明記しているものから、チャンネルの広さで選ぶ:
     * <pre>
     *   extra44          95本 rot87 pos14 scl6 zero2  —— **効くことを実測済み**
     *   extra43          69本 rot59 pos 8 scl2        —— CLAUDE.md の判例 (実機検証済み)
     *   sneaking_1       42本 rot36 pos 9 scl9 zero7  —— 実 run に出た。**scale=0 が最多**
     *   use_offhand:bow  20本 rot17 pos10 scl2 zero1  —— 実 run に出た。**position が最多**
     *   extra95          21本 rot20 pos 2 scl1 zero1  —— 実 run に出た
     * </pre>
     * 回転しか動かない姿勢だけだと<b>変換式が間違っていても一致してしまう</b>ので、
     * position・scale・scale=0 を必ず通す。
     */
    private static final String[] POSES = {
            "empty", "extra44", "extra43", "sneaking_1", "use_offhand:bow", "extra95",
    };

    /** アニメを送ってから録り始めるまでの待ち。{@code SimAnimSweep.SETTLE_TICKS} と同じ値。 */
    private static final int SETTLE_TICKS = 8;

    private static volatile boolean armed = false;
    private static int perPose;
    private static int spacing;
    private static int taken;
    private static int poseIndex;
    private static int takenThisPose;
    private static int settle;
    private static int targetEntityId = -1;
    private static long lastTick = Long.MIN_VALUE;
    private static Path outDir;
    private static JsonArray samples;

    public static String start(int countPerPose, int spacingTicks) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null || mc.player == null) {
            return "ワールドに入ってから実行すること";
        }
        if (mc.getSingleplayerServer() == null) {
            return "シングルプレイ (統合サーバ) でないとアニメを送れない";
        }
        EntityMaid reimu = nearestReimu();
        if (reimu == null) {
            return "近くに霊夢が居ない";
        }
        targetEntityId = reimu.getId();
        perPose = Math.max(1, countPerPose);
        spacing = Math.max(1, spacingTicks);
        taken = 0;
        poseIndex = 0;
        takenThisPose = 0;
        settle = SETTLE_TICKS;
        lastTick = Long.MIN_VALUE;
        samples = new JsonArray();
        baseline = null;
        noisePerBone = null;
        lastServerAnim = null;
        String stamp = new SimpleDateFormat("yyyyMMdd-HHmmss", Locale.ROOT).format(new Date());
        outDir = SimModelDump.outDir().resolveSibling("spike004").resolve(stamp);
        armed = true;
        sendPose();
        return "[SIM] bonecapture: " + POSES.length + " 姿勢 × " + perPose + " 枚 (間隔 "
                + spacing + "t) を自動で採る。**動かさなくてよい** -> " + outDir;
    }

    public static boolean isArmed() {
        return armed;
    }

    /** 一番近い霊夢。{@code /tlmsim animsweep} と同じ選び方。 */
    private static EntityMaid nearestReimu() {
        Minecraft mc = Minecraft.getInstance();
        EntityMaid best = null;
        double bestD = Double.MAX_VALUE;
        for (net.minecraft.world.entity.Entity e : mc.level.entitiesForRendering()) {
            if (!(e instanceof EntityMaid m)) {
                continue;
            }
            if (!(m.isReimuMaid() || m.isNamedReimu())) {
                continue;
            }
            double d = mc.player.distanceToSqr(m);
            if (d < bestD) {
                bestD = d;
                best = m;
            }
        }
        return best;
    }

    /**
     * 今の姿勢を送る。<b>AI は止めない</b> —— {@code SimAnimSweep} と同じく、
     * 割り込まれたら送り直す（{@link #reassert}）。AI を切ると「実機の霊夢」でなくなり、
     * 採ったボーンが実機の姿勢を表さなくなる。
     */
    private static void sendPose() {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || poseIndex >= POSES.length) {
            return;
        }
        String anim = POSES[poseIndex];
        SimAnimSweep.withServerMaid(mc.player, targetEntityId,
                maid -> maid.playReimuMaidAnimation(anim, true));
    }

    /**
     * サーバ側で今どのアニメが再生中か、の 1 tick 遅れの写し。
     *
     * <p><b>クライアントからは直接読めない。</b> {@code reimuExt().lastPlayedReimuAnim} は
     * サーバ側の状態で、クライアントで読むと必ず {@code null} になる
     * （1 回目の採取で全標本 {@code actualAnim=null} だった原因）。
     * {@link #reassert} がサーバスレッドで読んだ値をここへ写しておく。
     */
    private static volatile String lastServerAnim = null;

    /** 霊夢自身の AI が別のアニメへ割り込んでいたら送り直す（{@code SimAnimSweep} と同じ手）。 */
    private static void reassert() {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || poseIndex >= POSES.length) {
            return;
        }
        String anim = POSES[poseIndex];
        SimAnimSweep.withServerMaid(mc.player, targetEntityId, maid -> {
            String cur = maid.reimuExt().lastPlayedReimuAnim;
            lastServerAnim = cur;   // 標本へ書くための写し
            if (!anim.equals(cur)) {
                maid.playReimuMaidAnimation(anim, true);
            }
        });
    }

    /** 今どの姿勢を撮っているか（標本に書く）。 */
    private static String currentPose() {
        return poseIndex < POSES.length ? POSES[poseIndex] : "(終了)";
    }

    // =========================================================================
    // 効いたかどうかを、その場で判定する
    // =========================================================================
    // **1 回目の採取では、効いていない姿勢が 3 つ混じっていたのに誰も気づかなかった**
    // (2026-08-24。にーくらが実機の見た目で気づき、私が後から測って確かめた)。
    // 採ったその場で言わないと、また同じことが起きる。
    //
    // 判定は**自己較正**する: 最初の姿勢 (empty) の標本どうしの差を「揺らぎ」とし、
    // 以降の姿勢がその何倍動いたかで見る。アニメの宣言ボーン集合を読む必要が無いので、
    // パックの JSON をクライアントで解析しなくて済む。

    /** 基準（最初の姿勢）の 1 枚目。以降の姿勢はこれと比べる。 */
    private static float[] baseline;

    /**
     * 基準の標本どうしの最大差 = 基底層の揺らぎ。<b>ボーンごと</b>に持つ
     * ({@code noisePerBone[b]}、長さ {@code palette.length / SimBoneNoise.STRIDE})。
     * これを超えた分だけが「姿勢の効果」(2026-08-24。旧実装は 1058 本を共有スカラー
     * 1 個で代表していたため、1 本の暴れたボーンが残り全部の閾値を吊り上げていた)。
     * 判定の純関数本体は {@link SimBoneNoise} へ切り出した ── ここは「いつ呼ぶか」だけ持つ。
     */
    private static float[] noisePerBone;

    /**
     * @return {@code [変化したボーン数, 最大差]}。基準がまだ無ければ {@code null}。
     */
    private static float[] takeUp(float[] palette) {
        if (baseline == null || noisePerBone == null || palette.length != baseline.length) {
            return null;
        }
        return SimBoneNoise.takeUp(baseline, palette, noisePerBone);
    }

    /** 基準どうしの差から、ボーンごとの揺らぎを更新する。 */
    private static void updateNoise(float[] palette) {
        if (baseline == null) {
            baseline = palette.clone();
            noisePerBone = SimBoneNoise.newPerBone(palette.length);
            return;
        }
        SimBoneNoise.accumulate(noisePerBone, baseline, palette);
    }

    /**
     * 描画の直前に呼ばれ、<b>採る回なら</b>分岐した buffer を返す。採らない回は null。
     * 返り値が null でなければ、呼び出し側はそれを {@code geoRender} へ渡し、
     * 描画後に {@link #after} を呼ぶ。
     */
    public static SimTeeBuffer before(EntityMaid maid, net.minecraft.client.renderer.MultiBufferSource real) {
        if (!armed || maid == null) {
            return null;
        }
        if (!(maid.isReimuMaid() || maid.isNamedReimu())) {
            return null;
        }
        if (maid.getId() != targetEntityId) {
            return null;
        }
        long t = maid.level().getGameTime();
        if (lastTick != Long.MIN_VALUE && t - lastTick < spacing) {
            return null;
        }
        // **AI が割り込んでいたら送り直す。** AI は止めない —— 止めると「実機の霊夢」でなくなる。
        reassert();
        // 送ってから効くまで待つ。待たずに録ると前の姿勢が混ざる。
        if (settle > 0) {
            settle--;
            lastTick = t;
            return null;
        }
        lastTick = t;
        return new SimTeeBuffer(real);
    }

    /** {@code geoRender} 直後。<b>ここでボーンを読む</b> —— 頂点と同じ 1 回の描画のもの。 */
    public static void after(EntityMaid maid, IGeoEntity geoEntity, SimTeeBuffer tee, float partialTick) {
        if (tee == null) {
            return;
        }
        try {
            Object root = geoEntity == null ? null : geoEntity.getGeoModel();
            SimBonePalette.Found found = root == null ? null : SimBonePalette.find(root);
            if (found == null) {
                armed = false;
                say(ChatFormatting.RED, "[SIM] bonecapture: ボーン配列が見つからない (fail closed)。"
                        + " YSM のバージョンが変わった可能性 —— 黙って別のものを掴まない");
                return;
            }
            writeSample(maid, tee, found, partialTick);
            taken++;
            takenThisPose++;
            // 最初の姿勢は基準。以降は「効いたか」をその場で言う。
            if (poseIndex == 0) {
                updateNoise(found.palette());
            } else if (takenThisPose >= perPose) {
                float[] up = takeUp(found.palette());
                if (up != null && up[0] < 3) {
                    // **黙って次へ行かない。** 1 回目はここで気づけず、効いていない姿勢を
                    // 3 つ抱えたまま解析へ回した (2026-08-24)。
                    say(ChatFormatting.YELLOW, "[SIM] bonecapture: 姿勢 '" + currentPose()
                            + "' はほとんど効いていない (変化したボーン " + (int) up[0]
                            + " 本 / 最大差 " + String.format(Locale.ROOT, "%.4f", up[1])
                            + ")。この姿勢は判定に使えない");
                }
            }
            if (takenThisPose >= perPose) {
                // 次の姿勢へ。送ってから settle だけ待つ。
                takenThisPose = 0;
                poseIndex++;
                settle = SETTLE_TICKS;
                if (poseIndex < POSES.length) {
                    sendPose();
                    say(ChatFormatting.GRAY, "[SIM] bonecapture: " + taken + "/"
                            + (POSES.length * perPose) + " 枚 — 次の姿勢 " + currentPose());
                }
            }
            if (poseIndex >= POSES.length) {
                armed = false;
                Path idx = writeIndex();
                say(ChatFormatting.GREEN, "[SIM] bonecapture: 完了 " + taken + " 枚 -> " + idx);
            }
        } catch (Throwable t) {
            armed = false;
            TouhouLittleMaid.LOGGER.error("[SIM] bonecapture failed", t);
            say(ChatFormatting.RED, "[SIM] bonecapture 失敗: " + t);
        }
    }

    // =========================================================================
    // 書き出し
    // =========================================================================
    // 探索 (「形で探す。難読名を焼き込まない」) は SimBonePalette へ移動した
    // (2026-08-25、SimBoneNoise と同じ理由でテスト可能にするため)。ここでは
    // SimBonePalette.find/declaredFields/read へ委譲するだけで、before/after/
    // SimTeeBuffer の挙動・書き出すファイルは一切変えていない。

    private static void writeSample(EntityMaid maid, SimTeeBuffer tee, SimBonePalette.Found found, float partialTick)
            throws Exception {
        Files.createDirectories(outDir);
        String base = String.format(Locale.ROOT, "%03d", taken);

        // --- ボーン: 生のまま。分解しない。 ---
        writeFloats(outDir.resolve(base + ".palette.bin"), found.palette());
        if (found.quats() != null) {
            writeFloats(outDir.resolve(base + ".quats.bin"), found.quats());
        }

        // --- ボーンの素性: 全件。標本ではない (受け入れ条件 2)。 ---
        JsonArray bones = new JsonArray();
        for (Map.Entry<?, ?> e : found.bones().entrySet()) {
            Object v = e.getValue();
            if (v == null) {
                continue;
            }
            JsonObject b = new JsonObject();
            b.addProperty("key", String.valueOf(e.getKey()));
            for (Field f : SimBonePalette.declaredFields(v.getClass())) {
                if (Modifier.isStatic(f.getModifiers())) {
                    continue;
                }
                Object fv = SimBonePalette.read(f, v);
                // 名前と整数と float だけ出す。配列やオブジェクトは型名で済ませる
                // (意味づけは後段。ここで推測しない)。
                if (fv instanceof String s) {
                    b.addProperty(f.getName(), s);
                } else if (fv instanceof Number num) {
                    b.addProperty(f.getName(), num);
                } else if (fv instanceof Boolean bo) {
                    b.addProperty(f.getName(), bo);
                } else if (fv == null) {
                    b.addProperty(f.getName(), (String) null);
                } else if (fv.getClass().isArray()) {
                    b.addProperty(f.getName(), "<" + fv.getClass().getSimpleName()
                            + " len=" + java.lang.reflect.Array.getLength(fv) + ">");
                } else if (fv.getClass().getName().startsWith("org.joml.")) {
                    b.addProperty(f.getName(), String.valueOf(fv));
                } else {
                    b.addProperty(f.getName(), "<" + fv.getClass().getName() + ">");
                }
            }
            bones.add(b);
        }
        Files.write(outDir.resolve(base + ".bones.json"),
                bones.toString().getBytes(StandardCharsets.UTF_8));

        // --- 頂点: RenderType ごとに分けたまま。どれが本体かは後で選ぶ。 ---
        JsonArray groups = new JsonArray();
        int gi = 0;
        for (Map.Entry<RenderType, SimVertexRecorder> e : tee.recorders().entrySet()) {
            SimVertexRecorder rec = e.getValue();
            if (rec.isEmpty()) {
                continue;
            }
            float[] verts = rec.toArray();
            String name = base + ".verts" + gi + ".bin";
            writeFloats(outDir.resolve(name), verts);
            JsonObject g = new JsonObject();
            g.addProperty("renderType", String.valueOf(e.getKey()));
            g.addProperty("file", name);
            g.addProperty("floats", verts.length);
            g.addProperty("stride", SimVertexRecorder.STRIDE);
            g.addProperty("verts", verts.length / SimVertexRecorder.STRIDE);
            g.addProperty("quads", rec.quadCount());
            groups.add(g);
            gi++;
        }

        JsonObject s = new JsonObject();
        s.addProperty("index", taken);
        // requestedPose は「こちらが送ったもの」、actualAnim は「霊夢が実際に再生しているもの」。
        // **一致するとは限らない**（AI が割り込む）ので両方書く —— 後で食い違う標本を外せる。
        s.addProperty("requestedPose", currentPose());
        // **サーバ側の状態なので、クライアントから直接読むと必ず null になる**
        // (1 回目の採取で全標本 actualAnim=null だった原因)。1 tick 遅れの写しを使う。
        s.addProperty("actualAnim", lastServerAnim);
        // 「効いたか」の数値。基準の姿勢では null。
        float[] up = poseIndex == 0 ? null : takeUp(found.palette());
        if (up != null) {
            s.addProperty("changedBones", (int) up[0]);
            s.addProperty("maxDelta", up[1]);
            // ボーンごと化 (2026-08-24) で単一スカラーのキーは無くなった (旧: JSON 内の
            // "baseline" + "Noise" を連結したキー1個)。代表値として median/max を書く
            // ── 下流の読み手は無い(grep 済み)。
            s.addProperty("baselineNoiseMedian", SimBoneNoise.median(noisePerBone));
            s.addProperty("baselineNoiseMax", SimBoneNoise.max(noisePerBone));
            s.addProperty("tookEffect", up[0] >= 3);
        }
        s.addProperty("gameTime", maid.level().getGameTime());
        s.addProperty("tickCount", maid.tickCount);
        s.addProperty("partialTick", partialTick);
        s.addProperty("yBodyRot", maid.yBodyRot);
        s.addProperty("yHeadRot", maid.yHeadRot);
        s.addProperty("xRot", maid.getXRot());
        s.addProperty("boneCount", found.bones().size());
        s.addProperty("paletteFloats", found.palette().length);
        s.addProperty("paletteFile", base + ".palette.bin");
        s.addProperty("quatFloats", found.quats() == null ? 0 : found.quats().length);
        s.addProperty("bonesFile", base + ".bones.json");
        s.addProperty("ownerClass", found.ownerClass());
        s.addProperty("ownerPath", found.path());
        s.add("vertexGroups", groups);
        samples.add(s);
    }

    private static Path writeIndex() throws Exception {
        JsonObject o = new JsonObject();
        o.addProperty("spike", "004-stage2");
        o.addProperty("note", "行列は分解していない。意味づけは後段でレイアウト候補を頂点と突き合わせて決める。");
        Minecraft mc = Minecraft.getInstance();
        o.addProperty("gameDir", String.valueOf(mc.gameDirectory));
        JsonArray jars = new JsonArray();
        for (String h : SimBoneProbeHashes.modJarHashes()) {
            jars.add(h);
        }
        o.add("jars", jars);
        o.add("samples", samples);
        Path f = outDir.resolve("index.json");
        Files.write(f, o.toString().getBytes(StandardCharsets.UTF_8));
        return f;
    }

    private static void writeFloats(Path f, float[] a) throws Exception {
        ByteBuffer bb = ByteBuffer.allocate(a.length * 4).order(ByteOrder.LITTLE_ENDIAN);
        for (float v : a) {
            bb.putFloat(v);
        }
        Files.write(f, bb.array(), StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
    }

    // =========================================================================
    // declaredFields/read は SimBonePalette へ移動した。ここからの利用は
    // SimBonePalette.declaredFields/read への委譲で足りるため、ローカル実装は持たない。

    private static void say(ChatFormatting color, String msg) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player != null) {
            mc.player.displayClientMessage(Component.literal(msg).withStyle(color), false);
        }
    }
}
