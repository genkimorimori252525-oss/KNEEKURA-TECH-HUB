package com.example.kirby_mod.entity.ai;

import java.util.List;

public final class KirbyAiDecisionPolicy {

    public static KirbyAiDecision select(
            List<KirbyAiCandidate> candidates,
            KirbyDecisionLane lane,
            KirbyAiAction currentAction,
            double switchMargin) {
        if (lane == null) throw new IllegalArgumentException("lane must not be null");
        if (currentAction == null) currentAction = KirbyAiAction.IDLE;
        if (candidates == null || candidates.isEmpty()) {
            return KirbyAiDecision.idle(lane, "no candidates");
        }
        double margin = Math.max(0.0D, switchMargin);
        KirbyAiCandidate best = null;
        KirbyAiCandidate current = null;

        for (KirbyAiCandidate candidate : candidates) {
            if (candidate == null || candidate.lane() != lane || !candidate.eligible()) continue;
            if (candidate.action() == currentAction) current = candidate;
            if (best == null
                    || candidate.score() > best.score()
                    || candidate.score() == best.score()
                    && candidate.legacyOrder() < best.legacyOrder()
                    || candidate.score() == best.score()
                    && candidate.legacyOrder() == best.legacyOrder()
                    && candidate.action().ordinal() < best.action().ordinal()) {
                best = candidate;
            }
        }

        if (best == null) {
            return KirbyAiDecision.idle(lane, "no eligible candidates");
        }
        if (current != null && best.action() != current.action()
                && best.score() < current.score() + margin) {
            return new KirbyAiDecision(current.action(), lane, current.score(),
                    "retained current action: " + current.reason(), true);
        }
        return new KirbyAiDecision(best.action(), lane, best.score(), best.reason(), false);
    }

    private KirbyAiDecisionPolicy() {}
}
