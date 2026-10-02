package com.github.tartaricacid.touhoulittlemaid.sim.trace;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import com.github.tartaricacid.touhoulittlemaid.sim.SimLab;
import com.github.tartaricacid.touhoulittlemaid.sim.SimRunner;
import com.google.gson.Gson;
import com.google.gson.JsonObject;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.fml.loading.FMLEnvironment;
import net.minecraftforge.fml.loading.FMLPaths;
import net.minecraftforge.server.ServerLifecycleHooks;

import javax.annotation.Nullable;
import java.io.BufferedWriter;
import java.lang.management.ManagementFactory;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Locale;
import java.util.Map;
import java.util.regex.Pattern;

/**
 * Forge SimpleChannel の runtime send/receive を process-local companion へ書く。
 *
 * <p><b>main arena trace へ直接混ぜない。</b> packet receive は client JVM で起こり、
 * arena JSONL は server JVM が書くため。pose/palette と同じく companion として分離する。
 *
 * <p>通常プレイでは {@code tlm.sim.scenario} が無いので完全に眠る。呼び出し側Mixinも
 * 同じ条件で適用されない想定だが、ここでも二重にガードする。
 */
public final class SimNetworkTrace {
    public static final int FORMAT_VERSION = 1;
    public static final String PROP_NET_OUT = "tlm.sim.net.out";

    private static final Object LOCK = new Object();
    private static final Gson GSON = new Gson();
    private static final Pattern SAFE = Pattern.compile("[^A-Za-z0-9._-]");
    private static final DateTimeFormatter STAMP = DateTimeFormatter.ofPattern("yyyyMMdd-HHmmss-SSS");

    @Nullable
    private static BufferedWriter out;
    @Nullable
    private static Path file;
    @Nullable
    private static String identityKey;
    private static long seq;
    private static boolean broken;
    private static boolean shutdownHookInstalled;

    private static final String YSM_M6_HOOK_CLASS =
            "com.github.tartaricacid.touhoulittlemaid.sim.client.SimYsmFormalM6Probe";
    private static volatile boolean ysmM6HookResolved;
    private static volatile boolean ysmM6HookUnavailable;
    @Nullable
    private static Method ysmM6SemanticHook;

    private SimNetworkTrace() {}

    public static void onSend(@Nullable String channel, @Nullable Object packet, @Nullable String direction) {
        record("send", channel, packet, direction);
    }

    public static void onReceive(@Nullable Object packet, @Nullable String direction) {
        record("receive", null, packet, direction);
    }

    /**
     * Record a client/server semantic milestone that belongs to the same network diagnostic stream.
     *
     * <p>Examples: decoded Reimu Molang handler entered, YSM Molang command dispatched.
     * Payload is sanitized with the same shallow scalar-only contract as packet snapshots.
     */
    public static void onSemantic(@Nullable String kind, @Nullable Map<String, ?> payload) {
        if (!requested() || kind == null || kind.isBlank()) {
            return;
        }

        Map<String, Object> hookPayload = null;
        synchronized (LOCK) {
            try {
                Identity id = identity();
                ensureOpen(id);
                if (out == null || broken) {
                    return;
                }

                JsonObject o = new JsonObject();
                o.addProperty("v", FORMAT_VERSION);
                o.addProperty("ch", "net_semantic");
                o.addProperty("seq", ++seq);
                o.addProperty("kind", safe(kind));
                o.addProperty("physicalSide", physicalSide());
                o.addProperty("gameTime", gameTime());
                o.addProperty("thread", Thread.currentThread().getName());

                Map<String, Object> safePayload = SimPacketSnapshot.sanitize(payload);
                if (!safePayload.isEmpty()) {
                    o.add("payload", GSON.toJsonTree(safePayload));
                }

                out.write(GSON.toJson(o));
                out.write('\n');
                out.flush();
                hookPayload = safePayload;
            } catch (Throwable e) {
                broken = true;
                TouhouLittleMaid.LOGGER.error(
                        "[SIM-NET] semantic write failed; disabling network companion", e);
                closeQuietly();
            }
        }

        // Forward only after the source row is durable. Hook failure never disables the
        // send/receive/network companion itself.
        if (hookPayload != null) {
            forwardYsmM6Semantic(kind, hookPayload);
        }
    }

