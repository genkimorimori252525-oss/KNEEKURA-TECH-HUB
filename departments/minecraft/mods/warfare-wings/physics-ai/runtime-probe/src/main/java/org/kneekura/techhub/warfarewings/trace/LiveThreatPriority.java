package org.kneekura.techhub.warfarewings.trace;

import org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.Vec3;
import org.kneekura.techhub.warfarewings.physics.ObservedProtectedAssetThreatSelection;
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
    record Threat(TacticalAirAI.Contact contact, double closestApproachBlocks,
                  double closestApproachTicks, double priorityBlocks,
                  double currentDistanceBlocks) {}

    private LiveThreatPriority() {}

    static Threat assess(TacticalAirAI.Contact visible, Vec3 protectedPosition,
                         Vec3 protectedVelocity) {
        return fromCommon(ObservedProtectedAssetThreatSelection.assess(
                visible, protectedPosition, protectedVelocity));
    }

    static boolean better(Threat candidate, Threat existing) {
        return ObservedProtectedAssetThreatSelection.better(toCommon(candidate), toCommon(existing));
    }

    /**
     * Retain ONLY a contact observed AGAIN this tick when its estimated
     * hazard remains competitive. Passing a remembered but invisible track
     * as previousVisible is prohibited by the caller's visual lookup.
     */
    static Threat chooseStable(Threat previousVisible, Threat bestVisible) {
        var previous = toCommon(previousVisible);
        var best = toCommon(bestVisible);
        var chosen = ObservedProtectedAssetThreatSelection.chooseStable(previous, best);
        return chosen == null ? null : chosen == previous ? previousVisible : bestVisible;
    }

    private static ObservedProtectedAssetThreatSelection.Threat toCommon(Threat threat) {
        return threat == null ? null : new ObservedProtectedAssetThreatSelection.Threat(
                threat.contact(), threat.closestApproachBlocks(), threat.closestApproachTicks(),
                threat.priorityBlocks(), threat.currentDistanceBlocks());
    }

    private static Threat fromCommon(ObservedProtectedAssetThreatSelection.Threat threat) {
        return new Threat(threat.contact(), threat.closestApproachBlocks(),
                threat.closestApproachTicks(), threat.priorityBlocks(), threat.currentDistanceBlocks());
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
        check(cap.closestApproachTicks() == 48.0, "track extrapolation bounded at 48 ticks");
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
