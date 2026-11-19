package org.kneekura.techhub.warfarewings.trace;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.server.ServerStoppingEvent;
import net.minecraftforge.fml.loading.FMLPaths;

import org.kneekura.techhub.warfarewings.physics.FlightControlLoop;
import org.kneekura.techhub.warfarewings.physics.FlightSafetyPlanner;
import org.kneekura.techhub.warfarewings.physics.HistoricalDoctrineOrders;
import org.kneekura.techhub.warfarewings.physics.Ia133Microkernel;
import org.kneekura.techhub.warfarewings.physics.RuntimeTacticalAtlas;
import org.kneekura.techhub.warfarewings.physics.TacticalAirAI;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;
import net.minecraft.world.phys.Vec3;

/**
 * Source-grounded server-side lab pilot for actual Warfare Wings entities.
 *
 * IA's tickPilot resets all non-local players' raw inputs to zero BEFORE the
 * controller. This listener runs at server END after the aircraft has ticked
 * and corrects IA's public InterpolatedFloat state for the NEXT physics tick.
 * Engine target is independently set through IA's existing setter. Thus a
 * command calculated at tick N affects aircraft dynamics at tick N+1.
 *
 * No entity position/rotation/velocity is directly overwritten and no
 * weapon is fired. These generated control traces are not runtime parity
 * proof until the staged exact aircraft/IA JARs actually execute.
 */
final class RuntimeTacticalPilot {
    static final String SCHEMA = "ww.physics.forge-tactical-pilot.v1";
    static final String GAME_TEST_ISOLATION_TAG = "ww_tactical_game_test";
    static final String LIVE_PAIR_TEST_TAG = "ww_live_pair_game_test";
    private static final int MAX_COMPLETED_RESULTS = 32;
    private static final long CONTACT_TRACK_TTL_TICKS = 6;
    private static final String HEADER =
            "schema_version,source,scenario_id,aircraft_id,sim_tick,game_time,"
            + "pos_x,pos_y,pos_z,vel_x,vel_y,vel_z,yaw_deg,pitch_deg,"
            + "engine_target,engine_power,smooth_x,smooth_z,"
            + "command_x,command_z,command_throttle,maneuver,reason,"
            + "world_safety_reason,terrain_clearance_blocks";
    private static final Map<UUID, Run> ACTIVE = new HashMap<>();
    // Bounded to avoid retaining stale runs and trace paths for the entire
    // dedicated-server lifetime. A completed scenario name may be rerun.
    private static final Map<String, Result> RESULTS = new LinkedHashMap<>();
    private static Map<String, RuntimeTacticalAtlas.Airframe> profiles;

    record Result(boolean complete, String failure, int samples, int nonzeroLateralTicks,
                  double yawTravelDeg, double displacementBlocks,
                  int firstCommandSample, int firstYawResponseSample, Path trace,
                  int observedContactTicks, int predictedContactTicks,
                  int escortTicks, int strikeIngressTicks, int strikeEgressTicks,
                  int returnTicks, double returnStartDistance, double closestReturnDistance) {}

    /** Immutable and entirely operator-assigned. Aircraft faction has no team meaning. */
    record LiveOrder(String team, TacticalAirAI.Mission mission,
                     Vec3 waypoint, Vec3 home, UUID designatedTarget,
                     String hostileTeam, UUID leader) {
        LiveOrder {
            if (!validTeam(team) || mission == null || !finite(waypoint) || !finite(home)
                    || hostileTeam != null && (!validTeam(hostileTeam) || hostileTeam.equals(team))
                    || leader != null && leader.equals(designatedTarget))
                throw new IllegalArgumentException("invalid explicit live aircraft orders");
        }
    }
    record LiveStatus(UUID aircraft, String aircraftType, String team,
                      TacticalAirAI.Mission mission, UUID target,
                      String hostileTeam, UUID leader, int observedTicks,
                      int elapsedTicks, int sensorCandidates, int blockedContacts,
                      int stationSlot, LiveMissionPlanner.Phase phase, int escortTicks) {}

    static boolean validTeam(String team) {
        return team != null && team.matches("[a-z][a-z0-9_-]{0,23}");
    }
    private static boolean finite(Vec3 p) {
        return p != null && Double.isFinite(p.x) && Double.isFinite(p.y) && Double.isFinite(p.z);
    }

    private RuntimeTacticalPilot() {}

    static synchronized Result result(String scenario) {
        return RESULTS.get(scenario);
    }

    private static void remember(Result result, String scenario) {
        RESULTS.remove(scenario);
        RESULTS.put(scenario, result);
        while (RESULTS.size() > MAX_COMPLETED_RESULTS)
            RESULTS.remove(RESULTS.keySet().iterator().next());
    }

    static synchronized boolean active(UUID aircraftId) {
        return ACTIVE.containsKey(aircraftId);
    }

    static synchronized List<LiveStatus> liveStatus() {
        List<LiveStatus> status = new ArrayList<>();
        for (Run run : ACTIVE.values()) {
            if (run.liveOrder == null) continue;
            LiveOrder order = run.liveOrder;
            status.add(new LiveStatus(run.aircraft.getUUID(), run.airframe.profile().aircraftId(),
                    order.team(), order.mission(), order.designatedTarget(),
                    order.hostileTeam(), order.leader(), run.observedTicks,
                    run.steps, run.sensorCandidates, run.blockedContacts,
                    run.stationSlot, run.livePhase, run.escortTicks));
        }
        status.sort(java.util.Comparator.comparing(s -> s.aircraft().toString()));
        return List.copyOf(status);
    }

