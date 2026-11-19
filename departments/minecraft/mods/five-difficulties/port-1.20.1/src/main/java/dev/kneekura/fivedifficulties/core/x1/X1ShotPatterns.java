package dev.kneekura.fivedifficulties.core.x1;

import dev.kneekura.fivedifficulties.core.math.Vec3d;

import java.util.Random;

import static dev.kneekura.fivedifficulties.core.x1.X1ShotTables.RAINBOW;
import static dev.kneekura.fivedifficulties.core.x1.X1ShotTables.RAINBOW_PATTERN;
import static dev.kneekura.fivedifficulties.core.x1.X1ShotTables.RANDOM;
import static dev.kneekura.fivedifficulties.core.x1.X1ShotTables.SPHERE_WAYS;

/**
 * Port of the THShotLib shot-emission helpers (createShot / createWideShot / createCircleShot /
 * createRingShot / createRandomRingShot / createSphereShot). Geometry, argument order and the
 * RANDOM / RAINBOW colour handling are literal, including that the sphere helper does not restore
 * a RANDOM colour. Spawning is delegated to {@link Sink}.
 */
public final class X1ShotPatterns {
    /** Receives one fully-resolved EntityTHShot constructor call. */
    public interface Sink {
        void spawn(Vec3d pos, Vec3d angle, float slope, Vec3d rotate, float rotationSpeed, int rotationEnd,
                   double firstSpeed, double limitSpeed, double acceleration, Vec3d gravity, X1ShotData shot);
    }

    private final Random random;
    private final Sink sink;

    public X1ShotPatterns(Random random, Sink sink) {
        this.random = random;
        this.sink = sink;
    }

    public static Vec3d gravity(double y) {
        return new Vec3d(0.0D, y, 0.0D);
    }

    /** THShotLib.getVecFromAngle. */
    public static Vec3d vecFromAngle(float yaw, float pitch, double force) {
        double yawRad = (double) yaw / 180.0D * Math.PI;
        double pitchRad = (double) pitch / 180.0D * Math.PI;
        return new Vec3d(
                -Math.sin(yawRad) * Math.cos(pitchRad) * force,
                -Math.sin(pitchRad) * force,
                Math.cos(yawRad) * Math.cos(pitchRad) * force);
    }

    private static Vec3d rot(Vec3d axis, Vec3d vector, float angle) {
        return X1WideShotGeometry.rotateAroundAxisRaw(axis, vector, angle);
    }

    /** Full createShot: resolves RAINBOW / RANDOM for this one shot, then restores it. */
    public void createShot(Vec3d pos, Vec3d angle, float slope, Vec3d rotate, float rotationSpeed, int rotationEnd,
                           double firstSpeed, double limitSpeed, double acceleration, Vec3d gravity, X1ShotData shot) {
        boolean wasRandom = false;
        boolean wasRainbow = false;
        if (shot.color == RAINBOW) {
            shot.color = random.nextInt(7);
            wasRainbow = true;
        } else if (shot.color == RANDOM) {
            shot.color = random.nextInt(8);
            wasRandom = true;
        }
        sink.spawn(pos, angle, slope, rotate, rotationSpeed, rotationEnd, firstSpeed, limitSpeed, acceleration,
                gravity, shot.copy());
        if (wasRandom) shot.color = RANDOM;
        else if (wasRainbow) shot.color = RAINBOW;
    }

    /** createShot without rotation: the rotate axis is 90 degrees "above" the aim. */
    public void createShot(Vec3d pos, Vec3d angle, float slope, double firstSpeed, double limitSpeed,
                           double acceleration, Vec3d gravity, X1ShotData shot) {
        float yaw = X1ShotMotion.yawFromVector(angle.x(), angle.z());
        float pitch = X1ShotMotion.pitchFromVector(angle.x(), angle.y(), angle.z());
        Vec3d rotate = vecFromAngle(yaw, pitch + 90F, 1.0D);
        createShot(pos, angle, slope, rotate, 0F, 9999, firstSpeed, limitSpeed, acceleration, gravity, shot);
    }

