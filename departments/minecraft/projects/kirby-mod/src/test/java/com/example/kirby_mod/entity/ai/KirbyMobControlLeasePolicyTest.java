package com.example.kirby_mod.entity.ai;

public final class KirbyMobControlLeasePolicyTest {

    public static void main(String[] args) {
        leaseStaysActiveDuringGraceWindow();
        leaseExpiresAtDeadline();
        leaseSaturatesAtLongMaximum();
        releaseVerificationUsesTwoTickWindow();
        ordinaryReleasedMobStartsFalling();
        specialReleasedMobKeepsItsVerticalVelocity();
    }

    private static void leaseStaysActiveDuringGraceWindow() {
        long lease = KirbyMobControlLeasePolicy.leaseUntil(100L);
        if (KirbyMobControlLeasePolicy.expired(139L, lease)) {
            throw new AssertionError("lease expired before grace window ended");
        }
        assertEquals(1L, KirbyMobControlLeasePolicy.remaining(139L, lease), "remaining");
    }

    private static void leaseExpiresAtDeadline() {
        long lease = KirbyMobControlLeasePolicy.leaseUntil(100L);
        if (!KirbyMobControlLeasePolicy.expired(140L, lease)) {
            throw new AssertionError("lease did not expire at deadline");
        }
    }

    private static void leaseSaturatesAtLongMaximum() {
        assertEquals(Long.MAX_VALUE,
                KirbyMobControlLeasePolicy.leaseUntil(Long.MAX_VALUE - 1L),
                "saturated lease");
    }

    private static void releaseVerificationUsesTwoTickWindow() {
        long verifyUntil = KirbyMobControlLeasePolicy.releaseVerifyUntil(200L);
        assertEquals(202L, verifyUntil, "release verify deadline");
        if (KirbyMobControlLeasePolicy.releaseVerificationFinished(201L, verifyUntil)) {
            throw new AssertionError("release verification finished too early");
        }
        if (!KirbyMobControlLeasePolicy.releaseVerificationFinished(202L, verifyUntil)) {
            throw new AssertionError("release verification did not finish at deadline");
        }
    }

    private static void ordinaryReleasedMobStartsFalling() {
        assertEquals(-0.08D,
                KirbyMobControlLeasePolicy.releasedVerticalVelocity(0.0D, false, false),
                "stationary ordinary Mob");
        assertEquals(-0.25D,
                KirbyMobControlLeasePolicy.releasedVerticalVelocity(-0.25D, false, false),
                "already falling Mob");
    }

    private static void specialReleasedMobKeepsItsVerticalVelocity() {
        assertEquals(0.35D,
                KirbyMobControlLeasePolicy.releasedVerticalVelocity(0.35D, true, false),
                "original no-gravity Mob");
        assertEquals(0.20D,
                KirbyMobControlLeasePolicy.releasedVerticalVelocity(0.20D, false, true),
                "original no-physics Mob");
    }

    private static void assertEquals(long expected, long actual, String label) {
        if (expected != actual) {
            throw new AssertionError(label + ": expected <" + expected + "> but was <" + actual + ">");
        }
    }

    private static void assertEquals(double expected, double actual, String label) {
        if (Double.compare(expected, actual) != 0) {
            throw new AssertionError(label + ": expected <" + expected + "> but was <" + actual + ">");
        }
    }

    private KirbyMobControlLeasePolicyTest() {}
}
