package com.example.kirby_mod.entity;

public enum CombatState {
    NONE,
    INHALE_PREP,
    INHALE,
    INHALE_END,
    KEEP_HOLDING,
    KEEP_NOMIKOMI,
    KEEP_SPIT,
    CROUCH_PREP,
    CROUCH_LOOP,
    CROUCH_END,
    SLIDE_START,
    SLIDING,
    SLIDE_FINISH;

    public static CombatState byId(int id) {
        CombatState[] values = values();
        return id < 0 || id >= values.length ? NONE : values[id];
    }

    public static CombatState loadSafeState(int id) {
        CombatState state = byId(id);
        return state.isRuntimeOnly() ? NONE : state;
    }

    public boolean isHolding() {
        return this == KEEP_HOLDING || this == KEEP_NOMIKOMI || this == KEEP_SPIT;
    }

    public boolean isInhaling() {
        return this == INHALE_PREP || this == INHALE || this == INHALE_END;
    }

    public boolean isCrouching() {
        return this == CROUCH_PREP || this == CROUCH_LOOP || this == CROUCH_END;
    }

    public boolean isSliding() {
        return this == SLIDE_START || this == SLIDING || this == SLIDE_FINISH;
    }

    public boolean usesLowProfileHitbox() {
        return isCrouching() || isSliding();
    }

    private boolean isRuntimeOnly() {
        return this != NONE;
    }
}
