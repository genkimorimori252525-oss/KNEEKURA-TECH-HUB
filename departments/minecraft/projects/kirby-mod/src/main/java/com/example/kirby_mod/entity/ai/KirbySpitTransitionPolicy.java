package com.example.kirby_mod.entity.ai;

/** Pure transition rules for the dedicated spit lifecycle. */
public final class KirbySpitTransitionPolicy {

    private KirbySpitTransitionPolicy() {}

    public static boolean isAllowed(KirbySpitState from, KirbySpitState to) {
        if (from == null || to == null || from == to) return false;
        return switch (from) {
            case IDLE -> to == KirbySpitState.STARTING;
            case STARTING -> to == KirbySpitState.FLYING
                    || to == KirbySpitState.FINISHING;
            case FLYING -> to == KirbySpitState.FINISHING;
            case FINISHING -> to == KirbySpitState.IDLE;
        };
    }
}
