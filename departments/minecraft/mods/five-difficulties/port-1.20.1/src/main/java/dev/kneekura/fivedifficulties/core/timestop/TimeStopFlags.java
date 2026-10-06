package dev.kneekura.fivedifficulties.core.timestop;

/**
 * Policy switches are deliberately explicit so Roundabout behavior is not mistaken for the X1 oracle.
 */
public record TimeStopFlags(
        boolean freezeLivingEntities,
        boolean freezeExistingProjectiles,
        boolean specialMoveNewProjectiles,
        boolean freezeItemEntities,
        boolean freezeBlockTicks,
        boolean freezeFluidTicks,
        boolean freezeBlockEntities,
        boolean freezeRandomChunkTicks,
        boolean freezeParticles,
        boolean freezeAnimatedTextures,
        boolean freezeWorldDayTime,
        boolean delayDamageUntilResume,
        ProjectileStopMode projectileStopMode
) {
    public TimeStopFlags {
        if (projectileStopMode == null) throw new NullPointerException("projectileStopMode");
    }

    /** Engineering default only. It is not a claim about Five Difficulties X1 behavior. */
    public static TimeStopFlags p0EngineeringDefault() {
        return new TimeStopFlags(
                true,
                true,
                true,
                false,
                false,
                false,
                false,
                false,
                false,
                false,
                false,
                false,
                ProjectileStopMode.ROUNDABOUT_DECELERATE
        );
    }
}
