package org.kneekura.techhub.warfarewings.physics;

import org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.Vec3;

/**
 * Per-observer protected-asset threat ordering based exclusively on current
 * visible hostile contacts and the actually observed allied protectee motion.
 *
 * The caller MUST supply only fresh hostile Contact measurements which passed
 * this actor's sensor/FOV/range/LOS check on this tick. Contact itself has no
 * observation timestamp or visibility proof: neither this class nor a SOURCE
 * test can certify that caller-side observation. Previous target ID is only
 * a preference, never an additional observation or an inferred global enemy.
 * No weapons are activated by this ranking.
 */
public final class ObservedProtectedAssetThreatSelection {
    private static final double HORIZON_TICKS = 48.0;
    private static final double EPS = 1e-12;
    private static final double URGENCY_BLOCKS_PER_TICK = 0.20;
    private static final double CONTACT_STICKINESS_BLOCKS = 8.0;

    public record Threat(TacticalAirAI.Contact contact, double closestApproachBlocks,
                         double closestApproachTicks, double priorityBlocks,
                         double currentDistanceBlocks) {}

    private ObservedProtectedAssetThreatSelection() {}

    /** Assess one actually visible hostile against the observed protectee. */
    public static Threat assess(TacticalAirAI.Contact visible, Vec3 protectedPosition,
                                Vec3 protectedVelocity) {
        if (visible == null || !visible.hostile() || protectedPosition == null
                || protectedVelocity == null)
            throw new IllegalArgumentException("Expected only an actually visible hostile and known ally");
        Vec3 r = visible.position().add(protectedPosition.scale(-1));
        Vec3 v = visible.velocity().add(protectedVelocity.scale(-1));
        if (!finite(r) || !finite(v))
            throw new IllegalArgumentException("Nonfinite observed relative aircraft geometry");
        double velocitySquared = v.lengthSquared();
        double t = velocitySquared <= EPS ? 0
                : clamp(-r.dot(v) / velocitySquared, 0, HORIZON_TICKS);
        double predictedDistance = r.add(v.scale(t)).length();
        double current = r.length();
        return new Threat(visible, predictedDistance, t,
                predictedDistance + t * URGENCY_BLOCKS_PER_TICK, current);
    }

    /** Lowest CPA + 0.2 blocks/tick; current distance then ID break near ties. */
    public static boolean better(Threat candidate, Threat existing) {
        if (candidate == null) return false;
        if (existing == null) return true;
        double diff = candidate.priorityBlocks() - existing.priorityBlocks();
        if (Math.abs(diff) > 1e-8) return diff < 0;
        double distanceDiff = candidate.currentDistanceBlocks() - existing.currentDistanceBlocks();
        if (Math.abs(distanceDiff) > 1e-8) return distanceDiff < 0;
        return candidate.contact().id().compareTo(existing.contact().id()) < 0;
    }

    /** Retain a former choice only if that same contact was observed again. */
    public static Threat chooseStable(Threat previousCurrentlyVisible, Threat bestCurrentlyVisible) {
        if (bestCurrentlyVisible == null) return null;
        if (previousCurrentlyVisible == null) return bestCurrentlyVisible;
        return previousCurrentlyVisible.priorityBlocks()
                <= bestCurrentlyVisible.priorityBlocks() + CONTACT_STICKINESS_BLOCKS
                ? previousCurrentlyVisible : bestCurrentlyVisible;
    }

    /**
     * Choose exclusively from this actor's freshly visible hostile contacts.
     * An absent previousTargetId has no influence, even if a historical track
     * for that ID exists elsewhere. Returns null if no hostiles are visible.
     */
    public static Threat select(Iterable<TacticalAirAI.Contact> currentlyVisibleHostiles,
                                Vec3 protectedPosition, Vec3 protectedVelocity,
                                String previousTargetId) {
        if (currentlyVisibleHostiles == null)
            throw new IllegalArgumentException("Current visible hostile observations required");
        Threat best = null;
        Threat previousCurrentlyVisible = null;
        for (TacticalAirAI.Contact visible : currentlyVisibleHostiles) {
            Threat candidate = assess(visible, protectedPosition, protectedVelocity);
            if (previousTargetId != null && previousTargetId.equals(visible.id()))
                previousCurrentlyVisible = candidate;
            if (better(candidate, best)) best = candidate;
        }
        return chooseStable(previousCurrentlyVisible, best);
    }

    private static double clamp(double x, double min, double max) {
        return Math.max(min, Math.min(max, x));
    }

    private static boolean finite(Vec3 v) {
        return Double.isFinite(v.x()) && Double.isFinite(v.y()) && Double.isFinite(v.z());
    }
}
