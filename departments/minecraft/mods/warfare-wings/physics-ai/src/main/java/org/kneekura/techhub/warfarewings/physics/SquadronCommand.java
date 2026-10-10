package org.kneekura.techhub.warfarewings.physics;

import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;

import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;

/**
 * Deterministic synchronous 20 Hz squadron laboratory over the 24-aircraft source Atlas.
 *
 * A local pilot owns its physics state, decision memory and remembered enemy tracks.
 * A commander may coordinate target saturation within a team, but only from tracks
 * each pilot actually senses/remembers. Friendly locations are an idealized team
 * information channel for formation and collision checks; enemy locations are not.
 *
 * Sensing angles, station spacing, target load penalty and safety distances are
 * gameplay research assumptions, NOT measured historical or Minecraft parameters.
 * There are no weapons, damage, kills, mission victories or Forge runtime claims.
 */
public final class SquadronCommand {
    public static final String SCHEMA = "ww.squadron.source-simulation.v1";

    /** Explicit synthetic laboratory instrumentation, not an in-game sensor model. */
    public record Sensors(double rangeBlocks, double halfConeDegrees,
                          int trackLifetimeTicks, double fireCorridorRadiusBlocks) {
        public Sensors {
            if (!Double.isFinite(rangeBlocks) || rangeBlocks <= 0
                    || !Double.isFinite(halfConeDegrees) || halfConeDegrees <= 0 || halfConeDegrees > 180
                    || trackLifetimeTicks < 0 || trackLifetimeTicks > 100
                    || !Double.isFinite(fireCorridorRadiusBlocks) || fireCorridorRadiusBlocks <= 0)
                throw new IllegalArgumentException("invalid experimental sensor/safety parameters");
        }
        public static final Sensors DEFAULT = new Sensors(190, 150, 6, 9);
    }

    /**
     * An instance ID is different from the shared aircraft type ID. A type may
     * occur several times on opposing teams with fully independent state.
     * Only fighter pilots get air-to-air target assignments. The optional
     * projectile speed enables advisory firing windows, not weapon emulation.
     */
    public record AircraftSpec(
            String unitId, String aircraftTypeId, String team, String squadron,
            int slot, TacticalAirAI.Mission mission, String escortedUnitId,
            HistoricalDoctrineOrders.Order historicalOrder,
            Vec3 startPosition, Vec3 startVelocity, double startYawDeg,
            Vec3 objective, Vec3 home,
            double fuelFraction, double integrityFraction, double projectileSpeedBpt) {
        public AircraftSpec {
            nonblank(unitId, "unit"); nonblank(aircraftTypeId, "type");
            nonblank(team, "team"); nonblank(squadron, "squadron");
            if (slot < 0 || slot > 5 || mission == null || startPosition == null
                    || startVelocity == null || objective == null || home == null)
                throw new IllegalArgumentException("airframe specification");
            finite(startPosition); finite(startVelocity); finite(objective); finite(home);
            if (!Double.isFinite(startYawDeg) || !Double.isFinite(fuelFraction)
                    || fuelFraction < 0 || fuelFraction > 1
                    || !Double.isFinite(integrityFraction) || integrityFraction < 0 || integrityFraction > 1
                    || !Double.isFinite(projectileSpeedBpt) || projectileSpeedBpt < 0)
                throw new IllegalArgumentException("invalid initial state");
            if (escortedUnitId != null && escortedUnitId.isBlank())
                throw new IllegalArgumentException("blank escorted unit ID");
            if (historicalOrder != null && historicalOrder.slot() != slot)
                throw new IllegalArgumentException("doctrine order must match slot");
        }
    }

    /** Each observer owns its own timed observation; never globally shared. */
    public record Track(Vec3 position, Vec3 velocity, long lastSeenTick) {
        public Track {
            if (position == null || velocity == null || lastSeenTick < 0)
                throw new IllegalArgumentException("track");
            finite(position); finite(velocity);
        }
        public Vec3 extrapolated(long now) {
            if (now < lastSeenTick) throw new IllegalArgumentException("reverse clock");
            return position.add(velocity.scale(now - lastSeenTick));
        }
    }