    static synchronized boolean hasLiveTeam(UUID aircraft, String team) {
        Run run = ACTIVE.get(aircraft);
        return run != null && run.liveOrder != null && run.liveOrder.team().equals(team);
    }

    static synchronized LiveOrder liveOrder(UUID aircraft) {
        Run run = ACTIVE.get(aircraft);
        if (run == null || run.liveOrder == null)
            throw new IllegalArgumentException("Aircraft is not enrolled in live autonomy");
        return run.liveOrder;
    }

    static synchronized void requestReturn(UUID aircraft) {
        Run run = ACTIVE.get(aircraft);
        if (run == null || run.liveOrder == null)
            throw new IllegalArgumentException("RTB requires an enrolled live aircraft");
        run.forcedReturn = true;
    }

    static synchronized void validateEnrollment(Entity aircraft, TacticalAirAI.Mission mission) {
        if (aircraft == null || mission == null || aircraft.isRemoved()
                || !(aircraft.level() instanceof ServerLevel)
                || !BuiltInRegistries.ENTITY_TYPE.getKey(aircraft.getType())
                        .getNamespace().equals("warfare_wings")
                || aircraft.onGround() || !aircraft.getPassengers().isEmpty()
                || ACTIVE.containsKey(aircraft.getUUID()))
            throw new IllegalArgumentException("Need one empty airborne, unmanaged Warfare Wings aircraft");
        if (profiles == null) profiles = RuntimeTacticalAtlas.load();
        var airframe = profiles.get(BuiltInRegistries.ENTITY_TYPE.getKey(aircraft.getType()).toString());
        if (airframe == null) throw new IllegalArgumentException("Aircraft missing from pinned 24-plane Atlas");
        requireRole(switch (mission) {
            case TORPEDO -> airframe.profile().role().equals("torpedo_bomber");
            case LEVEL_BOMB -> airframe.profile().role().equals("bomber");
            case DIVE_BOMB -> airframe.profile().role().equals("attacker");
            case STRAFE -> airframe.profile().role().equals("attacker")
                    || airframe.profile().role().equals("fighter");
            default -> true;
        }, mission);
    }

    static synchronized void setLiveOrders(UUID aircraft, LiveOrder order) {
        Run run = ACTIVE.get(aircraft);
        if (run == null || run.liveOrder == null)
            throw new IllegalArgumentException("Aircraft is not enrolled in live autonomy");
        validateOrderAgainstWorld(run.aircraft, run.airframe, order);
        int assignedSlot = run.liveOrder.leader() != null
                && run.liveOrder.leader().equals(order.leader())
                && run.liveOrder.team().equals(order.team())
                ? run.stationSlot : nextFreeStationSlot(order, run.aircraft.getUUID());
        run.liveOrder = order;
        run.stationSlot = assignedSlot;
        run.lastConfirmedContact = null;
        run.lastConfirmedTick = -1;
    }

    static synchronized void startLive(String scenario, ServerLevel level, Entity aircraft,
                                       ArmorStand pilot, LiveOrder order, int durationTicks) {
        if (order == null) throw new IllegalArgumentException("Live order required");
        if (profiles == null) profiles = RuntimeTacticalAtlas.load();
        var airframe = profiles.get(BuiltInRegistries.ENTITY_TYPE.getKey(aircraft.getType()).toString());
        if (airframe == null) throw new IllegalArgumentException("No verified Warfare Wings aircraft profile");
        validateOrderAgainstWorld(aircraft, airframe, order);
        int slot = nextFreeStationSlot(order, aircraft.getUUID());
        start(scenario, level, aircraft, pilot, order.mission(), order.waypoint(), order.home(),
                null, null, null, durationTicks, true);
        // start has already initialized and added the independently owned Run.
        Run run = ACTIVE.get(aircraft.getUUID());
        run.liveOrder = order;
        run.stationSlot = slot;
    }

    private static void validateOrderAgainstWorld(Entity aircraft,
            RuntimeTacticalAtlas.Airframe airframe, LiveOrder order) {
        String role = airframe.profile().role();
        switch (order.mission()) {
            case TORPEDO -> requireRole(role.equals("torpedo_bomber"), order.mission());
            case LEVEL_BOMB -> requireRole(role.equals("bomber"), order.mission());
            case DIVE_BOMB -> requireRole(role.equals("attacker"), order.mission());
            case STRAFE -> requireRole(role.equals("attacker") || role.equals("fighter"), order.mission());
            default -> { }
        }
        if (order.designatedTarget() != null) {
            Entity target = ((ServerLevel) aircraft.level()).getEntity(order.designatedTarget());
            if (target == null || target.isRemoved() || target == aircraft)
                throw new IllegalArgumentException("Explicit target absent from aircraft dimension");
            Run targetRun = ACTIVE.get(target.getUUID());
            if (targetRun != null && targetRun.liveOrder != null
                    && targetRun.liveOrder.team().equals(order.team()))
                throw new IllegalArgumentException("Explicit target belongs to own live team");
        }
        if (order.leader() != null) {
            if (order.leader().equals(aircraft.getUUID()))
                throw new IllegalArgumentException("Aircraft cannot lead itself");
            Run lead = ACTIVE.get(order.leader());
            if (lead == null || lead.liveOrder == null || !lead.liveOrder.team().equals(order.team())
                    || lead.aircraft.level() != aircraft.level())
                throw new IllegalArgumentException("Leader must be enrolled in same live team and dimension");
        }
    }
    private static void requireRole(boolean accepted, TacticalAirAI.Mission mission) {
        if (!accepted) throw new IllegalArgumentException("Aircraft role incompatible with mission " + mission);
    }

