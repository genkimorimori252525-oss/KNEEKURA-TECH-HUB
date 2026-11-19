package dev.kneekura.fivedifficulties.forge;

import net.minecraft.server.MinecraftServer;

import java.util.LinkedHashSet;
import java.util.Set;

/**
 * Lets several env-gated runtime scenarios share one dedicated-server run: the server is halted
 * once every enabled scenario has finished (or immediately when one fails).
 */
public final class ScenarioShutdown {
    private static final Set<String> FINISHED = new LinkedHashSet<>();

    private ScenarioShutdown() {}

    private static boolean enabled(String env) {
        return "1".equals(System.getenv(env));
    }

    public static synchronized void finished(MinecraftServer server, String env) {
        FINISHED.add(env);
        for (String scenario : new String[] {
                "FIVE_DIFFICULTIES_P6_RUNTIME_SCENARIO", "FIVE_DIFFICULTIES_P8_RUNTIME_SCENARIO",
                "FIVE_DIFFICULTIES_P9_RUNTIME_SCENARIO", "FIVE_DIFFICULTIES_P10_RUNTIME_SCENARIO",
                "FIVE_DIFFICULTIES_P11_RUNTIME_SCENARIO", "FIVE_DIFFICULTIES_P12_RUNTIME_SCENARIO",
                "FIVE_DIFFICULTIES_P13_RUNTIME_SCENARIO", "FIVE_DIFFICULTIES_P14_RUNTIME_SCENARIO",
                "FIVE_DIFFICULTIES_P15_RUNTIME_SCENARIO"}) {
            if (enabled(scenario) && !FINISHED.contains(scenario)) return;
        }
        server.halt(false);
    }

    public static void failed(MinecraftServer server) {
        server.halt(false);
    }
}
