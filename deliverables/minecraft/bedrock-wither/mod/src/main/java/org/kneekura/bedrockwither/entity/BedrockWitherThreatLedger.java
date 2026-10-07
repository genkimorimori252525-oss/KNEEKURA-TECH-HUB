package org.kneekura.bedrockwither.entity;

import net.minecraft.world.entity.LivingEntity;

import java.util.Collection;
import java.util.Comparator;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

public final class BedrockWitherThreatLedger {
    public enum Metric {
        TOTAL_DAMAGE,
        MAX_SINGLE_HIT
    }

    private final Map<UUID, Entry> entries = new HashMap<>();

    public void recordDamage(LivingEntity attacker, float amount, long gameTime) {
        if (amount <= 0.0F || !attacker.isAlive()) {
            return;
        }

        entries.compute(attacker.getUUID(), (uuid, previous) -> {
            if (previous == null) {
                return new Entry(amount, amount, gameTime);
            }
            return new Entry(
                    previous.totalDamage + amount,
                    Math.max(previous.maxSingleHit, amount),
                    gameTime
            );
        });
    }

    public Optional<LivingEntity> selectHighestDamageTarget(
            Collection<? extends LivingEntity> candidates,
            Metric metric,
            long gameTime,
            long ttlTicks
    ) {
        prune(gameTime, ttlTicks);

        Comparator<LivingEntity> comparator = Comparator
                .comparingDouble((LivingEntity entity) -> score(entity.getUUID(), metric))
                .thenComparingLong(entity -> lastHitTick(entity.getUUID()))
                .thenComparing(entity -> entity.getUUID().toString());

        return candidates.stream()
                .filter(LivingEntity::isAlive)
                .filter(entity -> entries.containsKey(entity.getUUID()))
                .max(comparator)
                .map(LivingEntity.class::cast);
    }

    public void prune(long gameTime, long ttlTicks) {
        if (ttlTicks < 0L) {
            return;
        }
        entries.entrySet().removeIf(entry -> gameTime - entry.getValue().lastHitTick > ttlTicks);
    }

    public void clear() {
        entries.clear();
    }

    public int size() {
        return entries.size();
    }

    private double score(UUID uuid, Metric metric) {
        Entry entry = entries.get(uuid);
        if (entry == null) {
            return 0.0D;
        }
        return metric == Metric.TOTAL_DAMAGE ? entry.totalDamage : entry.maxSingleHit;
    }

    private long lastHitTick(UUID uuid) {
        Entry entry = entries.get(uuid);
        return entry == null ? Long.MIN_VALUE : entry.lastHitTick;
    }

    private record Entry(float totalDamage, float maxSingleHit, long lastHitTick) {
    }
}