    private static int nextFreeStationSlot(LiveOrder order, UUID excluded) {
        if (order.leader() == null) return -1;
        boolean[] occupied = new boolean[16];
        for (Run other : ACTIVE.values()) {
            if (other.aircraft.getUUID().equals(excluded) || other.liveOrder == null
                    || other.stationSlot < 0 || other.stationSlot >= occupied.length) continue;
            if (order.team().equals(other.liveOrder.team())
                    && order.leader().equals(other.liveOrder.leader())) occupied[other.stationSlot] = true;
        }
        for (int i = 0; i < occupied.length; i++) if (!occupied[i]) return i;
        throw new IllegalArgumentException("Leader already has 16 assigned formation stations");
    }

    static synchronized boolean stop(UUID aircraftId) {
        Run run = ACTIVE.remove(aircraftId);
        if (run == null) return false;
        try { run.close(); } catch (IOException ignored) {}
        remember(new Result(false, "STOPPED_BY_OPERATOR", run.steps,
                run.nonzeroLateral, run.yawTravel, run.displacement(),
                run.firstCommandSample, run.firstYawResponseSample, run.trace,
                run.observedTicks, run.predictedTicks, run.escortTicks,
                run.strikeIngressTicks, run.strikeEgressTicks, run.returnTicks,
                run.returnStartDistance, run.closestReturnDistance), run.scenario);
        return true;
    }

    static synchronized void onServerStopping(ServerStoppingEvent event) {
        // Static fields survive development-server restarts in a classloader.
        // Do not retain old-world entities, open writers or completed results.
        for (Run run : new ArrayList<>(ACTIVE.values())) {
            try { run.close(); } catch (IOException ignored) {}
        }
        ACTIVE.clear();
        RESULTS.clear();
        profiles = null;
    }

    static synchronized void start(String scenario, ServerLevel level, Entity aircraft,
                                   ArmorStand pilot, TacticalAirAI.Mission mission,
                                   net.minecraft.world.phys.Vec3 objective,
                                   net.minecraft.world.phys.Vec3 home,
                                   Entity observedHostile,
                                   net.minecraft.world.phys.Vec3 formationAnchor,
                                   HistoricalDoctrineOrders.Order doctrine,
                                   int durationTicks) {
        start(scenario, level, aircraft, pilot, mission, objective, home, observedHostile,
                formationAnchor, doctrine, durationTicks, false);
    }

    static synchronized void start(String scenario, ServerLevel level, Entity aircraft,
                                   ArmorStand pilot, TacticalAirAI.Mission mission,
                                   net.minecraft.world.phys.Vec3 objective,
                                   net.minecraft.world.phys.Vec3 home,
                                   Entity observedHostile,
                                   net.minecraft.world.phys.Vec3 formationAnchor,
                                   HistoricalDoctrineOrders.Order doctrine,
                                   int durationTicks, boolean ownsPilot) {
        if (scenario == null || !scenario.matches("[a-z0-9_-]{1,80}") || durationTicks < 40
                || durationTicks > 1000 || level == null || aircraft == null
                || pilot == null || objective == null || home == null || mission == null)
            throw new IllegalArgumentException("invalid tactical runtime scenario");
        // Late resolve because hosted Forge source compiles run without private
        // Warfare Wings or pinned IA JAR. The exact runtime stage must supply both.
        try {
            if (!Class.forName("immersive_aircraft.entity.VehicleEntity").isInstance(aircraft))
                throw new IllegalArgumentException("Observed entity is not an IA VehicleEntity");
        } catch (ClassNotFoundException ex) {
            throw new IllegalStateException("Immersive Aircraft not installed", ex);
        }
        if (profiles == null) profiles = RuntimeTacticalAtlas.load();
        String id = BuiltInRegistries.ENTITY_TYPE.getKey(aircraft.getType()).toString();
        var airframe = profiles.get(id);
        if (airframe == null) throw new IllegalArgumentException("Not in exact 24-plane roster: " + id);
        if (ACTIVE.containsKey(aircraft.getUUID())
                || ACTIVE.values().stream().anyMatch(r -> r.scenario.equals(scenario)))
            throw new IllegalStateException("tactical aircraft or scenario already active: " + scenario);
        IaRuntimeAccess.validateTacticalControlSurface(aircraft);
        BufferedWriter writer = null;
        try {
            Path dir = FMLPaths.GAMEDIR.get().resolve("ww-physics-traces");
            Files.createDirectories(dir);
            Path trace = dir.resolve(scenario + "-forge-controls.csv");
            writer = Files.newBufferedWriter(trace, StandardCharsets.UTF_8);
            writer.write(HEADER);
            writer.newLine();
            Run run = new Run(scenario, level, aircraft, pilot, observedHostile, mission,
                    xyz(objective), xyz(home),
                    formationAnchor == null ? null : xyz(formationAnchor),
                    doctrine, airframe, durationTicks, writer, trace, ownsPilot);
            run.keepTestChunksLoaded();
            // A failed initial sample must not leave an ACTIVE run containing
            // a failed writer (or mask an earlier successful result).
            run.write(0, null, null, null);
            ACTIVE.put(aircraft.getUUID(), run);
            RESULTS.remove(scenario);
            writer = null; // ownership transferred to Run
        } catch (IOException ex) {
            throw new IllegalStateException("Unable to open tactical runtime trace", ex);
        } finally {
            if (writer != null) {
                try { writer.close(); } catch (IOException ignored) {}
            }
        }
    }

