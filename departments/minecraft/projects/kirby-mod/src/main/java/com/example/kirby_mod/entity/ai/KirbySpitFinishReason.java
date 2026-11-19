package com.example.kirby_mod.entity.ai;

/** Every exit from a spit flight is recorded as one of these reasons. */
public enum KirbySpitFinishReason {
    NONE(false),
    WALL_HIT(false),
    ENTITY_HIT(false),
    TIMEOUT(false),
    CONTROL_LOST(false),
    PROJECTILE_MISSING(false),
    ALL_PROJECTILES_FINISHED(false),
    LAUNCH_FAILED(true),
    GOAL_INTERRUPTED(true),
    KIRBY_REMOVED(true),
    STATE_DESYNC(true);

    private final boolean abortsMouth;

    KirbySpitFinishReason(boolean abortsMouth) {
        this.abortsMouth = abortsMouth;
    }

    public boolean abortsMouth() {
        return this.abortsMouth;
    }
}
