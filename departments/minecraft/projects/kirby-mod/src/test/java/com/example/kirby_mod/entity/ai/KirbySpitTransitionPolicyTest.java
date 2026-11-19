package com.example.kirby_mod.entity.ai;

public final class KirbySpitTransitionPolicyTest {

    public static void main(String[] args) {
        acceptsCompleteLifecycle();
        acceptsLaunchFailureCleanup();
        rejectsLifecycleShortcuts();
        classifiesAbortReasons();
    }

    private static void acceptsCompleteLifecycle() {
        assertAllowed(KirbySpitState.IDLE, KirbySpitState.STARTING);
        assertAllowed(KirbySpitState.STARTING, KirbySpitState.FLYING);
        assertAllowed(KirbySpitState.FLYING, KirbySpitState.FINISHING);
        assertAllowed(KirbySpitState.FINISHING, KirbySpitState.IDLE);
    }

    private static void acceptsLaunchFailureCleanup() {
        assertAllowed(KirbySpitState.STARTING, KirbySpitState.FINISHING);
    }

    private static void rejectsLifecycleShortcuts() {
        assertRejected(KirbySpitState.IDLE, KirbySpitState.FLYING);
        assertRejected(KirbySpitState.FLYING, KirbySpitState.IDLE);
        assertRejected(KirbySpitState.FINISHING, KirbySpitState.STARTING);
        assertRejected(KirbySpitState.FLYING, KirbySpitState.FLYING);
    }

    private static void classifiesAbortReasons() {
        assertEquals(true, KirbySpitFinishReason.GOAL_INTERRUPTED.abortsMouth(),
                "goal interruption");
        assertEquals(true, KirbySpitFinishReason.KIRBY_REMOVED.abortsMouth(),
                "Kirby removal");
        assertEquals(false, KirbySpitFinishReason.TIMEOUT.abortsMouth(),
                "ordinary timeout");
        assertEquals(false, KirbySpitFinishReason.WALL_HIT.abortsMouth(),
                "ordinary wall hit");
    }

    private static void assertAllowed(KirbySpitState from, KirbySpitState to) {
        assertEquals(true, KirbySpitTransitionPolicy.isAllowed(from, to),
                from + " -> " + to);
    }

    private static void assertRejected(KirbySpitState from, KirbySpitState to) {
        assertEquals(false, KirbySpitTransitionPolicy.isAllowed(from, to),
                from + " -> " + to);
    }

    private static void assertEquals(boolean expected, boolean actual, String label) {
        if (expected != actual) {
            throw new AssertionError(label + ": expected <" + expected
                    + "> but was <" + actual + ">");
        }
    }

    private KirbySpitTransitionPolicyTest() {}
}
