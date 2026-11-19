package com.github.tartaricacid.touhoulittlemaid.sim.client;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import com.github.tartaricacid.touhoulittlemaid.entity.passive.reimu.IReimuMaidHost;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
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
import java.util.UUID;

/**
 * 霊夢の<b>姿勢</b>を毎tick記録するクライアント側レコーダ (09-CONTEXT.md D-01 の実装本体)。
 *
 * <p>{@link SimPoseDump} が「molang 式を送って {@code SETTLE_TICKS} 待ってから 1 枚録る」
 * オフライン収集器なのに対し、こちらは「今動いている霊夢を毎tick録り続ける」——
 * tick を跨いだ姿勢の連続再生 (VIEW-02) 用のオンライン収集器。中身は同じ
 * {@link SimModelDump#shoot(Entity)} を使い、同じ 1.0e-4 のデデュープ規則
 * ({@link SimPoseCodec#same}) で相異なるフレームだけを bin へ書く。
 * {@link SimPoseDump} / {@link SimModelDump} / {@link SimVertexRecorder} は
 * <b>変更しない</b> —— 実機の描画結果を変えないことを、そもそも触らないことで保証する。
 *
 * <h3>companion 形式 v1</h3>
 * 出力は 2 ファイル 1 組 ({@code <gameDir>/simlab/poses/<stamp>.pose.json} /
 * {@code .pose.bin})。スキーマは {@link SimPoseCodec} と
 * {@link com.github.tartaricacid.touhoulittlemaid.sim.trace.SimCh#POSE} の javadoc を参照。
 * tick の突き合わせは companion の {@code gt0} と本体 trace の {@code meta.gameTime} —
 * {@code t = gameTime - gt0}。
 *
 * <h3>冪等性ゲート (RESEARCH Pitfall 3)</h3>
 * {@link #start(int)} は記録を始める前に、同一 tick 内 (同期呼び出し内) で {@code shoot()}
 * を 2 回連続で呼び、頂点が完全一致するか確認する。一致しなければ「二重 render が YSM
 * の内部状態を進めている」と判断し、<b>記録を開始せず</b>理由を返す
 * —— 沈黙で先へ進まないための安全弁 (方式の前提が崩れたら にーくら へ判断を戻す)。
 *
 * <h3>頭向き (RESEARCH Pitfall 2)</h3>
 * {@code shoot()} は yHeadRot を yBodyRot と同じ値に揃えて撮る (head-body デルタが常に 0)
 * ため、このクラスが録る頂点には頭の向きが含まれない。Viewer 側 (gl.js) が既存の
 * {@code headMatrix()} で頭だけ別途回す前提で、ここでは意図的に直さない
 * (計画 09-01 Task 1 §3。実装コストゼロの解)。
 *
 * <h3>多方向撮影 (quick 260818-x0k)</h3>
 * {@code shoot()} は同一 tick 内 (同一呼び出し内) で yaw=0/180 の 2 方向を撮り、
 * 180° 側を符号反転のみの厳密な逆回転で yaw=0 の座標系へ戻して連結する ——
 * YSM native のバックフェースカリングが「表を向いている面」しか吐かないため。
 * 効いたかどうかは {@link #logDirectionSummary} が出す
 * {@code [SIM] pose shot: dirA … / dirB …} 行と、方向Bが方向Aの複製だった場合の
 * 衝突警告行で判別する (実機でしか判らないので、沈黙させない)。
 *
 * <h3>上限 (RESEARCH Pitfall 1 の保険)</h3>
 * 相異なるフレーム数が {@link #PROP_MAX_FRAMES} (既定 96) に達したら<b>頂点記録だけ</b>を
 * 止め、黄字で警告する。<b>run そのものは終わらない</b> —— {@link SimPaletteTrace} は
 * {@code EntityMaidRenderer} の実描画経路から独立に録られており、頂点の上限で道連れに
 * する理由が無いため (それが 1 run = 約 5 秒という壁の正体だった)。上限後は
 * {@code slots} を<b>伸ばさない</b>: 範囲内に {@code -1} を積むと Viewer の
 * {@code poseTraceParts()} がそれを直前の有効フレームで backfill し、上限時の古い 1 枚を
 * 貼り続ける (gl.js:995-1017 の注記、2026-08-19 の夢想封印と同じ嘘)。範囲外なら
 * Viewer は {@code null} を返してアニメライブラリ/再構成へ落ちる。
 * 既存フレームを間引いたり近いフレームで代用したりしない
 * (嘘のデータを作らない)。<b>上限に早く到達する主因は量子化ではなく、持ち物・レイヤー・
 * spell circle・隠しパーツの有無で頂点数がフレームごとに変わり、{@link SimPoseCodec#same}
 * の長さ比較で常に別フレーム扱いになること</b> (quick 260818-6cj で確定)。
 * {@code -Dtlm.sim.poseframes=<N>} で上限そのものを上げられる。
 *
 * <h3>フレームごとの頂点数 (quick 260818-6cj)</h3>
 * {@code SimModelDump.shoot()} が実際にレンダラの吐いた頂点を拾うため、頂点数は tick ごとに
 * 変わりうる。旧形式は {@code Header.verts}(先頭フレームの頂点数)ひとつだけを信じて
 * 固定幅で bin を切っていたため、頂点数が変わった後のフレームはずれた位置から読まれていた。
 * {@link #frameLens} が格納フレームごとの頂点数を {@code appendFrame} と同じ分岐で積み、
 * {@link SimPoseCodec.Index#lens} として書き出すことで Viewer 側が可変オフセットで
 * 正しく切り出せるようにする。
 */
@Mod.EventBusSubscriber(modid = TouhouLittleMaid.MOD_ID, value = Dist.CLIENT)
public final class SimPoseTrace {

