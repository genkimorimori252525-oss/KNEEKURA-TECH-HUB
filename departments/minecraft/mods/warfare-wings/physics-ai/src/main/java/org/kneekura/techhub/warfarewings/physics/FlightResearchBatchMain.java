package org.kneekura.techhub.warfarewings.physics;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.SplittableRandom;

import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;
import static org.kneekura.techhub.warfarewings.physics.TacticalAirAI.*;

/**
 * Reproducible batch experiments on the ACTUAL pure-Java SOURCE microkernel.
 *
 * This is deliberately not a Minecraft/Forge parity runner. Each step invokes
 * Ia133Microkernel.tickWithReaction with the exact bytecode-backed 24-aircraft
 * engine-reaction override. World wind and the ridge are scripted experiments,
 * NOT a reconstruction of Forge's world/collision/wind callbacks.
 *
 * Outputs are independent of wall time, host locale, and filesystem separators.
 * Trial seeds depend on aircraft ID and per-aircraft trial number (not file order).
 */
public final class FlightResearchBatchMain {
    public static final String SCHEMA = "ww.flight-research-lab.v1";
    public static final String EVIDENCE = "SOURCE_MICROKERNEL_BYTECODE_REACTION__SYNTHETIC_WORLD__NO_FORGE_PARITY";
    private static final String SOURCE = "Ia133Microkernel.tickWithReaction";
    private static final PinnedIa133WindWorld PINNED_CALM_WIND =
            PinnedIa133WindWorld.calmAirCalibration();
    private static final int DEFAULT_TRIALS_PER_AIRCRAFT = 512;
    private static final int DEFAULT_TICKS = 180;
    private static final int DEFAULT_TRACE_STRIDE = 10;
    private static final long DEFAULT_SEED = 20261011L;

    private FlightResearchBatchMain() {}

    private enum Experiment {
        CRUISE,
        THROTTLE_STEP,
        TURN_LEFT,
        TURN_RIGHT,
        CLIMB,
        DIVE_RECOVERY,
        SCRIPTED_WIND,
        TERRAIN_RIDGE,
        AI_MISSION_ROUTE,
        AI_OBSERVED_CONTACT,
        AI_FORMATION;

        boolean usesAI() {
            return this == TERRAIN_RIDGE || name().startsWith("AI_");
        }
    }

    private record Arguments(Path input, Path output, long seed,
                             int trialsPerAircraft, int ticks, int traceStride) {
        static Arguments parse(String[] args) {
            if (args.length < 2 || args.length % 2 != 0) {
                throw new IllegalArgumentException(
                        "Usage: FlightResearchBatchMain ANCHOR_CSV OUTPUT_DIR " +
                        "[--seed LONG] [--trials-per-aircraft INT] [--ticks INT] [--trace-stride INT]");
            }
            long seed = DEFAULT_SEED;
            int trials = DEFAULT_TRIALS_PER_AIRCRAFT, ticks = DEFAULT_TICKS;
            int stride = DEFAULT_TRACE_STRIDE;
            for (int i = 2; i < args.length; i += 2) {
                switch (args[i]) {
                    case "--seed" -> seed = Long.parseLong(args[i+1]);
                    case "--trials-per-aircraft" -> trials = Integer.parseInt(args[i+1]);
                    case "--ticks" -> ticks = Integer.parseInt(args[i+1]);
                    case "--trace-stride" -> stride = Integer.parseInt(args[i+1]);
                    default -> throw new IllegalArgumentException("Unknown option: " + args[i]);
                }
            }
            if (trials < Experiment.values().length || trials > 1_000_000 || ticks < 20 || ticks > 10_000
                    || stride < 1 || stride > ticks || (long) trials * ticks * 24 > 400_000_000L)
                throw new IllegalArgumentException(
                        "Invalid budget (minimum 11 trials/aircraft to cover all scenarios)");
            return new Arguments(Path.of(args[0]), Path.of(args[1]), seed, trials, ticks, stride);
        }
    }

