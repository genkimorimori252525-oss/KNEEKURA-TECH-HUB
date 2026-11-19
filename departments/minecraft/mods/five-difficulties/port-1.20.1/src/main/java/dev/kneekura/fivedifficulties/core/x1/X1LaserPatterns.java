package dev.kneekura.fivedifficulties.core.x1;

import dev.kneekura.fivedifficulties.core.math.Vec3d;

import java.util.Random;

import static dev.kneekura.fivedifficulties.core.x1.X1ShotPatterns.vecFromAngle;
import static dev.kneekura.fivedifficulties.core.x1.X1ShotTables.RAINBOW;
import static dev.kneekura.fivedifficulties.core.x1.X1ShotTables.RAINBOW_PATTERN;
import static dev.kneekura.fivedifficulties.core.x1.X1ShotTables.RANDOM;
import static dev.kneekura.fivedifficulties.core.x1.X1ShotTables.SPHERE_WAYS;

/**
 * Port of the THShotLib laser emitters (createLaserA, createWideLaserA, createCircleLaserA,
 * createRingLaserA, createRandomRingLaser, createSphereLaserA). They differ from the shot emitters
 * in ways kept literally:
 * <ul>
 *   <li>createLaserA resolves RANDOM / RAINBOW into the caller's LaserData and never restores it;</li>
 *   <li>a wide laser re-rolls RANDOM for every ray;</li>
 *   <li>createCircleLaserA emits way + 1 rays over 360 degrees (first and last coincide);</li>
 *   <li>createSphereLaserA spawns the backward laser at the <em>front</em> position.</li>
 * </ul>
 * Lasers always get rotate = (0, 1, 0), no yaw rotation, rotationEnd 9999 and slope 0.
 */
public final class X1LaserPatterns {
    public interface Sink {
        void spawn(Vec3d pos, Vec3d angle, double firstSpeed, double limitSpeed, double acceleration, Vec3d gravity,
                   X1LaserData laser);
    }

    private final Random random;
    private final Sink sink;

    public X1LaserPatterns(Random random, Sink sink) {
        this.random = random;
        this.sink = sink;
    }

    private static Vec3d rot(Vec3d axis, Vec3d v, float angle) {
        return X1WideShotGeometry.rotateAroundAxisRaw(axis, v, angle);
    }

    public void createLaserA(Vec3d pos, Vec3d angle, double firstSpeed, double limitSpeed, double acceleration,
                             Vec3d gravity, X1LaserData laser) {
        if (laser.color == RANDOM) laser.color = random.nextInt(8);
        else if (laser.color == RAINBOW) laser.color = random.nextInt(7);
        sink.spawn(pos, angle, firstSpeed, limitSpeed, acceleration, gravity, laser.copy());
    }

    public void createWideLaserA(Vec3d pos, Vec3d angle, double firstSpeed, double limitSpeed, double acceleration,
                                 Vec3d gravity, X1LaserData laser, int way, float wideAngle, double distance) {
        float yaw = X1ShotMotion.yawFromVector(angle.x(), angle.z());
        float pitch = X1ShotMotion.pitchFromVector(angle.x(), angle.y(), angle.z());
        Vec3d rotateVec = vecFromAngle(-yaw, -pitch + 90F, 1.0F);
        float angle2 = -wideAngle / 2F;
        float span = wideAngle / (way - 1);
        boolean wasRandom = laser.color == RANDOM;
        boolean wasRainbow = !wasRandom && laser.color == RAINBOW;
        int color = random.nextInt(7);
        for (int i = 0; i < way; i++) {
            if (wasRandom) {
                laser.color = random.nextInt(8);
            } else if (wasRainbow) {
                laser.color = RAINBOW_PATTERN[color % 7];
                color++;
            }
            Vec3d angleVec = rot(rotateVec, angle, angle2);
            createLaserA(pos.add(angleVec.scale(distance)), angleVec, firstSpeed, limitSpeed, acceleration, gravity, laser);
            angle2 += span;
        }
    }

    public void createCircleLaserA(Vec3d pos, Vec3d angle, double firstSpeed, double limitSpeed, double acceleration,
                                   Vec3d gravity, X1LaserData laser, int way, double distance) {
        createWideLaserA(pos, angle, firstSpeed, limitSpeed, acceleration, gravity, laser, way + 1, 360F, distance);
    }

