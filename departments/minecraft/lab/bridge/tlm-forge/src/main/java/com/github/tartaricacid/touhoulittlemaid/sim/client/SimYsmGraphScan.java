package com.github.tartaricacid.touhoulittlemaid.sim.client;

import java.lang.reflect.Array;
import java.lang.reflect.Field;
import java.lang.reflect.Modifier;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Map;

/**
 * Shape-oriented YSM runtime object graph probe.
 *
 * <p>Traversal itself is delegated to {@link SimYsmObjectWalker}, the shared field-only walker
 * used by scalar/state discovery as well. This class only classifies container shapes against
 * cube/bone counts; it does not assign runtime meaning.
 *
 * <p>A negative result is only conclusive when {@link Report#complete()} is true.
 */
public final class SimYsmGraphScan {

    private SimYsmGraphScan() {}

    static final int MAX_DEPTH = SimYsmObjectWalker.MAX_DEPTH;
    static final int MAX_VISITED = SimYsmObjectWalker.MAX_VISITED;
    static final int MAX_CONTAINER_ELEMENTS = SimYsmObjectWalker.MAX_CONTAINER_ELEMENTS;

    public record ElementInfo(String className, List<String> fieldNames) {}

    public record SizeClassification(
            boolean candidate,
            boolean cubeMultiple,
            int cubeMultipleValue,
            boolean boneMultiple,
            int boneMultipleValue,
            int remainderVsCube,
            int remainderVsBone
    ) {
        public boolean exactMultiple() {
            return cubeMultiple || boneMultiple;
        }
    }

    public static SizeClassification classifySize(int length, int cubeCount, int boneCount) {
        if (length <= 0) {
            return new SizeClassification(false, false, 0, false, 0, 0, 0);
        }
        boolean cubeOk = cubeCount > 0;
        boolean boneOk = boneCount > 0;
        boolean cubeMul = cubeOk && length % cubeCount == 0;
        boolean boneMul = boneOk && length % boneCount == 0;
        int floor;
        if (cubeOk && boneOk) {
            floor = Math.min(cubeCount, boneCount);
        } else if (cubeOk) {
            floor = cubeCount;
        } else if (boneOk) {
            floor = boneCount;
        } else {
            floor = Integer.MAX_VALUE;
        }
        boolean candidate = length >= floor;
        int remCube = cubeOk ? length % cubeCount : length;
        int remBone = boneOk ? length % boneCount : length;
        return new SizeClassification(
                candidate,
                cubeMul, cubeMul ? length / cubeCount : 0,
                boneMul, boneMul ? length / boneCount : 0,
                remCube, remBone);
    }

    public record Candidate(
            String path,
            String ownerClass,
            String componentType,
            int length,
            SizeClassification size,
            ElementInfo elementInfo,
            float[] rawFloats
    ) {}

    public record Report(
            List<Candidate> exactMultiples,
            List<Candidate> largeNonMultiples,
            int visited,
            int depthReached,
            int cubeCount,
            int boneCount,
            boolean negative,
            int truncatedContainers,
            boolean depthBudgetExhausted,
            boolean visitBudgetExhausted
    ) {
        public boolean complete() {
            return truncatedContainers == 0 && !depthBudgetExhausted && !visitBudgetExhausted;
        }

        public boolean conclusiveNegative() {
            return negative && complete();
        }
    }

    public static Report scan(Object root, int cubeCount, int boneCount) {
        List<Candidate> exact = new ArrayList<>();
        List<Candidate> large = new ArrayList<>();

        SimYsmObjectWalker.Report walk = SimYsmObjectWalker.walk(root, new SimYsmObjectWalker.Visitor() {
            @Override
            public void onArray(SimYsmObjectWalker.Node node, Object array, int length) {
                recordArray(array, node.ownerClass(), node.path(), cubeCount, boneCount, exact, large);
            }

            @Override
            public void onMap(SimYsmObjectWalker.Node node, Map<?, ?> map) {
                recordMap(map, node.ownerClass(), node.path(), cubeCount, boneCount, exact, large);
            }

            @Override
            public void onCollection(SimYsmObjectWalker.Node node, Collection<?> collection) {
                recordCollection(
                        collection, node.ownerClass(), node.path(), cubeCount, boneCount, exact, large);
            }
        });

        boolean negative = exact.isEmpty() && large.isEmpty();
        return new Report(
                exact,
                large,
                walk.visited(),
                walk.depthReached(),
                cubeCount,
                boneCount,
                negative,
                walk.truncatedContainers(),
                walk.depthBudgetExhausted(),
                walk.visitBudgetExhausted());
    }

    private static void recordArray(Object array, String ownerClass, String path, int cubeCount, int boneCount,
                                    List<Candidate> exact, List<Candidate> large) {
        int length = Array.getLength(array);
        SizeClassification sc = classifySize(length, cubeCount, boneCount);
        if (!sc.candidate()) {
            return;
        }
        Class<?> componentType = array.getClass().getComponentType();
        ElementInfo info = null;
        float[] rawFloats = null;
        if (componentType == float.class) {
            rawFloats = (float[]) array;
        } else if (!componentType.isPrimitive() && length > 0) {
            int limit = Math.min(length, MAX_CONTAINER_ELEMENTS);
            for (int i = 0; i < limit; i++) {
                Object element = Array.get(array, i);
                if (element != null) {
                    info = describeElement(element);
                    break;
                }
            }
        }
        file(new Candidate(path, ownerClass, componentType.getName(), length, sc, info, rawFloats), exact, large);
    }

    private static void recordMap(Map<?, ?> map, String ownerClass, String path, int cubeCount, int boneCount,
                                  List<Candidate> exact, List<Candidate> large) {
        int length = map.size();
        SizeClassification sc = classifySize(length, cubeCount, boneCount);
        if (!sc.candidate()) {
            return;
        }
        ElementInfo info = null;
        for (Object value : map.values()) {
            if (value != null) {
                info = describeElement(value);
                break;
            }
        }
        file(new Candidate(path, ownerClass, map.getClass().getName(), length, sc, info, null), exact, large);
    }

    private static void recordCollection(Collection<?> collection, String ownerClass, String path,
                                         int cubeCount, int boneCount,
                                         List<Candidate> exact, List<Candidate> large) {
        int length = collection.size();
        SizeClassification sc = classifySize(length, cubeCount, boneCount);
        if (!sc.candidate()) {
            return;
        }
        ElementInfo info = null;
        for (Object value : collection) {
            if (value != null) {
                info = describeElement(value);
                break;
            }
        }
        file(new Candidate(
                path, ownerClass, collection.getClass().getName(), length, sc, info, null), exact, large);
    }

    private static void file(Candidate candidate, List<Candidate> exact, List<Candidate> large) {
        if (candidate.size().exactMultiple()) {
            exact.add(candidate);
        } else {
            large.add(candidate);
        }
    }

    private static ElementInfo describeElement(Object value) {
        List<String> names = new ArrayList<>();
        for (Field f : SimBonePalette.declaredFields(value.getClass())) {
            if (Modifier.isStatic(f.getModifiers())) {
                continue;
            }
            names.add(f.getName() + ":" + f.getType().getSimpleName());
        }
        return new ElementInfo(value.getClass().getName(), names);
    }
}