    /**
     * Genuine pinned IA 1.3.3 speed-dependent calm-air wind is always applied.
     * Only SCRIPTED_WIND adds an explicitly artificial forcing experiment.
     * Terrain remains a synthetic analytic height field with no voxel collision.
     */
    private record ScriptedWorld(Experiment experiment, double windPhase, double windScale,
                                 double ridgeZ, double ridgeHeight, double ridgeWidth)
            implements World, FlightSafetyPlanner.Terrain {
        @Override public double groundHeight(double x, double z) {
            if (experiment != Experiment.TERRAIN_RIDGE) return 0.0;
            double dz = (z - ridgeZ) / ridgeWidth;
            return ridgeHeight * Math.exp(-dz * dz)
                    * (0.88 + 0.12 * Math.cos(x / 24.0));
        }
        @Override public double topY(double x, double z) {
            return groundHeight(x, z);
        }
        @Override public Wind windAfterFriction(Model model, State state, Vec3 physicalVelocity) {
            Wind pinned = PINNED_CALM_WIND.windAfterFriction(model, state, physicalVelocity);
            if (experiment != Experiment.SCRIPTED_WIND) return pinned;
            // Controlled perturbation ADDED to the original pinned wind effect.
            // Multipliers and harmonic periods are experiment parameters.
            double magnitude = model.wind() * windScale, tick = state.tick();
            return new Wind(
                    pinned.pitchDeltaDeg() + magnitude * Math.sin(tick / 13.0 + windPhase),
                    pinned.yawDeltaDeg() + magnitude * Math.cos(tick / 17.0 + windPhase * 0.7));
        }
    }

    private record Trial(
            String trialId, String aircraftId, String role, String scenario,
            long trialSeed, int engineReactionTicks, int ticks,
            double initialSpeedBps, double meanSpeedBps, double finalSpeedBps,
            double peakSpeedBps, double pathBlocks, double displacementBlocks,
            double minClearanceBlocks, double maxClearanceBlocks,
            double totalAbsYawDeg, double totalAbsPitchDeg,
            int first90YawTick, int groundContactTicks, int safetyOverrideTicks,
            int terrainRecoveryTicks, int maneuverChanges, int aiDecisionTicks,
            int advisoryFireTicks, double finalX, double finalY, double finalZ) {}

    private static final class Aggregate {
        final AircraftAtlasMain.Entry entry;
        final Experiment experiment;
        final int reaction;
        int trials, groundContactTrials, yaw90Trials;
        long groundContactTicks, safetyOverrideTicks, terrainRecoveryTicks;
        long aiDecisionTicks, advisoryFireTicks;
        double distance, speed, finalSpeed, minimumClearance, absYaw, absPitch;
        double ticksToYaw90;
        Aggregate(AircraftAtlasMain.Entry entry, Experiment experiment, int reaction) {
            this.entry = entry;
            this.experiment = experiment;
            this.reaction = reaction;
        }
        void add(Trial t) {
            trials++;
            if (t.groundContactTicks() > 0) groundContactTrials++;
            if (t.first90YawTick() > 0) {
                yaw90Trials++;
                ticksToYaw90 += t.first90YawTick();
            }
            groundContactTicks += t.groundContactTicks();
            safetyOverrideTicks += t.safetyOverrideTicks();
            terrainRecoveryTicks += t.terrainRecoveryTicks();
            aiDecisionTicks += t.aiDecisionTicks();
            advisoryFireTicks += t.advisoryFireTicks();
            distance += t.pathBlocks();
            speed += t.meanSpeedBps();
            finalSpeed += t.finalSpeedBps();
            minimumClearance += t.minClearanceBlocks();
            absYaw += t.totalAbsYawDeg();
            absPitch += t.totalAbsPitchDeg();
        }
    }

