package org.kneekura.techhub.warfarewings.trace;

import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestAssertException;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;
import org.kneekura.techhub.warfarewings.physics.TacticalAirAI;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;
import net.minecraftforge.fml.loading.FMLPaths;

/**
 * Operational acceptance of 20Hz real Forge airplane flight, not simulator
 * predictions. The threat must physically reach an engagement opportunity,
 * and the B-17 protectee must stay outside the explicitly measured 95-block
 * hostile corridor for a PASS. No weapons are fired by this test.
 *
 * One batch per scenario, no synthetic hostile ArmorStand, and separate
 * same-game-time CSV geometry for independent mission receipt validation.
 */
@GameTestHolder(PhysicsTraceProbeMod.MOD_ID)
@PrefixGameTestTemplate(false)
public final class OperationalAirCombatGameTests {
    private OperationalAirCombatGameTests() {}
    private static final int TWO_V_TWO_TICKS = 280;
    private static final int ESCORT_TICKS = 340;
    private static final double MIN_PHYSICAL_SEPARATION = 6.0;
    private static final double B17_PROTECTION_RADIUS = 95.0;

    @GameTest(template = "empty", batch = "ww_operational_2v2", timeoutTicks = 530)
    public static void twoVsTwoMustReallyEngageAndManeuver(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        IaRuntimeAccess.configureCalibrationRuntime();
        Vec3 base = Vec3.atBottomCenterOf(helper.absolutePos(new BlockPos(0, 220, 0)));
        List<Participant> entries = new ArrayList<>();
        var warmup = preload(level, List.of(base.add(-65, 0, -12),
                base.add(65, 0, -18), base.add(-58, 0, 130),
                base.add(58, 0, 140)));
        helper.runAfterDelay(10, () -> {
            try {
                entries.add(spawn(level, "a6m", "red-1", "red", "blue",
                        base.add(-65, 0, -12), 0, .76, TWO_V_TWO_TICKS));
                entries.add(spawn(level, "a6m", "red-2", "red", "blue",
                        base.add(65, 0, -18), 0, .76, TWO_V_TWO_TICKS));
                entries.add(spawn(level, "p47n", "blue-1", "blue", "red",
                        base.add(-58, 0, 130), 180, -.78, TWO_V_TWO_TICKS));
                entries.add(spawn(level, "p47n", "blue-2", "blue", "red",
                        base.add(58, 0, 140), 180, -.78, TWO_V_TWO_TICKS));
                Recorder recorder = new Recorder("operational-2v2", level, entries, null);
                helper.succeedWhen(() -> completeWhenReady(recorder, TWO_V_TWO_TICKS, false));
                helper.runAfterDelay(TWO_V_TWO_TICKS + 35, () ->
                        failIfUnsuccessful(helper, recorder));
            } catch (RuntimeException exception) {
                closeUnfinished(entries);
                throw exception;
            } finally {
                warmup.forEach(GameTestFlightChunkLease::close);
            }
        });
    }

    @GameTest(template = "empty", batch = "ww_operational_b17_escort", timeoutTicks = 640)
    public static void twoEscortsDefendB17AgainstTwoApproachingHostiles(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        IaRuntimeAccess.configureCalibrationRuntime();
        Vec3 base = Vec3.atBottomCenterOf(helper.absolutePos(new BlockPos(0, 225, 0)));
        List<Participant> entries = new ArrayList<>();
        var warmup = preload(level, List.of(base, base.add(-48, 7, 18),
                base.add(48, 7, 18), base.add(-40, 3, 148),
                base.add(40, 3, 153)));
        helper.runAfterDelay(10, () -> {
            try {
                // The protectee belongs to the explicitly assigned convoy
                // team, and its declared opponents are the raiders.  Without
                // this order it cannot ever see an enemy through observeLive,
                // even if a raider is physically in its real FOV and LOS.
                Participant bomber = spawn(level, "b17", "b17", "convoy", "raiders",
                        base, 0, .65, ESCORT_TICKS);
                entries.add(bomber);
                entries.add(spawnEscort(level, "left", base.add(-48, 7, 18),
                        bomber.plane(), ESCORT_TICKS));
                entries.add(spawnEscort(level, "right", base.add(48, 7, 18),
                        bomber.plane(), ESCORT_TICKS));
                entries.add(spawn(level, "a6m", "raider-1", "raiders", "convoy",
                        base.add(-40, 3, 148), 180, -.78, ESCORT_TICKS));
                entries.add(spawn(level, "a6m", "raider-2", "raiders", "convoy",
                        base.add(40, 3, 153), 180, -.78, ESCORT_TICKS));
                Recorder recorder = new Recorder("operational-b17-escort", level, entries, bomber);
                helper.succeedWhen(() -> completeWhenReady(recorder, ESCORT_TICKS, true));
                helper.runAfterDelay(ESCORT_TICKS + 35, () ->
                        failIfUnsuccessful(helper, recorder));
            } catch (RuntimeException exception) {
                closeUnfinished(entries);
                throw exception;
            } finally {
                warmup.forEach(GameTestFlightChunkLease::close);
            }
        });
    }

