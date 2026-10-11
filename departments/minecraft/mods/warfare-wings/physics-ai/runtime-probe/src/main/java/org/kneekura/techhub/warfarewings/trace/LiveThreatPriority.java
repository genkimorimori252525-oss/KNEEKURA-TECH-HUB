package org.kneekura.techhub.warfarewings.trace;

import org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.Vec3;
import org.kneekura.techhub.warfarewings.physics.TacticalAirAI;

/**
 * Threat ranking for an already observed, explicit hostile-team contact.
 *
 * This class has no Minecraft entity/world access and MUST only receive
 * contacts returned by LiveAirSensor.observe or previously measured tracks.
 * A friendly protectee's actual velocity is allowed via same-team radio.
 * Scores are steering priorities, never damage, collision or firing evidence.
 */
final class LiveThreatPriority {
    private static final double HORIZON_TICKS = 48.0;
    private static final double EPS = 1e-12;
    private static final double URGENCY_BLOCKS_PER_TICK = .20;
    // A threat-choice deadband suppresses flip-flop steering between two
    // comparably dangerous, *simultaneously visible* opponents. It is a
    // guidance hysteresis, not the original 95b/6b/30b GameTest threshold.
    // The complete original Forge control trace showed switches at 47 and
    // 109 with predicted approach scores differing by <0.03 blocks.
    private static final double CONTACT_STICKINESS_BLOCKS = 8.0;

    record Threat(TacticalAirAI.Contact contact, double closestApproachBlocks,
                  double closestApproachTicks, double priorityBlocks,
                  double currentDistanceBlocks) {}

    private LiveThreatPriority() {}

    static Threat assess(TacticalAirAI.Contact visible, Vec3 protectedPosition,
                         Vec3 protectedVelocity) {
        if (visible == null || !visible.hostile() || protectedPosition == null
                || protectedVelocity == null) {
            throw new IllegalArgumentException("Expected only an actually visible hostile and known ally");
        }
        Vec3 r = visible.position().add(protectedPosition.scale(-1));
        Vec3 v = visible.velocity().add(protectedVelocity.scale(-1));
        if (!finite(r) || !finite(v))
            throw new IllegalArgumentException("Nonfinite observed relative aircraft geometry");
        double velocitySquared = v.lengthSquared();
        double t = velocitySquared <= EPS ? 0
                : clamp(-r.dot(v) / velocitySquared, 0, HORIZON_TICKS);
        double predictedDistance = r.add(v.scale(t)).length();
        double current = r.length();
        // Earlier risks deserve priority, but the selection never knows the
        // actual future target position. This is constant-velocity extrapolation
        // of the visible current measurement, not a guaranteed intercept.
        return new Threat(visible, predictedDistance, t,
                predictedDistance + t * URGENCY_BLOCKS_PER_TICK, current);
    }

    static boolean better(Threat candidate, Threat existing) {
        if (candidate == null) return false;
        if (existing == null) return true;
        double diff = candidate.priorityBlocks() - existing.priorityBlocks();
        if (Math.abs(diff) > 1e-8) return diff < 0;
        double distanceDiff = candidate.currentDistanceBlocks() - existing.currentDistanceBlocks();
        if (Math.abs(distanceDiff) > 1e-8) return distanceDiff < 0;
        return candidate.contact().id().compareTo(existing.contact().id()) < 0;
    }

    /**
     * Retain ONLY a contact observed AGAIN this tick when its estimated
     * hazard remains competitive. Passing a remembered but invisible track
     * as previousVisible is prohibited by the caller's visual lookup.
     */
    static Threat chooseStable(Threat previousVisible, Threat bestVisible) {
        if (bestVisible == null) return null;
        if (previousVisible == null) return bestVisible;
        return previousVisible.priorityBlocks()
                <= bestVisible.priorityBlocks() + CONTACT_STICKINESS_BLOCKS
                ? previousVisible : bestVisible;
    }

    private static double clamp(double x, double min, double max) {
        return Math.max(min, Math.min(max, x));
    }

