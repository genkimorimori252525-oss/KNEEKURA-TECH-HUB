package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.nio.charset.StandardCharsets;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.time.Instant;

/**
 * Run-bound clean evidence shutdown coordinator.
 *
 * <p>The Supervisor asks the Probe to stop accepting observations, drain the
 * bounded queue, flush/close the raw writer, and publish an ACK before the
 * Minecraft process is terminated.
 */
public final class KneekuraDebugShutdownCoordinator {
    private static final Gson GSON = new Gson();
    private static final long POLL_TICKS = 5L;
    private static final long FLUSH_TIMEOUT_MS = 5000L;

    private static long lastPollTick = Long.MIN_VALUE;
    private static boolean handled;

    private KneekuraDebugShutdownCoordinator() {
    }

    public static void onClientTick(
            KneekuraDebugEnv.Config config,
            long localClientTick
    ) {
        if (config == null || !config.enabled() || handled) {
            return;
        }

        if (lastPollTick != Long.MIN_VALUE
                && localClientTick - lastPollTick < POLL_TICKS) {
            return;
        }
        lastPollTick = localClientTick;

        Path requestFile = config.shutdownRequestFile();
        if (!Files.exists(requestFile)) {
            return;
        }

        try {
            JsonObject request = JsonParser.parseString(
                    Files.readString(requestFile, StandardCharsets.UTF_8)
            ).getAsJsonObject();

            validateRequest(config, request);
            if (!KneekuraDebugOwnerConnection.prepareShutdownClient(config)) return;

            KneekuraDebugEvidenceWriter.FlushResult flush =
                    KneekuraDebugEvidenceWriter.sealAndFlush(FLUSH_TIMEOUT_MS);

            JsonObject ack = new JsonObject();
            ack.addProperty("v", 1);
            ack.addProperty("debugSessionId", config.debugSessionId());
            ack.addProperty("runId", config.runId());
            ack.addProperty("runSnapshotId", config.runSnapshotId());
            ack.addProperty("processEpoch", config.processEpoch());
            ack.addProperty(
                    "status",
                    flush.clean()
                            ? "CLEAN_EVIDENCE_SHUTDOWN"
                            : "PARTIAL_EVIDENCE_SHUTDOWN");
            ack.addProperty("clean", flush.clean());
            ack.addProperty("ackedAt", Instant.now().toString());
            ack.addProperty("finalWriterSeq", flush.finalWriterSeq());
            ack.addProperty("writerDroppedTotal", flush.droppedTotal());
            ack.addProperty("remainingQueue", flush.remainingQueue());
            if (flush.file() != null) {
                ack.addProperty("rawEvidenceFile", flush.file());
            }

            writeAckAtomically(config.shutdownAckFile(), ack);
            handled = true;

            TouhouLittleMaid.LOGGER.info(
                    "[KNEEKURA-DEBUG] evidence shutdown ack clean={} finalSeq={} dropped={} remaining={}",
                    flush.clean(),
                    flush.finalWriterSeq(),
                    flush.droppedTotal(),
                    flush.remainingQueue());
        } catch (Throwable e) {
            TouhouLittleMaid.LOGGER.error(
                    "[KNEEKURA-DEBUG] shutdown request rejected or ACK failed: {}",
                    requestFile,
                    e);
        }
    }

    private static void validateRequest(
            KneekuraDebugEnv.Config config,
            JsonObject request
    ) {
        if (request.get("v").getAsInt() != 1) {
            throw new IllegalArgumentException("shutdown request v must be 1");
        }
        if (!config.debugSessionId().equals(
                request.get("debugSessionId").getAsString())) {
            throw new IllegalArgumentException(
                    "shutdown request debugSessionId mismatch");
        }
        if (!config.runId().equals(request.get("runId").getAsString())) {
            throw new IllegalArgumentException(
                    "shutdown request runId mismatch");
        }
        if (!config.runSnapshotId().equals(
                request.get("runSnapshotId").getAsString())) {
            throw new IllegalArgumentException(
                    "shutdown request runSnapshotId mismatch");
        }
        if (config.processEpoch()
                != request.get("processEpoch").getAsInt()) {
            throw new IllegalArgumentException(
                    "shutdown request processEpoch mismatch");
        }
    }

    private static void writeAckAtomically(
            Path target,
            JsonObject ack
    ) throws Exception {
        Files.createDirectories(target.getParent());
        String json = GSON.toJson(ack) + "\n";

        if (Files.exists(target)) {
            String existing = Files.readString(target, StandardCharsets.UTF_8);
            if (existing.equals(json)) {
                return;
            }
            throw new IllegalStateException(
                    "shutdown ACK already exists with different content: "
                            + target);
        }

        Path temp = target.resolveSibling(
                target.getFileName()
                        + ".tmp-"
                        + ProcessHandle.current().pid());

        Files.writeString(
                temp,
                json,
                StandardCharsets.UTF_8,
                StandardOpenOption.CREATE_NEW,
                StandardOpenOption.WRITE);

        try {
            try {
                Files.move(
                        temp,
                        target,
                        StandardCopyOption.ATOMIC_MOVE);
            } catch (AtomicMoveNotSupportedException e) {
                Files.move(temp, target);
            }
        } finally {
            Files.deleteIfExists(temp);
        }
    }
}
