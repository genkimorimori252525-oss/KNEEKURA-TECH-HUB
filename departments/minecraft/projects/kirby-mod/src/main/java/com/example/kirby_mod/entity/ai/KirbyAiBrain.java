package com.example.kirby_mod.entity.ai;

import com.example.kirby_mod.debug.KirbyDebugInfoProvider;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.EnumSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * Lane-based decision memory. Enforcement is enabled lane-by-lane by the Goal
 * that owns the corresponding behavior; this class itself does not mutate entities.
 */
public final class KirbyAiBrain implements KirbyDebugInfoProvider {

    public enum Mode {
        OBSERVE,
        HYBRID,
        ENFORCE
    }

    private static final double DEFAULT_SWITCH_MARGIN = 0.35D;
    private static final int MAX_DEBUG_CANDIDATES = 5;

    private final EnumMap<KirbyAiAction, Integer> cooldownUntilTick =
            new EnumMap<>(KirbyAiAction.class);
    private final EnumMap<KirbyDecisionLane, KirbyAiAction> activeActions =
            new EnumMap<>(KirbyDecisionLane.class);
    private final EnumMap<KirbyDecisionLane, KirbyAiDecision> lastDecisions =
            new EnumMap<>(KirbyDecisionLane.class);
    private final EnumMap<KirbyDecisionLane, List<KirbyAiCandidate>> lastCandidates =
            new EnumMap<>(KirbyDecisionLane.class);
    private final EnumMap<KirbyDecisionLane, Integer> actionTransitionTicks =
            new EnumMap<>(KirbyDecisionLane.class);
    private final EnumMap<KirbyDecisionLane, Integer> lastDecisionTicks =
            new EnumMap<>(KirbyDecisionLane.class);
    private final EnumSet<KirbyDecisionLane> enforcedLanes =
            EnumSet.noneOf(KirbyDecisionLane.class);
    private Mode mode = Mode.OBSERVE;
    private KirbyLocomotionMode locomotionMode = KirbyLocomotionMode.IDLE;
    private int lastObservedTick;
    private int locomotionTransitionTick;

    public KirbyAiBrain() {
        for (KirbyDecisionLane lane : KirbyDecisionLane.values()) {
            activeActions.put(lane, KirbyAiAction.IDLE);
            lastDecisions.put(lane, KirbyAiDecision.idle(lane, "planner not evaluated"));
            lastCandidates.put(lane, List.of());
            actionTransitionTicks.put(lane, 0);
            lastDecisionTicks.put(lane, -1);
        }
    }

    public void observeActive(KirbyDecisionLane lane, KirbyAiAction action, int tick) {
        if (lane == null || action == null) return;
        if (action != activeActions.get(lane)) {
            activeActions.put(lane, action);
            actionTransitionTicks.put(lane, tick);
        }
        this.lastObservedTick = tick;
        pruneCooldowns(tick);
    }

    public void observeLocomotion(KirbyLocomotionMode locomotion, int tick) {
        if (locomotion == null) return;
        if (locomotion != this.locomotionMode) {
            this.locomotionMode = locomotion;
            this.locomotionTransitionTick = tick;
        }
        this.lastObservedTick = tick;
        pruneCooldowns(tick);
    }

    public KirbyAiDecision evaluate(
            KirbyDecisionLane lane,
            int tick,
            List<KirbyAiCandidate> candidates) {
        List<KirbyAiCandidate> effective = applyCooldowns(tick, candidates);
        effective = effective.stream()
                .filter(candidate -> candidate.lane() == lane)
                .toList();
        KirbyAiDecision previous = lastDecisions.get(lane);
        KirbyAiDecision decision = KirbyAiDecisionPolicy.select(
                effective, lane, previous.action(), DEFAULT_SWITCH_MARGIN);
        lastDecisions.put(lane, decision);
        lastCandidates.put(lane, List.copyOf(effective));
        lastDecisionTicks.put(lane, tick);
        return decision;
    }

    public void startCooldown(KirbyAiAction action, int currentTick, int durationTicks) {
        if (action == null || durationTicks <= 0) return;
        cooldownUntilTick.merge(action, currentTick + durationTicks, Math::max);
    }

    public int cooldownRemaining(KirbyAiAction action, int currentTick) {
        return Math.max(0, cooldownUntilTick.getOrDefault(action, currentTick) - currentTick);
    }

    public Mode getMode() {
        return mode;
    }

