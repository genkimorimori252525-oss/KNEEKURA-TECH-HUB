package dev.kneekura.fivedifficulties.core.x1;

import dev.kneekura.fivedifficulties.core.math.Vec3d;

/**
 * World-independent port of the movement half of X1 {@code EntityTHShot.onUpdate}.
 *
 * Kept literal on purpose, including X1 quirks:
 * <ul>
 *   <li>speed is read through {@code MathHelper.sqrt_double}, i.e. rounded to float;</li>
 *   <li>acceleration is applied along the stored unit {@code angle}, not along the motion;</li>
 *   <li>the animation counter jumps to {@code lastTime} after the delay, so the end time
 *       effectively includes the delay;</li>
 *   <li>a tick whose {@code ticksExisted <= lastTime} (time stopped) does nothing.</li>
 * </ul>
 * Entity/block collision and the world are supplied by {@link Hooks}.
 */
public final class X1ShotMotion {
    public enum Step { FROZEN, DELAY, ACTIVE }

    public interface Hooks {
        /** Authoritative (server) side owns the synced animation counter. */
        boolean authoritative();

        int animationCount();

        void setAnimationCount(int value);

        /** X1 specialMotion: registry / switch on {@code shotSpecial}. */
        default void specialMotion(X1ShotMotion motion) {
            if (motion.special == X1ShotTables.FALL01) {
                motion.motion = new Vec3d(motion.motion.x(), motion.motion.y() - 0.02D, motion.motion.z());
            }
        }

        /** X1 hitCheck: may delete the shot or change {@link #motion}. */
        default void hitCheck(X1ShotMotion motion) {}
    }

    public Vec3d position;
    public Vec3d motion;
    /** X1 {@code angle}: unit travel direction, rotated by {@code setShotRotationYaw}. */
    public Vec3d angle;
    /** X1 {@code rotate}: axis used by the per-tick yaw rotation. */
    public Vec3d rotate;
    public double shotSpeed;
    public double limitSpeed;
    public double acceleration;
    public Vec3d gravity;
    public float rotationYawSpeed;
    public int rotationEnd;
    public int special;

    public int lastTime;
    public Vec3d lastMotion;
    /** X1 rotationYaw / rotationPitch (yaw = atan2(motionX, motionZ), not the Minecraft sign). */
    public float yaw;
    public float pitch;

    public X1ShotMotion(
            Vec3d position,
            Vec3d angle,
            Vec3d rotate,
            float rotationSpeed,
            int rotationEnd,
            double firstSpeed,
            double limitSpeed,
            double acceleration,
            Vec3d gravity,
            int special
    ) {
        this.position = position;
        this.angle = angle;
        this.rotate = rotate;
        this.rotationYawSpeed = rotationSpeed;
        this.rotationEnd = rotationEnd;
        this.shotSpeed = firstSpeed;
        this.limitSpeed = limitSpeed;
        this.acceleration = acceleration;
        this.gravity = gravity;
        this.special = special;
        this.motion = angle.scale(firstSpeed);
        this.lastMotion = this.motion;
        this.yaw = yawFromVector(angle.x(), angle.z());
        this.pitch = pitchFromVector(angle.x(), angle.y(), angle.z());
        this.lastTime = 0;
    }

    /** Initial synced animation counter for a shot with this delay ({@code setAnimationCount(-delay)}). */
    public static int initialAnimationCount(int delay) {
        return -delay;
    }

    /** X1 death check, run before the time-stop check: {@code getAnimationCount() > getDeadTime()}. */
    public static boolean isPastEnd(int animationCount, int endTime) {
        return animationCount > endTime;
    }

