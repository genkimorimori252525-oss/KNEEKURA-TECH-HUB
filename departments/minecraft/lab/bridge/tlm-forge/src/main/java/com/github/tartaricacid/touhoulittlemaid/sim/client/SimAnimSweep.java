package com.github.tartaricacid.touhoulittlemaid.sim.client;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import com.github.tartaricacid.touhoulittlemaid.entity.passive.EntityMaid;
import com.github.tartaricacid.touhoulittlemaid.entity.passive.reimu.IReimuMaidHost;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import javax.annotation.Nullable;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Consumer;

/**
 * 霊夢の YSM パックが持つ<b>全アニメーションを 1 本ずつ強制再生し、その間の頂点を録る</b>
 * オフライン収集器 (quick 260819-o9l、コマンド {@code /tlmsim animsweep [ticksPerAnim]})。
 *
 * <h3>なぜ要るのか</h3>
 * {@link SimPoseTrace} は「今動いている霊夢を毎tick録る」オンライン収集器なので、
 * 夢想封印のように滅多に出ない・出るタイミングが読めない技の正解が記録に入らない
 * (実測: 記録 4.8 秒に腕を大きく開く姿勢が 1 つも無く、回転順序の総当たり 36 通りが
 * 1.3% 差で判別不能だった)。<b>記録に無いものは検証できない</b> —— これはコードのバグでは
 * なく記録の網羅性の問題なので、網羅的に録る道具をもう 1 つ作る。
 * 姿勢の計算は今回も YSM に任せたまま ({@link SimPoseDump} / {@link SimPoseTrace} と同じ思想)。
 *
 * <h3>送信経路 —— 証明済みのものを呼ぶ。複製しない</h3>
 * {@link EntityMaid#playReimuMaidAnimation(String, boolean)}
 * ({@code ReimuMaidExtension.fireReimuAnimImmediate} への薄い委譲) は、<b>霊夢エンティティ
 * 自身を command source にして {@code ysm play} を実行する</b>経路で、
 * {@code ReimuGroundAttackTask} だけで 20 箇所以上 ({@code extra43}/{@code extra93}/
 * {@code extra94} 等) から呼ばれ、CLAUDE.md の「浮遊/構えポーズ不具合の判例」節が実機検証済みと
 * 明記している。ここはそれを<b>呼ぶだけ</b>で、コマンド文字列の組み立ても {@code @e[...]}
 * セレクタの生成も行わない。副産物として、{@code hold_mainhand:slashblade} のように
 * {@code :} を含むアニメ名 (実測 140/316 本) を引用符で包む処理が無料で付いてくる。
 *
 * <p>当初 BRIEF は「プレイヤー source の {@code execCommand} で {@code ysm play} を流す」を
 * 検証すべき未知数として書いていたが、それは誤りだった (plan-checker の実コード調査で判明)。
 * {@code YsmReimuNaianClientRunner} は今回、参考にも複製にもしていない。
 *
 * <h3>ヒープに全フレームを溜めない (BRIEF 制約 2)</h3>
 * {@link SimPoseTrace} は相異なるフレームだけを bin へ書くために、判定材料として全フレームの
 * 頂点をヒープに持つ。同じことを 316 本 × 20 tick × 約 24,000 頂点 × 11 float × 4 byte で
 * やると <b>約 6.6GB</b> になり、{@code -Xmx2G} の JVM では確実に落ちる。
 * よってこのクラスは<b>デデュープを一切使わず</b>、毎 tick 無条件に
 * {@link SimPoseCodec#appendFrame} でディスクへ逐次追記する。ヒープに保持するのは
 * 索引用の int 系メタデータだけ (ディスクは食ってよい、ヒープを食ってはいけない)。
 * その結果 tick とフレームが 1:1 に対応するので、{@code .anims.json} の {@code from}/{@code to}
 * は bin 内の連番そのものになる。
 *
 * <h3>霊夢自身の AI との競合</h3>
 * sweep 中も霊夢の通常 AI (歩行/交戦/待機ランダム/昼夜切替等) は動き続け、
 * {@code playReimuMaidAnimation} を独自に呼んで割り込みうる。対策として
 * {@code ReimuMaidExtension.lastPlayedReimuAnim} を毎 tick 突き合わせ、
 * 食い違っていたら<b>同じ API で即座に送り直す</b>。一致している限り再送はしない ——
 * 毎 tick 無条件に force 送信すると同じアニメが毎 tick 頭から再生され、
 * <b>アニメ自身の時間経過が録れなくなる</b>。霊夢の AI 側には一切手を入れない。
 *
 * <h3>「送れた」と「効いた」は別 (この quick で唯一の実効性チェック)</h3>
 * {@code server.execute()} は非同期なので、戻り値からは「実際に霊夢の見た目が変わったか」は
 * 判らない。そこで開始時に撮った {@code baselineVerts} と、1 本目のアニメの settle 後に撮った
 * 頂点を {@link SimPoseCodec#same} で比べ、同一なら黄字で 1 回だけ警告する
 * ({@code SimPoseDump.finish()} の「全部同じ形だった」警告と同じ思想)。
 */
