package com.example.kirby_mod.entity;

/** The authoritative lifecycle of Kirby's mouth, independent of locomotion states. */
public enum KirbyMouthPhase {
    EMPTY(CombatState.NONE, false),
    INHALE_PREP(CombatState.INHALE_PREP, false),
    INHALING(CombatState.INHALE, true),
    INHALE_END(CombatState.INHALE_END, false),
    HOLDING(CombatState.KEEP_HOLDING, true),
    SWALLOWING(CombatState.KEEP_NOMIKOMI, true),
    SPITTING(CombatState.KEEP_SPIT, true);

    private final CombatState combatState;
    private final boolean sealsContents;

    KirbyMouthPhase(CombatState combatState, boolean sealsContents) {
        this.combatState = combatState;
        this.sealsContents = sealsContents;
    }

    public CombatState toCombatState() {
        return this.combatState;
    }

    public boolean sealsContents() {
        return this.sealsContents;
    }

    public boolean isInhaleLifecycle() {
        return this == INHALE_PREP || this == INHALING || this == INHALE_END;
    }

    public boolean isActive() {
        return this != EMPTY;
    }

    public static KirbyMouthPhase afterInhale(int heldMobCount) {
        return heldMobCount > 0 ? HOLDING : INHALE_END;
    }

    public static KirbyMouthPhase fromCombatState(CombatState state) {
        switch (state) {
            case INHALE_PREP:  return INHALE_PREP;
            case INHALE:       return INHALING;
            case INHALE_END:   return INHALE_END;
            case KEEP_HOLDING: return HOLDING;
            case KEEP_NOMIKOMI:return SWALLOWING;
            case KEEP_SPIT:    return SPITTING;
            default:           return EMPTY;
        }
    }
}
