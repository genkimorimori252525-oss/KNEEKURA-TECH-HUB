package com.github.tartaricacid.touhoulittlemaid.sim.client;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.Commands;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.EntityType;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.RegisterClientCommandsEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.ArrayList;
import java.util.List;

/**
 * SimLab のクライアント側コマンド。
 *
 * <pre>
 * /tlmsim dumpmodels            全モブを書き出す (描画できないものは自動で飛ばす)
 * /tlmsim dumpmodels reimu      touhou_little_maid:reimu だけ
 * /tlmsim dumpmodels minecraft:zombie
 * </pre>
 *
 * <p>クライアントコマンドにしてあるのは、モデルがクライアント側にしか無いから。
 * sim 本体 (ヘッドレス) はこの書き出し結果を使うだけで、実行時にクライアントを必要としない。
 */
@Mod.EventBusSubscriber(modid = TouhouLittleMaid.MOD_ID, value = Dist.CLIENT)
public final class SimClientCommands {

    /** {@code /tlmsim animsweep} の既定 {@code ticksPerAnim} (20 tick = 1 秒)。 */
    private static final int DEFAULT_ANIMSWEEP_TICKS = 20;

    /** {@code /tlmsim dumpcubes} の既定 cube 数 (spike 004 実測: 6634)。 */
    private static final int DEFAULT_DUMPCUBES_COUNT = 6634;

    private SimClientCommands() {}

    @SubscribeEvent
    public static void onRegisterClientCommands(RegisterClientCommandsEvent event) {
        event.getDispatcher().register(
                Commands.literal("tlmsim").then(
                        Commands.literal("dumpmodels")
                                .executes(ctx -> run(ctx.getSource(), null))
                                .then(Commands.argument("entity", StringArgumentType.string())
                                        .executes(ctx -> run(ctx.getSource(),
                                                StringArgumentType.getString(ctx, "entity")))))
                        .then(Commands.literal("dumpposes").executes(ctx -> runPoses(ctx.getSource())))
                        .then(Commands.literal("posetrace")
                                .then(Commands.literal("start")
                                        .executes(ctx -> runPoseTraceStart(ctx.getSource(), 0))
                                        // 水槽向け: palette だけ録る。頂点 (約 128MB/run の
                                        // 死荷重 + 毎 tick の shoot()) を最初から採らない。
                                        .then(Commands.literal("palette")
                                                .executes(ctx -> runPoseTraceStartPalette(ctx.getSource())))
                                        .then(Commands.argument("quant", IntegerArgumentType.integer(0, 4))
                                                .executes(ctx -> runPoseTraceStart(ctx.getSource(),
                                                        IntegerArgumentType.getInteger(ctx, "quant")))))
                                .then(Commands.literal("stop")
                                        .executes(ctx -> runPoseTraceStop(ctx.getSource()))))
                        // spike 004: 全ボーンへ届く経路があるかの探り針。次の 1 フレームだけ採る。
                        .then(Commands.literal("boneprobe")
                                .executes(ctx -> runBoneProbe(ctx.getSource())))
                        .then(Commands.literal("renderframe")
                                .executes(ctx -> runRenderFrame(ctx.getSource())))
                        .then(Commands.literal("golden")
                                .executes(ctx -> runGolden(ctx.getSource())))
                        // spike 004 第2段階: 同一 geoRender からボーン行列と頂点を同時に採る。
                        .then(Commands.literal("bonecapture")
                                .executes(ctx -> runBoneCapture(ctx.getSource(), 3, 6))
                                .then(Commands.argument("count", IntegerArgumentType.integer(1, 64))
                                        .executes(ctx -> runBoneCapture(ctx.getSource(),
                                                IntegerArgumentType.getInteger(ctx, "count"), 6))
                                        .then(Commands.argument("spacing", IntegerArgumentType.integer(1, 200))
                                                .executes(ctx -> runBoneCapture(ctx.getSource(),
                                                        IntegerArgumentType.getInteger(ctx, "count"),
                                                        IntegerArgumentType.getInteger(ctx, "spacing"))))))
                        .then(Commands.literal("animsweep")
                                .executes(ctx -> runAnimSweep(ctx.getSource(), DEFAULT_ANIMSWEEP_TICKS))
                                .then(Commands.argument("ticksPerAnim", IntegerArgumentType.integer(1, 200))
                                        .executes(ctx -> runAnimSweep(ctx.getSource(),
                                                IntegerArgumentType.getInteger(ctx, "ticksPerAnim"))))
                                .then(Commands.literal("stop")
                                        .executes(ctx -> runAnimSweepStop(ctx.getSource()))))
                        // spike 004 第6段階 (14-04): YSM のスキニング前ローカル cube 座標の探り針。
                        // 値の意味は推測しない —— manifest + 生 float バイナリ + bone 名テーブルだけを書く。
                        .then(Commands.literal("dumpcubes")
                                .executes(ctx -> runDumpCubes(ctx.getSource(), DEFAULT_DUMPCUBES_COUNT))
                                .then(Commands.argument("cubeCount", IntegerArgumentType.integer(1))
                                        .executes(ctx -> runDumpCubes(ctx.getSource(),
                                                IntegerArgumentType.getInteger(ctx, "cubeCount")))))
                        // M6 discovery: runtime scalar stateを採るだけ。Molang適用成功とは認定しない。
                        .then(Commands.literal("ysmprobe")
                                .then(Commands.literal("snapshot")
                                        .executes(ctx -> runYsmProbeSnapshot(ctx.getSource(), "manual"))
                                        .then(Commands.argument("label", StringArgumentType.word())
                                                .executes(ctx -> runYsmProbeSnapshot(
                                                        ctx.getSource(),
                                                        StringArgumentType.getString(ctx, "label")))))
                                .then(Commands.literal("toggle")
                                        .then(Commands.argument("variable", StringArgumentType.word())
                                                .executes(ctx -> runYsmProbeToggle(
                                                        ctx.getSource(),
                                                        StringArgumentType.getString(ctx, "variable")))))
                                .then(Commands.literal("accept")
                                        .then(Commands.argument("variable", StringArgumentType.word())
                                                .executes(ctx -> runYsmProbeAccept(
                                                        ctx.getSource(),
                                                        StringArgumentType.getString(ctx, "variable")))))
                                .then(Commands.literal("stop")
                                        .executes(ctx -> runYsmProbeStop(ctx.getSource())))));
    }

