package org.kneekura.sporeobserver.core;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

/**
 * Independent Java 17 snapshot diff. Never invokes Goal.start/stop/tick.
 *
 * It tracks the same observer-assigned goal_instance_id across two consecutive
 * observed snapshots of one Mob. Missing goals are NOT counted as stops,
 * especially when the snapshot was truncated. Changes seen between two end
 * ticks are NOT exact GoalSelector callback timestamps.
 */
public final class GoalRunningStateDiff {
    private static final int MAX_ENTITIES = 64;
    private static final int MAX_CHANGES_SHOWN = 12;
    private final Map<String, Map<Integer, Boolean>> previous = new HashMap<>();

    public Map<String, Object> observe(Map<String, Object> snapshot) {
        Objects.requireNonNull(snapshot);
        Object rawId = snapshot.get("entity_uuid");
        TraceSink.require(rawId instanceof String && !((String) rawId).isBlank(), "missing entity uuid");
        String entityId = (String) rawId;
        Object rawGoals = snapshot.get("goals");
        TraceSink.require(rawGoals instanceof List<?>, "missing goal list");
        List<?> goals = (List<?>)rawGoals;
        TraceSink.require(goals.size() <= 12, "goal snapshot must be bounded");
        TraceSink.require(previous.size() < MAX_ENTITIES || previous.containsKey(entityId),
                "goal diff entity budget exceeded");

        Map<Integer, Boolean> current = new HashMap<>();
        List<Map<String, Object>> transitions = new ArrayList<>();
        Map<Integer, Boolean> prior = previous.get(entityId);
        Set<Integer> ids = new HashSet<>();

        for (Object item : goals) {
            TraceSink.require(item instanceof Map<?, ?>, "invalid goal row");
            Map<?, ?> row = (Map<?, ?>) item;
            Object id = row.get("goal_instance_id");
            Object now = row.get("running");
            TraceSink.require(id instanceof Integer && (Integer)id > 0, "missing goal instance id");
            TraceSink.require(now instanceof Boolean, "missing running state");
            int instance = (Integer) id;
            TraceSink.require(ids.add(instance), "duplicate goal id");
            current.put(instance, (Boolean)now);
            if (prior == null || !prior.containsKey(instance) || prior.get(instance).equals(now)) continue;
            if (transitions.size() >= MAX_CHANGES_SHOWN) continue;
            // Use only owned primitive metadata. Do not copy goal code.
            transitions.add(Map.of(
                    "goal_instance_id", instance,
                    "selector", Objects.toString(row.get("selector"), ""),
                    "goal_class", Objects.toString(row.get("goal_class"), ""),
                    "priority", row.get("priority"),
                    "previous_running", prior.get(instance),
                    "current_running", now));
        }
        int observedChanges = 0;
        if (prior != null) for (Map.Entry<Integer,Boolean> entry:current.entrySet()) {
            Boolean before = prior.get(entry.getKey());
            if (before != null && !before.equals(entry.getValue())) observedChanges++;
        }
        previous.put(entityId, current);
        return Map.of(
                "entity_uuid", entityId,
                "changes", transitions,
                "observed_state_changes", observedChanges,
                "changes_truncated", observedChanges > transitions.size(),
                "snapshot_goal_entries", goals.size(),
                "snapshot_truncated", Boolean.TRUE.equals(snapshot.get("truncated")),
                "capture_scope", "END_TICK_RUNNING_STATE_DIFF_NOT_GOAL_CALLBACK");
    }

    public void remove(String entityUuid) { previous.remove(entityUuid); }
    public void clear() { previous.clear(); }
}
