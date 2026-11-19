package dev.kneekura.fivedifficulties.forge.shot;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1LaserData;
import dev.kneekura.fivedifficulties.core.x1.X1LaserPatterns;
import dev.kneekura.fivedifficulties.core.x1.X1ShotData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotMotion;
import dev.kneekura.fivedifficulties.core.x1.X1ShotPatterns;
import dev.kneekura.fivedifficulties.core.x1.X1WideShotGeometry;
import dev.kneekura.fivedifficulties.forge.entity.ShotMaterialEntity;
import dev.kneekura.fivedifficulties.forge.entity.THLaserEntity;
import dev.kneekura.fivedifficulties.forge.entity.THSetLaserEntity;
import dev.kneekura.fivedifficulties.forge.entity.THShotEntity;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;

import java.util.List;
import java.util.Random;

/**
 * A THShotLib-shaped facade over the ported emitters, so X1 spell cards and items translate almost
 * line by line. Methods keep X1 names and argument order; vectors are immutable {@link Vec3d}.
 * Shots ignore {@code source} (X1 only uses it for lasers and set lasers).
 */
public final class X1Danmaku {
    private X1Danmaku() {}

    private static ServerLevel level(Entity e) {
        return (ServerLevel) e.level();
    }

    private static X1ShotPatterns shots(LivingEntity user) {
        return X1ShotSpawner.patterns(level(user), user);
    }

    // ---- vectors (THShotLib) ----

    public static Vec3d pos(double x, double y, double z) { return new Vec3d(x, y, z); }
    public static Vec3d pos_Entity(Entity e) { return new Vec3d(e.getX(), e.getY(), e.getZ()); }
    public static Vec3d pos_Living(LivingEntity e) { return X1ShotSpawner.posLiving(e); }
    public static Vec3d angle(double x, double y, double z) { return new Vec3d(x, y, z); }
    public static Vec3d angle(float yaw, float pitch) { return getVecFromAngle(yaw, pitch); }
    public static Vec3d gravity(double x, double y, double z) { return new Vec3d(x, y, z); }
    public static Vec3d gravity(double y) { return new Vec3d(0, y, 0); }
    public static Vec3d gravity_Zero() { return Vec3d.ZERO; }
    public static Vec3d gravity_Default() { return new Vec3d(0, -0.03D, 0); }
    public static Vec3d rotate_Default() { return new Vec3d(0, 1, 0); }
    public static Vec3d getVecFromAngle(float yaw, float pitch) { return X1ShotPatterns.vecFromAngle(yaw, pitch, 1.0D); }
    public static Vec3d getVecFromAngle(float yaw, float pitch, double force) { return X1ShotPatterns.vecFromAngle(yaw, pitch, force); }
    public static Vec3d getVectorFromRotation(Vec3d rotate, Vec3d angle, float degrees) {
        return X1WideShotGeometry.rotateAroundAxisRaw(rotate, angle, degrees);
    }
    public static float getYawFromVector(double x, double z) { return X1ShotMotion.yawFromVector(x, z); }
    public static float getPitchFromVector(double x, double y, double z) { return X1ShotMotion.pitchFromVector(x, y, z); }

    /** THShotLib.angle_ToPos: unit vector from A to B (float sqrt). */
    public static Vec3d angle_ToPos(Vec3d a, Vec3d b) {
        return dev.kneekura.fivedifficulties.core.x1.X1ShotSpecials.normalize(b.subtract(a));
    }

    /** THShotLib.angle_Random: yaw 0..360, pitch -90..90. */
    public static Vec3d angle_Random(Random rand) {
        return getVecFromAngle(rand.nextFloat() * 360F, rand.nextFloat() * 180F - 90F);
    }

    /** THShotLib.rotate_Random (same distribution as angle_Random). */
    public static Vec3d rotate_Random(Random rand) {
        return angle_Random(rand);
    }

    /** THShotLib.angle_LimitRandom. */
    public static Vec3d angle_LimitRandom(Random rand, Vec3d angle, float limitAngle) {
        Vec3d rotate = rotate_Random(rand);
        return getVectorFromRotation(rotate, angle, rand.nextFloat() * limitAngle - (limitAngle / 2.0F));
    }

    /** THShotLib.getPosYFromEye. */
    public static double getPosYFromEye(LivingEntity e) {
        return X1ShotSpawner.posLiving(e).y();
    }