    public static void main(String[] rawArgs) throws Exception {
        long started = System.nanoTime();
        Arguments args = Arguments.parse(rawArgs);
        List<AircraftAtlasMain.Entry> roster = new ArrayList<>(AircraftAtlasMain.load(args.input()));
        roster.sort(Comparator.comparing(AircraftAtlasMain.Entry::aircraftId));
        if (roster.size() != 24 || WarfareWingsEngineReaction.all().size() != 24)
            throw new IllegalStateException("Require exactly 24 pinned aircraft");
        verifyAnchorColumn(args.input(), roster.size());
        for (AircraftAtlasMain.Entry entry : roster)
            WarfareWingsEngineReaction.ticks(entry.aircraftId());

        // Prevent accidental output clobber of input/source data.
        Path output = args.output().toAbsolutePath().normalize();
        if (output.equals(args.input().toAbsolutePath().normalize()))
            throw new IllegalArgumentException("Output must be a directory, not the input file");
        Files.createDirectories(output);
        if (Files.isSameFile(output, args.input()))
            throw new IllegalArgumentException("Refusing input/output alias");

        Aggregate[][] aggregates = new Aggregate[roster.size()][Experiment.values().length];
        for (int a = 0; a < roster.size(); a++) {
            int reaction = WarfareWingsEngineReaction.ticks(roster.get(a).aircraftId());
            for (Experiment experiment : Experiment.values())
                aggregates[a][experiment.ordinal()] = new Aggregate(roster.get(a), experiment, reaction);
        }
        long completedTicks = 0, contactTrials = 0, sampledTraces = 0, sampledRows = 0;
        Path outcomes = output.resolve("outcomes.csv");
        Path slices = output.resolve("time_slices.csv");
        try (BufferedWriter trialWriter = Files.newBufferedWriter(outcomes, StandardCharsets.UTF_8);
             BufferedWriter traceWriter = Files.newBufferedWriter(slices, StandardCharsets.UTF_8)) {
            trialWriter.write("schema,trial_id,aircraft_id,role,scenario,trial_seed,engine_reaction_ticks,"
                    + "ticks,initial_speed_bps,mean_speed_bps,final_speed_bps,peak_speed_bps,"
                    + "path_blocks,displacement_blocks,min_clearance_blocks,max_clearance_blocks,"
                    + "total_abs_yaw_deg,total_abs_pitch_deg,first_90_yaw_tick,"
                    + "ground_contact_ticks,safety_override_ticks,terrain_recovery_ticks,"
                    + "maneuver_changes,ai_decision_ticks,advisory_fire_ticks,"
                    + "final_x,final_y,final_z\n");
            traceWriter.write("schema,trial_id,aircraft_id,role,scenario,tick,seconds,"
                    + "x,y,z,vx,vy,vz,speed_bps,yaw_deg,pitch_deg,roll_deg,"
                    + "raw_x,raw_z,engine_target,engine_power,ground_y,clearance,"
                    + "on_ground,maneuver,reason_code,safety_reason,wind_stress_multiplier\n");
            for (int a = 0; a < roster.size(); a++) {
                AircraftAtlasMain.Entry entry = roster.get(a);
                // Profiles are source Atlas V3 profiles; compute once per aircraft.
                Profile profile = Profile.fromAtlas(AircraftAtlasMain.evaluateReaction(entry));
                for (int i = 0; i < args.trialsPerAircraft(); i++) {
                    Experiment experiment = Experiment.values()[i % Experiment.values().length];
                    // Each scenario gets one representative trace for every aircraft.
                    boolean sample = i < Experiment.values().length;
                    long seed = trialSeed(args.seed(), entry.aircraftId(), i);
                    Trial t = simulate(entry, profile, experiment, i, seed, args, sample ? traceWriter : null);
                    aggregates[a][experiment.ordinal()].add(t);
                    trialWriter.write(csv(t));
                    trialWriter.write('\n');
                    completedTicks += t.ticks();
                    if (t.groundContactTicks() > 0) contactTrials++;
                    if (sample) {
                        sampledTraces++;
                        sampledRows += 1L + args.ticks() / args.traceStride()
                                + (args.ticks() % args.traceStride() == 0 ? 0 : 1);
                    }
                }
            }
        }
        writeSummary(output.resolve("summary.json"), roster, aggregates,
                args, completedTicks, contactTrials, sampledTraces, sampledRows);
        double elapsed = (System.nanoTime() - started) / 1e9;
        System.out.printf(Locale.ROOT,
                "FLIGHT_LAB SOURCE_ONLY PASS aircraft=%d scenarios=%d trials=%d ticks=%d " +
                "sample_traces=%d sample_rows=%d ground_contact_trials=%d elapsed_s=%.3f " +
                "trial_per_s=%.1f tick_per_s=%.0f%n",
                roster.size(), Experiment.values().length,
                (long) roster.size() * args.trialsPerAircraft(), completedTicks,
                sampledTraces, sampledRows, contactTrials, elapsed,
                roster.size() * args.trialsPerAircraft() / Math.max(1e-9, elapsed),
                completedTicks / Math.max(1e-9, elapsed));
    }

