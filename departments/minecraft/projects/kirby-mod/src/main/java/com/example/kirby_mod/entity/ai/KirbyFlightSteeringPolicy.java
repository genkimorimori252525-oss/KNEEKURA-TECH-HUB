package com.example.kirby_mod.entity.ai;

/** Pure, deterministic horizontal detour selection for Kirby's flight. */
public final class KirbyFlightSteeringPolicy {

    private static final double[] OFFSETS_DEGREES = {
            0.0D, 35.0D, -35.0D, 70.0D, -70.0D, 110.0D, -110.0D, 180.0D
    };

    private KirbyFlightSteeringPolicy() {}

    public static int candidateCount() {
        return OFFSETS_DEGREES.length;
    }

    public static Direction candidateDirection(double desiredX, double desiredZ, int index) {
        if (index < 0 || index >= OFFSETS_DEGREES.length) {
            throw new IllegalArgumentException("candidate index out of range");
        }
        double length = Math.sqrt(desiredX * desiredX + desiredZ * desiredZ);
        if (length < 1.0E-8D) return new Direction(0.0D, 0.0D);
        double x = desiredX / length;
        double z = desiredZ / length;
        double radians = Math.toRadians(OFFSETS_DEGREES[index]);
        double cos = Math.cos(radians);
        double sin = Math.sin(radians);
        return new Direction(x * cos - z * sin, x * sin + z * cos);
    }

    public static Decision select(double desiredX, double desiredZ, boolean[] clear) {
        if (clear == null || clear.length != OFFSETS_DEGREES.length) {
            throw new IllegalArgumentException("clear flags must match candidate count");
        }
        double desiredLength = Math.sqrt(desiredX * desiredX + desiredZ * desiredZ);
        if (desiredLength < 1.0E-8D) {
            return new Decision(0.0D, 0.0D, -1, 0.0D, 0, false);
        }
        int blocked = 0;
        for (int i = 0; i < clear.length; i++) {
            if (!clear[i]) {
                blocked++;
                continue;
            }
            Direction direction = candidateDirection(desiredX, desiredZ, i);
            return new Decision(direction.x(), direction.z(), i,
                    OFFSETS_DEGREES[i], blocked, true);
        }
        return new Decision(0.0D, 0.0D, -1, 0.0D, blocked, false);
    }

    public record Direction(double x, double z) {}

    public record Decision(
            double x,
            double z,
            int candidateIndex,
            double offsetDegrees,
            int blockedDirections,
            boolean hasDirection) {

        public boolean avoidingObstacle() {
            return hasDirection && candidateIndex > 0;
        }
    }
}
