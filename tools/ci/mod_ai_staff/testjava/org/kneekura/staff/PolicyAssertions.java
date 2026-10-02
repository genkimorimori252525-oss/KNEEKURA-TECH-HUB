package org.kneekura.staff;

/** Pure policy checks; this class starts no Minecraft process. */
public final class PolicyAssertions {
    private static void require(boolean pass, String why) {
        if (!pass) throw new AssertionError(why);
    }
    public static void main(String[] args) {
        require(StaffUsePolicy.GLOW_TICKS == 60, "Glowing is exactly 60 ticks");
        require(StaffUsePolicy.COOLDOWN_TICKS == 100, "Cooldown is exactly 100 ticks");
        require(StaffUsePolicy.decide(true, false) == StaffUsePolicy.Decision.CLIENT_ACK, "Client never applies mutation");
        require(StaffUsePolicy.decide(true, true) == StaffUsePolicy.Decision.CLIENT_ACK, "Client cooldown never applies mutation");
        require(StaffUsePolicy.decide(false, true) == StaffUsePolicy.Decision.COOLDOWN, "Server cooldown does not reapply");
        require(StaffUsePolicy.decide(false, false) == StaffUsePolicy.Decision.APPLY, "Available server handler applies");
        System.out.println("STAFF_POLICY_ASSERTIONS_PASS_NOT_GAMEPLAY");
    }
}
