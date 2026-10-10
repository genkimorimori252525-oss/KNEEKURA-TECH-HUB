package org.kneekura.techhub.warfarewings.physics;

import java.nio.file.Path;
import java.util.List;
import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;
import static org.kneekura.techhub.warfarewings.physics.TacticalAirAI.*;

/**
 * Dynamic controllability baseline for every source-Atlas airframe.
 * Measures yaw-heading acquisition, input bounds and finite 20 Hz integration
 * under the actual microkernel's delayed raw-input path.
 */
public final class FlightGuidanceAtlasSelfTest {
    private static int checks;
    private static void check(boolean value, String reason) {
        checks++;
        if (!value) throw new AssertionError(reason);
    }
    public static void main(String[] args) throws Exception {
        if (args.length != 1) throw new IllegalArgumentException("anchor CSV needed");
        List<AircraftAtlasMain.Entry> types = AircraftAtlasMain.load(Path.of(args[0]));
        check(types.size() == 24, "entire aircraft roster");
        World flat = new FlatWorld(0);
        Vec3 objective = new Vec3(1200, 250, 0);
        for (AircraftAtlasMain.Entry entry : types) {
            Model model = entry.model();
            Profile profile = Profile.fromAtlas(AircraftAtlasMain.evaluate(entry));
            State state = State.airborne(new Vec3(0,250,0),new Vec3(0,0,0.7));
            double initial = Math.abs(FlightGuidance.wrapDeg(-90 - state.yawDeg()));
            double lowest = initial;
            double yawChange = 0;
            for (int i=0;i<200;i++) {
                Frame frame = new Frame(profile, model, state, Mission.PATROL,
                        objective, new Vec3(0,250,-100), null, null, null,
                        1, 1, 0, false, 0);
                var command = FlightGuidance.plan(frame, objective, 1.0);
                check(Double.isFinite(command.control().x())
                        && Double.isFinite(command.control().z())
                        && Double.isFinite(command.control().engineTarget()),
                        entry.baseId() + " finite autopilot commands");
                check(Math.abs(command.control().x()) <= 1
                        && Math.abs(command.control().z()) <= 1,
                        entry.baseId() + " bounded pilot inputs");
                State next = Ia133Microkernel.tick(model, state, command.control(), flat);
                check(Double.isFinite(next.position().x())
                        && Double.isFinite(next.position().y())
                        && Double.isFinite(next.position().z())
                        && Double.isFinite(next.yawDeg()),
                        entry.baseId() + " finite aircraft state");
                yawChange = Math.max(yawChange, Math.abs(next.yawDeg() - state.yawDeg()));
                lowest = Math.min(lowest, Math.abs(FlightGuidance.wrapDeg(-90 - next.yawDeg())));
                state = next;
            }
            check(lowest < initial * 0.55,
                    entry.baseId() + " did not acquire requested heading: bestError=" + lowest);
            check(yawChange > 0.01, entry.baseId() + " no actual yaw from pilot");
            check(state.position().x() > 15, entry.baseId() + " missed eastbound displacement");
        }
        System.out.println("FlightGuidanceAtlasSelfTest passed: " + checks
                + " checks / 24 aircraft / 4800 actual microkernel control ticks");
    }
}