    public void createRingLaserA(Vec3d pos, Vec3d angle, double firstSpeed, double limitSpeed, double acceleration,
                                 Vec3d gravity, X1LaserData laser, int way, double distance, float ringSpan,
                                 float ringBaseAngle) {
        ringSpan /= 2F;
        float yaw = X1ShotMotion.yawFromVector(-angle.x(), angle.z());
        float pitch = X1ShotMotion.pitchFromVector(angle.x(), angle.y(), angle.z());
        Vec3d baseVec = vecFromAngle(-yaw, pitch + ringSpan, 1.0D);
        Vec3d overVec = vecFromAngle(-yaw, pitch + 90F, 1.0D);
        Vec3d mirrored = new Vec3d(-angle.x(), -angle.y(), angle.z());
        float angle2 = ringBaseAngle;
        float span = 360F / way;
        int color = random.nextInt(7);
        boolean wasRandom = laser.color == RANDOM;
        boolean wasRainbow = !wasRandom && laser.color == RAINBOW;
        if (wasRandom) laser.color = random.nextInt(8);
        for (int i = 0; i < way; i++) {
            if (wasRainbow) {
                laser.color = RAINBOW_PATTERN[color % 7];
                color++;
            }
            Vec3d movingVec = rot(mirrored, baseVec, angle2);
            Vec3d extendVec = rot(mirrored, overVec, angle2);
            Vec3d spawn = new Vec3d(pos.x() - extendVec.x() * distance, pos.y() - extendVec.y() * distance,
                    pos.z() + extendVec.z() * distance);
            createLaserA(spawn, new Vec3d(-movingVec.x(), -movingVec.y(), movingVec.z()), firstSpeed, limitSpeed,
                    acceleration, gravity, laser);
            angle2 += span;
        }
        if (wasRandom) laser.color = RANDOM;
        else if (wasRainbow) laser.color = RAINBOW;
    }

    public void createRandomRingLaser(Vec3d pos, Vec3d angle, double firstSpeed, double limitSpeed,
                                      double acceleration, Vec3d gravity, X1LaserData laser, int num, double distance,
                                      float ringSpan) {
        float ringMaxSpan = ringSpan / 2F;
        float yaw = X1ShotMotion.yawFromVector(-angle.x(), angle.z());
        float pitch = X1ShotMotion.pitchFromVector(angle.x(), angle.y(), angle.z());
        Vec3d overVec = vecFromAngle(-yaw, pitch + 90F, 1.0D);
        Vec3d mirrored = new Vec3d(-angle.x(), -angle.y(), angle.z());
        for (int i = 0; i < num; i++) {
            float angle2 = random.nextFloat() * 360F;
            Vec3d baseVec = vecFromAngle(-yaw, pitch + random.nextFloat() * ringMaxSpan, 1.0D);
            Vec3d movingVec = rot(mirrored, baseVec, angle2);
            Vec3d extendVec = rot(mirrored, overVec, angle2);
            Vec3d spawn = new Vec3d(pos.x() - extendVec.x() * distance, pos.y() - extendVec.y() * distance,
                    pos.z() + extendVec.z() * distance);
            createLaserA(spawn, new Vec3d(-movingVec.x(), -movingVec.y(), movingVec.z()), firstSpeed, limitSpeed,
                    acceleration, gravity, laser);
        }
    }

    public void createSphereLaserA(Vec3d pos, Vec3d angle, double firstSpeed, double limitSpeed, double acceleration,
                                   Vec3d gravity, X1LaserData laser, int way, double distance, float baseAngle) {
        if (way >= SPHERE_WAYS.length) return;
        int[] rings = SPHERE_WAYS[way];
        Vec3d frontPos = pos.add(angle.scale(distance));
        float angleBase = 0F;
        float angleSpan = rings.length >= 2 ? 360F / (float) (rings.length - 1) : 0F;
        boolean frontDone = false;
        float slope = 0F;
        if (laser.color == RANDOM) laser.color = random.nextInt(8);
        for (int ring : rings) {
            if (ring == 1) {
                if (!frontDone) {
                    createLaserA(frontPos, angle, firstSpeed, limitSpeed, acceleration, gravity, laser);
                    frontDone = true;
                } else {
                    // X1 uses frontPos here too.
                    createLaserA(frontPos, angle.scale(-1.0D), firstSpeed, limitSpeed, acceleration, gravity, laser);
                }
            } else {
                createRingLaserA(pos, angle, firstSpeed, limitSpeed, acceleration, gravity, laser, ring, distance,
                        angleBase, baseAngle + slope);
                slope += 180F / rings.length;
            }
            angleBase += angleSpan;
        }
    }
}
