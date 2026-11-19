package org.kneekura.techhub.warfarewings.physics;

import java.util.ArrayList;
import java.util.List;

import org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.Vec3;
import org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.State;
import org.kneekura.techhub.warfarewings.physics.TacticalAirAI.Frame;
import org.kneekura.techhub.warfarewings.physics.TacticalAirAI.Mission;
import org.kneekura.techhub.warfarewings.physics.TacticalAirAI.Profile;

/** Only SOURCE geometry/waypoint contracts; no actual Forge physics or LOS. */
public final class FlightSafetyPlannerSourceSelfTest {
    private static int checks;

    private FlightSafetyPlannerSourceSelfTest() {}

    private static Frame frame(Vec3 position, Vec3 velocity, double fuel) {
        var model = WarfareWingsAircraft.p47n();
        var profile = new Profile(model.id(), model.role(), "usaaf", model.doctrine(),
                45.79, 22.52, 60, 0.964626);
        return new Frame(profile, model, State.airborne(position, velocity), Mission.INTERCEPT,
                position.add(0, 0, 200), position, null, null, null,
                fuel, 1.0, 0, false, 0);
    }

    private static FlightSafetyPlanner.Clearance plan(Frame frame, Vec3 obstaclePosition,
                                                       Vec3 obstacleVelocity, boolean hostile,
                                                       double terrain) {
        return plan(frame, obstaclePosition, obstacleVelocity, hostile, terrain, true);
    }

    private static FlightSafetyPlanner.Clearance plan(Frame frame, Vec3 obstaclePosition,
                                                       Vec3 obstacleVelocity, boolean hostile,
                                                       double terrain, boolean largeFormation) {
        List<FlightSafetyPlanner.MovingObstacle> obstacles = new ArrayList<>();
        obstacles.add(new FlightSafetyPlanner.MovingObstacle("observed",
                obstaclePosition, obstacleVelocity, 6.0, hostile));
        if (largeFormation) {
            // Four actual radio-observed distant wingmates model a large flight.
            // They are never promoted to unseen enemy contacts.
            for (int i = 0; i < 4; i++)
                obstacles.add(new FlightSafetyPlanner.MovingObstacle("wing-" + i,
                        frame.self().position().add(250 + 40 * i, 0, 0),
                        frame.self().velocity(), 6.0, false));
        }
        return FlightSafetyPlanner.guard(frame, frame.objective(),
                new FlightSafetyPlanner.Environment((x, z) -> terrain,
                        obstacles, 6.0));
    }

    private static void require(boolean result, String context) {
        if (!result) throw new AssertionError(context);
        checks++;
    }

    public static void main(String[] ignored) {
        var selfAbove = frame(new Vec3(0, 160, 0), new Vec3(0, 0, 1), 1.0);
        var above = plan(selfAbove, new Vec3(0, 155, 24),
                new Vec3(0, 0, -1), true, 0);
        require(above.override(), "visible closing contact must override");
        require(above.reason() == FlightSafetyPlanner.Reason.MOVING_COLLISION_RISK,
                "visible collision reason retained");
        require("observed".equals(above.obstacleId()), "obstacle identity retained");
        require(above.waypoint().y() == 220, "higher aircraft climbs 60b target");
        require(plan(selfAbove, new Vec3(0, 155, 24),
                new Vec3(0, 0, -1), true, 0, false).waypoint().y() == 163,
                "small source patrol retains earlier +3b hostile height target");

        var selfBelow = frame(new Vec3(0, 160, 0), new Vec3(0, 0, 1), 1.0);
        var below = plan(selfBelow, new Vec3(0, 165, 24),
                new Vec3(0, 0, -1), true, 0);
        require(below.waypoint().y() == 100, "lower aircraft descends 60b when high above ground");
        var terrainLimited = plan(selfBelow, new Vec3(0, 165, 24),
                new Vec3(0, 0, -1), true, 108);
        require(terrainLimited.reason() == FlightSafetyPlanner.Reason.MOVING_COLLISION_RISK,
                "terrain-constrained descending contact still actively avoided");
        require(terrainLimited.waypoint().y() < 160 && terrainLimited.waypoint().y() > 108 + 18,
                "descent limit respects source terrain reserve");

        var equalLeft = plan(selfAbove, new Vec3(2, 160, 24),
                new Vec3(0, 0, -1), true, 0);
        var equalRight = plan(frame(new Vec3(2, 160, 0), new Vec3(0, 0, 1), 1.0),
                new Vec3(0, 160, 24), new Vec3(0, 0, -1), true, 0);
        require(equalLeft.waypoint().y() == 100 && equalRight.waypoint().y() == 220,
                "equal-height opposite relative X gets reciprocal vertical waypoints");

        var friendly = plan(selfAbove, new Vec3(0, 155, 24),
                new Vec3(0, 0, -1), false, 0);
        require(friendly.waypoint().y() == 205, "imminent team crossing adds 45b vertical escape");
        require(plan(selfAbove, new Vec3(0, 155, 24),
                new Vec3(0, 0, -1), false, 0, false).waypoint().y() == 184,
                "small formation keeps original 24b friend clearance");
        var distantFriendly = plan(selfAbove, new Vec3(0, 155, 48),
                new Vec3(0, 0, -1), false, 0);
        require(distantFriendly.waypoint().y() == 184,
                "ordinary more-distant friendly keeps original 24b climb behavior");
        var receding = plan(selfAbove, new Vec3(0, 160, -80),
                new Vec3(0, 0, -1), true, 0);
        require(!receding.override(), "separating hostile does not trigger collision guard");
        var retreat = plan(frame(selfAbove.self().position(), selfAbove.self().velocity(), .05),
                new Vec3(0, 155, 24), new Vec3(0, 0, -1), true, 0);
        require(!retreat.override(), "low fuel conservative withdrawal rule remains");
        var clear = FlightSafetyPlanner.guard(selfAbove, selfAbove.objective(),
                new FlightSafetyPlanner.Environment((x, z) -> 0, List.of(), 6.0));
        require(!clear.override(), "no visible obstacle cannot synthesize one");
        System.out.println("FlightSafetyPlannerSourceSelfTest SOURCE PASS checks=" + checks
                + "; collision outcomes/Forge NOT_RUN");
    }
}
