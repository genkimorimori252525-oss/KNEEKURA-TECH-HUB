package com.github.tartaricacid.touhoulittlemaid.sim.client;

import java.lang.reflect.Array;
import java.lang.reflect.Field;
import java.lang.reflect.Modifier;
import java.util.ArrayDeque;
import java.util.Collection;
import java.util.Deque;
import java.util.IdentityHashMap;
import java.util.Map;

/**
 * Shared field-only walker for unknown YSM runtime object graphs.
 *
 * <p>Unknown YSM methods are never invoked. The only reflective read is {@link Field#get}
 * through {@link SimBonePalette#read}. JDK Map/Collection iteration and Array access are
 * allowed container operations.
 *
 * <p>Traversal budgets are centralized here so every probe has identical completeness
 * semantics.
 */
final class SimYsmObjectWalker {
    static final int MAX_DEPTH = 6;
    static final int MAX_VISITED = 40000;
    static final int MAX_CONTAINER_ELEMENTS = 64;

    private SimYsmObjectWalker() {}

    record Node(Object value, String path, int depth, String ownerClass) {}

    interface Visitor {
        default void onArray(Node node, Object array, int length) {}
        default void onMap(Node node, Map<?, ?> map) {}
        default void onMapEntry(Node node, int index, Object key, Object value) {}
        default void onCollection(Node node, Collection<?> collection) {}
        default void onCollectionElement(Node node, int index, Object value) {}
        default void onField(Node node, Field field, Object value) {}
    }

    record Report(
            int visited,
            int depthReached,
            int truncatedContainers,
            boolean depthBudgetExhausted,
            boolean visitBudgetExhausted
    ) {
        boolean complete() {
            return truncatedContainers == 0 && !depthBudgetExhausted && !visitBudgetExhausted;
        }
    }

    private static final class State {
        final Map<Object, Boolean> seen = new IdentityHashMap<>();
        final Deque<Node> queue = new ArrayDeque<>();
        int visited;
        int depthReached;
        int truncatedContainers;
        boolean depthBudgetExhausted;
    }

    static Report walk(Object root, Visitor visitor) {
        State s = new State();
        Visitor v = visitor == null ? new Visitor() {} : visitor;
        if (root == null) {
            return new Report(0, 0, 0, false, false);
        }

        s.seen.put(root, Boolean.TRUE);
        s.queue.add(new Node(root, "root", 0, root.getClass().getName()));

        while (!s.queue.isEmpty() && s.visited < MAX_VISITED) {
            Node n = s.queue.poll();
            s.visited++;
            s.depthReached = Math.max(s.depthReached, n.depth());

            Object o = n.value();
            Class<?> cls = o.getClass();

            if (cls.isArray()) {
                processArray(n, v, s);
                continue;
            }
            if (o instanceof Map<?, ?> map) {
                processMap(n, map, v, s);
                continue;
            }
            if (o instanceof Collection<?> collection) {
                processCollection(n, collection, v, s);
                continue;
            }
            if (isPrimitiveLike(o)) {
                continue;
            }

            for (Field f : SimBonePalette.declaredFields(cls)) {
                if (Modifier.isStatic(f.getModifiers())) {
                    continue;
                }
                Object value = SimBonePalette.read(f, o);
                v.onField(n, f, value);
                if (value == null || isPrimitiveLike(value)) {
                    continue;
                }
                enqueue(value, n.path() + "." + f.getName(), n.depth() + 1, cls.getName(), s);
            }
        }

        return new Report(
                s.visited,
                s.depthReached,
                s.truncatedContainers,
                s.depthBudgetExhausted,
                !s.queue.isEmpty());
    }

    private static void processArray(Node n, Visitor v, State s) {
        Object array = n.value();
        int length = Array.getLength(array);
        v.onArray(n, array, length);

        Class<?> component = array.getClass().getComponentType();
        if (component.isPrimitive() || length == 0) {
            return;
        }
        if (n.depth() >= MAX_DEPTH) {
            s.depthBudgetExhausted = true;
            return;
        }

        int limit = containerLimit(length, s);
        for (int i = 0; i < limit; i++) {
            Object child = Array.get(array, i);
            if (child == null || isPrimitiveLike(child)) {
                continue;
            }
            enqueue(child, n.path() + "[" + i + "]", n.depth() + 1,
                    array.getClass().getName(), s);
        }
    }

    private static void processMap(Node n, Map<?, ?> map, Visitor v, State s) {
        v.onMap(n, map);
        if (map.isEmpty()) {
            return;
        }
        if (n.depth() >= MAX_DEPTH) {
            s.depthBudgetExhausted = true;
            return;
        }

        int limit = containerLimit(map.size(), s);
        int i = 0;
        for (Map.Entry<?, ?> entry : map.entrySet()) {
            if (i >= limit) {
                break;
            }
            Object key = entry.getKey();
            Object value = entry.getValue();
            v.onMapEntry(n, i, key, value);
            if (key != null && !isPrimitiveLike(key)) {
                enqueue(key, n.path() + ".key[" + i + "]", n.depth() + 1,
                        map.getClass().getName(), s);
            }
            if (value != null && !isPrimitiveLike(value)) {
                enqueue(value, n.path() + ".value[" + i + "]", n.depth() + 1,
                        map.getClass().getName(), s);
            }
            i++;
        }
    }

    private static void processCollection(Node n, Collection<?> collection, Visitor v, State s) {
        v.onCollection(n, collection);
        if (collection.isEmpty()) {
            return;
        }
        if (n.depth() >= MAX_DEPTH) {
            s.depthBudgetExhausted = true;
            return;
        }

        int limit = containerLimit(collection.size(), s);
        int i = 0;
        for (Object child : collection) {
            if (i >= limit) {
                break;
            }
            v.onCollectionElement(n, i, child);
            if (child != null && !isPrimitiveLike(child)) {
                enqueue(child, n.path() + "[" + i + "]", n.depth() + 1,
                        collection.getClass().getName(), s);
            }
            i++;
        }
    }

    private static int containerLimit(int size, State s) {
        if (size > MAX_CONTAINER_ELEMENTS) {
            s.truncatedContainers++;
            return MAX_CONTAINER_ELEMENTS;
        }
        return size;
    }

    private static void enqueue(Object value, String path, int depth, String ownerClass, State s) {
        if (value == null || isPrimitiveLike(value)) {
            return;
        }
        if (depth > MAX_DEPTH) {
            s.depthBudgetExhausted = true;
            return;
        }
        if (s.seen.put(value, Boolean.TRUE) == null) {
            s.queue.add(new Node(value, path, depth, ownerClass));
        }
    }

    static boolean isPrimitiveLike(Object value) {
        return value instanceof String || value instanceof Number || value instanceof Boolean
                || value instanceof Character || value.getClass().isEnum() || value instanceof Class<?>;
    }
}
