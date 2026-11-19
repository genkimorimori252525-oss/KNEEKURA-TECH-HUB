package com.example.kirby_mod.entity.ai;

/** Pure damage-to-expression classification for deterministic boundary tests. */
public final class KirbyDamageFacePolicy {

    public static final float MEDIUM_THRESHOLD = 4.0F;
    public static final float CATASTROPHIC_THRESHOLD = 10.0F;

    public enum Severity {
        NONE,
        LIGHT,
        MEDIUM,
        CATASTROPHIC
    }

    private KirbyDamageFacePolicy() {}

    public static Severity classify(float requestedAmount) {
        if (!Float.isFinite(requestedAmount) || requestedAmount <= 0.0F) {
            return Severity.NONE;
        }
        if (requestedAmount >= CATASTROPHIC_THRESHOLD) {
            return Severity.CATASTROPHIC;
        }
        if (requestedAmount >= MEDIUM_THRESHOLD) {
            return Severity.MEDIUM;
        }
        return Severity.LIGHT;
    }
}
