package dev.kneekura.fivedifficulties.core.timestop;

/**
 * Policy switches are deliberately explicit so donor behavior is not mistaken for the X1 oracle.
 */
public record TimeStopFlags(
        boolean freezeLivingEntities,
        boolean freezeExistingProjectiles,
        boolean specialMoveNewProjectiles,
        boolean freezeItemEntities,
        boolean freezeOtherEntities,
        boolean freezeBlockTicks,
        boolean freezeFluidTicks,
        boolean freezeBlockEntities,
        boolean freezeRandomChunkTicks,
        boolean freezeParticles,
        boolean freezeAnimatedTextures,
        boolean freezeWorldDayTime,
        boolean delayDamageUntilResume,
        int minimumEntityAgeTicks,
        ProjectileStopMode projectileStopMode
) {
    public TimeStopFlags {
        if (minimumEntityAgeTicks < 0) throw new IllegalArgumentException("minimumEntityAgeTicks");
        if (projectileStopMode == null) throw new NullPointerException("projectileStopMode");
    }

    /** Engineering donor default only. It is not a claim about Five Difficulties X1 behavior. */
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
                false,
                0,
                ProjectileStopMode.ROUNDABOUT_DECELERATE
        );
    }

    /** Exact X1 entity-scope policy recovered from EntitySakuyaWatch/StopWatch. */
    public static TimeStopFlags x1EntityOnly() {
        return new TimeStopFlags(
                true,
                true,
                false,
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
                2,
                ProjectileStopMode.LEGACY_X1_UNRESOLVED
        );
    }
}
