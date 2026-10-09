package com.example.kirby_mod.entity.ai.target;

import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/** Deterministic, Minecraft-object-free memory of the best observed target per kind. */
public final class KirbyTargetMemory {

    private final EnumMap<KirbyTargetKind, KirbyTargetObservation> targets =
            new EnumMap<>(KirbyTargetKind.class);
    private final EnumMap<KirbyTargetKind, Integer> candidateCounts =
            new EnumMap<>(KirbyTargetKind.class);
    private final List<String> warnings = new ArrayList<>();
    private int lastScanTick = -1;

    public void observeScan(
            int scanTick,
            List<KirbyTargetObservation> observations,
            Map<KirbyTargetKind, Integer> counts) {
        if (scanTick < 0) throw new IllegalArgumentException("scanTick must not be negative");
        EnumMap<KirbyTargetKind, KirbyTargetObservation> best =
                new EnumMap<>(KirbyTargetKind.class);
        for (KirbyTargetObservation observation : observations) {
            if (observation.seenTick() > scanTick) {
                throw new IllegalArgumentException("observation cannot be from the future");
            }
            KirbyTargetObservation current = best.get(observation.kind());
            if (current == null || isBetter(observation, current)) {
                best.put(observation.kind(), observation);
            }
        }

        KirbyTargetObservation ally = best.get(KirbyTargetKind.ALLY);
        KirbyTargetObservation prey = best.get(KirbyTargetKind.PREY);
        if (ally != null && prey != null && ally.targetKey().equals(prey.targetKey())) {
            best.remove(KirbyTargetKind.PREY);
        }

        for (KirbyTargetKind kind : KirbyTargetKind.values()) {
            KirbyTargetObservation fresh = best.get(kind);
            if (fresh != null) {
                targets.put(kind, fresh);
            } else {
                KirbyTargetObservation remembered = targets.get(kind);
                if (remembered != null && scanTick - remembered.seenTick() > remembered.ttlTicks()) {
                    targets.remove(kind);
                }
            }
            candidateCounts.put(kind, Math.max(0, counts.getOrDefault(kind, 0)));
        }
        ally = targets.get(KirbyTargetKind.ALLY);
        prey = targets.get(KirbyTargetKind.PREY);
        if (ally != null && prey != null && ally.targetKey().equals(prey.targetKey())) {
            targets.remove(KirbyTargetKind.PREY);
        }
        lastScanTick = scanTick;
        rebuildWarnings();
    }

    public Optional<KirbyTargetObservation> get(KirbyTargetKind kind) {
        return Optional.ofNullable(targets.get(kind));
    }

    public Map<KirbyTargetKind, KirbyTargetObservation> snapshot() {
        return Collections.unmodifiableMap(new EnumMap<>(targets));
    }

    public int getCandidateCount(KirbyTargetKind kind) {
        return candidateCounts.getOrDefault(kind, 0);
    }

    public int getLastScanTick() {
        return lastScanTick;
    }

    public List<String> getWarnings() {
        return List.copyOf(warnings);
    }

    private static boolean isBetter(KirbyTargetObservation candidate, KirbyTargetObservation current) {
        int score = Double.compare(candidate.score(), current.score());
        if (score != 0) return score > 0;
        int distance = Double.compare(candidate.distance(), current.distance());
        if (distance != 0) return distance < 0;
        return candidate.targetKey().compareTo(current.targetKey()) < 0;
    }

    private void rebuildWarnings() {
        warnings.clear();
        KirbyTargetObservation ally = targets.get(KirbyTargetKind.ALLY);
        KirbyTargetObservation threat = targets.get(KirbyTargetKind.THREAT);
        if (ally != null && threat != null && ally.targetKey().equals(threat.targetKey())) {
            warnings.add("ally-threat target=" + ally.targetKey());
        }
    }
}