    public void createWideShot(Vec3d pos, Vec3d angle, float rotationSpeed, int rotationEnd,
                               double firstSpeed, double limitSpeed, double acceleration, Vec3d gravity,
                               X1ShotData shot, int way, float wideAngle, double distance, float baseAngle) {
        float yaw = X1ShotMotion.yawFromVector(angle.x(), angle.z());
        float pitch = X1ShotMotion.pitchFromVector(angle.x(), angle.y(), angle.z());
        Vec3d rotateVec = vecFromAngle(-yaw, -pitch + 90F, 1.0F);
        float angle2 = -wideAngle / 2F;
        float span = wideAngle / (way - 1);
        angle2 += baseAngle;

        int color = random.nextInt(7);
        boolean wasRandom = shot.color == RANDOM;
        boolean wasRainbow = !wasRandom && shot.color == RAINBOW;
        if (wasRandom) shot.color = random.nextInt(8);

        for (int i = 0; i < way; i++) {
            if (wasRainbow) {
                shot.color = RAINBOW_PATTERN[color % 7];
                color++;
            }
            Vec3d angleVec = rot(rotateVec, angle, angle2);
            createShot(pos.add(angleVec.scale(distance)), angleVec,
                    pitch * (float) Math.sin(angle2 / 180F * 3.141593F), rotateVec, rotationSpeed, rotationEnd,
                    firstSpeed, limitSpeed, acceleration, gravity, shot);
            angle2 += span;
        }
        if (wasRandom) shot.color = RANDOM;
        else if (wasRainbow) shot.color = RAINBOW;
    }

    /** createWideShot(user, source, pos, angle, first, limit, accel, gravity, shot, way, wide, distance). */
    public void createWideShot(Vec3d pos, Vec3d angle, double firstSpeed, double limitSpeed, double acceleration,
                               Vec3d gravity, X1ShotData shot, int way, float wideAngle, double distance) {
        createWideShot(pos, angle, 0F, 9999, firstSpeed, limitSpeed, acceleration, gravity, shot, way, wideAngle,
                distance, 0F);
    }

    public void createCircleShot(Vec3d pos, Vec3d angle, float rotationSpeed, int rotationEnd,
                                 double firstSpeed, double limitSpeed, double acceleration, Vec3d gravity,
                                 X1ShotData shot, int way, double distance, float baseAngle) {
        if (way % 2 == 0) baseAngle += 360F / (way * 2F);
        createWideShot(pos, angle, rotationSpeed, rotationEnd, firstSpeed, limitSpeed, acceleration, gravity, shot,
                way, 360F - (360F / way), distance, baseAngle);
    }

    public void createCircleShot(Vec3d pos, Vec3d angle, double firstSpeed, double limitSpeed, double acceleration,
                                 Vec3d gravity, X1ShotData shot, int way, double distance, float baseAngle) {
        createCircleShot(pos, angle, 0F, 9999, firstSpeed, limitSpeed, acceleration, gravity, shot, way, distance,
                baseAngle);
    }

    public void createRingShot(Vec3d pos, Vec3d angle, float rotationSpeed, int rotationEnd,
                               double firstSpeed, double limitSpeed, double acceleration, Vec3d gravity,
                               X1ShotData shot, int way, double distance, float ringSpan, float ringBaseAngle) {
        ringSpan /= 2F;
        float yaw = X1ShotMotion.yawFromVector(-angle.x(), angle.z());
        float pitch = X1ShotMotion.pitchFromVector(-angle.x(), -angle.y(), angle.z());
        Vec3d baseVec = vecFromAngle(yaw, pitch + ringSpan, 1.0D);
        Vec3d baseOverVec = vecFromAngle(yaw, pitch + ringSpan + 90F, 1.0D);
        Vec3d overVec = vecFromAngle(yaw, pitch + 90F, 1.0D);
        float angle2 = ringBaseAngle;
        float span = 360F / way;

        int color = random.nextInt(7);
        boolean wasRandom = shot.color == RANDOM;
        boolean wasRainbow = !wasRandom && shot.color == RAINBOW;
        if (wasRandom) shot.color = random.nextInt(8);

        for (int i = 0; i < way; i++) {
            if (wasRainbow) {
                shot.color = RAINBOW_PATTERN[color % 7];
                color++;
            }
            Vec3d movingVec = rot(angle, baseVec, angle2);
            Vec3d extendVec = rot(angle, overVec, angle2);
            Vec3d overVec2 = rot(angle, baseOverVec, angle2);
            createShot(pos.add(extendVec.scale(distance)), movingVec, angle2, overVec2, rotationSpeed, rotationEnd,
                    firstSpeed, limitSpeed, acceleration, gravity, shot);
            angle2 += span;
        }
        if (wasRandom) shot.color = RANDOM;
        else if (wasRainbow) shot.color = RAINBOW;
    }

