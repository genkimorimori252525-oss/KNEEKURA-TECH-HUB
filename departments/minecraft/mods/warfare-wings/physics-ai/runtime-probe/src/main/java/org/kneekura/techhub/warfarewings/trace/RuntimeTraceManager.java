package org.kneekura.techhub.warfarewings.trace;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.server.ServerStoppingEvent;
import net.minecraftforge.fml.loading.FMLPaths;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;
import java.util.HashSet;
import java.util.Set;

final class RuntimeTraceManager {
    static final String SCHEMA = "ww.physics.trace.v1";
    static final String SCENARIO = "a6m-throttle-step-v1";
    static final String AIRCRAFT = "warfare_wings:a6m";
    static final int TICKS = 400;
    static final String HEADER =
            "schema_version,source,scenario_id,aircraft_id,tick,game_time," +
            "pos_x,pos_y,pos_z,vel_x,vel_y,vel_z,speed_bps,horizontal_speed_bps," +
            "yaw_deg,pitch_deg,roll_deg,engine_target,engine_power,fuel_utilization," +
            "raw_x,raw_y,raw_z,smooth_x,smooth_y,smooth_z";

    private static Run active;
    private static String failure;
    private static boolean complete;

    private RuntimeTraceManager() {}

    static synchronized void start(ServerLevel level, Entity aircraft, ArmorStand pilot) {
        if (active != null) throw new IllegalStateException("Trace already active");
        complete = false;
        failure = null;
        BufferedWriter writer = null;
        try {
            Path dir = FMLPaths.GAMEDIR.get().resolve("ww-physics-traces");
            Files.createDirectories(dir);
            Path path = dir.resolve("a6m-throttle-step-v1-runtime.csv");
            writer = Files.newBufferedWriter(path, StandardCharsets.UTF_8);
            writer.write(HEADER);
            writer.newLine();
            active = new Run(level, aircraft, pilot, writer, path);
            // A 400-tick aircraft exceeds GameTest's automatically loaded
            // 160-block radius. Preload the forward corridor dynamically so
            // crossing a chunk boundary cannot silently freeze real physics.
            active.forceFlightCorridor();
            active.write(0);
        } catch (IOException | RuntimeException e) {
            try {
                if (active != null) active.close();
                else if (writer != null) writer.close();
            } catch (IOException ignored) {}
            active = null;
            throw new IllegalStateException("Could not start exact runtime trace safely", e);
        }
    }

    static synchronized boolean complete() { return complete; }
    static synchronized String failure() { return failure; }

    static synchronized void onServerStopping(ServerStoppingEvent event) {
        if (active == null) return;
        fail("SERVER_STOPPED_DURING_REAL_TRACE");
    }

    static synchronized void onServerTick(TickEvent.ServerTickEvent event) {
        if (event.phase != TickEvent.Phase.END || active == null) return;
        try {
            if (active.skipFirstEnd) {
                active.skipFirstEnd = false;
                return;
            }
            if (active.aircraft.isRemoved() || active.pilot.isRemoved()
                    || !active.pilot.isPassengerOfSameVehicle(active.aircraft)) {
                fail("aircraft_or_pilot_removed");
                return;
            }
            // An entity in an unloaded chunk stops ticking while the server
            // clock and this recorder keep ticking. This MUST be a failed
            // measurement, never 401 duplicated "real" physics samples.
            int entityTick = active.aircraft.tickCount;
            if (entityTick != active.lastAircraftTick + 1) {
                fail("NON_TICKING_REAL_AIRCRAFT: expected aircraft tick "
                        + (active.lastAircraftTick + 1) + " actual=" + entityTick);
                return;
            }
            active.lastAircraftTick = entityTick;
            active.forceFlightCorridor();
            active.sampleTick++;
            active.write(active.sampleTick);
            if (active.sampleTick >= TICKS) {
                active.close();
                active = null;
                complete = true;
            }
        } catch (Throwable t) {
            fail(t.getClass().getSimpleName() + ":" + t.getMessage());
        }
    }

    private static void fail(String reason) {
        failure = reason;
        try {
            if (active != null) active.close();
        } catch (IOException ignored) {
        }
        active = null;
    }

    private static final class Run {
        final ServerLevel level;
        final Entity aircraft;
        final ArmorStand pilot;
        final BufferedWriter writer;
        final Path path;
        final Set<Long> visitedChunks = new HashSet<>();
        final Set<Long> forcedChunks = new HashSet<>();
        int lastAircraftTick;
        int sampleTick;
        boolean skipFirstEnd = true;

        Run(ServerLevel level, Entity aircraft, ArmorStand pilot, BufferedWriter writer, Path path) {
            this.level = level;
            this.aircraft = aircraft;
            this.pilot = pilot;
            this.writer = writer;
            this.path = path;
            this.lastAircraftTick = aircraft.tickCount;
        }

        void forceFlightCorridor() {
            int chunkX = ((int) Math.floor(aircraft.getX())) >> 4;
            int chunkZ = ((int) Math.floor(aircraft.getZ())) >> 4;
            // A6M calibration deliberately starts facing +Z with neutral
            // rudder. Three lateral columns and twelve chunks ahead ensure
            // nearby movement stays loaded until the next recorder sample.
            for (int dx = -1; dx <= 1; dx++) {
                for (int dz = -2; dz <= 12; dz++) {
                    int x = chunkX + dx, z = chunkZ + dz;
                    long key = ChunkPos.asLong(x, z);
                    if (visitedChunks.add(key)) {
                        // Do not unforce a chunk that was already owned by a
                        // server/admin. setChunkForced returns true only
                        // when our test changed the forced state.
                        if (level.setChunkForced(x, z, true))
                            forcedChunks.add(key);
                    }
                }
            }
        }

        void write(long tick) throws IOException {
            Vec3 p = aircraft.position();
            Vec3 v = aircraft.getDeltaMovement();
            double speed = v.length() * 20.0;
            double horizontal = v.horizontalDistance() * 20.0;
            String row = String.join(",",
                    SCHEMA, "minecraft_runtime", SCENARIO, AIRCRAFT,
                    Long.toString(tick), Long.toString(level.getGameTime()),
                    d(p.x), d(p.y), d(p.z), d(v.x), d(v.y), d(v.z),
                    d(speed), d(horizontal),
                    d(aircraft.getYRot()), d(aircraft.getXRot()), d(IaRuntimeAccess.roll(aircraft)),
                    d(IaRuntimeAccess.engineTarget(aircraft)), d(IaRuntimeAccess.enginePower(aircraft)),
                    d(IaRuntimeAccess.fuelUtilization(aircraft)),
                    d(0), d(0), d(0),
                    d(IaRuntimeAccess.smooth(aircraft, "pressingInterpolatedX")),
                    d(IaRuntimeAccess.smooth(aircraft, "pressingInterpolatedY")),
                    d(IaRuntimeAccess.smooth(aircraft, "pressingInterpolatedZ")));
            writer.write(row);
            writer.newLine();
            writer.flush();
        }

        void close() throws IOException {
            try {
                writer.close();
            } finally {
                for (long key : forcedChunks) {
                    ChunkPos pos = new ChunkPos(key);
                    level.setChunkForced(pos.x, pos.z, false);
                }
                forcedChunks.clear();
                visitedChunks.clear();
            }
        }
    }

    private static String d(double v) {
        return String.format(Locale.ROOT, "%.12f", v);
    }
}
