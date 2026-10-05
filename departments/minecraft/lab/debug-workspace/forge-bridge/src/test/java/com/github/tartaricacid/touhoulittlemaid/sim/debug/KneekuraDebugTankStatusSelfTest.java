package com.github.tartaricacid.touhoulittlemaid.sim.debug;

/** Pure clock/server/lease tests; no client, disk or graphics context. */
public final class KneekuraDebugTankStatusSelfTest {
    private static void check(boolean value, String message) { if (!value) throw new AssertionError(message); }
    public static void main(String[] args) {
        Object server = new Object();
        var view = new KneekuraDebugTankPresentationRecipe.View(
                new KneekuraDebugTankPresentationRecipe.Geometry(0, 64, 0, 16, 8, 16), true, "a".repeat(64));
        var context = new KneekuraDebugTankPresentationRecipe.Context(view, server, 0L, 120_000_000_000L);
        var status = new KneekuraDebugTankStatus();
        var first = status.sample(context, server, 0L, true, false);
        check(first != null && first.eligible() && !first.drawSubmitted(), "registration does not prove drawing");
        check(status.sample(context, server, 1L, true, true) == null, "first transition is rate limited");
        var drawn = status.sample(context, server, 500_000_000L, true, true);
        check(drawn != null && drawn.drawSubmitted(), "endBatch submitted, pixels remain unproven");
        check(drawn.reportedRemainingMs() == 119500L && drawn.statusSuppressedTotal() == 1L, "original remaining and suppression");
        check(status.sample(context, server, 600_000_000L, true, true) == null, "no frame-rate records");
        check(status.sample(context, server, 1_499_000_000L, true, true) == null, "steady state at most 1Hz");
        check(status.sample(context, server, 1_500_000_000L, true, true) != null, "steady state 1Hz");
        var expired = status.sample(context, server, 120_000_000_000L, true, false);
        check(expired != null && !expired.eligible() && !expired.drawSubmitted() && expired.reason().equals("EXPIRED"), "pause cannot renew lease");
        check(expired.reportedRemainingMs() == 0L, "no new deadline");
        var foreign = status.sample(context, new Object(), 121_000_000_000L, true, false);
        check(foreign != null && foreign.reason().equals("SERVER_MISMATCH"), "server ownership exact");
        var disconnected = status.sample(context, server, 122_000_000_000L, false, false);
        check(disconnected != null && disconnected.reason().equals("DISCONNECTED"), "disconnected never eligible");
        check(first.eligible() && !first.drawSubmitted(), "prior snapshot immutable");
        var cleared = status.sample(null, server, 123_000_000_000L, true, false);
        check(cleared != null && !cleared.eligible() && !cleared.registered() && cleared.reason().equals("EXPIRED")
                && cleared.recipeHash().equals(view.recipeHash()), "cleared presentation retains only historical expiry metadata");
        status.reset();
        check(status.sample(null, server, 124_000_000_000L, true, false).reason().equals("UNREGISTERED"), "new owner binding does not reuse old metadata");
        System.out.println("TANK_STATUS_INTEROP:" + new com.google.gson.Gson().toJson(drawn.json()));
        System.out.println("TANK_STATUS_INTEROP:" + new com.google.gson.Gson().toJson(new KneekuraDebugTankStatus().sample(null, server, 0L, true, false).json()));
        System.out.println("Tank status clock self-test: 14 checks passed");
    }
}
