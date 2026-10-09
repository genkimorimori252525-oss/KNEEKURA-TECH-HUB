package com.example.kirby_mod.entity.ai;

public final class KirbyFlightRecoveryPolicyTest {

    public static void main(String[] args) {
        startsHoverAfterTwoFallingTicks();
        groundGuardPreventsTakeoffLanding();
        repumpsOnlyWhenAltitudeIsStillNeeded();
        descentRecoveryRespectsLandingPurpose();
    }

    private static void startsHoverAfterTwoFallingTicks() {
        check(!KirbyFlightRecoveryPolicy.initialHover(
                true, true, true, 1, 4.0D).shouldHover(), "one falling tick is too early");
        check(KirbyFlightRecoveryPolicy.initialHover(
                true, true, true, 2, 4.0D).shouldHover(), "two falling ticks start hover");
    }

    private static void groundGuardPreventsTakeoffLanding() {
        check(KirbyFlightRecoveryPolicy.initialHover(
                true, true, true, 1, 1.25D).shouldHover(), "near ground starts hover early");
        check(!KirbyFlightRecoveryPolicy.initialHover(
                true, true, false, 0, 0.5D).shouldHover(), "rising jump is not interrupted");
    }

    private static void repumpsOnlyWhenAltitudeIsStillNeeded() {
        check(!KirbyFlightRecoveryPolicy.ascentRepump(true, 16).shouldHover(),
                "sixteen falling ticks are still inside the cooldown");
        check(KirbyFlightRecoveryPolicy.ascentRepump(true, 17).shouldHover(),
                "seventeen falling ticks permit another pump");
        check(!KirbyFlightRecoveryPolicy.ascentRepump(false, 20).shouldHover(),
                "reached altitude must descend");
    }

    private static void descentRecoveryRespectsLandingPurpose() {
        check(KirbyFlightRecoveryPolicy.descentRecovery(
                true, false, false, 17, 4.0D).shouldHover(), "unsafe landing recovers");
        check(KirbyFlightRecoveryPolicy.descentRecovery(
                true, true, false, 17, 1.5D).shouldHover(), "misaligned low approach recovers");
        check(!KirbyFlightRecoveryPolicy.descentRecovery(
                true, true, true, 17, 0.5D).shouldHover(), "aligned landing completes");
    }

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
}
