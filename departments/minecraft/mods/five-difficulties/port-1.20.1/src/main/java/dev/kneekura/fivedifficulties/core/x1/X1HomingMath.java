package dev.kneekura.fivedifficulties.core.x1;

import dev.kneekura.fivedifficulties.core.math.Vec3d;

/** Exact scalar/vector math used by the red X1 homing amulet. */
public final class X1HomingMath {
    private X1HomingMath() {}

    public static double angleDegrees(Vec3d a, Vec3d b) {
        Vec3d an = a.normalized();
        Vec3d bn = b.normalized();
        double dot = clamp(an.x() * bn.x() + an.y() * bn.y() + an.z() * bn.z(), -1.0, 1.0);
        return Math.toDegrees(Math.acos(dot));
    }

    /** Direct port of THShotLib.halfAbsSin(angleSpanRadians). */
    public static double targetScore(double distance, double angleDegrees) {
        if (!Double.isFinite(distance) || distance < 0.0) throw new IllegalArgumentException("distance");
        double radians = Math.toRadians(Math.abs(angleDegrees));
        return distance * Math.abs(Math.sin(radians * 0.5));
    }

    /**
     * Turns current direction toward target by at most maxTurnDegrees.
     * The ordinary path matches EntityHomingAmulet: axis = current x target,
     * angle = acos(current,target), then Rodrigues rotation.
     *
     * Exact anti-parallel vectors have no defined legacy rotation axis; P2
     * fail-safely keeps the current direction instead of introducing NaN.
     */
    public static Vec3d turnToward(Vec3d current, Vec3d target, double maxTurnDegrees) {
        if (!Double.isFinite(maxTurnDegrees) || maxTurnDegrees < 0.0) {
            throw new IllegalArgumentException("maxTurnDegrees");
        }
        Vec3d c = current.normalized();
        Vec3d t = target.normalized();
        double angle = angleDegrees(c, t);
        if (angle <= 1.0e-9) return c;
        double turn = Math.min(angle, maxTurnDegrees);

        Vec3d axis = cross(c, t);
        if (axis.lengthSquared() <= 1.0e-18) {
            return c;
        }
        return X1WideShotGeometry.rotateAroundAxis(axis, c, turn).normalized();
    }

    public static Vec3d cross(Vec3d a, Vec3d b) {
        return new Vec3d(
                a.y() * b.z() - a.z() * b.y(),
                a.z() * b.x() - a.x() * b.z(),
                a.x() * b.y() - a.y() * b.x()
        );
    }

    /** Direct port of THShotLib.getPosYFromEye(living). */
    public static double legacyShotOriginY(double baseY, double eyeHeight, double pitchDegrees) {
        double pitch = Math.toRadians(pitchDegrees);
        return baseY + eyeHeight - 0.5 * Math.sin(pitch) - 0.5 * Math.cos(pitch);
    }

    private static double clamp(double value, double min, double max) {
        return Math.max(min, Math.min(max, value));
    }
}
