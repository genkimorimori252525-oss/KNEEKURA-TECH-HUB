package dev.kneekura.fivedifficulties.core.x1;

import java.util.Set;

/**
 * ORIGINAL_SOURCE / ORIGINAL_BINARY derived contract retained by PR #93.
 *
 * Source evidence says both branches use speed 0.7 and HOMING01, while Shift
 * changes count/spread/size/damage from a wide fan to a focused pair.
 */
public final class HomingAmuletContract {
    private static final Set<String> CURRENTLY_UNRESOLVED = Set.of(
            "legacyNumericShotType",
            "legacyNumericColorId",
            "lifetimeTicks",
            "THShotLibPerShotAngleDistribution"
    );

    public static final HomingAmuletShotContract NORMAL = new HomingAmuletShotContract(
            5,
            100.0,
            0.4,
            5.0,
            0.7,
            "AMULET",
            "RED",
            "HOMING01",
            4.0,
            EvidenceGrade.X1_EXACT_STATIC,
            CURRENTLY_UNRESOLVED
    );

    public static final HomingAmuletShotContract FOCUSED = new HomingAmuletShotContract(
            2,
            20.0,
            1.0,
            8.0,
            0.7,
            "AMULET",
            "RED",
            "HOMING01",
            4.0,
            EvidenceGrade.X1_EXACT_STATIC,
            CURRENTLY_UNRESOLVED
    );

    private HomingAmuletContract() {}

    public static HomingAmuletShotContract resolve(boolean focused) {
        return focused ? FOCUSED : NORMAL;
    }
}
