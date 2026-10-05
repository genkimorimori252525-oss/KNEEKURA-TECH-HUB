package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonObject;

/** Bounded sampled display state; does not grant owner authority or prove visible pixels. */
public final class KneekuraDebugTankStatus {
    private static final Gson GSON = new GsonBuilder().serializeNulls().create();
    public record Snapshot(String schema, boolean requested, boolean registered, boolean eligible,
            boolean drawSubmitted, boolean brightness, String reason, String recipeHash,
            KneekuraDebugTankPresentationRecipe.Geometry geometry, Long reportedRemainingMs,
            long statusSuppressedTotal) {
        JsonObject json() { return GSON.toJsonTree(this).getAsJsonObject(); }
    }
    private long lastSentNanos = Long.MIN_VALUE;
    private long lastDrawNanos = Long.MIN_VALUE;
    private KneekuraDebugTankPresentationRecipe.Context drawnContext;
    private String previousReason;
    private KneekuraDebugTankPresentationRecipe.View previousView;
    private long suppressed;

    synchronized Snapshot sample(KneekuraDebugTankPresentationRecipe.Context context, Object server,
            long now, boolean connected, boolean submitted) {
        boolean eligible = connected && context != null && context.viewFor(server, now) != null;
        if (submitted && eligible) { lastDrawNanos = now; drawnContext = context; }
        boolean drawn = eligible && drawnContext == context && lastDrawNanos != Long.MIN_VALUE
                && now - lastDrawNanos >= 0 && now - lastDrawNanos < 1_000_000_000L;
        String reason = !connected ? "DISCONNECTED" : context == null ? "UNREGISTERED"
                : server != context.server() ? "SERVER_MISMATCH"
                : !eligible ? "EXPIRED" : drawn ? "DRAW_SUBMITTED" : "ELIGIBLE_NOT_DRAWN";
        var view = context == null ? null : context.view();
        long interval = reason.equals(previousReason) && java.util.Objects.equals(view, previousView)
                ? 1_000_000_000L : 500_000_000L;
        if (lastSentNanos != Long.MIN_VALUE && now - lastSentNanos < interval) { suppressed++; return null; }
        lastSentNanos = now;
        previousReason = reason;
        previousView = view;
        Long remaining = context == null ? null : Math.max(0L, Math.min(120_000L,
                (context.deadlineNanos() - now) / 1_000_000L));
        return new Snapshot("kneekura.tank-presentation-status/v1", context != null, context != null,
                eligible, drawn, view != null && view.bright(), reason, view == null ? null : view.recipeHash(),
                view == null ? null : view.geometry(), remaining, suppressed);
    }
}
