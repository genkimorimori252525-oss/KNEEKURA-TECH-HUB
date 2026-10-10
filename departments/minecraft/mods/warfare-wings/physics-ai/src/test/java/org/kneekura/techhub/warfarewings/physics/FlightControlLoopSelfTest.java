package org.kneekura.techhub.warfarewings.physics;

import java.util.List;
import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;
import static org.kneekura.techhub.warfarewings.physics.TacticalAirAI.*;
import static org.kneekura.techhub.warfarewings.physics.FlightSafetyPlanner.*;

public final class FlightControlLoopSelfTest {
    private static int checks;
    private static final Model MODEL = WarfareWingsAircraft.p47n();
    private static final Profile PROFILE = new Profile(MODEL.id(), MODEL.role(),
            "usaaf", MODEL.doctrine(), 45.79, 22.52, 60, 0.964626);
    private static void require(boolean condition, String why) {
        checks++;
        if (!condition) throw new AssertionError(why);
    }
    private static Frame frame(State self) {
        return new Frame(PROFILE, MODEL, self, Mission.INTERCEPT,
                new Vec3(200, 130, 350), new Vec3(-200,130,-100),
                null, null, null, 1, 1, 0, false, 0);
    }
    private static State state(double altitude, double velocityY, double velocityZ) {
        return State.airborne(new Vec3(0,altitude,0), new Vec3(0,velocityY,velocityZ));
    }
    private static void commandSafe(FlightControlLoop.Output output) {
        Control c = output.decision().controls();
        require(Math.abs(c.x()) <= 1 && Math.abs(c.z()) <= 1, "bounded flight stick");
        require(c.engineTarget() >= 0 && c.engineTarget() <= 1, "bounded throttle");
    }
    public static void main(String[] args) {
        Environment clear = new Environment((x,z) -> 0, List.of(), 3.0);
        Frame ordinary = frame(state(150,0,1.0));
        FlightControlLoop.Output baseline = FlightControlLoop.step(
                new FlightControlLoop.Input(ordinary, Memory.INITIAL, null, clear));
        require(!baseline.safety().override(), "clear air should not override task");
        require(baseline.decision().maneuver() == Maneuver.PATROL_ROUTE,
                "normal tactical decision still selected");
        commandSafe(baseline);

        Environment hill = new Environment((x,z) -> z >= 12 ? 146 : 0,
                List.of(), 4.0);
        FlightControlLoop.Output terrain = FlightControlLoop.step(
                new FlightControlLoop.Input(ordinary, Memory.INITIAL, null, hill));
        require(terrain.safety().reason() == Reason.TERRAIN_AHEAD,
                "hill along velocity path must trigger anticipation");
        require(terrain.decision().maneuver() == Maneuver.TERRAIN_RECOVERY,
                "terrain overrides patrol mission");
        require(terrain.decision().steeringPoint().y() > ordinary.self().position().y(),
                "lookahead recovers with positive altitude target");
        require(!terrain.decision().firingWindowCandidate(), "safety blocks fire");
        commandSafe(terrain);

        Environment converging = new Environment((x,z) -> 0,
                List.of(new MovingObstacle("friendly-wingman",
                    new Vec3(0,150,28), new Vec3(0,0,-0.5), 4.0)), 3.0);
        FlightControlLoop.Output avoid = FlightControlLoop.step(
                new FlightControlLoop.Input(ordinary, Memory.INITIAL, null, converging));
        require(avoid.safety().reason() == Reason.MOVING_COLLISION_RISK,
                "predict conflicting future occupied location");
        require(avoid.decision().maneuver() == Maneuver.COLLISION_AVOID,
                "collision guard owns command");
        require("friendly-wingman".equals(avoid.safety().obstacleId()),
                "diagnostic obstacle identity");
        commandSafe(avoid);

        Environment separating = new Environment((x,z) -> 0,
                List.of(new MovingObstacle("departing-wingman",
                    new Vec3(0,150,-30), new Vec3(0,0,-1.0), 4.0)), 3.0);
        require(!FlightControlLoop.step(
                new FlightControlLoop.Input(ordinary, Memory.INITIAL,null,separating))
                .safety().override(), "separating follower must not trigger false collision");

        Frame lowSpeed = frame(state(60,0,0.15));
        FlightControlLoop.Output recovery = FlightControlLoop.step(
                new FlightControlLoop.Input(lowSpeed,Memory.INITIAL,null,clear));
        require(recovery.safety().reason() == Reason.LOW_SPEED_RESERVE,
                "below source speed fraction engages margin (not a claimed stall speed)");
        require(recovery.decision().controls().engineTarget() == 1,
                "speed recovery requests full throttle");
        Frame nearGround = frame(state(9,-0.1,0.15));
        require(FlightControlLoop.step(
                new FlightControlLoop.Input(nearGround, Memory.INITIAL,null,clear))
                .safety().reason() == Reason.TERRAIN_AHEAD,
                "terrain danger outranks speed reserve");

        boolean rejected = false;
        try {
            FlightControlLoop.step(new FlightControlLoop.Input(ordinary,
                    Memory.INITIAL,null,new Environment((x,z) -> Double.NaN,List.of(),3.0)));
        } catch (IllegalArgumentException expected) { rejected = true; }
        require(rejected, "unresolved terrain must fail closed");

        // Same-frame deterministic output even with a procedural terrain sampler.
        for (int i=0;i<24;i++) {
            State sample = state(80 + i, -0.01 * i,0.45 + 0.03*i);
            Frame snapshot = frame(sample);
            Environment terrainMap = new Environment((x,z) ->
                    z > 15 && z < 45 ? 22 + 0.5 * x : 0, List.of(), 3.0);
            var a = FlightControlLoop.step(new FlightControlLoop.Input(
                    snapshot, Memory.INITIAL, null, terrainMap));
            var b = FlightControlLoop.step(new FlightControlLoop.Input(
                    snapshot, Memory.INITIAL, null, terrainMap));
            require(a.equals(b), "deterministic complete source control loop");
        }
        System.out.println("FlightControlLoopSelfTest passed: " + checks + " checks");
    }
}
