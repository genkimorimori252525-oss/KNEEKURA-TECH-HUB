package dev.kneekura.fivedifficulties.core.legacy;

/**
 * Version-neutral container for a legacy X1 shot definition.
 *
 * Numeric type/color fields intentionally remain numeric until the exact X1 mapping is repinned.
 */
public record LegacyShotSpec(
        int legacyType,
        int legacyColor,
        double speed,
        double acceleration,
        double maxSpeed,
        double gravity,
        double scale,
        double damage,
        boolean homing,
        double homingStrength,
        int delayTicks,
        int lifetimeTicks,
        int bounceCount
) {
    public LegacyShotSpec {
        finite(speed, "speed");
        finite(acceleration, "acceleration");
        finite(maxSpeed, "maxSpeed");
        finite(gravity, "gravity");
        finite(scale, "scale");
        finite(damage, "damage");
        finite(homingStrength, "homingStrength");
        if (speed < 0.0) throw new IllegalArgumentException("speed < 0");
        if (maxSpeed < 0.0) throw new IllegalArgumentException("maxSpeed < 0");
        if (scale <= 0.0) throw new IllegalArgumentException("scale <= 0");
        if (damage < 0.0) throw new IllegalArgumentException("damage < 0");
        if (homingStrength < 0.0) throw new IllegalArgumentException("homingStrength < 0");
        if (delayTicks < 0) throw new IllegalArgumentException("delayTicks < 0");
        if (lifetimeTicks <= 0) throw new IllegalArgumentException("lifetimeTicks <= 0");
        if (bounceCount < 0) throw new IllegalArgumentException("bounceCount < 0");
    }

    private static void finite(double value, String name) {
        if (!Double.isFinite(value)) throw new IllegalArgumentException(name + " must be finite");
    }
}