    private static Trial simulate(AircraftAtlasMain.Entry entry, Profile profile,
                                  Experiment experiment, int trialIndex, long seed,
                                  Arguments args, BufferedWriter traceWriter) throws IOException {
        Model model = entry.model();
        SplittableRandom rand = new SplittableRandom(seed);
        double windScale = 6.0 + 16.0 * rand.nextDouble();
        ScriptedWorld world = new ScriptedWorld(experiment,
                rand.nextDouble() * Math.PI * 2.0,
                windScale,
                65.0 + rand.nextDouble() * 35.0,
                50.0 + rand.nextDouble() * 40.0,
                38.0 + rand.nextDouble() * 22.0);
        double x = rand.nextDouble(-8, 8), y = 127 + rand.nextDouble(-13, 13);
        if (experiment == Experiment.TERRAIN_RIDGE) y = 54 + rand.nextDouble(-9, 9);
        double speed = 0.48 + rand.nextDouble() * 0.50;
        double yaw = rand.nextDouble(-9, 9), pitch = rand.nextDouble(-3, 3);
        double initialEngine = experiment == Experiment.THROTTLE_STEP ? 0.0 : 1.0;
        State state = new State(0, new Vec3(x, y, 0), new Vec3(0, -0.015, speed),
                yaw, pitch, 0, 0, 0, 0, 0, 0, 0, initialEngine,
                0.28 + rand.nextDouble() * 0.54, 1, 0, false, false);
        double initialSpeed = state.velocity().length() * TICKS_PER_SECOND;
        Vec3 start = state.position();
        Vec3 objective = start.add(rand.nextDouble(-80, 80),
                experiment == Experiment.TERRAIN_RIDGE ? 0 : rand.nextDouble(-28, 28),
                220 + rand.nextDouble() * 150);
        Vec3 home = start.add(0, 20, -110);
        Vec3 observedStart = start.add(22 + rand.nextDouble(-24, 24),
                rand.nextDouble(-12, 12), 82 + rand.nextDouble() * 60);
        Vec3 contactVelocity = new Vec3(rand.nextDouble(-0.12, 0.12), 0,
                -0.28 - rand.nextDouble() * 0.28);
        Vec3 leaderStart = start.add(35, 12, 36);
        Vec3 leaderVelocity = new Vec3(0, 0, 0.65);
        Memory memory = Memory.INITIAL;
        HistoricalDoctrineOrders.Order order = doctrineOrder(entry, experiment, trialIndex);
        FlightSafetyPlanner.Environment environment = new FlightSafetyPlanner.Environment(
                world, List.of(), 4.0);
        int reaction = WarfareWingsEngineReaction.ticks(entry.aircraftId());
        String trialId = entry.baseId() + "-" + String.format(Locale.ROOT, "%05d", trialIndex)
                + "-" + experiment.name().toLowerCase(Locale.ROOT);
        double distance = 0, sumSpeeds = initialSpeed, peak = initialSpeed;
        double minClearance = state.position().y() - world.groundHeight(start.x(), start.z());
        double maxAltitude = minClearance, yawAbs = 0, pitchAbs = 0;
        int first90 = -1, groundTicks = 0, overrides = 0, recovery = 0;
        int changes = 0, aiTicks = 0, advisoryFire = 0;
        Maneuver last = null;
        String maneuver = "SCRIPTED", reason = "FIXED_INPUT", safety = "NONE";
        if (traceWriter != null)
            writeSlice(traceWriter, trialId, entry, experiment, state, world, maneuver, reason, safety);

        for (int t = 1; t <= args.ticks(); t++) {
            Control control;
            if (experiment.usesAI()) {
                Vec3 formationAnchor = experiment == Experiment.AI_FORMATION
                        ? leaderStart.add(leaderVelocity.scale(t - 1)) : null;
                Contact contact = experiment == Experiment.AI_OBSERVED_CONTACT
                        ? new Contact("scripted-observed-contact",
                        observedStart.add(contactVelocity.scale(t - 1)), contactVelocity, true)
                        : null;
                List<FlightSafetyPlanner.MovingObstacle> moving = contact == null
                        ? List.of() : List.of(new FlightSafetyPlanner.MovingObstacle(
                            contact.id(), contact.position(), contact.velocity(), 5.0, true));
                FlightSafetyPlanner.Environment activeEnvironment = moving.isEmpty()
                        ? environment : new FlightSafetyPlanner.Environment(world, moving, 4.0);
                Frame frame = new Frame(profile, model, state,
                        mission(entry, experiment), objective, home, contact, formationAnchor,
                        null, 1.0, 1.0, world.groundHeight(state.position().x(), state.position().z()),
                        false, 0.0, formationAnchor == null ? Vec3.ZERO : leaderVelocity);
                FlightControlLoop.Output command = FlightControlLoop.step(
                        new FlightControlLoop.Input(frame, memory, order, activeEnvironment));
                Decision decision = command.decision();
                memory = decision.nextMemory();
                control = decision.controls();
                maneuver = decision.maneuver().name();
                reason = decision.reasonCode();
                safety = command.safety().reason().name();
                if (last != null && last != decision.maneuver()) changes++;
                last = decision.maneuver();
                aiTicks++;
                if (decision.firingWindowCandidate()) advisoryFire++;
                if (command.safety().override()) overrides++;
                if (decision.maneuver() == Maneuver.TERRAIN_RECOVERY) recovery++;
            } else {
                control = scriptedControl(experiment, t, args.ticks());
                safety = "NONE";
                maneuver = "SCRIPTED";
                reason = experiment.name();
            }
            State next = Ia133Microkernel.tickWithReaction(model, state, control, world, reaction);
            requireFinite(next, trialId, t);
            double clearance = next.position().y()
                    - world.groundHeight(next.position().x(), next.position().z());
            minClearance = Math.min(minClearance, clearance);
            maxAltitude = Math.max(maxAltitude, clearance);
            if (next.onGround()) groundTicks++;
            distance += next.position().add(state.position().scale(-1)).length();
            double nextSpeed = next.velocity().length() * TICKS_PER_SECOND;
            sumSpeeds += nextSpeed;
            peak = Math.max(peak, nextSpeed);
            yawAbs += Math.abs(next.yawDeg() - state.yawDeg());
            pitchAbs += Math.abs(next.pitchDeg() - state.pitchDeg());
            if (first90 == -1 && Math.abs(next.yawDeg() - yaw) >= 90.0) first90 = t;
            state = next;
            if (traceWriter != null && (t % args.traceStride() == 0 || t == args.ticks()))
                writeSlice(traceWriter, trialId, entry, experiment, state, world,
                        maneuver, reason, safety);
        }
        return new Trial(trialId, entry.aircraftId(), entry.role(), experiment.name(),
                seed, reaction, args.ticks(), initialSpeed, sumSpeeds / (args.ticks() + 1),
                state.velocity().length() * TICKS_PER_SECOND, peak, distance,
                state.position().add(start.scale(-1)).length(), minClearance,
                maxAltitude, yawAbs, pitchAbs, first90, groundTicks,
                overrides, recovery, changes, aiTicks, advisoryFire,
                state.position().x(), state.position().y(), state.position().z());
    }

