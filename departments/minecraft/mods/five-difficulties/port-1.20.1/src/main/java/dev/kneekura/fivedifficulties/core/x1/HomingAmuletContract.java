package dev.kneekura.fivedifficulties.core.x1;

import java.util.Set;

/**
 * Exact red Homing Amulet contract recovered from the canonical X1 archive.
 */
public final class HomingAmuletContract {
    public static final int FORM_AMULET = 27;
    public static final int COLOR_RED = 0;
    public static final int SPECIAL_HOMING01 = 10;
    public static final int LIFETIME_TICKS = 90;
    public static final int DELAY_TICKS = 0;
    public static final double SPAWN_DISTANCE = 0.5;
    public static final double BASE_ANGLE_DEGREES = 0.0;

    public static final HomingAmuletShotContract NORMAL = new HomingAmuletShotContract(
            5,
            100.0,
            0.4,
            5.0,
            0.7,
            FORM_AMULET,
            COLOR_RED,
            DELAY_TICKS,
            LIFETIME_TICKS,
            SPECIAL_HOMING01,
            SPAWN_DISTANCE,
            BASE_ANGLE_DEGREES,
            "AMULET",
            "RED",
            "HOMING01",
            4.0,
            EvidenceGrade.X1_EXACT_STATIC,
            Set.of()
    );

    public static final HomingAmuletShotContract FOCUSED = new HomingAmuletShotContract(
            2,
            20.0,
            1.0,
            8.0,
            0.7,
            FORM_AMULET,
            COLOR_RED,
            DELAY_TICKS,
            LIFETIME_TICKS,
            SPECIAL_HOMING01,
            SPAWN_DISTANCE,
            BASE_ANGLE_DEGREES,
            "AMULET",
            "RED",
            "HOMING01",
            4.0,
            EvidenceGrade.X1_EXACT_STATIC,
            Set.of()
    );

    private HomingAmuletContract() {}

    public static HomingAmuletShotContract resolve(boolean focused) {
        return focused ? FOCUSED : NORMAL;
    }
}
