package dev.kneekura.fivedifficulties.core.legacy;

/** Version-neutral laser state. Exact X1 flags can be appended after the oracle pass. */
public record LegacyLaserSpec(
        int legacyColor,
        double width,
        double length,
        double damage,
        int delayTicks,
        int lifetimeTicks,
        boolean fullBright
) {
    public LegacyLaserSpec {
        finite(width, "width");
        finite(length, "length");
        finite(damage, "damage");
        if (width <= 0.0) throw new IllegalArgumentException("width <= 0");
        if (length < 0.0) throw new IllegalArgumentException("length < 0");
        if (damage < 0.0) throw new IllegalArgumentException("damage < 0");
        if (delayTicks < 0) throw new IllegalArgumentException("delayTicks < 0");
        if (lifetimeTicks <= 0) throw new IllegalArgumentException("lifetimeTicks <= 0");
    }

    private static void finite(double value, String name) {
        if (!Double.isFinite(value)) throw new IllegalArgumentException(name + " must be finite");
    }
}