    static synchronized void onServerTick(TickEvent.ServerTickEvent event) {
        if (event.phase != TickEvent.Phase.END || ACTIVE.isEmpty()) return;
        for (Run run : new ArrayList<>(ACTIVE.values())) {
            try {
                if (run.aircraft.isRemoved() || run.pilot.isRemoved()
                        || !run.pilot.isPassengerOfSameVehicle(run.aircraft))
                    throw new IllegalStateException("missing IA aircraft or mounted pilot");
                // The GameTest may register in the middle of a server tick.
                // Only compute one command after a completed aircraft entity tick.
                int tick = run.aircraft.tickCount;
                if (tick == run.lastAircraftTick) {
                    if (run.testLease != null && run.stalledServerTicks % 4 == 0)
                        run.testLease.reconfirmLoaded(run.aircraft);
                    if (++run.stalledServerTicks > 20)
                        throw new IllegalStateException("NON_TICKING_REAL_AIRCRAFT: "
                                + run.scenario + " stuck at entityTick=" + tick
                                + " gameTime=" + run.level.getGameTime()
                                + " pos=" + run.aircraft.blockPosition());
                    continue;
                }
                if (tick != run.lastAircraftTick + 1)
                    throw new IllegalStateException("Aircraft tick gap: " + run.lastAircraftTick + " -> " + tick);
                run.stalledServerTicks = 0;
                run.lastAircraftTick = tick;
                run.keepTestChunksLoaded();
                run.step();
                if (run.steps >= run.duration) {
                    run.close();
                    remember(new Result(true, null, run.steps,
                            run.nonzeroLateral, run.yawTravel, run.displacement(),
                            run.firstCommandSample, run.firstYawResponseSample, run.trace,
                            run.observedTicks, run.predictedTicks, run.escortTicks,
                            run.strikeIngressTicks, run.strikeEgressTicks, run.returnTicks,
                            run.returnStartDistance, run.closestReturnDistance), run.scenario);
                    ACTIVE.remove(run.aircraft.getUUID());
                }
            } catch (Throwable ex) {
                try { run.close(); } catch (IOException ignored) {}
                if (run.testLease != null) {
                    // A failing GameTest must never leave an orphan aircraft
                    // that contaminates the next distinct test batch.
                    run.pilot.stopRiding();
                    run.pilot.discard();
                    run.aircraft.discard();
                }
                remember(new Result(false,
                        ex.getClass().getSimpleName() + ": " + ex.getMessage(),
                        run.steps, run.nonzeroLateral, run.yawTravel, run.displacement(),
                        run.firstCommandSample, run.firstYawResponseSample, run.trace,
                        run.observedTicks, run.predictedTicks, run.escortTicks,
                        run.strikeIngressTicks, run.strikeEgressTicks, run.returnTicks,
                        run.returnStartDistance, run.closestReturnDistance), run.scenario);
                ACTIVE.remove(run.aircraft.getUUID());
            }
        }
    }

    private static Ia133Microkernel.Vec3 xyz(net.minecraft.world.phys.Vec3 v) {
        return new Ia133Microkernel.Vec3(v.x, v.y, v.z);
    }

    private static String n(double value) {
        return String.format(Locale.ROOT, "%.9f", value);
    }

    private static final class Run {
        final String scenario;
        final ServerLevel level;
        final Entity aircraft;
        final ArmorStand pilot;
        final Entity hostile;
        final TacticalAirAI.Mission mission;
        final Ia133Microkernel.Vec3 objective, home, anchor;
        final HistoricalDoctrineOrders.Order doctrine;
        final RuntimeTacticalAtlas.Airframe airframe;
        final int duration;
        final BufferedWriter writer;
        final Path trace;
        final boolean ownsPilot;
        final boolean isolatedGameTest;
        final GameTestFlightChunkLease testLease;
        final net.minecraft.world.phys.Vec3 startPosition;
        LiveOrder liveOrder;
        LiveMissionPlanner.Phase livePhase = LiveMissionPlanner.Phase.TRANSIT;
        boolean forcedReturn;
        int escortTicks, strikeIngressTicks, strikeEgressTicks, returnTicks;
        String lastPhaseReason = "NO_LIVE_ORDER";
        double returnStartDistance = Double.NaN;
        double closestReturnDistance = Double.POSITIVE_INFINITY;
        int stationSlot = -1;
        int observedTicks, sensorCandidates, blockedContacts;
        int predictedTicks;
        // Every entry here has independently passed the current real
        // Minecraft FOV/range/voxel LOS. Do not silently reduce collision
        // avoidance to the ONE threat selected for strategic pursuit.
        final List<TacticalAirAI.Contact> currentVisibleHostiles = new ArrayList<>();
        TacticalAirAI.Contact lastConfirmedContact;
        long lastConfirmedTick = -1;
        String lastContactStatus = "none";
        String lastContactSelection = "NO_VISIBLE_HOSTILE";
        int lastVisibleHostileCount;
        boolean lastContactWasRetainedByHysteresis;
        TacticalAirAI.Memory memory = TacticalAirAI.Memory.INITIAL;
        int lastAircraftTick, steps, nonzeroLateral;
        int stalledServerTicks;
        int firstCommandSample = -1, firstYawResponseSample = -1;
        double firstCommandX;
        double lastYaw, yawTravel;

        Run(String scenario, ServerLevel level, Entity aircraft, ArmorStand pilot,
            Entity hostile, TacticalAirAI.Mission mission,
            Ia133Microkernel.Vec3 objective, Ia133Microkernel.Vec3 home,
            Ia133Microkernel.Vec3 anchor, HistoricalDoctrineOrders.Order doctrine,
            RuntimeTacticalAtlas.Airframe airframe, int duration,
            BufferedWriter writer, Path trace, boolean ownsPilot) {
            this.scenario = scenario;
            this.level = level;
            this.aircraft = aircraft;
            this.pilot = pilot;
            this.hostile = hostile;
            this.mission = mission;
            this.objective = objective;
            this.home = home;
            this.anchor = anchor;
            this.doctrine = doctrine;
            this.airframe = airframe;
            this.duration = duration;
            this.writer = writer;
            this.trace = trace;
            this.ownsPilot = ownsPilot;
            this.isolatedGameTest = aircraft.getTags().contains(GAME_TEST_ISOLATION_TAG);
            this.testLease = (isolatedGameTest || aircraft.getTags().contains(LIVE_PAIR_TEST_TAG))
                    ? new GameTestFlightChunkLease(level) : null;
            this.startPosition = aircraft.position();
            this.lastAircraftTick = aircraft.tickCount;
            this.lastYaw = aircraft.getYRot();
        }

