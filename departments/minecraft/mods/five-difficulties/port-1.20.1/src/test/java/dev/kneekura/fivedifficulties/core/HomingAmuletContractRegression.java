package dev.kneekura.fivedifficulties.core;

import dev.kneekura.fivedifficulties.core.x1.EvidenceGrade;
import dev.kneekura.fivedifficulties.core.x1.HomingAmuletContract;
import dev.kneekura.fivedifficulties.core.x1.HomingAmuletShotContract;

public final class HomingAmuletContractRegression {
    public static void main(String[] args) {
        HomingAmuletShotContract normal = HomingAmuletContract.resolve(false);
        HomingAmuletShotContract focus = HomingAmuletContract.resolve(true);

        check(normal.shotCount() == 5, "normal count");
        close(normal.totalSpreadDegrees(), 100.0, "normal span");
        close(normal.shotSize(), 0.4, "normal hitbox size");
        close(normal.damage(), 5.0, "normal damage");

        check(focus.shotCount() == 2, "focus count");
        close(focus.totalSpreadDegrees(), 20.0, "focus span");
        close(focus.shotSize(), 1.0, "focus hitbox size");
        close(focus.damage(), 8.0, "focus damage");

        close(normal.speed(), 0.7, "normal speed");
        close(focus.speed(), 0.7, "focus speed");
        check(normal.legacyForm() == 27, "FORM_AMULET");
        check(normal.legacyColor() == 0, "RED");
        check(normal.delayTicks() == 0, "delay");
        check(normal.lifetimeTicks() == 90, "lifetime");
        check(normal.specialId() == 10, "HOMING01 id");
        close(normal.spawnDistance(), 0.5, "spawn distance");
        close(normal.baseAngleDegrees(), 0.0, "base angle");
        check(normal.specialBehavior().equals("HOMING01"), "normal special");
        close(normal.maxHomingTurnDegreesPerTick(), 4.0, "homing turn");
        check(normal.projectileFamily().equals("AMULET"), "projectile family");
        check(normal.colorName().equals("RED"), "color semantic");
        check(normal.evidenceGrade() == EvidenceGrade.X1_EXACT_STATIC, "evidence grade");

        check(normal.isExecutableShotSpecComplete(), "canonical archive resolves executable fields");
        check(normal.unresolvedFields().isEmpty(), "no unresolved shot fields");

        // The old source labels Shift as low-speed mode, but the actual speed stays 0.7.
        close(normal.speed(), focus.speed(), "focus must retain speed 0.7");

        System.out.println("HOMING_AMULET_CONTRACT_REGRESSION_PASS");
    }

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    private static void close(double actual, double expected, String message) {
        if (Math.abs(actual - expected) > 1.0e-9) {
            throw new AssertionError(message + ": " + actual + " != " + expected);
        }
    }
}