    private record Participant(Entity plane, String name, String team, String scenario) {}

    private static List<GameTestFlightChunkLease> preload(ServerLevel level, List<Vec3> positions) {
        List<GameTestFlightChunkLease> leases = new ArrayList<>();
        try {
            for (Vec3 position : positions) {
                var lease = new GameTestFlightChunkLease(level);
                lease.update(position, Vec3.ZERO);
                leases.add(lease);
                // This synchronous load is necessary before adding entities
                // hundreds of blocks outside GameTest's 1x1 structure.
                level.getChunkAt(BlockPos.containing(position));
            }
            return leases;
        } catch (RuntimeException error) {
            leases.forEach(GameTestFlightChunkLease::close);
            throw error;
        }
    }

    private static Participant spawn(ServerLevel level, String model, String name,
                                     String team, String opposingTeam, Vec3 origin,
                                     float yaw, double vz, int duration) {
        var bootstrap = new GameTestFlightChunkLease(level);
        bootstrap.update(origin, new Vec3(0, 0, vz));
        try {
            Entity plane = LiveSquadronGameTests.spawn(level, model, origin, yaw, vz);
            plane.addTag(RuntimeTacticalPilot.LIVE_PAIR_TEST_TAG);
            String scenario = "op-" + name;
            RuntimeTacticalPilot.LiveOrder order = new RuntimeTacticalPilot.LiveOrder(team,
                    TacticalAirAI.Mission.INTERCEPT, origin.add(0, 0, yaw == 0 ? 380 : -380),
                    origin, null, opposingTeam, null);
            if (model.equals("b17"))
                order = new RuntimeTacticalPilot.LiveOrder(team,
                        TacticalAirAI.Mission.PATROL, origin.add(0, 0, 500),
                        origin, null, opposingTeam, null);
            RuntimeTacticalPilot.startLive(scenario, level, plane,
                    (ArmorStand) plane.getFirstPassenger(), order, duration);
            return new Participant(plane, name, team, scenario);
        } finally {
            bootstrap.close();
        }
    }

    private static Participant spawnEscort(ServerLevel level, String name,
                                            Vec3 origin, Entity protectee, int duration) {
        var bootstrap = new GameTestFlightChunkLease(level);
        bootstrap.update(origin, new Vec3(0, 0, .8));
        try {
            Entity plane = LiveSquadronGameTests.spawn(level, "p47n", origin, 0, .8);
            plane.addTag(RuntimeTacticalPilot.LIVE_PAIR_TEST_TAG);
            String scenario = "op-escort-" + name;
            RuntimeTacticalPilot.startLive(scenario, level, plane,
                    (ArmorStand) plane.getFirstPassenger(),
                    new RuntimeTacticalPilot.LiveOrder("convoy", TacticalAirAI.Mission.ESCORT,
                            origin.add(0, 0, 400), origin, null, "raiders",
                            protectee.getUUID()), duration);
            return new Participant(plane, "escort-" + name, "convoy", scenario);
        } finally {
            bootstrap.close();
        }
    }

    private static void closeUnfinished(List<Participant> entries) {
        for (Participant item : entries) {
            RuntimeTacticalPilot.stop(item.plane().getUUID());
            LiveSquadronGameTests.cleanupTestEntities(item.plane());
        }
    }