    private static void forwardYsmM6Semantic(String kind, Map<String, Object> payload) {
        if (FMLEnvironment.dist != Dist.CLIENT) {
            return;
        }
        if (!"reimu_spellcard_handler".equals(kind)
                && !"ysm_molang_command_pre_dispatch".equals(kind)
                && !"ysm_client_command_result".equals(kind)) {
            return;
        }
        ensureYsmM6Hook();
        Method method = ysmM6SemanticHook;
        if (method == null) {
            return;
        }
        try {
            method.invoke(null, kind, payload);
        } catch (Throwable e) {
            ysmM6HookUnavailable = true;
            ysmM6SemanticHook = null;
            TouhouLittleMaid.LOGGER.debug(
                    "[SIM-NET] optional YSM M6 semantic hook disabled after invoke failure: {}",
                    e.toString());
        }
    }

    private static void ensureYsmM6Hook() {
        if (ysmM6HookResolved || ysmM6HookUnavailable || FMLEnvironment.dist != Dist.CLIENT) {
            return;
        }
        synchronized (SimNetworkTrace.class) {
            if (ysmM6HookResolved || ysmM6HookUnavailable) {
                return;
            }
            try {
                Class<?> hook = Class.forName(
                        YSM_M6_HOOK_CLASS, false, SimNetworkTrace.class.getClassLoader());
                ysmM6SemanticHook = hook.getMethod(
                        "onNetworkSemantic", String.class, Map.class);
                ysmM6HookResolved = true;
            } catch (Throwable e) {
                ysmM6HookUnavailable = true;
                ysmM6SemanticHook = null;
                TouhouLittleMaid.LOGGER.debug(
                        "[SIM-NET] optional YSM M6 hook unavailable: {}", e.toString());
            }
        }
    }

    private static void record(String stage, @Nullable String channel,
                               @Nullable Object packet, @Nullable String direction) {
        if (!requested()) {
            return;
        }
        synchronized (LOCK) {
            try {
                Identity id = identity();
                ensureOpen(id);
                if (out == null || broken) {
                    return;
                }

                JsonObject o = new JsonObject();
                o.addProperty("v", FORMAT_VERSION);
                o.addProperty("ch", "net");
                o.addProperty("seq", ++seq);
                o.addProperty("stage", stage);
                o.addProperty("physicalSide", physicalSide());
                o.addProperty("gameTime", gameTime());
                o.addProperty("thread", Thread.currentThread().getName());

                if (channel != null && !channel.isBlank()) {
                    o.addProperty("channel", channel);
                }
                if (packet != null) {
                    Class<?> type = packet.getClass();
                    o.addProperty("packet", type.getName());
                    o.addProperty("packetSimple", type.getSimpleName());
                    var payload = SimPacketSnapshot.capture(packet);
                    if (!payload.isEmpty()) {
                        o.add("payload", GSON.toJsonTree(payload));
                    }
                }
                if (direction != null && !direction.isBlank()) {
                    o.addProperty("direction", direction);
                }

                out.write(GSON.toJson(o));
                out.write('\n');
                // network evidence は「送った/受けた」の境界そのもの。クラッシュで落としたくないので毎行 flush。
                out.flush();
            } catch (Throwable e) {
                broken = true;
                TouhouLittleMaid.LOGGER.error("[SIM-NET] write failed; disabling network companion", e);
                closeQuietly();
            }
        }
    }

    private static void ensureOpen(Identity id) throws Exception {
        if (broken) {
            return;
        }
        if (out != null && id.key().equals(identityKey)) {
            return;
        }

        closeQuietly();
        identityKey = id.key();
        seq = 0;

        Path dir = outputRoot()
                .resolve(safe(id.scenario))
                .resolve("_network")
                .resolve(safe(id.run));
        Files.createDirectories(dir);

        String side = physicalSide().toLowerCase(Locale.ROOT);
        String pid = safe(pid());
        String stamp = LocalDateTime.now().format(STAMP);
        file = dir.resolve(side + "-" + pid + "-" + stamp + ".net.jsonl");
        out = Files.newBufferedWriter(file, StandardCharsets.UTF_8,
                StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING, StandardOpenOption.WRITE);

        JsonObject meta = new JsonObject();
        meta.addProperty("v", FORMAT_VERSION);
        meta.addProperty("ch", "net_meta");
        meta.addProperty("scenario", id.scenario);
        meta.addProperty("run", id.run);
        meta.addProperty("bound", id.bound);
        meta.addProperty("physicalSide", physicalSide());
        meta.addProperty("pid", pid());
        meta.addProperty("startedGameTime", gameTime());
        meta.addProperty("file", file.getFileName().toString());
        out.write(GSON.toJson(meta));
        out.write('\n');
        out.flush();

        installShutdownHook();
        TouhouLittleMaid.LOGGER.info("[SIM-NET] companion opened: {}", file);
    }

