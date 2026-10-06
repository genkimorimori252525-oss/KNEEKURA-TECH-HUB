package dev.kneekura.fivedifficulties.core;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1HomingMath;

public final class X1HomingMathRegression {
    public static void main(String[] args) {
        Vec3d forward = new Vec3d(0, 0, 1);
        Vec3d right = new Vec3d(1, 0, 0);

        close(X1HomingMath.angleDegrees(forward, right), 90.0, "right angle");
        close(X1HomingMath.targetScore(10.0, 0.0), 0.0, "direct-ahead score");
        close(X1HomingMath.targetScore(10.0, 180.0), 10.0, "behind score");

        Vec3d turned = X1HomingMath.turnToward(forward, right, 4.0);
        close(X1HomingMath.angleDegrees(forward, turned), 4.0, "bounded turn");
        close(X1HomingMath.angleDegrees(turned, right), 86.0, "turns toward target");
        close(turned.length(), 1.0, "unit direction");

        close(X1HomingMath.legacyShotOriginY(64.0, 1.62, 0.0), 65.12, "level origin");
        close(X1HomingMath.legacyShotOriginY(64.0, 1.62, 90.0), 65.12, "down origin");
        close(X1HomingMath.legacyShotOriginY(64.0, 1.62, -90.0), 66.12, "up origin");

        Vec3d opposite = X1HomingMath.turnToward(forward, new Vec3d(0, 0, -1), 4.0);
        check(opposite.equals(forward), "anti-parallel fails safe without NaN");

        System.out.println("X1_HOMING_MATH_REGRESSION_PASS");
    }

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    private static void close(double actual, double expected, String message) {
        if (Math.abs(actual - expected) > 1.0e-9) {
            throw new AssertionError(message + ": " + actual + " != " + expected);
        }
    }
}
