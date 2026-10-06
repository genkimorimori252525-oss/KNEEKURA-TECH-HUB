package dev.kneekura.fivedifficulties.core.timestop;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import java.util.UUID;

public record SakuyaTimeStopInstance(
        UUID stopId,
        UUID sourceEntityId,
        Vec3d center,
        double range,
        int startedAtTick,
        int durationTicks,
        TimeStopFlags flags,
        TimeStopShape shape,
        TimeDomainMode mode
) {
    public SakuyaTimeStopInstance {
        if (stopId == null || sourceEntityId == null || center == null || flags == null || shape == null || mode == null) {
            throw new NullPointerException();
        }
        if (!Double.isFinite(range) || range < 0.0) throw new IllegalArgumentException("invalid range");
        if (startedAtTick < 0) throw new IllegalArgumentException("startedAtTick < 0");
        if (durationTicks == 0 || durationTicks < -1) throw new IllegalArgumentException("durationTicks must be -1 or positive");
    }

    /** Backward-compatible engineering constructor: spherical full stop. */
    public SakuyaTimeStopInstance(
            UUID stopId,
            UUID sourceEntityId,
            Vec3d center,
            double range,
            int startedAtTick,
            int durationTicks,
            TimeStopFlags flags
    ) {
        this(stopId, sourceEntityId, center, range, startedAtTick, durationTicks, flags, TimeStopShape.SPHERE, TimeDomainMode.FULL_STOP);
    }

    public boolean contains(Vec3d position) {
        Vec3d delta = position.subtract(center);
        return switch (shape) {
            case SPHERE -> delta.lengthSquared() <= range * range;
            case AABB -> Math.abs(delta.x()) <= range
                    && Math.abs(delta.y()) <= range
                    && Math.abs(delta.z()) <= range;
        };
    }

    public boolean isUnbounded() {
        return durationTicks == -1;
    }

    public boolean isActiveAt(int tick) {
        if (tick < startedAtTick) return false;
        return isUnbounded() || ((long) tick) < ((long) startedAtTick + durationTicks);
    }

    public boolean isExpiredAt(int tick) {
        return !isUnbounded() && ((long) tick) >= ((long) startedAtTick + durationTicks);
    }

    public int remainingTicks(int tick) {
        if (isUnbounded()) return Integer.MAX_VALUE;
        long remaining = ((long) startedAtTick + durationTicks) - tick;
        return (int) Math.max(0L, Math.min(Integer.MAX_VALUE, remaining));
    }

    public int elapsedTicks(int tick) {
        return Math.max(0, tick - startedAtTick);
    }

    /** Modern half-speed scheduler phase chosen to match X1 count=0 first processing phase. */
    public boolean shouldCancelEntityTickForMode(int tick) {
        return switch (mode) {
            case FULL_STOP -> true;
            case HALF_SPEED -> (elapsedTicks(tick) & 1) == 0;
        };
    }
}
