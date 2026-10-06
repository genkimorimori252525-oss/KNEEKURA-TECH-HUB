package dev.kneekura.fivedifficulties.core;

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
        check(half.survivalFullChargeEffect().nominalDurationTicks() == 160, "limited half nominal duration");
        check(half.survivalFullChargeEffect().durationEvidenceGrade() == EvidenceGrade.X1_STATIC_INFERENCE,
                "limited half duration must remain inference-grade");

        check(stop.itemDamageMode() == 1, "stop item mode");
        check(stop.maxUseDurationTicks() == 48, "stop charge time");
        check(stop.creativeEffect().kind() == SakuyaTimeEffectKind.FULL_STOP, "creative stop");
        close(stop.creativeEffect().timeScale(), 0.0, "full-stop time scale");
        check(stop.survivalFullChargeEffect().nominalDurationTicks() == 100, "limited stop nominal duration");

        check(SakuyaWatchContract.SPELL_CARD_STOP.nominalDurationTicks() == 60, "spell stop nominal duration");
        check(SakuyaWatchContract.STOPWATCH_STOP.nominalDurationTicks() == 40, "stopwatch nominal duration");

        close(SakuyaWatchContract.FIELD_RANGE_BLOCKS, 40.0, "field range");
        close(SakuyaWatchContract.SPELL_CARD_STOP.rangeBlocks(), 40.0, "spell range");
        close(SakuyaWatchContract.STOPWATCH_STOP.rangeBlocks(), 40.0, "stopwatch range");

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
            check(!effect.freezeCategoryPolicyResolved(), "freeze-category policy must stay unresolved");
            check(effect.unresolvedFreezeCategories().contains("particles"), "particles unresolved");
            check(effect.unresolvedFreezeCategories().contains("blockTicks"), "block ticks unresolved");
            check(effect.unresolvedFreezeCategories().contains("otherPlayerMultiplayerPolicy"), "multiplayer unresolved");
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
