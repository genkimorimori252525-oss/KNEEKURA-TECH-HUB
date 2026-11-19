package com.example.kirby_mod.entity.ai;

public final class KirbyMobControlOwnerPolicyTest {

    public static void main(String[] args) {
        unclaimedMobCanBeCaptured();
        ownerCanRenewControl();
        liveForeignLeaseRejectsCapture();
        expiredForeignLeaseCanBeRecovered();
    }

    private static void unclaimedMobCanBeCaptured() {
        assertEquals(true, KirbyMobControlOwnerPolicy.canClaim(false, false, false), "unclaimed");
    }

    private static void ownerCanRenewControl() {
        assertEquals(true, KirbyMobControlOwnerPolicy.canClaim(true, true, false), "same owner");
    }

    private static void liveForeignLeaseRejectsCapture() {
        assertEquals(false, KirbyMobControlOwnerPolicy.canClaim(true, false, false), "foreign owner");
    }

    private static void expiredForeignLeaseCanBeRecovered() {
        assertEquals(true, KirbyMobControlOwnerPolicy.canClaim(true, false, true), "expired lease");
    }

    private static void assertEquals(boolean expected, boolean actual, String label) {
        if (expected != actual) {
            throw new AssertionError(label + ": expected <" + expected + "> but was <" + actual + ">");
        }
    }

    private KirbyMobControlOwnerPolicyTest() {}
}
