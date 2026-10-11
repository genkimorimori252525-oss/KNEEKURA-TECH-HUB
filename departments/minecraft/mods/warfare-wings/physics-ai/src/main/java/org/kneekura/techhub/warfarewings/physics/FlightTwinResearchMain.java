package org.kneekura.techhub.warfarewings.physics;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;

import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;

/**
 * Deterministic simultaneous (not scripted-opponent) multi-aircraft 20 Hz
 * source flight twin. Each tick has a strict frozen snapshot boundary:
 *
 *  (1) every aircraft physically advances under the PRIOR queued raw controls;
 *  (2) each aircraft privately senses that newly completed tick's opponents;
 *  (3) its tracks expire/refresh (FOV/range/terrain LOS);
 *  (4) team commander assigns ONLY locally remembered hostile IDs;
 *  (5) FlightControlLoop sees that completed snapshot and QUEUES controls
 *      for the NEXT physics tick, matching real ServerTick.END timing;
 *  (6) unchanged 6b pair/95b bomber distances measured on new positions.
 *
 * This uses original pinned IA speed-dependent calm-weather wind, no fake
 * kills or weapons. Height-only LOS and swept centre distances are DIAGNOSTIC
 * research approximations, not actual Minecraft voxel raycasts/hitboxes.
 */
public final class FlightTwinResearchMain {
    public static final String SCHEMA = "ww.flight-twin.closed-loop.v1";
    public static final String EVIDENCE =
            "SOURCE_TICK_WITH_REACTION_PINNED_IA133_WIND_SYNTHETIC_SENSORS_NO_FORGE_PARITY";
    private static final double BODY = FlightTwinScenario.BODY_SEPARATION_BLOCKS;
    private static final double B17 = FlightTwinScenario.B17_PROTECTION_BLOCKS;
    private static final FlightTwinSensor.Parameters SENSOR = FlightTwinSensor.Parameters.DEFAULT;
    private static final String JAVA_MAIN = "FlightTwinResearchMain";

    private FlightTwinResearchMain() {}

    private record Options(Path anchor, Path output, long seed, int uniqueTicks,
                           int traceStride, String scenario, boolean reverseInput) {
        static Options parse(String[] args) {
            if (args.length < 2) throw new IllegalArgumentException(
                    "Usage: FlightTwinResearchMain ANCHOR_CSV OUTPUT_DIRECTORY "
                    + "[--seed LONG] [--24-ticks 240] [--trace-stride 10] "
                    + "[--scenario all|all_24_unique|original_2v2|original_b17_aft"
                    + "|original_b17_forward|synthetic_los_occluded|forge_original_b17_340] [--reverse-roster]");
            long seed = 20261011L;
            int ticks = 240, stride = 10;
            String scene = "all";
            boolean reverse = false;
            for (int i = 2; i < args.length; i++) {
                String flag = args[i];
                if ("--reverse-roster".equals(flag)) { reverse = true; continue; }
                if (i+1 >= args.length) throw new IllegalArgumentException("Missing option value for " + flag);
                String value = args[++i];
                switch (flag) {
                    case "--seed" -> seed = Long.parseLong(value);
                    case "--24-ticks" -> ticks = Integer.parseInt(value);
                    case "--trace-stride" -> stride = Integer.parseInt(value);
                    case "--scenario" -> scene = value;
                    default -> throw new IllegalArgumentException("Unknown option " + flag);
                }
            }
            if (ticks < 20 || ticks > 2400 || stride < 1 || stride > ticks)
                throw new IllegalArgumentException("Invalid 24-ticks/stride");
            if (!Set.of("all","all_24_unique","original_2v2","original_b17_aft",
                    "original_b17_forward","synthetic_los_occluded",
                    "forge_original_b17_340").contains(scene))
                throw new IllegalArgumentException("Unknown Twin scenario: " + scene);
            return new Options(Path.of(args[0]),Path.of(args[1]),seed,ticks,stride,scene,reverse);
        }
    }

    private record Local(State state, TacticalAirAI.Memory policyMemory,
                         Map<String, FlightTwinSensor.Track> tracks) {
        Local {
            tracks = Collections.unmodifiableMap(new TreeMap<>(tracks));
        }
    }
    private record Command(TacticalAirAI.Decision decision,
                           FlightSafetyPlanner.Clearance safety,
                           String targetId, String observedContactId,
                           int contactAge, int friendCount, double nearestFriendly,
                           FlightTwinSensor.Update sensed) {}

    private static final class UnitStats {
        final FlightTwinScenario.Plane plane;
        final String role;
        final int reactionTicks;
        final Vec3 start;
        final double initialSpeed;
        double path, minClearance = Double.POSITIVE_INFINITY, finalSpeed, finalObjectiveDistance;
        Vec3 finalPosition;
        int groundTicks, visibleTicks, memoryTicks, firstVisible = -1, firstRemembered = -1;
        int expiredTracks, losRejections, fovRejections, rangeRejections;
        int assignedTicks, avoidanceTicks, terrainSafetyTicks, safetyOverrides;
        int decisionChanges, fireCandidateTicks, firstTargetAssignment = -1;
        TacticalAirAI.Maneuver lastManeuver;
        UnitStats(FlightTwinScenario.Plane plane, String role, int reactionTicks) {
            this.plane = plane;
            this.role = role;
            this.reactionTicks = reactionTicks;
            this.start = plane.start();
            this.finalPosition = start;
            this.initialSpeed = plane.velocity().length() * 20.0;
        }
        void add(Local before, Local after, Command command, int tick, World world) {
            path += length(after.state().position().add(before.state().position().scale(-1)));
            double clearance = after.state().position().y()
                    - world.groundHeight(after.state().position().x(),after.state().position().z());
            minClearance = Math.min(minClearance, clearance);
            if (after.state().onGround()) groundTicks++;
            finalSpeed = after.state().velocity().length() * 20;
            finalPosition = after.state().position();
            finalObjectiveDistance = length(after.state().position().add(plane.objective().scale(-1)));
            var sensed = command.sensed();
            if (!sensed.currentlyVisible().isEmpty()) {
                visibleTicks++;
                if (firstVisible < 0) firstVisible = tick;
            }
            if (sensed.rememberedCount() > 0) {
                memoryTicks++;
                if (firstRemembered < 0) firstRemembered = tick;
            }
            expiredTracks += sensed.expired().size();
            losRejections += sensed.losRejected();
            fovRejections += sensed.fovRejected();
            rangeRejections += sensed.rangeRejected();
            if (command.targetId() != null) {
                assignedTicks++;
                if (firstTargetAssignment < 0) firstTargetAssignment = tick;
            }
            switch (command.safety().reason()) {
                case MOVING_COLLISION_RISK -> avoidanceTicks++;
                case TERRAIN_AHEAD -> terrainSafetyTicks++;
                default -> {}
            }
            if (command.safety().override()) safetyOverrides++;
            if (command.decision().firingWindowCandidate()) fireCandidateTicks++;
            if (lastManeuver != null && command.decision().maneuver() != lastManeuver) decisionChanges++;
            lastManeuver = command.decision().maneuver();
        }
    }

