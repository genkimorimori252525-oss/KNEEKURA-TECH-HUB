package dev.kneekura.fivedifficulties.core.x1;

import dev.kneekura.fivedifficulties.core.timestop.TimeStopShape;
import java.util.Set;

/** Exact static contract from canonical X1 Sakuya Watch/StopWatch source. */
public final class SakuyaWatchContract {
    public static final double FIELD_RANGE_BLOCKS = 40.0;
    public static final double DUPLICATE_PRECHECK_RANGE_BLOCKS = 20.0;
    public static final double CONTROLLER_FOLLOW_DISTANCE = 1.2;
    public static final double CONTROLLER_YAW_OFFSET_DEGREES = -30.0;
    public static final double CONTROLLER_EYE_Y_OFFSET = -0.5;
    public static final int MIN_ENTITY_AGE_TICKS = 2;
    public static final int MANUAL_RELEASE_MIN_AGE_TICKS = 11;
    public static final TimeStopShape FIELD_SHAPE = TimeStopShape.AABB;

    /**
     * Processing-update counts, not merely source thresholds.
     * Watch's >N checks do not immediately return, so modes 1/5/6 can process on N+1.
     */
    public static final int SPELL_STOP_PROCESSING_TICKS = 61;
    public static final int LIMITED_STOP_PROCESSING_TICKS = 101;
    public static final int LIMITED_HALF_PROCESSING_TICKS = 161;
    public static final int STOPWATCH_PROCESSING_TICKS = 40;

    public static final SakuyaTimeEffectContract CREATIVE_HALF = effect(
            SakuyaTimeEffectKind.HALF_SPEED, 0.5, false, -1
    );

    public static final SakuyaTimeEffectContract LIMITED_HALF = effect(
            SakuyaTimeEffectKind.HALF_SPEED, 0.5, true, LIMITED_HALF_PROCESSING_TICKS
    );

    public static final SakuyaTimeEffectContract CREATIVE_STOP = effect(
            SakuyaTimeEffectKind.FULL_STOP, 0.0, false, -1
    );

    public static final SakuyaTimeEffectContract LIMITED_STOP = effect(
            SakuyaTimeEffectKind.FULL_STOP, 0.0, true, LIMITED_STOP_PROCESSING_TICKS
    );

    public static final SakuyaTimeEffectContract SPELL_CARD_STOP = effect(
            SakuyaTimeEffectKind.SPELL_CARD_STOP, 0.0, true, SPELL_STOP_PROCESSING_TICKS
    );

    public static final SakuyaTimeEffectContract STOPWATCH_STOP = effect(
            SakuyaTimeEffectKind.FULL_STOP, 0.0, true, STOPWATCH_PROCESSING_TICKS
    );

    public static final SakuyaWatchModeContract HALF_MODE = new SakuyaWatchModeContract(
            0,
            20,
            CREATIVE_HALF,
            LIMITED_HALF
    );

    public static final SakuyaWatchModeContract STOP_MODE = new SakuyaWatchModeContract(
            1,
            48,
            CREATIVE_STOP,
            LIMITED_STOP
    );

    private SakuyaWatchContract() {}

    public static SakuyaWatchModeContract resolveMode(int itemDamageMode) {
        return switch (itemDamageMode) {
            case 0 -> HALF_MODE;
            case 1 -> STOP_MODE;
            default -> throw new IllegalArgumentException("Unsupported X1 Sakuya Watch mode: " + itemDamageMode);
        };
    }

    public static int toggleModeDamage(int itemDamageMode) {
        return switch (itemDamageMode) {
            case 0 -> 1;
            case 1 -> 0;
            default -> throw new IllegalArgumentException("Unsupported X1 Sakuya Watch mode: " + itemDamageMode);
        };
    }

    private static SakuyaTimeEffectContract effect(
            SakuyaTimeEffectKind kind,
            double timeScale,
            boolean bounded,
            int durationTicks
    ) {
        return new SakuyaTimeEffectContract(
                kind,
                FIELD_RANGE_BLOCKS,
                timeScale,
                bounded,
                durationTicks,
                EvidenceGrade.X1_EXACT_STATIC,
                true,
                Set.of()
        );
    }
}
