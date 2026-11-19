package com.example.kirby_mod.entity.ai;

public final class KirbySwimMotionPolicyTest {

    public static void main(String[] args) {
        testUsesFacingDirectionIncludingVerticalAxis();
        testNormalizesFacingDirection();
        testNoInputUsesIdleDamping();
    }

    private static void testUsesFacingDirectionIncludingVerticalAxis() {
        KirbySwimMotionPolicy.Decision result = KirbySwimMotionPolicy.decide(
                0.0D, 1.0D, 1.0D,
                0.0D, 0.0D, 0.0D,
                1.0D, 0.25D);
        check(result.active(), "movement input should activate swimming");
        check(result.velocityY() > 0.0D, "upward look should produce upward motion");
        check(close(result.velocityY(), result.velocityZ()),
                "equal look components should produce equal velocity components");
    }

    private static void testNormalizesFacingDirection() {
        KirbySwimMotionPolicy.Decision unit = KirbySwimMotionPolicy.decide(
                1.0D, 0.0D, 0.0D,
                0.0D, 0.0D, 0.0D,
                1.0D, 0.25D);
        KirbySwimMotionPolicy.Decision scaled = KirbySwimMotionPolicy.decide(
                20.0D, 0.0D, 0.0D,
                0.0D, 0.0D, 0.0D,
                1.0D, 0.25D);
        check(close(unit.velocityX(), scaled.velocityX()),
                "look vector magnitude must not change swim speed");
    }

    private static void testNoInputUsesIdleDamping() {
        KirbySwimMotionPolicy.Decision result = KirbySwimMotionPolicy.decide(
                0.0D, 0.0D, 1.0D,
                0.4D, -0.2D, 0.1D,
                0.0D, 0.25D);
        check(!result.active(), "zero input should use idle state");
        check(close(result.velocityX(), 0.3D), "idle motion should be damped");
        check(close(result.velocityY(), -0.15D), "vertical idle motion should be damped");
    }

    private static boolean close(double left, double right) {
        return Math.abs(left - right) < 1.0E-9D;
    }

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
}