        void keepTestChunksLoaded() {
            if (testLease != null) testLease.update(aircraft);
        }

        void step() throws IOException {
            var currentPosition = xyz(aircraft.position());
            var velocity = xyz(aircraft.getDeltaMovement());
            double surface = level.getHeight(Heightmap.Types.MOTION_BLOCKING,
                    Mth.floor(currentPosition.x()), Mth.floor(currentPosition.z()));
            double fuel = IaRuntimeAccess.remainingFuelReserve(aircraft);
            double integrity = Math.max(0, Math.min(1, IaRuntimeAccess.health(aircraft)));
            var state = new Ia133Microkernel.State(
                    aircraft.tickCount, currentPosition, velocity,
                    aircraft.getYRot(), aircraft.getXRot(), IaRuntimeAccess.roll(aircraft),
                    0, 0, 0,
                    IaRuntimeAccess.smooth(aircraft, "pressingInterpolatedX"),
                    IaRuntimeAccess.smooth(aircraft, "pressingInterpolatedY"),
                    IaRuntimeAccess.smooth(aircraft, "pressingInterpolatedZ"),
                    IaRuntimeAccess.engineTarget(aircraft),
                    IaRuntimeAccess.enginePower(aircraft),
                    // Source microkernel State field means engine utilization,
                    // distinct from the actual remaining-fuel reserve in Frame.
                    IaRuntimeAccess.fuelUtilization(aircraft),
                    currentPosition.y(), aircraft.onGround(), aircraft.isInWater());
            // The original synthetic ArmorStand contact remains exclusively
            // for legacy GameTests. Live runs scan real entities every tick.
            LiveOrder orders = liveOrder;
            currentVisibleHostiles.clear();
            TacticalAirAI.Contact freshlyObserved = orders == null
                    ? hostile != null && !hostile.isRemoved()
                      ? new TacticalAirAI.Contact(hostile.getUUID().toString(),
                              xyz(hostile.position()), xyz(hostile.getDeltaMovement()), true) : null
                    : observeLive(orders);
            TacticalAirAI.Contact contact = freshlyObserved;
            if (orders != null) {
                if (freshlyObserved != null) {
                    observedTicks++;
                    lastConfirmedContact = freshlyObserved;
                    lastConfirmedTick = level.getGameTime();
                } else if (lastConfirmedContact != null && lastConfirmedTick >= 0
                        && level.getGameTime() - lastConfirmedTick > 0
                        && level.getGameTime() - lastConfirmedTick <= CONTACT_TRACK_TTL_TICKS
                        && trackStillEligible(orders)) {
                    long elapsed = level.getGameTime() - lastConfirmedTick;
                    var known = lastConfirmedContact;
                    // Position prediction uses LAST OBSERVED state only.
                    // Never substitute an entity's current hidden position.
                    contact = new TacticalAirAI.Contact(known.id(),
                            known.position().add(known.velocity().scale(elapsed)),
                            known.velocity(), true);
                    predictedTicks++;
                } else if (lastConfirmedContact != null
                        && level.getGameTime() - lastConfirmedTick > CONTACT_TRACK_TTL_TICKS) {
                    lastConfirmedContact = null;
                    lastConfirmedTick = -1;
                }
                lastContactStatus = freshlyObserved != null ? "visible:" + freshlyObserved.id()
                        : contact != null ? "last_seen_prediction:" + contact.id()
                        : "none";
            }
            var nearby = new ArrayList<FlightSafetyPlanner.MovingObstacle>();
            Ia133Microkernel.Vec3 nearestFriendly = null;
            double nearestFriendlyDistance = Double.POSITIVE_INFINITY;
            // Airframe faction is historical operator metadata, NOT an
            // alliance/team assignment. All nearby planes obstruct flight,
            // but we do not invent an allied aircraft for tactical decisions.
            for (Entity other : level.getEntities(aircraft,
                    aircraft.getBoundingBox().inflate(80), e -> !e.isRemoved())) {
                var otherId = BuiltInRegistries.ENTITY_TYPE.getKey(other.getType()).toString();
                var otherFrame = profiles.get(otherId);
                if (otherFrame == null) continue;
                if (isolatedGameTest) {
                    // The five test cases intentionally have exactly one
                    // registered aircraft each. Fail instead of silently
                    // changing the source-AI path to collision avoidance.
                    throw new IllegalStateException("cross-scenario aircraft within tactical sensor range: "
                            + otherId + " UUID=" + other.getUUID()
                            + " while running " + scenario);
                }
                if (aircraft.getTags().contains(LIVE_PAIR_TEST_TAG)
                        && !other.getTags().contains(LIVE_PAIR_TEST_TAG))
                    throw new IllegalStateException("Unexpected foreign aircraft near live pair test: "
                            + other.getUUID());
                Run otherRun = ACTIVE.get(other.getUUID());
                boolean sameTeamDatalink = orders != null && otherRun != null
                        && otherRun.liveOrder != null
                        && orders.team().equals(otherRun.liveOrder.team());
                if (orders != null && !sameTeamDatalink) {
                    // The broad entity query exists solely to detect physical
                    // test isolation violations and find explicitly linked
                    // wingmen. It MUST NOT expose invisible hostiles or
                    // unassigned aircraft positions to the tactical planner.
                    // Observed/last-known enemies are appended below using
                    // the already gated Contact snapshot.
                    continue;
                }
                var p = xyz(other.position());
                nearby.add(new FlightSafetyPlanner.MovingObstacle(other.getUUID().toString(),
                        p, xyz(other.getDeltaMovement()), Math.max(1, other.getBbWidth() * 0.5)));
                if (sameTeamDatalink) {
                    double distance = p.add(currentPosition.scale(-1)).lengthSquared();
                    if (distance < nearestFriendlyDistance) {
                        nearestFriendlyDistance = distance;
                        nearestFriendly = p;
                    }
                }
            }
            // Safety must consider ALL independently visible enemy aircraft,
            // even when only one has the highest bomber-interception urgency.
            // Their only input is the output of LiveAirSensor.observe, never
            // raw globally-known aircraft positions. For a lost sighting,
            // at most the selected explicit <=6tick memory track may enter.
            boolean selectedCurrentlyVisible = false;
            for (TacticalAirAI.Contact seen : currentVisibleHostiles) {
                nearby.add(new FlightSafetyPlanner.MovingObstacle(seen.id(),
                        seen.position(), seen.velocity(), 3.0));
                if (contact != null && seen.id().equals(contact.id()))
                    selectedCurrentlyVisible = true;
            }
            if (contact != null && !selectedCurrentlyVisible) {
                nearby.add(new FlightSafetyPlanner.MovingObstacle(contact.id(),
                        contact.position(), contact.velocity(), 3.0));
            }
            Ia133Microkernel.Vec3 currentObjective = orders == null ? objective : xyz(orders.waypoint());
            Ia133Microkernel.Vec3 currentHome = orders == null ? home : xyz(orders.home());
            Ia133Microkernel.Vec3 currentAnchor = orders == null ? anchor : resolveLeader(orders);
            // Air attack missions use a currently observed designated target
            // as their actual objective; a lost contact does not magically
            // update to the target's hidden true position.
            if (orders != null && contact != null && (orders.mission() == TacticalAirAI.Mission.TORPEDO
                    || orders.mission() == TacticalAirAI.Mission.STRAFE
                    || orders.mission() == TacticalAirAI.Mission.DIVE_BOMB
                    || orders.mission() == TacticalAirAI.Mission.LEVEL_BOMB))
                currentObjective = contact.position();
            TacticalAirAI.Mission guidanceMission = orders == null ? mission : orders.mission();
            TacticalAirAI.Contact guidanceContact = contact;
            if (orders != null) {
                Vec3 station = currentAnchor == null ? null
                        : new Vec3(currentAnchor.x(), currentAnchor.y(), currentAnchor.z());
                var intent = LiveMissionPlanner.select(orders.mission(), livePhase,
                        aircraft.position(),
                        new Vec3(currentObjective.x(), currentObjective.y(), currentObjective.z()),
                        orders.home(), station, forcedReturn, fuel, integrity);
                livePhase = intent.phase();
                lastPhaseReason = intent.reason();
                guidanceMission = intent.guidanceMission();
                currentObjective = xyz(intent.waypoint());
                guidanceContact = intent.mayUseObservedHostile() ? contact : null;
                switch (livePhase) {
                    case ESCORT_COVER -> escortTicks++;
                    case STRIKE_INGRESS -> strikeIngressTicks++;
                    case STRIKE_EGRESS -> strikeEgressTicks++;
                    case RETURNING -> {
                        returnTicks++;
                        double distanceToHome = aircraft.position().distanceTo(orders.home());
                        if (Double.isNaN(returnStartDistance))
                            returnStartDistance = distanceToHome;
                        closestReturnDistance = Math.min(closestReturnDistance, distanceToHome);
                    }
                    default -> { }
                }
                if (livePhase == LiveMissionPlanner.Phase.RETURNING
                        || livePhase == LiveMissionPlanner.Phase.STRIKE_EGRESS)
                    currentAnchor = null;
                else if (livePhase == LiveMissionPlanner.Phase.ESCORT_COVER) {
                    if (guidanceContact != null && orders.leader() != null) {
                        // Enemy present: TacticalAirAI protects the actual
                        // leader, never a follower's offset station.
                        Run leader = ACTIVE.get(orders.leader());
                        if (leader != null && !leader.aircraft.isRemoved()
                                && leader.aircraft.level() == level)
                            currentAnchor = xyz(leader.aircraft.position());
                    } else {
                        // In quiet air, steer to the unique follower station
                        // rather than stacking constant offsets onto a slot.
                        guidanceMission = TacticalAirAI.Mission.PATROL;
                        currentAnchor = null;
                    }
                }
            }
            Ia133Microkernel.Vec3 observedLeaderVelocity = new Ia133Microkernel.Vec3(0, 0, 0);
            if (orders != null && orders.leader() != null
                    && livePhase == LiveMissionPlanner.Phase.ESCORT_COVER) {
                Run leader = ACTIVE.get(orders.leader());
                if (leader != null && leader.liveOrder != null
                        && orders.team().equals(leader.liveOrder.team())
                        && leader.aircraft.level() == level && !leader.aircraft.isRemoved()) {
                    // Shared *friendly* live Entity state is a legitimate
                    // datalink measurement; never extrapolate a hidden foe.
                    observedLeaderVelocity = xyz(leader.aircraft.getDeltaMovement());
                }
            }
            var frame = new TacticalAirAI.Frame(airframe.profile(), airframe.model(), state,
                    guidanceMission, currentObjective, currentHome,
                    guidanceContact, currentAnchor, nearestFriendly,
                    fuel, integrity, surface, false, 0, observedLeaderVelocity);
            FlightSafetyPlanner.Terrain terrain = (x, z) ->
                    level.getHeight(Heightmap.Types.MOTION_BLOCKING, Mth.floor(x), Mth.floor(z));
            var environment = new FlightSafetyPlanner.Environment(terrain, nearby,
                    Math.max(1, aircraft.getBbWidth() * 0.5));
            var output = FlightControlLoop.step(new FlightControlLoop.Input(frame, memory,
                    doctrine, environment));
            var decision = output.decision();
            var control = decision.controls();
            int sampling = steps + 1;
            double signedYawChange = FlightGuidanceAngle.wrap(aircraft.getYRot() - lastYaw);
            double observedYawChange = Math.abs(signedYawChange);
            // An aircraft can drift ~0.005 degrees naturally before the
            // first END-tick command is injected. Only register a causal
            // steering response AFTER that command's tick and in the IA
            // controller's actual sign convention: yaw -= yawSpeed*smoothX.
            if (firstCommandSample >= 1 && sampling > firstCommandSample
                    && firstYawResponseSample == -1
                    && -signedYawChange * Math.signum(firstCommandX) > 0.02)
                firstYawResponseSample = sampling;
            if (Math.abs(control.x()) > 1e-3 && firstCommandSample == -1) {
                firstCommandSample = sampling;
                firstCommandX = control.x();
            }
            if (Math.abs(control.y()) > 1e-7)
                throw new IllegalStateException("Runtime pilot does not emulate raw IA throttle/brake key");
            IaRuntimeAccess.applyTacticalControls(aircraft, (float) control.x(),
                    (float) control.z(), (float) control.engineTarget());
            memory = decision.nextMemory();
            steps++;
            if (Math.abs(control.x()) > 1e-3) nonzeroLateral++;
            yawTravel += observedYawChange;
            lastYaw = aircraft.getYRot();
            write(steps, decision, output.safety(), control);
        }

