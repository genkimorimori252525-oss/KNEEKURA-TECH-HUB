package dev.kneekura.fivedifficulties.core.x1;

import dev.kneekura.fivedifficulties.core.math.Vec3d;

/** Exact static port of THKaguyaLib.itemEffectFollowUser for Sakuya Watch. */
public final class X1SakuyaControllerGeometry {
    private X1SakuyaControllerGeometry() {}

    public static Vec3d center(
            Vec3d sourcePosition,
            double sourceEyeHeight,
            double yawDegrees,
            double pitchDegrees
    ) {
        if (sourcePosition == null) throw new NullPointerException("sourcePosition");
        if (!Double.isFinite(sourceEyeHeight)
                || !Double.isFinite(yawDegrees)
                || !Double.isFinite(pitchDegrees)) {
            throw new IllegalArgumentException("non-finite source pose");
        }

        double yaw = Math.toRadians(yawDegrees + SakuyaWatchContract.CONTROLLER_YAW_OFFSET_DEGREES);
        double pitch = Math.toRadians(pitchDegrees);
        double distance = SakuyaWatchContract.CONTROLLER_FOLLOW_DISTANCE;

        double x = sourcePosition.x() - Math.sin(yaw) * Math.cos(pitch) * distance;
        double z = sourcePosition.z() + Math.cos(yaw) * Math.cos(pitch) * distance;
        double y = sourcePosition.y()
                - Math.sin(pitch) * distance
                + sourceEyeHeight
                + SakuyaWatchContract.CONTROLLER_EYE_Y_OFFSET;

        return new Vec3d(x, y, z);
    }
}
