package com.github.tartaricacid.touhoulittlemaid.sim.client;

import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Field-only scalar snapshot probe for locating YSM Molang runtime state.
 *
 * <p>This class does not assign Molang meaning. It records safe scalar observations from the
 * runtime object graph so controlled before/after mutations can be compared later.
 */
public final class SimYsmScalarProbe {
    static final int MAX_TEXT_CHARS = 256;

    private SimYsmScalarProbe() {}

    public record Scalar(
            String path,
            String ownerClass,
            String fieldName,
            String containerKey,
            boolean containerKeyTruncated,
            String type,
            String value,
            boolean valueTruncated
    ) {
        public boolean hasExactContainerKey() {
            return containerKey != null && !containerKeyTruncated;
        }

        public boolean comparable() {
            return !containerKeyTruncated && !valueTruncated;
        }

        public String stableIdentity() {
            if (containerKey != null) {
                return "map|" + path + "|" + containerKey;
            }
            return "field|" + path;
        }
    }

    public record Snapshot(
            List<Scalar> scalars,
            int visited,
            int depthReached,
            int truncatedContainers,
            boolean depthBudgetExhausted,
            boolean visitBudgetExhausted
    ) {
        public boolean complete() {
            return truncatedContainers == 0 && !depthBudgetExhausted && !visitBudgetExhausted;
        }

        public boolean negative() {
            return scalars.isEmpty();
        }

        public boolean conclusiveNegative() {
            return negative() && complete();
        }
    }

    public record Change(Scalar before, Scalar after) {}

    public static Snapshot snapshot(Object root) {
        List<Scalar> scalars = new ArrayList<>();

        SimYsmObjectWalker.Report walk = SimYsmObjectWalker.walk(root, new SimYsmObjectWalker.Visitor() {
            @Override
            public void onField(SimYsmObjectWalker.Node node, Field field, Object value) {
                Encoded encoded = encodeKnownScalar(value);
                if (encoded == null) {
                    return;
                }
                scalars.add(new Scalar(
                        node.path() + "." + field.getName(),
                        node.value().getClass().getName(),
                        field.getName(),
                        null,
                        false,
                        encoded.type(),
                        encoded.value(),
                        encoded.truncated()));
            }

            @Override
            public void onMapEntry(SimYsmObjectWalker.Node node, int index, Object key, Object value) {
                if (!(key instanceof String stringKey)) {
                    return;
                }
                Encoded encoded = encodeKnownScalar(value);
                if (encoded == null) {
                    return;
                }
                Clipped keyClip = clip(stringKey);
                scalars.add(new Scalar(
                        node.path(),
                        node.value().getClass().getName(),
                        null,
                        keyClip.value(),
                        keyClip.truncated(),
                        encoded.type(),
                        encoded.value(),
                        encoded.truncated()));
            }
        });

        return new Snapshot(
                List.copyOf(scalars),
                walk.visited(),
                walk.depthReached(),
                walk.truncatedContainers(),
                walk.depthBudgetExhausted(),
                walk.visitBudgetExhausted());
    }

    /**
     * Return only values present at the same stable location in both snapshots.
     * Truncated keys/values are excluded to avoid turning an ambiguous prefix into evidence.
     */
    public static List<Change> diff(Snapshot before, Snapshot after) {
        if (before == null || after == null) {
            return List.of();
        }
        Map<String, Scalar> left = comparableByIdentity(before.scalars());
        Map<String, Scalar> right = comparableByIdentity(after.scalars());
        List<Change> changes = new ArrayList<>();
        for (Map.Entry<String, Scalar> entry : left.entrySet()) {
            Scalar a = entry.getValue();
            Scalar b = right.get(entry.getKey());
            if (b == null) {
                continue;
            }
            if (!a.type().equals(b.type()) || !a.value().equals(b.value())) {
                changes.add(new Change(a, b));
            }
        }
        return List.copyOf(changes);
    }

    private static Map<String, Scalar> comparableByIdentity(List<Scalar> scalars) {
        Map<String, Scalar> out = new LinkedHashMap<>();
        for (Scalar scalar : scalars) {
            if (scalar != null && scalar.comparable()) {
                out.putIfAbsent(scalar.stableIdentity(), scalar);
            }
        }
        return out;
    }

    private record Encoded(String type, String value, boolean truncated) {}
    private record Clipped(String value, boolean truncated) {}

    private static Encoded encodeKnownScalar(Object value) {
        if (value instanceof String s) {
            Clipped c = clip(s);
            return new Encoded(String.class.getName(), c.value(), c.truncated());
        }
        if (value instanceof Boolean b) {
            return new Encoded(Boolean.class.getName(), Boolean.toString(b), false);
        }
        if (value instanceof Character c) {
            return new Encoded(Character.class.getName(), Character.toString(c), false);
        }
        if (value instanceof Byte b) {
            return new Encoded(Byte.class.getName(), Byte.toString(b), false);
        }
        if (value instanceof Short s) {
            return new Encoded(Short.class.getName(), Short.toString(s), false);
        }
        if (value instanceof Integer i) {
            return new Encoded(Integer.class.getName(), Integer.toString(i), false);
        }
        if (value instanceof Long l) {
            return new Encoded(Long.class.getName(), Long.toString(l), false);
        }
        if (value instanceof Float f) {
            return new Encoded(Float.class.getName(), Float.toString(f), false);
        }
        if (value instanceof Double d) {
            return new Encoded(Double.class.getName(), Double.toString(d), false);
        }
        return null;
    }

    private static Clipped clip(String value) {
        if (value.length() <= MAX_TEXT_CHARS) {
            return new Clipped(value, false);
        }
        return new Clipped(value.substring(0, MAX_TEXT_CHARS), true);
    }
}