    public void createRandomRingShot(Vec3d pos, Vec3d angle, float rotationSpeed, int rotationEnd,
                                     double firstSpeed, double limitSpeed, double acceleration, Vec3d gravity,
                                     X1ShotData shot, int num, double distance, float ringSpan) {
        float ringMaxSpan = ringSpan / 2F;
        float yaw = X1ShotMotion.yawFromVector(-angle.x(), angle.z());
        float pitch = X1ShotMotion.pitchFromVector(angle.x(), angle.y(), angle.z());
        Vec3d overVec = vecFromAngle(-yaw, pitch + 90F, 1.0D);
        Vec3d mirroredAxis = new Vec3d(-angle.x(), -angle.y(), angle.z());

        int color = random.nextInt(7);
        boolean wasRandom = shot.color == RANDOM;
        boolean wasRainbow = !wasRandom && shot.color == RAINBOW;
        if (wasRandom) shot.color = random.nextInt(8);

        for (int i = 0; i < num; i++) {
            if (wasRainbow) {
                shot.color = RAINBOW_PATTERN[color % 7];
                color++;
            }
            float angle2 = random.nextFloat() * 360F;
            Vec3d baseVec = vecFromAngle(-yaw, pitch + random.nextFloat() * ringMaxSpan, 1.0D);
            Vec3d movingVec = rot(mirroredAxis, baseVec, angle2);
            Vec3d extendVec = rot(mirroredAxis, overVec, angle2);
            Vec3d spawn = new Vec3d(pos.x() - extendVec.x() * distance, pos.y() - extendVec.y() * distance,
                    pos.z() + extendVec.z() * distance);
            createShot(spawn, new Vec3d(-movingVec.x(), -movingVec.y(), movingVec.z()), angle2, angle,
                    rotationSpeed, rotationEnd, firstSpeed, limitSpeed, acceleration, gravity, shot);
        }
        if (wasRandom) shot.color = RANDOM;
        else if (wasRainbow) shot.color = RAINBOW;
    }

    public void createSphereShot(Vec3d pos, Vec3d angle, float angleZ, Vec3d rotate, float rotationSpeed,
                                 int rotationEnd, double firstSpeed, double limitSpeed, double acceleration,
                                 Vec3d gravity, X1ShotData shot, int way, double distance, float baseAngle) {
        if (way >= SPHERE_WAYS.length) return;
        int[] rings = SPHERE_WAYS[way];
        Vec3d frontPos = pos.add(angle.scale(distance));
        Vec3d backPos = pos.subtract(angle.scale(distance));
        float angleBase = 0F;
        float angleSpan = rings.length >= 2 ? 360F / (float) (rings.length - 1) : 0F;
        boolean frontDone = false;
        float slope = 0F;
        // X1 resolves RANDOM once here and never restores it.
        if (shot.color == RANDOM) shot.color = random.nextInt(8);

        for (int ring : rings) {
            if (ring == 1) {
                if (!frontDone) {
                    createShot(frontPos, angle, angleZ, rotate, rotationSpeed, rotationEnd, firstSpeed, limitSpeed,
                            acceleration, gravity, shot);
                    frontDone = true;
                } else {
                    createShot(backPos, angle.scale(-1.0D), angleZ, rotate, rotationSpeed, rotationEnd, firstSpeed,
                            limitSpeed, acceleration, gravity, shot);
                }
            } else {
                createRingShot(pos, angle, rotationSpeed, rotationEnd, firstSpeed, limitSpeed, acceleration, gravity,
                        shot, ring, distance, angleBase, baseAngle + slope);
                slope += 180F / rings.length;
            }
            angleBase += angleSpan;
        }
    }
}