    private static Control scriptedControl(Experiment experiment, int tick, int totalTicks) {
        int oneThird = Math.max(1, totalTicks / 3);
        return switch (experiment) {
            case CRUISE, SCRIPTED_WIND -> Control.neutral(1.0);
            case THROTTLE_STEP -> Control.neutral(tick <= oneThird ? 0.0 : 1.0);
            case TURN_LEFT -> new Control(tick > 15 ? -1 : 0, 0, 0, 1);
            case TURN_RIGHT -> new Control(tick > 15 ? 1 : 0, 0, 0, 1);
            case CLIMB -> new Control(0, 0, tick > 10 ? -1 : 0, 1);
            case DIVE_RECOVERY -> new Control(0, 0, tick <= oneThird ? 0.9 : -0.9, 1);
            default -> throw new IllegalArgumentException("AI scenario has no scripted control");
        };
    }

    private static Mission mission(AircraftAtlasMain.Entry entry, Experiment experiment) {
        if (experiment == Experiment.TERRAIN_RIDGE) return Mission.PATROL;
        if ("fighter".equals(entry.role()))
            return experiment == Experiment.AI_OBSERVED_CONTACT ? Mission.INTERCEPT
                    : experiment == Experiment.AI_FORMATION ? Mission.ESCORT : Mission.PATROL;
        return switch (entry.role()) {
            case "bomber" -> Mission.LEVEL_BOMB;
            case "torpedo_bomber" -> Mission.TORPEDO;
            case "attacker" -> Mission.DIVE_BOMB;
            default -> Mission.PATROL;
        };
    }

