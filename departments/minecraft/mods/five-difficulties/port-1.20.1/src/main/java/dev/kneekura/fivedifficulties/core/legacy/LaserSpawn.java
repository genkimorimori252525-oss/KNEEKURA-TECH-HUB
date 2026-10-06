package dev.kneekura.fivedifficulties.core.legacy;

import dev.kneekura.fivedifficulties.core.math.Vec3d;

public record LaserSpawn(
        int tick,
        long sequence,
        Vec3d origin,
        Vec3d direction,
        LegacyLaserSpec spec
) {
    public LaserSpawn {
        if (tick < 0) throw new IllegalArgumentException("tick < 0");
        if (origin == null || direction == null || spec == null) throw new NullPointerException();
        direction = direction.normalized();
    }
}
