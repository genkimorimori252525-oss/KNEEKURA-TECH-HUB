package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import net.minecraft.SharedConstants;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.EntityJoinLevelEvent;
import net.minecraftforge.event.entity.EntityLeaveLevelEvent;
import net.minecraftforge.event.server.ServerStoppingEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.ModList;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.server.ServerLifecycleHooks;

import java.io.InputStream;
import java.lang.management.ManagementFactory;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

@Mod.EventBusSubscriber(modid = TouhouLittleMaid.MOD_ID, value = Dist.CLIENT)
public final class KneekuraDebugClientBootstrap {
    private static final int STABLE_WORLD_TICKS_REQUIRED = 5;
    private static final int RETRY_TICKS = 20;

    private static volatile boolean envResolved;
    private static volatile KneekuraDebugEnv.Config config;
    private static volatile boolean disabled;
    private static volatile boolean readyWritten;
    private static boolean wrongWorldLogged;
    private static long tickCounter;
    private static long serverTickCounter;
    private static long nextWriteAttemptTick;

    private static ClientLevel lastLevel;
    private static int stableWorldTicks;

    private static final String JVM_STARTED_AT = Instant.ofEpochMilli(
            ManagementFactory.getRuntimeMXBean().getStartTime()).toString();

    private static volatile String forgeInitializedAt;
    private static String clientWorldAvailableAt;
    private static String playerJoinedAt;
    private static String probeReadyAt;
    private static String debugWorldReadyAt;

    private KneekuraDebugClientBootstrap() {
    }

    @SubscribeEvent
    public static void onClientTick(TickEvent.ClientTickEvent event) {
        if (event.phase != TickEvent.Phase.END || disabled) {
            return;
        }
        tickCounter++;

        if (!resolveEnvironment()) {
            return;
        }

        Minecraft mc = Minecraft.getInstance();

        Long evidenceGameTime = mc.level == null ? null : mc.level.getGameTime();
        KneekuraDebugEvidenceWriter.maybeClientHeartbeat(
                config,
                tickCounter,
                evidenceGameTime,
                mc.isPaused());

        KneekuraDebugTargetTracker.onClientTick(
                config,
                mc,
                tickCounter);

        KneekuraDebugShutdownCoordinator.onClientTick(
                config,
                tickCounter);

        // G2 observation continues for the whole debug run. G1 READY publication
        // is one-shot and stops here after it has succeeded.
        if (readyWritten) {
            return;
        }

        if (forgeInitializedAt == null) {
            return;
        }
        ClientLevel level = mc.level;
        if (level == null) {
            lastLevel = null;
            stableWorldTicks = 0;
            return;
        }

        if (level != lastLevel) {
            lastLevel = level;
            stableWorldTicks = 0;
            clientWorldAvailableAt = Instant.now().toString();
            playerJoinedAt = null;
            debugWorldReadyAt = null;
        }

        if (mc.player == null || mc.getConnection() == null) {
            stableWorldTicks = 0;
            return;
        }

        var integratedServer = mc.getSingleplayerServer();
        if (integratedServer == null) {
            stableWorldTicks = 0;
            if (!wrongWorldLogged) {
                wrongWorldLogged = true;
                TouhouLittleMaid.LOGGER.error(
                        "[KNEEKURA-DEBUG] expected integrated debug world '{}' but no integrated server is active",
                        config.worldName());
            }
            return;
        }

        String actualWorldName = integratedServer.getWorldData().getLevelName();
        if (!config.worldName().equals(actualWorldName)) {
            stableWorldTicks = 0;
            if (!wrongWorldLogged) {
                wrongWorldLogged = true;
                TouhouLittleMaid.LOGGER.error(
                        "[KNEEKURA-DEBUG] wrong world: expected='{}' actual='{}'; refusing DEBUG_READY",
                        config.worldName(),
                        actualWorldName);
            }
            return;
        }
        wrongWorldLogged = false;

        if (playerJoinedAt == null) {
            playerJoinedAt = Instant.now().toString();
        }
        if (probeReadyAt == null) {
            probeReadyAt = Instant.now().toString();
        }

        stableWorldTicks++;
        if (stableWorldTicks < STABLE_WORLD_TICKS_REQUIRED) {
            return;
        }

        if (debugWorldReadyAt == null) {
            debugWorldReadyAt = Instant.now().toString();
        }

        if (tickCounter < nextWriteAttemptTick) {
            return;
        }

        try {
            KneekuraDebugReadyWriter.write(config, readyState(mc));
            readyWritten = true;
            TouhouLittleMaid.LOGGER.info(
                    "[KNEEKURA-DEBUG] DEBUG_READY session={} run={} epoch={} file={}",
                    config.debugSessionId(),
                    config.runId(),
                    config.processEpoch(),
                    config.readyFile());
        } catch (Exception e) {
            nextWriteAttemptTick = tickCounter + RETRY_TICKS;
            TouhouLittleMaid.LOGGER.error(
                    "[KNEEKURA-DEBUG] READY manifest write failed; retrying in {} ticks",
                    RETRY_TICKS,
                    e);
        }
    }

