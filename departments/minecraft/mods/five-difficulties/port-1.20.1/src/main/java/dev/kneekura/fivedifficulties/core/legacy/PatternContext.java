package dev.kneekura.fivedifficulties.core.legacy;

import dev.kneekura.fivedifficulties.core.math.Vec3d;

public record PatternContext(
        Vec3d origin,
        Vec3d aimDirection,
        boolean focused,
        long deterministicSeed
) {
    public PatternContext {
        if (origin == null || aimDirection == null) throw new NullPointerException();
        aimDirection = aimDirection.normalized();
    }
}
