package org.kneekura.techhub.warfarewings.physics;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;

/**
 * Replay the unmodified NEXT-TICK IA flight-control input stream from real
 * multi-aircraft/escort/strike/RTB GameTests. Crucially, this does not rerun
 * decisions using all known opponents: it reads only the command that was
 * actually issued to the tested aircraft by the real observed-only sensor.
 *
 * This existing tactical receipt lacks roll, fuel and actual collision state;
 * consequently these are documented assumptions (no roll parity claim,
 * fuel=1 as configured by GameTest, flat airborne far from collision blocks).
 */
public final class RealTacticalPhysicsTwinReplayMain {
    private static final String HEADER =
            "schema_version,source,scenario_id,aircraft_id,sim_tick,game_time," +
            "pos_x,pos_y,pos_z,vel_x,vel_y,vel_z,yaw_deg,pitch_deg," +
            "engine_target,engine_power,smooth_x,smooth_z," +
            "command_x,command_z,command_throttle,maneuver,reason," +
            "world_safety_reason,terrain_clearance_blocks";
    private RealTacticalPhysicsTwinReplayMain() {}

    static List<RealPhysicsTwinReplayMain.Observation> loadLive(Path csv, String scenario,
                                                                String aircraftId) throws IOException {
        if (!scenario.matches("[a-z0-9_-]+") || !aircraftId.matches("warfare_wings:[a-z0-9]+"))
            throw new IllegalArgumentException("Unsafe/unknown real flight scenario identity");
        List<String> lines = Files.readAllLines(csv, StandardCharsets.UTF_8);
        if (lines.size() < 5 || !HEADER.equals(lines.get(0)))
            throw new IllegalArgumentException("Real Forge tactical control CSV header mismatch");
        List<RealPhysicsTwinReplayMain.Observation> rows = new ArrayList<>();
        for (int i=1;i<lines.size();i++) {
            String[] c = lines.get(i).split(",", -1);
            if (c.length != 25 || !"ww.physics.forge-tactical-pilot.v1".equals(c[0])
                    || !"minecraft_runtime_ia_next_tick_injection".equals(c[1])
                    || !scenario.equals(c[2]) || !aircraftId.equals(c[3]))
                throw new IllegalArgumentException("Real tactical physics identity/source changed at " + i);
            long tick = Long.parseLong(c[4]);
            long clock = Long.parseLong(c[5]);
            if (tick != i-1)
                throw new IllegalArgumentException("Non-consecutive ORIGINAL aircraft physics tick in "
                        + scenario + " at CSV sample=" + i + " expected=" + (i-1)
                        + " recorded=" + tick);
            if (i > 1 && clock != rows.get(i-2).gameTime() + 1)
                throw new IllegalArgumentException("ORIGINAL_MINECRAFT_SERVER_CLOCK_GAP: " + scenario
                        + " aircraft_tick=" + tick
                        + " previous_game_time=" + rows.get(i-2).gameTime()
                        + " current_game_time=" + clock
                        + " missing_server_ticks=" + (clock - rows.get(i-2).gameTime() - 1)
                        + "; external free-air parity NOT ESTABLISHED");
            double clearance = d(c,24);
            if (i>1 && clearance < 10)
                throw new IllegalArgumentException("Ground/voxel contact may matter; no flat-world source replay at " + i);
            // The real per-tick commands were injected at tick END and
            // therefore affect exactly the NEXT aircraft physics update.
            // No attacker position/velocity or delayed sensor may be invented.
            double rawX=d(c,18), rawZ=d(c,19), target=d(c,14), throttle=d(c,20);
            if (rawX < -1 || rawX > 1 || rawZ < -1 || rawZ > 1
                    || target < 0 || target > 1 || throttle < 0 || throttle > 1
                    || Math.abs(target - throttle) > 1e-4 && i > 1)
                throw new IllegalArgumentException("Out-of-range/mismatched actual server pilot controls at " + i);
            if (i==1 && (!"INITIAL".equals(c[21]) || !"INITIAL".equals(c[22])))
                throw new IllegalArgumentException("Real tactical initial state missing");
            rows.add(new RealPhysicsTwinReplayMain.Observation(scenario, aircraftId, tick, clock,
                    new Vec3(d(c,6),d(c,7),d(c,8)),
                    new Vec3(d(c,9),d(c,10),d(c,11)),
                    d(c,12),d(c,13),
                    0, target,d(c,15),1.0,rawX,0,rawZ,d(c,16),0,d(c,17)));
        }
        int repeated=0;
        for (int i=1;i<rows.size();i++) {
            var a=rows.get(i-1);var b=rows.get(i);
            if (a.position().equals(b.position()) && a.velocity().equals(b.velocity())
                    && a.power()==b.power() && a.yaw()==b.yaw() && a.pitch()==b.pitch()) repeated++;
            else repeated=0;
            if (repeated >= 3) throw new IllegalArgumentException("NON_TICKING_REAL_AIRCRAFT at " + i);
        }
        return List.copyOf(rows);
    }

    private static double d(String[] row,int index) {
        double number = Double.parseDouble(row[index]);
        if (!Double.isFinite(number)) throw new IllegalArgumentException("Non-finite real pilot telemetry at " + index);
        return number;
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 5 && (args.length != 6 || !"--pinned-wind".equals(args[5])))
            throw new IllegalArgumentException("Usage: RealTacticalPhysicsTwinReplayMain EXACT_ANCHOR_CSV AIRCRAFT_ID LIVE_SCENARIO ACTUAL_FORGE_CONTROL_CSV OUTPUT_CSV [--pinned-wind]");
        String aircraft=args[1];
        var observed=loadLive(Path.of(args[3]),args[2],aircraft);
        boolean wind = args.length==6;
        RealPhysicsTwinReplayMain.replaySamples(Path.of(args[0]),aircraft,observed,Path.of(args[4]),false,
                wind ? "tactical_pinned_wind" : "tactical_runtime",
                (wind ? "AIRBORNE_PINNED_IA_WIND" : "AIRBORNE_FLAT_NO_WIND")
                        + "|RECORDED_NEXT_TICK_AXIS_COMMAND|ROLL_UNOBSERVED|FUEL_ASSUMED_1|VOXEL_UNOBSERVED",
                wind ? PinnedIa133WindWorld.calmAirCalibration() : new FlatWorld(0));
    }
}
