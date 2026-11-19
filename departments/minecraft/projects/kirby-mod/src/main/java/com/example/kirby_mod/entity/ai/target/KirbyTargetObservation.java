package com.example.kirby_mod.entity.ai.target;

/** Immutable target data that does not retain a Minecraft Entity or Level. */
public record KirbyTargetObservation(
        KirbyTargetKind kind,
        String targetKey,
        String typeKey,
        double x,
        double y,
        double z,
        double distance,
        KirbyTargetVisibility visibility,
        double score,
        int seenTick,
        int ttlTicks,
        String reason) {

    public KirbyTargetObservation {
        if (kind == null) throw new IllegalArgumentException("kind must not be null");
        if (targetKey == null || targetKey.isBlank()) {
            throw new IllegalArgumentException("targetKey must not be blank");
        }
        if (typeKey == null || typeKey.isBlank()) typeKey = "unknown";
        if (!Double.isFinite(x) || !Double.isFinite(y) || !Double.isFinite(z)) {
            throw new IllegalArgumentException("position must be finite");
        }
        if (!Double.isFinite(distance) || distance < 0.0D) {
            throw new IllegalArgumentException("distance must be finite and non-negative");
        }
        if (visibility == null) visibility = KirbyTargetVisibility.UNKNOWN;
        if (!Double.isFinite(score)) throw new IllegalArgumentException("score must be finite");
        if (seenTick < 0) throw new IllegalArgumentException("seenTick must not be negative");
        if (ttlTicks < 0) throw new IllegalArgumentException("ttlTicks must not be negative");
        reason = reason == null ? "" : reason;
    }
}