    public void setLaneEnforced(KirbyDecisionLane lane, boolean enforced) {
        if (lane == null) return;
        if (enforced) {
            enforcedLanes.add(lane);
        } else {
            enforcedLanes.remove(lane);
        }
        mode = enforcedLanes.isEmpty()
                ? Mode.OBSERVE
                : enforcedLanes.size() == KirbyDecisionLane.values().length
                        ? Mode.ENFORCE
                        : Mode.HYBRID;
    }

    public boolean isLaneEnforced(KirbyDecisionLane lane) {
        return enforcedLanes.contains(lane);
    }

    public KirbyAiAction getActiveAction(KirbyDecisionLane lane) {
        return activeActions.getOrDefault(lane, KirbyAiAction.IDLE);
    }

    public KirbyLocomotionMode getLocomotionMode() {
        return locomotionMode;
    }

    public KirbyAiDecision getLastDecision(KirbyDecisionLane lane) {
        return lastDecisions.get(lane);
    }

    private List<KirbyAiCandidate> applyCooldowns(int tick, List<KirbyAiCandidate> candidates) {
        if (candidates == null || candidates.isEmpty()) return List.of();
        List<KirbyAiCandidate> effective = new ArrayList<>(candidates.size());
        for (KirbyAiCandidate candidate : candidates) {
            if (candidate == null) continue;
            int remaining = cooldownRemaining(candidate.action(), tick);
            if (remaining > 0) {
                effective.add(new KirbyAiCandidate(candidate.action(), candidate.lane(),
                        candidate.score(), false, candidate.legacyOrder(),
                        candidate.reason() + " cooldown=" + remaining));
            } else {
                effective.add(candidate);
            }
        }
        return effective;
    }

    private void pruneCooldowns(int tick) {
        cooldownUntilTick.entrySet().removeIf(entry -> entry.getValue() <= tick);
    }

    @Override
    public void appendDebugInfo(List<String> lines) {
        lines.add("AiBrain: mode=" + mode
                + " enforcedLanes=" + enforcedLanes
                + " locomotion=" + locomotionMode
                + " locomotionAge=" + Math.max(0, lastObservedTick - locomotionTransitionTick));
        for (KirbyDecisionLane lane : KirbyDecisionLane.values()) {
            KirbyAiDecision decision = lastDecisions.get(lane);
            lines.add("AiBrain lane=" + lane
                    + " active=" + activeActions.get(lane)
                    + " activeAge=" + Math.max(0,
                    lastObservedTick - actionTransitionTicks.getOrDefault(lane, 0))
                    + " recommended=" + decision.action()
                    + " score=" + fmt(decision.score())
                    + " retained=" + decision.retainedByHysteresis()
                    + " tick=" + lastDecisionTicks.getOrDefault(lane, -1)
                    + " reason=" + decision.reason());
        }
        int emitted = 0;
        for (KirbyDecisionLane lane : KirbyDecisionLane.values()) {
            for (KirbyAiCandidate candidate : lastCandidates.getOrDefault(lane, List.of())) {
                if (emitted >= MAX_DEBUG_CANDIDATES) break;
                lines.add("AiBrain candidate[" + emitted + "] lane=" + candidate.lane()
                        + " action=" + candidate.action()
                        + " score=" + fmt(candidate.score())
                        + " eligible=" + candidate.eligible()
                        + " legacyOrder=" + candidate.legacyOrder()
                        + " target=" + candidate.targetKey()
                        + " reason=" + candidate.reason());
                emitted++;
            }
            if (emitted >= MAX_DEBUG_CANDIDATES) break;
        }
        lines.add("AiBrain cooldowns=" + cooldownSummary());
        lines.add("AiBrain thought=" + (mode == Mode.OBSERVE
                ? "observing legacy goals; recommendations are not authoritative"
                : mode == Mode.HYBRID
                        ? "planner is authoritative only for enforced lanes"
                        : "planner recommendations are authoritative"));
    }

    private String cooldownSummary() {
        if (cooldownUntilTick.isEmpty()) return "none";
        List<String> values = new ArrayList<>();
        for (Map.Entry<KirbyAiAction, Integer> entry : cooldownUntilTick.entrySet()) {
            values.add(entry.getKey() + "@" + entry.getValue());
        }
        return String.join(",", values);
    }

    private static String fmt(double value) {
        return String.format(Locale.ROOT, "%.2f", value);
    }
}
