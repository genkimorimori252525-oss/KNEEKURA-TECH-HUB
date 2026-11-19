package com.example.kirby_mod.entity.ai;

public record KirbyAiDecision(
        KirbyAiAction action,
        KirbyDecisionLane lane,
        double score,
        String reason,
        boolean retainedByHysteresis) {

    public KirbyAiDecision {
        if (action == null) throw new IllegalArgumentException("action must not be null");
        if (lane == null) throw new IllegalArgumentException("lane must not be null");
        if (!Double.isFinite(score)) throw new IllegalArgumentException("score must be finite");
        reason = reason == null ? "" : reason;
    }

    public static KirbyAiDecision idle(KirbyDecisionLane lane, String reason) {
        return new KirbyAiDecision(KirbyAiAction.IDLE, lane, 0.0D, reason, false);
    }
}
