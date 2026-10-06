package dev.kneekura.fivedifficulties.core.legacy;

import dev.kneekura.fivedifficulties.core.math.Vec3d;

/** Small reusable geometry helpers. Exact X1 call sites will be ported on top of these primitives. */
public final class LegacyPatterns {
    private LegacyPatterns() {}

    public static LegacyPattern fan(
            LegacyShotSpec spec,
            int periodTicks,
            int normalCount,
            double normalSpreadDegrees,
            int focusedCount,
            double focusedSpreadDegrees
    ) {
        if (spec == null) throw new NullPointerException("spec");
        if (periodTicks <= 0) throw new IllegalArgumentException("periodTicks <= 0");
        if (normalCount <= 0 || focusedCount <= 0) throw new IllegalArgumentException("count <= 0");
        if (!Double.isFinite(normalSpreadDegrees) || normalSpreadDegrees < 0.0) throw new IllegalArgumentException("normalSpreadDegrees");
        if (!Double.isFinite(focusedSpreadDegrees) || focusedSpreadDegrees < 0.0) throw new IllegalArgumentException("focusedSpreadDegrees");

        return (tick, context, sink) -> {
            if (tick % periodTicks != 0) return;
            int count = context.focused() ? focusedCount : normalCount;
            double spread = context.focused() ? focusedSpreadDegrees : normalSpreadDegrees;
            double baseYaw = context.aimDirection().yawDegrees();
            double basePitch = context.aimDirection().pitchDegrees();
            for (int i = 0; i < count; i++) {
                double offset = count == 1 ? 0.0 : (-spread * 0.5) + (spread * i / (count - 1.0));
                Vec3d velocity = Vec3d.fromYawPitchDegrees(baseYaw + offset, basePitch).scale(spec.speed());
                long sequence = (((long) tick) << 32) ^ (i & 0xffffffffL);
                sink.shot(new ShotSpawn(tick, sequence, context.origin(), velocity, spec));
            }
        };
    }
}
