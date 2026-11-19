package com.example.kirby_mod.entity.ai;

import java.util.List;

public final class KirbySpitTargetPolicyTest {

    public static void main(String[] args) {
        rememberedThreatWinsRegardlessOfFacing();
        fallsBackToNearestClearThreat();
        rejectsBlockedAndNonAttackableCandidates();
    }

    private static void rememberedThreatWinsRegardlessOfFacing() {
        KirbySpitTargetPolicy.Selection selection = KirbySpitTargetPolicy.select(List.of(
                new KirbySpitTargetPolicy.Candidate(
                        "near", 2.0D, 0.0D, 2.0D, true, true, false),
                new KirbySpitTargetPolicy.Candidate(
                        "remembered", -6.0D, 0.0D, 6.0D, true, true, true)));
        assertEquals("remembered", selection.targetKey(), "remembered target");
        assertNear(-1.0D, selection.directionX(), 1.0E-9D, "behind direction");
        assertEquals("remembered_threat", selection.reason(), "selection reason");
    }

    private static void fallsBackToNearestClearThreat() {
        KirbySpitTargetPolicy.Selection selection = KirbySpitTargetPolicy.select(List.of(
                new KirbySpitTargetPolicy.Candidate(
                        "far", 8.0D, 0.0D, 8.0D, true, true, false),
                new KirbySpitTargetPolicy.Candidate(
                        "near", 3.0D, 4.0D, 5.0D, true, true, false)));
        assertEquals("near", selection.targetKey(), "nearest target");
        assertNear(0.6D, selection.directionX(), 1.0E-9D, "normalized x");
        assertNear(0.8D, selection.directionZ(), 1.0E-9D, "normalized z");
    }

    private static void rejectsBlockedAndNonAttackableCandidates() {
        KirbySpitTargetPolicy.Selection selection = KirbySpitTargetPolicy.select(List.of(
                new KirbySpitTargetPolicy.Candidate(
                        "blocked", 1.0D, 0.0D, 1.0D, false, true, true),
                new KirbySpitTargetPolicy.Candidate(
                        "friendly", 2.0D, 0.0D, 2.0D, true, false, false)));
        if (selection.found()) {
            throw new AssertionError("unsafe target must not be selected");
        }
    }

    private static void assertNear(double expected, double actual, double tolerance, String label) {
        if (Math.abs(expected - actual) > tolerance) {
            throw new AssertionError(label + ": expected <" + expected + "> but was <" + actual + ">");
        }
    }

    private static void assertEquals(String expected, String actual, String label) {
        if (!expected.equals(actual)) {
            throw new AssertionError(label + ": expected <" + expected + "> but was <" + actual + ">");
        }
    }

    private KirbySpitTargetPolicyTest() {}
}
