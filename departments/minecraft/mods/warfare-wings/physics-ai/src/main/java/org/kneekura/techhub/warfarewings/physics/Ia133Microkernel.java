package org.kneekura.techhub.warfarewings.physics;

/**
 * Pure-Java approximation of the Immersive Aircraft 1.3.3 fixed-wing tick path.
 *
 * Scope: source-faithful ordering for fast deterministic research.
 * Non-goals: exact Minecraft Entity.move voxel resolution, chunks, fluids, networking,
 * client-originated crash damage, exact IA wind noise, and projectile callbacks.
 */
public final class Ia133Microkernel {
    public static final double TICKS_PER_SECOND = 20.0;
    public static final double BASE_GRAVITY = -0.04;
    public static final double INPUT_SMOOTH_FACTOR = 0.1; // InterpolatedFloat(10)
    public static final double ENGINE_REACTION_TICKS = 20.0;
    public static final double BRAKE_FACTOR_133 = 0.95;

    private Ia133Microkernel() {}

    public record Vec3(double x, double y, double z) {
        public static final Vec3 ZERO = new Vec3(0, 0, 0);
        public Vec3 add(Vec3 o) { return new Vec3(x + o.x, y + o.y, z + o.z); }
        public Vec3 add(double dx, double dy, double dz) { return new Vec3(x + dx, y + dy, z + dz); }
        public Vec3 scale(double s) { return new Vec3(x * s, y * s, z * s); }
        public double dot(Vec3 o) { return x * o.x + y * o.y + z * o.z; }
        public double lengthSquared() { return dot(this); }
        public double length() { return Math.sqrt(lengthSquared()); }
        public double horizontalLength() { return Math.hypot(x, z); }
        public Vec3 normalize() { double l = length(); return l < 1e-12 ? ZERO : scale(1.0 / l); }
        public Vec3 lerp(Vec3 o, double t) {
            return new Vec3(x + (o.x - x) * t, y + (o.y - y) * t, z + (o.z - z) * t);
        }
    }

    public record Control(double x, double y, double z, double engineTarget) {
        public Control {
            x = clamp(x, -1, 1); y = clamp(y, -1, 1); z = clamp(z, -1, 1);
            engineTarget = clamp(engineTarget, 0, 1);
        }
        public static Control neutral(double engineTarget) { return new Control(0, 0, 0, engineTarget); }
    }

    /** Effective IA 1.3.3 values plus raw driftDrag only for provenance. */
    public record Model(
            String id, String role, String doctrine,
            double engineSpeed, double yawSpeed, double pitchSpeed, double pushSpeed,
            double acceleration, double durability, double fuel,
            double friction, double glideFactor, double lift, double rollFactor,
            double groundPitch, double stabilizer, double wind, double mass,
            double groundFriction, double waterFriction, double rotationDecay,
            double horizontalDecay, double verticalDecay,
            double rawDriftDrag) {
        public Model {
            if (id == null || id.isBlank()) throw new IllegalArgumentException("id");
            if (acceleration <= 0) throw new IllegalArgumentException("acceleration");
            if (friction < 0 || friction >= 1) throw new IllegalArgumentException("friction");
        }
    }

    public record State(
            long tick, Vec3 position, Vec3 velocity,
            double yawDeg, double pitchDeg, double rollDeg,
            double rawX, double rawY, double rawZ,
            double smoothX, double smoothY, double smoothZ,
            double engineTarget, double enginePowerSmooth, double fuelUtilization,
            double previousY, boolean onGround, boolean touchingWater) {
        public State {
            if (position == null || velocity == null) throw new IllegalArgumentException("vectors");
            if (fuelUtilization < 0 || fuelUtilization > 1) throw new IllegalArgumentException("fuelUtilization");
        }
        public static State airborne(Vec3 position, Vec3 velocity) {
            return new State(0, position, velocity, 0, 0, 0,
                    0, 0, 0, 0, 0, 0,
                    0, 0, 1, 0, false, false);
        }
    }

    public record Wind(double pitchDeltaDeg, double yawDeltaDeg) {
        public static final Wind ZERO = new Wind(0, 0);
    }

    public interface World {
        double groundHeight(double x, double z);
        default Wind wind(Model model, State state) { return Wind.ZERO; }
    }

    public record FlatWorld(double y) implements World {
        @Override public double groundHeight(double x, double z) { return y; }
    }

