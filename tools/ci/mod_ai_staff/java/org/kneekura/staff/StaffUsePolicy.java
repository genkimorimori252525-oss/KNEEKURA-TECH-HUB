package org.kneekura.staff;

/** Pure bounded policy, independently testable without a game launch. */
public final class StaffUsePolicy {
    public static final int GLOW_TICKS = 60;
    public static final int COOLDOWN_TICKS = 100;
    public enum Decision { CLIENT_ACK, COOLDOWN, APPLY }
    private StaffUsePolicy() {}
    public static Decision decide(boolean clientSide, boolean coolingDown) {
        if (clientSide) return Decision.CLIENT_ACK;
        return coolingDown ? Decision.COOLDOWN : Decision.APPLY;
    }
}