    public record Local(State aircraft, TacticalAirAI.Memory decisionMemory,
                        Map<String, Track> tracks, String assignedTargetId) {
        public Local {
            if (aircraft == null || decisionMemory == null || tracks == null)
                throw new IllegalArgumentException("local state");
            tracks = frozen(tracks);
        }
    }

    public record Snapshot(long tick, Map<String, Local> units) {
        public Snapshot {
            if (tick < 0 || units == null) throw new IllegalArgumentException("snapshot");
            units = frozen(units);
        }
    }

    /** Both the chosen target and firing window are only advisory. */
    public record Instruction(
            String unitId, String assignedTargetId, String threatContactId,
            TacticalAirAI.Decision decision, boolean observedTargetThisTick,
            boolean friendlyFireCorridorClear, Vec3 formationAnchor, double nearestFriendlyDistance,
            FlightSafetyPlanner.Clearance safetyClearance) {}

    public record Step(Snapshot next, Map<String, Instruction> commands) {
        public Step {
            if (next == null || commands == null) throw new IllegalArgumentException("step");
            commands = frozen(commands);
        }
    }

    private final Map<String, AircraftSpec> specifications;
    private final Map<String, AircraftAtlasMain.Entry> models;
    private final Map<String, TacticalAirAI.Profile> profiles;
    private final Map<String, String> leaders;
    private final World world;
    private final Sensors sensors;

    private SquadronCommand(Map<String, AircraftSpec> specifications,
                            Map<String, AircraftAtlasMain.Entry> models,
                            Map<String, TacticalAirAI.Profile> profiles,
                            Map<String, String> leaders, World world, Sensors sensors) {
        this.specifications = frozen(specifications);
        this.models = frozen(models);
        this.profiles = frozen(profiles);
        this.leaders = frozen(leaders);
        this.world = world;
        this.sensors = sensors;
    }

    public static SquadronCommand load(Path anchorCsv, List<AircraftSpec> aircraft,
                                        World world, Sensors sensors) throws IOException {
        if (anchorCsv == null || aircraft == null || aircraft.isEmpty()
                || world == null || sensors == null) throw new IllegalArgumentException("scenario");

        List<AircraftAtlasMain.Entry> source = AircraftAtlasMain.load(anchorCsv);
        if (source.size() != 24) throw new IllegalArgumentException("expected 24 source-Atlas aircraft");
        Map<String, AircraftAtlasMain.Entry> catalog = new TreeMap<>();
        Map<String, TacticalAirAI.Profile> profiles = new TreeMap<>();
        for (AircraftAtlasMain.Entry entry : source) {
            catalog.put(entry.aircraftId(), entry);
            profiles.put(entry.aircraftId(),
                    TacticalAirAI.Profile.fromAtlas(AircraftAtlasMain.evaluate(entry)));
        }

        Map<String, AircraftSpec> units = new TreeMap<>();
        Map<String, String> leaders = new TreeMap<>();
        Map<String, Set<Integer>> slots = new TreeMap<>();
        for (AircraftSpec spec : aircraft) {
            if (spec == null || units.putIfAbsent(spec.unitId(), spec) != null)
                throw new IllegalArgumentException("missing or duplicate unit");
            AircraftAtlasMain.Entry type = catalog.get(spec.aircraftTypeId());
            if (type == null) throw new IllegalArgumentException("unknown 24-Atlas type: " + spec.aircraftTypeId());
            checkMissionRole(type.role(), spec.mission());
            checkDoctrine(spec, type.role());

            String flight = flightId(spec);
            if (!slots.computeIfAbsent(flight, ignored -> new HashSet<>()).add(spec.slot()))
                throw new IllegalArgumentException("duplicate flight slot: " + flight + " / " + spec.slot());
            if (spec.slot() == 0 && leaders.putIfAbsent(flight, spec.unitId()) != null)
                throw new IllegalArgumentException("duplicate leader");
        }
        for (AircraftSpec spec : units.values()) {
            if (!leaders.containsKey(flightId(spec)))
                throw new IllegalArgumentException("squadron has no slot-0 leader: " + flightId(spec));
            if (spec.escortedUnitId() != null) {
                AircraftSpec escorted = units.get(spec.escortedUnitId());
                if (escorted == null || escorted.unitId().equals(spec.unitId())
                        || !escorted.team().equals(spec.team())
                        || spec.mission() != TacticalAirAI.Mission.ESCORT)
                    throw new IllegalArgumentException("escort must reference a separate allied unit");
            }
        }
        return new SquadronCommand(units, catalog, profiles, leaders, world, sensors);
    }

