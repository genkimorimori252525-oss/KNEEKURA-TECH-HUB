package com.example.kirby_mod.entity;

public final class KirbyFallPhysicsTest {

    public static void main(String[] args) {
        usesOneThirdGravityWhileFalling();
        keepsExistingAscentGravity();
        terminalSpeedIsApproximatelyOneThirdOfVanilla();
        clampsExternalDownwardVelocity();
    }

    private static void usesOneThirdGravityWhileFalling() {
        assertNear(KirbyFallPhysics.VANILLA_GRAVITY / 3.0D,
                KirbyFallPhysics.flightGravity(-0.01D), "fall gravity");
    }

    private static void keepsExistingAscentGravity() {
        assertNear(0.04D, KirbyFallPhysics.flightGravity(0.2D), "ascent gravity");
    }

    private static void terminalSpeedIsApproximatelyOneThirdOfVanilla() {
        double kirby = 0.0D;
        double vanilla = 0.0D;
        for (int tick = 0; tick < 400; tick++) {
            kirby = KirbyFallPhysics.applyFlightFall(kirby);
            vanilla = (vanilla - KirbyFallPhysics.VANILLA_GRAVITY) * KirbyFallPhysics.AIR_DRAG;
        }
        double ratio = Math.abs(kirby / vanilla);
        if (ratio < 0.32D || ratio > 0.35D) {
            throw new AssertionError("terminal speed ratio: " + ratio);
        }
    }

    private static void clampsExternalDownwardVelocity() {
        assertNear(-KirbyFallPhysics.MAX_FALL_SPEED,
                KirbyFallPhysics.adjustVanillaFallVelocity(-10.0D), "fall-speed cap");
    }

    private static void assertNear(double expected, double actual, String label) {
        if (Math.abs(expected - actual) > 1.0E-9D) {
            throw new AssertionError(label + ": expected <" + expected + "> but was <" + actual + ">");
        }
    }
}
