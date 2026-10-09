package com.example.kirby_mod.entity.ai;

/** Pure timing and safety policy for starting or restoring Kirby's hover. */
public final class KirbyFlightRecoveryPolicy {

    public static final int INITIAL_HOVER_FALL_TICKS = 2;
    /** 0.85 seconds at Minecraft's fixed 20 ticks per second. */
    public static final int REHOVER_FALL_TICKS = 17;
    public static final double TAKEOFF_GROUND_GUARD = 1.5D;
    public static final double LANDING_GROUND_GUARD = 2.0D;

    private KirbyFlightRecoveryPolicy() {}

    public static Decision initialHover(
            boolean flightRequired,
            boolean airborne,
            boolean descending,
            int fallingTicks,
            double groundDistance) {
        if (!flightRequired) return Decision.no("jump_only_target");
        if (!airborne) return Decision.no("waiting_for_takeoff");
        if (fallingTicks >= INITIAL_HOVER_FALL_TICKS) {
            return Decision.yes("falling_for_initial_hover");
        }
        if (descending && groundDistance <= TAKEOFF_GROUND_GUARD) {
            return Decision.yes("ground_guard_during_takeoff");
        }
        return Decision.no(descending ? "confirming_initial_fall" : "jump_still_rising");
    }

    public static Decision ascentRepump(boolean needsAltitude, int fallingTicks) {
        if (!needsAltitude) return Decision.no("target_altitude_reached");
        if (fallingTicks >= REHOVER_FALL_TICKS) {
            return Decision.yes("ascent_fall_recovery");
        }
        return Decision.no("waiting_for_rehover_window");
    }

    public static Decision descentRecovery(
            boolean recoveryAvailable,
            boolean landingSafe,
            boolean landingAligned,
            int fallingTicks,
            double groundDistance) {
        if (!recoveryAvailable) return Decision.no("descent_recovery_budget_spent");
        if (fallingTicks < REHOVER_FALL_TICKS) {
            return Decision.no("descent_fall_not_confirmed");
        }
        if (!landingSafe) return Decision.yes("unsafe_landing_recovery");
        if (!landingAligned && groundDistance <= LANDING_GROUND_GUARD) {
            return Decision.yes("landing_alignment_recovery");
        }
        return Decision.no(landingAligned ? "safe_landing_aligned" : "safe_descent_has_room");
    }

    public record Decision(boolean shouldHover, String reason) {
        private static Decision yes(String reason) {
            return new Decision(true, reason);
        }

        private static Decision no(String reason) {
            return new Decision(false, reason);
        }
    }
}
