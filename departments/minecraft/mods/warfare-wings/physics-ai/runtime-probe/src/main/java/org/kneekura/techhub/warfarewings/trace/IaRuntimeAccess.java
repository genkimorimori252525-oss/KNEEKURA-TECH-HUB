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