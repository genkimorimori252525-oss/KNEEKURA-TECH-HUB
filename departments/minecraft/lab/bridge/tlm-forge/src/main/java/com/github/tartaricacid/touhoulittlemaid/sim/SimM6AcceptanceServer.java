package com.github.tartaricacid.touhoulittlemaid.sim;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import com.github.tartaricacid.touhoulittlemaid.entity.passive.EntityMaid;
import com.mojang.brigadier.arguments.StringArgumentType;
import net.minecraft.commands.Commands;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.Level;
import net.minecraftforge.event.RegisterCommandsEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import javax.annotation.Nullable;
import java.util.UUID;
import java.util.regex.Pattern;

/**
 * SimLab-only server driver for the actual Reimu packet path used by formal M6 acceptance.
 *
 * <p>The controlled client probe qualifies the runtime candidate first. It then sends
 * {@code tlmsimserver m6toggle <entityUuid> <variable>} to the integrated/dedicated server.
 * This class drives 0 -> 1 -> 0 -> 1 through EntityMaid#sendSpellCardMolang(..., true), i.e. the
 * real server packet route rather than the controlled client scheduler.
 */
@Mod.EventBusSubscriber(modid = TouhouLittleMaid.MOD_ID)
public final class SimM6AcceptanceServer {
    private static final int[] SEQUENCE = {0, 1, 0, 1};
    private static final int INTERVAL_TICKS = 12;
    private static final Pattern VARIABLE =
            Pattern.compile("[A-Za-z_][A-Za-z0-9_]*");

    private static boolean active;
    @Nullable private static UUID targetUuid;
    @Nullable private static String variable;
    @Nullable private static String runKey;
    @Nullable private static ResourceKey<Level> targetDimension;
    private static int index;
    private static int waitTicks;

    private SimM6AcceptanceServer() {}

    @SubscribeEvent
    public static void onRegisterCommands(RegisterCommandsEvent event) {
        if (!SimLab.requested()) {
            return;
        }
        event.getDispatcher().register(
                Commands.literal("tlmsimserver")
                        .requires(src -> SimLab.ENABLED)
                        .then(Commands.literal("m6toggle")
                                .then(Commands.argument("targetUuid", StringArgumentType.word())
                                        .then(Commands.argument("variable", StringArgumentType.word())
                                                .executes(ctx -> start(
                                                        ctx.getSource(),
                                                        StringArgumentType.getString(ctx, "targetUuid"),
                                                        StringArgumentType.getString(ctx, "variable"))))))
                        .then(Commands.literal("m6stop")
                                .executes(ctx -> stop(ctx.getSource()))));
    }

    @SubscribeEvent
    public static void onServerTick(TickEvent.ServerTickEvent event) {
        if (!active || event.phase != TickEvent.Phase.END) {
            return;
        }
        try {
            tick(event.getServer());
        } catch (Throwable t) {
            TouhouLittleMaid.LOGGER.error("[SIM-M6-ACCEPT] server sequence failed", t);
            clear();
        }
    }

    private static int start(
            CommandSourceStack source, String uuidText, String variableInput) {
        if (!SimLab.ENABLED) {
            source.sendFailure(Component.literal("[SIM] SimLab run が有効ではない"));
            return 0;
        }
        if (active) {
            source.sendFailure(Component.literal("[SIM] M6 actual sequence はすでに実行中"));
            return 0;
        }

        String scenario = System.getProperty(SimLab.PROP_SCENARIO);
        String run = System.getProperty(SimLab.PROP_RUN);
        if (scenario == null || scenario.isBlank() || run == null || run.isBlank()) {
            source.sendFailure(Component.literal(
                    "[SIM] tlm.sim.scenario と tlm.sim.run の両方が必要"));
            return 0;
        }

        String bare = normalizeVariable(variableInput);
        if (bare == null) {
            source.sendFailure(Component.literal(
                    "[SIM] variable は英数字/underscoreの単純名だけ指定すること"));
            return 0;
        }

        UUID uuid;
        try {
            uuid = UUID.fromString(uuidText);
        } catch (IllegalArgumentException ex) {
            source.sendFailure(Component.literal("[SIM] target UUID が不正"));
            return 0;
        }

        ServerLevel level = source.getLevel();
        Entity entity = level.getEntity(uuid);
        if (!(entity instanceof EntityMaid maid)
                || !maid.isAlive()
                || !(maid.isReimuMaid() || maid.isNamedReimu())) {
            source.sendFailure(Component.literal(
                    "[SIM] 指定UUIDの生存Reimu maidがこのlevelに居ない"));
            return 0;
        }

        active = true;
        targetUuid = uuid;
        variable = bare;
        runKey = scenario.trim() + "|" + run.trim();
        targetDimension = level.dimension();
        index = 0;
        waitTicks = 0;

        // First packet is sent synchronously from the command so the acceptance run starts at a
        // clear boundary. Subsequent packets are spaced far enough apart for M5 + 2-tick verify.
        sendNext(level, maid);

        source.sendSuccess(
                () -> Component.literal(
                        "[SIM] M6 actual packet sequence 開始: v." + bare
                                + " = 0 -> 1 -> 0 -> 1 / target=" + uuid
                                + " / interval=" + INTERVAL_TICKS + " ticks"),
                false);
        return 1;
    }

