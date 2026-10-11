package org.kneekura.techhub.warfarewings.physics;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;

/**
 * Exact pinned-owner Forge TRACE -> deterministic source physics discrepancy
 * microscope. Runs independent, one-step teacher-forced and 400-tick free-run
 * predictions from the SAME real recorded aircraft state and raw controls.
 *
 * This source-only tool DOES NOT prove runtime parity, identify an unseen
 * collision, reconstruct Minecraft Entity.move, or train/fix parameters.
 * It measures which observable component diverges and at which tick. Source
 * state assumptions (previousY, onGround=false, zero world wind/height) are
 * explicit and deliberately separate from original runtime evidence.
 */
public final class RealPhysicsTwinReplayMain {
    public static final String OWNER_SHA256 =
            "dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43";
    public static final String HEADER = "scenario_id,aircraft_id,tick,game_time," +
            "real_pos_x,real_pos_y,real_pos_z,real_vel_x,real_vel_y,real_vel_z," +
            "one_step_pos_error_blocks,one_step_delta_pos_x,one_step_delta_pos_y,one_step_delta_pos_z," +
            "one_step_vel_error_bpt,one_step_delta_vel_x,one_step_delta_vel_y,one_step_delta_vel_z," +
            "one_step_speed_error_bps,one_step_yaw_error_deg,one_step_pitch_error_deg," +
            "one_step_roll_error_deg,one_step_engine_power_error,one_step_smooth_x_error," +
            "one_step_smooth_z_error,free_run_pos_error_blocks,free_run_vel_error_bpt," +
            "free_run_speed_error_bps,free_run_yaw_error_deg,free_run_pitch_error_deg," +
            "real_displacement_velocity_mismatch_bpt,real_yaw_deg,real_pitch_deg," +
            "one_step_predicted_yaw_deg,one_step_predicted_pitch_deg,trace_kind,assumptions";

    private RealPhysicsTwinReplayMain() {}

    record Observation(String scenario, String aircraft, long tick, long gameTime,
                       Vec3 position, Vec3 velocity, double yaw, double pitch,
                       double roll, double target, double power, double fuel,
                       double rawX, double rawY, double rawZ,
                       double smoothX, double smoothY, double smoothZ) {
        Observation {
            if (fuel <= 0 || fuel > 1 || target < 0 || target > 1)
                throw new IllegalArgumentException("Invalid real engine target/fuel state");
            double[] numbers = {position.x(), position.y(), position.z(), velocity.x(), velocity.y(), velocity.z(),
                    yaw, pitch, roll, target, power, fuel, rawX, rawY, rawZ, smoothX, smoothY, smoothZ};
            for (double number : numbers)
                if (!Double.isFinite(number)) throw new IllegalArgumentException("Non-finite real physics sample");
        }
    }

    /** Full provenance check BEFORE any output file is created. */
    static List<Observation> loadReal(Path runtime, String aircraftId) throws IOException {
        List<String> lines = Files.readAllLines(runtime, StandardCharsets.UTF_8);
        if (lines.size() < 5 || !TraceCsv.HEADER.equals(lines.get(0)))
            throw new IllegalArgumentException("Missing or modified exact real Forge trace CSV header");
        String baseId = aircraftId.replaceFirst("^warfare_wings:", "");
        String scenario = baseId + "-throttle-step-v1";
        List<Observation> observations = new ArrayList<>();
        for (int i = 1; i < lines.size(); i++) {
            String[] row = lines.get(i).split(",", -1);
            if (row.length != 26 || !TraceCsv.VERSION.equals(row[0])
                    || !"minecraft_runtime".equals(row[1])
                    || !scenario.equals(row[2]) || !aircraftId.equals(row[3]))
                throw new IllegalArgumentException("Trace identity/source/schema mismatch at CSV line " + (i + 1));
            long tick = Long.parseLong(row[4]);
            long clock = Long.parseLong(row[5]);
            if (tick != i - 1 || i > 1 && clock != observations.get(i-2).gameTime() + 1)
                throw new IllegalArgumentException("Missing or duplicated real Minecraft entity/game tick at " + tick);
            Observation o = new Observation(scenario, aircraftId, tick, clock,
                    new Vec3(num(row,6),num(row,7),num(row,8)),
                    new Vec3(num(row,9),num(row,10),num(row,11)),
                    num(row,14),num(row,15),num(row,16),num(row,17),num(row,18),num(row,19),
                    num(row,20),num(row,21),num(row,22),num(row,23),num(row,24),num(row,25));
            double speed = o.velocity().length() * TICKS_PER_SECOND;
            if (Math.abs(num(row,12) - speed) > 1e-6)
                throw new IllegalArgumentException("Real velocity/speed field mismatch at tick " + tick);
            observations.add(o);
        }
        // A frozen client rendering while the server clock advances must
        // NEVER be accepted as an operational observation.
        int frozen = 0;
        for (int i = 1; i < observations.size(); i++) {
            var a = observations.get(i-1); var b = observations.get(i);
            if (a.position().equals(b.position()) && a.velocity().equals(b.velocity())
                    && a.power() == b.power() && a.yaw() == b.yaw() && a.pitch() == b.pitch())
                frozen++;
            else frozen = 0;
            if (frozen >= 3)
                throw new IllegalArgumentException("NON_TICKING_REAL_AIRCRAFT repeated physics at " + i);
        }
        return List.copyOf(observations);
    }

