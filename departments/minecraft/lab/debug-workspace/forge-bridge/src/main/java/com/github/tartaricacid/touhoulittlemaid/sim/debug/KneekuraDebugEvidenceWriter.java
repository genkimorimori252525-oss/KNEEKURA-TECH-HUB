package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import org.slf4j.Logger;
import com.mojang.logging.LogUtils;
import com.google.gson.Gson;
import com.google.gson.JsonObject;

import javax.annotation.Nullable;
import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.UUID;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.TimeUnit;

/**
 * Low-perturbation raw Observation writer for the autonomous Debug Workspace.
 *
 * <p>Runtime threads only build a bounded JSON row and enqueue it. Disk I/O is
 * performed by one daemon writer thread. Queue overflow is never hidden:
 * writerSeq still advances, so the next accepted row exposes a sequence gap to
 * the Node-side Evidence Store.
 *
 * <p>This class writes runtime facts only. It never writes Findings,
 * Hypotheses, or Conclusions; those belong to the Node-side Evidence Broker.
 */
public final class KneekuraDebugEvidenceWriter {
    public static final int FORMAT_VERSION = 1;
    public static final long HEARTBEAT_INTERVAL_TICKS = 20L;
    public static final int QUEUE_CAPACITY = 2048;
    public static final int MAX_ROW_BYTES = 64 * 1024;

    private static final Object LOCK = new Object();
    private static final Gson GSON = new Gson();
    private static final Logger LOGGER = LogUtils.getLogger();
    private static int pendingImageBytes;
    private static final int MAX_PENDING_IMAGE_BYTES = 16 * 1024 * 1024;
    private record QueuedRow(String line, CompletableFuture<String> durable, KneekuraDebugImageArtifact image) { }
    private static final ArrayBlockingQueue<QueuedRow> QUEUE =
            new ArrayBlockingQueue<>(QUEUE_CAPACITY);
    private static final long CLOCK_ORIGIN_NANOS = System.nanoTime();
    private static final Instant CLOCK_ORIGIN_WALL = Instant.now();
    @Nullable
    private static final Instant PROCESS_STARTED_AT =
            ProcessHandle.current().info().startInstant().orElse(null);

    @Nullable
    private static volatile BufferedWriter out;
    @Nullable
    private static String identityKey;
    @Nullable
    private static Path file;

    private static long seq;
    private static long droppedTotal;
    private static long lastAnyClientTick = Long.MIN_VALUE;
    private static long lastAnyServerTick = Long.MIN_VALUE;
    private static volatile boolean broken;
    private static volatile boolean workerStarted;
    private static volatile boolean accepting = true;
    private static volatile boolean sealed;
    private static volatile boolean writerBusy;

    private KneekuraDebugEvidenceWriter() {
    }

    public static void maybeClientHeartbeat(
            KneekuraDebugEnv.Config config,
            long localClientTick,
            @Nullable Long gameTime,
            boolean paused
    ) {
        if (config == null || !config.enabled() || broken || sealed) {
            return;
        }

        synchronized (LOCK) {
            if (lastAnyClientTick != Long.MIN_VALUE
                    && localClientTick - lastAnyClientTick < HEARTBEAT_INTERVAL_TICKS) {
                return;
            }

            JsonObject payload = new JsonObject();
            payload.addProperty("heartbeat", true);
            payload.addProperty("paused", paused);
            payload.addProperty("localClientTick", localClientTick);

            try {
                writeObservationLocked(
                        config,
                        localClientTick,
                        gameTime,
                        "L0",
                        "CLIENT_TICK",
                        "GLOBAL_HEALTH",
                        null,
                        "CLIENT",
                        "ClientTickEvent.END",
                        payload);
            } catch (Throwable e) {
                failWriterLocked("raw client heartbeat enqueue failed", e);
            }
        }
    }

    public static void maybeServerHeartbeat(
            KneekuraDebugEnv.Config config,
            long localServerTick,
            @Nullable Long gameTime
    ) {
        if (config == null || !config.enabled() || broken || sealed) {
            return;
        }

        synchronized (LOCK) {
            if (lastAnyServerTick != Long.MIN_VALUE
                    && localServerTick - lastAnyServerTick < HEARTBEAT_INTERVAL_TICKS) {
                return;
            }

            JsonObject payload = new JsonObject();
            payload.addProperty("heartbeat", true);
            payload.addProperty("localServerTick", localServerTick);

            try {
                writeObservationLocked(
                        config,
                        localServerTick,
                        gameTime,
                        "L0",
                        "SERVER_TICK",
                        "GLOBAL_HEALTH",
                        null,
                        "SERVER",
                        "ServerTickEvent.END",
                        payload);
            } catch (Throwable e) {
                failWriterLocked("raw server heartbeat enqueue failed", e);
            }
        }
    }

