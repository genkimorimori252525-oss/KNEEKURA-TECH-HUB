package org.kneekura.techhub.warfarewings.physics;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Locale;

import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;
import static org.kneekura.techhub.warfarewings.physics.WarfareWingsAircraft.LegacyMeasuredProfile;

public final class PerformanceReportMain {
    private static final World FLAT = new FlatWorld(0.0);
    private PerformanceReportMain() {}

    public record Result(String aircraftId, String doctrine,
                         double sourcePredictedTopSpeedBps,
                         double yawChange20TicksDeg,
                         double yawStepInitialSpeedBps,
                         double yawStepExitSpeedBps,
                         double yawStepEnergyRetention,
                         double pitchChange20TicksDeg,
                         double engineSpeed, double yawSpeed, double pitchSpeed, double lift,
                         double runtimeFriction, double rawDriftDrag, double durability,
                         double legacyMeasuredTopSpeedBps, String legacyProvenance) {}

    public static Result evaluate(Model model, LegacyMeasuredProfile legacy) {
        State straight = warmStraight(model, 800);
        double top = straight.velocity().horizontalLength() * TICKS_PER_SECOND;

        State yawStart = warmStraight(model, 600);
        double yawInitial = yawStart.velocity().length() * TICKS_PER_SECOND;
        State yawEnd = run(yawStart, model, new Control(1, 0, 0, 1), 20);
        double yawChange = Math.abs(yawEnd.yawDeg() - yawStart.yawDeg());
        double yawExit = yawEnd.velocity().length() * TICKS_PER_SECOND;

        State pitchStart = warmStraight(model, 600);
        State pitchEnd = run(pitchStart, model, new Control(0, 0, 1, 1), 20);

        return new Result(model.id(), model.doctrine(), top, yawChange, yawInitial, yawExit,
                yawExit / yawInitial, Math.abs(pitchEnd.pitchDeg() - pitchStart.pitchDeg()),
                model.engineSpeed(), model.yawSpeed(), model.pitchSpeed(), model.lift(),
                model.friction(), model.rawDriftDrag(), model.durability(),
                legacy.measuredTopSpeedBps(), legacy.provenance());
    }

    static State warmStraight(Model model, int ticks) {
        State state = State.airborne(new Vec3(0, 1000, 0), new Vec3(0, 0, 0.70));
        return run(state, model, Control.neutral(1.0), ticks);
    }

    static State run(State state, Model model, Control control, int ticks) {
        State current = state;
        for (int i = 0; i < ticks; i++) current = Ia133Microkernel.tick(model, current, control, FLAT);
        return current;
    }

    public static void main(String[] args) throws IOException {
        if (args.length != 1) throw new IllegalArgumentException("Usage: PerformanceReportMain OUTPUT_DIR");
        Path output = Path.of(args[0]);
        Files.createDirectories(output);
        List<Result> results = List.of(
                evaluate(WarfareWingsAircraft.a6m(), WarfareWingsAircraft.legacyA6m()),
                evaluate(WarfareWingsAircraft.p47n(), WarfareWingsAircraft.legacyP47n()));
        Files.writeString(output.resolve("a6m-p47n-source-microkernel.csv"), csv(results), StandardCharsets.UTF_8);
        Files.writeString(output.resolve("a6m-p47n-source-microkernel.md"), markdown(results), StandardCharsets.UTF_8);
        System.out.println("Wrote A6M/P-47N source-microkernel reports to " + output);
    }

    static String csv(List<Result> results) {
        StringBuilder out = new StringBuilder();
        out.append("aircraft,doctrine,source_predicted_top_speed_bps,yaw_change_20t_deg,yaw_step_initial_speed_bps,yaw_step_exit_speed_bps,yaw_step_energy_retention,pitch_change_20t_deg,engine_speed,yaw_speed,pitch_speed,lift,runtime_friction,raw_drift_drag,durability,legacy_measured_top_speed_bps,legacy_scope\n");
        for (Result r : results) {
            out.append(String.join(",", r.aircraftId(), r.doctrine(), f(r.sourcePredictedTopSpeedBps()),
                    f(r.yawChange20TicksDeg()), f(r.yawStepInitialSpeedBps()), f(r.yawStepExitSpeedBps()),
                    f(r.yawStepEnergyRetention()), f(r.pitchChange20TicksDeg()), f(r.engineSpeed()),
                    f(r.yawSpeed()), f(r.pitchSpeed()), f(r.lift()), f(r.runtimeFriction()),
                    f(r.rawDriftDrag()), f(r.durability()), f(r.legacyMeasuredTopSpeedBps()),
                    quote(r.legacyProvenance()))).append('\n');
        }
        return out.toString();
    }

