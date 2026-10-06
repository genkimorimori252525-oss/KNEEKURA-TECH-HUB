package dev.kneekura.fivedifficulties.core;

import dev.kneekura.fivedifficulties.core.legacy.*;
import dev.kneekura.fivedifficulties.core.math.Vec3d;

public final class LegacyPatternCoreRegression {
    public static void main(String[] args) {
        LegacyShotSpec shot = new LegacyShotSpec(
                7, 2, 2.0, 0.0, 2.0, 0.0, 1.0, 4.0,
                false, 0.0, 0, 200, 0
        );
        LegacyPattern pattern = LegacyPatterns.fan(shot, 4, 5, 40.0, 3, 10.0);
        LegacyPatternRuntime runtime = new LegacyPatternRuntime(pattern);
        PatternContext normal = new PatternContext(Vec3d.ZERO, new Vec3d(0, 0, 1), false, 123L);

        PatternFrame f0 = runtime.step(normal);
        check(f0.tick() == 0, "first tick");
        check(f0.shots().size() == 5, "normal fan count");
        check(f0.lasers().isEmpty(), "no lasers");
        close(f0.shots().get(2).velocity().x(), 0.0, "center x");
        close(f0.shots().get(2).velocity().z(), 2.0, "center z");
        close(f0.shots().get(0).velocity().x(), -f0.shots().get(4).velocity().x(), "fan symmetry x");
        close(f0.shots().get(0).velocity().z(), f0.shots().get(4).velocity().z(), "fan symmetry z");

        check(runtime.step(normal).shots().isEmpty(), "tick1 empty");
        check(runtime.step(normal).shots().isEmpty(), "tick2 empty");
        check(runtime.step(normal).shots().isEmpty(), "tick3 empty");
        check(runtime.step(normal).shots().size() == 5, "tick4 fan");

        runtime.reset();
        PatternContext focused = new PatternContext(Vec3d.ZERO, new Vec3d(0, 0, 1), true, 123L);
        PatternFrame focus = runtime.step(focused);
        check(focus.shots().size() == 3, "focused fan count");
        close(focus.shots().get(1).velocity().z(), 2.0, "focused center");

        runtime.reset();
        PatternFrame again = runtime.step(normal);
        check(again.equals(f0), "reset must be deterministic");

        LegacyLaserSpec laserSpec = new LegacyLaserSpec(4, 1.5, 32.0, 6.0, 3, 20, true);
        LegacyPattern laserPattern = (tick, context, sink) -> {
            if (tick == 2) sink.laser(new LaserSpawn(tick, 9L, context.origin(), context.aimDirection(), laserSpec));
        };
        LegacyPatternRuntime laserRuntime = new LegacyPatternRuntime(laserPattern);
        check(laserRuntime.step(normal).lasers().isEmpty(), "laser tick0");
        check(laserRuntime.step(normal).lasers().isEmpty(), "laser tick1");
        PatternFrame laserFrame = laserRuntime.step(normal);
        check(laserFrame.lasers().size() == 1, "laser tick2");
        close(laserFrame.lasers().get(0).direction().length(), 1.0, "laser direction normalized");

        System.out.println("LEGACY_PATTERN_CORE_REGRESSION_PASS");
    }

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    private static void close(double actual, double expected, String message) {
        if (Math.abs(actual - expected) > 1.0e-9) {
            throw new AssertionError(message + ": " + actual + " != " + expected);
        }
    }
}
