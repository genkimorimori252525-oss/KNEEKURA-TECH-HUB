package dev.kneekura.fivedifficulties.core.legacy;

import dev.kneekura.fivedifficulties.core.math.Vec3d;

public record ShotSpawn(
        int tick,
        long sequence,
        Vec3d origin,
        Vec3d velocity,
        LegacyShotSpec spec
) {
    public ShotSpawn {
        if (tick < 0) throw new IllegalArgumentException("tick < 0");
        if (origin == null || velocity == null || spec == null) throw new NullPointerException();
    }
}
