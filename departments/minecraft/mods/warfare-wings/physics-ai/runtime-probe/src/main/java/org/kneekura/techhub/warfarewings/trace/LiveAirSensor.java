package org.kneekura.techhub.warfarewings.trace;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.kneekura.techhub.warfarewings.physics.TacticalAirAI;

/**
 * Observes actual entities in the same dimension, subject to geometric FOV,
 * distance and Minecraft block occlusion. Team eligibility is decided by
 * explicit RuntimeTacticalPilot orders before calling this class.
 *
 * This has no connection to the legacy GameTest's predesignated ArmorStand:
 * live contacts must pass each visibility check on every server tick.
 */
final class LiveAirSensor {
    static final double DEFAULT_RANGE = 240.0;
    static final double DEFAULT_FULL_FOV_DEG = 150.0;

    private LiveAirSensor() {}

    static TacticalAirAI.Contact observe(ServerLevel world, Entity observer, Entity candidate) {
        if (world == null || observer == null || candidate == null
                || observer == candidate || candidate.isRemoved()
                || observer.level() != world || candidate.level() != world) return null;
        Vec3 from = observer.getBoundingBox().getCenter();
        Vec3 to = candidate.getBoundingBox().getCenter();
        Vec3 direction = to.subtract(from);
        double distanceSq = direction.lengthSqr();
        if (!Double.isFinite(distanceSq) || distanceSq < 1e-6
                || distanceSq > DEFAULT_RANGE * DEFAULT_RANGE) return null;
        if (!insideCone(observer.getYRot(), observer.getXRot(), direction,
                DEFAULT_FULL_FOV_DEG)) return null;
        var ray = world.clip(new ClipContext(from, to, ClipContext.Block.COLLIDER,
                ClipContext.Fluid.NONE, observer));
        if (ray.getType() != HitResult.Type.MISS) return null;
        Vec3 velocity = candidate.getDeltaMovement();
        return new TacticalAirAI.Contact(candidate.getUUID().toString(),
                new org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.Vec3(
                        candidate.getX(), candidate.getY(), candidate.getZ()),
                new org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.Vec3(
                        velocity.x, velocity.y, velocity.z), true);
    }

    // IA forward convention verified in the pinned source:
    // yaw=0 -> +Z; positive pitch looks down.
    static boolean insideCone(double yawDeg, double pitchDeg, Vec3 toTarget,
                              double fullFovDeg) {
        if (!Double.isFinite(yawDeg) || !Double.isFinite(pitchDeg)
                || !Double.isFinite(fullFovDeg) || fullFovDeg <= 0
                || fullFovDeg > 360 || toTarget == null
                || !Double.isFinite(toTarget.x) || !Double.isFinite(toTarget.y)
                || !Double.isFinite(toTarget.z) || toTarget.lengthSqr() < 1e-12)
            return false;
        double yaw = Math.toRadians(yawDeg), pitch = Math.toRadians(pitchDeg);
        Vec3 forward = new Vec3(-Math.sin(yaw) * Math.cos(pitch),
                -Math.sin(pitch), Math.cos(yaw) * Math.cos(pitch));
        return forward.dot(toTarget.normalize()) >= Math.cos(Math.toRadians(fullFovDeg * .5));
    }

    /** Source-only unit checks for the visibility cone; block occlusion needs Forge runtime. */
    public static void main(String[] args) {
        check(insideCone(0, 0, new Vec3(0, 0, 30), 150), "forward +Z visible");
        check(!insideCone(0, 0, new Vec3(0, 0, -30), 150), "rear -Z hidden");
        check(insideCone(-90, 0, new Vec3(30, 0, 0), 150), "yaw east visible");
        check(!insideCone(-90, 0, new Vec3(-30, 0, 0), 150), "yaw west hidden");
        check(insideCone(0, -45, new Vec3(0, 20, 20), 100), "pitch-up visible");
        check(!insideCone(0, -45, new Vec3(0, -20, 20), 100), "opposite vertical hidden");
        System.out.println("LiveAirSensor geometry passed: FOV/yaw/pitch; real block LOS NOT_RUN");
    }

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
}