    private static final class PairStats {
        final String a, b;
        final double initial;
        double minSampled, minSwept, finalDistance;
        int closestTick, sweptClosestTick, sampledUnderSix, sweptUnderSix;
        PairStats(String a, String b, double initial) {
            this.a = a; this.b = b; this.initial = initial;
            this.minSampled = initial; this.minSwept = initial; this.finalDistance = initial;
        }
        void sample(Vec3 oldA, Vec3 oldB, Vec3 newA, Vec3 newB, int tick) {
            double sampled = distance(newA,newB);
            double swept = segmentApproach(oldA,oldB,newA,newB);
            finalDistance = sampled;
            if (sampled < minSampled) { minSampled = sampled; closestTick = tick; }
            if (swept < minSwept) { minSwept = swept; sweptClosestTick = tick; }
            if (sampled < BODY) sampledUnderSix++;
            if (swept < BODY) sweptUnderSix++;
        }
        boolean safe() {
            return minSampled >= BODY && minSwept >= BODY
                    && sampledUnderSix == 0 && sweptUnderSix == 0;
        }
    }

    private static final class AssetStats {
        final String id;
        double initialHostile = Double.POSITIVE_INFINITY;
        double minSampled = Double.POSITIVE_INFINITY, minSwept = Double.POSITIVE_INFINITY;
        int within95, sweptWithin95, firstEntry = -1, firstSweptEntry = -1;
        int escortAssignmentTicks, firstEscortAssignment = -1, interpositionTicks;
        double bomberPath, bomberFinalObjective, bomberFinalSpeed;
        int bomberGroundTicks;
        AssetStats(String id) { this.id = id; }
        void sampleThreat(double sampled, double swept, int tick) {
            if (tick == 0) initialHostile = Math.min(initialHostile,sampled);
            minSampled = Math.min(minSampled,sampled);
            minSwept = Math.min(minSwept,swept);
            if (tick > 0 && sampled <= B17) {
                within95++;
                if (firstEntry < 0) firstEntry = tick;
            }
            if (tick > 0 && swept <= B17) {
                sweptWithin95++;
                if (firstSweptEntry < 0) firstSweptEntry = tick;
            }
        }
        boolean safe() {
            return minSampled > B17 && minSwept > B17
                    && within95 == 0 && sweptWithin95 == 0;
        }
    }

    private record Report(String scenario, int ticks, int aircraftCount,
                          int uniqueAircraftTypes, int observedTicks,
                          int rememberedTicks, int terrainBlockedObservations,
                          int fovBlockedObservations, int rangeBlockedObservations,
                          int totalDecisions, int sourcePhysicsTicks,
                          double minPairSampled, double minPairSwept,
                          int sixBreaches, int ninetyFiveBreaches,
                          List<String> failedGates,
                          List<UnitStats> units, List<PairStats> pairs,
                          List<AssetStats> assets, String terrain) {
        String status() { return failedGates.isEmpty() ? "PASS_SOURCE_SAFETY" : "FAILED_SOURCE_SAFETY"; }
    }

    public static void main(String[] rawArgs) throws Exception {
        long started = System.nanoTime();
        Options options = Options.parse(rawArgs);
        List<AircraftAtlasMain.Entry> entries = AircraftAtlasMain.load(options.anchor());
        if (entries.size() != 24) throw new IllegalArgumentException("Expected 24 Atlas types");
        Map<String, AircraftAtlasMain.Entry> models = new TreeMap<>();
        Map<String, TacticalAirAI.Profile> profiles = new TreeMap<>();
        for (var entry : entries) {
            if (models.putIfAbsent(entry.aircraftId(),entry) != null)
                throw new IllegalArgumentException("Duplicate Atlas model");
            profiles.put(entry.aircraftId(),TacticalAirAI.Profile.fromAtlas(
                    AircraftAtlasMain.evaluateReaction(entry)));
            WarfareWingsEngineReaction.ticks(entry.aircraftId());
        }
        validateAnchor(options.anchor());
        Path output = options.output().toAbsolutePath().normalize();
        if (output.equals(options.anchor().toAbsolutePath().normalize()))
            throw new IllegalArgumentException("Output cannot alias anchor data");
        Files.createDirectories(output);
        if (Files.isSameFile(options.anchor(),output))
            throw new IllegalArgumentException("Output points to the Atlas CSV");
        List<FlightTwinScenario.Case> scenarios = new ArrayList<>(List.of(
                FlightTwinScenario.original2v2(),
                FlightTwinScenario.originalB17Aft(),
                FlightTwinScenario.originalB17Forward(),
                FlightTwinScenario.occludedContact(),
                FlightTwinScenario.all24(entries,options.seed(),options.uniqueTicks())));
        if (options.scenario().equals("forge_original_b17_340"))
            scenarios.add(FlightTwinScenario.realForgeOriginalB17340());
        scenarios.removeIf(c -> !options.scenario().equals("all")
                && !options.scenario().equals(c.id()));
        List<Report> reports = new ArrayList<>();
        try (BufferedWriter unitWriter = writer(output,"twin_units.csv");
             BufferedWriter pairWriter = writer(output,"twin_pairs.csv");
             BufferedWriter assetWriter = writer(output,"twin_assets.csv");
             BufferedWriter sliceWriter = writer(output,"twin_time_slices.csv");
             BufferedWriter sensorWriter = writer(output,"twin_sensor_events.csv")) {
            headers(unitWriter,pairWriter,assetWriter,sliceWriter,sensorWriter);
            for (FlightTwinScenario.Case scenario : scenarios) {
                Report report = simulate(scenario,models,profiles,options.traceStride(),
                        options.reverseInput(),sliceWriter,sensorWriter);
                reports.add(report);
                for (var u : report.units()) writeUnit(unitWriter,report.scenario(),u);
                for (var p : report.pairs()) writePair(pairWriter,report.scenario(),p);
                for (var a : report.assets()) writeAsset(assetWriter,report.scenario(),a);
            }
        }
        writeSummary(output.resolve("twin_summary.json"), options, reports);
        int planes = reports.stream().mapToInt(Report::aircraftCount).sum();
        int ticks = reports.stream().mapToInt(Report::sourcePhysicsTicks).sum();
        long failures = reports.stream().filter(r->!r.failedGates().isEmpty()).count();
        System.out.printf(Locale.ROOT,
                "FLIGHT_TWIN SOURCE_EXECUTION_COMPLETE scenarios=%d unique_types=%d aircraft_instances=%d "
                + "source_ticks=%d safety_failed_scenarios=%d elapsed_s=%.3f%n",
                reports.size(),models.size(),planes,ticks,failures,
                (System.nanoTime()-started)/1e9);
        for (Report report : reports)
            System.out.printf(Locale.ROOT,
                    "TWIN_CASE %s %s aircraft=%d t=%d min_sampled=%.6f "
                    + "min_swept=%.6f violations_6b=%d intrusions_95b=%d%n",
                    report.scenario(),report.status(),report.aircraftCount(),report.ticks(),
                    report.minPairSampled(),report.minPairSwept(),
                    report.sixBreaches(),report.ninetyFiveBreaches());
    }

