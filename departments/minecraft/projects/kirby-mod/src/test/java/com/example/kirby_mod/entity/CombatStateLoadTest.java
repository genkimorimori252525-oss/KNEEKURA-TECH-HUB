package com.example.kirby_mod.entity;

public final class CombatStateLoadTest {

    public static void main(String[] args) {
        noneSurvivesLoad();
        temporaryStatesResetToNoneOnLoad();
        invalidSavedStateResetsToNoneOnLoad();
        crouchAndSlideUseLowProfileHitbox();
    }

    private static void noneSurvivesLoad() {
        assertEquals(CombatState.NONE,
                CombatState.loadSafeState(CombatState.NONE.ordinal()),
                "NONE should survive load");
    }

    private static void temporaryStatesResetToNoneOnLoad() {
        for (CombatState state : CombatState.values()) {
            if (state == CombatState.NONE) continue;
            assertEquals(CombatState.NONE,
                    CombatState.loadSafeState(state.ordinal()),
                    state + " should reset to NONE on load");
        }
    }

    private static void invalidSavedStateResetsToNoneOnLoad() {
        assertEquals(CombatState.NONE, CombatState.loadSafeState(-1), "negative saved state");
        assertEquals(CombatState.NONE, CombatState.loadSafeState(999), "out of range saved state");
    }

    private static void crouchAndSlideUseLowProfileHitbox() {
        for (CombatState state : CombatState.values()) {
            boolean expected = state.isCrouching() || state.isSliding();
            assertEquals(expected, state.usesLowProfileHitbox(), state + " low-profile hitbox");
        }
    }

    private static void assertEquals(Object expected, Object actual, String label) {
        if (expected == null ? actual != null : !expected.equals(actual)) {
            throw new AssertionError(label + ": expected <" + expected + "> but was <" + actual + ">");
        }
    }

    private CombatStateLoadTest() {}
}