    /**
     * One X1 tick. {@code ticksExisted} must already include this tick (the world increments it
     * before {@code onUpdate}, as both 1.7.10 and 1.20.1 do).
     */
    public Step tick(int ticksExisted, Hooks hooks) {
        if (ticksExisted <= lastTime) return Step.FROZEN;

        motion = lastMotion;
        if (hooks.authoritative()) {
            int animation = hooks.animationCount();
            if (animation >= 0) {
                hooks.setAnimationCount(lastTime);
            } else {
                hooks.setAnimationCount(animation + 1);
                timeProcess(ticksExisted);
                return Step.DELAY;
            }
        }

        if (rotationYawSpeed != 0F) rotateYaw(rotationYawSpeed);
        updateAngle();
        accelerate();
        hooks.specialMotion(this);
        motion = motion.add(gravity);
        hooks.hitCheck(this);
        shotSpeed = speed();
        if (rotationEnd < lastTime) rotationYawSpeed = 0F;
        if (hooks.animationCount() >= 0) position = position.add(motion);
        timeProcess(ticksExisted);
        return Step.ACTIVE;
    }

    /** {@code MathHelper.sqrt_double} returns float in 1.7.10. */
    public double speed() {
        return (double) (float) Math.sqrt(motion.x() * motion.x() + motion.y() * motion.y() + motion.z() * motion.z());
    }

    /** setShotRotationYaw: rotate {@code angle} about {@code rotate}, then updateMotion. */
    public void rotateYaw(float degrees) {
        angle = X1WideShotGeometry.rotateAroundAxisRaw(rotate, angle, degrees);
        updateMotion();
    }

    /** updateMotion: keep the current speed, follow {@code angle}. */
    public void updateMotion() {
        double speed = speed();
        motion = angle.scale(speed);
        lastMotion = motion;
    }

    /** setSpeed. */
    public void setSpeed(double speed) {
        shotSpeed = speed;
        motion = angle.scale(speed);
        lastMotion = motion;
    }

    /** EntityTHLaser overrides updateAngle: yaw / pitch follow the stored angle, not the motion. */
    public boolean laserAngle;

    /** updateAngle (server branch). */
    public void updateAngle() {
        if (laserAngle) {
            float horizontal = (float) Math.sqrt(angle.x() * angle.x() + angle.z() * angle.z());
            yaw = (float) ((Math.atan2(angle.x(), angle.z()) * 180D) / 3.1415927410125732D);
            if (yaw >= 180F) yaw = -180F + (yaw - 180F);
            else if (yaw <= -180F) yaw = 180F + (yaw + 180F);
            pitch = (float) ((Math.atan2(angle.y(), horizontal) * 180D) / 3.1415927410125732D);
            return;
        }
        float horizontal = (float) Math.sqrt(motion.x() * motion.x() + motion.z() * motion.z());
        yaw = (float) ((Math.atan2(motion.x(), motion.z()) * 180D) / 3.1415927410125732D);
        pitch = (float) ((Math.atan2(motion.y(), horizontal) * 180D) / 3.1415927410125732D);
    }

    /** shotAcceleration. */
    public void accelerate() {
        if (acceleration > 0.0D && speed() < limitSpeed) {
            motion = motion.add(angle.scale(acceleration));
            if (acceleration > 0.0D && speed() > limitSpeed) {
                motion = angle.scale(limitSpeed);
            }
        } else if (acceleration < 0.0D && speed() > limitSpeed) {
            if (Math.abs(acceleration) > speed() - limitSpeed) {
                motion = angle.scale(limitSpeed);
            } else {
                motion = motion.add(angle.scale(acceleration));
            }
        }
    }

    /** timeProcess. */
    public void timeProcess(int ticksExisted) {
        if (ticksExisted > lastTime) {
            lastTime = ticksExisted;
            lastMotion = motion;
        }
    }

    /** THShotLib.getYawFromVector. */
    public static float yawFromVector(double x, double z) {
        return (float) ((Math.atan2(x, z) * 180D) / 3.1415927410125732D);
    }

    /** THShotLib.getPitchFromVector. */
    public static float pitchFromVector(double x, double y, double z) {
        double horizontal = (float) Math.sqrt(x * x + z * z);
        return (float) ((Math.atan2(y, horizontal) * 180D) / 3.1415927410125732D);
    }
}
