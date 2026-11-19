package org.kneekura.techhub.warfarewings.physics;

import java.io.BufferedWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;

public final class TraceScenarioMain {
    public static final String SCENARIO_ID = "a6m-throttle-step-v1";
    public static final int TICKS = 400;

    private TraceScenarioMain() {}

    public static void main(String[] args) throws Exception {
        if (args.length != 1) throw new IllegalArgumentException("Usage: TraceScenarioMain OUTPUT_CSV");
        Path out = Path.of(args[0]);
        Files.createDirectories(out.toAbsolutePath().getParent());

        Model model = WarfareWingsAircraft.a6m();
        State state = new State(
                0, new Vec3(0,200,0), new Vec3(0,0,0.7),
                0,0,0, 0,0,0, 0,0,0,
                1,0,1, 0,false,false);
        Control control = Control.neutral(1.0);
        World world = new FlatWorld(0.0);

        try (BufferedWriter w = Files.newBufferedWriter(out, StandardCharsets.UTF_8)) {
            w.write(TraceCsv.HEADER); w.newLine();
            write(w, state);
            for (int i=0;i<TICKS;i++) {
                state = Ia133Microkernel.tick(model, state, control, world);
                write(w, state);
            }
        }
        System.out.println("Wrote " + (TICKS+1) + " trace rows to " + out);
    }

    private static void write(BufferedWriter w, State s) throws Exception {
        w.write(TraceCsv.row(new TraceCsv.Frame(
                "microkernel", SCENARIO_ID, WarfareWingsAircraft.a6m().id(), s.tick(), null,
                s.position().x(), s.position().y(), s.position().z(),
                s.velocity().x(), s.velocity().y(), s.velocity().z(),
                s.yawDeg(), s.pitchDeg(), s.rollDeg(),
                s.engineTarget(), s.enginePowerSmooth() * Math.sqrt(s.fuelUtilization()),
                s.fuelUtilization(), s.rawX(), s.rawY(), s.rawZ(),
                s.smoothX(), s.smoothY(), s.smoothZ())));
        w.newLine();
    }
}