    public static void recordGlobalObserved(
            KneekuraDebugEnv.Config config,
            long localTick,
            @Nullable Long gameTime,
            String level,
            String lane,
            String sourceSide,
            String method,
            JsonObject payload
    ) throws IOException {
        if (config == null || !config.enabled()) {
            return;
        }

        synchronized (LOCK) {
            if (broken) {
                return;
            }
            writeObservationLocked(
                    config,
                    localTick,
                    gameTime,
                    level,
                    lane,
                    "GLOBAL_HEALTH",
                    null,
                    sourceSide,
                    method,
                    payload == null ? new JsonObject() : payload);
        }
    }

    public static void recordEntityObserved(
            KneekuraDebugEnv.Config config,
            long localClientTick,
            @Nullable Long gameTime,
            String level,
            String lane,
            String method,
            UUID entityUuid,
            JsonObject payload
    ) throws IOException {
        recordEntityObserved(
                config,
                localClientTick,
                gameTime,
                level,
                lane,
                "CLIENT",
                method,
                entityUuid,
                payload);
    }

    public static void recordEntityObserved(
            KneekuraDebugEnv.Config config,
            long localTick,
            @Nullable Long gameTime,
            String level,
            String lane,
            String sourceSide,
            String method,
            UUID entityUuid,
            JsonObject payload
    ) throws IOException {
        if (config == null || !config.enabled() || entityUuid == null) {
            return;
        }

        synchronized (LOCK) {
            if (broken || sealed) {
                return;
            }
            writeObservationLocked(
                    config,
                    localTick,
                    gameTime,
                    level,
                    lane,
                    "ENTITY_UUID",
                    entityUuid,
                    sourceSide,
                    method,
                    payload == null ? new JsonObject() : payload);
        }
    }

    /** Selected owner event, preserving its actual Arena epoch on the existing bounded writer. */
    public static void recordOwnedEntityObserved(
            KneekuraDebugEnv.Config config, long arenaEpoch, long localTick, Long gameTime,
            String method, UUID entityUuid, JsonObject payload) throws IOException {
        if (config == null || !config.enabled() || entityUuid == null) return;
        synchronized (LOCK) {
            if (broken || sealed || !accepting) return;
            if (arenaEpoch < 0 || arenaEpoch > 9007199254740991L || localTick < 0)
                throw new IOException("INVALID_TRIGGER_OBSERVATION_EPOCH");
            writeObservationLocked(config, localTick, gameTime, "L1", "SERVER_ENTITY_STATE",
                    "ENTITY_UUID", entityUuid, "SERVER", method, payload.deepCopy(), arenaEpoch, null);
        }
    }

    /** Async durable Arena checkpoint, on the same existing raw evidence worker. */
    public static CompletableFuture<String> recordArenaObservedAsync(
            KneekuraDebugEnv.Config config, long arenaEpoch, long localTick, Long gameTime,
            String lane, String method, JsonObject payload) {
        CompletableFuture<String> proof = new CompletableFuture<>();
        synchronized (LOCK) {
            if (config == null || !config.enabled() || broken || sealed || !accepting ||
                    arenaEpoch < 0 || arenaEpoch > 9007199254740991L || localTick < 0) {
                proof.completeExceptionally(new IOException("ARENA_EVIDENCE_UNAVAILABLE"));
                return proof;
            }
            try {
                writeObservationLocked(config, localTick, gameTime, "L2", lane,
                        "GLOBAL_HEALTH", null, "SERVER", method,
                        payload == null ? new JsonObject() : payload.deepCopy(), arenaEpoch, proof);
            } catch (Exception e) { proof.completeExceptionally(e); }
        }
        return proof;
    }