    private static double num(String[] row, int column) {
        double n = Double.parseDouble(row[column]);
        if (!Double.isFinite(n)) throw new IllegalArgumentException("Non-finite Forge value at column " + column);
        return n;
    }

    private static Map<String, Model> models(Path anchor) throws IOException {
        List<String> lines = Files.readAllLines(anchor, StandardCharsets.UTF_8);
        if (lines.size() != 25) throw new IllegalArgumentException("Exact 24-plane source anchor missing");
        String[] fields = lines.get(0).split(",", -1);
        int shaIndex = -1;
        for (int j=0;j<fields.length;j++) if (fields[j].equals("anchor_sha256")) shaIndex=j;
        if (shaIndex<0) throw new IllegalArgumentException("Exact original hash column missing");
        for (int i=1;i<lines.size();i++) {
            String[] row = lines.get(i).split(",", -1);
            if (row.length != fields.length || !OWNER_SHA256.equals(row[shaIndex]))
                throw new IllegalArgumentException("Non-original/modified WW source anchor at line " + (i+1));
        }
        Map<String, Model> models = new HashMap<>();
        for (var entry : AircraftAtlasMain.load(anchor))
            if (models.put(entry.aircraftId(), entry.model()) != null)
                throw new IllegalArgumentException("Duplicated original airframe");
        if (models.size()!=24) throw new IllegalArgumentException("24-source roster incomplete");
        return models;
    }

    private static State state(Observation o, double previousY) {
        // enginePowerSmooth is observable only through IA's enginePower,
        // which includes a sqrt(fuel) factor. Do not silently assume full fuel.
        return new State(o.tick(), o.position(), o.velocity(), o.yaw(), o.pitch(), o.roll(),
                o.rawX(), o.rawY(), o.rawZ(), o.smoothX(), o.smoothY(), o.smoothZ(),
                o.target(), o.power()/Math.sqrt(o.fuel()), o.fuel(),
                previousY, false, false);
    }

    private static Control controls(Observation o) {
        return new Control(o.rawX(), o.rawY(), o.rawZ(), o.target());
    }

    /** Never use the real next tick to advance an open-loop source run. */
    public static void replay(Path anchor, String aircraftId, Path actualCsv, Path output) throws IOException {
        replaySamples(anchor, aircraftId, loadReal(actualCsv, aircraftId), output, true,
                "neutral_runtime", "AIRBORNE_FLAT_NO_WIND|ENGINE_POWER_OBSERVED|ROLL_OBSERVED");
    }

    public static void replayWithPinnedWind(Path anchor, String aircraftId,
                                            Path actualCsv, Path output) throws IOException {
        replaySamples(anchor, aircraftId, loadReal(actualCsv, aircraftId), output, true,
                "neutral_pinned_wind", "AIRBORNE_PINNED_IA_WIND|ENGINE_POWER_OBSERVED|ROLL_OBSERVED",
                PinnedIa133WindWorld.calmAirCalibration());
    }

    static void replaySamples(Path anchor, String aircraftId, List<Observation> real, Path output,
                              boolean rollObserved, String kind, String assumptions) throws IOException {
        replaySamples(anchor, aircraftId, real, output, rollObserved, kind, assumptions, new FlatWorld(0));
    }

