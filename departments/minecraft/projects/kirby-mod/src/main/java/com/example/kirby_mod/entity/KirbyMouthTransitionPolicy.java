package com.example.kirby_mod.entity;

/** Pure transition guard for the mouth lifecycle. EMPTY remains a universal recovery target. */
public final class KirbyMouthTransitionPolicy {

    private KirbyMouthTransitionPolicy() {}

    public static boolean isAllowed(KirbyMouthPhase from, KirbyMouthPhase to, int heldMobCount) {
        if (from == to || to == KirbyMouthPhase.EMPTY) return true;
        switch (from) {
            case EMPTY:
                return to == KirbyMouthPhase.INHALE_PREP;
            case INHALE_PREP:
                return to == KirbyMouthPhase.INHALING;
            case INHALING:
                return heldMobCount > 0
                        ? to == KirbyMouthPhase.HOLDING
                        : to == KirbyMouthPhase.INHALE_END;
            case HOLDING:
                return to == KirbyMouthPhase.SWALLOWING || to == KirbyMouthPhase.SPITTING;
            case INHALE_END:
            case SWALLOWING:
            case SPITTING:
            default:
                return false;
        }
    }
}