    @SubscribeEvent
    public static void onServerTick(TickEvent.ServerTickEvent event) {
        if (event.phase != TickEvent.Phase.END || disabled) {
            return;
        }
        if (!resolveEnvironment()) {
            return;
        }

        serverTickCounter++;
        Long gameTime = null;
        net.minecraft.server.MinecraftServer server = null;
        try {
            server = ServerLifecycleHooks.getCurrentServer();
            if (server != null && server.overworld() != null) {
                gameTime = server.overworld().getGameTime();
            }
        } catch (Throwable ignored) {
        }

        KneekuraDebugEvidenceWriter.maybeServerHeartbeat(
                config,
                serverTickCounter,
                gameTime);

        if (server != null) {
            try {
                if (config.ownerSetup() != null) {
                    KneekuraDebugOwnerConnection.onServerTick(config, server, serverTickCounter, KneekuraDebugClientBootstrap.class);
                } else {
                    KneekuraDebugArenaRuntime.onServerTick(config, server, serverTickCounter);
                }
            } catch (Exception e) {
                TouhouLittleMaid.LOGGER.error("[KNEEKURA-DEBUG] Arena owner tick blocked", e);
            }
            KneekuraDebugTankPresentation.update(config, server);
            KneekuraDebugServerObserver.onServerTick(
                    config,
                    server,
                    serverTickCounter);
        }
    }

    @SubscribeEvent
    public static void onServerStopping(ServerStoppingEvent event) {
        KneekuraDebugServerObserver.stop();
    }

    @SubscribeEvent
    public static void onEntityJoin(EntityJoinLevelEvent event) {
        if (!event.getLevel().isClientSide) {
            return;
        }
        KneekuraDebugTargetTracker.onEntityJoin(event.getEntity());
    }

    @SubscribeEvent
    public static void onEntityLeave(EntityLeaveLevelEvent event) {
        if (!event.getLevel().isClientSide) {
            return;
        }
        KneekuraDebugTargetTracker.onEntityLeave(event.getEntity());
    }

    static synchronized void markForgeInitialized() {
        if (forgeInitializedAt == null) {
            forgeInitializedAt = Instant.now().toString();
        }
    }

    private static synchronized boolean resolveEnvironment() {
        if (envResolved) {
            return config != null && config.enabled();
        }
        envResolved = true;
        try {
            config = KneekuraDebugEnv.fromSystemEnvironment();
            if (!config.enabled()) {
                disabled = true;
                return false;
            }
            TouhouLittleMaid.LOGGER.info(
                    "[KNEEKURA-DEBUG] debug bootstrap enabled session={} run={} epoch={}",
                    config.debugSessionId(),
                    config.runId(),
                    config.processEpoch());
            return true;
        } catch (Exception e) {
            disabled = true;
            TouhouLittleMaid.LOGGER.error(
                    "[KNEEKURA-DEBUG] invalid debug environment; bootstrap disabled",
                    e);
            return false;
        }
    }

    private static KneekuraDebugReadyWriter.ReadyState readyState(Minecraft mc) {
        KneekuraDebugReadyWriter.Milestones milestones =
                new KneekuraDebugReadyWriter.Milestones(
                        JVM_STARTED_AT,
                        forgeInitializedAt,
                        clientWorldAvailableAt,
                        playerJoinedAt,
                        probeReadyAt,
                        debugWorldReadyAt);

        List<String> mods = new ArrayList<>();
        ModList.get().getMods().forEach(mod ->
                mods.add(mod.getModId() + "@" + mod.getVersion()));
        mods.sort(Comparator.naturalOrder());

        String forgeVersion = ModList.get().getMods().stream()
                .filter(mod -> "forge".equals(mod.getModId()))
                .findFirst()
                .map(mod -> mod.getVersion().toString())
                .orElse("unknown");

        String topology = "INTEGRATED_SERVER";

        KneekuraDebugReadyWriter.RuntimeInfo runtime =
                new KneekuraDebugReadyWriter.RuntimeInfo(
                        SharedConstants.getCurrentVersion().getName(),
                        forgeVersion,
                        System.getProperty("java.version", "unknown"),
                        topology,
                        probeBuildIdentity(),
                        "java",
                        mods);

        return new KneekuraDebugReadyWriter.ReadyState(
                ProcessHandle.current().pid(),
                milestones,
                runtime);
    }

    private static String probeBuildIdentity() {
        String resource = "/" + KneekuraDebugClientBootstrap.class
                .getName()
                .replace('.', '/') + ".class";
        try (InputStream in = KneekuraDebugClientBootstrap.class.getResourceAsStream(resource)) {
            if (in == null) {
                return "unknown";
            }
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] buffer = new byte[8192];
            int n;
            while ((n = in.read(buffer)) >= 0) {
                if (n > 0) {
                    digest.update(buffer, 0, n);
                }
            }
            return "sha256:" + HexFormat.of().formatHex(digest.digest());
        } catch (Exception e) {
            return "unknown";
        }
    }
}
