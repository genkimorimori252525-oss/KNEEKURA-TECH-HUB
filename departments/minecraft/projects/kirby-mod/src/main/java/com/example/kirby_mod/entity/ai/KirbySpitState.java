package com.example.kirby_mod.entity.ai;

/** Runtime lifecycle owned exclusively by {@link KirbySpitController}. */
public enum KirbySpitState {
    IDLE,
    STARTING,
    FLYING,
    FINISHING;

    public boolean isActive() {
        return this != IDLE;
    }
}