    private static Identity identity() {
        SimRunner runner = SimLab.runner();
        if (runner != null) {
            String scenario = runner.scenario() == null ? scenarioProperty() : runner.scenario().name;
            return new Identity(scenario, runner.runId(), true);
        }

        String scenario = scenarioProperty();
        String rawRun = System.getProperty(SimLab.PROP_RUN);
        String run = rawRun == null || rawRun.isBlank() ? "unbound" : rawRun.trim();
        return new Identity(scenario, run, !"unbound".equals(run));
    }

    private static String scenarioProperty() {
        String s = System.getProperty(SimLab.PROP_SCENARIO);
        return s == null || s.isBlank() ? "unknown" : s.trim();
    }

    private static boolean requested() {
        String s = System.getProperty(SimLab.PROP_SCENARIO);
        return s != null && !s.isBlank();
    }

    private static Path outputRoot() {
        String explicit = System.getProperty(PROP_NET_OUT);
        if (explicit != null && !explicit.isBlank()) {
            return Path.of(explicit);
        }
        String shared = System.getProperty(SimLab.PROP_OUT);
        if (shared != null && !shared.isBlank()) {
            return Path.of(shared);
        }
        return FMLPaths.GAMEDIR.get().resolve("simlab-out");
    }

    private static String physicalSide() {
        try {
            return FMLEnvironment.dist == Dist.CLIENT ? "CLIENT" : "DEDICATED_SERVER";
        } catch (Throwable ignored) {
            return "UNKNOWN";
        }
    }

    /**
     * server では ServerLifecycleHooks、client では reflection で Minecraft.level を読む。
     * client class を common class の constant pool に直接型参照しないため dedicated server でも安全。
     */
    private static long gameTime() {
        try {
            var server = ServerLifecycleHooks.getCurrentServer();
            if (server != null && server.overworld() != null) {
                return server.overworld().getGameTime();
            }
        } catch (Throwable ignored) {
        }

        if (FMLEnvironment.dist == Dist.CLIENT) {
            try {
                Class<?> mcClass = Class.forName("net.minecraft.client.Minecraft");
                Method getInstance = mcClass.getMethod("getInstance");
                Object mc = getInstance.invoke(null);
                Field levelField = mcClass.getField("level");
                Object level = levelField.get(mc);
                if (level != null) {
                    Method getGameTime = level.getClass().getMethod("getGameTime");
                    Object value = getGameTime.invoke(level);
                    if (value instanceof Number n) {
                        return n.longValue();
                    }
                }
            } catch (Throwable ignored) {
            }
        }
        return -1L;
    }

    private static String pid() {
        try {
            return Long.toString(ProcessHandle.current().pid());
        } catch (Throwable ignored) {
            String runtime = ManagementFactory.getRuntimeMXBean().getName();
            int at = runtime.indexOf('@');
            return at > 0 ? runtime.substring(0, at) : runtime;
        }
    }

    public static Path file() {
        synchronized (LOCK) {
            return file;
        }
    }

    public static void close() {
        synchronized (LOCK) {
            closeQuietly();
            identityKey = null;
            seq = 0;
            broken = false;
        }
    }

    private static void closeQuietly() {
        if (out != null) {
            try {
                out.flush();
                out.close();
            } catch (Exception ignored) {
            } finally {
                out = null;
            }
        }
    }

    private static void installShutdownHook() {
        if (shutdownHookInstalled) {
            return;
        }
        shutdownHookInstalled = true;
        try {
            Runtime.getRuntime().addShutdownHook(new Thread(SimNetworkTrace::close, "sim-net-close"));
        } catch (Throwable ignored) {
        }
    }

    private static String safe(String raw) {
        String s = raw == null ? "" : SAFE.matcher(raw.trim()).replaceAll("_");
        if (s.isEmpty() || s.chars().allMatch(ch -> ch == '.')) {
            return "unbound";
        }
        return s.length() > 80 ? s.substring(0, 80) : s;
    }

    private record Identity(String scenario, String run, boolean bound) {
        String key() {
            return scenario + "|" + run + "|" + physicalSide();
        }

        private Identity {
            scenario = scenario == null || scenario.isBlank() ? "unknown" : scenario;
            run = run == null || run.isBlank() ? "unbound" : run;
        }
    }
}
