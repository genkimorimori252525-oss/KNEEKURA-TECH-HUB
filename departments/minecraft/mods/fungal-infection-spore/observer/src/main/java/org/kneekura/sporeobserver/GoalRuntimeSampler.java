package org.kneekura.sporeobserver;

import net.minecraft.world.entity.Mob;
import org.kneekura.sporeobserver.core.GoalSnapshotSelection;
import net.minecraft.world.entity.ai.goal.GoalSelector;
import net.minecraft.world.entity.ai.goal.WrappedGoal;
import net.minecraftforge.fml.util.ObfuscationReflectionHelper;

import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;

/**
 * Passive Forge 1.20.1 GoalSelector snapshots.
 * Never invokes Goal.start/stop/tick/canUse, never modifies the selector.
 * Goal IDs are ephemeral observer-assigned integers; they are NOT persisted IDs.
 */
public final class GoalRuntimeSampler {
    private static final int MAX_GOAL_IDENTITIES = 2048;
    private final Field actionField, targetField;
    private final IdentityHashMap<WrappedGoal, Integer> identities = new IdentityHashMap<>();
    private int nextIdentity = 1;

    public GoalRuntimeSampler() {
        actionField = ObfuscationReflectionHelper.findField(Mob.class, "f_21345_");
        targetField = ObfuscationReflectionHelper.findField(Mob.class, "f_21346_");
    }

    /**
     * When truncation is required, retain watched Spore logistics/support
     * candidates first, then running goals, then low-priority-number goals.
     * This avoids systematically discarding the priority-4 Witch buff goals.
     */
    public Map<String,Object> snapshot(Mob mob) throws IllegalAccessException {
        ArrayList<Map<String,Object>> values = new ArrayList<>();
        collect(values, "goal", (GoalSelector)actionField.get(mob));
        collect(values, "target", (GoalSelector)targetField.get(mob));

        int total = values.size();
        int running = (int)values.stream().filter(row -> Boolean.TRUE.equals(row.get("running"))).count();
        List<Map<String,Object>> captured = GoalSnapshotSelection.select(values);
        return Map.of(
                "entity_uuid", mob.getUUID().toString(),
                "registered_goal_count", total,
                "registered_running_count", running,
                "goals", new ArrayList<>(captured),
                "truncated", total > GoalSnapshotSelection.MAX_GOALS,
                "selection_policy", "WATCHED_SPORE_ROLES_THEN_RUNNING_THEN_PRIORITY",
                "capture_scope", "READ_ONLY_GOALSELECTOR_SNAPSHOT_NOT_SCHEDULER_CALL");
    }

    private int stableId(WrappedGoal goal) {
        Integer prior = identities.get(goal);
        if (prior != null) return prior;
        if (identities.size() >= MAX_GOAL_IDENTITIES) {
            throw new IllegalStateException("Goal identity observation limit");
        }
        int id = nextIdentity++;
        identities.put(goal, id);
        return id;
    }

    private void collect(List<Map<String,Object>> into, String selector, GoalSelector goals) {
        for (WrappedGoal wrapped : goals.getAvailableGoals()) {
            var flags = wrapped.getFlags().stream().map(Enum::name).sorted().toList();
            into.add(Map.of(
                    "goal_instance_id", stableId(wrapped),
                    "selector", selector,
                    "priority", wrapped.getPriority(),
                    "goal_class", wrapped.getGoal().getClass().getName(),
                    "flags", flags,
                    "running", wrapped.isRunning()));
        }
    }
}