    private static Report simulate(FlightTwinScenario.Case scenario,
                                   Map<String, AircraftAtlasMain.Entry> models,
                                   Map<String, TacticalAirAI.Profile> profiles,
                                   int stride, boolean reverse,
                                   BufferedWriter slices, BufferedWriter observations)
            throws IOException {
        List<FlightTwinScenario.Plane> roster = new ArrayList<>(scenario.planes());
        if (reverse) Collections.reverse(roster);
        Map<String, FlightTwinScenario.Plane> specs = new TreeMap<>();
        Map<String, Local> previous = new TreeMap<>();
        // Original first GameTest physics step is autonomous vehicle physics:
        // its pilot is registered before the first aircraft tick, but the
        // first server END callback has not yet sent IA control. No first
        // policy decision may retroactively steer tick 0 -> tick 1.
        Map<String,Control> queuedControls = new TreeMap<>();
        for (var spec : roster) {
            if (specs.putIfAbsent(spec.id(),spec) != null)
                throw new IllegalArgumentException("duplicate unit ID");
            if (!models.containsKey(spec.typeId()))
                throw new IllegalArgumentException("Unsupported aircraft: " + spec.typeId());
            var model = models.get(spec.typeId()).model();
            checkRole(model.role(),spec.mission());
            State initial = new State(0,spec.start(),spec.velocity(),spec.yaw(),0,0,
                    0,0,0,0,0,0,1,0,1,0,false,false);
            previous.put(spec.id(),new Local(initial,TacticalAirAI.Memory.INITIAL,Map.of()));
            queuedControls.put(spec.id(),Control.neutral(1.0));
        }
        if (scenario.unique24() && (specs.size() != 24
                || specs.values().stream().map(FlightTwinScenario.Plane::typeId).distinct().count() != 24))
            throw new IllegalArgumentException("All24 case must contain exactly 24 unique active models");

        Map<String, UnitStats> units = new TreeMap<>();
        Map<String, PairStats> pairs = new TreeMap<>();
        Map<String, AssetStats> assets = new TreeMap<>();
        Map<String, Map<String, FlightTwinSensor.Visibility>> lastVisibility = new TreeMap<>();
        List<String> ids = List.copyOf(specs.keySet());
        for (var spec : specs.values()) {
            units.put(spec.id(),new UnitStats(spec,models.get(spec.typeId()).role(),
                    WarfareWingsEngineReaction.ticks(spec.typeId())));
            lastVisibility.put(spec.id(),new TreeMap<>());
        }
        for (int i = 0; i < ids.size(); i++) for (int j = i+1; j < ids.size(); j++) {
            String a = ids.get(i), b = ids.get(j);
            pairs.put(a+"|"+b,new PairStats(a,b,distance(
                    previous.get(a).state().position(), previous.get(b).state().position())));
        }
        for (var assetId : new HashSet<>(scenario.escortAssets().values()))
            assets.put(assetId,new AssetStats(assetId));
        for (var asset : assets.values()) {
            Vec3 pos = previous.get(asset.id).state().position();
            double closest = Double.POSITIVE_INFINITY;
            for (var spec : specs.values()) if (!spec.team().equals(specs.get(asset.id).team()))
                closest = Math.min(closest,distance(pos,previous.get(spec.id()).state().position()));
            asset.sampleThreat(closest,closest,0);
        }
        for (var own : previous.entrySet()) writeSlice(slices,scenario,0,own.getKey(),
                specs.get(own.getKey()),models.get(specs.get(own.getKey()).typeId()).role(),
                own.getValue(),null,null,-1);

        for (int tick = 0; tick < scenario.ticks(); tick++) {
            int completed = tick+1;
            // IA physical entity steps are completed BEFORE server END-stage
            // perception/policy updates. All aircraft advance in a synchronized
            // physical phase using only the controls queued on the prior tick.
            Map<String,Local> physicallyAdvanced = new TreeMap<>();
            Map<String,Control> appliedControls = new TreeMap<>();
            for (var spec : specs.values()) {
                Local own = previous.get(spec.id());
                var model = models.get(spec.typeId()).model();
                Control applied = queuedControls.get(spec.id());
                if (applied == null) throw new IllegalStateException("Missing prior actuation " + spec.id());
                State after = Ia133Microkernel.tickWithReaction(model,own.state(),
                        applied,scenario.world(),WarfareWingsEngineReaction.ticks(model.id()));
                if (after.tick() != completed || !finite(after.position())
                        || !finite(after.velocity()) || !Double.isFinite(after.yawDeg())
                        || !Double.isFinite(after.pitchDeg()))
                    throw new IllegalStateException("Bad SOURCE twin advance " + spec.id());
                physicallyAdvanced.put(spec.id(),new Local(after,own.policyMemory(),own.tracks()));
                appliedControls.put(spec.id(),applied);
            }

            // Sensor and policy snapshots all read the same COMPLETED physics
            // time. Each new decision is queued, never injected into physics
            // that has already happened.
            Map<String, FlightTwinSensor.Update> sensed = new TreeMap<>();
            for (var own : specs.values()) {
                Map<String, State> enemies = new TreeMap<>();
                for (var other : specs.values())
                    if (!other.team().equals(own.team()))
                        enemies.put(other.id(), physicallyAdvanced.get(other.id()).state());
                FlightTwinSensor.Update observation = FlightTwinSensor.update(
                        completed,physicallyAdvanced.get(own.id()).state(),enemies,
                        physicallyAdvanced.get(own.id()).tracks(),scenario.world(),SENSOR);
                sensed.put(own.id(),observation);
                Map<String, FlightTwinSensor.Visibility> previousReasons =
                        lastVisibility.get(own.id());
                for (var other : observation.assessments().entrySet()) {
                    String hostileId = other.getKey();
                    FlightTwinSensor.Visibility before = previousReasons.put(
                            hostileId,other.getValue().visibility());
                    FlightTwinSensor.Track track = observation.tracks().get(hostileId);
                    boolean expired = observation.expired().contains(hostileId);
                    if (before != other.getValue().visibility() || expired)
                        writeSensorEvent(observations,scenario.id(),completed,own.id(),hostileId,
                                before,other.getValue(),track,expired);
                }
            }
            Map<String,String> assigned = targetAssignments(
                    specs,physicallyAdvanced,sensed,completed,models);
            Map<String,Local> next = new TreeMap<>();
            Map<String,Command> commands = new TreeMap<>();
            Map<String,Control> nextQueuedControls = new TreeMap<>();
            for (var spec : specs.values()) {
                Command command = decide(spec,specs,models,profiles,
                        physicallyAdvanced,sensed.get(spec.id()),assigned.get(spec.id()),
                        scenario.world(),completed);
                Local own = physicallyAdvanced.get(spec.id());
                next.put(spec.id(),new Local(own.state(),
                        command.decision().nextMemory(),sensed.get(spec.id()).tracks()));
                commands.put(spec.id(),command);
                nextQueuedControls.put(spec.id(),command.decision().controls());
            }
            for (var spec : specs.values()) {
                String id = spec.id();
                units.get(id).add(previous.get(id),next.get(id),commands.get(id),
                        completed,scenario.world());
                if (completed % stride == 0 || completed == scenario.ticks())
                    writeSlice(slices,scenario,completed,id,spec,
                            models.get(spec.typeId()).role(),next.get(id),commands.get(id),
                            appliedControls.get(id),completed == 1 ? -1 : completed-1);
            }
            for (var pair : pairs.values()) {
                pair.sample(previous.get(pair.a).state().position(),
                        previous.get(pair.b).state().position(),
                        next.get(pair.a).state().position(),
                        next.get(pair.b).state().position(),completed);
            }
            for (var asset : assets.values()) {
                FlightTwinScenario.Plane protectedUnit = specs.get(asset.id);
                Vec3 oldAsset = previous.get(asset.id).state().position();
                Vec3 newAsset = next.get(asset.id).state().position();
                double closestAtSample = Double.POSITIVE_INFINITY;
                double closestAlongTick = Double.POSITIVE_INFINITY;
                for (var hostile : specs.values()) {
                    if (hostile.team().equals(protectedUnit.team())) continue;
                    closestAtSample = Math.min(closestAtSample,
                            distance(newAsset,next.get(hostile.id()).state().position()));
                    closestAlongTick = Math.min(closestAlongTick,
                            segmentApproach(oldAsset,previous.get(hostile.id()).state().position(),
                                    newAsset,next.get(hostile.id()).state().position()));
                }
                asset.sampleThreat(closestAtSample,closestAlongTick,completed);
                boolean someoneInterposed = false;
                for (var escort : scenario.escortAssets().entrySet()) {
                    if (!escort.getValue().equals(asset.id)) continue;
                    Command command = commands.get(escort.getKey());
                    if (command.targetId() != null) {
                        asset.escortAssignmentTicks++;
                        if (asset.firstEscortAssignment < 0) asset.firstEscortAssignment = completed;
                    }
                    // Segment between protectee and the physical hostile with
                    // this moving escort close to the direct line of approach.
                    Vec3 escortPosition = next.get(escort.getKey()).state().position();
                    for (var hostile : specs.values()) {
                        if (hostile.team().equals(protectedUnit.team())) continue;
                        Vec3 delta = next.get(hostile.id()).state().position().add(newAsset.scale(-1));
                        double lengthSq = delta.lengthSquared();
                        if (lengthSq < 1e-9) continue;
                        double param = escortPosition.add(newAsset.scale(-1)).dot(delta) / lengthSq;
                        if (param > 0 && param < 1
                                && distance(escortPosition,newAsset.add(delta.scale(param))) < 18) {
                            someoneInterposed = true;
                            break;
                        }
                    }
                }
                if (someoneInterposed) asset.interpositionTicks++;
                UnitStats bomber = units.get(asset.id);
                asset.bomberPath = bomber.path;
                asset.bomberGroundTicks = bomber.groundTicks;
                asset.bomberFinalSpeed = bomber.finalSpeed;
                asset.bomberFinalObjective = bomber.finalObjectiveDistance;
            }
            previous = next;
            queuedControls = nextQueuedControls;
        }
        List<String> gates = new ArrayList<>();
        int sampledBreaches = 0, within = 0, obsTicks = 0, memoryTicks = 0;
        int los = 0, fov = 0, range = 0;
        double minPairSampled = Double.POSITIVE_INFINITY, minPairSwept = Double.POSITIVE_INFINITY;
        for (var pair : pairs.values()) {
            minPairSampled = Math.min(minPairSampled,pair.minSampled);
            minPairSwept = Math.min(minPairSwept,pair.minSwept);
            sampledBreaches += pair.sweptUnderSix;
            if (!pair.safe()) gates.add("BODY_SEPARATION_LT6:" + pair.a + ":" + pair.b
                    + ":swept_ticks=" + pair.sweptUnderSix);
        }
        for (var asset : assets.values()) {
            within += asset.sweptWithin95;
            if (!asset.safe()) gates.add("B17_PROTECTION_BREACHED:" + asset.id
                    + ":swept_intrusion_ticks=" + asset.sweptWithin95);
        }
        for (var metric : units.values()) {
            obsTicks += metric.visibleTicks;
            memoryTicks += metric.memoryTicks;
            los += metric.losRejections;
            fov += metric.fovRejections;
            range += metric.rangeRejections;
            if (metric.groundTicks > 0)
                gates.add("TERRAIN_CONTACT:" + metric.plane.id() + ":ticks=" + metric.groundTicks);
            if (metric.fireCandidateTicks != 0)
                throw new IllegalStateException("Unverified projectiles unexpectedly advisory-active");
        }
        return new Report(scenario.id(),scenario.ticks(),specs.size(),
                (int) specs.values().stream().map(FlightTwinScenario.Plane::typeId).distinct().count(),
                obsTicks,memoryTicks,los,fov,range,
                scenario.ticks() * specs.size(),scenario.ticks() * specs.size(),
                minPairSampled,minPairSwept,sampledBreaches,within,List.copyOf(gates),
                List.copyOf(units.values()),List.copyOf(pairs.values()),List.copyOf(assets.values()),
                scenario.environmentLabel());
    }

