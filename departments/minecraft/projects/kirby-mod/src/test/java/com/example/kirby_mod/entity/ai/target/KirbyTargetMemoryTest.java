package com.example.kirby_mod.entity.ai.target;

import java.util.EnumMap;
import java.util.List;
import java.util.Map;

public final class KirbyTargetMemoryTest {

    public static void main(String[] args) {
        selectsDeterministically();
        expiresAtTtlBoundary();
        excludesAllyFromPrey();
        retainsAllyThreatAndReportsWarning();
    }

    private static void selectsDeterministically() {
        KirbyTargetMemory memory = new KirbyTargetMemory();
        memory.observeScan(10, List.of(
                observation(KirbyTargetKind.THREAT, "b", 8.0D, 4.0D, 10, 15),
                observation(KirbyTargetKind.THREAT, "a", 8.0D, 4.0D, 10, 15),
                observation(KirbyTargetKind.THREAT, "high", 9.0D, 20.0D, 10, 15)),
                counts(KirbyTargetKind.THREAT, 3));
        assertEquals("high", memory.get(KirbyTargetKind.THREAT).orElseThrow().targetKey(),
                "higher score");

        memory.observeScan(15, List.of(
                observation(KirbyTargetKind.THREAT, "b", 8.0D, 4.0D, 15, 15),
                observation(KirbyTargetKind.THREAT, "a", 8.0D, 4.0D, 15, 15)),
                counts(KirbyTargetKind.THREAT, 2));
        assertEquals("a", memory.get(KirbyTargetKind.THREAT).orElseThrow().targetKey(),
                "stable target key tie-break");
    }

    private static void expiresAtTtlBoundary() {
        KirbyTargetMemory memory = new KirbyTargetMemory();
        memory.observeScan(10, List.of(
                observation(KirbyTargetKind.INTEREST, "player", 1.0D, 2.0D, 10, 15)),
                counts(KirbyTargetKind.INTEREST, 1));
        memory.observeScan(25, List.of(), Map.of());
        assertTrue(memory.get(KirbyTargetKind.INTEREST).isPresent(), "present at TTL boundary");
        memory.observeScan(26, List.of(), Map.of());
        assertTrue(memory.get(KirbyTargetKind.INTEREST).isEmpty(), "expired after TTL boundary");
    }

    private static void excludesAllyFromPrey() {
        KirbyTargetMemory memory = new KirbyTargetMemory();
        memory.observeScan(0, List.of(
                observation(KirbyTargetKind.PREY, "wolf", 9.0D, 3.0D, 0, 15)),
                counts(KirbyTargetKind.PREY, 1));
        memory.observeScan(5, List.of(
                observation(KirbyTargetKind.ALLY, "wolf", 2.0D, 3.0D, 5, 15)),
                counts(KirbyTargetKind.ALLY, 1));
        assertTrue(memory.get(KirbyTargetKind.ALLY).isPresent(), "ally retained");
        assertTrue(memory.get(KirbyTargetKind.PREY).isEmpty(), "remembered prey removed after becoming ally");
    }

    private static void retainsAllyThreatAndReportsWarning() {
        KirbyTargetMemory memory = new KirbyTargetMemory();
        memory.observeScan(5, List.of(
                observation(KirbyTargetKind.ALLY, "wolf", 2.0D, 3.0D, 5, 15),
                observation(KirbyTargetKind.THREAT, "wolf", 20.0D, 3.0D, 5, 60)),
                Map.of(KirbyTargetKind.ALLY, 1, KirbyTargetKind.THREAT, 1));
        assertTrue(memory.get(KirbyTargetKind.THREAT).isPresent(), "threat retained");
        assertEquals(1, memory.getWarnings().size(), "ally-threat warning count");
    }

    private static KirbyTargetObservation observation(
            KirbyTargetKind kind,
            String key,
            double score,
            double distance,
            int seenTick,
            int ttlTicks) {
        return new KirbyTargetObservation(kind, key, "test:entity", 0.0D, 0.0D, 0.0D,
                distance, KirbyTargetVisibility.CLEAR, score, seenTick, ttlTicks, "test");
    }

    private static Map<KirbyTargetKind, Integer> counts(KirbyTargetKind kind, int count) {
        EnumMap<KirbyTargetKind, Integer> counts = new EnumMap<>(KirbyTargetKind.class);
        counts.put(kind, count);
        return counts;
    }

    private static void assertEquals(Object expected, Object actual, String label) {
        if (expected == null ? actual != null : !expected.equals(actual)) {
            throw new AssertionError(label + ": expected <" + expected + "> but was <" + actual + ">");
        }
    }

    private static void assertTrue(boolean value, String label) {
        if (!value) throw new AssertionError(label);
    }

    private KirbyTargetMemoryTest() {}
}
