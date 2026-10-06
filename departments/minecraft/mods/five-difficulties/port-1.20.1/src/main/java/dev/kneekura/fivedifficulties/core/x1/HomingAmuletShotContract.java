package dev.kneekura.fivedifficulties.core.x1;

import java.util.Set;

/**
 * Evidence-backed intent for one Homing Amulet firing branch.
 *
 * This deliberately stops before converting into LegacyShotSpec because the
 * current retained X1 evidence does not pin every numeric ShotData field.
 */
public record HomingAmuletShotContract(
        int shotCount,
        double totalSpreadDegrees,
        double shotSize,
        double damage,
        double speed,
        String projectileFamily,
        String colorName,
        String specialBehavior,
        double maxHomingTurnDegreesPerTick,
        EvidenceGrade evidenceGrade,
        Set<String> unresolvedFields
) {
    public HomingAmuletShotContract {
        if (shotCount <= 0) throw new IllegalArgumentException("shotCount <= 0");
        finiteNonNegative(totalSpreadDegrees, "totalSpreadDegrees");
        finitePositive(shotSize, "shotSize");
        finiteNonNegative(damage, "damage");
        finiteNonNegative(speed, "speed");
        finiteNonNegative(maxHomingTurnDegreesPerTick, "maxHomingTurnDegreesPerTick");
        if (projectileFamily == null || colorName == null || specialBehavior == null || evidenceGrade == null) {
            throw new NullPointerException();
        }
        unresolvedFields = Set.copyOf(unresolvedFields);
    }

    public boolean isExecutableShotSpecComplete() {
        return unresolvedFields.isEmpty();
    }

    private static void finiteNonNegative(double value, String name) {
        if (!Double.isFinite(value) || value < 0.0) throw new IllegalArgumentException(name);
    }

    private static void finitePositive(double value, String name) {
        if (!Double.isFinite(value) || value <= 0.0) throw new IllegalArgumentException(name);
    }
}