        private Ia133Microkernel.Vec3 resolveLeader(LiveOrder order) {
            if (order.leader() == null) return null;
            Run leader = ACTIVE.get(order.leader());
            if (leader == null || leader.liveOrder == null || leader.aircraft.isRemoved()
                    || leader.aircraft.level() != level
                    || !leader.liveOrder.team().equals(order.team())) return null;
            if (stationSlot < 0) return null;
            // Stable per-enrollment slot in the leader's yaw-oriented frame.
            // Values are gameplay spacing; historical doctrine still needs
            // explicit unit/year context and live distance calibration.
            int rank = stationSlot / 2;
            double side = stationSlot % 2 == 0 ? -1 : 1;
            var local = new Ia133Microkernel.Vec3(
                    side * (36 + rank * 28), 8 + rank * 4, -42 - rank * 32);
            return HistoricalDoctrineOrders.station(xyz(leader.aircraft.position()),
                    leader.aircraft.getYRot(), local);
        }

        private TacticalAirAI.Contact observeLive(LiveOrder order) {
            lastVisibleHostileCount = 0;
            lastContactSelection = "NO_VISIBLE_HOSTILE";
            lastContactWasRetainedByHysteresis = false;
            if (order.designatedTarget() != null) {
                Entity target = level.getEntity(order.designatedTarget());
                if (target == null || target.isRemoved() || target == aircraft) return null;
                Run targetRun = ACTIVE.get(target.getUUID());
                if (targetRun != null && targetRun.liveOrder != null
                        && order.team().equals(targetRun.liveOrder.team()))
                    return null; // fail closed even after a team reassignment
                sensorCandidates++;
                var observed = LiveAirSensor.observe(level, aircraft, target);
                if (observed == null) blockedContacts++;
                else {
                    currentVisibleHostiles.add(observed);
                    lastVisibleHostileCount = 1;
                    lastContactSelection = "EXPLICIT_TARGET_VISUAL_FOV_LOS";
                }
                return observed;
            }
            if (order.hostileTeam() == null) return null;
            TacticalAirAI.Contact nearest = null;
            double bestDistSq = Double.POSITIVE_INFINITY;
            // An escort may know its explicitly allied protectee's real
            // position/velocity by radio, but may never see unseen raiders.
            // Protect the moving asset against the most threatening VISIBLE
            // approach, rather than simply following the opponent currently
            // nearest to the escort itself. Bombers similarly rank threats
            // against their own measured flight. This is a finite 48-tick
            // constant-velocity estimate, not an omniscient future reading.
            var protectedPosition = xyz(aircraft.position());
            var protectedVelocity = xyz(aircraft.getDeltaMovement());
            boolean assetRisk = airframe.profile().role().equals("bomber");
            if (order.mission() == TacticalAirAI.Mission.ESCORT
                    && order.leader() != null) {
                Run ally = ACTIVE.get(order.leader());
                if (ally != null && ally.liveOrder != null
                        && order.team().equals(ally.liveOrder.team())
                        && ally.aircraft.level() == level && !ally.aircraft.isRemoved()) {
                    protectedPosition = xyz(ally.aircraft.position());
                    protectedVelocity = xyz(ally.aircraft.getDeltaMovement());
                    assetRisk = true;
                }
            }
            LiveThreatPriority.Threat risk = null;
            LiveThreatPriority.Threat previouslySelectedStillVisible = null;
            for (Run other : ACTIVE.values()) {
                if (other == this || other.liveOrder == null
                        || !order.hostileTeam().equals(other.liveOrder.team())
                        || other.aircraft.level() != level || other.aircraft.isRemoved()) continue;
                sensorCandidates++;
                var observed = LiveAirSensor.observe(level, aircraft, other.aircraft);
                if (observed == null) {
                    blockedContacts++;
                    continue;
                }
                currentVisibleHostiles.add(observed);
                lastVisibleHostileCount++;
                if (assetRisk) {
                    var candidate = LiveThreatPriority.assess(
                            observed, protectedPosition, protectedVelocity);
                    // The previous selection is eligible for stabilization
                    // ONLY if it passed FOV/range/voxel LOS AGAIN this tick.
                    // A six-tick last-seen prediction MUST NOT be promoted
                    // into a fresh contact by this tactical tie-breaker.
                    if (lastConfirmedContact != null
                            && observed.id().equals(lastConfirmedContact.id()))
                        previouslySelectedStillVisible = candidate;
                    if (LiveThreatPriority.better(candidate, risk)) {
                        risk = candidate;
                        nearest = observed;
                    }
                } else {
                    // Preserve nearest-visible patrol/2v2 target selection;
                    // only its already-visible Contact position may rank it.
                    double dist = observed.position()
                            .add(xyz(aircraft.position()).scale(-1)).lengthSquared();
                    if (dist < bestDistSq - 1e-9
                            || Math.abs(dist - bestDistSq) <= 1e-9
                            && (nearest == null || observed.id().compareTo(nearest.id()) < 0)) {
                        bestDistSq = dist;
                        nearest = observed;
                    }
                }
            }
            if (assetRisk && risk != null) {
                var stable = LiveThreatPriority.chooseStable(
                        previouslySelectedStillVisible, risk);
                lastContactWasRetainedByHysteresis = previouslySelectedStillVisible != null
                        && stable == previouslySelectedStillVisible
                        && !stable.contact().id().equals(risk.contact().id());
                nearest = stable.contact();
            }
            if (nearest != null)
                lastContactSelection = assetRisk
                        ? "VISIBLE_CPA_TO_PROTECTED_ASSET" : "NEAREST_VISIBLE_HOSTILE";
            return nearest;
        }

