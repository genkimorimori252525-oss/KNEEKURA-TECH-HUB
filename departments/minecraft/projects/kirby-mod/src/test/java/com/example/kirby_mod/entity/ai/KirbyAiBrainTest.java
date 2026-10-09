package com.example.kirby_mod.entity.ai;

import java.util.ArrayList;
import java.util.List;

public final class KirbyAiBrainTest {

    public static void main(String[] args) {
        observesActionAndLocomotionWithoutTakingAuthority();
        enablesOneLaneInHybridMode();
        cooldownMakesCandidateTemporarilyIneligible();
        brainAppliesDecisionHysteresis();
    }

    private static void enablesOneLaneInHybridMode() {
        KirbyAiBrain brain = new KirbyAiBrain();
        brain.setLaneEnforced(KirbyDecisionLane.LOCOMOTION, true);
        assertEquals(KirbyAiBrain.Mode.HYBRID, brain.getMode(), "hybrid mode");
        assertTrue(brain.isLaneEnforced(KirbyDecisionLane.LOCOMOTION), "locomotion enforced");
        assertTrue(!brain.isLaneEnforced(KirbyDecisionLane.MOUTH), "mouth remains observed");
    }

    private static void observesActionAndLocomotionWithoutTakingAuthority() {
        KirbyAiBrain brain = new KirbyAiBrain();
        brain.observeActive(KirbyDecisionLane.LOCOMOTION, KirbyAiAction.FOLLOW, 20);
        brain.observeLocomotion(KirbyLocomotionMode.RUN, 20);
        assertEquals(KirbyAiBrain.Mode.OBSERVE, brain.getMode(), "default mode");
        assertEquals(KirbyAiAction.FOLLOW,
                brain.getActiveAction(KirbyDecisionLane.LOCOMOTION), "observed action");
        assertEquals(KirbyLocomotionMode.RUN, brain.getLocomotionMode(), "observed locomotion");
    }

    private static void cooldownMakesCandidateTemporarilyIneligible() {
        KirbyAiBrain brain = new KirbyAiBrain();
        brain.startCooldown(KirbyAiAction.SPIT, 10, 20);
        KirbyAiDecision during = brain.evaluate(KirbyDecisionLane.BODY, 15, List.of(
                candidate(KirbyAiAction.SPIT, 9.0D),
                candidate(KirbyAiAction.WANDER, 1.0D)));
        assertEquals(KirbyAiAction.WANDER, during.action(), "candidate during cooldown");

        KirbyAiDecision after = brain.evaluate(KirbyDecisionLane.BODY, 30, List.of(
                candidate(KirbyAiAction.SPIT, 9.0D),
                candidate(KirbyAiAction.WANDER, 1.0D)));
        assertEquals(KirbyAiAction.SPIT, after.action(), "candidate after cooldown");
    }

    private static void brainAppliesDecisionHysteresis() {
        KirbyAiBrain brain = new KirbyAiBrain();
        brain.evaluate(KirbyDecisionLane.BODY, 1,
                List.of(candidate(KirbyAiAction.INHALE, 5.0D)));
        KirbyAiDecision decision = brain.evaluate(KirbyDecisionLane.BODY, 2, List.of(
                candidate(KirbyAiAction.INHALE, 5.0D),
                candidate(KirbyAiAction.SPIT, 5.2D)));
        assertEquals(KirbyAiAction.INHALE, decision.action(), "brain hysteresis");

        List<String> debug = new ArrayList<>();
        brain.appendDebugInfo(debug);
        assertTrue(debug.stream().anyMatch(line -> line.contains("retained=true")), "debug retained flag");
    }

    private static KirbyAiCandidate candidate(KirbyAiAction action, double score) {
        return new KirbyAiCandidate(action, KirbyDecisionLane.BODY, score, true,
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

    private KirbyAiBrainTest() {}
}