    /**
     * Coordination uses only individually acquired tracks, never an omniscient
     * enemy list. Assignment load is shared but cannot invent visibility.
     * Sorted tie-breaking and previously assigned hysteresis ensure replay.
     */
    private static Map<String,String> targetAssignments(
            Map<String,FlightTwinScenario.Plane> specs,
            Map<String,Local> snapshot,
            Map<String,FlightTwinSensor.Update> observations,
            long tick, Map<String,AircraftAtlasMain.Entry> models) {
        Map<String,String> result = new TreeMap<>();
        Map<String,Integer> load = new HashMap<>();
        List<FlightTwinScenario.Plane> ordered = new ArrayList<>(specs.values());
        ordered.sort(Comparator.comparing(FlightTwinScenario.Plane::team)
                .thenComparingInt(p->p.mission()==TacticalAirAI.Mission.ESCORT?0:1)
                .thenComparing(FlightTwinScenario.Plane::id));
        for (var spec : ordered) {
            if (!models.get(spec.typeId()).role().equals("fighter")) {
                result.put(spec.id(),null);
                continue;
            }
            String best = null;
            double bestScore = Double.POSITIVE_INFINITY;
            Vec3 own = snapshot.get(spec.id()).state().position();
            for (var entry : observations.get(spec.id()).tracks().entrySet()) {
                String hostileId = entry.getKey();
                FlightTwinSensor.Track track = entry.getValue();
                Vec3 enemy = track.extrapolate(tick);
                double fromOwn = distance(own,enemy);
                double age = tick-track.lastSeenTick();
                double score = fromOwn + 75 * load.getOrDefault(spec.team()+"|"+hostileId,0)
                        + 12 * age;
                if (spec.escortAsset() != null) {
                    Vec3 asset = snapshot.get(spec.escortAsset()).state().position();
                    score = 0.15 * fromOwn + 1.6 * distance(enemy,asset)
                            + 75 * load.getOrDefault(spec.team()+"|"+hostileId,0) + 12 * age;
                }
                if (score < bestScore-1e-9 || (Math.abs(score-bestScore) <= 1e-9
                        && (best == null || hostileId.compareTo(best) < 0))) {
                    bestScore = score;
                    best = hostileId;
                }
            }
            result.put(spec.id(),best);
            if (best != null) load.merge(spec.team()+"|"+best,1,Integer::sum);
        }
        return Collections.unmodifiableMap(result);
    }

