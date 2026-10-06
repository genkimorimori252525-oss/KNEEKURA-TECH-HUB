package dev.kneekura.fivedifficulties.core.timestop;

import dev.kneekura.fivedifficulties.core.math.Vec3d;

/**
 * Minecraft-independent approximation of Roundabout's stopped-time projectile mover.
 * LEGACY_X1_UNRESOLVED intentionally refuses to simulate before the X1 oracle is measured.
 */
public record StoppedProjectileState(
        Vec3d position,
        Vec3d resumeVelocity,
        double speedMultiplier,
        boolean held,
        ProjectileStopMode mode
) {
    public StoppedProjectileState {
        if (position == null || resumeVelocity == null || mode == null) throw new NullPointerException();
        if (!Double.isFinite(speedMultiplier) || speedMultiplier < 0.0) throw new IllegalArgumentException("speedMultiplier");
    }

    public static StoppedProjectileState create(Vec3d position, Vec3d resumeVelocity, ProjectileStopMode mode) {
        return new StoppedProjectileState(position, resumeVelocity, mode == ProjectileStopMode.PLACE_AND_HOLD ? 0.0 : 1.0,
                mode == ProjectileStopMode.PLACE_AND_HOLD, mode);
    }

    public StoppedProjectileState advance(boolean farProbeHit, boolean nearProbeHit, boolean collided) {
        return switch (mode) {
            case PLACE_AND_HOLD -> this;
            case LEGACY_X1_UNRESOLVED -> throw new UnsupportedOperationException("X1 projectile time-stop oracle not measured yet");
            case ROUNDABOUT_DECELERATE -> advanceRoundabout(farProbeHit, nearProbeHit, collided);
        };
    }

    private StoppedProjectileState advanceRoundabout(boolean farProbeHit, boolean nearProbeHit, boolean collided) {
        if (held || collided) {
            return new StoppedProjectileState(position, resumeVelocity, 0.0, true, mode);
        }

        double multiplier = speedMultiplier;
        if (farProbeHit) multiplier *= 0.7;
        if (nearProbeHit) multiplier *= 0.6;
        if (farProbeHit && nearProbeHit && multiplier <= 0.1) multiplier = 0.11;

        Vec3d nextPosition = position.add(resumeVelocity.scale(multiplier));
        double nextMultiplier = multiplier * 0.87;
        boolean nextHeld = nextMultiplier <= 0.01;
        if (nextHeld) nextMultiplier = 0.0;
        return new StoppedProjectileState(nextPosition, resumeVelocity, nextMultiplier, nextHeld, mode);
    }
}
