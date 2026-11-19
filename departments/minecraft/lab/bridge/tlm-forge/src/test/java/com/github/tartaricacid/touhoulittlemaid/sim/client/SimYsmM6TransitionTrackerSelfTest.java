package com.github.tartaricacid.touhoulittlemaid.sim.client;

/** Standalone JDK-only regression for actual pre-dispatch -> post-M5 M6 qualification. */
public final class SimYsmM6TransitionTrackerSelfTest {
    public static void main(String[] args) {
        SimYsmM6TransitionTracker tracker = new SimYsmM6TransitionTracker();
        String id = "map|root.vars|variable.wuqi";

        var changed = tracker.observeTransition(
                "u", "wuqi", state(id, 0), state(id, 1), 1);
        require(changed.correlated() && changed.applied(),
                "same exact candidate 0 -> 1 matching assignment should be applied");
        require(changed.before() == 0.0d && changed.after() == 1.0d,
                "before/after mismatch");
        require(changed.matchedTransitionCount() == 1, "transition count mismatch");

        var same = tracker.observeTransition(
                "u", "wuqi", state(id, 1), state(id, 1), 1);
        require(same.correlated() && !same.applied(),
                "already-equal pre-state is correlation, not command-applied change");
        require(same.matchedTransitionCount() == 1,
                "non-transition must not increment evidence count");

        var wrongExpected = tracker.observeTransition(
                "u", "wuqi", state(id, 1), state(id, 0), 1);
        require(!wrongExpected.correlated() && !wrongExpected.applied(),
                "post state that misses assigned literal is not positive evidence");

        var moved = tracker.observeTransition(
                "u", "wuqi", state(id, 0), state("field|root.other.wuqi", 1), 1);
        require(moved.correlated() && !moved.applied(),
                "candidate identity change must not bridge before/after paths");

        var noBefore = tracker.observeTransition(
                "u", "wuqi", null, state(id, 1), 1);
        require(noBefore.correlated() && !noBefore.applied(),
                "missing pre-dispatch state cannot prove application");

        var changedBack = tracker.observeTransition(
                "u", "wuqi", state(id, 1), state(id, 0), 0);
        require(changedBack.applied() && changedBack.matchedTransitionCount() == 2,
                "second real transition should accumulate evidence");

        System.out.println("SimYsmM6TransitionTrackerSelfTest OK");
    }

    private static SimYsmM6TransitionTracker.State state(String identity, double value) {
        return new SimYsmM6TransitionTracker.State(identity, value);
    }

    private static void require(boolean ok, String message) {
        if (!ok) throw new AssertionError(message);
    }
}