    private static Command decide(
            FlightTwinScenario.Plane spec,
            Map<String,FlightTwinScenario.Plane> specs,
            Map<String,AircraftAtlasMain.Entry> models,
            Map<String,TacticalAirAI.Profile> profiles,
            Map<String,Local> snapshot,
            FlightTwinSensor.Update sensed, String assigned,
            World world, long now) {
        Local own = snapshot.get(spec.id());
        String threatId = assigned;
        if (threatId == null) {
            double closest = Double.POSITIVE_INFINITY;
            for (var entry : sensed.tracks().entrySet()) {
                double range = distance(own.state().position(),entry.getValue().extrapolate(now));
                if (range < closest-1e-9 || Math.abs(range-closest) <= 1e-9
                        && (threatId == null || entry.getKey().compareTo(threatId) < 0)) {
                    closest = range;
                    threatId = entry.getKey();
                }
            }
        }
        FlightTwinSensor.Track track = threatId == null ? null : sensed.tracks().get(threatId);
        TacticalAirAI.Contact opponent = track == null ? null :
                new TacticalAirAI.Contact(threatId,track.extrapolate(now),
                        track.lastVelocity(),true);
        // The real current enemy position is ONLY used for sensing. The
        // TacticalAirAI.Contact is constructed from an acquired/remembered track.
        int trackAge = track == null ? -1 : Math.toIntExact(now-track.lastSeenTick());
        String leaderId = spec.escortAsset();
        if (leaderId == null && spec.slot() > 0) {
            for (var fellow : specs.values())
                if (fellow.team().equals(spec.team())
                        && fellow.flight().equals(spec.flight()) && fellow.slot()==0) {
                    leaderId = fellow.id();
                    break;
                }
        }
        Vec3 anchor = null, anchorVelocity = Vec3.ZERO;
        if (leaderId != null) {
            State leader = snapshot.get(leaderId).state();
            anchorVelocity = leader.velocity();
            if (spec.escortAsset() != null && opponent != null) {
                anchor = leader.position();
            } else {
                Vec3 local = spec.escortAsset() == null
                        ? new Vec3(spec.slot() % 2 == 0 ? 26 : -26,5,-24)
                        : new Vec3(spec.slot() == 0 ? -40 : 40,24,18);
                Vec3 station = HistoricalDoctrineOrders.station(
                        leader.position(),leader.yawDeg(),local);
                anchor = spec.mission() == TacticalAirAI.Mission.ESCORT
                        ? station.add(0,-18,-24) : station.add(0,-4,-16);
            }
        }
        Vec3 nearestFriend = null;
        double nearestDist = Double.POSITIVE_INFINITY;
        int friendCount = 0;
        List<FlightSafetyPlanner.MovingObstacle> physicalContacts = new ArrayList<>();
        for (var other : specs.values()) {
            if (other.id().equals(spec.id()) || !other.team().equals(spec.team())) continue;
            friendCount++;
            State friendState = snapshot.get(other.id()).state();
            double d = distance(own.state().position(),friendState.position());
            if (d < nearestDist) { nearestDist = d; nearestFriend = friendState.position(); }
            physicalContacts.add(new FlightSafetyPlanner.MovingObstacle(
                    other.id(),friendState.position(),friendState.velocity(),BODY,false));
        }
        // Only tracks currently visible enter instantaneous hostile avoidance.
        // Stale memory can direct pursuit, but cannot become perfect obstacle state.
        for (String hostileId : sensed.currentlyVisible()) {
            var hostile = sensed.tracks().get(hostileId);
            physicalContacts.add(new FlightSafetyPlanner.MovingObstacle(
                    hostileId,hostile.lastPosition(),hostile.lastVelocity(),BODY,true));
        }
        double terrainHeight = world.groundHeight(
                own.state().position().x(),own.state().position().z());
        TacticalAirAI.Frame frame = new TacticalAirAI.Frame(
                profiles.get(spec.typeId()),models.get(spec.typeId()).model(),
                own.state(),spec.mission(),spec.objective(),spec.home(),opponent,
                anchor,nearestFriend,spec.fuelFraction(),1.0,terrainHeight,
                false,0.0,anchorVelocity);
        FlightSafetyPlanner.Environment environment = new FlightSafetyPlanner.Environment(
                world::groundHeight,physicalContacts,BODY);
        FlightControlLoop.Output result = FlightControlLoop.step(
                new FlightControlLoop.Input(frame,own.policyMemory(),null,environment));
        return new Command(result.decision(),result.safety(),assigned,threatId,
                trackAge,friendCount,nearestDist,sensed);
    }