    public int supportedAircraftTypes() { return profiles.size(); }

    public Snapshot start() {
        Map<String, Local> units = new TreeMap<>();
        for (AircraftSpec spec : specifications.values()) {
            State state = new State(0, spec.startPosition(), spec.startVelocity(),
                    spec.startYawDeg(), 0, 0, 0, 0, 0, 0, 0, 0,
                    1, 0, 1, 0, false, false);
            units.put(spec.unitId(), new Local(state, TacticalAirAI.Memory.INITIAL, Map.of(), null));
        }
        return new Snapshot(0, units);
    }

    /** One decision and one physics integration for every unit, using one frozen prior tick. */
    public Step advance(Snapshot previous) {
        if (previous == null || !previous.units().keySet().equals(specifications.keySet()))
            throw new IllegalArgumentException("snapshot must contain the exact scenario roster");
        long now = previous.tick();
        if (now == Long.MAX_VALUE) throw new IllegalArgumentException("tick overflow");
        for (Local local : previous.units().values())
            if (local.aircraft().tick() != now) throw new IllegalArgumentException("mixed snapshot ticks");

        // Read-only snapshots make input-list order and sibling update order irrelevant.
        Map<String, Map<String, Track>> sensed = new TreeMap<>();
        for (AircraftSpec spec : specifications.values())
            sensed.put(spec.unitId(), observe(spec, previous, now));

        Map<String, String> assignments = assign(previous, sensed, now);
        Map<String, Local> next = new TreeMap<>();
        Map<String, Instruction> instructions = new TreeMap<>();
        for (AircraftSpec spec : specifications.values()) {
            Local own = previous.units().get(spec.unitId());
            Map<String, Track> tracks = sensed.get(spec.unitId());
            String targetId = assignments.get(spec.unitId());
            String threatId = targetId != null ? targetId : nearestThreat(own.aircraft(), tracks, now);
            Track target = threatId == null ? null : tracks.get(threatId);
            TacticalAirAI.Contact contact = target == null ? null
                    : new TacticalAirAI.Contact(threatId, target.extrapolated(now), target.velocity(), true);

            Vec3 anchor = formationAnchor(spec, previous);
            double closest = Double.POSITIVE_INFINITY;
            Vec3 closestPos = null;
            for (AircraftSpec ally : specifications.values()) {
                if (ally.unitId().equals(spec.unitId()) || !ally.team().equals(spec.team())) continue;
                Vec3 position = previous.units().get(ally.unitId()).aircraft().position();
                double separation = own.aircraft().position().add(position.scale(-1)).length();
                if (separation < closest) { closest = separation; closestPos = position; }
            }
            // Never open a firing window on a stale target or across another friendly.
            boolean recent = target != null && target.lastSeenTick() == now;
            boolean corridor = recent && clearFireCorridor(spec, own.aircraft().position(),
                    target.position(), previous);
            Model model = models.get(spec.aircraftTypeId()).model();
            TacticalAirAI.Frame frame = new TacticalAirAI.Frame(
                    profiles.get(spec.aircraftTypeId()), model, own.aircraft(), spec.mission(),
                    spec.objective(), spec.home(), contact, anchor, closestPos,
                    spec.fuelFraction(), spec.integrityFraction(),
                    world.groundHeight(own.aircraft().position().x(), own.aircraft().position().z()),
                    corridor, spec.projectileSpeedBpt());
            // Only teammates enter the world-safety obstacle channel. Unseen
            // hostiles cannot leak their actual positions into a pilot's plan.
            List<FlightSafetyPlanner.MovingObstacle> obstacles = new ArrayList<>();
            for (AircraftSpec ally : specifications.values()) {
                if (ally.unitId().equals(spec.unitId()) || !ally.team().equals(spec.team())) continue;
                State teammate = previous.units().get(ally.unitId()).aircraft();
                obstacles.add(new FlightSafetyPlanner.MovingObstacle(ally.unitId(),
                        teammate.position(), teammate.velocity(), 6));
            }
            FlightSafetyPlanner.Environment environment = new FlightSafetyPlanner.Environment(
                    world::groundHeight, obstacles, 6);
            HistoricalDoctrineOrders.Order order = spec.historicalOrder();
            if (order != null && anchor != null) {
                String leaderId = spec.escortedUnitId() != null
                        ? spec.escortedUnitId() : leaders.get(flightId(spec));
                // The historical order's heading is an *observation*, refreshed
                // from the current leader each tick as the formation turns.
                double actualYaw = previous.units().get(leaderId).aircraft().yawDeg();
                order = new HistoricalDoctrineOrders.Order(
                        order.pattern(), order.slot(), actualYaw, order.scenarioYear());
            }
            FlightControlLoop.Output loop = FlightControlLoop.step(new FlightControlLoop.Input(
                    frame, own.decisionMemory(), order, environment));
            TacticalAirAI.Decision decision = loop.decision();
            State after = Ia133Microkernel.tick(model, own.aircraft(), decision.controls(), world);
            finite(after.position()); finite(after.velocity());
            if (!Double.isFinite(after.yawDeg()) || !Double.isFinite(after.pitchDeg()))
                throw new IllegalStateException("non-finite heading: " + spec.unitId());

            next.put(spec.unitId(), new Local(after, decision.nextMemory(), tracks, targetId));
            instructions.put(spec.unitId(), new Instruction(
                    spec.unitId(), targetId, threatId, decision, recent, corridor, anchor, closest,
                    loop.safety()));
        }
        return new Step(new Snapshot(now + 1, next), instructions);
    }

