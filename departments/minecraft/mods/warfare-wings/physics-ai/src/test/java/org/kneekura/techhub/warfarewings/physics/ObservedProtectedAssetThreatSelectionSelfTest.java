package org.kneekura.techhub.warfarewings.physics;

import java.util.Arrays;
import java.util.List;

import org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.Vec3;

/** Adversarial SOURCE-only selection checks; no Minecraft sightline proof. */
public final class ObservedProtectedAssetThreatSelectionSelfTest {
    private static final Vec3 ZERO = Vec3.ZERO;
    private static int assertions;

    private ObservedProtectedAssetThreatSelectionSelfTest() {}

    public static void main(String[] args) {
        var nearReceding = hostile("near-receding", 40, 0, 0, 1, 0, 0);
        var farInbound = hostile("far-inbound", 0, 0, 140, 0, 0, -4);
        var inbound = ObservedProtectedAssetThreatSelection.assess(farInbound, ZERO, ZERO);
        check(inbound.closestApproachTicks() == 35, "measured closing speed gives 35 ticks");
        check(inbound.closestApproachBlocks() == 0, "3D extrapolated crossing CPA");
        check(inbound.priorityBlocks() == 7, "0.2 blocks per tick urgency");
        check(inbound.currentDistanceBlocks() == 140, "current range is not CPA range");
        check(choose(List.of(nearReceding, farInbound), ZERO, ZERO, null).contact() == farInbound,
                "inbound outranks near departing enemy");
        check(choose(List.of(farInbound, nearReceding), ZERO, ZERO, null).contact() == farInbound,
                "ranking independent of observation iteration order");

        var stationaryRelative = ObservedProtectedAssetThreatSelection.assess(
                hostile("parallel", 70, 0, 0, 1, 0, 0), ZERO, new Vec3(1, 0, 0));
        check(stationaryRelative.closestApproachTicks() == 0, "matching ally/enemy velocity has no CPA clock");
        check(stationaryRelative.closestApproachBlocks() == 70, "matching velocities retain current gap");
        var bounded = ObservedProtectedAssetThreatSelection.assess(
                hostile("slow", 150, 0, 0, -1, 0, 0), ZERO, ZERO);
        check(bounded.closestApproachTicks() == 48, "CPA horizon capped to 48 ticks");
        check(bounded.closestApproachBlocks() == 102, "no far-future interception invented");
        check(bounded.priorityBlocks() == 111.6, "48-tick urgency included at bound");
        var perpendicular = ObservedProtectedAssetThreatSelection.assess(
                hostile("perpendicular", 100, 0, 0, 0, 0, 2), ZERO, ZERO);
        check(perpendicular.closestApproachTicks() == 0, "non-closing contact is not misclassified inbound");
        check(perpendicular.closestApproachBlocks() == 100, "perpendicular risk uses actual distance");
        var movingAsset = ObservedProtectedAssetThreatSelection.assess(
                hostile("relative", 130, 0, 0, 0, 0, 0), new Vec3(100, 0, 0), new Vec3(1, 0, 0));
        check(movingAsset.closestApproachTicks() == 30, "real allied velocity changes relative CPA");
        check(movingAsset.priorityBlocks() == 6, "protectee motion enters score");
        var vertical = ObservedProtectedAssetThreatSelection.assess(
                hostile("vertical", 10, 20, 50, 0, 0, -1), new Vec3(10, 20, 30), ZERO);
        check(vertical.closestApproachTicks() == 20, "nonzero XYZ protectee and contact geometry");
        check(vertical.closestApproachBlocks() == 0, "nonzero XYZ CPA is correct");

        var tieA = hostile("a", 30, 0, 0, 0, 0, 0);
        var tieZ = hostile("z", -30, 0, 0, 0, 0, 0);
        check(choose(List.of(tieZ, tieA), ZERO, ZERO, null).contact() == tieA,
                "exact tie uses ascending ID");
        check(choose(List.of(tieA, tieZ), ZERO, ZERO, null).contact() == tieA,
                "ID tie-breaker remains deterministic in reverse order");
        var farButSamePriority = hostile("a", 40, 0, 0, -1, 0, 0);
        var nearButSamePriority = hostile("z", 8, 0, 0, 0, 0, 0);
        check(choose(List.of(farButSamePriority, nearButSamePriority), ZERO, ZERO, null)
                .contact() == nearButSamePriority, "current distance beats ID for equal CPA priority");

        var retained = hostile("retain", 20, 0, 0, 0, 0, 0);
        var alternate = hostile("alternate", 14, 0, 0, 0, 0, 0);
        var emergency = hostile("emergency", 11, 0, 0, 0, 0, 0);
        check(choose(List.of(retained, alternate), ZERO, ZERO, "retain").contact() == retained,
                "previous contact still visible remains inside eight-block deadband");
        check(choose(List.of(alternate, retained), ZERO, ZERO, "retain").contact() == retained,
                "deadband is independent of hash iteration order");
        check(choose(List.of(retained, emergency), ZERO, ZERO, "retain").contact() == emergency,
                "urgent opponent breaks deadband");
        check(choose(List.of(retained, nearButSamePriority), ZERO, ZERO, "retain")
                .contact() == nearButSamePriority, "large margin overrides remembered target");
        var atBoundary = hostile("boundary", 12, 0, 0, 0, 0, 0);
        check(choose(List.of(retained, atBoundary), ZERO, ZERO, "retain").contact() == retained,
                "eight-block deadband upper bound is inclusive");
        check(choose(List.of(alternate), ZERO, ZERO, "retain").contact() == alternate,
                "unseen prior contact never enters current ranking");
        check(choose(List.of(alternate), ZERO, ZERO, "stale-could-have-been-dangerous")
                .contact() == alternate, "unknown previous ID cannot invent a contact");
        check(choose(List.of(), ZERO, ZERO, "retain") == null,
                "no observations produce no selected enemy");
        check(choose(List.of(), ZERO, ZERO, null) == null, "empty observation stays empty");

        var ignoreExtraFar = hostile("distant", 1000, 0, 0, 0, 0, 0);
        check(choose(List.of(alternate, ignoreExtraFar), ZERO, ZERO, null).contact() == alternate,
                "no per-target shared load penalty distorts CPA score");
        check(choose(List.of(alternate, ignoreExtraFar), new Vec3(1000, 0, 0), ZERO, null)
                .contact() == ignoreExtraFar, "same observed tracks scored separately for each protectee");
        check(!ObservedProtectedAssetThreatSelection.better(null, inbound), "null cannot outrank sighting");
        check(ObservedProtectedAssetThreatSelection.better(inbound, null), "sighting beats null");
        check(ObservedProtectedAssetThreatSelection.chooseStable(inbound, null) == null,
                "no best visible contact cannot retain past one");
        check(ObservedProtectedAssetThreatSelection.chooseStable(null, inbound) == inbound,
                "no prior visible contact leaves best contact unchanged");

        rejects(() -> ObservedProtectedAssetThreatSelection.assess(
                new TacticalAirAI.Contact("friendly", ZERO, ZERO, false), ZERO, ZERO),
                "non-hostile contact rejected");
        rejects(() -> choose(List.of(new TacticalAirAI.Contact("friendly", ZERO, ZERO, false)),
                ZERO, ZERO, null), "non-hostile inside selection rejected");
        rejects(() -> ObservedProtectedAssetThreatSelection.assess(null, ZERO, ZERO),
                "null is not a visible hostile");
        rejects(() -> choose(Arrays.asList((TacticalAirAI.Contact) null), ZERO, ZERO, null),
                "null list member must not synthesize a target");
        rejects(() -> choose(null, ZERO, ZERO, null), "null observation iterable invalid");
        rejects(() -> choose(List.of(farInbound), new Vec3(Double.NaN, 0, 0), ZERO, null),
                "invalid observed protectee position rejected");
        rejects(() -> choose(List.of(farInbound), ZERO, new Vec3(0, Double.POSITIVE_INFINITY, 0), null),
                "invalid allied velocity rejected");
        rejects(() -> choose(List.of(farInbound), ZERO, null, null), "unknown allied velocity rejected");

        System.out.println("ObservedProtectedAssetThreatSelection SOURCE PASS assertions=" + assertions
                + "; Forge visibility/gameplay NOT_RUN; B17 intrusion NOT_PROVEN");
    }

    private static TacticalAirAI.Contact hostile(String id, double x, double y, double z,
                                                  double vx, double vy, double vz) {
        return new TacticalAirAI.Contact(id, new Vec3(x, y, z), new Vec3(vx, vy, vz), true);
    }

    private static ObservedProtectedAssetThreatSelection.Threat choose(
            Iterable<TacticalAirAI.Contact> visible, Vec3 allyPosition,
            Vec3 allyVelocity, String previousId) {
        return ObservedProtectedAssetThreatSelection.select(visible, allyPosition, allyVelocity, previousId);
    }

    private static void rejects(Runnable operation, String reason) {
        try {
            operation.run();
            throw new AssertionError(reason);
        } catch (IllegalArgumentException expected) {
            assertions++;
        }
    }

    private static void check(boolean ok, String reason) {
        if (!ok) throw new AssertionError(reason);
        assertions++;
    }
}
