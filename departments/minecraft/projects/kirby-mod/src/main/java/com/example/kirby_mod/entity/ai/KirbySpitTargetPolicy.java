package com.example.kirby_mod.entity.ai;

import java.util.List;

/** Selects a clear attackable threat and produces a horizontal spit direction. */
public final class KirbySpitTargetPolicy {

    private static final double MIN_DIRECTION_LENGTH = 1.0E-4D;

    private KirbySpitTargetPolicy() {}

    public static Selection select(List<Candidate> candidates) {
        Candidate best = null;
        for (Candidate candidate : candidates) {
            if (!candidate.clearLineOfSight() || !candidate.attackable()) continue;
            double horizontalLength = Math.sqrt(
                    candidate.offsetX() * candidate.offsetX()
                            + candidate.offsetZ() * candidate.offsetZ());
            if (!Double.isFinite(horizontalLength)
                    || horizontalLength < MIN_DIRECTION_LENGTH
                    || !Double.isFinite(candidate.distance())) continue;
            if (best == null || isBetter(candidate, best)) best = candidate;
        }
        if (best == null) return Selection.none("no_clear_attackable_threat");

        double horizontalLength = Math.sqrt(
                best.offsetX() * best.offsetX() + best.offsetZ() * best.offsetZ());
        String reason = best.rememberedThreat()
                ? "remembered_threat"
                : "nearest_clear_threat";
        return new Selection(best.targetKey(),
                best.offsetX() / horizontalLength,
                best.offsetZ() / horizontalLength,
                best.distance(), best.rememberedThreat(), reason);
    }

    private static boolean isBetter(Candidate candidate, Candidate current) {
        if (candidate.rememberedThreat() != current.rememberedThreat()) {
            return candidate.rememberedThreat();
        }
        int distance = Double.compare(candidate.distance(), current.distance());
        if (distance != 0) return distance < 0;
        return candidate.targetKey().compareTo(current.targetKey()) < 0;
    }

    public record Candidate(
            String targetKey,
            double offsetX,
            double offsetZ,
            double distance,
            boolean clearLineOfSight,
            boolean attackable,
            boolean rememberedThreat) {}

    public record Selection(
            String targetKey,
            double directionX,
            double directionZ,
            double distance,
            boolean rememberedThreat,
            String reason) {

        public static Selection none(String reason) {
            return new Selection("none", 0.0D, 0.0D,
                    Double.POSITIVE_INFINITY, false, reason);
        }

        public boolean found() {
            return !"none".equals(targetKey);
        }
    }
}