    /**
     * A one-tick segment approach is a conservative additional centre-spacing
     * diagnostic. It cannot stand in for a swept Minecraft collider.
     */
    private static double segmentApproach(Vec3 oldA, Vec3 oldB, Vec3 newA, Vec3 newB) {
        Vec3 start = oldA.add(oldB.scale(-1));
        Vec3 relativeMotion = newA.add(oldA.scale(-1))
                .add(newB.add(oldB.scale(-1)).scale(-1));
        double denom = relativeMotion.lengthSquared();
        double fraction = denom < 1e-12 ? 0.0
                : Math.max(0,Math.min(1,-start.dot(relativeMotion) / denom));
        return start.add(relativeMotion.scale(fraction)).length();
    }
    private static double length(Vec3 v) { return v.length(); }
    private static double distance(Vec3 a, Vec3 b) {
        return length(a.add(b.scale(-1)));
    }
    private static boolean finite(Vec3 v) {
        return v != null && Double.isFinite(v.x())
                && Double.isFinite(v.y()) && Double.isFinite(v.z());
    }
    private static void checkRole(String role, TacticalAirAI.Mission mission) {
        if (mission == TacticalAirAI.Mission.LEVEL_BOMB && !role.equals("bomber")
                || mission == TacticalAirAI.Mission.DIVE_BOMB && !role.equals("attacker")
                || mission == TacticalAirAI.Mission.TORPEDO && !role.equals("torpedo_bomber")
                || mission == TacticalAirAI.Mission.STRAFE && !Set.of("fighter","attacker").contains(role)
                || mission == TacticalAirAI.Mission.ESCORT && !role.equals("fighter"))
            throw new IllegalArgumentException("Mission incompatible with aircraft role: "+role);
    }

    private static BufferedWriter writer(Path output, String name) throws IOException {
        return Files.newBufferedWriter(output.resolve(name),StandardCharsets.UTF_8);
    }
    private static void headers(BufferedWriter units,BufferedWriter pairs,
                                BufferedWriter assets,BufferedWriter slices,
                                BufferedWriter sensors) throws IOException {
        units.write("schema,scenario,unit_id,aircraft_id,role,team,mission,engine_reaction_ticks,"
                + "path_blocks,displacement_blocks,initial_speed_bps,final_speed_bps,"
                + "final_objective_distance,min_clearance_blocks,ground_ticks,"
                + "visible_contact_ticks,first_visible_tick,stale_track_ticks,"
                + "first_stale_tick,track_expiration_events,los_blocked_observations,"
                + "fov_blocked_observations,range_blocked_observations,"
                + "assigned_target_ticks,first_assignment_tick,collision_avoidance_ticks,"
                + "terrain_safety_ticks,safety_override_ticks,decision_changes,"
                + "advisory_fire_ticks\n");
        pairs.write("schema,scenario,first_unit,second_unit,initial_separation_blocks,"
                + "min_sampled_separation_blocks,min_swept_center_separation_blocks,"
                + "sampled_lt6_ticks,swept_lt6_ticks,closest_sampled_tick,"
                + "closest_swept_tick,final_separation_blocks,body_gate\n");
        assets.write("schema,scenario,asset_unit,protection_radius_blocks,"
                + "initial_closest_hostile_blocks,min_sampled_hostile_blocks,"
                + "min_swept_hostile_blocks,within95_sampled_ticks,"
                + "within95_swept_ticks,first_intrusion_sampled_tick,"
                + "first_intrusion_swept_tick,escort_target_assignment_ticks,"
                + "first_escort_assignment_tick,interposition_ticks,"
                + "bomber_path_blocks,bomber_ground_ticks,bomber_final_speed_bps,"
                + "bomber_final_objective_distance,protection_gate\n");
        slices.write("schema,scenario,tick,seconds,unit_id,aircraft_id,role,team,"
                + "x,y,z,vx,vy,vz,speed_bps,yaw_deg,pitch_deg,roll_deg,"
                + "engine_target,engine_power,ground_y,clearance_blocks,on_ground,"
                + "nearest_ally_blocks,team_known_count,visible_hostiles_count,"
                + "stale_tracks_count,los_rejected_count,fov_rejected_count,"
                + "out_of_range_count,target_id,observed_contact_id,contact_age_ticks,"
                + "maneuver,reason_code,safety_reason,control_x,control_z,control_throttle,"
                + "applied_control_x,applied_control_z,applied_control_throttle,"
                + "applied_control_from_policy_tick,command_generated_at_end_tick\n");
        sensors.write("schema,scenario,tick,observer_id,hostile_id,previous_visibility,"
                + "visibility,track_available,current_observation,track_age_ticks,"
                + "track_expired,range_blocks,nose_dot,ray_clearance_blocks\n");
    }

