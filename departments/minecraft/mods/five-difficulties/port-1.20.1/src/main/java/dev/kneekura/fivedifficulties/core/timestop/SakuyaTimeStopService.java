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
        // P0 keeps at most one active stop per source. Overlap between different sources remains supported.
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
     * Overlap rule: a foreign FREEZE beats SPECIAL_PROJECTILE; SPECIAL beats ALLOW.
     * This keeps multi-stopper behavior conservative until X1 multiplayer is observed.
     */
    public TimeStopDecision decision(TimeStopSubject subject, int tick) {
        TimeStopDecision result = TimeStopDecision.ALLOW;
        for (SakuyaTimeStopInstance stop : active.values()) {
            TimeStopDecision next = policy.decide(stop, subject, tick);
            if (next == TimeStopDecision.FREEZE) return TimeStopDecision.FREEZE;
            if (next == TimeStopDecision.SPECIAL_PROJECTILE) result = TimeStopDecision.SPECIAL_PROJECTILE;
        }
        return result;
    }
}