@Mod.EventBusSubscriber(modid = TouhouLittleMaid.MOD_ID, value = Dist.CLIENT)
public final class SimAnimSweep {

    /**
     * アニメを送ってから録り始めるまでの待ち。{@code SimPoseDump.SETTLE_TICKS} と同じ値だが、
     * 元ファイルは無改変対象なので値をここへ写している。
     */
    private static final int SETTLE_TICKS = 8;

    /** 霊夢を探す半径。{@link SimPoseTrace} と同じ考え方。 */
    private static final double SEARCH_RADIUS = 16.0;

    /** {@code ticksPerAnim} の既定値 (20 tick = 1 秒)。 */
    private static final int DEFAULT_TICKS_PER_ANIM = 20;

    /** YSM のパック置き場。{@code <gameDir>/config/yes_steve_model/custom}。 */
    private static final String[] YSM_CUSTOM_DIR = {"config", "yes_steve_model", "custom"};

    private SimAnimSweep() {}

    /** 1 本のアニメを処理する 3 段階。 */
    private enum Phase {
        /** アニメを 1 回だけ送る。 */
        SEND,
        /** コマンドが効くまで待つ ({@link #SETTLE_TICKS})。 */
        WAIT_SETTLE,
        /** 毎 tick 撮ってディスクへ追記する。 */
        CAPTURE
    }

    // ---- 進行状態 ----
    private static boolean active = false;
    @Nullable
    private static Entity target = null;
    /** クライアント側 entity id。シングルプレイでは統合サーバと共有される。 */
    private static int targetEntityId = -1;
    private static List<String> animNames = List.of();
    private static Map<String, Double> animLengths = SimAnimManifest.emptyLengths();
    private static int animIndex = 0;
    private static int ticksPerAnim = DEFAULT_TICKS_PER_ANIM;
    private static int wait = 0;
    private static Phase phase = Phase.SEND;
    private static int capturedThisAnim = 0;
    /** {@code .pose.bin} へ書いたフレーム数。次に書くフレームの番号でもある。 */
    private static int frameCounter = 0;
    /** 今録っているアニメの最初のフレーム番号。 */
    private static int currentAnimFromFrame = 0;
    /** 送信に失敗して 0 フレームで飛ばしたアニメの本数。 */
    private static int failedSends = 0;
    private static long gt0 = 0L;
    @Nullable
    private static String type = null;
    @Nullable
    private static String texture = null;
    private static int vertsPerFrame = -1;

    /**
     * 開始時 (どのアニメも送る前) の頂点。1 本目の settle 後の頂点と比べて
     * 「そもそも効いたのか」を判定するためだけに 1 枚だけ持ち、判定が済んだら捨てる。
     * フレーム列を溜めるのとは別物 (1 枚 ≒ 1MB)。
     */
    @Nullable
    private static float[] baselineVerts = null;

    /** AI 割り込みの警告ログを既に 1 回出したか (以降は debug へ落とす)。 */
    private static boolean interferenceLogged = false;
    private static boolean firstAnimBaselineChecked = false;

    /** AI 割り込みの黄字警告を既に出したか (チャットは 1 回だけ、ログは毎回)。 */
    private static boolean interferenceWarned = false;
    /**
     * サーバスレッドが検出した割り込み回数の受け渡し箱。
     * チャットへの出力はクライアントスレッドで行う必要があるので、ここへ積んで
     * {@link #drainDriftReports()} が拾う。
     */
    private static final AtomicInteger driftEvents = new AtomicInteger(0);
    /** 割り込みの累計 (要約行に出す)。 */
    private static int driftTotal = 0;

