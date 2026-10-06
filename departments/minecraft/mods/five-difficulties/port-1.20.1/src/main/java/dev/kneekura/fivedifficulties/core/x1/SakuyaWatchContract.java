package dev.kneekura.fivedifficulties.core.x1;

import java.util.Set;

/**
 * ORIGINAL_SOURCE / ORIGINAL_BINARY derived Sakuya Watch/StopWatch contract retained by PR #93.
 *
 * Range/mode/charge selection is static evidence. Durations that the retained atlas records as
 * "about" are intentionally marked X1_STATIC_INFERENCE until the raw source is reopened.
 */
public final class SakuyaWatchContract {
    public static final double FIELD_RANGE_BLOCKS = 40.0;

    private static final Set<String> UNRESOLVED_FREEZE_CATEGORIES = Set.of(
            "blockTicks",
            "fluidTicks",
            "blockEntities",
            "randomChunkTicks",
            "particles",
            "animatedTextures",
            "worldDayTime",
            "damageReleaseSemantics",
            "otherPlayerMultiplayerPolicy"
    );

    public static final SakuyaTimeEffectContract CREATIVE_HALF = effect(
            SakuyaTimeEffectKind.HALF_SPEED, 0.5, false, -1, EvidenceGrade.X1_EXACT_STATIC
    );

    public static final SakuyaTimeEffectContract LIMITED_HALF = effect(
            SakuyaTimeEffectKind.HALF_SPEED, 0.5, true, 160, EvidenceGrade.X1_STATIC_INFERENCE
    );

    public static final SakuyaTimeEffectContract CREATIVE_STOP = effect(
            SakuyaTimeEffectKind.FULL_STOP, 0.0, false, -1, EvidenceGrade.X1_EXACT_STATIC
    );

    public static final SakuyaTimeEffectContract LIMITED_STOP = effect(
            SakuyaTimeEffectKind.FULL_STOP, 0.0, true, 100, EvidenceGrade.X1_STATIC_INFERENCE
    );

    public static final SakuyaTimeEffectContract SPELL_CARD_STOP = effect(
            SakuyaTimeEffectKind.SPELL_CARD_STOP, 0.0, true, 60, EvidenceGrade.X1_STATIC_INFERENCE
    );

    public static final SakuyaTimeEffectContract STOPWATCH_STOP = effect(
            SakuyaTimeEffectKind.FULL_STOP, 0.0, true, 40, EvidenceGrade.X1_STATIC_INFERENCE
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
            int durationTicks,
            EvidenceGrade durationEvidence
    ) {
        return new SakuyaTimeEffectContract(
                kind,
                FIELD_RANGE_BLOCKS,
                timeScale,
                bounded,
                durationTicks,
                durationEvidence,
                false,
                UNRESOLVED_FREEZE_CATEGORIES
        );
    }
}
