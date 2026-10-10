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
    private static final int MAX_COMPLETED_RESULTS = 32;
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
                  int firstCommandSample, int firstYawResponseSample, Path trace) {}

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

    static synchronized boolean stop(UUID aircraftId) {
        Run run = ACTIVE.remove(aircraftId);
        if (run == null) return false;
        try { run.close(); } catch (IOException ignored) {}
        remember(new Result(false, "STOPPED_BY_OPERATOR", run.steps,
                run.nonzeroLateral, run.yawTravel, run.displacement(),
                run.firstCommandSample, run.firstYawResponseSample, run.trace), run.scenario);
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
                if (tick == run.lastAircraftTick) continue;
                if (tick != run.lastAircraftTick + 1)
                    throw new IllegalStateException("Aircraft tick gap: " + run.lastAircraftTick + " -> " + tick);
                run.lastAircraftTick = tick;
                run.step();
                if (run.steps >= run.duration) {
                    run.close();
                    remember(new Result(true, null, run.steps,
                            run.nonzeroLateral, run.yawTravel, run.displacement(),
                            run.firstCommandSample, run.firstYawResponseSample, run.trace), run.scenario);
                    ACTIVE.remove(run.aircraft.getUUID());
                }
            } catch (Throwable ex) {
                try { run.close(); } catch (IOException ignored) {}
                remember(new Result(false,
                        ex.getClass().getSimpleName() + ": " + ex.getMessage(),
                        run.steps, run.nonzeroLateral, run.yawTravel, run.displacement(),
                        run.firstCommandSample, run.firstYawResponseSample, run.trace), run.scenario);
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
        final net.minecraft.world.phys.Vec3 startPosition;
        TacticalAirAI.Memory memory = TacticalAirAI.Memory.INITIAL;
        int lastAircraftTick, steps, nonzeroLateral;
        int firstCommandSample = -1, firstYawResponseSample = -1;
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
            this.startPosition = aircraft.position();
            this.lastAircraftTick = aircraft.tickCount;
            this.lastYaw = aircraft.getYRot();
        }

        void step() throws IOException {
            var currentPosition = xyz(aircraft.position());
            var velocity = xyz(aircraft.getDeltaMovement());
            double surface = level.getHeight(Heightmap.Types.MOTION_BLOCKING,
                    Mth.floor(currentPosition.x()), Mth.floor(currentPosition.z()));
            double fuel = Math.max(0, Math.min(1, IaRuntimeAccess.fuelUtilization(aircraft)));
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
                    fuel, currentPosition.y(), aircraft.onGround(), aircraft.isInWater());
            TacticalAirAI.Contact contact = hostile != null && !hostile.isRemoved()
                    ? new TacticalAirAI.Contact(hostile.getUUID().toString(),
                    xyz(hostile.position()), xyz(hostile.getDeltaMovement()), true)
                    : null;
            var nearby = new ArrayList<FlightSafetyPlanner.MovingObstacle>();
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
                var p = xyz(other.position());
                nearby.add(new FlightSafetyPlanner.MovingObstacle(other.getUUID().toString(),
                        p, xyz(other.getDeltaMovement()), Math.max(1, other.getBbWidth() * 0.5)));
            }
            var frame = new TacticalAirAI.Frame(airframe.profile(), airframe.model(), state,
                    mission, objective, home, contact, anchor, null,
                    fuel, integrity, surface, false, 0);
            FlightSafetyPlanner.Terrain terrain = (x, z) ->
                    level.getHeight(Heightmap.Types.MOTION_BLOCKING, Mth.floor(x), Mth.floor(z));
            var environment = new FlightSafetyPlanner.Environment(terrain, nearby,
                    Math.max(1, aircraft.getBbWidth() * 0.5));
            var output = FlightControlLoop.step(new FlightControlLoop.Input(frame, memory,
                    doctrine, environment));
            var decision = output.decision();
            var control = decision.controls();
            int sampling = steps + 1;
            double observedYawChange = Math.abs(FlightGuidanceAngle.wrap(aircraft.getYRot() - lastYaw));
            if (observedYawChange > 0.005 && firstYawResponseSample == -1)
                firstYawResponseSample = sampling;
            if (Math.abs(control.x()) > 1e-3 && firstCommandSample == -1)
                firstCommandSample = sampling;
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
                    decision == null ? "INITIAL" : decision.reasonCode(),
                    clearance == null ? "INITIAL" : clearance.reason().name(),
                    n(clearance == null ? 0 : clearance.minPredictedClearance())));
            writer.newLine();
            writer.flush();
        }

        void close() throws IOException {
            try { writer.close(); } finally {
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
