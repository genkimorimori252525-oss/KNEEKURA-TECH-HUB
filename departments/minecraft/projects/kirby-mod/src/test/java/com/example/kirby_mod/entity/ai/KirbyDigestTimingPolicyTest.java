package com.example.kirby_mod.entity.ai;

public final class KirbyDigestTimingPolicyTest {

    public static void main(String[] args) {
        waitsForFullSecond();
        becomesReadyAtOneSecond();
        remainsReadyAfterDeadline();
    }

    private static void waitsForFullSecond() {
        assertEquals(false, KirbyDigestTimingPolicy.readyForDecision(19),
                "19 ticks");
    }

    private static void becomesReadyAtOneSecond() {
        assertEquals(20, KirbyDigestTimingPolicy.HOLD_DECISION_TICKS,
                "one second in ticks");
        assertEquals(true, KirbyDigestTimingPolicy.readyForDecision(20),
                "20 ticks");
    }

    private static void remainsReadyAfterDeadline() {
        assertEquals(true, KirbyDigestTimingPolicy.readyForDecision(21),
                "21 ticks");
    }

    private static void assertEquals(boolean expected, boolean actual, String label) {
        if (expected != actual) {
            throw new AssertionError(label + ": expected <" + expected
                    + "> but was <" + actual + ">");
        }
    }

    private static void assertEquals(int expected, int actual, String label) {
        if (expected != actual) {
            throw new AssertionError(label + ": expected <" + expected
                    + "> but was <" + actual + ">");
        }
    }

    private KirbyDigestTimingPolicyTest() {}
}
