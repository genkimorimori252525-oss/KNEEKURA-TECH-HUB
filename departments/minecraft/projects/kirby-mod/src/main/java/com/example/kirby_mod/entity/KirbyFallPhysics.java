package com.example.kirby_mod.entity;

/** Pure constants and calculations for Kirby's soft-body falling behavior. */
public final class KirbyFallPhysics {

    public static final double VANILLA_GRAVITY = 0.08D;
    public static final double FALL_GRAVITY = VANILLA_GRAVITY / 3.0D;
    public static final double ASCENT_GRAVITY = 0.04D;
    public static final double AIR_DRAG = 0.98D;
    public static final double MAX_FALL_SPEED = 1.31D;

    private KirbyFallPhysics() {}

    public static double flightGravity(double verticalVelocity) {
        return verticalVelocity <= 0.0D ? FALL_GRAVITY : ASCENT_GRAVITY;
    }

    public static double adjustVanillaFallVelocity(double vanillaVelocity) {
        double gravityCorrection = (VANILLA_GRAVITY - FALL_GRAVITY) * AIR_DRAG;
        return Math.max(-MAX_FALL_SPEED, vanillaVelocity + gravityCorrection);
    }

    public static double applyFlightFall(double verticalVelocity) {
        return Math.max(-MAX_FALL_SPEED,
                (verticalVelocity - flightGravity(verticalVelocity)) * AIR_DRAG);
    }
}
