package com.example.kirby_mod.entity.ai;

/** Pure distance policy for stable ground walk/run transitions. */
public final class KirbyGroundMovementPolicy {

    public static final double STOP_DISTANCE = 2.5D;
    public static final double RESUME_DISTANCE = 3.0D;
    public static final double RUN_ENTER_DISTANCE = 8.0D;
    public static final double RUN_EXIT_DISTANCE = 6.0D;

    private KirbyGroundMovementPolicy() {}

    public static KirbyLocomotionMode select(
            boolean hasTarget,
            double distance,
            KirbyLocomotionMode current) {
        if (!hasTarget) return KirbyLocomotionMode.IDLE;
        if (!Double.isFinite(distance) || distance < 0.0D) {
            throw new IllegalArgumentException("distance must be finite and non-negative");
        }
        KirbyLocomotionMode previous = current == null ? KirbyLocomotionMode.IDLE : current;
        if (previous == KirbyLocomotionMode.RUN && distance >= RUN_EXIT_DISTANCE) {
            return KirbyLocomotionMode.RUN;
        }
        if (distance >= RUN_ENTER_DISTANCE) return KirbyLocomotionMode.RUN;
        if (previous == KirbyLocomotionMode.IDLE && distance < RESUME_DISTANCE) {
            return KirbyLocomotionMode.IDLE;
        }
        if (distance <= STOP_DISTANCE) return KirbyLocomotionMode.IDLE;
        return KirbyLocomotionMode.WALK;
    }
}
