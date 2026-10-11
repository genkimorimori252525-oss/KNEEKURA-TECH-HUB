package org.kneekura.techhub.warfarewings.trace;

import net.minecraft.world.phys.Vec3;
import org.kneekura.techhub.warfarewings.physics.TacticalAirAI;

/**
 * Deterministic server-side mission phases around the source-only tactical
 * controller. Distances/timers are GAME_ADAPTATION, not historical ballistics.
 * No projectile, landing, damage, or weapon-release operation happens here.
 */
final class LiveMissionPlanner {
    enum Phase { TRANSIT, ESCORT_COVER, STRIKE_INGRESS, STRIKE_EGRESS, RETURNING }

    record Intent(Phase phase, TacticalAirAI.Mission guidanceMission, Vec3 waypoint,
                  boolean mayUseObservedHostile, String reason) {}

    static Intent select(TacticalAirAI.Mission mission, Phase prior, Vec3 position,
                         Vec3 destination, Vec3 home, Vec3 escortStation,
                         boolean requestedReturn, double fuel, double health) {
        if (mission == null || prior == null || !valid(position) || !valid(destination)
                || !valid(home) || escortStation != null && !valid(escortStation)
                || !Double.isFinite(fuel) || !Double.isFinite(health))
            throw new IllegalArgumentException("invalid live mission state");
        // The human order or the observed IA fuel/health reading may override
        // every combat/strike duty. This remains route-to-home, not landing.
        if (requestedReturn || prior == Phase.RETURNING || fuel < 0.12 || health < 0.22)
            return new Intent(Phase.RETURNING, TacticalAirAI.Mission.PATROL,
                    home, false, "RTB_WAYPOINT_NO_AUTOLAND");

        if (strike(mission)) {
            if (prior == Phase.STRIKE_EGRESS || position.distanceTo(destination) < 75)
                return new Intent(Phase.STRIKE_EGRESS, TacticalAirAI.Mission.PATROL,
                        home, false, "STRIKE_EGRESS_NO_ORDNANCE");
            return new Intent(Phase.STRIKE_INGRESS, mission, destination,
                    true, "STRIKE_INGRESS_NO_ORDNANCE");
        }

        if (mission == TacticalAirAI.Mission.ESCORT)
            return new Intent(Phase.ESCORT_COVER, mission,
                    escortStation == null ? destination : escortStation,
                    true, "ESCORT_STATION");

        return new Intent(Phase.TRANSIT, mission, destination, true, "NORMAL_MISSION");
    }

    private static boolean strike(TacticalAirAI.Mission mission) {
        return mission == TacticalAirAI.Mission.LEVEL_BOMB
                || mission == TacticalAirAI.Mission.DIVE_BOMB
                || mission == TacticalAirAI.Mission.STRAFE
                || mission == TacticalAirAI.Mission.TORPEDO;
    }

    private static boolean valid(Vec3 v) {
        return v != null && Double.isFinite(v.x) && Double.isFinite(v.y)
                && Double.isFinite(v.z);
    }

    /** Source-only regression: no assumptions about actual IA speed/weapon API. */
    public static void main(String[] args) {
        Vec3 origin = new Vec3(0, 130, 0), home = new Vec3(-180, 130, -180);
        Vec3 target = new Vec3(110, 125, 200), station = new Vec3(35, 140, 55);
        var ingress = select(TacticalAirAI.Mission.STRAFE, Phase.TRANSIT,
                origin, target, home, null, false, 1, 1);
        check(ingress.phase == Phase.STRIKE_INGRESS && ingress.mayUseObservedHostile,
                "must start on attack approach");
        var egress = select(TacticalAirAI.Mission.STRAFE, ingress.phase,
                target.add(0, 0, -12), target, home, null, false, 1, 1);
        check(egress.phase == Phase.STRIKE_EGRESS && egress.waypoint.equals(home)
                && !egress.mayUseObservedHostile
                && egress.guidanceMission == TacticalAirAI.Mission.PATROL,
                "completed approach must leave and stop attack pursuit");
        check(select(TacticalAirAI.Mission.STRAFE, egress.phase,
                origin, target, home, null, false, 1, 1).phase == Phase.STRIKE_EGRESS,
                "egress must not oscillate into attack during same run");
        var escort = select(TacticalAirAI.Mission.ESCORT, Phase.TRANSIT,
                origin, target, home, station, false, 1, 1);
        check(escort.phase == Phase.ESCORT_COVER && escort.waypoint.equals(station),
                "escort maintains assigned moving station");
        var rtb = select(TacticalAirAI.Mission.ESCORT, escort.phase,
                origin, target, home, station, true, 1, 1);
        check(rtb.phase == Phase.RETURNING && rtb.waypoint.equals(home)
                && !rtb.mayUseObservedHostile, "operator RTB overrides escort");
        check(select(TacticalAirAI.Mission.ESCORT, rtb.phase,
                origin, target, home, station, false, 1, 1).phase == Phase.RETURNING,
                "RTB stays latched");
        check(select(TacticalAirAI.Mission.INTERCEPT, Phase.TRANSIT,
                origin, target, home, null, false, .1, 1).phase == Phase.RETURNING,
                "low fuel must override intercept");
        check(select(TacticalAirAI.Mission.TORPEDO, Phase.TRANSIT,
                origin, target, home, null, false, 1, .2).phase == Phase.RETURNING,
                "damage must override strike");
        System.out.println("LiveMissionPlanner source contract PASS: escort, strike approach/egress, RTB latch");
    }

    private static void check(boolean yes, String error) {
        if (!yes) throw new AssertionError(error);
    }
}
