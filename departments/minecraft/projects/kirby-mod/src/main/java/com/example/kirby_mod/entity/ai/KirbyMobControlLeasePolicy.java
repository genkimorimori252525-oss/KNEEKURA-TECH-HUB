package com.example.kirby_mod.entity.ai;

/** Pure timing policy for self-healing held/spit mob control. */
public final class KirbyMobControlLeasePolicy {

    public static final int RECOVERY_GRACE_TICKS = 40;
    public static final int RELEASE_VERIFY_TICKS = 2;
    public static final double VANILLA_GRAVITY_STEP = -0.08D;

    private KirbyMobControlLeasePolicy() {}

    public static long leaseUntil(long gameTime) {
        return addSaturated(gameTime, RECOVERY_GRACE_TICKS);
    }

    public static long releaseVerifyUntil(long gameTime) {
        return addSaturated(gameTime, RELEASE_VERIFY_TICKS);
    }

    public static boolean expired(long gameTime, long leaseUntil) {
        return gameTime >= leaseUntil;
    }

    public static long remaining(long gameTime, long leaseUntil) {
        return Math.max(0L, leaseUntil - gameTime);
    }

    public static boolean releaseVerificationFinished(long gameTime, long verifyUntil) {
        return gameTime >= verifyUntil;
    }

    /**
     * Starts an ordinary released Mob falling immediately instead of leaving one
     * client frame that still looks like the scripted zero-gravity projectile.
     */
    public static double releasedVerticalVelocity(
            double currentY, boolean originalNoGravity, boolean originalNoPhysics) {
        if (originalNoGravity || originalNoPhysics) return currentY;
        return Math.min(currentY, VANILLA_GRAVITY_STEP);
    }

    private static long addSaturated(long gameTime, int ticks) {
        if (gameTime > Long.MAX_VALUE - ticks) return Long.MAX_VALUE;
        return gameTime + ticks;
    }
}
