package com.example.kirby_mod.entity.ai;

import com.example.kirby_mod.entity.KirbyFallPhysics;

/** Plans a purpose-driven jump and solves the required vertical impulse. */
public final class KirbyJumpPolicy {

    public static final double MAX_JUMP_HEIGHT = 5.0D;
    public static final double CLEARANCE_PROBE_STEP = 0.25D;
    public static final int FLIGHT_REQUIRED_DELTA = 4;
    private static final double MIN_USEFUL_JUMP_HEIGHT = 1.0D;
    private static final double JUMP_ONLY_CLEARANCE = 0.35D;
    private static final double MAX_JUMP_DISTANCE_BONUS = 1.0D;
    private static final double FLIGHT_BASE_HEIGHT = 2.0D;
    private static final double MAX_TARGET_BONUS = 1.5D;
    private static final double MAX_DISTANCE_BONUS = 1.5D;

    private KirbyJumpPolicy() {}

    public static Decision plan(
            int verticalDelta,
            double horizontalDistance,
            double availableClearance) {
        boolean hoverRequired = verticalDelta > FLIGHT_REQUIRED_DELTA;
        double requestedHeight;
        String reason;
        if (hoverRequired) {
            double targetBonus = Math.min(MAX_TARGET_BONUS,
                    Math.max(0.0D, verticalDelta - FLIGHT_REQUIRED_DELTA) * 0.5D);
            double distanceBonus = Math.min(MAX_DISTANCE_BONUS,
                    Math.max(0.0D, horizontalDistance) / 10.0D);
            requestedHeight = FLIGHT_BASE_HEIGHT + targetBonus + distanceBonus;
            reason = "flight_takeoff_target_and_distance";
        } else {
            double distanceBonus = Math.min(MAX_JUMP_DISTANCE_BONUS,
                    Math.max(0.0D, horizontalDistance) / 12.0D);
            requestedHeight = Math.max(MIN_USEFUL_JUMP_HEIGHT,
                    Math.max(0, verticalDelta) + JUMP_ONLY_CLEARANCE + distanceBonus);
            reason = "jump_only_target_and_distance";
        }

        double clearance = clamp(availableClearance, 0.0D, MAX_JUMP_HEIGHT);
        double targetHeight = Math.min(MAX_JUMP_HEIGHT, Math.min(requestedHeight, clearance));
        if (targetHeight + 1.0E-6D < requestedHeight) {
            reason += ":limited_by_headroom";
        }
        return new Decision(targetHeight, impulseForHeight(targetHeight),
                hoverRequired, reason);
    }

    public static double impulseForHeight(double desiredHeight) {
        double target = clamp(desiredHeight, 0.0D, MAX_JUMP_HEIGHT);
        if (target <= 0.0D) return 0.0D;
        double low = 0.0D;
        double high = 1.0D;
        for (int iteration = 0; iteration < 48; iteration++) {
            double middle = (low + high) * 0.5D;
            if (peakHeight(middle) < target) {
                low = middle;
            } else {
                high = middle;
            }
        }
        return high;
    }

    public static double peakHeight(double impulse) {
        double velocity = Math.max(0.0D, impulse);
        double height = 0.0D;
        for (int tick = 0; tick < 80 && velocity > 0.0D; tick++) {
            height += velocity;
            velocity = (velocity - KirbyFallPhysics.ASCENT_GRAVITY)
                    * KirbyFallPhysics.AIR_DRAG;
        }
        return height;
    }

    private static double clamp(double value, double minimum, double maximum) {
        if (!Double.isFinite(value)) return maximum;
        return Math.max(minimum, Math.min(maximum, value));
    }

    public record Decision(
            double targetHeight,
            double impulse,
            boolean hoverRequired,
            String reason) {}
}
