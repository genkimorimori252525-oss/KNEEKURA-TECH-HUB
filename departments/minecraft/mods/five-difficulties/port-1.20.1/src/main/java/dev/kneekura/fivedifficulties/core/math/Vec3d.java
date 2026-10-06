package dev.kneekura.fivedifficulties.core.math;

/**
 * Small Minecraft-independent vector used by preservation-core tests and oracles.
 */
public record Vec3d(double x, double y, double z) {
    public static final Vec3d ZERO = new Vec3d(0.0, 0.0, 0.0);

    public Vec3d {
        requireFinite(x, "x");
        requireFinite(y, "y");
        requireFinite(z, "z");
    }

    public Vec3d add(Vec3d other) {
        return new Vec3d(x + other.x, y + other.y, z + other.z);
    }

    public Vec3d subtract(Vec3d other) {
        return new Vec3d(x - other.x, y - other.y, z - other.z);
    }

    public Vec3d scale(double factor) {
        requireFinite(factor, "factor");
        return new Vec3d(x * factor, y * factor, z * factor);
    }

    public double lengthSquared() {
        return x * x + y * y + z * z;
    }

    public double length() {
        return Math.sqrt(lengthSquared());
    }

    public Vec3d normalized() {
        double len = length();
        if (len <= 1.0e-12) {
            throw new IllegalStateException("Cannot normalize a zero-length vector");
        }
        return scale(1.0 / len);
    }

    /** Minecraft-style look vector: yaw 0 points +Z, pitch +90 points -Y. */
    public static Vec3d fromYawPitchDegrees(double yawDegrees, double pitchDegrees) {
        requireFinite(yawDegrees, "yawDegrees");
        requireFinite(pitchDegrees, "pitchDegrees");
        double yaw = Math.toRadians(yawDegrees);
        double pitch = Math.toRadians(pitchDegrees);
        double cosPitch = Math.cos(pitch);
        return new Vec3d(
                -Math.sin(yaw) * cosPitch,
                -Math.sin(pitch),
                Math.cos(yaw) * cosPitch
        );
    }

    public double yawDegrees() {
        return Math.toDegrees(Math.atan2(-x, z));
    }

    public double pitchDegrees() {
        return Math.toDegrees(Math.asin(-normalized().y));
    }

    private static void requireFinite(double value, String field) {
        if (!Double.isFinite(value)) {
            throw new IllegalArgumentException(field + " must be finite");
        }
    }
}
