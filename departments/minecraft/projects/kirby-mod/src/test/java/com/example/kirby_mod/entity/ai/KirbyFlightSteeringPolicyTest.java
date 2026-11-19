package com.example.kirby_mod.entity.ai;

public final class KirbyFlightSteeringPolicyTest {

    public static void main(String[] args) {
        selectsDirectRouteWhenClear();
        selectsNearestDetourDeterministically();
        stopsWhenEveryDirectionIsBlocked();
    }

    private static void selectsDirectRouteWhenClear() {
        boolean[] clear = new boolean[KirbyFlightSteeringPolicy.candidateCount()];
        clear[0] = true;
        KirbyFlightSteeringPolicy.Decision decision =
                KirbyFlightSteeringPolicy.select(1.0D, 0.0D, clear);
        assertEquals(0, decision.candidateIndex(), "direct candidate");
        assertNear(1.0D, decision.x(), "direct x");
        assertNear(0.0D, decision.z(), "direct z");
    }

    private static void selectsNearestDetourDeterministically() {
        boolean[] clear = new boolean[KirbyFlightSteeringPolicy.candidateCount()];
        clear[2] = true;
        clear[3] = true;
        KirbyFlightSteeringPolicy.Decision decision =
                KirbyFlightSteeringPolicy.select(1.0D, 0.0D, clear);
        assertEquals(2, decision.candidateIndex(), "ordered detour candidate");
        assertEquals(2, decision.blockedDirections(), "blocked directions");
        assertTrue(decision.avoidingObstacle(), "avoidance flag");
    }

    private static void stopsWhenEveryDirectionIsBlocked() {
        boolean[] clear = new boolean[KirbyFlightSteeringPolicy.candidateCount()];
        KirbyFlightSteeringPolicy.Decision decision =
                KirbyFlightSteeringPolicy.select(0.0D, 1.0D, clear);
        assertTrue(!decision.hasDirection(), "no direction");
        assertEquals(KirbyFlightSteeringPolicy.candidateCount(),
                decision.blockedDirections(), "all blocked");
        assertNear(0.0D, decision.x(), "blocked x");
        assertNear(0.0D, decision.z(), "blocked z");
    }

    private static void assertNear(double expected, double actual, String label) {
        if (Math.abs(expected - actual) > 1.0E-9D) {
            throw new AssertionError(label + ": expected <" + expected + "> but was <" + actual + ">");
        }
    }

    private static void assertEquals(Object expected, Object actual, String label) {
        if (expected == null ? actual != null : !expected.equals(actual)) {
            throw new AssertionError(label + ": expected <" + expected + "> but was <" + actual + ">");
        }
    }

    private static void assertTrue(boolean value, String label) {
        if (!value) throw new AssertionError(label);
    }

    private KirbyFlightSteeringPolicyTest() {}
}
