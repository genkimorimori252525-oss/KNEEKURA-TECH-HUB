package org.kneekura.techhub.warfarewings.physics;

import java.nio.file.Path;
import java.util.List;
import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;

/**
 * All 24 airframe role-independent navigator pilots through the same 20 Hz
 * command loop using the exact user JAR's engine reactions, with legacy V2 as
 * a separate independently integrated control. No actual combat claims.
 */
public final class ExactReactionSquadronSelfTest {
    private static int checks;
    private static void require(boolean yes, String reason) {
        checks++;
        if (!yes) throw new AssertionError(reason);
    }
    public static void main(String[] args) throws Exception {
        if (args.length != 1) throw new IllegalArgumentException("exact Atlas CSV path");
        Path atlas = Path.of(args[0]);
        var data = AircraftAtlasMain.load(atlas);
        require(data.size() == 24, "must cover exact all24");
        var world = new FlatWorld(0);
        for (var airframe : data) {
            String id = airframe.aircraftId();
            var craft = new SquadronCommand.AircraftSpec(
                    "solo", id, "blue", "solo", 0,
                    TacticalAirAI.Mission.PATROL, null, null,
                    new Vec3(0, 200, 0), new Vec3(0, 0, .7), 0,
                    new Vec3(130, 205, 450), new Vec3(0, 205, -200),
                    1, 1, 0);
            var legacy = SquadronCommand.load(atlas, List.of(craft), world, SquadronCommand.Sensors.DEFAULT);
            var exact = SquadronCommand.loadWithExactReaction(
                    atlas, List.of(craft), world, SquadronCommand.Sensors.DEFAULT);
            var v2 = legacy.start();
            var v3 = exact.start();
            double expectedPower = 0;
            double alpha = 1.0 / WarfareWingsEngineReaction.ticks(id);
            for (int t=1;t<=140;t++) {
                var old=legacy.advance(v2);
                var modern=exact.advance(v3);
                v2=old.next();
                v3=modern.next();
                var sample=v3.units().get("solo").aircraft();
                require(sample.tick() == t, id+" actual 20Hz source tick");
                require(Double.isFinite(sample.position().x()) &&
                        Double.isFinite(sample.position().y()) &&
                        Double.isFinite(sample.yawDeg()), id+" finite physical flight");
                require(!sample.onGround(), id+" source flight has not touched terrain");
                var pilot=modern.commands().get("solo").decision().controls();
                require(Math.abs(pilot.x()) <= 1 && Math.abs(pilot.z()) <= 1
                        && pilot.engineTarget() >= 0 && pilot.engineTarget() <= 1,
                        id+" bounded actual command through source");
                // The patrol commander may choose throttle <1 and safety
                // overrides may raise it. Integrate the ACTUALLY issued
                // target, not an invented constant-full-throttle input.
                expectedPower = expectedPower*(1.0-alpha) + pilot.engineTarget()*alpha;
                require(Math.abs(sample.enginePowerSmooth()-expectedPower)<2e-6,
                        id+" source engine response to actual 20Hz issued throttle");
            }
            var recent = v3.units().get("solo").aircraft();
            var previous = v2.units().get("solo").aircraft();
            require(recent.position().length() > 10 && recent.position().z() > 25,
                    id+" physical forward progress");
            require(recent.enginePowerSmooth() < previous.enginePowerSmooth(),
                    id+" source reaction overrides materially slower than old20");
            require(Math.abs(recent.enginePowerSmooth()-expectedPower)<2e-6,
                    id+" exact bytecode response to the nonconstant squadron controls");
        }
        System.out.println("ExactReactionSquadronSelfTest passed: " + checks
                + " checks, 24 aircraft x 140 physically integrated calibrated source ticks");
    }
}
