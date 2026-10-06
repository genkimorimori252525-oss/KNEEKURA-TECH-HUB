package org.kneekura.techhub.warfarewings.physics;

import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;

public final class Ia133MicrokernelSelfTest {
    private static final World FLAT = new FlatWorld(0.0);
    private static int checks;

    public static void main(String[] args) {
        inputSmoothingHasOneTickPhaseLag();
        enginePowerHasOneTickPhaseLag();
        brakingUsesHardcoded133Factor();
        gravityDependsOnHorizontalishSpeed();
        liftBendsVelocityTowardNose();
        driftDragIsNotRuntimeFriction();
        performanceOrderingMatchesModelIntent();
        System.out.println("Ia133MicrokernelSelfTest passed: " + checks + " checks");
    }

    private static void inputSmoothingHasOneTickPhaseLag() {
        Model m = WarfareWingsAircraft.a6m();
        State start = State.airborne(new Vec3(0, 100, 0), new Vec3(0, 0, 0.7));
        State one = tick(m, start, new Control(1, 0, 0, 0), FLAT);
        near(one.yawDeg(), 0, 1e-12, "current raw X must not affect same-tick yaw");
        near(one.smoothX(), 0.1, 1e-12, "post-move input smoothing");
        State two = tick(m, one, new Control(1, 0, 0, 0), FLAT);
        double retention = (1.0 - m.friction()) * m.rotationDecay();
        near(two.yawDeg(), -m.yawSpeed() * (0.1 * retention), 1e-10,
                "second tick uses decayed previous smooth X");
    }

    private static void enginePowerHasOneTickPhaseLag() {
        Model m = WarfareWingsAircraft.a6m();
        State start = State.airborne(new Vec3(0, 100, 0), new Vec3(0, 0, 0.7));
        State one = tick(m, start, Control.neutral(1), FLAT);
        near(one.enginePowerSmooth(), 0.05, 1e-12, "engine smoothing advances after movement");
        near(one.velocity().z(), 0.7 * (1.0 - m.friction()) * m.horizontalDecay(), 1e-10,
                "first tick consumes previous zero engine power");
        State two = tick(m, one, Control.neutral(1), FLAT);
        require(two.velocity().z() > one.velocity().z() * (1.0 - m.friction()) * m.horizontalDecay(),
                "second tick must contain thrust");
    }

    private static void brakingUsesHardcoded133Factor() {
        Model m = WarfareWingsAircraft.a6m();
        State end = tick(m, State.airborne(new Vec3(0, 100, 0), new Vec3(0, 0, 1)),
                new Control(0, -1, 0, 0), FLAT);
        near(end.velocity().z(), (1.0 - m.friction()) * m.horizontalDecay() * BRAKE_FACTOR_133,
                1e-10, "1.3.3 hard-coded brake");
    }

    private static void gravityDependsOnHorizontalishSpeed() {
        Vec3 f = new Vec3(0, 0, 1);
        near(airplaneGravity(new Vec3(0, 0, 0.7), f), 0, 1e-12, "fast horizontal gravity suppression");
        near(airplaneGravity(new Vec3(0, 0, 0.3), f), -0.022, 1e-12, "low-speed partial gravity");
    }

    private static void liftBendsVelocityTowardNose() {
        Model m = WarfareWingsAircraft.a6m();
        Vec3 converted = convertPower(new Vec3(1, 0, 0), new Vec3(0, 0, 1), m.lift(), m.friction());
        require(converted.z() > 0, "lift must bend sideways velocity toward nose");
        require(converted.x() < 1, "sideways component must reduce");
    }

    private static void driftDragIsNotRuntimeFriction() {
        Model m = WarfareWingsAircraft.a6m();
        near(m.rawDriftDrag(), 0.008, 1e-12, "raw driftDrag provenance");
        near(m.friction(), 0.015, 1e-12, "IA 1.3.3 runtime friction default");
        require(m.rawDriftDrag() != m.friction(), "no silent driftDrag substitution");
    }

    private static void performanceOrderingMatchesModelIntent() {
        PerformanceReportMain.Result a6m = PerformanceReportMain.evaluate(WarfareWingsAircraft.a6m(), WarfareWingsAircraft.legacyA6m());
        PerformanceReportMain.Result p47 = PerformanceReportMain.evaluate(WarfareWingsAircraft.p47n(), WarfareWingsAircraft.legacyP47n());
        require(p47.sourcePredictedTopSpeedBps() > a6m.sourcePredictedTopSpeedBps(), "P-47N speed tendency");
        require(a6m.yawChange20TicksDeg() > p47.yawChange20TicksDeg(), "A6M yaw authority");
        require(a6m.pitchChange20TicksDeg() > p47.pitchChange20TicksDeg(), "A6M pitch authority");
        require(p47.durability() > a6m.durability(), "P-47N durability");
    }

    private static void near(double actual, double expected, double tolerance, String detail) {
        checks++;
        if (Math.abs(actual - expected) > tolerance)
            throw new AssertionError(detail + ": expected=" + expected + " actual=" + actual);
    }
    private static void require(boolean condition, String detail) {
        checks++;
        if (!condition) throw new AssertionError(detail);
    }
}