    /**
     * 何を録るか。
     *
     * <p><b>{@code poseFull} を流用しない。</b> あちらは「頂点が上限に達した」という
     * <b>途中で起きる事象</b>で、こちらは「最初から頂点を録らない」という<b>開始時の選択</b>。
     * 混ぜると {@code finish()} が 0 フレームの索引を書いて「頂点は上限で打ち切り」と
     * <b>誤報する</b> (2026-08-25 の審査で指摘)。
     */
    public enum CaptureMode {
        /** 頂点と palette の両方。従来どおり。 */
        POSE_AND_PALETTE,
        /**
         * palette だけ。水槽向け。
         *
         * <p>2026-08-25 に palette が最上位の姿勢源になった (にーくら判定) 以降、
         * 水槽で頂点を録る理由が無くなった —— 上限まで録っても run あたり約 128MB の
         * 死荷重で、しかも毎 tick の {@code shoot()} を払う。
         *
         * <p><b>palette を回すのはこのクラスではない。</b>
         * {@code EntityMaidRenderer} の描画後フックから {@link SimPaletteTrace#afterRender}
         * が呼ばれる。ここが貸すのは start/checkpoint/finish のライフサイクルだけで、
         * <b>実際に採れるのはクライアントが霊夢を描いた tick に限られる</b>
         * (視錐台カリングを受け、最小化中はゼロ)。被覆は {@code .pal.json} の
         * {@code slots} から数える —— 終了ログの frames:ticks は構造上つねに 1.000。
         */
        PALETTE_ONLY,
    }

    /** いまの記録の {@link CaptureMode}。{@code start} で決まる。 */
    private static CaptureMode mode = CaptureMode.POSE_AND_PALETTE;

    /**
     * 自動開始のプロパティ名。<b>既定 off</b>。{@code -Dtlm.sim.autopose=1} で入る。
     *
     * <p><b>なぜ既定 off か</b>: これはクライアント側の勝手な書き込みで、sim を起動して
     * いない通常のゲームで動いてはならない。{@code SimTuningGuardTest} と同じ
     * 「素通し保証」の流儀 —— 明示的に頼まれない限り 1 バイトも書かない。
     *
     * <p><b>サーバの状態は見ない。</b> 水槽は専用サーバで、クライアントは別プロセス。
     * {@code SimLab.enabled()} は JVM 内の static なのでクライアント側では常に偽で、
     * 判定に使えない (2026-08-25 の審査で指摘)。使えるのは「このクライアントに
     * そう頼まれたか」と「近くに霊夢が居るか」だけ。
     */
    public static final String PROP_AUTOPOSE = "tlm.sim.autopose";

    /**
     * 手動 {@link #stop()} の後は自分から再開しない錠。
     * これが無いと「止めた」の次の tick で勝手に録り直す。ワールドを出ると外れる。
     */
    private static boolean autoLatched = false;

    /**
     * 自動開始を既に試した霊夢の UUID。<b>1 run・1 UUID につき 1 回だけ</b>試す ——
     * 失敗する状況 (描画できない等) で毎 tick 試すとログとチャットが溢れる。
     */
    @Nullable
    private static UUID autoTriedFor = null;

    /** 相異なるフレーム数の上限 (システムプロパティ名)。既定 {@value #DEFAULT_MAX_FRAMES}。 */
    public static final String PROP_MAX_FRAMES = "tlm.sim.poseframes";
    private static final int DEFAULT_MAX_FRAMES = 96;

    /** 霊夢を探す半径。{@code SimPoseDump.SEARCH_RADIUS} と同じ考え方 (SimPoseDump は変更しない)。 */
    private static final double SEARCH_RADIUS = 16.0;

    /** この tick 数ごとに索引を中間保存する。 */
    private static final int CHECKPOINT_EVERY = 100;

    private SimPoseTrace() {}

    // ---- 進行状態 ----
    private static boolean active = false;
    @Nullable
    private static Entity target = null;
    private static long gt0 = 0L;
    private static int quant = 0;
    private static boolean idempotentResult = false;
    /**
     * 頂点記録が上限に達したか。{@code true} の間 {@code shoot()} を呼ばず {@code slots} も
     * 伸ばさないが、tick ループ・{@code captureCtrl}・palette の記録は続く。
     * <b>{@link #start(int)} で必ず {@code false} へ戻す</b> (戻さないと 2 本目が録れない)。
     */
    private static boolean poseFull = false;
    @Nullable
    private static String type = null;
    @Nullable
    private static String texture = null;
    private static int vertsPerFrame = -1;
    private static final List<float[]> frames = new ArrayList<>();
    private static final List<Integer> slots = new ArrayList<>();
    /**
     * 格納フレームごとの頂点数 (フレーム番号→頂点数)。{@code appendFrame} を呼ぶのと同じ分岐で
     * 積むため、bin の並びとこの配列の並びが必ず一致する (quick 260818-6cj)。
     */
    private static final List<Integer> frameLens = new ArrayList<>();
    /**
     * 格納フレームごとの、各グループの頂点数 (quick 260818-oq4)。{@link #frameLens} と同じ分岐
     * ({@code appendFrame} を呼ぶのと同じ if) で積むため、フレーム数・並びが必ず一致する。
     */
    private static final List<int[]> frameGlens = new ArrayList<>();
    /** 格納フレームごとの、各グループのテクスチャ添字 ({@link #textureTable} への添字)。 */
    private static final List<int[]> frameGtex = new ArrayList<>();
    /** テクスチャ id → {@code textures[]} への添字。挿入順を保つ重複除去表。 */
    private static final LinkedHashMap<String, Integer> textureTable = new LinkedHashMap<>();
    /** 直近に観測したグループ内訳の署名。変化検出に使う ({@code null} = まだ観測していない)。 */
    @Nullable
    private static String lastGroupSig = null;
    /**
     * 方向B衝突の警告を既に出したか (quick 260818-x0k)。衝突は決定論的に毎tick起き続けうるので、
     * 「変化したら」ではなく<b>初回だけ</b>知らせる。
     */
    private static boolean collisionWarned = false;
    /** 直近に観測した方向別 (dirA/dirB) サマリの署名。変化検出に使う ({@code null} = 未観測)。 */
    @Nullable
    private static String lastDirSummarySig = null;
    /** グループ内訳の署名が変化した回数 (初回観測を含む)。 */
    private static int groupSigChanges = 0;
    /** 記録中に観測したグループ数の最大値。{@code finish()} の要約行に使う。 */
    private static int maxGroupCount = -1;
    /** 直近 tick の頂点数。{@code -1} = まだ観測していない。頂点数の変化検出に使う。 */
    private static int lastVertCount = -1;
    /** 記録中に頂点数が変化した回数 (毎tickではなく、変化のたびに 1 回)。 */
    private static int vertCountChanges = 0;
    private static int minVertCount = Integer.MAX_VALUE;
    private static int maxVertCount = -1;
    @Nullable
    private static Path outJson = null;
    @Nullable
    private static Path outBin = null;

