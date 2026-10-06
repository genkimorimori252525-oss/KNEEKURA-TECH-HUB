package dev.kneekura.fivedifficulties.core;

import dev.kneekura.fivedifficulties.core.timestop.TimeStopShape;
import dev.kneekura.fivedifficulties.core.x1.*;

public final class SakuyaWatchContractRegression {
    public static void main(String[] args) {
        SakuyaWatchModeContract half = SakuyaWatchContract.resolveMode(0);
        SakuyaWatchModeContract stop = SakuyaWatchContract.resolveMode(1);

        check(half.itemDamageMode() == 0, "half item mode");
        check(half.maxUseDurationTicks() == 20, "half charge time");
        check(half.creativeEffect().kind() == SakuyaTimeEffectKind.HALF_SPEED, "creative half");
        close(half.creativeEffect().timeScale(), 0.5, "half time scale");
        check(!half.creativeEffect().bounded(), "creative half unbounded");
        check(half.survivalFullChargeEffect().nominalDurationTicks() == 161, "limited half processing ticks");
        check(half.survivalFullChargeEffect().durationEvidenceGrade() == EvidenceGrade.X1_EXACT_STATIC,
                "limited half duration exact");

        check(stop.itemDamageMode() == 1, "stop item mode");
        check(stop.maxUseDurationTicks() == 48, "stop charge time");
        check(stop.creativeEffect().kind() == SakuyaTimeEffectKind.FULL_STOP, "creative stop");
        close(stop.creativeEffect().timeScale(), 0.0, "full-stop time scale");
        check(stop.survivalFullChargeEffect().nominalDurationTicks() == 101, "limited stop processing ticks");

        check(SakuyaWatchContract.SPELL_CARD_STOP.nominalDurationTicks() == 61, "spell stop processing ticks");
        check(SakuyaWatchContract.STOPWATCH_STOP.nominalDurationTicks() == 40, "stopwatch processing ticks");

        close(SakuyaWatchContract.FIELD_RANGE_BLOCKS, 40.0, "field range");
        close(SakuyaWatchContract.DUPLICATE_PRECHECK_RANGE_BLOCKS, 20.0, "duplicate precheck range");
        close(SakuyaWatchContract.CONTROLLER_FOLLOW_DISTANCE, 1.2, "controller follow distance");
        close(SakuyaWatchContract.CONTROLLER_YAW_OFFSET_DEGREES, -30.0, "controller yaw offset");
        close(SakuyaWatchContract.CONTROLLER_EYE_Y_OFFSET, -0.5, "controller eye y offset");
        check(SakuyaWatchContract.MIN_ENTITY_AGE_TICKS == 2, "new entity grace");
        check(SakuyaWatchContract.MANUAL_RELEASE_MIN_AGE_TICKS == 11, "sneak release threshold");
        check(SakuyaWatchContract.FIELD_SHAPE == TimeStopShape.AABB, "X1 field is AABB");

        check(SakuyaWatchContract.toggleModeDamage(0) == 1, "toggle 0->1");
        check(SakuyaWatchContract.toggleModeDamage(1) == 0, "toggle 1->0");

        for (SakuyaTimeEffectContract effect : new SakuyaTimeEffectContract[] {
                SakuyaWatchContract.CREATIVE_HALF,
                SakuyaWatchContract.LIMITED_HALF,
                SakuyaWatchContract.CREATIVE_STOP,
                SakuyaWatchContract.LIMITED_STOP,
                SakuyaWatchContract.SPELL_CARD_STOP,
                SakuyaWatchContract.STOPWATCH_STOP
        }) {
            check(effect.freezeCategoryPolicyResolved(), "freeze-category policy resolved");
            check(effect.unresolvedFreezeCategories().isEmpty(), "no unresolved freeze categories");
            check(effect.hasExactDuration(), "duration exact or unbounded");
        }

        boolean invalidRejected = false;
        try {
            SakuyaWatchContract.resolveMode(2);
        } catch (IllegalArgumentException expected) {
            invalidRejected = true;
        }
        check(invalidRejected, "invalid mode must fail closed");

        System.out.println("SAKUYA_WATCH_CONTRACT_REGRESSION_PASS");
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
