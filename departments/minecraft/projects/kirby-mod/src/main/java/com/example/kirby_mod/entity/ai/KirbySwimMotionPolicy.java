package com.example.kirby_mod.entity.ai;

/** Pure swimming motion calculation kept separate from Minecraft entity state for testing. */
public final class KirbySwimMotionPolicy {

    private static final double MIN_INPUT = 1.0E-4D;
    private static final double SPEED_MULTIPLIER = 0.65D;
    private static final double ACCELERATION = 0.35D;
    private static final double ACTIVE_DRAG = 0.90D;
    private static final double IDLE_DRAG = 0.75D;

    private KirbySwimMotionPolicy() {}

    public static Decision decide(
            double lookX,
            double lookY,
            double lookZ,
            double currentX,
            double currentY,
            double currentZ,
            double inputStrength,
            double movementSpeed) {
        double clampedInput = Math.max(0.0D, Math.min(1.0D, inputStrength));
        double lookLength = Math.sqrt(lookX * lookX + lookY * lookY + lookZ * lookZ);
        if (clampedInput <= MIN_INPUT || lookLength <= MIN_INPUT) {
            return new Decision(false,
                    currentX * IDLE_DRAG,
                    currentY * IDLE_DRAG,
                    currentZ * IDLE_DRAG,
                    clampedInput);
        }

        double targetSpeed = Math.max(0.0D, movementSpeed) * SPEED_MULTIPLIER * clampedInput;
        double targetX = lookX / lookLength * targetSpeed;
        double targetY = lookY / lookLength * targetSpeed;
        double targetZ = lookZ / lookLength * targetSpeed;
        double nextX = lerp(currentX, targetX, ACCELERATION) * ACTIVE_DRAG;
        double nextY = lerp(currentY, targetY, ACCELERATION) * ACTIVE_DRAG;
        double nextZ = lerp(currentZ, targetZ, ACCELERATION) * ACTIVE_DRAG;
        return new Decision(true, nextX, nextY, nextZ, clampedInput);
    }

    private static double lerp(double from, double to, double amount) {
        return from + (to - from) * amount;
    }

    public record Decision(
            boolean active,
            double velocityX,
            double velocityY,
            double velocityZ,
            double inputStrength) {}
}
