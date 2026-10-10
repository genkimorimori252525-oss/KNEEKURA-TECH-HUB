package org.kneekura.sporeobserver;

import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.goal.GoalSelector;
import net.minecraft.world.entity.ai.goal.WrappedGoal;
import net.minecraftforge.fml.util.ObfuscationReflectionHelper;

import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;

/**
 * Passive Forge 1.20.1 GoalSelector observation. No goals are added,
 * interrupted, ticked, removed or mutated. The two protected Mob fields are
 * resolved from stable SRG identifiers by Forge's own remapping helper.
 */
public final class GoalRuntimeSampler {
    private static final int MAX_CAPTURED_GOALS = 24;
    private final Field actionField, targetField;

    public GoalRuntimeSampler() {
        actionField = ObfuscationReflectionHelper.findField(Mob.class, "f_21345_");
        targetField = ObfuscationReflectionHelper.findField(Mob.class, "f_21346_");
    }

    public Map<String,Object> snapshot(Mob mob) throws IllegalAccessException {
        ArrayList<Map<String,Object>> values = new ArrayList<>();
        collect(values, "goal", (GoalSelector)actionField.get(mob));
        collect(values, "target", (GoalSelector)targetField.get(mob));

        values.sort(Comparator
                .comparingInt((Map<String,Object> row) -> ((Number)row.get("priority")).intValue())
                .thenComparing(row -> (String)row.get("selector"))
                .thenComparing(row -> (String)row.get("goal_class")));

        int allCount = values.size();
        int running = (int) values.stream().filter(row -> Boolean.TRUE.equals(row.get("running"))).count();
        List<Map<String,Object>> captured = values.subList(0, Math.min(allCount, MAX_CAPTURED_GOALS));
        return Map.of(
                "entity_uuid", mob.getUUID().toString(),
                "registered_goal_count", allCount,
                "registered_running_count", running,
                "goals", new ArrayList<>(captured),
                "truncated", allCount > MAX_CAPTURED_GOALS,
                "capture_scope", "READ_ONLY_GOALSELECTOR_SNAPSHOT_NOT_SCHEDULER_CALL");
    }

    private static void collect(List<Map<String,Object>> into, String selector, GoalSelector goals) {
        for (WrappedGoal wrapped : goals.getAvailableGoals()) {
            var flags = wrapped.getFlags().stream()
                    .map(Enum::name).sorted().toList();
            into.add(Map.of(
                    "selector", selector,
                    "priority", wrapped.getPriority(),
                    "goal_class", wrapped.getGoal().getClass().getName(),
                    "flags", flags,
                    "running", wrapped.isRunning()));
        }
    }
}