    private Map<String, Track> observe(AircraftSpec self, Snapshot previous, long now) {
        Local own = previous.units().get(self.unitId());
        Map<String, Track> tracks = new TreeMap<>();
        for (Map.Entry<String, Track> entry : own.tracks().entrySet()) {
            AircraftSpec target = specifications.get(entry.getKey());
            if (target == null || target.team().equals(self.team()))
                throw new IllegalArgumentException("unexpected friendly/unknown track");
            if (entry.getValue().lastSeenTick() <= now
                    && now - entry.getValue().lastSeenTick() <= sensors.trackLifetimeTicks())
                tracks.put(entry.getKey(), entry.getValue());
        }
        Vec3 position = own.aircraft().position();
        Vec3 forward = Ia133Microkernel.forward(own.aircraft().yawDeg(), own.aircraft().pitchDeg());
        double threshold = Math.cos(Math.toRadians(sensors.halfConeDegrees()));
        for (AircraftSpec target : specifications.values()) {
            if (target.team().equals(self.team())) continue;
            State other = previous.units().get(target.unitId()).aircraft();
            Vec3 delta = other.position().add(position.scale(-1));
            double distance = delta.length();
            if (distance > 1e-9 && distance <= sensors.rangeBlocks()
                    && forward.dot(delta.scale(1.0 / distance)) >= threshold)
                tracks.put(target.unitId(), new Track(other.position(), other.velocity(), now));
        }
        return frozen(tracks);
    }