    static String markdown(List<Result> results) {
        Result a6m = results.get(0), p47 = results.get(1);
        StringBuilder out = new StringBuilder();
        out.append("# A6M vs P-47N — IA 1.3.3 Microkernel Report\n\n");
        out.append("> Status: **SOURCE-MICROKERNEL ONLY / REAL-RUNTIME PARITY NOT YET RUN.**  \n");
        out.append("> Warfare Wings model values come from supplied ANCHOR SHA-256 `")
                .append(WarfareWingsAircraft.WARFARE_WINGS_ANCHOR_SHA256).append("`.  \n");
        out.append("> Legacy measured values are historical references from a differently identified Warfare Wings runtime artifact.\n\n");
        out.append("| Aircraft | Source-predicted top speed | Yaw change (20t) | Pitch change (20t) | Turn exit retention | Durability |\n");
        out.append("|---|---:|---:|---:|---:|---:|\n");
        for (Result r : results) {
            out.append(String.format(Locale.ROOT, "| %s | %.2f b/s | %.2f deg | %.2f deg | %.3f | %.1f |%n",
                    r.aircraftId(), r.sourcePredictedTopSpeedBps(), r.yawChange20TicksDeg(),
                    r.pitchChange20TicksDeg(), r.yawStepEnergyRetention(), r.durability()));
        }
        out.append("\n## Explainable differences\n\n");
        out.append(String.format(Locale.ROOT,
                "- **Speed tendency — SOURCE_DIRECT:** P-47N uses `engineSpeed=%.3f` vs A6M `%.3f`. IA 1.3.3 thrust is `enginePower^2 * engineSpeed`; this source microkernel predicts %.2f b/s vs %.2f b/s in the flat/wind-off envelope.\n",
                p47.engineSpeed(), a6m.engineSpeed(), p47.sourcePredictedTopSpeedBps(), a6m.sourcePredictedTopSpeedBps()));
        out.append(String.format(Locale.ROOT,
                "- **Nose authority — SOURCE_DIRECT:** A6M uses `yawSpeed=%.1f` / `pitchSpeed=%.1f`; P-47N uses `%.1f` / `%.1f`. The identical 20-tick yaw trace yields %.2f vs %.2f degrees.\n",
                a6m.yawSpeed(), a6m.pitchSpeed(), p47.yawSpeed(), p47.pitchSpeed(), a6m.yawChange20TicksDeg(), p47.yawChange20TicksDeg()));
        out.append(String.format(Locale.ROOT,
                "- **Survivability input — SOURCE_DIRECT:** P-47N durability %.1f is twice A6M %.1f; IA divides normalized vehicle damage by durability before health reduction.\n",
                p47.durability(), a6m.durability()));
        out.append("- **Mass caution:** no turn-inertia claim is made from `mass`; the inspected 1.3.3 source does not use mass as ordinary yaw/pitch inertia.\n");
        out.append(String.format(Locale.ROOT,
                "- **driftDrag caution:** raw values differ (A6M %.3f, P-47N %.3f), but the pinned source loader registers runtime `friction`; both seed models therefore use default %.3f.\n",
                a6m.rawDriftDrag(), p47.rawDriftDrag(), a6m.runtimeFriction()));
        out.append("\n## Legacy reference — NOT a parity verdict\n\n");
        for (Result r : results) {
            out.append(String.format(Locale.ROOT, "- %s legacy measured top speed: %.2f b/s — %s%n",
                    r.aircraftId(), r.legacyMeasuredTopSpeedBps(), r.legacyProvenance()));
        }
        out.append("\nThe A6M source prediction differs strongly from the legacy measurement. That mismatch is preserved as evidence, not tuned away: the old profile came from a differently identified Warfare Wings artifact, and IA source-tag ↔ distributed-binary equivalence is still not proven. The next gate is same-artifact Minecraft trace replay.\n");
        return out.toString();
    }

    private static String f(double v) { return String.format(Locale.ROOT, "%.9f", v); }
    private static String quote(String v) { return '"' + v.replace("\"", "\"\"") + '"'; }
}
