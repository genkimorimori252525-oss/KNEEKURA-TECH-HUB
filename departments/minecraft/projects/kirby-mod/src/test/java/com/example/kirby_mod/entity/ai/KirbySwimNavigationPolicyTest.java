package com.example.kirby_mod.entity.ai;

public final class KirbySwimNavigationPolicyTest {

    public static void main(String[] args) {
        testAlignedWaypointAllowsPropulsion();
        testSharpTurnPausesPropulsion();
        testTargetMovementThresholdIsDeterministic();
    }

    private static void testAlignedWaypointAllowsPropulsion() {
        check(KirbySwimNavigationPolicy.canPropel(
                        0.0D, 0.0D, 1.0D,
                        0.2D, 0.1D, 1.0D),
                "a waypoint near the look direction should allow propulsion");
    }

    private static void testSharpTurnPausesPropulsion() {
        check(!KirbySwimNavigationPolicy.canPropel(
                        0.0D, 0.0D, 1.0D,
                        1.0D, 0.0D, 0.0D),
                "a sharp turn should pause propulsion until Kirby turns");
        check(!KirbySwimNavigationPolicy.canPropel(
                        0.0D, 0.0D, 0.0D,
                        1.0D, 0.0D, 0.0D),
                "an invalid look vector must not activate propulsion");
    }

    private static void testTargetMovementThresholdIsDeterministic() {
        check(!KirbySwimNavigationPolicy.targetMoved(
                        0.0D, 0.0D, 0.0D,
                        1.5D, 0.0D, 0.0D, 1.5D),
                "movement exactly on the threshold should not force a replan");
        check(KirbySwimNavigationPolicy.targetMoved(
                        0.0D, 0.0D, 0.0D,
                        1.5001D, 0.0D, 0.0D, 1.5D),
                "movement beyond the threshold should force a replan");
        check(KirbySwimNavigationPolicy.targetMoved(
                        Double.NaN, Double.NaN, Double.NaN,
                        0.0D, 0.0D, 0.0D, 1.5D),
                "an uninitialized target must force the first plan");
    }

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
}