    private static HistoricalDoctrineOrders.Order doctrineOrder(
            AircraftAtlasMain.Entry entry, Experiment experiment, int trialIndex) {
        if (experiment != Experiment.AI_FORMATION) return null;
        HistoricalDoctrineOrders.Pattern pattern = null;
        int slot = trialIndex % 2;
        if ("fighter".equals(entry.role())) {
            pattern = switch (entry.faction()) {
                case "raf" -> HistoricalDoctrineOrders.Pattern.RAF_FINGER_FOUR_1940;
                case "usn" -> HistoricalDoctrineOrders.Pattern.USN_MUTUAL_SUPPORT_1942;
                case "usaaf" -> HistoricalDoctrineOrders.Pattern.USAAF_ESCORT_COVER_1944;
                default -> null;
            };
        } else if ("bomber".equals(entry.role()) && "usaaf".equals(entry.faction())) {
            pattern = HistoricalDoctrineOrders.Pattern.USAAF_COMBAT_BOX_1943;
        }
        return pattern == null ? null : new HistoricalDoctrineOrders.Order(pattern, slot, 0, 1944);
    }

    private static void requireFinite(State state, String trialId, int tick) {
        Vec3 p = state.position(), v = state.velocity();
        if (!Double.isFinite(p.x()) || !Double.isFinite(p.y()) || !Double.isFinite(p.z())
                || !Double.isFinite(v.x()) || !Double.isFinite(v.y()) || !Double.isFinite(v.z())
                || !Double.isFinite(state.yawDeg()) || !Double.isFinite(state.pitchDeg())
                || !Double.isFinite(state.rollDeg()) || !Double.isFinite(state.enginePowerSmooth()))
            throw new IllegalStateException("Nonfinite SOURCE state: " + trialId + " tick=" + tick);
    }

    private static long trialSeed(long seed, String id, int index) {
        long z = seed ^ ((long) id.hashCode() * 0x9E3779B97F4A7C15L)
                ^ ((long) index + 1) * 0xD1B54A32D192ED03L;
        z = (z ^ (z >>> 30)) * 0xBF58476D1CE4E5B9L;
        z = (z ^ (z >>> 27)) * 0x94D049BB133111EBL;
        return z ^ (z >>> 31);
    }

    private static void verifyAnchorColumn(Path source, int expectedCount) throws IOException {
        List<String> lines = Files.readAllLines(source, StandardCharsets.UTF_8);
        if (lines.size() != expectedCount + 1) throw new IllegalArgumentException("Unexpected Atlas CSV row count");
        String[] columns = lines.get(0).split(",", -1);
        int hashIndex = -1;
        for (int i = 0; i < columns.length; i++)
            if (columns[i].equals("anchor_sha256")) hashIndex = i;
        if (hashIndex < 0) throw new IllegalArgumentException("Missing ANCHOR JAR provenance column");
        for (int row = 1; row < lines.size(); row++) {
            String[] parts = lines.get(row).split(",", -1);
            if (parts.length <= hashIndex || !parts[hashIndex].equals(
                    WarfareWingsAircraft.WARFARE_WINGS_ANCHOR_SHA256))
                throw new IllegalArgumentException("ANCHOR provenance mismatch in CSV row " + row);
        }
    }

