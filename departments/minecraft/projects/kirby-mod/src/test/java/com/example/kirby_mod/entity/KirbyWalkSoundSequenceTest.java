package com.example.kirby_mod.entity;

public final class KirbyWalkSoundSequenceTest {

    public static void main(String[] args) {
        firstWalkingStepUsesInitialSoundThenAlternates();
        idleForThirtyTicksResetsToInitialSound();
        slowerWalkingAdvancesStepPhaseMoreSlowly();
        runningUsesShorterIntervalAndHigherPitch();
        heldWalkUsesAnimationSpecificStepIntervals();
        heldWalkStillRespondsToMovementSpeed();
        changingGaitPreservesTheCurrentStepPhase();
    }

    private static void firstWalkingStepUsesInitialSoundThenAlternates() {
        KirbyWalkSoundSequence sequence = new KirbyWalkSoundSequence();

        assertEquals("kirby_walk_1", sequence.tick(true, false, 1.0D), "first walking tick");
        for (int i = 0; i < 7; i++) {
            assertEquals(null, sequence.tick(true, false, 1.0D), "cooldown tick " + i);
        }
        assertEquals("kirby_walk_2", sequence.tick(true, false, 1.0D), "second walking sound");
        for (int i = 0; i < 7; i++) {
            assertEquals(null, sequence.tick(true, false, 1.0D), "cooldown tick " + i);
        }
        assertEquals("kirby_walk_3", sequence.tick(true, false, 1.0D), "third walking sound");
        for (int i = 0; i < 7; i++) {
            assertEquals(null, sequence.tick(true, false, 1.0D), "cooldown tick " + i);
        }
        assertEquals("kirby_walk_2", sequence.tick(true, false, 1.0D), "fourth walking sound");
    }

    private static void idleForThirtyTicksResetsToInitialSound() {
        KirbyWalkSoundSequence sequence = new KirbyWalkSoundSequence();

        assertEquals("kirby_walk_1", sequence.tick(true, false, 1.0D), "first walking tick");
        for (int i = 0; i < 30; i++) {
            assertEquals(null, sequence.tick(false, false, 0.0D), "idle tick " + i);
        }

        assertEquals("kirby_walk_1", sequence.tick(true, false, 1.0D), "walking after idle reset");
    }

    private static void slowerWalkingAdvancesStepPhaseMoreSlowly() {
        KirbyWalkSoundSequence sequence = new KirbyWalkSoundSequence();

        assertEquals("kirby_walk_1", sequence.tick(true, false, 0.5D), "first walking tick");
        for (int i = 0; i < 15; i++) {
            assertEquals(null, sequence.tick(true, false, 0.5D), "slow walking tick " + i);
        }
        assertEquals("kirby_walk_2", sequence.tick(true, false, 0.5D), "slow second walking sound");
        assertEquals(0.5D, sequence.getSpeedScale(), "telemetry speed scale");
    }

    private static void runningUsesShorterIntervalAndHigherPitch() {
        KirbyWalkSoundSequence sequence = new KirbyWalkSoundSequence();

        assertEquals("kirby_walk_1", sequence.tick(true, true, 1.0D), "first running tick");
        assertEquals(1.12F, sequence.getLastPitch(), "running pitch");
        for (int i = 0; i < 3; i++) {
            assertEquals(null, sequence.tick(true, true, 1.0D), "running tick " + i);
        }
        assertEquals("kirby_walk_2", sequence.tick(true, true, 1.0D), "second running sound");
        assertEquals(0.192D, sequence.getStepIntervalSeconds(), "running interval");
        assertEquals(KirbyWalkSoundSequence.Gait.RUN, sequence.getGait(), "running gait");
        assertEquals("kirby_walk_2", sequence.getLastSoundName(), "last sound remains visible for telemetry");
    }

    private static void heldWalkUsesAnimationSpecificStepIntervals() {
        assertHeldInterval(KirbyWalkSoundSequence.Gait.HELD_SMALL,
                KirbyWalkSoundSequence.HELD_SMALL_STEP_INTERVAL_SECONDS);
        assertHeldInterval(KirbyWalkSoundSequence.Gait.HELD_MIDDLE,
                KirbyWalkSoundSequence.HELD_MIDDLE_STEP_INTERVAL_SECONDS);
        assertHeldInterval(KirbyWalkSoundSequence.Gait.HELD_BIG,
                KirbyWalkSoundSequence.HELD_BIG_STEP_INTERVAL_SECONDS);
    }

    private static void assertHeldInterval(KirbyWalkSoundSequence.Gait gait, double expectedInterval) {
        KirbyWalkSoundSequence sequence = new KirbyWalkSoundSequence();

        assertEquals("kirby_walk_1", sequence.tick(true, gait, 1.0D), gait + " first tick");
        for (int i = 0; i < 13; i++) {
            assertEquals(null, sequence.tick(true, gait, 1.0D), gait + " cooldown tick " + i);
        }
        assertEquals("kirby_walk_2", sequence.tick(true, gait, 1.0D), gait + " second sound");
        assertEquals(expectedInterval, sequence.getStepIntervalSeconds(), gait + " interval");
        assertEquals(gait, sequence.getGait(), gait + " telemetry");
    }

    private static void heldWalkStillRespondsToMovementSpeed() {
        KirbyWalkSoundSequence sequence = new KirbyWalkSoundSequence();
        KirbyWalkSoundSequence.Gait gait = KirbyWalkSoundSequence.Gait.HELD_SMALL;

        assertEquals("kirby_walk_1", sequence.tick(true, gait, 0.5D), "slow held first tick");
        for (int i = 0; i < 26; i++) {
            assertEquals(null, sequence.tick(true, gait, 0.5D), "slow held cooldown tick " + i);
        }
        assertEquals("kirby_walk_2", sequence.tick(true, gait, 0.5D), "slow held second sound");
    }

    private static void changingGaitPreservesTheCurrentStepPhase() {
        KirbyWalkSoundSequence sequence = new KirbyWalkSoundSequence();

        assertEquals("kirby_walk_1", sequence.tick(true, KirbyWalkSoundSequence.Gait.WALK, 1.0D),
                "walk before gait change");
        for (int i = 0; i < 4; i++) {
            assertEquals(null, sequence.tick(true, KirbyWalkSoundSequence.Gait.WALK, 1.0D),
                    "walk phase tick " + i);
        }
        assertEquals(null, sequence.tick(true, KirbyWalkSoundSequence.Gait.HELD_SMALL, 1.0D),
                "gait change must not inject an extra step");
        assertEquals(KirbyWalkSoundSequence.Gait.HELD_SMALL, sequence.getGait(), "changed gait");
    }

    private static void assertEquals(Object expected, Object actual, String label) {
        if (expected == null ? actual != null : !expected.equals(actual)) {
            throw new AssertionError(label + ": expected <" + expected + "> but was <" + actual + ">");
        }
    }

    private static void assertEquals(float expected, float actual, String label) {
        if (Math.abs(expected - actual) > 0.0001F) {
            throw new AssertionError(label + ": expected <" + expected + "> but was <" + actual + ">");
        }
    }

    private static void assertEquals(double expected, double actual, String label) {
        if (Math.abs(expected - actual) > 0.0001D) {
            throw new AssertionError(label + ": expected <" + expected + "> but was <" + actual + ">");
        }
    }

    private KirbyWalkSoundSequenceTest() {}
}
