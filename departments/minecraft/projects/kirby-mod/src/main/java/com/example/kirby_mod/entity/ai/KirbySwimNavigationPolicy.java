package com.example.kirby_mod.entity.ai;

/** Pure steering decisions used by the water navigation Goal. */
public final class KirbySwimNavigationPolicy {

    private static final double MIN_VECTOR_LENGTH = 1.0E-6D;
    private static final double MOVE_ALIGNMENT_COSINE = Math.cos(Math.toRadians(55.0D));

    private KirbySwimNavigationPolicy() {}

    public static boolean canPropel(
            double lookX,
            double lookY,
            double lookZ,
            double waypointX,
            double waypointY,
            double waypointZ) {
        double lookLength = length(lookX, lookY, lookZ);
        double waypointLength = length(waypointX, waypointY, waypointZ);
        if (lookLength <= MIN_VECTOR_LENGTH || waypointLength <= MIN_VECTOR_LENGTH) {
            return false;
        }
        double cosine = (lookX * waypointX + lookY * waypointY + lookZ * waypointZ)
                / (lookLength * waypointLength);
        return cosine >= MOVE_ALIGNMENT_COSINE;
    }

    public static boolean targetMoved(
            double previousX,
            double previousY,
            double previousZ,
            double currentX,
            double currentY,
            double currentZ,
            double threshold) {
        if (!Double.isFinite(previousX) || !Double.isFinite(previousY)
                || !Double.isFinite(previousZ)) {
            return true;
        }
        double dx = currentX - previousX;
        double dy = currentY - previousY;
        double dz = currentZ - previousZ;
        double safeThreshold = Math.max(0.0D, threshold);
        return dx * dx + dy * dy + dz * dz > safeThreshold * safeThreshold;
    }

    private static double length(double x, double y, double z) {
        return Math.sqrt(x * x + y * y + z * z);
    }
}
