package org.kneekura.techhub.warfarewings.trace;

/**
 * Exact IA 1.3.3 source non-player input correction, including the preceding
 * airborne rotation friction. Isolated from Forge so all phase assumptions
 * stay executable without private binary dependencies.
 */
final class IaNonPlayerInputBridgeMath {
    static final float INPUT_WEIGHT = 0.1f; // IA VehicleEntity.getInputInterpolationSteps()==10
    static final float FRICTION = 0.015f; // supplied source Atlas effective friction
    static final float ROTATION_DECAY = 0.97f; // pinned IA VehicleStat.ROTATION_DECAY
    static final float AIRBORNE_HOST_RETENTION =
            (1f - FRICTION) * ROTATION_DECAY * (1f - INPUT_WEIGHT);

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
        // Source: InventoryVehicleEntity.applyFriction()
        //   rf = (1-FRICTION)*ROTATION_DECAY;
        //   pressingInterpolatedX/Z.decay(0,1-rf);
        // Then VehicleEntity.tick() update(0), and our END correction adds
        // +0.1*command. Thus actual source/real runtime coefficient is
        // 0.9*0.985*0.97=0.859905 rather than 0.9.
        float[] expectedAfter = {.1f, .1859905f, .159934161f,
                .037528185f, .032270674f, .027749714f};
        float[] consumedAtController = new float[controls.length];
        for (int tick = 0; tick < controls.length; tick++) {
            // VehicleEntity.updateController consumes previous END injection.
            consumedAtController[tick] = smoothAtStart;
            // VehicleEntity.tickPilot resets to zero, then tick ends with update(0).
            float afterHostUpdate = smoothAtStart * AIRBORNE_HOST_RETENTION;
            smoothAtStart = correctZeroedSmooth(afterHostUpdate, controls[tick]);
            if (Math.abs(smoothAtStart - expectedAfter[tick]) > 0.000002f)
                throw new AssertionError("IA 10-step smoothing diverged at tick " + tick);
        }
        if (consumedAtController[0] != 0 || consumedAtController[1] < .099f
                || Math.abs(consumedAtController[2] - .1859905f) > .000002f)
            throw new AssertionError("END injection violated one-physics-tick lag");
        if (correctZeroedSmooth(.45f, -1) >= .45f
                || correctZeroedSmooth(-.45f, 1) <= -.45f)
            throw new AssertionError("IA steering command polarity");
        System.out.println("IaNonPlayerInputBridgeMath passed: 6 x 20Hz ticks, "
                + "airborne retention=" + AIRBORNE_HOST_RETENTION
                + ", one-tick control lag; source-only arithmetic");
    }
}