    /**
     * 霊夢の姿勢を収集する。実在の霊夢が近くに必要
     * (YSM の molang が位置セレクタで対象を選ぶため)。tick をまたいで進む。
     */
    private static int runPoses(net.minecraft.commands.CommandSourceStack src) {
        String err = SimPoseDump.start();
        if (err != null) {
            src.sendFailure(Component.literal("[SIM] " + err));
            return 0;
        }
        return 1;
    }

    /**
     * 姿勢トレース (毎tick記録) を開始する。実在の霊夢が近くに必要
     * (探索方法は {@link SimPoseDump#start()} と同型)。冪等性ゲートに失敗したら
     * 記録を始めずに理由を返す。
     */
    private static int runPoseTraceStart(net.minecraft.commands.CommandSourceStack src, int quant) {
        String err = SimPoseTrace.start(quant);
        if (err != null) {
            src.sendFailure(Component.literal("[SIM] " + err));
            return 0;
        }
        return 1;
    }

    /**
     * palette だけを録り始める (水槽向け)。
     *
     * <p><b>頂点は一切録らない。</b> 2026-08-25 に palette が最上位の姿勢源になった
     * (にーくら判定) 以降、水槽で頂点を録る理由が無い —— 上限まで録っても run あたり
     * 約 128MB の死荷重で、毎 tick の {@code shoot()} も払う。
     *
     * <p><b>霊夢を画面内に保つこと。</b> palette は {@code EntityMaidRenderer} の
     * 実描画経路からしか採れないので視錐台カリングを受け、最小化中はゼロになる。
     * 被覆は {@code .pal.json} の {@code slots} から数える。
     */
    private static int runPoseTraceStartPalette(net.minecraft.commands.CommandSourceStack src) {
        String err = SimPoseTrace.start(0, SimPoseTrace.CaptureMode.PALETTE_ONLY);
        if (err != null) {
            src.sendFailure(Component.literal("[SIM] " + err));
            return 0;
        }
        return 1;
    }

