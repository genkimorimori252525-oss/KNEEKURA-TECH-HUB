package dev.kneekura.fivedifficulties.core;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.HomingAmuletContract;
import dev.kneekura.fivedifficulties.core.x1.HomingAmuletVisualContract;
import dev.kneekura.fivedifficulties.core.x1.X1WideShotGeometry;
import java.util.List;

public final class X1WideShotGeometryRegression {
    public static void main(String[] args) {
        Vec3d forward = new Vec3d(0.0, 0.0, 1.0);

        List<X1WideShotGeometry.Ray> normal = X1WideShotGeometry.create(
                forward,
                HomingAmuletContract.NORMAL.shotCount(),
                HomingAmuletContract.NORMAL.totalSpreadDegrees(),
                HomingAmuletContract.NORMAL.spawnDistance(),
                HomingAmuletContract.NORMAL.baseAngleDegrees()
        );
        check(normal.size() == 5, "normal way count");
        double[] normalOffsets = {-50.0, -25.0, 0.0, 25.0, 50.0};
        for (int i = 0; i < normal.size(); i++) {
            close(normal.get(i).offsetDegrees(), normalOffsets[i], "normal offset " + i);
            close(normal.get(i).direction().length(), 1.0, "normal unit " + i);
            close(normal.get(i).spawnOffset().length(), 0.5, "normal spawn distance " + i);
        }
        close(normal.get(0).direction().x(), Math.sin(Math.toRadians(50.0)), "legacy -50 x sign");
        close(normal.get(4).direction().x(), -Math.sin(Math.toRadians(50.0)), "legacy +50 x sign");
        close(normal.get(2).direction().z(), 1.0, "normal center forward");

        List<X1WideShotGeometry.Ray> focused = X1WideShotGeometry.create(
                forward,
                HomingAmuletContract.FOCUSED.shotCount(),
                HomingAmuletContract.FOCUSED.totalSpreadDegrees(),
                HomingAmuletContract.FOCUSED.spawnDistance(),
                HomingAmuletContract.FOCUSED.baseAngleDegrees()
        );
        check(focused.size() == 2, "focus way count");
        close(focused.get(0).offsetDegrees(), -10.0, "focus left");
        close(focused.get(1).offsetDegrees(), 10.0, "focus right");

        check(HomingAmuletVisualContract.SOURCE_SHOT_TEXTURE_WIDTH == 64, "shot texture width");
        check(HomingAmuletVisualContract.SOURCE_SHOT_TEXTURE_HEIGHT == 32, "shot texture height");
        close(HomingAmuletVisualContract.U_MAX, 0.5, "legacy left-half UV");
        close(HomingAmuletVisualContract.RED_FIRST_PASS_SCALE, 0.5, "legacy first pass scale");
        close(HomingAmuletVisualContract.RED_SECOND_PASS_EFFECTIVE_SCALE, 0.275, "legacy second pass effective scale");

        // Critical fidelity boundary: focused ShotData.size=1.0 changes entity/hit geometry,
        // while RenderHomingAmulet still uses the same red visual scale as normal mode.
        close(HomingAmuletContract.NORMAL.shotSize(), 0.4, "normal logical size");
        close(HomingAmuletContract.FOCUSED.shotSize(), 1.0, "focus logical size");
        close(HomingAmuletVisualContract.RED_FIRST_PASS_SCALE, 0.5, "red visual scale independent of logical size");

        System.out.println("X1_WIDE_SHOT_GEOMETRY_REGRESSION_PASS");
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
