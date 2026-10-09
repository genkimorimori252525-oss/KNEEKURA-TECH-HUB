package com.example.kirby_mod.entity;

public final class KirbyMouthFullnessTest {

    public static void main(String[] args) {
        easeOutUsesFixedNormalizedDuration();
        easeOutClampsOutOfRangeProgress();
    }

    private static void easeOutUsesFixedNormalizedDuration() {
        assertEquals(0.0D, KirbyMouthFullness.easeOut(0.0D), "start");
        assertEquals(0.75D, KirbyMouthFullness.easeOut(0.5D), "middle");
        assertEquals(1.0D, KirbyMouthFullness.easeOut(1.0D), "end");
    }

    private static void easeOutClampsOutOfRangeProgress() {
        assertEquals(0.0D, KirbyMouthFullness.easeOut(-1.0D), "below start");
        assertEquals(1.0D, KirbyMouthFullness.easeOut(2.0D), "above end");
    }

    private static void assertEquals(double expected, double actual, String label) {
        if (Math.abs(expected - actual) > 0.0001D) {
            throw new AssertionError(label + ": expected <" + expected + "> but was <" + actual + ">");
        }
    }

    private KirbyMouthFullnessTest() {}
}