    private static void writeUnit(BufferedWriter w,String scene,UnitStats m) throws IOException {
        w.write(String.join(",", SCHEMA,scene,m.plane.id(),m.plane.typeId(),
                m.role,
                m.plane.team(),m.plane.mission().name(),Integer.toString(m.reactionTicks),
                n(m.path),n(distance(m.start,m.finalPosition)),
                n(m.initialSpeed),n(m.finalSpeed),n(m.finalObjectiveDistance),
                n(m.minClearance),Integer.toString(m.groundTicks),
                Integer.toString(m.visibleTicks),Integer.toString(m.firstVisible),
                Integer.toString(m.memoryTicks),Integer.toString(m.firstRemembered),
                Integer.toString(m.expiredTracks),Integer.toString(m.losRejections),
                Integer.toString(m.fovRejections),Integer.toString(m.rangeRejections),
                Integer.toString(m.assignedTicks),Integer.toString(m.firstTargetAssignment),
                Integer.toString(m.avoidanceTicks),Integer.toString(m.terrainSafetyTicks),
                Integer.toString(m.safetyOverrides),Integer.toString(m.decisionChanges),
                Integer.toString(m.fireCandidateTicks)));
        w.write('\n');
    }

    private static void writePair(BufferedWriter w,String scene,PairStats p) throws IOException {
        w.write(String.join(",",SCHEMA,scene,p.a,p.b,n(p.initial),n(p.minSampled),n(p.minSwept),
                Integer.toString(p.sampledUnderSix),Integer.toString(p.sweptUnderSix),
                Integer.toString(p.closestTick),Integer.toString(p.sweptClosestTick),
                n(p.finalDistance),p.safe()?"PASS":"FAILED"));
        w.write('\n');
    }

    private static void writeAsset(BufferedWriter w,String scene,AssetStats a) throws IOException {
        w.write(String.join(",",SCHEMA,scene,a.id,n(B17),n(a.initialHostile),n(a.minSampled),
                n(a.minSwept),Integer.toString(a.within95),Integer.toString(a.sweptWithin95),
                Integer.toString(a.firstEntry),Integer.toString(a.firstSweptEntry),
                Integer.toString(a.escortAssignmentTicks),Integer.toString(a.firstEscortAssignment),
                Integer.toString(a.interpositionTicks),n(a.bomberPath),
                Integer.toString(a.bomberGroundTicks),n(a.bomberFinalSpeed),
                n(a.bomberFinalObjective),a.safe()?"PASS":"FAILED"));
        w.write('\n');
    }

    private static void writeSlice(BufferedWriter w,FlightTwinScenario.Case scene,int tick,
                                   String id,FlightTwinScenario.Plane spec,String role,
                                   Local own,Command command,Control applied,
                                   int appliedPolicyTick) throws IOException {
        State s = own.state();
        double ground = scene.world().groundHeight(s.position().x(),s.position().z());
        FlightTwinSensor.Update sensor = command == null ? null : command.sensed();
        TacticalAirAI.Decision decision = command == null ? null : command.decision();
        // t0 is BEFORE the first policy call, hence no queued policy command.
        // First physics tick uses INITIAL neutral raw stick and initial engine
        // target; that is reported separately as physical actuation.
        Control control = decision == null ? Control.neutral(0) : decision.controls();
        w.write(String.join(",",SCHEMA,scene.id(),Integer.toString(tick),n(tick/20.0),
                id,spec.typeId(),role,spec.team(),
                n(s.position().x()),n(s.position().y()),n(s.position().z()),
                n(s.velocity().x()),n(s.velocity().y()),n(s.velocity().z()),
                n(s.velocity().length()*20),
                n(s.yawDeg()),n(s.pitchDeg()),n(s.rollDeg()),
                n(s.engineTarget()),n(s.enginePowerSmooth()),n(ground),
                n(s.position().y()-ground),Boolean.toString(s.onGround()),
                command == null ? "" : optional(command.nearestFriendly()),
                command == null ? "0" : Integer.toString(command.friendCount()),
                sensor == null ? "0" : Integer.toString(sensor.currentlyVisible().size()),
                sensor == null ? "0" : Integer.toString(sensor.rememberedCount()),
                sensor == null ? "0" : Integer.toString(sensor.losRejected()),
                sensor == null ? "0" : Integer.toString(sensor.fovRejected()),
                sensor == null ? "0" : Integer.toString(sensor.rangeRejected()),
                command == null ? "" : safeText(command.targetId()),
                command == null ? "" : safeText(command.observedContactId()),
                command == null ? "-1" : Integer.toString(command.contactAge()),
                decision == null ? "INITIAL" : decision.maneuver().name(),
                decision == null ? "INITIAL" : decision.reasonCode(),
                command == null ? "INITIAL" : command.safety().reason().name(),
                n(control.x()),n(control.z()),n(control.engineTarget()),
                applied == null ? "" : n(applied.x()),
                applied == null ? "" : n(applied.z()),
                applied == null ? "" : n(applied.engineTarget()),
                Integer.toString(appliedPolicyTick),
                decision == null ? "-1" : Integer.toString(tick)));
        w.write('\n');
    }

    private static void writeSensorEvent(BufferedWriter w,String scene,int tick,String observer,
                                         String hostile,FlightTwinSensor.Visibility before,
                                         FlightTwinSensor.Assessment now,
                                         FlightTwinSensor.Track track,boolean expired) throws IOException {
        int age = track == null ? -1 : Math.toIntExact(tick-track.lastSeenTick());
        w.write(String.join(",",SCHEMA,scene,Integer.toString(tick),observer,hostile,
                before == null ? "INITIAL" : before.name(),now.visibility().name(),
                Boolean.toString(track != null),Boolean.toString(now.visible()),
                Integer.toString(age),Boolean.toString(expired),n(now.rangeBlocks()),
                n(now.noseDot()),optional(now.sampledRayMinClearance())));
        w.write('\n');
    }

