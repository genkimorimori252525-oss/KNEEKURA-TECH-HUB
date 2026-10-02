package com.github.tartaricacid.touhoulittlemaid.sim.client;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Pure-JDK qualifier for one actual pre-dispatch -> post-M5 YSM state transition.
 *
 * <p>Correlation requires the post state to equal the assigned literal. Applied evidence further
 * requires the pre and post observations to use the same stable exact candidate and different
 * values. Transition counts are kept per entity/variable/candidate for cumulative evidence.
 */
public final class SimYsmM6TransitionTracker {
    private final Map<Key, Integer> transitionCounts = new LinkedHashMap<>();

    public record State(String stableIdentity, double value) {}

    public record Decision(
            boolean correlated,
            boolean applied,
            Double before,
            double after,
            int matchedTransitionCount,
            String stableIdentity
    ) {}

    private record Key(String entityUuid, String variable, String stableIdentity) {}

    public Decision observeTransition(
            String entityUuid,
            String variable,
            State before,
            State after,
            double expectedValue) {
        if (blank(entityUuid)
                || blank(variable)
                || after == null
                || blank(after.stableIdentity())
                || !Double.isFinite(after.value())
                || !Double.isFinite(expectedValue)
                || Double.compare(after.value(), expectedValue) != 0) {
            return new Decision(false, false, null, Double.NaN, 0, "");
        }

        Key key = new Key(entityUuid, variable, after.stableIdentity());
        int count = transitionCounts.getOrDefault(key, 0);

        if (before == null
                || blank(before.stableIdentity())
                || !before.stableIdentity().equals(after.stableIdentity())
                || !Double.isFinite(before.value())
                || Double.compare(before.value(), after.value()) == 0) {
            return new Decision(
                    true, false,
                    before == null ? null : before.value(),
                    after.value(),
                    count,
                    after.stableIdentity());
        }

        int next = count + 1;
        transitionCounts.put(key, next);
        return new Decision(
                true, true, before.value(), after.value(), next, after.stableIdentity());
    }

    public void clear() {
        transitionCounts.clear();
    }

    private static boolean blank(String value) {
        return value == null || value.isBlank();
    }
}
