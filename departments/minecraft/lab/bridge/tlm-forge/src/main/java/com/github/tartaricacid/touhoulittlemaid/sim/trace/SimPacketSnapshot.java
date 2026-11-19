package com.github.tartaricacid.touhoulittlemaid.sim.trace;

import java.lang.reflect.Field;
import java.lang.reflect.Modifier;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;

/**
 * Safe, shallow packet snapshot for runtime network evidence.
 *
 * <p>Only public instance scalar fields are observed. No methods are called, private fields are not
 * opened, and arrays/collections/unknown object graphs are not traversed. This is intentionally much
 * narrower than a general serializer: the probe must not turn observation into behavior.
 */
public final class SimPacketSnapshot {
    public static final int MAX_FIELDS = 24;
    public static final int MAX_STRING_CHARS = 2048;

    private SimPacketSnapshot() {}

    public static Map<String, Object> capture(Object packet) {
        Map<String, Object> out = new LinkedHashMap<>();
        if (packet == null) {
            return out;
        }

        Field[] fields = packet.getClass().getFields();
        Arrays.sort(fields, java.util.Comparator.comparing(Field::getName));

        int accepted = 0;
        for (Field f : fields) {
            if (accepted >= MAX_FIELDS) {
                break;
            }
            int mods = f.getModifiers();
            if (!Modifier.isPublic(mods) || Modifier.isStatic(mods)) {
                continue;
            }
            try {
                Object value = f.get(packet);
                Object safe = safeScalar(value);
                if (safe == null) {
                    continue;
                }
                out.put(f.getName(), safe);
                accepted++;
            } catch (Throwable ignored) {
                // Observation must be fail-open. Skip one field, never fail the packet.
            }
        }
        return out;
    }

    /**
     * Sanitize an explicitly supplied semantic payload with the same scalar-only boundary.
     * Keys are sorted for stable JSON and unknown values are dropped.
     */
    public static Map<String, Object> sanitize(Map<String, ?> values) {
        Map<String, Object> out = new LinkedHashMap<>();
        if (values == null || values.isEmpty()) {
            return out;
        }
        values.entrySet().stream()
                .filter(e -> e.getKey() != null)
                .sorted(Map.Entry.comparingByKey())
                .limit(MAX_FIELDS)
                .forEach(e -> {
                    Object safe = safeScalar(e.getValue());
                    if (safe != null) {
                        out.put(e.getKey(), safe);
                    }
                });
        return out;
    }

    private static Object safeScalar(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof String s) {
            return s.length() <= MAX_STRING_CHARS ? s : s.substring(0, MAX_STRING_CHARS);
        }
        if (value instanceof Character c) {
            return String.valueOf(c);
        }
        if (value instanceof Boolean
                || value instanceof Byte
                || value instanceof Short
                || value instanceof Integer
                || value instanceof Long
                || value instanceof Float
                || value instanceof Double) {
            return value;
        }
        if (value instanceof Enum<?> e) {
            return e.name();
        }
        if (value instanceof UUID uuid) {
            return uuid.toString();
        }
        return null;
    }
}
