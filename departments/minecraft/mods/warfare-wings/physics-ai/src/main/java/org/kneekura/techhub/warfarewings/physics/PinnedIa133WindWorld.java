package org.kneekura.techhub.warfarewings.physics;

import static org.kneekura.techhub.warfarewings.physics.Ia133Microkernel.*;

/**
 * Literal pinned IA 1.3.3 original JAR bytecode reconstruction of
 * AircraftEntity.getWindStrength()/getWindEffect() and Utils.cosNoise().
 *
 * SHA-512 pinned Immersive Aircraft:
 * 7b74442e161bb74538e0d8da34a81616daeea56a0da62db86113a78b3bf3c2b3a6b0e12f12454fd7c96092762f6b212ba57cb87eb1af2b242a4d5df4eca03055
 *
 * CRITICAL finding: getWindStrength includes the craft's current speed even
 * when ALL three weather wind config values equal zero. Previous laboratory
 * FlatWorld mistakenly omitted this deterministic aerodynamic perturbation.
 * Its periodic yaw/pitch accumulation compounds into open-loop trajectory
 * differences. Here weather scalars are explicit, not silently guessed.
 *
 * Does not simulate real Minecraft collisions, liquids, entity tick order,
 * installed upgrades or random/unobserved enemies. Source experiment ONLY.
 */
public record PinnedIa133WindWorld(
        double groundY, float clearConfig, float rainConfig, float thunderConfig,
        float raining, float thundering) implements World {

    public PinnedIa133WindWorld {
        double[] scalars = {groundY, clearConfig, rainConfig, thunderConfig, raining, thundering};
        for (double value : scalars)
            if (!Double.isFinite(value)) throw new IllegalArgumentException("Non-finite original IA environment");
        if (raining < 0 || raining > 1 || thundering < 0 || thundering > 1)
            throw new IllegalArgumentException("Rain/thunder strength outside Minecraft range");
    }

    public static PinnedIa133WindWorld calmAirCalibration() {
        return new PinnedIa133WindWorld(0,0,0,0,0,0);
    }

    @Override public double groundHeight(double x, double z) { return groundY; }

    /** IA 1.3.3 Utils.cosNoise(value,5): five cos harmonics, x*=1.3. */
    public static double cosNoise(double argument) {
        if (!Double.isFinite(argument)) throw new IllegalArgumentException("Invalid IA wind period");
        double total = 0;
        for (int i=0;i<5;i++) {
            total += Math.cos(argument);
            argument *= 1.3;
        }
        return total;
    }

    @Override public Wind windAfterFriction(Model model, State state, Vec3 physicalVelocity) {
        if (model == null || state == null || physicalVelocity == null ||
                !Double.isFinite(physicalVelocity.length()) || model.mass() <= 0)
            throw new IllegalArgumentException("Invalid original IA wind state");
        // Original AircraftEntity.getWindStrength():
        // (float)(windClearWeather + deltaMovement.length()
        //         + thunder*windThunderWeather + rain*windRainWeather)
        //     * (float)VehicleProperties.WIND;
        float amplitude = (float)((double)clearConfig + physicalVelocity.length()
                + (double)(thundering * thunderConfig)
                + (double)(raining * rainConfig)) * (float)model.wind();
        // Original getWindEffect uses entity.tickCount rather than level time
        // (AirplaneEntity entity has just incremented tickCount for this step).
        double tick = (double)(state.tick() + 1);
        float mass = (float)model.mass();
        float wx = (float)(cosNoise(tick / 20.0 / mass) * amplitude);
        float wz = (float)(cosNoise(tick / 21.0 / mass) * amplitude);
        // IA applies effect.x to pitch and effect.z to yaw, then weakly adds
        // x,z components to velocity with coefficient 0.005f.
        return new Wind(wx,wz);
    }
}