    /** 姿勢トレースを終える。索引を書き、結果をチャットへ出す。 */
    private static int runPoseTraceStop(net.minecraft.commands.CommandSourceStack src) {
        SimPoseTrace.stop();
        return 1;
    }

    /** 同一フレームの entities 前後 framebuffer と final-vertex raw frame を結合する。 */
    private static int runGolden(net.minecraft.commands.CommandSourceStack src) {
        String msg = SimFinalVertexCapture.requestNextGolden();
        if (SimFinalVertexCapture.isArmed()) {
            src.sendSuccess(() -> Component.literal(msg).withStyle(ChatFormatting.GREEN), false);
            return 1;
        }
        src.sendFailure(Component.literal("[SIM] " + msg));
        return 0;
    }

    /** 次の実描画 1 回を final-vertex raw frame として採る。再renderは行わない。 */
    private static int runRenderFrame(net.minecraft.commands.CommandSourceStack src) {
        String msg = SimFinalVertexCapture.requestNext();
        if (SimFinalVertexCapture.isArmed()) {
            src.sendSuccess(() -> Component.literal(msg).withStyle(ChatFormatting.GREEN), false);
            return 1;
        }
        src.sendFailure(Component.literal("[SIM] " + msg));
        return 0;
    }

    /** spike 004 の探り針を 1 フレームぶん立てる。値の意味は推測せず、到達できたものを書き出すだけ。 */
    private static int runBoneProbe(net.minecraft.commands.CommandSourceStack src) {
        String msg = SimBoneProbe.arm();
        src.sendSuccess(() -> Component.literal(msg), false);
        return 1;
    }

    /**
     * spike 004 第2段階。行列と頂点を<b>同じ描画から</b>採る (別々に採るとフレームがずれる)。
     * <b>姿勢は自分で作る</b> —— 5 姿勢 (静止/大回転/position/scale/scale=0) を順に送るので、
     * 実行する側は霊夢を動かさなくてよい。count は 1 姿勢あたりの枚数。
     */
    private static int runBoneCapture(net.minecraft.commands.CommandSourceStack src, int count, int spacing) {
        String msg = SimBoneCapture.start(count, spacing);
        src.sendSuccess(() -> Component.literal(msg), false);
        return 1;
    }

    /**
     * 霊夢の YSM パックが持つ全アニメを 1 本ずつ再生させて頂点を録る (quick 260819-o9l)。
     * 実在の霊夢が近くに必要。既定 20 tick/本 × 実測 316 本で 5 分強かかるので、
     * 途中で打ち切れるよう {@code /tlmsim animsweep stop} を用意してある。
     */
    private static int runAnimSweep(net.minecraft.commands.CommandSourceStack src, int ticksPerAnim) {
        String err = SimAnimSweep.start(ticksPerAnim);
        if (err != null) {
            src.sendFailure(Component.literal("[SIM] " + err));
            return 0;
        }
        return 1;
    }

    /** 実行中の animsweep を安全に打ち切る。それまでのチェックポイントが最終成果物になる。 */
    private static int runAnimSweepStop(net.minecraft.commands.CommandSourceStack src) {
        SimAnimSweep.stop();
        return 1;
    }

    /**
     * spike 004 第6段階 (14-04): YSM の内部から cube 数・bone 数の倍数関係を持つ
     * 配列/Collection/Map を候補として書き出す。<b>見つからなくても manifest は必ず書く</b>。
     * 探索完了かつ候補0件だけ赤、budgetで未探索が残れば黄色で「未確定」と報告する。
     */
    private static int runDumpCubes(net.minecraft.commands.CommandSourceStack src, int cubeCount) {
        src.sendSuccess(() -> Component.literal("[SIM] dumpcubes: 走査中… (cubeCount=" + cubeCount + ")")
                .withStyle(ChatFormatting.GRAY), false);
        SimModelDump.DumpCubesResult r = SimModelDump.dumpYsmLocalCubes(cubeCount);
        if (!r.ok()) {
            src.sendFailure(Component.literal("[SIM] dumpcubes 失敗: " + r.message()));
            return 0;
        }
        ChatFormatting color = !r.complete()
                ? ChatFormatting.YELLOW
                : (r.negative() ? ChatFormatting.RED : ChatFormatting.GREEN);
        src.sendSuccess(() -> Component.literal("[SIM] dumpcubes: " + r.message()).withStyle(color), false);
        src.sendSuccess(() -> Component.literal("  -> " + r.dir()).withStyle(ChatFormatting.DARK_GRAY), false);
        return 1;
    }

