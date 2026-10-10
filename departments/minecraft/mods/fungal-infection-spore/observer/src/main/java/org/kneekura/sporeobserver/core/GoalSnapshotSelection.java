package org.kneekura.sporeobserver.core;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;

/**
 * Bounded, deterministic, owned ordering for passive Goal observations.
 * This does not choose or interrupt any Minecraft AI Goal.
 */
public final class GoalSnapshotSelection {
    private GoalSnapshotSelection() {}
    public static final int MAX_GOALS = 12;

    public static int rank(Map<String,Object> row) {
        String name = (String)row.get("goal_class");
        boolean watched = name.contains("InfectedWitch$") ||
                name.endsWith(".TransportInfected") ||
                name.endsWith(".SearchAreaGoal") ||
                name.endsWith(".FollowOthersGoal") ||
                name.endsWith(".LocalTargettingGoal") ||
                name.endsWith(".InfectedConsumeFromRemains") ||
                name.endsWith(".BufferAI") ||
                name.endsWith(".BuffAlliesGoal");
        if (watched) return 0;
        if (Boolean.TRUE.equals(row.get("running"))) return 1;
        return 2;
    }

    public static List<Map<String,Object>> select(List<Map<String,Object>> all) {
        ArrayList<Map<String,Object>> sorted = new ArrayList<>(all);
        sorted.sort(Comparator
                .comparingInt(GoalSnapshotSelection::rank)
                .thenComparingInt(row -> ((Number)row.get("priority")).intValue())
                .thenComparing(row -> (String)row.get("selector"))
                .thenComparing(row -> (String)row.get("goal_class"))
                .thenComparingInt(row -> ((Number)row.get("goal_instance_id")).intValue()));
        return new ArrayList<>(sorted.subList(0, Math.min(sorted.size(), MAX_GOALS)));
    }
}