    private static void writeSummary(Path file,Options options,List<Report> reports)
            throws IOException {
        try (BufferedWriter w = Files.newBufferedWriter(file,StandardCharsets.UTF_8)) {
            w.write("{\n  \"schema\":"+q(SCHEMA)
                    +",\n  \"evidence\":"+q(EVIDENCE)
                    +",\n  \"kernel\":"+q("Ia133Microkernel.tickWithReaction")
                    +",\n  \"wind\":"+q("PinnedIa133WindWorld.calmAirCalibration().windAfterFriction")
                    +",\n  \"visibility\":"+q("FINITE_RANGE_3D_FOV_ANALYTIC_TERRAIN_RAYCAST_TRACK_TTL")
                    +",\n  \"seed\":"+q(Long.toString(options.seed()))
                    +",\n  \"tick_hz\":20"
                    +",\n  \"actuation_phase\":"
                    +q("ENTITY_PHYSICS_WITH_PREVIOUS_QUEUED_INPUT_THEN_SERVER_TICK_END_OBSERVE_AND_QUEUE_NEXT")
                    +",\n  \"first_physics_input\":"
                    +q("INITIAL_NEUTRAL_STICK_ENGINE_TARGET_1_NO_POLICY_YET")
                    +",\n  \"body_separation_radius_blocks\":"+n(BODY)
                    +",\n  \"b17_protection_radius_blocks\":"+n(B17)
                    +",\n  \"source_geometry\":"+q("CombatSimulationSelfTest.original_2v2/B17_aft/B17_prepositioned")
                    +",\n  \"all24_team_assignment\":"
                    +q("EXPLICIT_SCENARIO_OPERATOR_12V12_BLUE_SET; NO_NATIONALITY_OR_FACTION_INFERENCE")
                    +",\n  \"aircraft_anchor_sha256\":"
                    +q(WarfareWingsAircraft.WARFARE_WINGS_ANCHOR_SHA256)
                    +",\n  \"sensor\":{\"range_blocks\":"+n(SENSOR.rangeBlocks())
                    +",\"fov_half_angle_degrees\":"+n(SENSOR.halfConeDegrees())
                    +",\"memory_ticks\":"+SENSOR.trackLifetimeTicks()
                    +",\"terrain_samples\":"+SENSOR.terrainSamples()
                    +",\"ray_margin_blocks\":"+n(SENSOR.terrainMarginBlocks())+"}"
                    +",\n  \"scenario_count\":"+reports.size()
                    +",\n  \"simulated_source_ticks\":"
                    +reports.stream().mapToInt(Report::sourcePhysicsTicks).sum()
                    +",\n  \"scenarios\":[\n");
            for (int i=0;i<reports.size();i++) {
                Report r=reports.get(i);
                if (i>0) w.write(",\n");
                w.write("    {\"id\":"+q(r.scenario())
                        +",\"status\":"+q(r.status())
                        +",\"simulated_ticks\":"+r.ticks()
                        +",\"active_aircraft\":"+r.aircraftCount()
                        +",\"unique_aircraft_types\":"+r.uniqueAircraftTypes()
                        +",\"simultaneous_source_updates\":"+r.sourcePhysicsTicks()
                        +",\"observed_hostile_ticks\":"+r.observedTicks()
                        +",\"remembered_hostile_ticks\":"+r.rememberedTicks()
                        +",\"los_rejected_observations\":"+r.terrainBlockedObservations()
                        +",\"fov_rejected_observations\":"+r.fovBlockedObservations()
                        +",\"range_rejected_observations\":"+r.rangeBlockedObservations()
                        +",\"total_ai_decisions\":"+r.totalDecisions()
                        +",\"min_sampled_pair_separation_blocks\":"+n(r.minPairSampled())
                        +",\"min_swept_pair_separation_blocks\":"+n(r.minPairSwept())
                        +",\"swept_lt6_pair_ticks\":"+r.sixBreaches()
                        +",\"swept_within95_hostile_ticks\":"+r.ninetyFiveBreaches()
                        +",\"environment\":"+q(r.terrain())
                        +",\"failed_operational_gates\":[");
                for (int k=0;k<r.failedGates().size();k++) {
                    if (k>0) w.write(",");
                    w.write(q(r.failedGates().get(k)));
                }
                w.write("]}");
            }
            w.write("\n  ],\n  \"limitations\":["
                    +q("Terrain LOS is sampled analytic height, not Minecraft voxel clip")+","
                    +q("Separation uses centres plus conservative within-tick linear sweep, not full hitboxes")+","
                    +q("Friendly team positions are an idealized independent channel")+","
                    +q("No weapons, damage, victories, Forge authority, chunk or network simulation")+","
                    +q("Safety failures are explicitly reported without changing 6/95 block thresholds")
                    +"]\n}\n");
        }
    }

    private static void validateAnchor(Path csv) throws IOException {
        List<String> lines=Files.readAllLines(csv,StandardCharsets.UTF_8);
        if (lines.size()!=25) throw new IllegalArgumentException("Expected 24 ANCHOR rows");
        String[] headers=lines.get(0).split(",",-1);
        int index=-1;
        for (int i=0;i<headers.length;i++) if (headers[i].equals("anchor_sha256")) index=i;
        if (index<0) throw new IllegalArgumentException("Missing ANCHOR hash column");
        for (int i=1;i<lines.size();i++) {
            String[] values=lines.get(i).split(",",-1);
            if (index>=values.length || !values[index].equals(
                    WarfareWingsAircraft.WARFARE_WINGS_ANCHOR_SHA256))
                throw new IllegalArgumentException("Mismatched ANCHOR provenance row "+i);
        }
    }
    private static String n(double value) {
        if (!Double.isFinite(value)) throw new IllegalArgumentException("Nonfinite twin metric");
        return String.format(Locale.ROOT,"%.9f",value);
    }
    private static String optional(double value) {
        return Double.isFinite(value) ? n(value) : "";
    }
    private static String safeText(String value) { return value == null ? "" : value; }
    private static String q(String value) {
        StringBuilder builder=new StringBuilder("\"");
        for (int i=0;i<value.length();i++) {
            char c=value.charAt(i);
            switch (c) {
                case '"' -> builder.append("\\\"");
                case '\\' -> builder.append("\\\\");
                case '\r' -> builder.append("\\r");
                case '\n' -> builder.append("\\n");
                case '\t' -> builder.append("\\t");
                default -> {
                    if (c<32) builder.append(String.format(Locale.ROOT,"\\u%04x",(int)c));
                    else builder.append(c);
                }
            }
        }
        return builder.append('"').toString();
    }
}