    /**
     * {@code ctrl.*} の実測値を書く companion (quick 260819)。
     *
     * <p><b>なぜ別ファイルなのか</b>: {@code .pose.json} の形式を一切変えずに済むため。
     * 既存の不変条件 ({@code lens.length == frames}, {@code sum(glens[i]) == lens[i]},
     * {@code sum(lens)*stride*4 == bin バイト数}) にも既存 JUnit にも触れない。
     * 読み手 (Viewer / 採点器) は要るときだけ開けばよい。
     */
    private static Path outCtrl = null;

    /**
     * 1 tick 1 行の JSON。<b>YSM の animation controller が見ているのと同じ値</b>を
     * クライアント側から実測して残す。
     *
     * <p><b>なぜ要るのか</b>: {@code controller/parallel_controllers.json} の遷移条件は
     * {@code ctrl.idle} / {@code ctrl.walk} / {@code ctrl.run} / {@code ctrl.jump} /
     * {@code ctrl.hold('mainhand', ':sword')} などで書かれている。これらを Viewer 側が
     * <b>推測で作ると層が当たらない</b> (2026-08-19 に実測。状態機械は正しく遷移するのに
     * 誤差が改善しなかった)。特に {@code onGround} は<b>クライアント側の値でなければならない</b>
     * ——霊夢は仕様上わずかに浮き、client では常に {@code false} になる (CLAUDE.md の判例)。
     * サーバ側トレース ({@code arena-*.jsonl} の {@code phys.onG}) を使うと取り違える。
     */
    private static final List<String> ctrlLines = new ArrayList<>();
    private static long stepsSinceCheckpoint = 0;

    private static int maxFrames() {
        return Integer.getInteger(PROP_MAX_FRAMES, DEFAULT_MAX_FRAMES);
    }

    /**
     * 近くの霊夢 (reimu host) を探す。{@code SimPoseDump.findReimu()} と同型の実装を
     * このクラス内に持つ ({@code SimPoseDump} は既存の実機動作に触れないため変更しない)。
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
     * 記録を開始する (頂点 + palette)。冪等性ゲートを通ってから状態を初期化する。
     *
     * @param quantDigits 量子化桁数 (0-4、0 = 量子化なし)
     * @return 開始できたら {@code null}、無理なら理由 (そのままチャットへ出せる文言)
     */
    @Nullable
    public static String start(int quantDigits) {
        return start(quantDigits, CaptureMode.POSE_AND_PALETTE);
    }

    /**
     * 記録を開始する。
     *
     * <p>{@link CaptureMode#PALETTE_ONLY} では冪等性ゲートを通さない ——
     * ゲートは「同一 tick 内で 2 回 {@code shoot()} して頂点が一致するか」を見るもので、
     * <b>頂点を録らない記録には意味が無い</b>。索引 ({@code .pose.json} /
     * {@code .pose.bin}) も書かない。
     *
     * @param quantDigits 量子化桁数 (0-4、0 = 量子化なし)。PALETTE_ONLY では未使用
     * @param captureMode 何を録るか
     * @return 開始できたら {@code null}、無理なら理由 (そのままチャットへ出せる文言)
     */
    @Nullable
    public static String start(int quantDigits, CaptureMode captureMode) {
        if (active) {
            return "すでに実行中";
        }
        Entity r = findReimu();
        if (r == null) {
            return "近くに霊夢が居ない (半径 " + (int) SEARCH_RADIUS + ")";
        }
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null) {
            return "ワールドに居ない";
        }

        // PALETTE_ONLY では頂点を一切録らないので、頂点の冪等性を問うゲートは通さない。
        // ここで shoot() を呼ぶと、録らないもののために毎回 2 回描かせることになる。
        SimModelDump.Shot s1 = null;
        if (captureMode == CaptureMode.POSE_AND_PALETTE) {
        // 冪等性ゲート (RESEARCH Pitfall 3): 同一 tick 内で 2 回連続 shoot() し、
        // 頂点が完全一致するか確認する。崩れていたら記録を開始せず、方式の前提が
        // 崩れた事実をそのまま人へ返す。
        s1 = SimModelDump.shoot(r);
        SimModelDump.Shot s2 = SimModelDump.shoot(r);
        if (s1 == null || s2 == null) {
            return "shoot() が null を返した (描画できない状態)";
        }
        boolean idempotent = SimPoseCodec.same(s1.verts(), s2.verts());
        if (!idempotent) {
            int mismatch = 0;
            int len = Math.min(s1.verts().length, s2.verts().length);
            for (int i = 0; i < len; i++) {
                if (Math.abs(s1.verts()[i] - s2.verts()[i]) > 1.0e-4F) {
                    mismatch++;
                }
            }
            say(ChatFormatting.RED, "[SIM] 二重 render が YSM の内部状態を進めている。"
                    + "この経路では記録が実機とズレる (不一致要素数 " + mismatch + "/" + len + ")");
            TouhouLittleMaid.LOGGER.error(
                    "[SIM] pose trace idempotency gate failed: {}/{} elements mismatched", mismatch, len);
            return "冪等性ゲート失敗: 不一致要素数 " + mismatch + "/" + len;
        }
        }

