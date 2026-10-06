package dev.kneekura.fivedifficulties.core.x1;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import java.util.ArrayList;
import java.util.List;

/**
 * Direct port of the X1 THShotLib.createWideShot direction math.
 */
public final class X1WideShotGeometry {
    private X1WideShotGeometry() {}

    public record Ray(double offsetDegrees, Vec3d direction, Vec3d spawnOffset) {}

    public static List<Ray> create(
            Vec3d aimDirection,
            int way,
            double wideAngleDegrees,
            double spawnDistance,
            double baseAngleDegrees
    ) {
        if (aimDirection == null) throw new NullPointerException("aimDirection");
        if (way < 2) throw new IllegalArgumentException("X1 wide shot requires way >= 2");
        if (!Double.isFinite(wideAngleDegrees)) throw new IllegalArgumentException("wideAngleDegrees");
        if (!Double.isFinite(spawnDistance) || spawnDistance < 0.0) throw new IllegalArgumentException("spawnDistance");
        if (!Double.isFinite(baseAngleDegrees)) throw new IllegalArgumentException("baseAngleDegrees");

        Vec3d angle = aimDirection.normalized();

        double yaw = Math.toDegrees(Math.atan2(angle.x(), angle.z()));
        double horizontal = Math.sqrt(angle.x() * angle.x() + angle.z() * angle.z());
        double pitch = Math.toDegrees(Math.atan2(angle.y(), horizontal));

        Vec3d rotateAxis = vecFromAngle(-yaw, -pitch + 90.0, 1.0).normalized();

        double current = -wideAngleDegrees / 2.0 + baseAngleDegrees;
        double span = wideAngleDegrees / (way - 1.0);

        List<Ray> result = new ArrayList<>(way);
        for (int i = 0; i < way; i++) {
            Vec3d direction = rotateAroundAxis(rotateAxis, angle, current).normalized();
            result.add(new Ray(current, direction, direction.scale(spawnDistance)));
            current += span;
        }
        return List.copyOf(result);
    }

    /**
     * Direct port of THShotLib.getVecFromAngle.
     */
    public static Vec3d vecFromAngle(double yawDegrees, double pitchDegrees, double force) {
        double yaw = Math.toRadians(yawDegrees);
        double pitch = Math.toRadians(pitchDegrees);
        return new Vec3d(
                -Math.sin(yaw) * Math.cos(pitch) * force,
                -Math.sin(pitch) * force,
                 Math.cos(yaw) * Math.cos(pitch) * force
        );
    }

    /**
     * Direct port of THShotLib.getVectorFromRotation (Rodrigues rotation matrix).
     */
    public static Vec3d rotateAroundAxis(Vec3d axis, Vec3d vector, double angleDegrees) {
        Vec3d a = axis.normalized();
        double x = a.x(), y = a.y(), z = a.z();
        double vx = vector.x(), vy = vector.y(), vz = vector.z();
        double angle = Math.toRadians(angleDegrees);
        double sin = Math.sin(angle);
        double cos = Math.cos(angle);
        double oneMinus = 1.0 - cos;

        double rx =
                (x * x * oneMinus + cos) * vx +
                (x * y * oneMinus - z * sin) * vy +
                (z * x * oneMinus + y * sin) * vz;
        double ry =
                (x * y * oneMinus + z * sin) * vx +
                (y * y * oneMinus + cos) * vy +
                (y * z * oneMinus - x * sin) * vz;
        double rz =
                (z * x * oneMinus - y * sin) * vx +
                (y * z * oneMinus + x * sin) * vy +
                (z * z * oneMinus + cos) * vz;

        return new Vec3d(rx, ry, rz);
    }
}