    private static void completeWhenReady(Recorder recorder, int requiredTicks,
                                          boolean protectee) {
        if (recorder.failure != null)
            throw new GameTestAssertException("OPERATIONAL_FAILED: " + recorder.failure);
        try {
            recorder.sample();
        } catch (RuntimeException failure) {
            recorder.fail(failure.getMessage());
            throw new GameTestAssertException("OPERATIONAL_FAILED: " + recorder.failure);
        }
        var results = new HashMap<String, RuntimeTacticalPilot.Result>();
        for (Participant item : recorder.participants) {
            var result = RuntimeTacticalPilot.result(item.scenario());
            if (result == null)
                throw new GameTestAssertException("Waiting for real " + recorder.name + ": "
                        + recorder.samples + "/" + requiredTicks);
            results.put(item.name(), result);
        }
        try {
            for (Participant item : recorder.participants) {
                var result = results.get(item.name());
                if (!result.complete() || result.samples() != requiredTicks)
                    throw new IllegalStateException("INCOMPLETE_REAL_FLIGHT "
                            + item.name() + " " + result.failure()
                            + " ticks=" + result.samples());
                if (result.displacementBlocks() < 30)
                    throw new IllegalStateException("INSUFFICIENT_REAL_MOVEMENT " + item.name()
                            + " displaced=" + result.displacementBlocks());
            }
            if (recorder.samples < requiredTicks - 2)
                throw new IllegalStateException("MISSING_GEOMETRY_TICKS "
                        + recorder.samples + " expected~" + requiredTicks);
            if (recorder.minimumSeparation < MIN_PHYSICAL_SEPARATION)
                throw new IllegalStateException("AIRCRAFT_COLLISION_CORRIDOR minDistance="
                        + recorder.minimumSeparation);
            if (recorder.minimumOpposingDistance > 120)
                throw new IllegalStateException("NO_PHYSICAL_ENGAGEMENT minOpposingDistance="
                        + recorder.minimumOpposingDistance);
            for (String side : List.of("red", "blue")) {
                if (protectee) break;
                if (recorder.visibleTicks.getOrDefault(side, 0) < 8)
                    throw new IllegalStateException("NO_REAL_HOSTILE_OBSERVATION "
                            + side + " visibleTicks=" + recorder.visibleTicks);
            }
            if (protectee) {
                if (results.get("escort-left").escortTicks() < 150
                        || results.get("escort-right").escortTicks() < 150)
                    throw new IllegalStateException("NO_SUSTAINED_REAL_ESCORT_PHASE");
                if (recorder.minimumProtecteeHostileDistance > 150)
                    throw new IllegalStateException("UNTESTED_B17_THREAT minB17Threat="
                            + recorder.minimumProtecteeHostileDistance);
                if (recorder.intrusionTicks > 0)
                    throw new IllegalStateException("B17_95_BLOCK_PROTECTION_BREACH "
                            + "intrusionTicks=" + recorder.intrusionTicks
                            + " minDistance=" + recorder.minimumProtecteeHostileDistance);
            }
            recorder.finished = true;
        } catch (RuntimeException operationalFailure) {
            recorder.fail(operationalFailure.getMessage());
            throw new GameTestAssertException("OPERATIONAL_FAILED: " + recorder.failure);
        } finally {
            if (!recorder.finished) recorder.fail(recorder.failure == null
                    ? "OPERATIONAL_TEST_FAILED" : recorder.failure);
            else recorder.release();
        }
    }

    private static void failIfUnsuccessful(GameTestHelper helper, Recorder recorder) {
        if (recorder.finished) return;
        recorder.fail(recorder.failure == null
                ? "TEST_DID_NOT_COMPLETE_BEFORE_DEADLINE" : recorder.failure);
        helper.fail("OPERATIONAL_REAL_FLIGHT_FAILED: " + recorder.failure);
    }

    private static final class Recorder {
        final String name;
        final ServerLevel level;
        final List<Participant> participants;
        final Participant protectee;
        final BufferedWriter writer;
        final Map<UUID, Integer> priorEntityTicks = new HashMap<>();
        final Map<String, Integer> visibleTicks = new HashMap<>();
        long lastGameTime = Long.MIN_VALUE;
        boolean started;
        boolean finished;
        boolean closed;
        String failure;
        int samples, intrusionTicks;
        double minimumSeparation = Double.POSITIVE_INFINITY;
        double minimumOpposingDistance = Double.POSITIVE_INFINITY;
        double minimumProtecteeHostileDistance = Double.POSITIVE_INFINITY;

