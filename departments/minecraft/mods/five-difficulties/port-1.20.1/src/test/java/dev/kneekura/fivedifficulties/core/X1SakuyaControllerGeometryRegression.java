package dev.kneekura.fivedifficulties.core;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1SakuyaControllerGeometry;

public final class X1SakuyaControllerGeometryRegression {
    public static void main(String[] args) {
        Vec3d source = new Vec3d(10.0, 64.0, 20.0);

        Vec3d level = X1SakuyaControllerGeometry.center(source, 1.62, 0.0, 0.0);
        close(level.x(), 10.6, "yaw0 x");
        close(level.y(), 65.12, "yaw0 y");
        close(level.z(), 20.0 + Math.cos(Math.toRadians(-30.0)) * 1.2, "yaw0 z");

        Vec3d right = X1SakuyaControllerGeometry.center(source, 1.62, 90.0, 0.0);
        close(right.x(), 10.0 - Math.sin(Math.toRadians(60.0)) * 1.2, "yaw90 x");
        close(right.z(), 20.0 + Math.cos(Math.toRadians(60.0)) * 1.2, "yaw90 z");

        Vec3d lookingDown = X1SakuyaControllerGeometry.center(source, 1.62, 0.0, 90.0);
        close(lookingDown.y(), 63.92, "pitch90 y");

        System.out.println("X1_SAKUYA_CONTROLLER_GEOMETRY_REGRESSION_PASS");
    }

    private static void close(double actual, double expected, String message) {
        if (Math.abs(actual - expected) > 1.0e-9) {
            throw new AssertionError(message + ": " + actual + " != " + expected);
        }
    }
}