    /** Image and observation are committed in order by the same bounded existing worker. */
    public static CompletableFuture<String> recordVisualObservedAsync(
            KneekuraDebugEnv.Config config, long arenaEpoch, long localTick, Long gameTime,
            byte[] png, JsonObject payload) {
        CompletableFuture<String> proof = new CompletableFuture<>();
        synchronized (LOCK) {
            if (config == null || !config.enabled() || broken || sealed || !accepting ||
                    arenaEpoch < 0 || localTick < 0 || payload == null) {
                proof.completeExceptionally(new IOException("VISUAL_EVIDENCE_UNAVAILABLE"));
                return proof;
            }
            try {
                KneekuraDebugImageArtifact image = png == null ? null : new KneekuraDebugImageArtifact(config.runDir(), png);
                if (image != null) {
                    if (pendingImageBytes + image.size() > MAX_PENDING_IMAGE_BYTES ||
                            !image.hash().equals(payload.get("imageHash").getAsString()) ||
                            payload.get("imageBytes").getAsInt() != image.size() ||
                            !("evidence/raw/visual/" + image.hash() + ".png").equals(payload.get("imagePath").getAsString()))
                        throw new IOException("VISUAL_ARTIFACT_BINDING_OR_QUEUE_BUDGET");
                    pendingImageBytes += image.size();
                    proof.whenComplete((value, error) -> { synchronized (LOCK) { pendingImageBytes -= image.size(); } });
                }
                writeObservationLocked(config, localTick, gameTime, "L2", "VISUAL_CAPTURE", "EXPERIMENT", null,
                        "CLIENT", png == null ? "KneekuraDebugCardinalCapture.finish" : "RenderLevelStageEvent.AFTER_LEVEL",
                        payload.deepCopy(), arenaEpoch, proof, image);
            } catch (Exception error) { proof.completeExceptionally(error); }
        }
        return proof;
    }

    /** Action path only. Render/camera callers use the asynchronous API. */
    public static String recordArenaObserved(
            KneekuraDebugEnv.Config config, long arenaEpoch, long localTick, Long gameTime,
            String lane, String method, JsonObject payload) throws IOException {
        try {
            return recordArenaObservedAsync(config, arenaEpoch, localTick, gameTime, lane, method, payload)
                    .get(1000L, TimeUnit.MILLISECONDS);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt(); throw new IOException("ARENA_EVIDENCE_INTERRUPTED", e);
        } catch (ExecutionException | TimeoutException e) {
            throw new IOException("ARENA_EVIDENCE_NOT_DURABLE", e);
        }
    }

    public record FlushResult(
            boolean clean,
            long finalWriterSeq,
            long droppedTotal,
            int remainingQueue,
            @Nullable String file
    ) {
    }

