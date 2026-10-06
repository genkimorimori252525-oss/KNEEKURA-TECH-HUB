package org.kneekura.techhub.warfarewings.physics;

import java.util.Locale;

public final class TraceCsv {
    public static final String VERSION = "ww.physics.trace.v1";
    public static final String HEADER =
            "schema_version,source,scenario_id,aircraft_id,tick,game_time," +
            "pos_x,pos_y,pos_z,vel_x,vel_y,vel_z,speed_bps,horizontal_speed_bps," +
            "yaw_deg,pitch_deg,roll_deg,engine_target,engine_power,fuel_utilization," +
            "raw_x,raw_y,raw_z,smooth_x,smooth_y,smooth_z";

    private TraceCsv() {}

    public record Frame(
            String source, String scenarioId, String aircraftId, long tick, Long gameTime,
            double posX, double posY, double posZ,
            double velX, double velY, double velZ,
            double yawDeg, double pitchDeg, double rollDeg,
            double engineTarget, double enginePower, double fuelUtilization,
            double rawX, double rawY, double rawZ,
            double smoothX, double smoothY, double smoothZ) {}

    public static String row(Frame f) {
        double speed = Math.sqrt(f.velX()*f.velX()+f.velY()*f.velY()+f.velZ()*f.velZ()) * 20.0;
        double horizontal = Math.hypot(f.velX(), f.velZ()) * 20.0;
        return String.join(",",
                VERSION, f.source(), f.scenarioId(), f.aircraftId(), Long.toString(f.tick()),
                f.gameTime()==null ? "" : Long.toString(f.gameTime()),
                d(f.posX()), d(f.posY()), d(f.posZ()),
                d(f.velX()), d(f.velY()), d(f.velZ()),
                d(speed), d(horizontal),
                d(f.yawDeg()), d(f.pitchDeg()), d(f.rollDeg()),
                d(f.engineTarget()), d(f.enginePower()), d(f.fuelUtilization()),
                d(f.rawX()), d(f.rawY()), d(f.rawZ()),
                d(f.smoothX()), d(f.smoothY()), d(f.smoothZ()));
    }

    private static String d(double v) {
        return String.format(Locale.ROOT, "%.12f", v);
    }
}
