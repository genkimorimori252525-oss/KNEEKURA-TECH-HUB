package org.kneekura.techhub.warfarewings.trace;

/**
 * The exact 1.3.3 non-player input reset compensation. Isolated from Forge so
 * that timing/polarity assumptions remain executable without private mod jars.
 */
final class IaNonPlayerInputBridgeMath {
    static final float INPUT_WEIGHT = 0.1f; // IA VehicleEntity.getInputInterpolationSteps()==10

    private IaNonPlayerInputBridgeMath() {}

    static float correctZeroedSmooth(float afterHostUpdate, float command) {
        if (!Float.isFinite(afterHostUpdate) || !Float.isFinite(command)
                || Math.abs(command) > 1.0f)
            throw new IllegalArgumentException("invalid command or IA smooth value");
        return Math.max(-1.0f, Math.min(1.0f,
                afterHostUpdate + INPUT_WEIGHT * command));
    }

    /**
     * The observable turn on tick N consumes the command submitted at END of
     * tick N-1, because IA calls updateController before its own smooth update.
     */
    public static void main(String[] args) {
        float smoothAtStart = 0;
        float[] controls = {1, 1, 0, -1, 0, 0};
        float[] expectedAfter = {.1f, .19f, .171f, .0539f, .04851f, .043659f};
        float[] consumedAtController = new float[controls.length];
        for (int tick = 0; tick < controls.length; tick++) {
            // VehicleEntity.updateController consumes previous END injection.
            consumedAtController[tick] = smoothAtStart;
            // VehicleEntity.tickPilot resets to zero, then tick ends with update(0).
            float afterHostUpdate = smoothAtStart * .9f;
            smoothAtStart = correctZeroedSmooth(afterHostUpdate, controls[tick]);
            if (Math.abs(smoothAtStart - expectedAfter[tick]) > 0.000002f)
                throw new AssertionError("IA 10-step smoothing diverged at tick " + tick);
        }
        if (consumedAtController[0] != 0 || consumedAtController[1] < .099f
                || consumedAtController[2] < .189f)
            throw new AssertionError("END injection violated one-physics-tick lag");
        if (correctZeroedSmooth(.45f, -1) >= .45f
                || correctZeroedSmooth(-.45f, 1) <= -.45f)
            throw new AssertionError("IA steering command polarity");
        System.out.println("IaNonPlayerInputBridgeMath passed: 6 x 20Hz ticks, "
                + "smoothing=10, one-tick control lag; Forge binary NOT_RUN");
    }
}