    private static void writeSlice(BufferedWriter w, String id, AircraftAtlasMain.Entry entry,
                                   Experiment ex, State s, ScriptedWorld world,
                                   String maneuver, String reason, String safety) throws IOException {
        double y = world.groundHeight(s.position().x(), s.position().z());
        w.write(String.join(",", SCHEMA, id, entry.aircraftId(), entry.role(), ex.name(),
                Long.toString(s.tick()), d(s.tick() / TICKS_PER_SECOND),
                d(s.position().x()), d(s.position().y()), d(s.position().z()),
                d(s.velocity().x()), d(s.velocity().y()), d(s.velocity().z()),
                d(s.velocity().length() * TICKS_PER_SECOND),
                d(s.yawDeg()), d(s.pitchDeg()), d(s.rollDeg()),
                d(s.rawX()), d(s.rawZ()), d(s.engineTarget()), d(s.enginePowerSmooth()),
                d(y), d(s.position().y() - y), Boolean.toString(s.onGround()),
                maneuver, reason, safety, d(world.windScale())));
        w.write('\n');
    }

    private static String csv(Trial t) {
        return String.join(",", SCHEMA, t.trialId(), t.aircraftId(), t.role(),
                t.scenario(), Long.toString(t.trialSeed()), Integer.toString(t.engineReactionTicks()),
                Integer.toString(t.ticks()), d(t.initialSpeedBps()), d(t.meanSpeedBps()),
                d(t.finalSpeedBps()), d(t.peakSpeedBps()), d(t.pathBlocks()),
                d(t.displacementBlocks()), d(t.minClearanceBlocks()), d(t.maxClearanceBlocks()),
                d(t.totalAbsYawDeg()), d(t.totalAbsPitchDeg()),
                Integer.toString(t.first90YawTick()), Integer.toString(t.groundContactTicks()),
                Integer.toString(t.safetyOverrideTicks()), Integer.toString(t.terrainRecoveryTicks()),
                Integer.toString(t.maneuverChanges()), Integer.toString(t.aiDecisionTicks()),
                Integer.toString(t.advisoryFireTicks()), d(t.finalX()), d(t.finalY()), d(t.finalZ()));
    }

    private static String d(double v) {
        if (!Double.isFinite(v)) throw new IllegalArgumentException("Nonfinite metric");
        return String.format(Locale.ROOT, "%.9f", v);
    }

