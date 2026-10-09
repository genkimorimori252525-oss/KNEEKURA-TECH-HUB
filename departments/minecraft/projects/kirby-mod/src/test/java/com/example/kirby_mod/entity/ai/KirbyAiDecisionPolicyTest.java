package com.example.kirby_mod.entity.ai;

import java.util.List;

public final class KirbyAiDecisionPolicyTest {

    public static void main(String[] args) {
        selectsHighestEligibleScore();
        resolvesEqualScoresDeterministically();
        retainsCurrentActionInsideSwitchMargin();
        returnsIdleWithoutEligibleCandidates();
    }

    private static void selectsHighestEligibleScore() {
        KirbyAiDecision decision = KirbyAiDecisionPolicy.select(List.of(
                candidate(KirbyAiAction.WANDER, 1.0D, true),
                mouthCandidate(KirbyAiAction.INHALE, 4.0D, true),
                candidate(KirbyAiAction.SLIDE, 9.0D, false)),
                KirbyDecisionLane.BODY, KirbyAiAction.IDLE, 0.35D);
        assertEquals(KirbyAiAction.WANDER, decision.action(), "highest eligible action in lane");

        decision = KirbyAiDecisionPolicy.select(List.of(
                candidate(KirbyAiAction.WANDER, 1.0D, true),
                mouthCandidate(KirbyAiAction.INHALE, 4.0D, true)),
                KirbyDecisionLane.MOUTH, KirbyAiAction.IDLE, 0.35D);
        assertEquals(KirbyAiAction.INHALE, decision.action(), "highest eligible action");
    }

    private static void resolvesEqualScoresDeterministically() {
        KirbyAiDecision decision = KirbyAiDecisionPolicy.select(List.of(
                new KirbyAiCandidate(KirbyAiAction.FLY, KirbyDecisionLane.BODY,
                        3.0D, true, 0, "fly"),
                new KirbyAiCandidate(KirbyAiAction.INHALE, KirbyDecisionLane.BODY,
                        3.0D, true, 1, "inhale")),
                KirbyDecisionLane.BODY, KirbyAiAction.IDLE, 0.0D);
        assertEquals(KirbyAiAction.FLY, decision.action(), "legacy-order tie break");
    }

    private static void retainsCurrentActionInsideSwitchMargin() {
        KirbyAiDecision decision = KirbyAiDecisionPolicy.select(List.of(
                candidate(KirbyAiAction.INHALE, 5.0D, true),
                candidate(KirbyAiAction.SPIT, 5.2D, true)),
                KirbyDecisionLane.BODY, KirbyAiAction.INHALE, 0.35D);
        assertEquals(KirbyAiAction.INHALE, decision.action(), "hysteresis action");
        assertTrue(decision.retainedByHysteresis(), "hysteresis flag");
    }

    private static void returnsIdleWithoutEligibleCandidates() {
        KirbyAiDecision decision = KirbyAiDecisionPolicy.select(List.of(
                candidate(KirbyAiAction.FLY, 8.0D, false)),
                KirbyDecisionLane.BODY, KirbyAiAction.FLY, 0.35D);
        assertEquals(KirbyAiAction.IDLE, decision.action(), "no eligible fallback");
    }

    private static KirbyAiCandidate candidate(KirbyAiAction action, double score, boolean eligible) {
        return new KirbyAiCandidate(action, KirbyDecisionLane.BODY, score, eligible,
                action.ordinal(), action.name().toLowerCase());
    }

    private static KirbyAiCandidate mouthCandidate(
            KirbyAiAction action, double score, boolean eligible) {
        return new KirbyAiCandidate(action, KirbyDecisionLane.MOUTH, score, eligible,
                action.ordinal(), action.name().toLowerCase());
    }

    private static void assertEquals(Object expected, Object actual, String label) {
        if (expected == null ? actual != null : !expected.equals(actual)) {
            throw new AssertionError(label + ": expected <" + expected + "> but was <" + actual + ">");
        }
    }

    private static void assertTrue(boolean value, String label) {
        if (!value) throw new AssertionError(label);
    }

    private KirbyAiDecisionPolicyTest() {}
}