    private static int stop(CommandSourceStack source) {
        if (!active) {
            source.sendFailure(Component.literal("[SIM] 実行中のM6 actual sequenceは無い"));
            return 0;
        }
        clear();
        source.sendSuccess(() -> Component.literal("[SIM] M6 actual sequence を中止"), false);
        return 1;
    }

    private static void tick(MinecraftServer server) {
        if (!active || targetUuid == null || variable == null
                || runKey == null || targetDimension == null) {
            clear();
            return;
        }

        String scenario = System.getProperty(SimLab.PROP_SCENARIO);
        String run = System.getProperty(SimLab.PROP_RUN);
        String currentRunKey = scenario == null || run == null
                ? null
                : scenario.trim() + "|" + run.trim();
        if (!runKey.equals(currentRunKey)) {
            TouhouLittleMaid.LOGGER.warn(
                    "[SIM-M6-ACCEPT] run identity changed; aborting actual sequence");
            clear();
            return;
        }

        if (waitTicks > 0) {
            waitTicks--;
            return;
        }
        if (index >= SEQUENCE.length) {
            clear();
            return;
        }

        ServerLevel level = server.getLevel(targetDimension);
        if (level == null) {
            TouhouLittleMaid.LOGGER.warn(
                    "[SIM-M6-ACCEPT] target dimension disappeared; aborting actual sequence");
            clear();
            return;
        }

        Entity entity = level.getEntity(targetUuid);
        if (!(entity instanceof EntityMaid maid)
                || !maid.isAlive()
                || !(maid.isReimuMaid() || maid.isNamedReimu())) {
            TouhouLittleMaid.LOGGER.warn(
                    "[SIM-M6-ACCEPT] target {} disappeared; aborting actual sequence", targetUuid);
            clear();
            return;
        }
        sendNext(level, maid);
    }

    private static void sendNext(ServerLevel level, EntityMaid maid) {
        if (!active || variable == null || index >= SEQUENCE.length) {
            return;
        }
        int value = SEQUENCE[index++];
        String expression = "(v." + variable + " = " + value + ")";
        maid.sendSpellCardMolang(expression, true);
        TouhouLittleMaid.LOGGER.info(
                "[SIM-M6-ACCEPT] actual packet {}/{}: {} target={} gameTime={}",
                index, SEQUENCE.length, expression, maid.getUUID(), level.getGameTime());
        waitTicks = INTERVAL_TICKS;

        if (index >= SEQUENCE.length) {
            // Keep active until the next interval expires so a second command cannot overlap the
            // final client's post-M5 verification window.
        }
    }

    @Nullable
    private static String normalizeVariable(String input) {
        if (input == null) {
            return null;
        }
        String bare = input.trim();
        if (bare.startsWith("variable.")) {
            bare = bare.substring("variable.".length());
        } else if (bare.startsWith("v.")) {
            bare = bare.substring(2);
        }
        return VARIABLE.matcher(bare).matches() ? bare : null;
    }

    private static void clear() {
        active = false;
        targetUuid = null;
        variable = null;
        runKey = null;
        targetDimension = null;
        index = 0;
        waitTicks = 0;
    }
}
