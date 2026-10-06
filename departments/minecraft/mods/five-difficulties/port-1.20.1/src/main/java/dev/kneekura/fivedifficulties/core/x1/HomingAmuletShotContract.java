package dev.kneekura.fivedifficulties.core.x1;

import java.util.Set;

/**
 * Exact X1 contract for one red Homing Amulet firing branch.
 */
public record HomingAmuletShotContract(
        int shotCount,
        double totalSpreadDegrees,
        double shotSize,
        double damage,
        double speed,
        int legacyForm,
        int legacyColor,
        int delayTicks,
        int lifetimeTicks,
        int specialId,
        double spawnDistance,
        double baseAngleDegrees,
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
        if (legacyForm < 0 || legacyColor < 0 || specialId < 0) throw new IllegalArgumentException("negative legacy id");
        if (delayTicks < 0) throw new IllegalArgumentException("delayTicks < 0");
        if (lifetimeTicks <= 0) throw new IllegalArgumentException("lifetimeTicks <= 0");
        finiteNonNegative(spawnDistance, "spawnDistance");
        if (!Double.isFinite(baseAngleDegrees)) throw new IllegalArgumentException("baseAngleDegrees");
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