    private static boolean finite(Vec3 v) {
        return Double.isFinite(v.x()) && Double.isFinite(v.y()) && Double.isFinite(v.z());
    }

    /** These 19 assertions are SOURCE tests only, never real-game proof. */
    public static void main(String[] ignored) {
        Vec3 z = new Vec3(0, 0, 0);
        var nearDeparting = assess(contact("near-departing", 40, 0, 0, 1, 0, 0), z, z);
        var farInbound = assess(contact("far-inbound", 0, 0, 140, 0, 0, -4), z, z);
        check(nearDeparting.currentDistanceBlocks() == 40, "current range of nearer receding hostile");
        check(farInbound.currentDistanceBlocks() == 140, "inbound is farther at first observation");
        check(farInbound.closestApproachTicks() == 35, "closing time from observed motion");
        check(farInbound.closestApproachBlocks() == 0, "observed route crosses protectee");
        check(better(farInbound, nearDeparting), "dangerous farther inbound outranks nearby receding");
        check(!better(nearDeparting, farInbound), "ranking not asymmetrically reversed");
        var fastFriend = assess(contact("parallel", 70, 0, 0, 1, 0, 0), z, new Vec3(1, 0, 0));
        check(fastFriend.closestApproachTicks() == 0, "same velocity doesn't invent approach");
        check(fastFriend.closestApproachBlocks() == 70, "stationary relative geometry remains far");
        var cap = assess(contact("slow-approach", 150, 0, 0, -1, 0, 0), z, z);
        check(cap.closestApproachTicks() == HORIZON_TICKS, "track extrapolation bounded at 48 ticks");
        check(cap.closestApproachBlocks() == 102, "bounded predicted miss distance");
        var miss = assess(contact("crossing", 100, 0, 0, 0, 0, 2), z, z);
        check(miss.closestApproachTicks() == 0, "perpendicular crossing receding from asset");
        check(miss.closestApproachBlocks() == 100, "no false closing on 90 degree flight");
        var a = assess(contact("a", 30, 0, 0, 0, 0, 0), z, z);
        var b = assess(contact("b", -30, 0, 0, 0, 0, 0), z, z);
        check(better(a, b), "tie is deterministic and independent of Java hash iteration order");
        check(!better(b, a), "tie symmetry is stable");
        check(!better(null, a), "missing sighting cannot outrank a real sighting");
        var previousStillVisible = assess(contact("previous", 20, 0, 0, 0, 0, 0), z, z);
        var barelyRiskier = assess(contact("alternate", 14, 0, 0, 0, 0, 0), z, z);
        check(chooseStable(previousStillVisible, barelyRiskier) == previousStillVisible,
                "small real-measured CPA score difference must not flicker the bomber bearing");
        var muchRiskier = assess(contact("critical", 9, 0, 0, 0, 0, 0), z, z);
        check(chooseStable(previousStillVisible, muchRiskier) == muchRiskier,
                "urgent real visible threat must override stale preferred direction");
        check(chooseStable(null, barelyRiskier) == barelyRiskier,
                "lost previous sighting cannot be injected as true visibility");
        check(chooseStable(previousStillVisible, null) == null,
                "no current sighting is not evidence of a threat choice");
        try {
            assess(new TacticalAirAI.Contact("hidden", z, z, false), z, z);
            throw new AssertionError("unseen hostile illegally accepted");
        } catch (IllegalArgumentException expected) {
            // Observability fail-closed: no unobserved contact enters ranking.
        }
        System.out.println("LiveThreatPriority SOURCE geometry tests PASS assertions=19; Forge LOS NOT_RUN");
    }

    private static TacticalAirAI.Contact contact(String id, double x, double y, double z,
                                                 double vx, double vy, double vz) {
        return new TacticalAirAI.Contact(id, new Vec3(x, y, z), new Vec3(vx, vy, vz), true);
    }

    private static void check(boolean ok, String reason) {
        if (!ok) throw new AssertionError(reason);
    }
}
