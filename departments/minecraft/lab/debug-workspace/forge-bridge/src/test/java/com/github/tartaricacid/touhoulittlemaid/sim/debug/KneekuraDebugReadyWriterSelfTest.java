package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class KneekuraDebugReadyWriterSelfTest {
    private KneekuraDebugReadyWriterSelfTest() {
    }

    public static void main(String[] args) throws Exception {
        disabledEnvironmentIsQuiet();
        enabledEnvironmentRequiresIdentity();
        readyManifestBindsIdentityAndAttestation();
        readyManifestCannotBeSilentlyRewritten();
        System.out.println("KneekuraDebugReadyWriterSelfTest OK");
    }

    private static void disabledEnvironmentIsQuiet() {
        KneekuraDebugEnv.Config config = KneekuraDebugEnv.fromEnvironment(Map.of());
        check(!config.enabled(), "missing enable flag must keep debug disabled");
        check(config.worldName() == null, "disabled config must not invent a world");
    }

    private static void enabledEnvironmentRequiresIdentity() {
        Map<String, String> env = new HashMap<>();
        env.put(KneekuraDebugEnv.ENV_ENABLED, "1");
        boolean failed = false;
        try {
            KneekuraDebugEnv.fromEnvironment(env);
        } catch (IllegalArgumentException expected) {
            failed = true;
        }
        check(failed, "enabled debug environment without identity must fail");
    }

    private static void readyManifestBindsIdentityAndAttestation() throws Exception {
        Path root = Files.createTempDirectory("kneekura-debug-ready");
        Path runDir = root.resolve("run");
        Path ready = runDir.resolve("ready.json");

        Map<String, String> env = baseEnv(root, runDir, ready);
        KneekuraDebugEnv.Config config = KneekuraDebugEnv.fromEnvironment(env);

        KneekuraDebugReadyWriter.ReadyState state = state("INTEGRATED_SERVER");
        KneekuraDebugReadyWriter.write(config, state);

        String json = Files.readString(ready);
        contains(json, "\"protocolVersion\": \"KNEEKURA_DEBUG_READY_V1\"");
        contains(json, "\"debugSessionId\": \"sess-test\"");
        contains(json, "\"runId\": \"run-test\"");
        contains(json, "\"runSnapshotId\": \"snapshot-test\"");
        contains(json, "\"worldName\": \"KNEEKURA_DEBUG_WORLD\"");
        contains(json, "\"processEpoch\": 3");
        contains(json, "\"handshakeNonce\": \"0123456789abcdef0123456789abcdef\"");
        contains(json, "\"status\": \"DEBUG_READY\"");
        contains(json, "\"jvmStartedAt\": \"2026-09-18T00:00:00Z\"");
        contains(json, "\"debugWorldReady\": true");
        contains(json, "\"runtimeAttested\": true");
        contains(json, "\"topology\": \"INTEGRATED_SERVER\"");
        contains(json, "\"processCommandHint\": \"java\"");
        contains(json, "\"touhou_little_maid@1.0\"");

        KneekuraDebugReadyWriter.write(config, state);
    }

    private static void readyManifestCannotBeSilentlyRewritten() throws Exception {
        Path root = Files.createTempDirectory("kneekura-debug-ready-rewrite");
        Path runDir = root.resolve("run");
        Path ready = runDir.resolve("ready.json");

        KneekuraDebugEnv.Config config =
                KneekuraDebugEnv.fromEnvironment(baseEnv(root, runDir, ready));

        KneekuraDebugReadyWriter.write(config, state("INTEGRATED_SERVER"));

        boolean failed = false;
        try {
            KneekuraDebugReadyWriter.write(config, state("REMOTE_CLIENT"));
        } catch (java.io.IOException expected) {
            failed = true;
        }
        check(failed, "different READY content must not overwrite existing manifest");
    }

    private static Map<String, String> baseEnv(Path root, Path runDir, Path ready) {
        Map<String, String> env = new HashMap<>();
        env.put(KneekuraDebugEnv.ENV_ENABLED, "1");
        env.put(KneekuraDebugEnv.ENV_SESSION, "sess-test");
        env.put(KneekuraDebugEnv.ENV_RUN, "run-test");
        env.put(KneekuraDebugEnv.ENV_PROCESS_EPOCH, "3");
        env.put(KneekuraDebugEnv.ENV_RUN_SNAPSHOT_ID, "snapshot-test");
        env.put(KneekuraDebugEnv.ENV_NONCE, "0123456789abcdef0123456789abcdef");
        env.put(KneekuraDebugEnv.ENV_READY_FILE, ready.toAbsolutePath().toString());
        env.put(KneekuraDebugEnv.ENV_RUN_DIR, runDir.toAbsolutePath().toString());
        env.put(KneekuraDebugEnv.ENV_RUNTIME_ROOT, root.toAbsolutePath().toString());
        env.put(
                KneekuraDebugEnv.ENV_EVIDENCE_RAW_DIR,
                root.resolve("evidence").resolve("raw").toAbsolutePath().toString());
        env.put(
                KneekuraDebugEnv.ENV_TARGET_FILE,
                runDir.resolve("control").resolve("target.json").toAbsolutePath().toString());
        env.put(
                KneekuraDebugEnv.ENV_SHUTDOWN_REQUEST_FILE,
                runDir.resolve("control").resolve("shutdown-request.json").toAbsolutePath().toString());
        env.put(
                KneekuraDebugEnv.ENV_SHUTDOWN_ACK_FILE,
                runDir.resolve("control").resolve("shutdown-ack.json").toAbsolutePath().toString());
        env.put(KneekuraDebugEnv.ENV_WORLD_NAME, "KNEEKURA_DEBUG_WORLD");
        return env;
    }

    private static KneekuraDebugReadyWriter.ReadyState state(String topology) {
        KneekuraDebugReadyWriter.Milestones milestones =
                new KneekuraDebugReadyWriter.Milestones(
                        "2026-09-18T00:00:00Z",
                        "2026-09-18T00:00:01Z",
                        "2026-09-18T00:00:02Z",
                        "2026-09-18T00:00:03Z",
                        "2026-09-18T00:00:04Z",
                        "2026-09-18T00:00:05Z"
                );
        KneekuraDebugReadyWriter.RuntimeInfo runtime =
                new KneekuraDebugReadyWriter.RuntimeInfo(
                        "1.20.1",
                        "47.x",
                        "17",
                        topology,
                        "sha256:0123456789abcdef",
                        "java",
                        List.of("forge@47.x", "touhou_little_maid@1.0")
                );
        return new KneekuraDebugReadyWriter.ReadyState(1234L, milestones, runtime);
    }

    private static void contains(String text, String expected) {
        check(text.contains(expected), "missing: " + expected + "\n" + text);
    }

    private static void check(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }
}
