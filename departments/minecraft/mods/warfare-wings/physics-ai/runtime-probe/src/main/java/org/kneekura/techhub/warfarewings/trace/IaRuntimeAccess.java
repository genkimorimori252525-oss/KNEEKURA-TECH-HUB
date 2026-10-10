package org.kneekura.techhub.warfarewings.trace;

import net.minecraft.world.entity.Entity;

import java.lang.reflect.Field;
import java.lang.reflect.Method;

final class IaRuntimeAccess {
    private IaRuntimeAccess() {}

    static void configureCalibrationRuntime() {
        try {
            Class<?> configClass = Class.forName("immersive_aircraft.config.Config");
            Object config = configClass.getMethod("getInstance").invoke(null);
            setField(configClass, config, "windClearWeather", 0.0f);
            setField(configClass, config, "windRainWeather", 0.0f);
            setField(configClass, config, "windThunderWeather", 0.0f);
            setField(configClass, config, "fuelConsumption", 0.0f);
            setField(configClass, config, "collisionDamage", false);
        } catch (ReflectiveOperationException e) {
            throw new IllegalStateException("Could not configure Immersive Aircraft calibration runtime", e);
        }
    }

    static void chill(Entity aircraft) { invoke(aircraft, "chill"); }
    static void setEngineTarget(Entity aircraft, float target) { invoke(aircraft, "setEngineTarget", new Class[]{float.class}, target); }
    static double engineTarget(Entity aircraft) { return number(invoke(aircraft, "getEngineTarget")); }
    static double enginePower(Entity aircraft) { return number(invoke(aircraft, "getEnginePower")); }
    static double fuelUtilization(Entity aircraft) { return number(invoke(aircraft, "getFuelUtilization")); }
    static double roll(Entity aircraft) { return number(invoke(aircraft, "getRoll")); }
    static double health(Entity aircraft) { return number(invoke(aircraft, "getHealth")); }

    /**
     * IA 1.3.3 source commit 550b38d: VehicleEntity.tickPilot() calls
     * setInputs(0,0,0) on a server-side ArmorStand pilot *before* the
     * controller, and at the end of tick() calls interpolated.update(0).
     * We therefore inject at ServerTickEvent.END after the entity's tick.
     *
     * At that point smooth = previousSmooth*0.9. Adding input*0.1 restores
     * the same one-update-per-tick response as InterpolatedFloat.update(input).
     * Its public decay(value,1) method sets the corrected state; next tick's
     * AirplaneEntity.updateController() consumes it. This is a lab-only
     * non-player control adapter, not a Forge-supported flight API.
     */
    static void applyTacticalControls(Entity aircraft, float x, float z, float engine) {
        if (!Float.isFinite(x) || !Float.isFinite(z) || !Float.isFinite(engine)
                || Math.abs(x) > 1 || Math.abs(z) > 1 || engine < 0 || engine > 1)
            throw new IllegalArgumentException("non-finite/out-of-range IA controls");
        correctZeroedInterpolation(aircraft, "pressingInterpolatedX", x);
        correctZeroedInterpolation(aircraft, "pressingInterpolatedZ", z);
        setEngineTarget(aircraft, engine);
    }

    static void validateTacticalControlSurface(Entity aircraft) {
        try {
            findMethod(aircraft.getClass(), "setInputs", float.class, float.class, float.class);
            for (String name : new String[]{"pressingInterpolatedX", "pressingInterpolatedZ"}) {
                Object interpolation = findField(aircraft.getClass(), name).get(aircraft);
                findMethod(interpolation.getClass(), "getSmooth");
                findMethod(interpolation.getClass(), "decay", float.class, float.class);
                // Exact pinned 1.3.3 source returns ten interpolation steps.
                float stepFraction = ((Number) findField(interpolation.getClass(), "steps")
                        .get(interpolation)).floatValue();
                if (Math.abs(stepFraction - 0.1f) > 1e-6f)
                    throw new IllegalStateException("Unknown IA input smoothing coefficient: " + stepFraction);
            }
            findMethod(aircraft.getClass(), "setEngineTarget", float.class);
        } catch (ReflectiveOperationException e) {
            throw new IllegalStateException("Pinned IA aircraft control surface unavailable", e);
        }
    }

    private static void correctZeroedInterpolation(Entity aircraft, String field, float command) {
        try {
            Object interpolation = findField(aircraft.getClass(), field).get(aircraft);
            float alreadyZeroed = ((Number) findMethod(interpolation.getClass(), "getSmooth")
                    .invoke(interpolation)).floatValue();
            float corrected = IaNonPlayerInputBridgeMath.correctZeroedSmooth(alreadyZeroed, command);
            findMethod(interpolation.getClass(), "decay", float.class, float.class)
                    .invoke(interpolation, corrected, 1.0f);
        } catch (ReflectiveOperationException e) {
            throw new IllegalStateException("Could not apply IA control " + field, e);
        }
    }

    static double smooth(Entity aircraft, String fieldName) {
        try {
            Field field = findField(aircraft.getClass(), fieldName);
            Object interpolated = field.get(aircraft);
            Method method = findMethod(interpolated.getClass(), "getSmooth");
            return number(method.invoke(interpolated));
        } catch (ReflectiveOperationException e) {
            throw new IllegalStateException("Could not read " + fieldName, e);
        }
    }

    private static void setField(Class<?> type, Object target, String name, Object value) throws ReflectiveOperationException {
        Field field = findField(type, name);
        field.set(target, value);
    }

    private static Object invoke(Object target, String name) {
        return invoke(target, name, new Class[0]);
    }

    private static Object invoke(Object target, String name, Class<?>[] parameterTypes, Object... args) {
        try {
            Method method = findMethod(target.getClass(), name, parameterTypes);
            return method.invoke(target, args);
        } catch (ReflectiveOperationException e) {
            throw new IllegalStateException("Could not invoke " + name, e);
        }
    }

    private static Method findMethod(Class<?> type, String name, Class<?>... parameterTypes) throws NoSuchMethodException {
        for (Class<?> current = type; current != null; current = current.getSuperclass()) {
            try {
                Method method = current.getDeclaredMethod(name, parameterTypes);
                method.setAccessible(true);
                return method;
            } catch (NoSuchMethodException ignored) {
            }
        }
        throw new NoSuchMethodException(name);
    }

    private static Field findField(Class<?> type, String name) throws NoSuchFieldException {
        for (Class<?> current = type; current != null; current = current.getSuperclass()) {
            try {
                Field field = current.getDeclaredField(name);
                field.setAccessible(true);
                return field;
            } catch (NoSuchFieldException ignored) {
            }
        }
        throw new NoSuchFieldException(name);
    }

    private static double number(Object value) {
        if (!(value instanceof Number n)) throw new IllegalStateException("Expected number, got " + value);
        return n.doubleValue();
    }
}
