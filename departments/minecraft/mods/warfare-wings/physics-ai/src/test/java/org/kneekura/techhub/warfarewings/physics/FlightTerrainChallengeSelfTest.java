package org.kneekura.techhub.warfarewings.physics;

import java.nio.file.Path;
import java.util.List;
import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;
import static org.kneekura.techhub.warfarewings.physics.TacticalAirAI.*;

/**
 * Dynamic ridge challenge for all 24 airframes. Synthetic heightfield only:
 * a regression test that pilot inputs feed physical position and do not fly
 * through this particular simulated terrain when hazards are in sensor range.
 */
public final class FlightTerrainChallengeSelfTest {
    private static int checks;
    private static void check(boolean ok, String detail) {
        checks++;
        if (!ok) throw new AssertionError(detail);
    }

    public static void main(String[] args) throws Exception {
        var roster = AircraftAtlasMain.load(Path.of(args[0]));
        check(roster.size() == 24, "all aircraft covered");
        FlightSafetyPlanner.Terrain terrain =
                (x,z) -> z >= 35 && z <= 200 ? 60.0 : 0.0;
        World simulatedWorld = (x,z) -> terrain.topY(x,z);
        FlightSafetyPlanner.Environment environment =
                new FlightSafetyPlanner.Environment(terrain,List.of(),4.0);
        for (AircraftAtlasMain.Entry type : roster) {
            Profile profile = Profile.fromAtlas(AircraftAtlasMain.evaluate(type));
            Model model = type.model();
            State aircraft = State.airborne(new Vec3(0,72,0), new Vec3(0,0,0.7));
            Memory memory = Memory.INITIAL;
            int warningTicks = 0;
            int actualMotionTicks = 0;
            double maximumZ = aircraft.position().z();
            for (int tick=0;tick<180;tick++) {
                double ground = terrain.topY(aircraft.position().x(),aircraft.position().z());
                Frame frame = new Frame(profile,model,aircraft,Mission.PATROL,
                        new Vec3(0,105,250),new Vec3(0,110,-120),
                        null,null,null,1,1,ground,false,0);
                var output = FlightControlLoop.step(
                        new FlightControlLoop.Input(frame,memory,null,environment));
                if (output.safety().override()) warningTicks++;
                State next = Ia133Microkernel.tick(model,aircraft,output.decision().controls(),
                        simulatedWorld);
                if (next.position().add(aircraft.position().scale(-1)).length() > 0.001)
                    actualMotionTicks++;
                // In this heightfield model Entity.move is intentionally simplified;
                // ground contact is still a definitive failed clearance on this test.
                check(!next.onGround(), type.baseId() + " touched ridge at tick " + tick);
                check(Double.isFinite(next.position().x()) && Double.isFinite(next.position().y())
                        && Double.isFinite(next.position().z()),"finite three-dimensional flight");
                maximumZ = Math.max(maximumZ,next.position().z());
                aircraft = next;
                memory = output.decision().nextMemory();
            }
            check(warningTicks > 0, type.baseId()+" did not see heightfield hazard");
            check(actualMotionTicks > 100, type.baseId()+" guidance did not move aircraft");
            check(maximumZ > 20,type.baseId()+" did not make forward mission progress");
        }
        System.out.println("FlightTerrainChallengeSelfTest passed: " + checks
                + " checks / 24 aircraft / 4320 terrain-aware flight ticks");
    }
}
