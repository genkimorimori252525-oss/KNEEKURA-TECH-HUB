package com.example.kirby_mod.entity.ai;

/** Pure timing rules between capture completion and digest choice. */
public final class KirbyDigestTimingPolicy {

    public static final int TICKS_PER_SECOND = 20;
    public static final int HOLD_DECISION_TICKS = TICKS_PER_SECOND;

    private KirbyDigestTimingPolicy() {}

    public static boolean readyForDecision(int holdTicks) {
        return holdTicks >= HOLD_DECISION_TICKS;
    }
}