    /** THShotLib.getPosYFromEye(living, yAdjustment). */
    public static double getPosYFromEye(LivingEntity e, double adj) {
        return e.getY() + e.getEyeHeight() + Math.sin((double) e.getXRot() / 180.0D * Math.PI) * adj + adj;
    }

    /** THShotLib.getOuterProduct. */
    public static Vec3d getOuterProduct(Vec3d a, Vec3d b) {
        return dev.kneekura.fivedifficulties.core.x1.X1ShotSpecials.cross(a, b);
    }

    /** THShotLib.getOverVector: 90 degrees above the horizontal part of vec. */
    public static Vec3d getOverVector(Vec3d vec) {
        Vec3d flat = dev.kneekura.fivedifficulties.core.x1.X1ShotSpecials.normalize(new Vec3d(vec.x(), 0.0D, vec.z()));
        float yaw = getYawFromVector(flat.x(), flat.z());
        float pitch = getPitchFromVector(flat.x(), flat.y(), flat.z());
        return getVecFromAngle(yaw, pitch + 90F);
    }

    /** THShotLib.getRotationVector (legacy; its rotateAroundY(2 pi) is the identity via the MathHelper table). */
    public static Vec3d getRotationVector(double x, double y, double z, float angle, double force) {
        float disXZ = (float) Math.sqrt(x * x + z * z);
        float baseYaw = (float) Math.atan2(-x, z);
        float basePitch = (float) Math.atan2(-y, disXZ);
        float a = angle / 180.0F * (float) Math.PI;
        double x1 = Math.sin(a) * Math.cos(baseYaw);
        double z1 = Math.sin(a) * Math.sin(baseYaw);
        double vecY = -Math.cos(a) * Math.sin(basePitch);
        double vecX = Math.cos(a) * x + x1;
        double vecZ = Math.cos(a) * z + z1;
        return new Vec3d(vecX * force, vecY * force, vecZ * force);
    }

    /** THShotLib.getRotationVectorFromAngle. */
    public static Vec3d getRotationVectorFromAngle(float yaw, float pitch, float angle, double force) {
        Vec3d v = getVecFromAngle(yaw, pitch, 1.0D);
        return getRotationVector(v.x(), v.y(), v.z(), angle, force);
    }

    /** Entity.getLookVec. */
    public static Vec3d look(LivingEntity e) {
        return X1ShotSpawner.pure(e.getLookAngle());
    }

    // ---- shots ----

    public static void createShot(LivingEntity user, Entity source, Vec3d pos, Vec3d angle, float slope, Vec3d rotate,
                                  float rotationSpeed, int rotationEnd, double first, double limit, double accel,
                                  Vec3d gravity, X1ShotData shot) {
        shots(user).createShot(pos, angle, slope, rotate, rotationSpeed, rotationEnd, first, limit, accel, gravity, shot);
    }

    public static void createShot(LivingEntity user, Entity source, Vec3d pos, Vec3d angle, float slope, double first,
                                  double limit, double accel, Vec3d gravity, X1ShotData shot) {
        shots(user).createShot(pos, angle, slope, first, limit, accel, gravity, shot);
    }

    /** createShot(user, pos, angle, speed, shot). */
    public static void createShot(LivingEntity user, Vec3d pos, Vec3d angle, double speed, X1ShotData shot) {
        shots(user).createShot(pos, angle, 0F, speed, speed, 0.0D, Vec3d.ZERO, shot);
    }

    /**
     * The full createShot when the caller keeps the returned EntityTHShot (X1 cards set its rotate or
     * attach set lasers to it). RAINBOW / RANDOM are resolved for this shot and restored, as in X1.
     */
    public static THShotEntity createShotEntity(LivingEntity user, Entity source, Vec3d pos, Vec3d angle, float slope,
                                                Vec3d rotate, float rotationSpeed, int rotationEnd, double first,
                                                double limit, double accel, Vec3d gravity, X1ShotData shot) {
        THShotEntity[] out = new THShotEntity[1];
        ServerLevel level = level(user);
        new X1ShotPatterns(new Random(), (p, a, s, r, rs, re, f, l, ac, g, data) -> {
            out[0] = new THShotEntity(level, user, p, a, s, r, rs, re, f, l, ac, g, data);
            level.addFreshEntity(out[0]);
        }).createShot(pos, angle, slope, rotate, rotationSpeed, rotationEnd, first, limit, accel, gravity, shot);
        return out[0];
    }