    private static void writeSummary(Path json, List<AircraftAtlasMain.Entry> roster,
                                     Aggregate[][] groups, Arguments args,
                                     long simulatedTicks, long groundContacts,
                                     long traceCount, long sliceRows) throws IOException {
        try (BufferedWriter w = Files.newBufferedWriter(json, StandardCharsets.UTF_8)) {
            w.write("{\n  \"schema\": " + quote(SCHEMA)
                    + ",\n  \"evidence\": " + quote(EVIDENCE)
                    + ",\n  \"kernel\": " + quote(SOURCE)
                    + ",\n  \"aircraft_anchor_sha256\": "
                    + quote(WarfareWingsAircraft.WARFARE_WINGS_ANCHOR_SHA256)
                    + ",\n  \"immersive_aircraft_source_tag\": "
                    + quote(WarfareWingsAircraft.IA_SOURCE_TAG)
                    + ",\n  \"immersive_aircraft_source_commit\": "
                    + quote(WarfareWingsAircraft.IA_SOURCE_COMMIT)
                    + ",\n  \"wind_baseline\": "
                    + quote("PINNED_IA133_SPEED_DEPENDENT_CALM")
                    + ",\n  \"wind_baseline_implementation\": "
                    + quote("PinnedIa133WindWorld.calmAirCalibration().windAfterFriction")
                    + ",\n  \"wind_stress_overlay\": "
                    + quote("SCRIPTED_WIND_ONLY")
                    + ",\n  \"seed\": " + quote(Long.toString(args.seed()))
                    + ",\n  \"tick_rate_hz\": 20,\n  \"ticks_per_trial\": " + args.ticks()
                    + ",\n  \"trials_per_aircraft\": " + args.trialsPerAircraft()
                    + ",\n  \"aircraft_count\": " + roster.size()
                    + ",\n  \"scenario_count\": " + Experiment.values().length
                    + ",\n  \"trial_count\": " + (long) roster.size() * args.trialsPerAircraft()
                    + ",\n  \"simulated_ticks\": " + simulatedTicks
                    + ",\n  \"ground_contact_trials\": " + groundContacts
                    + ",\n  \"sample_trace_stride_ticks\": " + args.traceStride()
                    + ",\n  \"sampled_traces\": " + traceCount
                    + ",\n  \"sampled_time_slice_rows\": " + sliceRows
                    + ",\n  \"scenarios\": [");
            for (Experiment e : Experiment.values()) {
                if (e.ordinal() > 0) w.write(", ");
                w.write(quote(e.name()));
            }
            w.write("],\n  \"disclaimers\": ["
                    + quote("Pinned IA 1.3.3 speed-dependent wind reconstructed for calm-weather baseline") + ","
                    + quote("SCRIPTED_WIND adds a synthetic forcing overlay, not the real weather configuration") + ","
                    + quote("Terrain height is a sampled analytic ridge, not Minecraft voxel collision") + ","
                    + quote("Contact is observed kinematic scenario data, not a simulated opponent") + ","
                    + quote("No weapon discharge or validated Forge parity") + "],\n  \"groups\": [\n");
            boolean first = true;
            for (Aggregate[] rows : groups) for (Aggregate group : rows) {
                if (!first) w.write(",\n");
                first = false;
                w.write("    {\"aircraft_id\":" + quote(group.entry.aircraftId())
                        + ",\"role\":" + quote(group.entry.role())
                        + ",\"faction\":" + quote(group.entry.faction())
                        + ",\"doctrine\":" + quote(group.entry.doctrine())
                        + ",\"scenario\":" + quote(group.experiment.name())
                        + ",\"trial_count\":" + group.trials
                        + ",\"engine_reaction_ticks\":" + group.reaction
                        + ",\"mean_path_blocks\":" + d(group.distance / group.trials)
                        + ",\"mean_speed_bps\":" + d(group.speed / group.trials)
                        + ",\"mean_final_speed_bps\":" + d(group.finalSpeed / group.trials)
                        + ",\"mean_min_clearance_blocks\":" + d(group.minimumClearance / group.trials)
                        + ",\"mean_abs_yaw_deg\":" + d(group.absYaw / group.trials)
                        + ",\"mean_abs_pitch_deg\":" + d(group.absPitch / group.trials)
                        + ",\"ground_contact_trials\":" + group.groundContactTrials
                        + ",\"ground_contact_ticks\":" + group.groundContactTicks
                        + ",\"safety_override_ticks\":" + group.safetyOverrideTicks
                        + ",\"terrain_recovery_ticks\":" + group.terrainRecoveryTicks
                        + ",\"ai_decision_ticks\":" + group.aiDecisionTicks
                        + ",\"advisory_fire_ticks\":" + group.advisoryFireTicks
                        + ",\"reached_90_yaw_trials\":" + group.yaw90Trials
                        + ",\"mean_ticks_to_90_yaw\":"
                        + (group.yaw90Trials > 0 ? d(group.ticksToYaw90 / group.yaw90Trials) : "null")
                        + "}");
            }
            w.write("\n  ]\n}\n");
        }
    }

    private static String quote(String value) {
        StringBuilder b = new StringBuilder("\"");
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            switch (c) {
                case '\\' -> b.append("\\\\");
                case '"' -> b.append("\\\"");
                case '\n' -> b.append("\\n");
                case '\r' -> b.append("\\r");
                case '\t' -> b.append("\\t");
                default -> {
                    if (c < 32) b.append(String.format(Locale.ROOT, "\\u%04x", (int) c));
                    else b.append(c);
                }
            }
        }
        return b.append('"').toString();
    }
}