        mode = captureMode;
        target = r;
        quant = quantDigits;
        gt0 = mc.level.getGameTime();
        type = String.valueOf(BuiltInRegistries.ENTITY_TYPE.getKey(r.getType()));
        // s1 は PALETTE_ONLY では null (ゲートを通していない)。索引を書かないので
        // texture / vertsPerFrame / idempotentResult はどこからも読まれない。
        texture = s1 == null ? null : s1.texture();
        vertsPerFrame = s1 == null ? -1
                : (SimVertexRecorder.STRIDE > 0 ? s1.verts().length / SimVertexRecorder.STRIDE : 0);
        idempotentResult = s1 != null;
        frames.clear();
        slots.clear();
        frameLens.clear();
        frameGlens.clear();
        frameGtex.clear();
        textureTable.clear();
        lastGroupSig = null;
        groupSigChanges = 0;
        maxGroupCount = -1;
        collisionWarned = false;
        lastDirSummarySig = null;
        lastVertCount = -1;
        vertCountChanges = 0;
        minVertCount = Integer.MAX_VALUE;
        maxVertCount = -1;
        stepsSinceCheckpoint = 0;
        poseFull = false;

        String stamp = new SimpleDateFormat("yyyyMMdd-HHmmss", Locale.ROOT).format(new Date());
        // **PALETTE_ONLY は頂点の索引を持たない。** null にしておけば writeIndex() が
        // そのまま素通りする (既に null ガードがある) ので、0 フレームの索引という
        // 嘘のファイルを作らずに済む。ctrl companion は残す —— 位置や molang 変数を
        // 毎 tick 持つ軽いファイルで、palette と併せて読む価値がある。
        outJson = captureMode == CaptureMode.PALETTE_ONLY ? null
                : outDir().resolve(stamp + ".pose.json");
        outBin = captureMode == CaptureMode.PALETTE_ONLY ? null
                : outDir().resolve(stamp + ".pose.bin");
        outCtrl = outDir().resolve(stamp + ".ctrl.jsonl");
        ctrlLines.clear();
        try {
            Files.createDirectories(outDir());
            if (outBin != null) {
                Files.deleteIfExists(outBin);
            }
        } catch (IOException e) {
            TouhouLittleMaid.LOGGER.error("[SIM] pose trace output dir prepare failed", e);
            target = null;
            return "出力先の準備に失敗: " + e.getMessage();
        }

