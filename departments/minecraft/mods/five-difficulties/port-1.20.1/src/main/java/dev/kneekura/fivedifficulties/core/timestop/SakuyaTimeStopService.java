package dev.kneekura.fivedifficulties.core.timestop;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/** Per-level logical registry. Minecraft adapters may keep one instance per ServerLevel. */
public final class SakuyaTimeStopService {
    private final Map<UUID, SakuyaTimeStopInstance> active = new LinkedHashMap<>();
    private final TimeStopPolicy policy;

    public SakuyaTimeStopService() {
        this(new TimeStopPolicy());
    }

    public SakuyaTimeStopService(TimeStopPolicy policy) {
        if (policy == null) throw new NullPointerException("policy");
        this.policy = policy;
    }

    public void start(SakuyaTimeStopInstance instance) {
        if (instance == null) throw new NullPointerException("instance");
        active.values().removeIf(existing -> existing.sourceEntityId().equals(instance.sourceEntityId()));
        active.put(instance.stopId(), instance);
    }

    public boolean stopSource(UUID sourceEntityId) {
        boolean removed = false;
        Iterator<SakuyaTimeStopInstance> it = active.values().iterator();
        while (it.hasNext()) {
            if (it.next().sourceEntityId().equals(sourceEntityId)) {
                it.remove();
                removed = true;
            }
        }
        return removed;
    }

    public void purgeExpired(int tick) {
        active.values().removeIf(stop -> stop.isExpiredAt(tick));
    }

    public List<SakuyaTimeStopInstance> activeStops(int tick) {
        List<SakuyaTimeStopInstance> out = new ArrayList<>();
        for (SakuyaTimeStopInstance stop : active.values()) {
            if (stop.isActiveAt(tick)) out.add(stop);
        }
        return List.copyOf(out);
    }

    /**
     * Conservative overlap priority until X1 duplicate-controller handling is moved
     * to the Forge controller layer:
     * FREEZE > HALF_SPEED > SPECIAL_PROJECTILE > ALLOW.
     */
    public TimeStopDecision decision(TimeStopSubject subject, int tick) {
        TimeStopDecision result = TimeStopDecision.ALLOW;
        for (SakuyaTimeStopInstance stop : active.values()) {
            TimeStopDecision next = policy.decide(stop, subject, tick);
            if (next == TimeStopDecision.FREEZE) return TimeStopDecision.FREEZE;
            if (next == TimeStopDecision.HALF_SPEED) result = TimeStopDecision.HALF_SPEED;
            else if (next == TimeStopDecision.SPECIAL_PROJECTILE && result == TimeStopDecision.ALLOW) {
                result = TimeStopDecision.SPECIAL_PROJECTILE;
            }
        }
        return result;
    }

    /**
     * True when the modern machinery should suppress this entity's normal tick.
     * FULL_STOP always suppresses; HALF_SPEED suppresses X1's count=0/even phase.
     */
    public boolean shouldCancelNormalTick(TimeStopSubject subject, int tick) {
        for (SakuyaTimeStopInstance stop : active.values()) {
            TimeStopDecision next = policy.decide(stop, subject, tick);
            if (next == TimeStopDecision.FREEZE) return true;
            if (next == TimeStopDecision.HALF_SPEED && stop.shouldCancelEntityTickForMode(tick)) return true;
        }
        return false;
    }
}