    // ---- 索引 (int 系のメタデータだけ。頂点データは持たない) ----
    private static final List<Integer> slots = new ArrayList<>();
    private static final List<Integer> frameLens = new ArrayList<>();
    private static final List<int[]> frameGlens = new ArrayList<>();
    private static final List<int[]> frameGtex = new ArrayList<>();
    private static final LinkedHashMap<String, Integer> textureTable = new LinkedHashMap<>();
    private static final List<SimAnimManifest.AnimRange> animRanges = new ArrayList<>();

    @Nullable
    private static Path outJson = null;
    @Nullable
    private static Path outBin = null;
    @Nullable
    private static Path outAnims = null;

    // =========================================================================
    // 開始 / 停止
    // =========================================================================

    /**
     * 近くの霊夢 (reimu host) を探す。{@code SimPoseTrace.findReimu()} と同型の実装を
     * このクラス内に持つ (元ファイルは無改変対象のため呼べない)。
     */
    @Nullable
    private static Entity findReimu() {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null || mc.player == null) {
            return null;
        }
        Entity best = null;
        double bestD = SEARCH_RADIUS * SEARCH_RADIUS;
        for (Entity e : mc.level.entitiesForRendering()) {
            if (!(e instanceof IReimuMaidHost h) || !h.isReimuMaidHost()) {
                continue;
            }
            double d = e.distanceToSqr(mc.player);
            if (d < bestD) {
                bestD = d;
                best = e;
            }
        }
        return best;
    }

    /**
     * sweep を開始する。
     *
     * @param ticksPerAnimArg 1 本のアニメを録る tick 数
     * @return 開始できたら {@code null}、無理ならそのままチャットへ出せる理由
     */
    @Nullable
    public static String start(int ticksPerAnimArg) {
        if (active) {
            return "すでに実行中 (/tlmsim animsweep stop で打ち切れる)";
        }
        Entity r = findReimu();
        if (r == null) {
            return "近くに霊夢が居ない (半径 " + (int) SEARCH_RADIUS + ")";
        }
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null || mc.player == null) {
            return "ワールドに居ない";
        }
        if (mc.getSingleplayerServer() == null) {
            return "統合サーバが無い (マルチ接続中は非対応。ysm play はサーバ側の霊夢から送る)";
        }
        if (!(r instanceof EntityMaid maid)) {
            return "対象が EntityMaid ではない (" + r.getType() + ")";
        }
        String modelId = maid.getYsmModelId();
        if (!maid.isYsmModel() || modelId == null || modelId.isBlank()) {
            return "対象が YSM モデルではない (isYsmModel=" + maid.isYsmModel()
                    + ", ysmModelId='" + modelId + "')";
        }

        Path customDir = mc.gameDirectory.toPath();
        for (String seg : YSM_CUSTOM_DIR) {
            customDir = customDir.resolve(seg);
        }
        Path packRoot = SimAnimManifest.resolvePackRoot(customDir, modelId);
        if (packRoot == null) {
            List<String> tried = SimAnimManifest.candidateNames(modelId);
            return "YSM パックが見つからない (ysm.json を持つディレクトリとして "
                    + customDir.resolve(tried.get(0)) + " と "
                    + customDir.resolve(tried.get(1)) + " を試した)";
        }

        Map<String, Double> lengths;
        try {
            lengths = SimAnimManifest.listAnimationLengths(packRoot);
        } catch (IOException e) {
            return "アニメーション一覧を作れない: " + e.getMessage();
        }
        List<String> names = new ArrayList<>(lengths.keySet());
        if (names.isEmpty()) {
            return "アニメーションが 1 本も無い: " + packRoot;
        }

        // 冪等性ゲート (SimPoseTrace.start() と同じ考え方): 同一呼び出し内で 2 回続けて撮り、
        // 一致しなければ「二重 render が YSM の内部状態を進めている」ので記録を始めない。
        // 一致した 1 枚目は、1 本目のアニメが実際に効いたかを見る基準値としても使う。
        SimModelDump.Shot s1 = SimModelDump.shoot(r);
        SimModelDump.Shot s2 = SimModelDump.shoot(r);
        if (s1 == null || s2 == null) {
            return "shoot() が null を返した (描画できない状態)";
        }
        if (!SimPoseCodec.same(s1.verts(), s2.verts())) {
            int mismatch = 0;
            int len = Math.min(s1.verts().length, s2.verts().length);
            for (int i = 0; i < len; i++) {
                if (Math.abs(s1.verts()[i] - s2.verts()[i]) > 1.0e-4F) {
                    mismatch++;
                }
            }
            TouhouLittleMaid.LOGGER.error(
                    "[SIM] animsweep idempotency gate failed: {}/{} elements mismatched", mismatch, len);
            return "冪等性ゲート失敗: 不一致要素数 " + mismatch + "/" + len;
        }

        target = r;
        targetEntityId = r.getId();
        animNames = names;
        animLengths = lengths;
        animIndex = 0;
        ticksPerAnim = ticksPerAnimArg;
        phase = Phase.SEND;
        wait = 0;
        capturedThisAnim = 0;
        frameCounter = 0;
        currentAnimFromFrame = 0;
        failedSends = 0;
        gt0 = mc.level.getGameTime();
        type = String.valueOf(BuiltInRegistries.ENTITY_TYPE.getKey(r.getType()));
        texture = s1.texture();
        vertsPerFrame = SimVertexRecorder.STRIDE > 0 ? s1.verts().length / SimVertexRecorder.STRIDE : 0;
        baselineVerts = s1.verts();
        firstAnimBaselineChecked = false;
        interferenceLogged = false;
        interferenceWarned = false;
        driftEvents.set(0);
        driftTotal = 0;
        slots.clear();
        frameLens.clear();
        frameGlens.clear();
        frameGtex.clear();
        textureTable.clear();
        animRanges.clear();

        String stamp = new SimpleDateFormat("yyyyMMdd-HHmmss", Locale.ROOT).format(new Date());
        Path dir = SimPoseTrace.outDir();
        outJson = dir.resolve(stamp + ".pose.json");
        outBin = dir.resolve(stamp + ".pose.bin");
        outAnims = dir.resolve(stamp + ".anims.json");
        try {
            Files.createDirectories(dir);
            Files.deleteIfExists(outBin);
        } catch (IOException e) {
            TouhouLittleMaid.LOGGER.error("[SIM] animsweep output dir prepare failed", e);
            target = null;
            return "出力先の準備に失敗: " + e.getMessage();
        }

        active = true;
        int estSec = animNames.size() * (SETTLE_TICKS + ticksPerAnim) / 20;
        say(ChatFormatting.GRAY, "[SIM] animsweep開始: " + animNames.size() + "本、推定 " + estSec + "秒。"
                + "1本目の送信に失敗したら直ちに中断する。/tlmsim animsweep stop で打ち切れる");
        TouhouLittleMaid.LOGGER.info(
                "[SIM] animsweep start: {} anims, {} ticks/anim, settle {}, pack {} -> {}",
                animNames.size(), ticksPerAnim, SETTLE_TICKS, packRoot, outJson);
        return null;
    }

    /**
     * 実行中の sweep を安全に打ち切る ({@code SimPoseTrace.stop()} と同型の薄いラッパ)。
     * それまでのチェックポイント書き出しがそのまま最終成果物になる。
     */
    public static void stop() {
        if (!active) {
            say(ChatFormatting.GRAY, "[SIM] animsweep は実行されていない");
            return;
        }
        say(ChatFormatting.GRAY, "[SIM] animsweep を打ち切る");
        finish();
    }

    // =========================================================================
    // 送信 (証明済み API を呼ぶだけ)
    // =========================================================================

    /**
     * 統合サーバ側で、クライアントの {@code entityId} に対応する {@link EntityMaid} を解決し、
     * {@code action} を<b>サーバスレッド上で</b>実行する。
     *
     * <p>エンティティの解決を {@code server.execute()} の<b>内側</b>で行うのが要点 ——
     * サーバ側の world からエンティティを引く操作をクライアントスレッドから行うと、
     * 起きたときに再現しない類の競合になる。
     */
    /** spike 004 の {@link SimBoneCapture} も同じ経路を使う —— 複製しないため package-private。 */
    /**
     * spike 004 の {@link SimBoneCapture} も同じ経路を使うので package-private。
     * <b>証明済みのものを呼ぶ。複製しない</b>（このクラスの冒頭と同じ理由）。
     */
    static void withServerMaid(LocalPlayer player, int entityId, Consumer<EntityMaid> action) {
        MinecraftServer server = Minecraft.getInstance().getSingleplayerServer();
        if (server == null) {
            return;
        }
        UUID uuid = player.getUUID();
        server.execute(() -> {
            ServerPlayer sp = server.getPlayerList().getPlayer(uuid);
            if (sp == null) {
                return;
            }
            if (sp.serverLevel().getEntity(entityId) instanceof EntityMaid maid) {
                action.accept(maid);
            }
        });
    }

    /**
     * 1 本のアニメを送る。
     *
     * <p><b>戻り値 {@code true} は「サーバスレッドへ積めた」ことの証明であって、
     * 「霊夢に効いた」ことの証明ではない</b> ({@code server.execute()} は非同期)。
     * 効いたかどうかは {@link #checkFirstAnimBaseline} の頂点比較が別途担当する。
     * ここで検出できるのは<b>統合サーバ不在</b>と<b>サーバ側プレイヤー未検出</b>の 2 つだけ。
     */
    private static boolean fireAnimOnServer(LocalPlayer player, int entityId, String animName) {
        MinecraftServer server = Minecraft.getInstance().getSingleplayerServer();
        if (server == null) {
            TouhouLittleMaid.LOGGER.error("[SIM] animsweep: 統合サーバが無い ('{}' を送れない)", animName);
            return false;
        }
        if (server.getPlayerList().getPlayer(player.getUUID()) == null) {
            TouhouLittleMaid.LOGGER.error(
                    "[SIM] animsweep: サーバ側プレイヤーが見つからない ('{}' を送れない)", animName);
            return false;
        }
        withServerMaid(player, entityId, maid -> maid.playReimuMaidAnimation(animName, true));
        return true;
    }

    /**
     * 霊夢自身の AI が別のアニメを送っていたら、同じ API で送り直す (自己修復)。
     * <b>一致している限り何もしない</b> —— 毎 tick 送り直すとアニメが毎 tick 頭から
     * 再生されてしまい、アニメ自身の時間経過が録れなくなる。
     */
    private static void reassertAnimIfDrifted(LocalPlayer player, int entityId, String animName) {
        withServerMaid(player, entityId, maid -> {
            String current = maid.reimuExt().lastPlayedReimuAnim;
            if (animName.equals(current)) {
                return;
            }
            maid.playReimuMaidAnimation(animName, true);
            int n = driftEvents.incrementAndGet();
            // **初回だけ warn。以降は debug。** 割り込みは毎tick起こりうるので、無条件に warn を
            // 出すと 7 分の sweep で数千行のログスパムになり、まさにその割り込みを診断するために
            // 読みたい latest.log を自分で埋めてしまう
            // (commit 6cb9ac3e で shoot() の衝突検出について直したのと同じ轍。
            //  quick 260819-o9l の code-review WR-02)。総数は finish() の報告に出る。
            if (n == 1 && !interferenceLogged) {
                interferenceLogged = true;
                TouhouLittleMaid.LOGGER.warn(
                        "[SIM] animsweep: 霊夢自身のAIが '{}' へ割り込んだため '{}' を送り直した"
                                + " (以降は debug。総数は終了報告に出る)", current, animName);
            } else {
                TouhouLittleMaid.LOGGER.debug(
                        "[SIM] animsweep: AI割り込み '{}' -> '{}' を送り直した", current, animName);
            }
        });
    }

    /** サーバスレッドが積んだ割り込み検出を拾い、初回だけチャットへ出す (沈黙しない)。 */
    private static void drainDriftReports() {
        int d = driftEvents.getAndSet(0);
        if (d <= 0) {
            return;
        }
        driftTotal += d;
        if (!interferenceWarned) {
            interferenceWarned = true;
            say(ChatFormatting.YELLOW,
                    "[SIM] 霊夢自身のAIが割り込んだため animsweep が送り直した（録り直しが必要な可能性）");
        }
    }

    // =========================================================================
    // tick 駆動の状態機械
    // =========================================================================

    @SubscribeEvent
    public static void onClientTick(TickEvent.ClientTickEvent event) {
        if (!active || event.phase != TickEvent.Phase.END) {
            return;
        }
        try {
            step();
        } catch (Throwable t) {
            TouhouLittleMaid.LOGGER.error("[SIM] animsweep step failed", t);
            say(ChatFormatting.RED, "[SIM] animsweep に失敗: " + t);
            finish();
        }
    }

    private static void step() {
        if (target == null || !target.isAlive()) {
            say(ChatFormatting.YELLOW, "[SIM] 対象の霊夢が居なくなったので animsweep を止めた");
            finish();
            return;
        }
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null || mc.player == null) {
            finish();
            return;
        }
        drainDriftReports();

        String animName = animNames.get(animIndex);

        if (wait > 0) {
            // settle 待ちの間も割り込みを監視する (待っている間に AI が上書きしたら、
            // 録り始めた時点で既に別のアニメになっている)。
            wait--;
            reassertAnimIfDrifted(mc.player, targetEntityId, animName);
            if (wait == 0) {
                capturedThisAnim = 0;
                currentAnimFromFrame = frameCounter;
                phase = Phase.CAPTURE;
            }
            return;
        }

        if (phase == Phase.SEND) {
            sendCurrentAnim(mc.player, animName);
            return;
        }
        if (phase == Phase.CAPTURE) {
            captureTick(mc.player, animName);
        }
    }

    /** SEND: 進捗を出し、1 回だけ送る。1 本目の送信失敗だけは全体を即座に中断する。 */
    private static void sendCurrentAnim(LocalPlayer player, String animName) {
        say(ChatFormatting.GRAY, "[SIM] animsweep " + (animIndex + 1) + "/" + animNames.size()
                + ": " + animName);
        TouhouLittleMaid.LOGGER.info("[SIM] animsweep {}/{}: {}", animIndex + 1, animNames.size(), animName);

        boolean sent = fireAnimOnServer(player, targetEntityId, animName);
        if (!sent && animIndex == 0) {
            say(ChatFormatting.RED,
                    "[SIM] animsweep 中断: 統合サーバまたはサーバ側プレイヤーが見つからず1本目を送れなかった");
            TouhouLittleMaid.LOGGER.error(
                    "[SIM] animsweep aborted: 統合サーバまたはサーバ側プレイヤーが見つからず1本目 '{}' を送れなかった",
                    animName);
            finish();
            return;
        }
        if (!sent) {
            failedSends++;
            TouhouLittleMaid.LOGGER.warn(
                    "[SIM] animsweep: {} の送信に失敗、この1本は0フレームで次へ進む", animName);
            advanceToNextAnim(false);
            return;
        }
        phase = Phase.WAIT_SETTLE;
        wait = SETTLE_TICKS;
    }

    /** CAPTURE: 割り込みを見張りつつ 1 枚撮り、ディスクへ追記する。 */
    private static void captureTick(LocalPlayer player, String animName) {
        reassertAnimIfDrifted(player, targetEntityId, animName);

        SimModelDump.Shot shot = SimModelDump.shoot(target);
        if (shot == null) {
            // 描画できなかった tick。記録を欠落させるが sweep 自体は続ける。
            slots.add(-1);
        } else {
            if (texture == null) {
                texture = shot.texture();
            }
            if (vertsPerFrame < 0) {
                vertsPerFrame = SimVertexRecorder.STRIDE > 0
                        ? shot.verts().length / SimVertexRecorder.STRIDE : 0;
            }
            checkFirstAnimBaseline(shot);
            appendShot(shot);
        }

        capturedThisAnim++;
        if (capturedThisAnim >= ticksPerAnim) {
            advanceToNextAnim(true);
        }
    }

    /**
     * 1 枚を bin へ追記し、索引 3 種を<b>同じ分岐で</b>積む。
     *
     * <p>この「同じ分岐で積む」が要 —— 別の場所に置くと bin の並びと {@code lens} の並びが
     * ずれ、Viewer が可変長フレームを誤った位置から切り出す (quick 260818-6cj の判例)。
     * デデュープを行わないので、ここは条件なしに毎回通る。
     */
    private static void appendShot(SimModelDump.Shot shot) {
        if (outBin == null) {
            return;
        }
        try {
            SimPoseCodec.appendFrame(outBin, shot.verts());

            frameLens.add(SimVertexRecorder.STRIDE > 0
                    ? shot.verts().length / SimVertexRecorder.STRIDE : 0);

            List<SimModelDump.Group> groups = shot.groups();
            int[] glens = new int[groups.size()];
            int[] gtex = new int[groups.size()];
            for (int i = 0; i < groups.size(); i++) {
                SimModelDump.Group g = groups.get(i);
                glens[i] = g.verts();
                String texId = g.texture();
                if (texId == null) {
                    texId = shot.texture();
                }
                if (texId == null) {
                    texId = "";
                }
                gtex[i] = textureTable.computeIfAbsent(texId, k -> textureTable.size());
            }
            frameGlens.add(glens);
            frameGtex.add(gtex);

            slots.add(frameCounter);
            frameCounter++;
        } catch (IOException e) {
            TouhouLittleMaid.LOGGER.error("[SIM] animsweep bin append failed", e);
            slots.add(-1);
        }
    }

    /**
     * 1 本目のアニメが実際に効いたかを 1 度だけ確かめる。
     * 開始前 (どのアニメも送る前) の頂点と同一なら、コマンドは受理されたのに霊夢へ届いて
     * いない可能性が高い —— 316 本を黙って録り続ける前に知らせる。
     */
    /**
     * 「アニメが効いた」と見なす、動いた頂点の最小割合。
     *
     * <p><b>なぜ「差があるか」では駄目か</b>: このコードベースは
     * {@code SimPoseCodec.quantize()} の javadoc で<b>idle でも頂点が微細に揺らぐ</b>ことを
     * 既知の落とし穴 (Pitfall 1) として記録している。髪・リボンのばね物理は待機中も動くので、
     * {@code same()} の 1e-4 判定では「揺らいだ ＝ アニメが効いた」と誤判定しうる
     * (quick 260819-o9l の code-review WR-01)。
     *
     * <p>アニメが本当に切り替われば<b>体の大半</b>が動く。揺らぎは<b>末端の一部</b>しか動かさない。
     * だから「どれだけの頂点が意味のある距離だけ動いたか」で分ける。
     */
    private static final double MOVED_FRACTION_MIN = 0.20;

    /** 意味のある移動と見なす距離 (ブロック)。1/16 ブロック = 1 ピクセルなので、その 1/3 程度。 */
    private static final double MOVED_EPS = 0.02;

    /**
     * 2 枚の頂点配列で、{@link #MOVED_EPS} 以上動いた頂点の割合を返す。
     * 長さが違えば形そのものが変わっているので {@code 1.0} (＝完全に動いた) とみなす。
     */
    private static double movedFraction(float[] a, float[] b) {
        if (a == null || b == null || a.length != b.length) {
            return 1.0;
        }
        final int stride = SimVertexRecorder.STRIDE;
        if (stride <= 0 || a.length < stride) {
            return 1.0;
        }
        int total = 0, moved = 0;
        for (int i = 0; i + stride <= a.length; i += stride) {
            total++;
            double dx = a[i] - b[i], dy = a[i + 1] - b[i + 1], dz = a[i + 2] - b[i + 2];
            if (dx * dx + dy * dy + dz * dz > MOVED_EPS * MOVED_EPS) {
                moved++;
            }
        }
        return total == 0 ? 1.0 : (double) moved / total;
    }

    private static void checkFirstAnimBaseline(SimModelDump.Shot shot) {
        if (firstAnimBaselineChecked || animIndex != 0 || capturedThisAnim != 0 || baselineVerts == null) {
            return;
        }
        firstAnimBaselineChecked = true;
        double moved = movedFraction(baselineVerts, shot.verts());
        if (moved < MOVED_FRACTION_MIN) {
            say(ChatFormatting.YELLOW,
                    "[SIM] 1本目のアニメを送っても姿勢がほとんど変わっていない（ysm play が効いていない可能性）");
            TouhouLittleMaid.LOGGER.warn(
                    "[SIM] animsweep: 動いた頂点 {}% (しきい値 {}%) — ysm play が効いていない可能性 (anim '{}')",
                    String.format(Locale.ROOT, "%.1f", moved * 100),
                    String.format(Locale.ROOT, "%.0f", MOVED_FRACTION_MIN * 100),
                    animNames.get(0));
        } else {
            TouhouLittleMaid.LOGGER.info(
                    "[SIM] animsweep: 動いた頂点 {}% — ysm play は効いている",
                    String.format(Locale.ROOT, "%.1f", moved * 100));
        }
        // 判定が済んだら 1MB 級の配列を抱え続けない。
        baselineVerts = null;
    }

    /**
     * 今のアニメを閉じて次へ進む。閉じるたびに索引と {@code .anims.json} を書き直す
     * (完了アニメ単位のチェックポイント) —— 途中で Minecraft が落ちても、
     * 失うのは「録り途中の 1 本」だけになる。
     *
     * @param recorded 実際に録れたか ({@code false} = 送信に失敗して 0 フレームだった)
     */
    private static void advanceToNextAnim(boolean recorded) {
        String animName = animNames.get(animIndex);
        if (recorded && frameCounter > currentAnimFromFrame) {
            animRanges.add(new SimAnimManifest.AnimRange(
                    animName, currentAnimFromFrame, frameCounter - 1,
                    animLengths.getOrDefault(animName, 0.0)));
        }
        // 1 本目が 1 フレームも録れなかった場合、checkFirstAnimBaseline が呼ばれないまま
        // 1MB 級の配列を抱え続けることになる。ここで必ず手放す
        // (quick 260819-o9l の code-review WR-03)。
        if (animIndex == 0) {
            firstAnimBaselineChecked = true;
            baselineVerts = null;
        }

        writeOutputs();

        animIndex++;
        capturedThisAnim = 0;
        currentAnimFromFrame = frameCounter;
        if (animIndex >= animNames.size()) {
            finish();
            return;
        }
        phase = Phase.SEND;
        wait = 0;
    }

    private static void finish() {
        active = false;
        drainDriftReports();
        writeOutputs();

        say(ChatFormatting.GREEN, "[SIM] animsweep終了: アニメ " + animRanges.size() + "/"
                + animNames.size() + "本 / フレーム " + frameCounter + "枚 / 送信失敗 " + failedSends
                + "本 / AI割り込み " + driftTotal + "回");
        if (outBin != null) {
            try {
                long size = Files.exists(outBin) ? Files.size(outBin) : 0L;
                say(ChatFormatting.DARK_GRAY, "  -> " + outJson + " (" + size + " bytes)");
            } catch (IOException ignored) {
                say(ChatFormatting.DARK_GRAY, "  -> " + outJson);
            }
        }
        say(ChatFormatting.DARK_GRAY, "  -> " + outAnims);
        TouhouLittleMaid.LOGGER.info(
                "[SIM] animsweep done: {}/{} anims, {} frames, {} send failures, {} AI interruptions -> {}",
                animRanges.size(), animNames.size(), frameCounter, failedSends, driftTotal, outJson);
        target = null;
    }

    // =========================================================================
    // 書き出し (チェックポイントと最終書き出しで共有する)
    // =========================================================================

    /** 索引と {@code .anims.json} を書く。チェックポイントと {@link #finish()} が同じものを呼ぶ。 */
    private static void writeOutputs() {
        writeIndex();
        writeAnims();
    }

    private static void writeIndex() {
        if (outJson == null || outBin == null) {
            return;
        }
        int[] slotArr = new int[slots.size()];
        for (int i = 0; i < slotArr.length; i++) {
            slotArr[i] = slots.get(i);
        }
        int[] lensArr = new int[frameLens.size()];
        for (int i = 0; i < lensArr.length; i++) {
            lensArr[i] = frameLens.get(i);
        }

        SimPoseCodec.Groups groups = null;
        if (frameGlens.size() != frameLens.size() || frameGtex.size() != frameLens.size()) {
            TouhouLittleMaid.LOGGER.warn(
                    "[SIM] animsweep: グループ表の本数 (glens {} / gtex {}) が lens ({}) と食い違うため"
                            + "グループ表なしで索引を書く",
                    frameGlens.size(), frameGtex.size(), frameLens.size());
        } else {
            groups = new SimPoseCodec.Groups(
                    frameGlens.toArray(new int[0][]),
                    frameGtex.toArray(new int[0][]),
                    textureTable.keySet().toArray(new String[0]));
        }

        // quant=0 固定 (量子化はデデュープの精度を上げる機構で、デデュープしない本経路では無関係)。
        // idempotent=true 固定 (ゲートを通った場合しかここへ来ない)。
        SimPoseCodec.Header header = new SimPoseCodec.Header(
                1, gt0, targetEntityId, type, texture,
                SimVertexRecorder.STRIDE, Math.max(vertsPerFrame, 0), 0,
                true, frameLens.size(), outBin.getFileName().toString());
        try {
            SimPoseCodec.writeIndex(outJson, header, slotArr, lensArr, groups);
        } catch (IOException e) {
            TouhouLittleMaid.LOGGER.error("[SIM] animsweep index write failed: {}", outJson, e);
            say(ChatFormatting.RED, "[SIM] 索引の書き出しに失敗: " + e.getMessage());
        }
    }

    private static void writeAnims() {
        if (outAnims == null) {
            return;
        }
        try {
            SimAnimManifest.writeAnimsCompanion(outAnims, animRanges);
        } catch (IOException e) {
            TouhouLittleMaid.LOGGER.error("[SIM] animsweep anims companion write failed: {}", outAnims, e);
            say(ChatFormatting.RED, "[SIM] アニメ範囲の書き出しに失敗: " + e.getMessage());
        }
    }

    private static void say(ChatFormatting color, String msg) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player != null) {
            mc.player.displayClientMessage(Component.literal(msg).withStyle(color), false);
        }
    }
}
