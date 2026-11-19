package com.example.kirby_mod.entity.ai;

/** Pure weighted choices shared by autonomous movement Goals. */
public final class KirbyAutonomyPolicy {

    public static final float GROUND_RUN_CHANCE = 0.25F;

    private KirbyAutonomyPolicy() {}

    public static KirbyLocomotionMode chooseGroundMode(float roll) {
        if (!Float.isFinite(roll) || roll < 0.0F || roll >= 1.0F) {
            throw new IllegalArgumentException("roll must be in [0, 1)");
        }
        return roll < GROUND_RUN_CHANCE
                ? KirbyLocomotionMode.RUN
                : KirbyLocomotionMode.WALK;
    }
}