        Recorder(String name, ServerLevel level, List<Participant> participants,
                 Participant protectee) {
            this.name = name;
            this.level = level;
            this.participants = List.copyOf(participants);
            this.protectee = protectee;
            try {
                Path directory = FMLPaths.GAMEDIR.get().resolve("ww-physics-traces");
                Files.createDirectories(directory);
                writer = Files.newBufferedWriter(directory.resolve(name + "-geometry.csv"),
                        StandardCharsets.UTF_8);
                writer.write("schema,scenario_id,game_time,sample,aircraft_id,team,entity_tick,"
                        + "pos_x,pos_y,pos_z,closest_enemy,dist_to_b17,"
                        + "observed_ticks,escort_ticks,phase");
                writer.newLine();
            } catch (IOException io) {
                throw new IllegalStateException("Could not write independent operational geometry", io);
            }
        }

        void sample() {
            // Newly spawned actors can be registered during a GameTest tick
            // before Minecraft has run their FIRST entity update. This is a
            // startup phase, not a skipped physics tick. Only start common
            // clock sampling once EVERY plane has tickCount>=1.
            if (!started) {
                for (Participant item : participants)
                    if (item.plane().tickCount == 0) return;
                started = true;
            }
            if (lastGameTime == level.getGameTime()) return;
            long time = level.getGameTime();
            if (lastGameTime != Long.MIN_VALUE && time != lastGameTime + 1)
                throw new IllegalStateException("NON_DETERMINISTIC_GAME_CLOCK " + time
                        + " prior=" + lastGameTime);
            lastGameTime = time;
            samples++;
            Map<UUID, RuntimeTacticalPilot.LiveStatus> live = new HashMap<>();
            for (var status : RuntimeTacticalPilot.liveStatus()) live.put(status.aircraft(), status);
            for (Participant actor : participants) {
                Entity aircraft = actor.plane();
                int current = aircraft.tickCount;
                Integer prior = priorEntityTicks.put(aircraft.getUUID(), current);
                if (prior != null && current != prior + 1 && RuntimeTacticalPilot.active(aircraft.getUUID()))
                    throw new IllegalStateException("CHUNK_OR_PHYSICS_TICK_GAP " + actor.name()
                            + " from=" + prior + " to=" + current);
                var status = live.get(aircraft.getUUID());
                if (status != null && status.observedTicks() > 0)
                    visibleTicks.merge(actor.team(), status.observedTicks()
                            - (samples > 1 ? previousObserved.getOrDefault(aircraft.getUUID(), 0) : 0),
                            Integer::sum);
                if (status != null) previousObserved.put(aircraft.getUUID(), status.observedTicks());
                double nearEnemy = Double.POSITIVE_INFINITY;
                for (Participant rival : participants) {
                    if (rival == actor) continue;
                    double dist = aircraft.distanceTo(rival.plane());
                    minimumSeparation = Math.min(minimumSeparation, dist);
                    if (!actor.team().equals(rival.team())) {
                        nearEnemy = Math.min(nearEnemy, dist);
                        minimumOpposingDistance = Math.min(minimumOpposingDistance, dist);
                    }
                }
                double toBomber = protectee == null ? Double.NaN
                        : aircraft.distanceTo(protectee.plane());
                try {
                    writer.write(String.format(Locale.ROOT,
                            "ww.physics.operational.geometry.v1,%s,%d,%d,%s,%s,%d,%.9f,%.9f,%.9f,%.9f,%.9f,%d,%d,%s",
                            name, time, samples, actor.name(), actor.team(), current,
                            aircraft.getX(), aircraft.getY(), aircraft.getZ(), nearEnemy,
                            toBomber, status == null ? -1 : status.observedTicks(),
                            status == null ? -1 : status.escortTicks(),
                            status == null ? "COMPLETED" : status.phase().name()));
                    writer.newLine();
                    writer.flush();
                } catch (IOException io) {
                    throw new IllegalStateException("Could not persist real 2v2/B17 geometry", io);
                }
            }
            if (protectee != null) {
                boolean intruding = false;
                for (Participant rival : participants) {
                    if (!rival.team().equals("raiders")) continue;
                    double distance = rival.plane().distanceTo(protectee.plane());
                    minimumProtecteeHostileDistance = Math.min(minimumProtecteeHostileDistance, distance);
                    if (distance < B17_PROTECTION_RADIUS) intruding = true;
                }
                if (intruding) intrusionTicks++;
            }
        }

        final Map<UUID, Integer> previousObserved = new HashMap<>();
        void fail(String reason) {
            if (failure == null) failure = reason == null ? "UNKNOWN_FAILURE" : reason;
            release();
        }

        void release() {
            if (closed) return;
            closed = true;
            try { writer.close(); } catch (IOException ignored) {}
            closeUnfinished(participants);
        }
    }
}