        private boolean trackStillEligible(LiveOrder order) {
            if (order.designatedTarget() == null && order.hostileTeam() == null)
                return false;
            if (order.designatedTarget() != null) {
                if (!order.designatedTarget().toString().equals(lastConfirmedContact.id())) return false;
                Entity targetEntity = level.getEntity(order.designatedTarget());
                if (targetEntity == null || targetEntity.isRemoved()) return false;
                Run target = ACTIVE.get(order.designatedTarget());
                return target == null || target.liveOrder == null
                        || !order.team().equals(target.liveOrder.team());
            }
            try {
                Run trackedRun = ACTIVE.get(UUID.fromString(lastConfirmedContact.id()));
                return trackedRun != null && trackedRun.liveOrder != null
                        && order.hostileTeam().equals(trackedRun.liveOrder.team())
                        && trackedRun.aircraft.level() == level && !trackedRun.aircraft.isRemoved();
            } catch (IllegalArgumentException badIdentifier) {
                return false;
            }
        }

        void write(int sample, TacticalAirAI.Decision decision,
                   FlightSafetyPlanner.Clearance clearance,
                   Ia133Microkernel.Control control) throws IOException {
            var p = aircraft.position();
            var v = aircraft.getDeltaMovement();
            writer.write(String.join(",",
                    SCHEMA, "minecraft_runtime_ia_next_tick_injection",
                    scenario, airframe.profile().aircraftId(),
                    Integer.toString(sample), Long.toString(level.getGameTime()),
                    n(p.x), n(p.y), n(p.z), n(v.x), n(v.y), n(v.z),
                    n(aircraft.getYRot()), n(aircraft.getXRot()),
                    n(IaRuntimeAccess.engineTarget(aircraft)), n(IaRuntimeAccess.enginePower(aircraft)),
                    n(IaRuntimeAccess.smooth(aircraft, "pressingInterpolatedX")),
                    n(IaRuntimeAccess.smooth(aircraft, "pressingInterpolatedZ")),
                    n(control == null ? 0 : control.x()),
                    n(control == null ? 0 : control.z()),
                    n(control == null ? 0 : control.engineTarget()),
                    decision == null ? "INITIAL" : decision.maneuver().name(),
                    decision == null ? "INITIAL"
                            : decision.reasonCode() + (liveOrder == null ? ""
                                    : "|live_team=" + liveOrder.team()
                                    + "|sighting=" + lastContactStatus
                                    + "|visible_hostile_count=" + lastVisibleHostileCount
                                    + "|contact_selection=" + lastContactSelection
                                    + "|contact_hysteresis_retained="
                                    + lastContactWasRetainedByHysteresis
                                    + "|phase=" + livePhase
                                    + "|phase_reason=" + lastPhaseReason),
                    clearance == null ? "INITIAL" : clearance.reason().name(),
                    n(clearance == null ? 0 : clearance.minPredictedClearance())));
            writer.newLine();
            writer.flush();
        }

        void close() throws IOException {
            try { writer.close(); } finally {
                if (testLease != null) testLease.close();
                if (ownsPilot) {
                    // Only the admin command's synthetic rider belongs to us.
                    try { IaRuntimeAccess.setEngineTarget(aircraft, 0f); } catch (RuntimeException ignored) {}
                    pilot.stopRiding();
                    pilot.discard();
                }
            }
        }
        double displacement() { return aircraft.position().distanceTo(startPosition); }
    }

    private static final class FlightGuidanceAngle {
        static double wrap(double value) {
            return org.kneekura.techhub.warfarewings.physics.FlightGuidance.wrapDeg(value);
        }
    }
}
