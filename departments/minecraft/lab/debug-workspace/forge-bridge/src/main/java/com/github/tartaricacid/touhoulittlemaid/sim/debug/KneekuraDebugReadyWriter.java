package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;

public final class KneekuraDebugReadyWriter {
    public static final String PROTOCOL_VERSION = "KNEEKURA_DEBUG_READY_V1";

    private KneekuraDebugReadyWriter() {
    }

    public record Milestones(
            String jvmStartedAt,
            String forgeInitializedAt,
            String clientWorldAvailableAt,
            String playerJoinedAt,
            String probeReadyAt,
            String debugWorldReadyAt
    ) {
    }

    public record RuntimeInfo(
            String minecraft,
            String forge,
            String java,
            String topology,
            String probeBuild,
            String processCommandHint,
            List<String> loadedMods
    ) {
        public RuntimeInfo {
            loadedMods = loadedMods == null ? List.of() : List.copyOf(loadedMods);
        }
    }

    public record ReadyState(
            long pid,
            Milestones milestones,
            RuntimeInfo runtime
    ) {
    }

    public static void write(KneekuraDebugEnv.Config config, ReadyState state) throws IOException {
        if (config == null || !config.enabled()) {
            throw new IllegalArgumentException("debug config is not enabled");
        }
        if (state == null || state.runtime() == null || state.milestones() == null) {
            throw new IllegalArgumentException("ready state, milestones and runtime are required");
        }

        String json = toJson(config, state);
        Path target = config.readyFile();
        Files.createDirectories(target.getParent());

        if (Files.exists(target)) {
            String existing = Files.readString(target, StandardCharsets.UTF_8);
            if (existing.equals(json)) {
                return;
            }
            throw new IOException("READY manifest already exists with different content: " + target);
        }

        Path temp = target.resolveSibling(
                target.getFileName() + ".tmp-" + ProcessHandle.current().pid()
                        + "-" + Thread.currentThread().getId());
        Files.writeString(
                temp,
                json,
                StandardCharsets.UTF_8,
                StandardOpenOption.CREATE_NEW,
                StandardOpenOption.WRITE);
        try {
            try {
                Files.move(temp, target, StandardCopyOption.ATOMIC_MOVE);
            } catch (AtomicMoveNotSupportedException e) {
                // Deliberately no REPLACE_EXISTING. If another writer published
                // READY after our pre-check, fail rather than overwrite its identity.
                Files.move(temp, target);
            }
        } finally {
            Files.deleteIfExists(temp);
        }
    }

    static String toJson(KneekuraDebugEnv.Config config, ReadyState state) {
        Milestones m = state.milestones();
        RuntimeInfo r = state.runtime();

        StringBuilder out = new StringBuilder(1024);
        out.append("{\n");
        field(out, "protocolVersion", PROTOCOL_VERSION, true);
        field(out, "debugSessionId", config.debugSessionId(), true);
        field(out, "runId", config.runId(), true);
        field(out, "runSnapshotId", config.runSnapshotId(), true);
        field(out, "worldName", config.worldName(), true);
        numberField(out, "processEpoch", config.processEpoch(), true);
        field(out, "handshakeNonce", config.handshakeNonce(), true);
        field(out, "status", "DEBUG_READY", true);
        numberField(out, "pid", state.pid(), true);

        out.append("  \"gates\": {\n");
        boolField(out, "probeHandshake", true, true, 4);
        boolField(out, "debugWorldReady", true, true, 4);
        boolField(out, "runtimeAttested", runtimeAttested(r), false, 4);
        out.append("  },\n");

        out.append("  \"milestones\": {\n");
        nullableField(out, "jvmStartedAt", m.jvmStartedAt(), true, 4);
        nullableField(out, "forgeInitializedAt", m.forgeInitializedAt(), true, 4);
        nullableField(out, "clientWorldAvailableAt", m.clientWorldAvailableAt(), true, 4);
        nullableField(out, "playerJoinedAt", m.playerJoinedAt(), true, 4);
        nullableField(out, "probeReadyAt", m.probeReadyAt(), true, 4);
        nullableField(out, "debugWorldReadyAt", m.debugWorldReadyAt(), false, 4);
        out.append("  },\n");

        out.append("  \"runtime\": {\n");
        nullableField(out, "minecraft", r.minecraft(), true, 4);
        nullableField(out, "forge", r.forge(), true, 4);
        nullableField(out, "java", r.java(), true, 4);
        nullableField(out, "topology", r.topology(), true, 4);
        nullableField(out, "probeBuild", r.probeBuild(), true, 4);
        nullableField(out, "processCommandHint", r.processCommandHint(), true, 4);
        out.append("    \"loadedMods\": [");
        List<String> mods = new ArrayList<>(r.loadedMods());
        Collections.sort(mods);
        for (int i = 0; i < mods.size(); i++) {
            if (i > 0) out.append(',');
            out.append('\"').append(escape(mods.get(i))).append('\"');
        }
        out.append("]\n");
        out.append("  }\n");
        out.append("}\n");
        return out.toString();
    }

    private static boolean runtimeAttested(RuntimeInfo info) {
        return info.minecraft() != null && !info.minecraft().isBlank()
                && info.forge() != null && !info.forge().isBlank()
                && !"unknown".equalsIgnoreCase(info.forge())
                && info.java() != null && !info.java().isBlank()
                && info.topology() != null && !info.topology().isBlank()
                && info.probeBuild() != null && info.probeBuild().startsWith("sha256:")
                && info.processCommandHint() != null && !info.processCommandHint().isBlank()
                && info.loadedMods() != null && !info.loadedMods().isEmpty();
    }

    private static void field(StringBuilder out, String key, String value, boolean comma) {
        nullableField(out, key, value, comma, 2);
    }

    private static void nullableField(
            StringBuilder out, String key, String value, boolean comma, int indent) {
        indent(out, indent);
        out.append('\"').append(escape(key)).append("\": ");
        if (value == null) {
            out.append("null");
        } else {
            out.append('\"').append(escape(value)).append('\"');
        }
        if (comma) out.append(',');
        out.append('\n');
    }

    private static void numberField(StringBuilder out, String key, long value, boolean comma) {
        indent(out, 2);
        out.append('\"').append(escape(key)).append("\": ").append(value);
        if (comma) out.append(',');
        out.append('\n');
    }

    private static void boolField(
            StringBuilder out, String key, boolean value, boolean comma, int indent) {
        indent(out, indent);
        out.append('\"').append(escape(key)).append("\": ").append(value);
        if (comma) out.append(',');
        out.append('\n');
    }

    private static void indent(StringBuilder out, int n) {
        out.append(" ".repeat(Math.max(0, n)));
    }

    private static String escape(String value) {
        if (value == null) return "";
        StringBuilder out = new StringBuilder(value.length() + 16);
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            switch (c) {
                case '\"' -> out.append("\\\"");
                case '\\' -> out.append("\\\\");
                case '\b' -> out.append("\\b");
                case '\f' -> out.append("\\f");
                case '\n' -> out.append("\\n");
                case '\r' -> out.append("\\r");
                case '\t' -> out.append("\\t");
                default -> {
                    if (c < 0x20) {
                        out.append(String.format("\\u%04x", (int) c));
                    } else {
                        out.append(c);
                    }
                }
            }
        }
        return out.toString();
    }
}