    public static State tick(Model model, State state, Control control, World world) {
        if (model == null || state == null || control == null || world == null)
            throw new IllegalArgumentException("null tick input");

        double roll = state.onGround ? state.rollDeg * 0.9
                : -state.smoothX * model.rollFactor * (1.0 - (state.touchingWater ? 1.0 : 0.0));

        double rawX = control.x, rawY = control.y, rawZ = control.z;
        double engineTarget = control.engineTarget;
        Vec3 position = state.position;
        Vec3 velocity = sanitize(state.velocity);
        double yaw = state.yawDeg;
        double pitch = state.pitchDeg;

        Vec3 forwardBefore = forward(yaw, pitch);
        double diff = state.previousY - position.y;
        if (state.previousY != 0 && model.glideFactor > 0 && diff != 0) {
            velocity = velocity.add(forwardBefore.scale(
                    diff * model.glideFactor * (1.0 - Math.abs(forwardBefore.y))));
        }
        double nextPreviousY = position.y;

        velocity = convertPower(velocity, forwardBefore, model.lift, model.friction);
        double gravity = airplaneGravity(velocity, forwardBefore);
        double decay;
        if (state.touchingWater) {
            gravity *= 0.25;
            decay = model.waterFriction;
        } else if (state.onGround) {
            decay = groundDecay(model, gravity);
        } else {
            decay = 1.0 - model.friction;
        }
        velocity = new Vec3(
                velocity.x * decay * model.horizontalDecay,
                velocity.y * decay * model.verticalDecay + gravity,
                velocity.z * decay * model.horizontalDecay);

        double rotationRetention = decay * model.rotationDecay;
        double smoothXForController = state.smoothX * rotationRetention;
        double smoothZForController = state.smoothZ * rotationRetention;

        if (state.onGround) {
            pitch = (pitch + model.groundPitch) * 0.9 - model.groundPitch;
        } else if (!state.touchingWater) {
            Wind wind = world.wind(model, state);
            pitch += wind.pitchDeltaDeg;
            yaw += wind.yawDeltaDeg;
            velocity = velocity.add(wind.pitchDeltaDeg * 0.005, 0, wind.yawDeltaDeg * 0.005);
        }

        yaw -= model.yawSpeed * smoothXForController;
        if (!state.onGround) pitch += model.pitchSpeed * smoothZForController;
        pitch *= 1.0 - model.stabilizer;

        if (rawY != 0) {
            engineTarget = clamp(engineTarget + 0.1 * rawY, 0, 1);
            if (rawY < 0) velocity = velocity.scale(BRAKE_FACTOR_133);
        }

        double enginePower = state.enginePowerSmooth * Math.sqrt(state.fuelUtilization);
        Vec3 forwardAfter = forward(yaw, pitch);
        double thrust = enginePower * enginePower * model.engineSpeed;
        if (state.onGround && engineTarget < 1.0) {
            thrust = model.pushSpeed / (1.0 + velocity.length() * 5.0)
                    * smoothZForController * (1.0 - enginePower);
        }
        velocity = velocity.add(forwardAfter.scale(thrust));

        Vec3 moved = position.add(velocity);
        double ground = world.groundHeight(moved.x, moved.z);
        boolean onGround = moved.y <= ground;
        if (onGround) {
            moved = new Vec3(moved.x, ground, moved.z);
            if (velocity.y < 0) velocity = new Vec3(velocity.x, 0, velocity.z);
        }

        double smoothX = smoothXForController * 0.9 + rawX * INPUT_SMOOTH_FACTOR;
        double smoothY = state.smoothY * 0.9 + rawY * INPUT_SMOOTH_FACTOR;
        double smoothZ = smoothZForController * 0.9 + rawZ * INPUT_SMOOTH_FACTOR;

        double engineFactor = model.acceleration / ENGINE_REACTION_TICKS;
        double enginePowerSmooth = state.enginePowerSmooth * (1.0 - engineFactor) + engineTarget * engineFactor;

        return new State(state.tick + 1, moved, sanitize(velocity), yaw, pitch, roll,
                rawX, rawY, rawZ, smoothX, smoothY, smoothZ,
                engineTarget, enginePowerSmooth, state.fuelUtilization,
                nextPreviousY, onGround, state.touchingWater);
    }

    public static Vec3 forward(double yawDeg, double pitchDeg) {
        double yaw = Math.toRadians(yawDeg), pitch = Math.toRadians(pitchDeg);
        double cp = Math.cos(pitch);
        return new Vec3(-Math.sin(yaw) * cp, -Math.sin(pitch), Math.cos(yaw) * cp).normalize();
    }

    static Vec3 convertPower(Vec3 velocity, Vec3 forward, double lift, double friction) {
        double speed = velocity.length();
        Vec3 direction = velocity.normalize();
        double alignment = Math.abs(forward.dot(direction));
        double magnitude = speed * (alignment * friction + (1.0 - friction));
        return direction.lerp(forward, lift).scale(magnitude);
    }

    static double airplaneGravity(Vec3 velocity, Vec3 forward) {
        double speed = velocity.length() * (1.0 - Math.abs(forward.y));
        return Math.max(0.0, 1.0 - speed * 1.5) * BASE_GRAVITY;
    }

    static double groundDecay(Model model, double gravity) {
        double gravityRatio = Math.min(1.0, Math.max(0.0, gravity / BASE_GRAVITY));
        double upgrade = Math.min(1.0, model.acceleration * 0.5);
        return (model.groundFriction * gravityRatio + (1.0 - gravityRatio)) * (1.0 - upgrade) + upgrade;
    }

    private static Vec3 sanitize(Vec3 v) {
        return Double.isFinite(v.x) && Double.isFinite(v.y) && Double.isFinite(v.z) ? v : Vec3.ZERO;
    }

    private static double clamp(double value, double min, double max) {
        return Math.max(min, Math.min(max, value));
    }
}