    static void replaySamples(Path anchor, String aircraftId, List<Observation> real, Path output,
                              boolean rollObserved, String kind, String assumptions, World world) throws IOException {
        if (!kind.matches("[a-z_]+") || !assumptions.matches("[A-Z0-9_|]+"))
            throw new IllegalArgumentException("Invalid replay identity/assumption label");
        Model model = models(anchor).get(aircraftId);
        if (model == null) throw new IllegalArgumentException("Unrecognized original airframe " + aircraftId);
        if (real.size() < 4) throw new IllegalArgumentException("Actual recording too short to establish physics");
        int reaction = WarfareWingsEngineReaction.ticks(aircraftId);
        State openLoop = state(real.get(0), 0);
        StringBuilder body = new StringBuilder(HEADER).append('\n');
        for (int i=1;i<real.size();i++) {
            Observation previous = real.get(i-1), observed = real.get(i);
            double previousY = i == 1 ? 0 : real.get(i-2).position().y();
            // Real tactical server: at END tick t, the pilot applies throttle
            // t to the next physics step. During tick t+1 the already-smoothed
            // axes are consumed; END tick t+1 then injects command(t+1) into
            // the stored interpolation. For recorded-control REPLAY only,
            // t+1 command is known from the actual trace. This is not a
            // counterfactual/autonomous AI prediction, merely deterministic
            // physics under exactly the recorded, exogenous control history.
            Control issued = kind.startsWith("tactical_")
                    ? new Control(observed.rawX(),observed.rawY(),observed.rawZ(),previous.target())
                    : controls(previous);
            State oneStep = tickWithReaction(model, state(previous, previousY),
                    issued, world, reaction);
            openLoop = tickWithReaction(model, openLoop,
                    issued, world, reaction);
            Vec3 poseDelta = oneStep.position().add(observed.position().scale(-1));
            Vec3 velocityDelta = oneStep.velocity().add(observed.velocity().scale(-1));
            double movedVsVelocity = observed.position().add(previous.position().scale(-1))
                    .add(observed.velocity().scale(-1)).length();
            double[] values = {
                    observed.position().x(), observed.position().y(), observed.position().z(),
                    observed.velocity().x(), observed.velocity().y(), observed.velocity().z(),
                    poseDelta.length(), poseDelta.x(), poseDelta.y(), poseDelta.z(),
                    velocityDelta.length(), velocityDelta.x(), velocityDelta.y(), velocityDelta.z(),
                    (oneStep.velocity().length() - observed.velocity().length()) * TICKS_PER_SECOND,
                    angle(oneStep.yawDeg(), observed.yaw()), angle(oneStep.pitchDeg(), observed.pitch()),
                    rollObserved ? angle(oneStep.rollDeg(), observed.roll()) : Double.NaN,
                    oneStep.enginePowerSmooth()*Math.sqrt(oneStep.fuelUtilization()) - observed.power(),
                    oneStep.smoothX() - observed.smoothX(), oneStep.smoothZ() - observed.smoothZ(),
                    openLoop.position().add(observed.position().scale(-1)).length(),
                    openLoop.velocity().add(observed.velocity().scale(-1)).length(),
                    (openLoop.velocity().length() - observed.velocity().length()) * TICKS_PER_SECOND,
                    angle(openLoop.yawDeg(), observed.yaw()), angle(openLoop.pitchDeg(), observed.pitch()),
                    movedVsVelocity, observed.yaw(), observed.pitch(), oneStep.yawDeg(), oneStep.pitchDeg()
            };
            body.append(observed.scenario()).append(',').append(aircraftId).append(',')
                    .append(i).append(',').append(observed.gameTime());
            for (int index = 0; index < values.length; index++) {
                body.append(',');
                if (index == 17 && !rollObserved) continue;
                if (!Double.isFinite(values[index]))
                    throw new IllegalStateException("Non-finite one-step source replay at tick " + i);
                body.append(String.format(Locale.ROOT, "%.12f", values[index]));
            }
            body.append(',').append(kind).append(',').append(assumptions).append('\n');
        }
        Files.createDirectories(output.toAbsolutePath().getParent());
        Files.writeString(output, body.toString(), StandardCharsets.UTF_8);
        System.out.printf(Locale.ROOT,
                "REAL_FORGE_TEACHER_FORCED_REPLAY %s ticks=%d reaction=%d kind=%s output=%s (parity NOT ESTABLISHED)%n",
                aircraftId, real.size()-1, reaction, kind, output);
    }

    private static double angle(double a, double b) {
        return (a-b+180)%360 < 0 ? (a-b+180)%360+360-180 : (a-b+180)%360-180;
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 4 && (args.length != 5 || !"--pinned-wind".equals(args[4])))
            throw new IllegalArgumentException(
                    "Usage: RealPhysicsTwinReplayMain EXACT_ANCHOR_CSV AIRCRAFT_ID REAL_FORGE_CSV OUTPUT_STEP_CSV [--pinned-wind]");
        if (args.length == 5)
            replayWithPinnedWind(Path.of(args[0]), args[1], Path.of(args[2]), Path.of(args[3]));
        else replay(Path.of(args[0]), args[1], Path.of(args[2]), Path.of(args[3]));
    }
}
