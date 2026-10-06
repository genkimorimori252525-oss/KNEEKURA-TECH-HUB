package dev.kneekura.fivedifficulties.core.x1;

import java.util.Set;

/** Exact static X1 time-effect contract. */
public record SakuyaTimeEffectContract(
        SakuyaTimeEffectKind kind,
        double rangeBlocks,
        double timeScale,
        boolean bounded,
        int nominalDurationTicks,
        EvidenceGrade durationEvidenceGrade,
        boolean freezeCategoryPolicyResolved,
        Set<String> unresolvedFreezeCategories
) {
    public SakuyaTimeEffectContract {
        if (kind == null || durationEvidenceGrade == null) throw new NullPointerException();
        if (!Double.isFinite(rangeBlocks) || rangeBlocks <= 0.0) throw new IllegalArgumentException("rangeBlocks");
        if (!Double.isFinite(timeScale) || timeScale < 0.0 || timeScale > 1.0) throw new IllegalArgumentException("timeScale");
        if (bounded && nominalDurationTicks <= 0) throw new IllegalArgumentException("bounded duration must be positive");
        if (!bounded && nominalDurationTicks != -1) throw new IllegalArgumentException("unbounded duration must use -1");
        unresolvedFreezeCategories = Set.copyOf(unresolvedFreezeCategories);
        if (freezeCategoryPolicyResolved && !unresolvedFreezeCategories.isEmpty()) {
            throw new IllegalArgumentException("resolved freeze policy cannot retain unresolved categories");
        }
    }

    public boolean hasExactDuration() {
        return !bounded || durationEvidenceGrade == EvidenceGrade.X1_EXACT_STATIC;
    }
}
