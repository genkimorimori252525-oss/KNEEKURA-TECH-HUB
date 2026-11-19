package org.kneekura.techhub.warfarewings.physics;

import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;
import static org.kneekura.techhub.warfarewings.physics.TacticalAirAI.*;

public final class FlightGuidanceSelfTest {
    private static int checks;
    private static final Model MODEL = WarfareWingsAircraft.a6m();
    private static final Profile PROFILE = new Profile(MODEL.id(), MODEL.role(), "ijn",
            MODEL.doctrine(), 33.67, 34.23, 42, 0.9255);
    private static void check(boolean yes, String why) {
        checks++;
        if (!yes) throw new AssertionError(why);
    }
    private static Frame frame(State state, double ground) {
        return new Frame(PROFILE, MODEL, state, Mission.PATROL,
                new Vec3(500, 150, 0), new Vec3(0, 150, -200),
                null, null, null, 1, 1, ground, false, 0);
    }
    private static State angled(double yaw, double pitch, double smoothX, double smoothZ) {
        return new State(0, new Vec3(0, 180, 0), new Vec3(0, 0, 0.7), yaw, pitch, 0,
                0, 0, 0, smoothX, 0, smoothZ,
                1, 1, 1, 180, false, false);
    }
    public static void main(String[] args) {
        check(FlightGuidance.wrapDeg(359) == -1, "wrap 359 to -1");
        check(FlightGuidance.wrapDeg(-359) == 1, "wrap -359 to 1");
        check(FlightGuidance.wrapDeg(181) == -179, "wrap 181");
        check(FlightGuidance.plan(frame(angled(0,0,0,0),0),
                new Vec3(100,180,0), 1).control().x() > 0, "east requires raw positive X");
        check(FlightGuidance.plan(frame(angled(0,0,0,0),0),
                new Vec3(-100,180,0), 1).control().x() < 0, "west requires raw negative X");
        check(FlightGuidance.plan(frame(angled(0,0,0,0),0),
                new Vec3(0,260,100),1).control().z() < 0, "above requires negative raw Z");
        check(FlightGuidance.plan(frame(angled(0,0,0,0),0),
                new Vec3(0,120,100),1).control().z() > 0, "below requires positive raw Z");
        check(FlightGuidance.plan(frame(angled(0,0,0.7,0),0),
                new Vec3(0,180,100),1).control().x() < 0,
                "smoothed positive X requires opposite counter-control before drift");
        check(FlightGuidance.plan(frame(angled(-179,0,0,0),0),
                new Vec3(0,180,-100),1).yawErrorDeg() > -2,
                "yaw seam must not demand a complete revolution");
        check(FlightGuidance.plan(frame(angled(0,0,0,0),170),
                new Vec3(0,260,100),0.1).control().engineTarget() >= 0.95,
                "climb near ground demands engine margin");
        check(FlightGuidance.plan(frame(angled(0,0,0,0),0),
                new Vec3(0,180,3),1).control().engineTarget() <= 0.58,
                "slow approach near a station");
        boolean rejected = false;
        try { FlightGuidance.plan(frame(angled(0,0,0,0),0),
                new Vec3(Double.NaN,1,1),1); }
        catch (IllegalArgumentException expected) { rejected = true; }
        check(rejected, "nonfinite target rejected");

        // Test the actual source-physics closed loop, not only one-step signs.
        State s = angled(0, 0, 0, 0);
        Vec3 east = new Vec3(200,180,0);
        double firstError = Math.abs(FlightGuidance.plan(frame(s, 0),east,1).yawErrorDeg());
        double minError = firstError;
        for (int i=0; i<100; i++) {
            Control raw = FlightGuidance.plan(frame(s,0),east,1).control();
            check(Math.abs(raw.x()) <= 1 && Math.abs(raw.z()) <= 1,
                    "raw commands bounded after filter");
            s = tick(MODEL, s, raw, new FlatWorld(0));
            minError = Math.min(minError,
                    Math.abs(FlightGuidance.plan(frame(s,0),east,1).yawErrorDeg()));
            check(Double.isFinite(s.yawDeg()) && Double.isFinite(s.pitchDeg()), "finite attitude");
        }
        check(minError < 18, "aircraft heading must approach requested track");
        System.out.println("FlightGuidanceSelfTest passed: " + checks + " checks");
    }
}
