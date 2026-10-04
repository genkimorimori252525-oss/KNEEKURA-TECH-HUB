package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.function.LongSupplier;

/** Source-owner maintenance seam; no request ingress or experimental action authority. */
final class KneekuraDebugTankRotationController {
    static final int CELLS_PER_TICK = 256;
    static final long TICK_WORK_BUDGET_NANOS = 25_000_000L;
    static final long MAX_EPOCH = 9007199254740991L;
    enum Phase { PREFLIGHT, GENERATING, VERIFYING, VERIFIED, OUTCOME_UNKNOWN }
    record Cell(int x, int y, int z) {}
    record Geometry(int x, int y, int z, int width, int height, int depth) {
        Geometry {
            if (width < 1 || width > 64 || height < 1 || height > 64 || depth < 1 || depth > 64
                    || (long) width * height * depth > 65536
                    || (long) (width + 2) * (height + 2) * (depth + 2) > 100000
                    || (long) x - 1 < -29999984 || (long) x + width > 29999984
                    || (long) z - 1 < -29999984 || (long) z + depth > 29999984
                    || (long) y - 1 < -64 || (long) y + height > 319) {
                throw new IllegalArgumentException("INVALID_TANK_ROTATION_GEOMETRY");
            }
        }
        int allocationCells() { return (width + 2) * (height + 2) * (depth + 2); }
        int innerCells() { return width * height * depth; }
        Cell cell(int index) {
            if (index < 0 || index >= allocationCells()) throw new IllegalArgumentException("INVALID_TANK_CELL_INDEX");
            int sx = width + 2, sz = depth + 2;
            return new Cell(x - 1 + index % sx, y - 1 + index / (sx * sz), z - 1 + index / sx % sz);
        }
        boolean inside(Cell cell) {
            return cell.x() >= x && cell.x() < x + width && cell.y() >= y && cell.y() < y + height
                    && cell.z() >= z && cell.z() < z + depth;
        }
        boolean overlaps(Geometry other) {
            return (long) x - 1 <= (long) other.x + other.width && (long) other.x - 1 <= (long) x + width
                    && (long) y - 1 <= (long) other.y + other.height && (long) other.y - 1 <= (long) y + height
                    && (long) z - 1 <= (long) other.z + other.depth && (long) other.z - 1 <= (long) z + depth;
        }
    }
    record Plan(Geometry next, List<Geometry> priorRegions, long previousEpoch, long issuedNanos, long deadlineNanos) {
        Plan {
            Objects.requireNonNull(next); priorRegions = List.copyOf(priorRegions);
            long duration = deadlineNanos - issuedNanos;
            if (priorRegions.isEmpty() || priorRegions.size() > 16 || previousEpoch < 0 || previousEpoch >= MAX_EPOCH
                    || duration <= 0 || duration > 120_000_000_000L) throw new IllegalArgumentException("INVALID_TANK_ROTATION_PLAN");
            for (Geometry prior : priorRegions) if (next.overlaps(prior)) throw new IllegalArgumentException("TANK_ROTATION_REGION_OVERLAP");
        }
    }
    /** Counters include only cells whose delegate and following authority check returned normally. */
    record Snapshot(Phase phase, int cursor, int preflightCells, int generationCells, int verifiedCells,
                    long nextEpoch, String geometryFingerprint, String error, boolean unknownPersisted) {}
    interface Backend {
        void guard() throws IOException;
        void requireQuiet() throws IOException;
        void preflight(Cell cell, boolean interior) throws IOException;
        void generate(Cell cell, boolean interior) throws IOException;
        String verify(Cell cell, boolean interior) throws IOException;
        void reserve(Plan plan) throws IOException;
        void publishVerified(Plan plan, String fingerprint) throws IOException;
        void unknown(Snapshot snapshot) throws IOException;
    }
    private final Plan plan;
    private final Backend backend;
    private final LongSupplier clock;
    private Phase phase = Phase.PREFLIGHT;
    private int cursor, preflightCells, generationCells, verifiedCells;
    private long lastTick = -1;
    private String fingerprint, error;
    private boolean unknownPersisted, executing;
    private MessageDigest digest;
    KneekuraDebugTankRotationController(Plan plan, Backend backend, LongSupplier clock) {
        this.plan = Objects.requireNonNull(plan); this.backend = Objects.requireNonNull(backend); this.clock = Objects.requireNonNull(clock);
    }
    Snapshot snapshot() { return new Snapshot(phase, cursor, preflightCells, generationCells, verifiedCells, plan.previousEpoch() + 1, fingerprint, error, unknownPersisted); }
    private boolean terminal() { return phase == Phase.VERIFIED || phase == Phase.OUTCOME_UNKNOWN; }
    private void requireAuthority() throws IOException {
        if (terminal()) throw new IOException("ROTATION_REVOKED_DURING_CALLBACK");
        backend.guard();
        long elapsed = clock.getAsLong() - plan.issuedNanos();
        if (elapsed < 0 || elapsed >= plan.deadlineNanos() - plan.issuedNanos()) throw new IOException("TANK_ROTATION_LEASE_EXPIRED_OR_CLOCK_CHANGED");
        if (terminal()) throw new IOException("ROTATION_REVOKED_DURING_CALLBACK");
    }
    Snapshot onTick(long tick) {
        if (terminal()) return snapshot();
        if (executing) return unknown("TANK_ROTATION_REENTRANT_TICK");
        executing = true;
        try {
            long tickStarted = clock.getAsLong();
            requireAuthority();
            if (tick < 0 || tick > MAX_EPOCH || lastTick >= 0 && tick != lastTick + 1) throw new IOException("TANK_ROTATION_TICK_DISCONTINUITY");
            lastTick = tick;
            backend.requireQuiet(); requireAuthority();
            int end = Math.min(cursor + CELLS_PER_TICK, plan.next().allocationCells());
            while (cursor < end) {
                requireAuthority(); backend.requireQuiet(); requireAuthority();
                Cell cell = plan.next().cell(cursor); boolean interior = plan.next().inside(cell);
                switch (phase) {
                    case PREFLIGHT -> { backend.preflight(cell, interior); requireAuthority(); preflightCells++; }
                    case GENERATING -> { backend.generate(cell, interior); requireAuthority(); generationCells++; }
                    case VERIFYING -> {
                        String observed = backend.verify(cell, interior); requireAuthority();
                        if (observed == null || observed.isEmpty() || observed.length() > 256) throw new IOException("INVALID_TANK_VERIFICATION_TOKEN");
                        digest.update((cell.x() + "," + cell.y() + "," + cell.z() + ":" + observed + "\n").getBytes(StandardCharsets.UTF_8)); verifiedCells++;
                    }
                    default -> throw new IOException("INVALID_TANK_ROTATION_PHASE");
                }
                cursor++;
                // Yield only after the delegate and its following authority check completed.
                // A synchronous delegate or boundary save may itself exceed this scheduling budget.
                if (clock.getAsLong() - tickStarted >= TICK_WORK_BUDGET_NANOS) break;
            }
            if (cursor == plan.next().allocationCells()) {
                requireAuthority(); backend.requireQuiet(); requireAuthority();
                switch (phase) {
                    case PREFLIGHT -> { backend.reserve(plan); requireAuthority(); phase = Phase.GENERATING; cursor = 0; }
                    case GENERATING -> { digest = sha256(); phase = Phase.VERIFYING; cursor = 0; }
                    case VERIFYING -> {
                        fingerprint = HexFormat.of().formatHex(digest.digest());
                        backend.publishVerified(plan, fingerprint); requireAuthority(); phase = Phase.VERIFIED;
                    }
                    default -> throw new IOException("INVALID_TANK_ROTATION_PHASE");
                }
            }
        } catch (IOException | RuntimeException failure) { unknown(failure.getMessage() == null ? failure.getClass().getSimpleName() : failure.getMessage()); }
        finally { executing = false; }
        return snapshot();
    }
    Snapshot revoke(String reason) { return terminal() ? snapshot() : unknown(reason); }
    private Snapshot unknown(String reason) {
        if (terminal()) return snapshot();
        phase = Phase.OUTCOME_UNKNOWN; error = bounded(reason); digest = null;
        try { backend.unknown(snapshot()); unknownPersisted = true; }
        catch (IOException | RuntimeException failure) { error = bounded(error + ";UNKNOWN_PERSISTENCE_FAILED"); }
        return snapshot();
    }
    private static String bounded(String reason) { String s = reason == null ? "UNKNOWN" : reason; return s.length() <= 256 ? s : s.substring(0, 256); }
    private static MessageDigest sha256() { try { return MessageDigest.getInstance("SHA-256"); } catch (NoSuchAlgorithmException impossible) { throw new AssertionError(impossible); } }
}