    public static FlushResult sealAndFlush(long timeoutMs) {
        long deadline = System.nanoTime()
                + TimeUnit.MILLISECONDS.toNanos(Math.max(0L, timeoutMs));

        synchronized (LOCK) {
            accepting = false;
        }

        while (System.nanoTime() < deadline) {
            if (QUEUE.isEmpty() && !writerBusy) {
                break;
            }
            try {
                Thread.sleep(10L);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }

        synchronized (LOCK) {
            boolean clean = !broken && QUEUE.isEmpty() && !writerBusy;
            try {
                if (out != null) {
                    out.flush();
                }
            } catch (Throwable e) {
                clean = false;
                LOGGER.error(
                        "[KNEEKURA-DEBUG] evidence flush during shutdown failed",
                        e);
            }

            sealed = true;
            if (!clean) {
                broken = true;
            }

            String fileName = file == null ? null : file.toString();
            int remaining = QUEUE.size();
            closeQuietlyLocked();

            return new FlushResult(
                    clean,
                    seq,
                    droppedTotal,
                    remaining,
                    fileName);
        }
    }

    private static void writeObservationLocked(
            KneekuraDebugEnv.Config config,
            long localTick,
            @Nullable Long gameTime,
            String level,
            String lane,
            String scopeKind,
            @Nullable UUID entityUuid,
            String sourceSide,
            String method,
            JsonObject payload
    ) throws IOException {
        writeObservationLocked(config, localTick, gameTime, level, lane, scopeKind,
                entityUuid, sourceSide, method, payload, 0L, null);
    }

    private static void writeObservationLocked(
            KneekuraDebugEnv.Config config,
            long localTick,
            @Nullable Long gameTime,
            String level,
            String lane,
            String scopeKind,
            @Nullable UUID entityUuid,
            String sourceSide,
            String method,
            JsonObject payload,
            long arenaEpoch,
            CompletableFuture<String> durable
    ) throws IOException {
        writeObservationLocked(config, localTick, gameTime, level, lane, scopeKind, entityUuid,
                sourceSide, method, payload, arenaEpoch, durable, null);
    }

    private static void writeObservationLocked(
            KneekuraDebugEnv.Config config, long localTick, Long gameTime, String level, String lane,
            String scopeKind, UUID entityUuid, String sourceSide, String method, JsonObject payload,
            long arenaEpoch, CompletableFuture<String> durable, KneekuraDebugImageArtifact image
    ) throws IOException {
        if (!accepting || sealed) {
            if (durable != null) durable.completeExceptionally(new IOException("EVIDENCE_SEALED"));
            return;
        }
        ensureOpenLocked(config);
        if (!accepting || sealed) {
            if (durable != null) durable.completeExceptionally(new IOException("EVIDENCE_SEALED"));
            return;
        }

        long nextSeq = ++seq;
        String writerId = writerId();
        Instant observedAt = Instant.now();

        JsonObject row = new JsonObject();
        row.addProperty("v", FORMAT_VERSION);
        row.addProperty("kind", "observation");
        row.addProperty("observationId", "obs:" + writerId + ":" + nextSeq);
        row.addProperty("debugSessionId", config.debugSessionId());
        row.addProperty("runId", config.runId());
        row.addProperty("runSnapshotId", config.runSnapshotId());
        row.addProperty("processEpoch", config.processEpoch());
        row.addProperty("arenaEpoch", arenaEpoch);
        row.addProperty("resourceEpoch", 0);
        row.addProperty("writerId", writerId);
        row.addProperty("writerSeq", nextSeq);
        row.addProperty("writerQueueDepth", QUEUE.size());
        row.addProperty("writerDroppedTotal", droppedTotal);
        row.addProperty("producerDeltaApplied", true);
        row.addProperty("level", level);
        row.addProperty("lane", lane);
        row.addProperty("observedAt", observedAt.toString());

        JsonObject clock = new JsonObject();
        clock.addProperty("domain", "JVM_PROCESS_MONOTONIC");
        clock.addProperty("processId", ProcessHandle.current().pid());
        if (PROCESS_STARTED_AT != null) {
            clock.addProperty(
                    "processStartedAt",
                    PROCESS_STARTED_AT.toString());
        }
        clock.addProperty(
                "monotonicOriginWallClock",
                CLOCK_ORIGIN_WALL.toString());
        clock.addProperty(
                "monotonicElapsedNanos",
                Math.max(0L, System.nanoTime() - CLOCK_ORIGIN_NANOS));
        clock.addProperty("wallClockSample", observedAt.toString());
        row.add("clock", clock);

        if (gameTime != null) {
            row.addProperty("gameTime", gameTime);
        }

        JsonObject scope = new JsonObject();
        scope.addProperty("kind", scopeKind);
        if ("EXPERIMENT".equals(scopeKind)) {
            scope.addProperty("experimentId", payload.getAsJsonObject("identity").get("experimentId").getAsString());
        }
        if (entityUuid != null) {
            scope.addProperty("entityUuid", entityUuid.toString());
        }
        row.add("scope", scope);

        JsonObject source = new JsonObject();
        source.addProperty("side", sourceSide);
        source.addProperty("method", method);
        row.add("source", source);

        row.addProperty("epistemicStatus", "OBSERVED");

        JsonObject completeness = new JsonObject();
        completeness.addProperty("status", "COMPLETE");
        completeness.addProperty("complete", true);
        row.add("completeness", completeness);

        row.add("payload", payload);

        String line = GSON.toJson(row);
        int bytes = line.getBytes(StandardCharsets.UTF_8).length;
        boolean accepted = false;

        if (bytes <= MAX_ROW_BYTES) {
            accepted = QUEUE.offer(new QueuedRow(line, durable, image));
        }

        if (!accepted) {
            if (durable != null) durable.completeExceptionally(new IOException("EVIDENCE_ROW_DROPPED"));
            droppedTotal++;
            logDropLocked(
                    bytes > MAX_ROW_BYTES ? "row-too-large" : "queue-full",
                    lane,
                    nextSeq,
                    bytes);
        }

        // An attempted row counts as activity for heartbeat suppression even if
        // it was dropped. The next accepted writerSeq exposes the loss.
        if ("CLIENT".equals(sourceSide)) {
            lastAnyClientTick = localTick;
        } else if ("SERVER".equals(sourceSide)) {
            lastAnyServerTick = localTick;
        }
    }

    private static void ensureOpenLocked(KneekuraDebugEnv.Config config) throws IOException {
        String key = config.identityKey();
        if (out != null && key.equals(identityKey)) {
            return;
        }

        if (out != null && (!QUEUE.isEmpty() || writerBusy)) {
            throw new IOException(
                    "cannot switch evidence identity while queued rows remain");
        }

        closeQuietlyLocked();
        identityKey = key;
        seq = 0L;
        droppedTotal = 0L;
        lastAnyClientTick = Long.MIN_VALUE;
        lastAnyServerTick = Long.MIN_VALUE;
        broken = false;
        accepting = true;
        sealed = false;
        writerBusy = false;
        QUEUE.clear();

        Path dir = config.evidenceRawDir();
        Files.createDirectories(dir);

        file = dir.resolve("forge-runtime-" + ProcessHandle.current().pid() + ".jsonl");
        if (Files.exists(file)) {
            throw new IOException("raw evidence file already exists for this run: " + file);
        }

        out = Files.newBufferedWriter(
                file,
                StandardCharsets.UTF_8,
                StandardOpenOption.CREATE_NEW,
                StandardOpenOption.WRITE);

        startWorkerLocked();
    }

    private static void startWorkerLocked() {
        if (workerStarted) {
            return;
        }
        workerStarted = true;

        Thread worker = new Thread(
                KneekuraDebugEvidenceWriter::writerLoop,
                "kneekura-evidence-writer");
        worker.setDaemon(true);
        worker.start();
    }

    private record ClaimedRow(QueuedRow row, BufferedWriter writer, Path file) { }

    /** Dequeue, busy ownership and exact output capture share the identity/shutdown lock. */
    private static ClaimedRow claimQueuedRow() {
        synchronized (LOCK) {
            if (broken || (sealed && QUEUE.isEmpty())) return null;
            QueuedRow row = QUEUE.poll();
            if (row == null) return null;
            writerBusy = true;
            return new ClaimedRow(row, out, file);
        }
    }

    private static void writerLoop() {
        while (true) {
            ClaimedRow claimed = claimQueuedRow();
            if (claimed == null) {
                if (broken || (sealed && QUEUE.isEmpty())) return;
                try { Thread.sleep(10L); }
                catch (InterruptedException e) { Thread.currentThread().interrupt(); return; }
                continue;
            }
            try {
                if (claimed.writer() == null || claimed.file() == null) {
                    synchronized (LOCK) {
                        droppedTotal++;
                        logDropLocked("writer-unavailable", "UNKNOWN", seq, claimed.row().line().length());
                    }
                    if (claimed.row().durable() != null) claimed.row().durable().completeExceptionally(new IOException("WRITER_UNAVAILABLE"));
                    continue;
                }
                if (claimed.row().image() != null) claimed.row().image().persist();
                KneekuraDebugDurability.write(claimed.file(), claimed.writer(), claimed.row().line(), claimed.row().durable());
            } catch (Throwable e) {
                if (claimed.row().durable() != null) claimed.row().durable().completeExceptionally(e);
                synchronized (LOCK) { failWriterLocked("async disk writer failed", e); }
                return;
            } finally {
                synchronized (LOCK) { writerBusy = false; }
            }
        }
    }

    private static String writerId() {
        return "forge-runtime:" + ProcessHandle.current().pid();
    }

    private static void logDropLocked(
            String reason,
            String lane,
            long writerSeq,
            int rowBytes
    ) {
        // Log at 1,2,4,8,... drops to avoid turning overload reporting into
        // another overload source.
        if (droppedTotal == 1 || (droppedTotal & (droppedTotal - 1)) == 0) {
            LOGGER.warn(
                    "[KNEEKURA-DEBUG] evidence row dropped reason={} lane={} seq={} bytes={} droppedTotal={} queue={}/{}",
                    reason,
                    lane,
                    writerSeq,
                    rowBytes,
                    droppedTotal,
                    QUEUE.size(),
                    QUEUE_CAPACITY);
        }
    }

    private static void failWriterLocked(String message, Throwable error) {
        broken = true;
        for (QueuedRow row : QUEUE) {
            if (row.durable() != null) row.durable().completeExceptionally(error);
        }
        LOGGER.error(
                "[KNEEKURA-DEBUG] " + message + "; disabling writer",
                error);
        closeQuietlyLocked();
    }

    private static void closeQuietlyLocked() {
        BufferedWriter writer = out;
        out = null;
        if (writer != null) {
            try {
                writer.flush();
            } catch (Throwable ignored) {
            }
            try {
                writer.close();
            } catch (Throwable ignored) {
            }
        }
    }
}