    /** Team commander assigns only sensor-known opponents, with deterministic load balancing. */
    private Map<String, String> assign(Snapshot previous,
                                        Map<String, Map<String, Track>> sensed, long now) {
        Map<String, String> assignments = new TreeMap<>();
        Map<String, Integer> load = new HashMap<>();
        List<AircraftSpec> order = new ArrayList<>(specifications.values());
        order.sort(Comparator
                .comparing(AircraftSpec::team)
                .thenComparingInt(spec -> spec.mission() == TacticalAirAI.Mission.ESCORT ? 0 : 1)
                .thenComparing(AircraftSpec::unitId));
        for (AircraftSpec spec : order) {
            if (!models.get(spec.aircraftTypeId()).role().equals("fighter")) {
                assignments.put(spec.unitId(), null);
                continue;
            }
            String best = null;
            double bestScore = Double.POSITIVE_INFINITY;
            Vec3 here = previous.units().get(spec.unitId()).aircraft().position();
            for (Map.Entry<String, Track> contact : sensed.get(spec.unitId()).entrySet()) {
                String hostile = contact.getKey();
                Track track = contact.getValue();
                Vec3 believed = track.extrapolated(now);
                double distance = believed.add(here.scale(-1)).length();
                int already = load.getOrDefault(spec.team() + "/" + hostile, 0);
                double score = distance + already * 75.0
                        + (now - track.lastSeenTick()) * 12.0;
                if (hostile.equals(previous.units().get(spec.unitId()).assignedTargetId()))
                    score -= 22; // keep a track unless a stronger reason to redistribute
                if (spec.mission() == TacticalAirAI.Mission.ESCORT && spec.escortedUnitId() != null) {
                    Vec3 protectedPos = previous.units().get(spec.escortedUnitId()).aircraft().position();
                    score = 0.15 * distance + 1.6 * believed.add(protectedPos.scale(-1)).length()
                            + already * 75.0 + (now - track.lastSeenTick()) * 12.0
                            - (hostile.equals(previous.units().get(spec.unitId()).assignedTargetId()) ? 22 : 0);
                }
                if (score < bestScore - 1e-9 || (Math.abs(score - bestScore) <= 1e-9
                        && (best == null || hostile.compareTo(best) < 0))) {
                    best = hostile;
                    bestScore = score;
                }
            }
            assignments.put(spec.unitId(), best);
            if (best != null) load.merge(spec.team() + "/" + best, 1, Integer::sum);
        }
        return assignments;
    }

    private static String nearestThreat(State own, Map<String, Track> tracks, long now) {
        String best = null;
        double distance = Double.POSITIVE_INFINITY;
        for (Map.Entry<String, Track> enemy : tracks.entrySet()) {
            double d = enemy.getValue().extrapolated(now)
                    .add(own.position().scale(-1)).length();
            if (d < distance - 1e-9 || (Math.abs(d - distance) <= 1e-9
                    && (best == null || enemy.getKey().compareTo(best) < 0))) {
                distance = d;
                best = enemy.getKey();
            }
        }
        return best;
    }

    private Vec3 formationAnchor(AircraftSpec self, Snapshot previous) {
        String anchorId = self.escortedUnitId() != null
                ? self.escortedUnitId() : leaders.get(flightId(self));
        if (self.unitId().equals(anchorId)) return null;
        State lead = previous.units().get(anchorId).aircraft();
        if (self.historicalOrder() != null
                && self.historicalOrder().pattern() != HistoricalDoctrineOrders.Pattern.NONE)
            return lead.position(); // historical pattern calculates its own unique slot
        Vec3 local = self.escortedUnitId() != null ? escortStation(self.slot()) : wingStation(self.slot());
        // Generic TacticalAirAI appends world-axis (0,4,16) on FORMATION_HOLD
        // and (0,18,24) on ESCORT_SCREEN. Cancel in world axes *after*
        // computing the heading-rotated station; this is deliberate even when
        // leader yaw != 0. Rotating the cancellation would miss the station.
        Vec3 station = HistoricalDoctrineOrders.station(lead.position(), lead.yawDeg(), local);
        return self.mission() == TacticalAirAI.Mission.ESCORT
                ? station.add(0, -18, -24) : station.add(0, -4, -16);
    }

