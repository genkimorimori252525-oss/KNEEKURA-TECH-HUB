package com.example.kirby_mod.entity;

public final class KirbyMouthPhaseTest {

    public static void main(String[] args) {
        mapsEveryMouthCombatState();
        finishesInhaleAccordingToContents();
        onlyContainedPhasesSealMobs();
        validatesLifecycleTransitions();
    }

    private static void mapsEveryMouthCombatState() {
        assertEquals(KirbyMouthPhase.INHALE_PREP,
                KirbyMouthPhase.fromCombatState(CombatState.INHALE_PREP), "inhale prep");
        assertEquals(KirbyMouthPhase.INHALING,
                KirbyMouthPhase.fromCombatState(CombatState.INHALE), "inhaling");
        assertEquals(KirbyMouthPhase.INHALE_END,
                KirbyMouthPhase.fromCombatState(CombatState.INHALE_END), "inhale end");
        assertEquals(KirbyMouthPhase.HOLDING,
                KirbyMouthPhase.fromCombatState(CombatState.KEEP_HOLDING), "holding");
        assertEquals(KirbyMouthPhase.SWALLOWING,
                KirbyMouthPhase.fromCombatState(CombatState.KEEP_NOMIKOMI), "swallowing");
        assertEquals(KirbyMouthPhase.SPITTING,
                KirbyMouthPhase.fromCombatState(CombatState.KEEP_SPIT), "spitting");
        assertEquals(KirbyMouthPhase.EMPTY,
                KirbyMouthPhase.fromCombatState(CombatState.SLIDING), "non-mouth state");
    }

    private static void finishesInhaleAccordingToContents() {
        assertEquals(KirbyMouthPhase.INHALE_END, KirbyMouthPhase.afterInhale(0), "empty inhale");
        assertEquals(KirbyMouthPhase.HOLDING, KirbyMouthPhase.afterInhale(1), "captured inhale");
        assertEquals(KirbyMouthPhase.HOLDING, KirbyMouthPhase.afterInhale(5), "full inhale");
    }

    private static void onlyContainedPhasesSealMobs() {
        assertEquals(false, KirbyMouthPhase.EMPTY.sealsContents(), "empty");
        assertEquals(false, KirbyMouthPhase.INHALE_PREP.sealsContents(), "prep");
        assertEquals(true, KirbyMouthPhase.INHALING.sealsContents(), "inhaling with contents");
        assertEquals(true, KirbyMouthPhase.HOLDING.sealsContents(), "holding");
        assertEquals(true, KirbyMouthPhase.SWALLOWING.sealsContents(), "swallowing");
        assertEquals(true, KirbyMouthPhase.SPITTING.sealsContents(), "spitting transition");
    }

    private static void validatesLifecycleTransitions() {
        assertEquals(true, KirbyMouthTransitionPolicy.isAllowed(
                KirbyMouthPhase.EMPTY, KirbyMouthPhase.INHALE_PREP, 0), "start inhale");
        assertEquals(true, KirbyMouthTransitionPolicy.isAllowed(
                KirbyMouthPhase.INHALING, KirbyMouthPhase.INHALE_END, 0), "empty inhale end");
        assertEquals(true, KirbyMouthTransitionPolicy.isAllowed(
                KirbyMouthPhase.INHALING, KirbyMouthPhase.HOLDING, 1), "captured inhale end");
        assertEquals(true, KirbyMouthTransitionPolicy.isAllowed(
                KirbyMouthPhase.HOLDING, KirbyMouthPhase.SPITTING, 1), "spit");
        assertEquals(false, KirbyMouthTransitionPolicy.isAllowed(
                KirbyMouthPhase.EMPTY, KirbyMouthPhase.SWALLOWING, 0), "invalid empty swallow");
        assertEquals(false, KirbyMouthTransitionPolicy.isAllowed(
                KirbyMouthPhase.INHALING, KirbyMouthPhase.HOLDING, 0), "holding without contents");
        assertEquals(true, KirbyMouthTransitionPolicy.isAllowed(
                KirbyMouthPhase.SWALLOWING, KirbyMouthPhase.EMPTY, 0), "universal recovery");
    }

    private static void assertEquals(Object expected, Object actual, String label) {
        if (expected == null ? actual != null : !expected.equals(actual)) {
            throw new AssertionError(label + ": expected <" + expected + "> but was <" + actual + ">");
        }
    }

    private KirbyMouthPhaseTest() {}
}