    /**
     * Run-bound discovery snapshot for the YSM runtime scalar graph.
     *
     * <p>Success here means only that a snapshot artifact was written. It does not mean the
     * preceding Molang command was evaluated or applied by YSM.
     */
    private static int runYsmProbeSnapshot(
            net.minecraft.commands.CommandSourceStack src, String label) {
        SimYsmMolangStateProbe.CaptureResult result = SimYsmMolangStateProbe.capture(label);
        if (!result.ok()) {
            src.sendFailure(Component.literal("[SIM] ysmprobe 失敗: " + result.message()));
            return 0;
        }
        ChatFormatting color = result.complete() ? ChatFormatting.GREEN : ChatFormatting.YELLOW;
        src.sendSuccess(
                () -> Component.literal("[SIM] " + result.message()).withStyle(color),
                false);
        if (!result.complete()) {
            src.sendSuccess(
                    () -> Component.literal(
                                    "  -> scan incomplete: 未探索領域があるためabsenceやM6を確定しない")
                            .withStyle(ChatFormatting.YELLOW),
                    false);
        }
        return 1;
    }

    /** Start the controlled 0 -> 1 -> 0 -> 1 discovery sequence. */
    private static int runYsmProbeToggle(
            net.minecraft.commands.CommandSourceStack src, String variable) {
        String err = SimYsmControlledToggleProbe.start(variable);
        if (err != null) {
            src.sendFailure(Component.literal("[SIM] ysmprobe toggle 失敗: " + err));
            return 0;
        }
        src.sendSuccess(
                () -> Component.literal(
                                "[SIM] ysmprobe toggle 開始: " + variable
                                        + " (controlled discovery only / formal M6ではない)")
                        .withStyle(ChatFormatting.GRAY),
                false);
        return 1;
    }

    /**
     * One-command formal-M6 acceptance flow. Controlled E2 qualification runs first; only after
     * successful qualification does the client request the server's real packet sequence.
     */
    private static int runYsmProbeAccept(
            net.minecraft.commands.CommandSourceStack src, String variable) {
        String err = SimYsmControlledToggleProbe.startAcceptance(variable);
        if (err != null) {
            src.sendFailure(Component.literal("[SIM] ysmprobe accept 失敗: " + err));
            return 0;
        }
        src.sendSuccess(
                () -> Component.literal(
                                "[SIM] ysmprobe accept 開始: controlled E2 -> actual packet 0→1→0→1")
                        .withStyle(ChatFormatting.GRAY),
                false);
        return 1;
    }

    /** Stop an in-progress controlled discovery sequence. */
    private static int runYsmProbeStop(net.minecraft.commands.CommandSourceStack src) {
        if (!SimYsmControlledToggleProbe.stop()) {
            src.sendFailure(Component.literal("[SIM] ysmprobe: 実行中のcontrolled probeは無い"));
            return 0;
        }
        return 1;
    }

    private static int run(net.minecraft.commands.CommandSourceStack src, String which) {
        List<EntityType<?>> types = new ArrayList<>();
        if (which != null && !which.isBlank()) {
            String id = which.contains(":") ? which : "touhou_little_maid:" + which;
            EntityType<?> t = BuiltInRegistries.ENTITY_TYPE.get(new ResourceLocation(id));
            if (t == null) {
                src.sendFailure(Component.literal("[SIM] unknown entity type: " + id));
                return 0;
            }
            types.add(t);
        }
        src.sendSuccess(() -> Component.literal("[SIM] モデルを書き出し中… (少しかかる)")
                .withStyle(ChatFormatting.GRAY), false);
        Object[] r = SimModelDump.dump(types);
        src.sendSuccess(() -> Component.literal(
                "[SIM] モブ " + r[0] + " 体 / スキップ " + r[1] + " 体"
                        + ((Integer) r[3] >= 0 ? " / ブロック " + r[3] + " 種 + アトラス" : ""))
                .withStyle(ChatFormatting.GREEN), false);
        src.sendSuccess(() -> Component.literal("  -> " + r[2]).withStyle(ChatFormatting.DARK_GRAY), false);
        return 1;
    }
}