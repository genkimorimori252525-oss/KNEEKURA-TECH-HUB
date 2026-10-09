package com.example.kirby_mod.entity.ai;

/** Pure ownership rule used to prevent two Kirbys from controlling the same Mob. */
public final class KirbyMobControlOwnerPolicy {

    private KirbyMobControlOwnerPolicy() {}

    public static boolean canClaim(boolean hasControl, boolean sameOwner, boolean leaseExpired) {
        return !hasControl || sameOwner || leaseExpired;
    }
}