        active = true;
        // palette companion (14-02): SimPoseTrace の冪等性ゲートを通した後、同じ stamp/gt0/
        // target を共有させる —— /api/pose の既存 uuid 突き合わせがそのまま両方を解決できる
        // ようにするため (新しい突き合わせ規則を作らない)。tlm.sim.palette=0 なら
        // SimPaletteTrace.start は armed のままにせず何もしない。
        SimPaletteTrace.start(target, gt0, stamp, outDir());
        // 「画面に映したままにすること」は spike 001 が実測で否定した虚偽 — shoot() は
        // EntityRenderDispatcher から取り出したレンダラを自前の PoseStack/Sink で直接呼ぶだけで
        // MC の描画ループに乗らないため、視錐台カリングの影響を受けない。正しい条件は
        // SEARCH_RADIUS による近接だけ (quick 260818-oq4、計画検査の指摘)。
        //
        // ただし別の機構 (YSM native のバックフェースカリング) による向き依存は実在した
        // (quick 260818-x0k)。shoot() が固定の 1 方向 (yaw=0) でしか撮っていなかったため、
        // その 1 方向から見て裏を向いた面が黙って欠落していた。x0k で yaw=0/180 の 2 方向を
        // 同一 shoot() 呼び出し内で撮り、180° 分は符号反転のみで元の座標系へ戻して連結する
        // ことで、向き依存の欠落を軽減した (90°/270° への拡張は将来の課題)。
        // 否定したのは「機構の説明 (視錐台カリング)」であって「現象 (何かが向きに依存して
        // 欠ける)」ではなかった、という区別が要点。
        say(ChatFormatting.GRAY, "[SIM] 姿勢トレース開始 (quant=" + quant + ")。"
                + "霊夢の" + (int) SEARCH_RADIUS + "ブロック以内に居ること"
                + " (頂点記録は画面に映す必要は無い、shoot() は描画ループに乗らない)。"
                + "多方向撮影 (yaw 0/180) でバックフェースカリングによる裏面欠落を軽減済み");
        // **palette は話が別。** shoot() と違い SimPaletteTrace は EntityMaidRenderer の
        // 実描画経路 (geoRender 直後) から採るので、視錐台カリングをまともに受ける。
        // 上の一文は 14-02 で palette が乗った後も更新されていなかった。
        say(ChatFormatting.YELLOW, "[SIM] palette は実描画経路から採る —— "
                + "霊夢を画面内に保つこと。画面外の tick は palette が欠落する "
                + "(欠落は .pal.json の slots の -1 にだけ現れ、終了ログには出ない)");
        return null;
    }

    @SubscribeEvent
    public static void onClientTick(TickEvent.ClientTickEvent event) {
        if (event.phase != TickEvent.Phase.END) {
            return;
        }
        if (!active) {
            maybeAutoStart();
            return;
        }
        try {
            step();
        } catch (Throwable t) {
            TouhouLittleMaid.LOGGER.error("[SIM] pose trace step failed", t);
            say(ChatFormatting.RED, "[SIM] 姿勢トレースに失敗: " + t);
            finish();
        }
    }

    /**
     * グループ内訳を、内訳が変わったとき (初回観測を含む) だけ 1 行ログへ出す
     * (quick 260818-oq4)。黙って連結すると「idle のゆらぎ」という誤診を再び生む
     * (quick 260818-6cj の判例)。
     *
     * <p>内訳の同一性は「グループ数 + 各グループの (頂点数, quad 数, テクスチャ id,
     * RenderType 名)」を連結した署名文字列で判定する。
     */
    private static void logGroupBreakdown(SimModelDump.Shot shot, int tick) {
        List<SimModelDump.Group> groups = shot.groups();
        maxGroupCount = Math.max(maxGroupCount, groups.size());

        StringBuilder sig = new StringBuilder().append(groups.size());
        StringBuilder detail = new StringBuilder();
        for (int i = 0; i < groups.size(); i++) {
            SimModelDump.Group g = groups.get(i);
            sig.append('|').append(g.verts()).append(',').append(g.quads()).append(',')
                    .append(g.texture()).append(',').append(g.type());
            if (i > 0) {
                detail.append(" / ");
            }
            detail.append('[').append(i).append("] quad=").append(g.quads())
                    .append(" verts=").append(g.verts())
                    .append(" tex=").append(g.texture())
                    .append(" type=").append(g.type());
        }
        String signature = sig.toString();
        if (signature.equals(lastGroupSig)) {
            return;
        }
        boolean firstObservation = lastGroupSig == null;
        lastGroupSig = signature;
        groupSigChanges++;
        TouhouLittleMaid.LOGGER.info("[SIM] pose trace: グループ {} 個 (tick {}): {}",
                groups.size(), tick, detail);
        if (firstObservation) {
            say(ChatFormatting.GRAY, "[SIM] グループ " + groups.size() + " 個を記録している");
        }
    }

    /**
     * 多方向撮影 (quick 260818-x0k) の結果を沈黙させないためのログ。2 つを出す。
     *
     * <p><b>衝突警告 (初回のみ)</b> — 方向Bの回転前の生配列が方向Aと完全一致したグループが
     * あれば、YSM が 2 枚目の render をキャッシュで潰している (＝向きを変えても別の面が
     * 撮れていない) 直接証拠になる。衝突は決定論的に毎tick起き続けうるので、
     * 「変化したら」ではなく初回だけ通知する。
     *
     * <p><b>方向別サマリ (初回＋変化時のみ)</b> — dirA (yaw=0) と dirB (yaw!=0) の
     * verts/quads を突き合わせられるようにする。衝突検出ガードは「完全一致」しか拾えず、
     * 「わずかに違う不完全な複製」までは検出できないため、<b>これが「正しく回った」と
     * 「壊れた重複が足されただけ」を実機で区別する唯一の識別子</b>。
     * dirB が 0 件 (全滅 = 衝突、または LivingEntity でない) でも {@code dirB verts=0 quads=0}
     * として出し、沈黙しない。
     */
    private static void logDirectionSummary(SimModelDump.Shot shot, int tick) {
        if (shot.collisionsDropped() > 0 && !collisionWarned) {
            collisionWarned = true;
            TouhouLittleMaid.LOGGER.warn(
                    "[SIM] pose trace: 方向Bが方向Aと {} 件衝突 (多方向撮影が効いていない可能性)。"
                            + "衝突したグループ: {}",
                    shot.collisionsDropped(), shot.collisionTypes());
            say(ChatFormatting.YELLOW, "[SIM] 多方向撮影が効いていない (YSM が同一結果を返した)");
        }

        int vertsA = 0, quadsA = 0, vertsB = 0, quadsB = 0;
        for (SimModelDump.Group g : shot.groups()) {
            if (g.yawDeg() == 0F) {
                vertsA += g.verts();
                quadsA += g.quads();
            } else {
                vertsB += g.verts();
                quadsB += g.quads();
            }
        }
        String sig = "dirA:" + vertsA + "," + quadsA + "|dirB:" + vertsB + "," + quadsB;
        if (sig.equals(lastDirSummarySig)) {
            return;
        }
        lastDirSummarySig = sig;
        TouhouLittleMaid.LOGGER.info(
                "[SIM] pose shot: dirA verts={} quads={} / dirB verts={} quads={} (tick {})",
                vertsA, quadsA, vertsB, quadsB, tick);
    }

    private static void step() {
        if (target == null || !target.isAlive()) {
            say(ChatFormatting.YELLOW, "[SIM] 対象の霊夢が居なくなったので記録を止めた");
            finish();
            return;
        }
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null) {
            finish();
            return;
        }
        long gt = mc.level.getGameTime();
        int idx = (int) (gt - gt0);
        if (idx < 0) {
            // 時間が巻き戻ることは無いはずだが、念のため無視する。
            return;
        }
        // shoot() は撮影のため向きを一時的に倒す (finally で戻す)。**その前に**捕まえる。
        captureCtrl(idx);

        if (mode == CaptureMode.PALETTE_ONLY) {
            // 頂点は最初から録らない。palette はこの return を通っても録られ続ける
            // (EntityMaidRenderer の描画後フックから独立に走るため)。
            afterStep();
            return;
        }

        if (poseFull) {
            // 頂点は上限で打ち切ってある。**slots を伸ばさない**のがここの要点 ——
            // 伸ばすと Viewer が範囲内の -1 を backfill して古い 1 枚を貼り続ける
            // (クラス javadoc の「上限」節)。shoot() も呼ばないので毎tickの費用も消える。
            // palette はこの return を通っても録られ続ける (実描画経路から独立に走る)。
            afterStep();
            return;
        }

        while (slots.size() <= idx) {
            slots.add(-1);
        }

        SimModelDump.Shot shot = SimModelDump.shoot(target);
        if (shot == null) {
            // 画面外などで描画できなかった tick。記録を欠落させるが記録自体は続行する。
            slots.set(idx, -1);
            afterStep();
            return;
        }

        // この Task が本件の「測定」を兼ねる。黙って連結してはならない (quick 260818-oq4)。
        logGroupBreakdown(shot, idx);
        // 多方向撮影が効いたのか、壊れた重複が足されただけなのかを実機で区別する
        // 唯一の識別子 (quick 260818-x0k)。
        logDirectionSummary(shot, idx);

        if (texture == null) {
            texture = shot.texture();
        }
        if (vertsPerFrame < 0) {
            vertsPerFrame = SimVertexRecorder.STRIDE > 0 ? shot.verts().length / SimVertexRecorder.STRIDE : 0;
        }

        // 頂点数の変動を沈黙させない (quick 260818-6cj): 沈黙していたことが、
        // 原因を idle のゆらぎだと誤診させた張本人。
        int vertCount = SimVertexRecorder.STRIDE > 0 ? shot.verts().length / SimVertexRecorder.STRIDE : 0;
        if (lastVertCount != vertCount) {
            if (lastVertCount >= 0) {
                vertCountChanges++;
                TouhouLittleMaid.LOGGER.info("[SIM] pose trace: 頂点数が {} -> {} に変化 (tick {})",
                        lastVertCount, vertCount, idx);
                if (vertCountChanges == 1) {
                    say(ChatFormatting.YELLOW,
                            "[SIM] フレームごとに頂点数が変わっている (記録は続行する)");
                }
            }
            lastVertCount = vertCount;
        }
        minVertCount = Math.min(minVertCount, vertCount);
        maxVertCount = Math.max(maxVertCount, vertCount);

        float[] verts = quant > 0 ? SimPoseCodec.quantize(shot.verts(), quant) : shot.verts();
        int before = frames.size();
        int slot = SimPoseCodec.slotFor(frames, verts, maxFrames());
        if (slot < 0) {
            poseFull = true;
            // 末尾の未記録 tick を落とし、記録範囲を「最後に本当に録れた tick」で終わらせる。
            // 範囲内に -1 を残すと Viewer がそこを backfill してしまうため
            // (理由の全文と JUnit は SimPoseCodec.trimTrailingUnrecorded に在る)。
            SimPoseCodec.trimTrailingUnrecorded(slots);
            say(ChatFormatting.YELLOW, "[SIM] 頂点記録だけ止めた。palette は続行する —— "
                    + "相異なるフレームが上限 (" + maxFrames() + ") に達した。"
                    + "頂点数がフレームごとに変わると常に別フレーム扱いになり、上限へ早く到達する"
                    + " (ログの『頂点数が…に変化』行を確認すること)。"
                    + "上限自体は -Dtlm.sim.poseframes=<N> で上げられる");
            TouhouLittleMaid.LOGGER.info(
                    "[SIM] pose trace: vertex cap {} reached at tick {} (recorded span now {} ticks);"
                            + " palette recording continues", maxFrames(), idx, slots.size());
            afterStep();
            return;
        }
        slots.set(idx, slot);
        if (frames.size() > before && outBin != null) {
            try {
                SimPoseCodec.appendFrame(outBin, verts);
                // appendFrame と同じ分岐に置くことが要 — 別の場所に置くと bin の並びと
                // lens の並びがずれ、今回のバグを別の形で再発させる (quick 260818-6cj)。
                frameLens.add(SimVertexRecorder.STRIDE > 0 ? verts.length / SimVertexRecorder.STRIDE : 0);

                // glens/gtex も同じ分岐で積む (quick 260818-oq4)。量子化 (quant > 0) は配列長を
                // 変えないので、glens の合計は量子化後もそのフレームの総頂点数に一致する。
                List<SimModelDump.Group> groups = shot.groups();
                int[] glens = new int[groups.size()];
                int[] gtex = new int[groups.size()];
                for (int i = 0; i < groups.size(); i++) {
                    SimModelDump.Group g = groups.get(i);
                    glens[i] = g.verts();
                    String texId = g.texture();
                    if (texId == null) {
                        texId = shot.texture(); // 最大グループのもので代用
                    }
                    if (texId == null) {
                        texId = ""; // validateGroups が null 要素を拒否するため空文字を使う
                    }
                    gtex[i] = textureTable.computeIfAbsent(texId, k -> textureTable.size());
                }
                frameGlens.add(glens);
                frameGtex.add(gtex);
            } catch (IOException e) {
                TouhouLittleMaid.LOGGER.error("[SIM] pose trace bin append failed", e);
            }
        }
        afterStep();
    }

    private static void afterStep() {
        stepsSinceCheckpoint++;
        if (stepsSinceCheckpoint >= CHECKPOINT_EVERY) {
            stepsSinceCheckpoint = 0;
            writeIndex();
            writeCtrl();
            SimPaletteTrace.checkpoint();
        }
    }

    /**
     * 頼まれていれば palette の記録を自動で始める。
     *
     * <p><b>入るのは 4 つ揃ったときだけ</b>: プロパティが 1 / 手動で止めていない /
     * ワールドに居る / 近くに霊夢が居る。どれか欠ければ何もしない。
     *
     * <p>始めるのは {@link CaptureMode#PALETTE_ONLY} —— 自動で頂点を録り始めると
     * 気づかないうちに run あたり約 128MB を書く。
     */
    private static void maybeAutoStart() {
        if (!"1".equals(System.getProperty(PROP_AUTOPOSE))) {
            return;
        }
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null || mc.player == null) {
            // ワールドの外。次に入ったときのために錠と札を外す。
            autoLatched = false;
            autoTriedFor = null;
            return;
        }
        if (autoLatched) {
            return;
        }
        Entity r = findReimu();
        if (r == null) {
            return;
        }
        UUID id = r.getUUID();
        if (id.equals(autoTriedFor)) {
            return;   // この霊夢では既に試した (成否によらず一度きり)
        }
        autoTriedFor = id;
        String err = start(0, CaptureMode.PALETTE_ONLY);
        if (err != null) {
            TouhouLittleMaid.LOGGER.warn("[SIM] palette の自動開始に失敗: {}", err);
            say(ChatFormatting.YELLOW, "[SIM] palette の自動開始に失敗: " + err);
            return;
        }
        say(ChatFormatting.GREEN, "[SIM] palette を自動で録り始めた (" + PROP_AUTOPOSE + "=1)。"
                + "霊夢を画面内に保つこと —— 実描画経路からしか採れない");
    }

    /** 記録を終える。索引を書き、チャットとログへ結果を出す。対象が既に無い場合も安全。 */
    public static void stop() {
        // **手で止めたら、自分からは戻らない。** 錠はワールドを出ると外れる
        // (maybeAutoStart の level == null の枝)。
        autoLatched = true;
        if (!active) {
            say(ChatFormatting.GRAY, "[SIM] 姿勢トレースは実行されていない");
            return;
        }
        finish();
    }

    private static void finish() {
        active = false;
        writeIndex();
        writeCtrl();
        SimPaletteTrace.finish();
        int distinct = frames.size();
        int ticks = slots.size();
        if (mode == CaptureMode.PALETTE_ONLY) {
            // **頂点の数字を出さない。** 0 tick / 0 フレームと出すと「録れなかった」に
            // 見えるが、実際には palette は録れている。数えるべきものが別の場所に在る。
            say(ChatFormatting.GREEN, "[SIM] palette 記録終了 (頂点は録っていない)。"
                    + "長さと被覆は .pal.json の slots で見ること "
                    + "(span=slots.length / captured=0以上の個数)");
            finishPaletteOnly();
            return;
        }
        say(ChatFormatting.GREEN, "[SIM] 姿勢トレース終了: " + ticks + "tick / 相異なるフレーム "
                + distinct + "本");
        if (poseFull) {
            // ticks は「頂点を録った範囲」であって run の長さではない。取り違えると
            // 60 秒録ったのに 96tick と読めてしまう。
            say(ChatFormatting.DARK_GRAY, "  頂点は上限で打ち切り (上の " + ticks
                    + "tick は頂点の範囲であって run の長さではない)。"
                    + "palette 側の長さと被覆は .pal.json の slots で見ること");
        }
        int minReport = minVertCount == Integer.MAX_VALUE ? 0 : minVertCount;
        int maxReport = Math.max(maxVertCount, 0);
        say(ChatFormatting.DARK_GRAY, "  頂点数: 変化 " + vertCountChanges + "回 / 最小 " + minReport
                + " / 最大 " + maxReport);
        say(ChatFormatting.DARK_GRAY, "  グループ内訳: 変化 " + groupSigChanges + "回 / 最大グループ数 "
                + Math.max(maxGroupCount, 0));
        if (outBin != null) {
            try {
                long size = Files.exists(outBin) ? Files.size(outBin) : 0L;
                say(ChatFormatting.DARK_GRAY, "  -> " + outJson + " (" + size + " bytes)");
            } catch (IOException ignored) {
                say(ChatFormatting.DARK_GRAY, "  -> " + outJson);
            }
        }
        TouhouLittleMaid.LOGGER.info(
                "[SIM] pose trace: {} ticks, {} distinct frames, vert count changes {} (min {} / max {}), "
                        + "group sig changes {} (max groups {}) -> {}",
                ticks, distinct, vertCountChanges, minReport, maxReport,
                groupSigChanges, Math.max(maxGroupCount, 0), outJson);
        target = null;
    }

    /** PALETTE_ONLY の終わり方。索引と ctrl と palette は既に上で書き終えている。頂点の集計は触らない。 */
    private static void finishPaletteOnly() {
        TouhouLittleMaid.LOGGER.info("[SIM] palette-only trace finished (no vertex companion written)");
        target = null;
    }

    /**
     * その tick の {@code ctrl.*} 相当をクライアントの実値から 1 行の JSON にする。
     *
     * <p>導出せずに<b>生の状態をそのまま</b>残すのが方針 —— {@code ctrl.walk} の速度しきい値の
     * ような「解釈」は読み手 (Viewer / 採点器) 側で試行錯誤できるようにしておく。ここで丸めると
     * しきい値を変えるたびに実機を録り直す羽目になる。
     */
    private static void captureCtrl(int tick) {
        if (target == null) {
            return;
        }
        try {
            Vec3 v = target.getDeltaMovement();
            StringBuilder b = new StringBuilder(256);
            b.append("{\"t\":").append(tick);
            b.append(",\"onG\":").append(target.onGround());
            b.append(",\"vx\":").append(fmt(v.x)).append(",\"vy\":").append(fmt(v.y)).append(",\"vz\":").append(fmt(v.z));
            b.append(",\"x\":").append(fmt(target.getX())).append(",\"y\":").append(fmt(target.getY())).append(",\"z\":").append(fmt(target.getZ()));
            b.append(",\"yaw\":").append(fmt(target.getYRot())).append(",\"pitch\":").append(fmt(target.getXRot()));
            b.append(",\"sprint\":").append(target.isSprinting());
            b.append(",\"crouch\":").append(target.isCrouching());
            b.append(",\"shift\":").append(target.isShiftKeyDown());
            b.append(",\"riding\":").append(target.isPassenger());
            if (target instanceof LivingEntity le) {
                b.append(",\"bodyYaw\":").append(fmt(le.yBodyRot)).append(",\"headYaw\":").append(fmt(le.yHeadRot));
                b.append(",\"fly\":").append(le.isFallFlying());
                b.append(",\"sleep\":").append(le.isSleeping());
                b.append(",\"main\":\"").append(itemId(le.getMainHandItem())).append("\"");
                b.append(",\"off\":\"").append(itemId(le.getOffhandItem())).append("\"");
            }
            b.append('}');
            ctrlLines.add(b.toString());
        } catch (Throwable t) {
            // 記録の付帯情報なので、ここで落ちて本体の記録を巻き添えにしない。
            TouhouLittleMaid.LOGGER.debug("[SIM] ctrl capture failed at tick {}", tick, t);
        }
    }

    /** {@code ItemStack} の登録 id。空なら {@code "empty"}。 */
    private static String itemId(ItemStack st) {
        if (st == null || st.isEmpty()) {
            return "empty";
        }
        return String.valueOf(BuiltInRegistries.ITEM.getKey(st.getItem()));
    }

    /** JSON へ入れる小数。桁を切って行を短く保つ (1 記録 = 1,000 行規模になるため)。 */
    private static String fmt(double d) {
        return String.format(Locale.ROOT, "%.4f", d);
    }

    /** {@link #ctrlLines} を companion へ書く。空なら何もしない (ファイルも作らない)。 */
    private static void writeCtrl() {
        if (outCtrl == null || ctrlLines.isEmpty()) {
            return;
        }
        try {
            Files.write(outCtrl, ctrlLines);
            TouhouLittleMaid.LOGGER.info("[SIM] pose trace: ctrl companion {} 行 -> {}", ctrlLines.size(), outCtrl);
        } catch (IOException e) {
            TouhouLittleMaid.LOGGER.error("[SIM] ctrl companion write failed", e);
        }
    }

    private static void writeIndex() {
        if (outJson == null || outBin == null) {
            return;
        }
        int[] slotArr = new int[slots.size()];
        for (int i = 0; i < slotArr.length; i++) {
            slotArr[i] = slots.get(i);
        }
        // frames.size() と長さが一致する前提で良い — appendFrame を呼ぶのと同じ分岐から
        // 積んでいるため (quick 260818-6cj)。
        int[] lensArr = new int[frameLens.size()];
        for (int i = 0; i < lensArr.length; i++) {
            lensArr[i] = frameLens.get(i);
        }

        // グループ表 (quick 260818-oq4): frameGlens/frameGtex も appendFrame と同じ分岐から
        // 積んでいるので frameLens と本数が一致するはず。食い違っていれば嘘の索引を書くより
        // グループ表なしで出す方を選ぶ (旧形式のまま出して落ちない方を選ぶ)。
        SimPoseCodec.Groups groups = null;
        if (frameGlens.size() != frameLens.size() || frameGtex.size() != frameLens.size()) {
            TouhouLittleMaid.LOGGER.warn(
                    "[SIM] pose trace: グループ表の本数 (glens {} / gtex {}) が lens ({}) と食い違うため"
                            + "グループ表なしで索引を書く", frameGlens.size(), frameGtex.size(), frameLens.size());
        } else {
            groups = new SimPoseCodec.Groups(
                    frameGlens.toArray(new int[0][]),
                    frameGtex.toArray(new int[0][]),
                    textureTable.keySet().toArray(new String[0]));
        }

        // uuid: どの run の誰を撮ったのかを索引自身に持たせる (形式 v2)。
        // これが無いと読み手は gt0 と gameTime の重なりでしか突き合わせられず、
        // tank のように宣言 duration が 24 時間あるシナリオでは**過去のあらゆる companion が
        // 窓に入ってしまい、別 run の姿勢が黙って採用される** (2026-08-24 実測)。
        // サーバ側の runId はクライアントへ渡す経路が無いが、run ごとに entity は作り直されるので
        // entity UUID だけで run は一意に決まる。
        String uuid = target != null ? target.getUUID().toString() : null;
        SimPoseCodec.Header header = new SimPoseCodec.Header(
                uuid != null ? SimPoseCodec.V2 : SimPoseCodec.V1,
                gt0, target != null ? target.getId() : -1, type, texture,
                SimVertexRecorder.STRIDE, Math.max(vertsPerFrame, 0), quant,
                idempotentResult, frames.size(), outBin.getFileName().toString(), uuid);
        try {
            SimPoseCodec.writeIndex(outJson, header, slotArr, lensArr, groups);
        } catch (IOException e) {
            TouhouLittleMaid.LOGGER.error("[SIM] pose trace index write failed: {}", outJson, e);
            say(ChatFormatting.RED, "[SIM] 索引の書き出しに失敗 (グループ表が不整合の場合を含む): "
                    + e.getMessage());
        }
    }

    /** 出力先。{@code <gameDir>/simlab/poses}。{@code SimModelDump.outDir()} と同じ流儀。 */
    public static Path outDir() {
        return Minecraft.getInstance().gameDirectory.toPath().resolve("simlab").resolve("poses");
    }

    private static void say(ChatFormatting color, String msg) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player != null) {
            mc.player.displayClientMessage(Component.literal(msg).withStyle(color), false);
        }
    }
}
