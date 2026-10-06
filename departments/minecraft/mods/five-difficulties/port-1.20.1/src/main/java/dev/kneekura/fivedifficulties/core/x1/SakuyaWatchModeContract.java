package dev.kneekura.fivedifficulties.core.x1;

public record SakuyaWatchModeContract(
        int itemDamageMode,
        int maxUseDurationTicks,
        SakuyaTimeEffectContract creativeEffect,
        SakuyaTimeEffectContract survivalFullChargeEffect
) {
    public SakuyaWatchModeContract {
        if (itemDamageMode < 0) throw new IllegalArgumentException("itemDamageMode");
        if (maxUseDurationTicks <= 0) throw new IllegalArgumentException("maxUseDurationTicks");
        if (creativeEffect == null || survivalFullChargeEffect == null) throw new NullPointerException();
    }
}
