package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import java.util.Objects;

/** Finite, exact-context guard for original-invocation capture. No AI is called here. */
public final class KneekuraDebugDecisionBurstBudget {
    public static final int MAX_TICKS = 200;
    public static final int MAX_EVENTS = 256;
    public static final int MAX_BYTES = 512 * 1024;
    public static final int MAX_EVENT_BYTES = 32 * 1024;
    public record Context(String sessionId, String runId, String snapshotId, int processEpoch,
                          long arenaEpoch, long selectionRevision, String subjectUuid, String dimension) {
        public Context {
            for (String value : new String[] {sessionId,runId,snapshotId,subjectUuid,dimension}) {
                if (value == null || value.isBlank() || value.length() > 512)
                    throw new IllegalArgumentException("Invalid burst identity");
            }
            if (processEpoch < 1 || arenaEpoch < 0 || selectionRevision < 1)
                throw new IllegalArgumentException("Invalid burst epoch/revision");
        }
    }
    private final Context context;
    private final long startTick;
    private final long endTick;
    private final int eventLimit;
    private final int byteLimit;
    private long lastTick;
    private int events;
    private int bytes;
    private String reason;

    public KneekuraDebugDecisionBurstBudget(Context context, long startTick, int ticks, int events, int bytes) {
        this.context = Objects.requireNonNull(context);
        if (startTick < 0 || startTick > Long.MAX_VALUE - MAX_TICKS
                || ticks < 1 || ticks > MAX_TICKS || events < 1 || events > MAX_EVENTS
                || bytes < 1 || bytes > MAX_BYTES) throw new IllegalArgumentException("Invalid burst limits");
        this.startTick = startTick;
        endTick = startTick + ticks;
        lastTick = startTick;
        eventLimit = events;
        byteLimit = bytes;
    }

    /** Check before building an expensive event. Must be called on its owning server thread. */
    public boolean allows(Context current, long tick) {
        if (reason != null) return false;
        if (!context.equals(current)) { reason = "CONTEXT_CHANGED"; return false; }
        if (tick < lastTick) { reason = "CLOCK_CHANGED"; return false; }
        if (tick >= endTick) { reason = "WINDOW_ENDED"; return false; }
        if (events >= eventLimit) { reason = "EVENT_BUDGET"; return false; }
        lastTick = tick;
        return true;
    }

    /** Reserve exactly the serialized event size; a closed guard can never be rearmed. */
    public boolean claim(Context current, long tick, int eventBytes) {
        if (!allows(current,tick)) return false;
        if (eventBytes < 1 || eventBytes > MAX_EVENT_BYTES) { reason = "EVENT_BYTE_LIMIT"; return false; }
        if (eventBytes > byteLimit - bytes) { reason = "BYTE_BUDGET"; return false; }
        events++;
        bytes += eventBytes;
        return true;
    }

    public void close(String detail) { if (reason == null) reason = Objects.requireNonNull(detail); }
    public Context context() { return context; }
    public String reason() { return reason; }
    public long startTick() { return startTick; }
    public long endTickExclusive() { return endTick; }
    public int events() { return events; }
    public int bytes() { return bytes; }
}