    private static Vec3 wingStation(int slot) {
        if (slot == 0) return Vec3.ZERO;
        int rank = (slot + 1) / 2;
        return new Vec3((slot % 2 == 0 ? 1 : -1) * rank * 26, rank * 5, -rank * 24);
    }

    private static Vec3 escortStation(int slot) {
        int rank = slot / 2;
        return new Vec3((slot % 2 == 0 ? -1 : 1) * (40 + rank * 8),
                24 + rank * 6, rank == 0 ? 18 : -34);
    }

    private boolean clearFireCorridor(AircraftSpec shooter, Vec3 origin,
                                      Vec3 aim, Snapshot previous) {
        Vec3 segment = aim.add(origin.scale(-1));
        double lengthSq = segment.lengthSquared();
        if (lengthSq < 1e-9) return false;
        for (AircraftSpec ally : specifications.values()) {
            if (ally.unitId().equals(shooter.unitId()) || !ally.team().equals(shooter.team())) continue;
            Vec3 point = previous.units().get(ally.unitId()).aircraft().position();
            double t = point.add(origin.scale(-1)).dot(segment) / lengthSq;
            if (t < 0 || t > 1) continue;
            Vec3 closest = origin.add(segment.scale(t));
            if (point.add(closest.scale(-1)).length() < sensors.fireCorridorRadiusBlocks())
                return false;
        }
        return true;
    }

    private static String flightId(AircraftSpec spec) { return spec.team() + "/" + spec.squadron(); }

    private static void checkMissionRole(String role, TacticalAirAI.Mission mission) {
        if (mission == TacticalAirAI.Mission.LEVEL_BOMB && !role.equals("bomber")
                || mission == TacticalAirAI.Mission.DIVE_BOMB && !role.equals("attacker")
                || mission == TacticalAirAI.Mission.STRAFE
                    && !(role.equals("attacker") || role.equals("fighter"))
                || mission == TacticalAirAI.Mission.TORPEDO && !role.equals("torpedo_bomber"))
            throw new IllegalArgumentException("mission incompatible with source aircraft role: " + role);
    }

    private static void checkDoctrine(AircraftSpec spec, String role) {
        HistoricalDoctrineOrders.Order order = spec.historicalOrder();
        if (order == null || order.pattern() == HistoricalDoctrineOrders.Pattern.NONE) return;
        switch (order.pattern()) {
            case RAF_FINGER_FOUR_1940 -> { if (!role.equals("fighter") || spec.slot() > 3)
                throw new IllegalArgumentException("finger-four requires fighter slot 0..3"); }
            case USN_MUTUAL_SUPPORT_1942 -> { if (!role.equals("fighter") || spec.slot() > 1
                    || spec.aircraftTypeId().equals("warfare_wings:f6f") && order.scenarioYear() < 1943)
                throw new IllegalArgumentException("mutual support fighter pair/history"); }
            case USAAF_COMBAT_BOX_1943 -> { if (!role.equals("bomber")
                    || spec.mission() != TacticalAirAI.Mission.LEVEL_BOMB)
                throw new IllegalArgumentException("combat box requires level bomber"); }
            case USAAF_ESCORT_COVER_1944 -> { if (!role.equals("fighter")
                    || spec.mission() != TacticalAirAI.Mission.ESCORT || spec.slot() > 3)
                throw new IllegalArgumentException("escort pattern requires escort fighter slot 0..3"); }
            case NONE -> { }
        }
    }

    private static void finite(Vec3 v) {
        if (!Double.isFinite(v.x()) || !Double.isFinite(v.y()) || !Double.isFinite(v.z()))
            throw new IllegalArgumentException("non-finite position/vector");
    }

    private static void nonblank(String value, String label) {
        if (value == null || value.isBlank() || value.contains("/"))
            throw new IllegalArgumentException("invalid " + label + " identifier");
    }

    private static <T> Map<String, T> frozen(Map<String, T> source) {
        return Collections.unmodifiableMap(new TreeMap<>(source));
    }
}
