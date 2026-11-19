package dev.kneekura.fivedifficulties.core.x1;

import dev.kneekura.fivedifficulties.core.math.Vec3d;

/** World-independent pieces of X1 EntityTHShot special shots and the THShotLib vector helpers. */
public final class X1ShotSpecials {
    private X1ShotSpecials() {}

    /** THShotLib.halfAbsSin. */
    public static double halfAbsSin(float angle) {
        angle = angle * 0.5F;
        return Math.abs(Math.sin(angle));
    }

    /** THShotLib.getAngleMax180. */
    public static float angleMax180(float angle) {
        angle %= 360F;
        if (angle > 180F) angle -= 360F;
        else if (angle < -180) angle += 360F;
        return angle;
    }

    /** THShotLib.getVectorNomalize: length through MathHelper.sqrt_double (float). */
    public static Vec3d normalize(Vec3d v) {
        double length = (double) (float) Math.sqrt(v.x() * v.x() + v.y() * v.y() + v.z() * v.z());
        length = 1.0D / length;
        return new Vec3d(v.x() * length, v.y() * length, v.z() * length);
    }

    /** THShotLib.getVectorAndVectorAngle, degrees. */
    public static float vectorAngle(Vec3d a, Vec3d b) {
        double inner = a.x() * b.x() + a.y() * b.y() + a.z() * b.z();
        return angleMax180((float) (Math.acos(inner / (a.length() * b.length())) / Math.PI * 180.0D));
    }

    /** THShotLib.getOuterProduct. */
    public static Vec3d cross(Vec3d a, Vec3d b) {
        return new Vec3d(a.y() * b.z() - a.z() * b.y(), a.z() * b.x() - a.x() * b.z(), a.x() * b.y() - a.y() * b.x());
    }

    /** X1 homing target score: distance * halfAbsSin(angle as radians). Lower wins. */
    public static double homingScore(double distance, float angleSpanDegrees) {
        return distance * halfAbsSin(angleSpanDegrees / 180F * (float) Math.PI);
    }

    /** Initial best score in EntityTHShot.homing: 999.9 * halfAbsSin(pi). */
    public static double homingInitialScore() {
        return 999.9D * halfAbsSin(180F / 180F * (float) Math.PI);
    }

    /**
     * Turn half of EntityTHShot.homing: rotate {@code angle} toward {@code toTarget} about the
     * (non-normalized, literal) cross product, clamped to +-level degrees. Returns the new angle.
     */
    public static Vec3d homingTurn(Vec3d angle, Vec3d toTarget, float level) {
        Vec3d shotVec = normalize(angle);
        Vec3d targetVec = normalize(toTarget);
        Vec3d rotate = cross(shotVec, targetVec);
        float rotateAngle = vectorAngle(shotVec, targetVec);
        if (rotateAngle > level) rotateAngle = level;
        else if (rotateAngle < -level) rotateAngle = -level;
        return X1WideShotGeometry.rotateAroundAxisRaw(rotate, angle, rotateAngle);
    }

    /**
     * One reflection of EntityTHShot.bound: side is the 1.7.10 sideHit (0/1 Y, 2/3 Z, 4/5 X),
     * which is also the 1.20 Direction ordinal.
     */
    public static Vec3d reflect(Vec3d motion, int side, double returnRate) {
        return switch (side) {
            case 0, 1 -> new Vec3d(motion.x(), motion.y() * -returnRate, motion.z());
            case 2, 3 -> new Vec3d(motion.x(), motion.y(), motion.z() * -returnRate);
            case 4, 5 -> new Vec3d(motion.x() * -returnRate, motion.y(), motion.z());
            default -> motion;
        };
    }

    /** EntityTHShot.diffusion: the three sphere bursts {first speed, acceleration, way}. */
    public static final double[][] DIFFUSION_BURSTS = {{0.6D, 0.00D, 20}, {0.4D, 0.01D, 16}, {0.2D, 0.01D, 8}};
    public static final double DIFFUSION_LIMIT_SPEED = 0.6D;
    public static final double DIFFUSION_GRAVITY = 0.09D;

    /** ShotData used by EntityTHShot.specialMotion for DIFFUSION01. */
    public static X1ShotData diffusionShot() {
        return X1ShotData.shot(X1ShotTables.FORM_AMULET, X1ShotTables.BLUE, 0.4F, 5.0F, 0, 60);
    }

    /** Gravity of the diffusion burst: the user's look vector times 0.09 (Minecraft yaw convention). */
    public static Vec3d diffusionGravity(float userYaw, float userPitch) {
        double g = DIFFUSION_GRAVITY;
        return new Vec3d(
                -Math.sin(userYaw / 180F * 3.141593F) * Math.cos(userPitch / 180F * 3.141593F) * g,
                -Math.sin(userPitch / 180F * 3.141593F) * g,
                Math.cos(userYaw / 180F * 3.141593F) * Math.cos(userPitch / 180F * 3.141593F) * g);
    }
}