    /** createShot without rotation, returning the entity. */
    public static THShotEntity createShotEntity(LivingEntity user, Entity source, Vec3d pos, Vec3d angle, float slope,
                                                double first, double limit, double accel, Vec3d gravity,
                                                X1ShotData shot) {
        float yaw = getYawFromVector(angle.x(), angle.z());
        float pitch = getPitchFromVector(angle.x(), angle.y(), angle.z());
        return createShotEntity(user, source, pos, angle, slope, getVecFromAngle(yaw, pitch + 90F), 0F, 9999, first,
                limit, accel, gravity, shot);
    }

    public static void createWideShot(LivingEntity user, Entity source, Vec3d pos, Vec3d angle, float rotationSpeed,
                                      int rotationEnd, double first, double limit, double accel, Vec3d gravity,
                                      X1ShotData shot, int way, float wide, double distance, float baseAngle) {
        shots(user).createWideShot(pos, angle, rotationSpeed, rotationEnd, first, limit, accel, gravity, shot, way, wide,
                distance, baseAngle);
    }

    public static void createWideShot(LivingEntity user, Entity source, Vec3d pos, Vec3d angle, double first,
                                      double limit, double accel, Vec3d gravity, X1ShotData shot, int way, float wide,
                                      double distance) {
        shots(user).createWideShot(pos, angle, first, limit, accel, gravity, shot, way, wide, distance);
    }

    public static void createCircleShot(LivingEntity user, Entity source, Vec3d pos, Vec3d angle, float rotationSpeed,
                                        int rotationEnd, double first, double limit, double accel, Vec3d gravity,
                                        X1ShotData shot, int way, double distance, float baseAngle) {
        shots(user).createCircleShot(pos, angle, rotationSpeed, rotationEnd, first, limit, accel, gravity, shot, way,
                distance, baseAngle);
    }

    public static void createCircleShot(LivingEntity user, Entity source, Vec3d pos, Vec3d angle, double first,
                                        double limit, double accel, Vec3d gravity, X1ShotData shot, int way,
                                        double distance, float baseAngle) {
        shots(user).createCircleShot(pos, angle, first, limit, accel, gravity, shot, way, distance, baseAngle);
    }

    public static void createRingShot(LivingEntity user, Entity source, Vec3d pos, Vec3d angle, float rotationSpeed,
                                      int rotationEnd, double first, double limit, double accel, Vec3d gravity,
                                      X1ShotData shot, int way, double distance, float span, float baseAngle) {
        shots(user).createRingShot(pos, angle, rotationSpeed, rotationEnd, first, limit, accel, gravity, shot, way,
                distance, span, baseAngle);
    }

    /** createCircleShot(user, source, pos, angle, rotationSpeed, rotationEnd, ..., way, distance): baseAngle 0. */
    public static void createCircleShot(LivingEntity user, Entity source, Vec3d pos, Vec3d angle, float rotationSpeed,
                                        int rotationEnd, double first, double limit, double accel, Vec3d gravity,
                                        X1ShotData shot, int way, double distance) {
        createCircleShot(user, source, pos, angle, rotationSpeed, rotationEnd, first, limit, accel, gravity, shot, way,
                distance, 0F);
    }

    /** createRingShot(user, pos, angle, speed, shot, way, distance, span, base). */
    public static void createRingShot(LivingEntity user, Vec3d pos, Vec3d angle, double speed, X1ShotData shot,
                                      int way, double distance, float span, float baseAngle) {
        createRingShot(user, user, pos, angle, 0F, 9999, speed, speed, 0.0D, Vec3d.ZERO, shot, way, distance, span,
                baseAngle);
    }

    /** createRandomRingShot(user, pos, angle, first, limit, accel, shot, num, distance, span). */
    public static void createRandomRingShot(LivingEntity user, Vec3d pos, Vec3d angle, double first, double limit,
                                            double accel, X1ShotData shot, int num, double distance, float span) {
        createRandomRingShot(user, user, pos, angle, 0F, 9999, first, limit, accel, Vec3d.ZERO, shot, num, distance,
                span);
    }

    public static void createRandomRingShot(LivingEntity user, Entity source, Vec3d pos, Vec3d angle,
                                            float rotationSpeed, int rotationEnd, double first, double limit,
                                            double accel, Vec3d gravity, X1ShotData shot, int num, double distance,
                                            float span) {
        shots(user).createRandomRingShot(pos, angle, rotationSpeed, rotationEnd, first, limit, accel, gravity, shot,
                num, distance, span);
    }

