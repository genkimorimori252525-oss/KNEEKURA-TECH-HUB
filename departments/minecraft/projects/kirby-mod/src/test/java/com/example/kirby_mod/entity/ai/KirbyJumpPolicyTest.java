package com.example.kirby_mod.entity.ai;

public final class KirbyJumpPolicyTest {

    public static void main(String[] args) {
        neverPlansAboveFiveBlocks();
        adjustsJumpOnlyHeightToTarget();
        usesTargetAndDistanceForFlightTakeoff();
        respectsMeasuredHeadroom();
        inverseImpulseMatchesRequestedHeight();
    }

    private static void neverPlansAboveFiveBlocks() {
        KirbyJumpPolicy.Decision decision = KirbyJumpPolicy.plan(100, 100.0D, 100.0D);
        assertNear(5.0D, decision.targetHeight(), 1.0E-9D, "height cap");
        if (KirbyJumpPolicy.peakHeight(decision.impulse()) > 5.000001D) {
            throw new AssertionError("impulse exceeded five-block cap");
        }
    }

    private static void adjustsJumpOnlyHeightToTarget() {
        KirbyJumpPolicy.Decision low = KirbyJumpPolicy.plan(1, 2.0D, 5.0D);
        KirbyJumpPolicy.Decision high = KirbyJumpPolicy.plan(4, 2.0D, 5.0D);
        if (low.hoverRequired() || high.hoverRequired()) {
            throw new AssertionError("jump-only targets must not request hover");
        }
        if (high.targetHeight() <= low.targetHeight()) {
            throw new AssertionError("higher target should produce higher jump");
        }
        KirbyJumpPolicy.Decision far = KirbyJumpPolicy.plan(1, 10.0D, 5.0D);
        if (far.targetHeight() <= low.targetHeight()) {
            throw new AssertionError("farther target should produce higher jump");
        }
    }

    private static void usesTargetAndDistanceForFlightTakeoff() {
        KirbyJumpPolicy.Decision near = KirbyJumpPolicy.plan(5, 1.0D, 5.0D);
        KirbyJumpPolicy.Decision far = KirbyJumpPolicy.plan(7, 14.0D, 5.0D);
        if (!near.hoverRequired() || !far.hoverRequired()) {
            throw new AssertionError("high targets must hand off to hover");
        }
        if (far.targetHeight() <= near.targetHeight()) {
            throw new AssertionError("far high target should use more takeoff height");
        }
    }

    private static void respectsMeasuredHeadroom() {
        KirbyJumpPolicy.Decision limited = KirbyJumpPolicy.plan(4, 3.0D, 2.25D);
        assertNear(2.25D, limited.targetHeight(), 1.0E-9D, "headroom limit");
        if (!limited.reason().contains("limited_by_headroom")) {
            throw new AssertionError("headroom limitation should be observable");
        }
    }

    private static void inverseImpulseMatchesRequestedHeight() {
        for (double height : new double[] {1.0D, 2.5D, 4.0D, 5.0D}) {
            double impulse = KirbyJumpPolicy.impulseForHeight(height);
            assertNear(height, KirbyJumpPolicy.peakHeight(impulse), 1.0E-6D,
                    "inverse height " + height);
        }
    }

    private static void assertNear(double expected, double actual, double tolerance, String label) {
        if (Math.abs(expected - actual) > tolerance) {
            throw new AssertionError(label + ": expected <" + expected + "> but was <" + actual + ">");
        }
    }
}
