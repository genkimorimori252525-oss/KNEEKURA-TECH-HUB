package com.example.kirby_mod.entity.ai;

public final class KirbyGroundMovementPolicyTest {

    public static void main(String[] args) {
        selectsWalkAndRunByDistance();
        keepsRunAndStopInsideHysteresisBands();
        returnsIdleWithoutTarget();
    }

    private static void selectsWalkAndRunByDistance() {
        assertEquals(KirbyLocomotionMode.IDLE,
                KirbyGroundMovementPolicy.select(true, 2.5D, KirbyLocomotionMode.WALK),
                "stop distance");
        assertEquals(KirbyLocomotionMode.WALK,
                KirbyGroundMovementPolicy.select(true, 4.0D, KirbyLocomotionMode.IDLE),
                "walk distance");
        assertEquals(KirbyLocomotionMode.RUN,
                KirbyGroundMovementPolicy.select(true, 8.0D, KirbyLocomotionMode.WALK),
                "run enter distance");
    }

    private static void keepsRunAndStopInsideHysteresisBands() {
        assertEquals(KirbyLocomotionMode.RUN,
                KirbyGroundMovementPolicy.select(true, 6.0D, KirbyLocomotionMode.RUN),
                "run retained");
        assertEquals(KirbyLocomotionMode.WALK,
                KirbyGroundMovementPolicy.select(true, 5.9D, KirbyLocomotionMode.RUN),
                "run exits");
        assertEquals(KirbyLocomotionMode.IDLE,
                KirbyGroundMovementPolicy.select(true, 2.9D, KirbyLocomotionMode.IDLE),
                "stop retained");
        assertEquals(KirbyLocomotionMode.WALK,
                KirbyGroundMovementPolicy.select(true, 3.0D, KirbyLocomotionMode.IDLE),
                "stop exits");
    }

    private static void returnsIdleWithoutTarget() {
        assertEquals(KirbyLocomotionMode.IDLE,
                KirbyGroundMovementPolicy.select(false, 100.0D, KirbyLocomotionMode.RUN),
                "no target");
    }

    private static void assertEquals(Object expected, Object actual, String label) {
        if (expected == null ? actual != null : !expected.equals(actual)) {
            throw new AssertionError(label + ": expected <" + expected + "> but was <" + actual + ">");
        }
    }

    private KirbyGroundMovementPolicyTest() {}
}