    public static void createSphereShot(LivingEntity user, Entity source, Vec3d pos, Vec3d angle, float angleZ,
                                        Vec3d rotate, float rotationSpeed, int rotationEnd, double first, double limit,
                                        double accel, Vec3d gravity, X1ShotData shot, int way, double distance,
                                        float baseAngle) {
        shots(user).createSphereShot(pos, angle, angleZ, rotate, rotationSpeed, rotationEnd, first, limit, accel,
                gravity, shot, way, distance, baseAngle);
    }

    public static void createSphereShot(LivingEntity user, Entity source, Vec3d pos, Vec3d angle, float angleZ,
                                        double first, double limit, double accel, Vec3d gravity, X1ShotData shot,
                                        int way, double distance, float baseAngle) {
        createSphereShot(user, source, pos, angle, angleZ, rotate_Default(), 0F, 9999, first, limit, accel, gravity,
                shot, way, distance, baseAngle);
    }

    // ---- lasers ----

    private static X1LaserPatterns lasers(LivingEntity user, Entity source) {
        return X1LaserSpawner.patterns(level(user), user, source);
    }

    public static void createLaserA(LivingEntity user, Entity source, Vec3d pos, Vec3d angle, double first,
                                    double limit, double accel, Vec3d gravity, X1LaserData laser) {
        lasers(user, source).createLaserA(pos, angle, first, limit, accel, gravity, laser);
    }

    public static void createWideLaserA(LivingEntity user, Entity source, Vec3d pos, Vec3d angle, double first,
                                        double limit, double accel, Vec3d gravity, X1LaserData laser, int way,
                                        float wide, double distance) {
        lasers(user, source).createWideLaserA(pos, angle, first, limit, accel, gravity, laser, way, wide, distance);
    }

    public static void createCircleLaserA(LivingEntity user, Entity source, Vec3d pos, Vec3d angle, double first,
                                          double limit, double accel, Vec3d gravity, X1LaserData laser, int way,
                                          double distance) {
        lasers(user, source).createCircleLaserA(pos, angle, first, limit, accel, gravity, laser, way, distance);
    }

    public static void createRingLaserA(LivingEntity user, Entity source, Vec3d pos, Vec3d angle, double first,
                                        double limit, double accel, Vec3d gravity, X1LaserData laser, int way,
                                        double distance, float span, float baseAngle) {
        lasers(user, source).createRingLaserA(pos, angle, first, limit, accel, gravity, laser, way, distance, span,
                baseAngle);
    }

    public static THSetLaserEntity createLaserB(LivingEntity user, Entity setting, Vec3d pos, Vec3d angle,
                                                Vec3d rotate, float rotateYawSpeed, int rotationEnd, X1LaserData laser,
                                                Entity set, double setLength, double setYOffset) {
        return X1LaserSpawner.createLaserB(level(user), user, setting, pos, angle, rotate, rotateYawSpeed, rotationEnd,
                laser, set, setLength, setYOffset);
    }

    // ---- effects ----

    /** THShotLib.playShotSound: "random.bow", volume 2.0, pitch 1.2. */
    public static void playShotSound(Entity entity) {
        entity.level().playSound(null, entity.getX(), entity.getY(), entity.getZ(), SoundEvents.ARROW_SHOOT,
                entity.getSoundSource(), 2.0F, 1.2F);
    }

    /** THShotLib.danmakuRemove: target "ALL", "Enemy", "Player" or "Other". Returns the count. */
    public static int danmakuRemove(Entity center, double range, String target, boolean dropBonus) {
        int count = 0;
        List<THShotEntity> shots = center.level().getEntitiesOfClass(THShotEntity.class,
                center.getBoundingBox().inflate(range), e -> e != center);
        for (THShotEntity shot : shots) {
            Entity owner = shot.getOwner();
            boolean hit = switch (target) {
                case "ALL" -> true;
                case "Enemy" -> !(owner instanceof Player);
                case "Player" -> owner instanceof Player;
                case "Other" -> owner != center;
                default -> false;
            };
            if (!hit) continue;
            if (dropBonus) shot.shotFinishBonus();
            else shot.discard();
            count++;
        }
        return count;
    }

    /** new EntityShotMaterial(world, x, y, z) + spawn. */
    public static void spawnShotMaterial(Entity at, double x, double y, double z) {
        if (at.level().isClientSide) return;
        at.level().addFreshEntity(new ShotMaterialEntity(at.level(), x, y, z));
    }

    static boolean isLaser(Entity e) {
        return e instanceof THLaserEntity;
    }
}
