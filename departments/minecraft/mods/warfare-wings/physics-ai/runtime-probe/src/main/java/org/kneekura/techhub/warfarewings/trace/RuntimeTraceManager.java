package org.kneekura.techhub.warfarewings.trace;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.fml.loading.FMLPaths;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;

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
        try {
            Path dir = FMLPaths.GAMEDIR.get().resolve("ww-physics-traces");
            Files.createDirectories(dir);
            Path path = dir.resolve("a6m-throttle-step-v1-runtime.csv");
            BufferedWriter writer = Files.newBufferedWriter(path, StandardCharsets.UTF_8);
            writer.write(HEADER);
            writer.newLine();
            active = new Run(level, aircraft, pilot, writer, path);
            active.write(0);
        } catch (IOException e) {
            throw new IllegalStateException("Could not open runtime trace", e);
        }
    }

    static synchronized boolean complete() { return complete; }
    static synchronized String failure() { return failure; }

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
        int sampleTick;
        boolean skipFirstEnd = true;

        Run(ServerLevel level, Entity aircraft, ArmorStand pilot, BufferedWriter writer, Path path) {
            this.level = level;
            this.aircraft = aircraft;
            this.pilot = pilot;
            this.writer = writer;
            this.path = path;
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
            writer.close();
        }
    }

    private static String d(double v) {
        return String.format(Locale.ROOT, "%.12f", v);
    }
}