package org.kneekura.techhub.warfarewings.physics;

import java.io.BufferedWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;

/**
 * An explicitly separate 24-airframe-capable response-time-calibrated SOURCE
 * trace, using exact WW bytecode values. Same 400 tick / 0.7 bpt warm-start
 * envelope as the legacy A6M throttle source, no game JAR bundled or loaded.
 * Physical parity still requires real Minecraft GameTest comparison.
 */
public final class ReactionCalibrationTraceMain {
    private ReactionCalibrationTraceMain() {}

    public static void main(String[] args) throws Exception {
        if (args.length != 3)
            throw new IllegalArgumentException("Usage: ReactionCalibrationTraceMain ANCHOR_CSV AIRCRAFT_ID OUTPUT_CSV");
        Path out = Path.of(args[2]);
        var entry = AircraftAtlasMain.load(Path.of(args[0])).stream()
                .filter(e -> e.aircraftId().equals(args[1])).findFirst()
                .orElseThrow(() -> new IllegalArgumentException("Aircraft outside exact 24-type Atlas"));
        Model model = entry.model();
        int reactionTicks = WarfareWingsEngineReaction.ticks(model.id());
        State state = new State(0, new Vec3(0, 200, 0), new Vec3(0,0,0.7),
                0,0,0, 0,0,0, 0,0,0, 1,0,1, 0,false,false);
        Control control = Control.neutral(1);
        World flat = new FlatWorld(0);
        String id = entry.baseId() + "-throttle-step-v1";
        Files.createDirectories(out.toAbsolutePath().getParent());
        try (BufferedWriter writer = Files.newBufferedWriter(out, StandardCharsets.UTF_8)) {
            writer.write(TraceCsv.HEADER);
            writer.newLine();
            for (int tick=0;tick<=400;tick++) {
                var s=state;
                writer.write(TraceCsv.row(new TraceCsv.Frame(
                        "microkernel", id, model.id(), s.tick(), null,
                        s.position().x(), s.position().y(), s.position().z(),
                        s.velocity().x(), s.velocity().y(), s.velocity().z(),
                        s.yawDeg(), s.pitchDeg(), s.rollDeg(), s.engineTarget(),
                        s.enginePowerSmooth() * Math.sqrt(s.fuelUtilization()), s.fuelUtilization(),
                        s.rawX(), s.rawY(), s.rawZ(), s.smoothX(), s.smoothY(), s.smoothZ())));
                writer.newLine();
                if (tick < 400) state = tickWithReaction(model, state, control, flat, reactionTicks);
            }
        }
        System.out.println("Exact-WW reaction SOURCE trace: " + model.id()
                + " reactionTicks=" + reactionTicks + " samples=401");
    }
}
