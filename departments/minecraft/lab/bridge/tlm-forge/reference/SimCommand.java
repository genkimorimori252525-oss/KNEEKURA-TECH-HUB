package com.github.tartaricacid.touhoulittlemaid.command.subcommand;

import com.github.tartaricacid.touhoulittlemaid.sim.SimArena;
import com.mojang.brigadier.Command;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import com.mojang.brigadier.context.CommandContext;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;

/**
 * {@code /tlm sim …} サブコマンド —— 走っている水槽(SimLab)のつまみ。
 *
 * <p>ここに置くのは<b>「水槽を実機と違わせる」設定</b>だけ。実機と同じ挙動は
 * 設定にしない —— つまみがあること自体が「ここは実機と違い得る」の印になるようにする。
 *
 * <pre>
 *   /tlm sim itemttl 20     落ちた物を 20 tick(1秒)で消す
 *   /tlm sim itemttl off    実機のまま(6000 tick = 5分)
 *   /tlm sim status         今の設定
 * </pre>
 *
 * <p>{@link ReimuDebugCommand} と同型 —— config による永続化はせず、走っている
 * セッションに即座に効く。水槽は立て直しが安いので、恒久設定はシナリオ側の仕事。
 */
public final class SimCommand {

    private static final String NAME = "sim";

    private SimCommand() {}

    public static LiteralArgumentBuilder<CommandSourceStack> get() {
        return Commands.literal(NAME)
                .then(Commands.literal("itemttl")
                        .then(Commands.literal("off").executes(c -> setTtl(c, 0)))
                        .then(Commands.argument("ticks", IntegerArgumentType.integer(0, 6000))
                                .executes(c -> setTtl(c, IntegerArgumentType.getInteger(c, "ticks")))))
                .then(Commands.literal("status").executes(SimCommand::status));
    }

    private static int setTtl(CommandContext<CommandSourceStack> context, int ticks) {
        SimArena.itemTtlTicks = ticks;
        context.getSource().sendSuccess(() -> Component.literal(describe(ticks)), true);
        return Command.SINGLE_SUCCESS;
    }

    private static int status(CommandContext<CommandSourceStack> context) {
        context.getSource().sendSuccess(() -> Component.literal(describe(SimArena.itemTtlTicks)), false);
        return Command.SINGLE_SUCCESS;
    }

    /** 数字だけでなく「実機と何が違うか」を毎回言う。設定を忘れたまま観察するのが一番危ない。 */
    private static String describe(int ticks) {
        if (ticks <= 0) {
            return "[SimLab] 落ちた物の寿命 = 実機のまま (6000 tick = 5 分)";
        }
        return "[SimLab] 落ちた物の寿命 = " + ticks + " tick ("
                + String.format("%.1f", ticks / 20.0F) + " 秒) — **実機 (5 分) とは違う**。"
                + " メイドのアイテム拾いを検証するときは /tlm sim itemttl off";
    }
}
