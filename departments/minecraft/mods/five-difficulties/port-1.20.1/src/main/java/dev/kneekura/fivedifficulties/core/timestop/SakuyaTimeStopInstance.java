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
        TimeStopFlags flags
) {
    public SakuyaTimeStopInstance {
        if (stopId == null || sourceEntityId == null || center == null || flags == null) throw new NullPointerException();
        if (!Double.isFinite(range) || range < 0.0) throw new IllegalArgumentException("invalid range");
        if (startedAtTick < 0) throw new IllegalArgumentException("startedAtTick < 0");
        if (durationTicks <= 0) throw new IllegalArgumentException("durationTicks <= 0");
    }

    public boolean contains(Vec3d position) {
        Vec3d delta = position.subtract(center);
        return delta.lengthSquared() <= range * range;
    }

    public boolean isActiveAt(int tick) {
        return tick >= startedAtTick && tick < startedAtTick + durationTicks;
    }

    public int remainingTicks(int tick) {
        return Math.max(0, startedAtTick + durationTicks - tick);
    }
}
