package com.example.kirby_mod.entity.ai;

/** Immutable, Minecraft-object-free input to the AI decision policy. */
public record KirbyAiCandidate(
        KirbyAiAction action,
        KirbyDecisionLane lane,
        double score,
        boolean eligible,
        int legacyOrder,
        String targetKey,
        String reason) {

    public KirbyAiCandidate(
            KirbyAiAction action,
            KirbyDecisionLane lane,
            double score,
            boolean eligible,
            int legacyOrder,
            String reason) {
        this(action, lane, score, eligible, legacyOrder, "none", reason);
    }

    public KirbyAiCandidate {
        if (action == null) throw new IllegalArgumentException("action must not be null");
        if (lane == null) throw new IllegalArgumentException("lane must not be null");
        if (!Double.isFinite(score)) throw new IllegalArgumentException("score must be finite");
        if (legacyOrder < 0) throw new IllegalArgumentException("legacyOrder must not be negative");
        targetKey = targetKey == null || targetKey.isBlank() ? "none" : targetKey;
        reason = reason == null ? "" : reason;
    }
}
