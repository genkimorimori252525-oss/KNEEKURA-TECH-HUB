package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import java.nio.file.Path;
import java.util.Map;
import java.util.Objects;

public final class KneekuraDebugEnv {
    public static final String ENV_ENABLED = "KNEEKURA_DEBUG_ENABLED";
    public static final String ENV_SESSION = "KNEEKURA_DEBUG_SESSION_ID";
    public static final String ENV_RUN = "KNEEKURA_DEBUG_RUN_ID";
    public static final String ENV_PROCESS_EPOCH = "KNEEKURA_DEBUG_PROCESS_EPOCH";
    public static final String ENV_RUN_SNAPSHOT_ID = "KNEEKURA_DEBUG_RUN_SNAPSHOT_ID";
    public static final String ENV_NONCE = "KNEEKURA_DEBUG_HANDSHAKE_NONCE";
    public static final String ENV_READY_FILE = "KNEEKURA_DEBUG_READY_FILE";
    public static final String ENV_RUN_DIR = "KNEEKURA_DEBUG_RUN_DIR";
    public static final String ENV_RUNTIME_ROOT = "KNEEKURA_DEBUG_RUNTIME_ROOT";
    public static final String ENV_EVIDENCE_RAW_DIR = "KNEEKURA_DEBUG_EVIDENCE_RAW_DIR";
    public static final String ENV_TARGET_FILE = "KNEEKURA_DEBUG_TARGET_FILE";
    public static final String ENV_SHUTDOWN_REQUEST_FILE = "KNEEKURA_DEBUG_SHUTDOWN_REQUEST_FILE";
    public static final String ENV_SHUTDOWN_ACK_FILE = "KNEEKURA_DEBUG_SHUTDOWN_ACK_FILE";
    public static final String ENV_WORLD_NAME = "KNEEKURA_DEBUG_WORLD_NAME";

    public static final String ENV_OWNER_FILE = "KNEEKURA_DEBUG_OWNER_ENVELOPE_FILE";
    public static final String ENV_OWNER_HASH = "KNEEKURA_DEBUG_OWNER_ENVELOPE_SHA256";
    public record OwnerSetup(Path file, String sha256) { }

    private KneekuraDebugEnv() {
    }

    public record Config(
            boolean enabled,
            String debugSessionId,
            String runId,
            int processEpoch,
            String runSnapshotId,
            String handshakeNonce,
            Path readyFile,
            Path runDir,
            Path runtimeRoot,
            Path evidenceRawDir,
            Path targetFile,
            Path shutdownRequestFile,
            Path shutdownAckFile,
            String worldName,
            OwnerSetup ownerSetup
    ) {
        public Config(boolean enabled, String debugSessionId, String runId, int processEpoch, String runSnapshotId, String handshakeNonce, Path readyFile, Path runDir, Path runtimeRoot, Path evidenceRawDir, Path targetFile, Path shutdownRequestFile, Path shutdownAckFile, String worldName) {
            this(enabled, debugSessionId, runId, processEpoch, runSnapshotId, handshakeNonce, readyFile, runDir, runtimeRoot, evidenceRawDir, targetFile, shutdownRequestFile, shutdownAckFile, worldName, null);
        }
        public String identityKey() {
            if (!enabled) {
                return "disabled";
            }
            return debugSessionId + "|" + runId + "|" + runSnapshotId + "|" + processEpoch;
        }
    }

    public static Config fromSystemEnvironment() {
        return fromEnvironment(System.getenv());
    }

    static Config fromEnvironment(Map<String, String> env) {
        Objects.requireNonNull(env, "env");
        if (!isTrue(env.get(ENV_ENABLED))) {
            return new Config(
                    false,
                    null,
                    null,
                    0,
                    null,
                    null,
                    null,
                    null,
                    null,
                    null,
                    null,
                    null,
                    null,
                    null);
        }

        String session = required(env, ENV_SESSION);
        String run = required(env, ENV_RUN);
        String nonce = required(env, ENV_NONCE);
        int epoch = parsePositiveInt(required(env, ENV_PROCESS_EPOCH), ENV_PROCESS_EPOCH);
        String runSnapshotId = required(env, ENV_RUN_SNAPSHOT_ID);
        Path readyFile = absolutePath(required(env, ENV_READY_FILE), ENV_READY_FILE);
        Path runDir = absolutePath(required(env, ENV_RUN_DIR), ENV_RUN_DIR);
        Path runtimeRoot = absolutePath(required(env, ENV_RUNTIME_ROOT), ENV_RUNTIME_ROOT);
        Path evidenceRawDir = absolutePath(
                required(env, ENV_EVIDENCE_RAW_DIR),
                ENV_EVIDENCE_RAW_DIR);
        Path targetFile = absolutePath(
                required(env, ENV_TARGET_FILE),
                ENV_TARGET_FILE);
        Path shutdownRequestFile = absolutePath(
                required(env, ENV_SHUTDOWN_REQUEST_FILE),
                ENV_SHUTDOWN_REQUEST_FILE);
        Path shutdownAckFile = absolutePath(
                required(env, ENV_SHUTDOWN_ACK_FILE),
                ENV_SHUTDOWN_ACK_FILE);
        String worldName = required(env, ENV_WORLD_NAME);

        if (nonce.length() < 16) {
            throw new IllegalArgumentException(ENV_NONCE + " must be at least 16 characters");
        }

        OwnerSetup ownerSetup = null;
        if (env.containsKey(ENV_OWNER_FILE) || env.containsKey(ENV_OWNER_HASH)) {
            Path ownerFile = absolutePath(required(env, ENV_OWNER_FILE), ENV_OWNER_FILE);
            String ownerHash = required(env, ENV_OWNER_HASH);
            if (!ownerFile.equals(runDir.resolve("control/owner-envelope.json")) || !ownerHash.matches("[a-f0-9]{64}")) {
                throw new IllegalArgumentException("INVALID_OWNER_ENVELOPE_BINDING");
            }
            ownerSetup = new OwnerSetup(ownerFile, ownerHash);
        }
        return new Config(
                true,
                session,
                run,
                epoch,
                runSnapshotId,
                nonce,
                readyFile,
                runDir,
                runtimeRoot,
                evidenceRawDir,
                targetFile,
                shutdownRequestFile,
                shutdownAckFile,
                worldName,
                ownerSetup);
    }

    private static boolean isTrue(String value) {
        if (value == null) {
            return false;
        }
        String v = value.trim();
        return "1".equals(v) || "true".equalsIgnoreCase(v) || "yes".equalsIgnoreCase(v);
    }

    private static String required(Map<String, String> env, String key) {
        String value = env.get(key);
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException(key + " is required when debug mode is enabled");
        }
        return value.trim();
    }

    private static int parsePositiveInt(String value, String key) {
        try {
            int parsed = Integer.parseInt(value);
            if (parsed <= 0) {
                throw new NumberFormatException("not positive");
            }
            return parsed;
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException(key + " must be a positive integer", e);
        }
    }

    private static Path absolutePath(String value, String key) {
        Path path = Path.of(value).normalize();
        if (!path.isAbsolute()) {
            throw new IllegalArgumentException(key + " must be an absolute path");
        }
        return path;
    }
}
