package com.example.kirby_mod.entity.ai;

public final class KirbySlideMotion {

    public static final int MOTION_TICKS = 36;
    public static final int FINISH_TICKS = 6;
    public static final double WALK_SPEED_MULTIPLIER = 2.0D;
    private static final double FRICTION_PER_TICK = 0.94D;

    public static double horizontalSpeed(double walkSpeed, int motionTick) {
        int tick = Math.max(0, Math.min(MOTION_TICKS - 1, motionTick));
        return Math.max(0.0D, walkSpeed) * WALK_SPEED_MULTIPLIER
                * Math.pow(FRICTION_PER_TICK, tick);
    }

    private KirbySlideMotion() {}
}
