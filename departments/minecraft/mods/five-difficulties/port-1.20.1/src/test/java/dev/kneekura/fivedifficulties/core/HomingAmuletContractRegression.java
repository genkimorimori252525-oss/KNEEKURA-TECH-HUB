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
        close(normal.shotSize(), 0.4, "normal size");
        close(normal.damage(), 5.0, "normal damage");

        check(focus.shotCount() == 2, "focus count");
        close(focus.totalSpreadDegrees(), 20.0, "focus span");
        close(focus.shotSize(), 1.0, "focus size");
        close(focus.damage(), 8.0, "focus damage");

        close(normal.speed(), 0.7, "normal speed");
        close(focus.speed(), 0.7, "focus speed");
        check(normal.specialBehavior().equals("HOMING01"), "normal special");
        check(focus.specialBehavior().equals("HOMING01"), "focus special");
        close(normal.maxHomingTurnDegreesPerTick(), 4.0, "normal homing turn");
        close(focus.maxHomingTurnDegreesPerTick(), 4.0, "focus homing turn");
        check(normal.projectileFamily().equals("AMULET"), "projectile family");
        check(normal.colorName().equals("RED"), "color semantic");
        check(normal.evidenceGrade() == EvidenceGrade.X1_EXACT_STATIC, "evidence grade");

        check(!normal.isExecutableShotSpecComplete(), "must remain incomplete without raw numeric mapping");
        check(normal.unresolvedFields().contains("legacyNumericShotType"), "shot type unresolved");
        check(normal.unresolvedFields().contains("legacyNumericColorId"), "color id unresolved");
        check(normal.unresolvedFields().contains("lifetimeTicks"), "lifetime unresolved");
        check(normal.unresolvedFields().contains("THShotLibPerShotAngleDistribution"), "fan distribution unresolved");

        // Regression against a common misreading of the old source comment:
        // Shift/focus does NOT lower projectile speed in the retained X1 evidence.
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
