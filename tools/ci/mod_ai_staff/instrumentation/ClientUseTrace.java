package org.kneekura.staff;

import java.util.ArrayDeque;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/** Opt-in fixture instrumentation. Reads game state; never supplies a gameplay verdict. */
public final class ClientUseTrace {
    private static final int LIMIT = 16;
    private static final ArrayDeque<Map<String, Object>> RECORDS = new ArrayDeque<>();
    private static final Scope NOOP = new Scope();
    private static Thread owner;
    private static long started, completed, unknown, dropped;

    private ClientUseTrace() {}

    private static Map<String, Object> frozen(Object... values) {
        Map<String, Object> result = new LinkedHashMap<>();
        for (int i = 0; i < values.length; i += 2) result.put((String) values[i], values[i + 1]);
        return Collections.unmodifiableMap(result);
    }

    private static Map<String, Object> state(Player player, Item usedItem) {
        float health = player.getHealth();
        ItemStack hand = player.getMainHandItem();
        String item = Objects.requireNonNull(BuiltInRegistries.ITEM.getKey(hand.getItem())).toString();
        int count = hand.getCount(), damage = hand.getDamageValue();
        MobEffectInstance effect = player.getEffect(MobEffects.GLOWING);
        Map<String, Object> glowing = effect == null ? null : frozen(
                "amplifier", effect.getAmplifier(), "duration_ticks", effect.getDuration());
        var cooldowns = player.getCooldowns();
        boolean active = cooldowns.isOnCooldown(usedItem);
        float fraction = cooldowns.getCooldownPercent(usedItem, 0.0F);
        if (!Float.isFinite(health) || !Float.isFinite(fraction) || count < 0 || damage < 0
                || fraction < 0.0F || fraction > 1.0F) throw new IllegalStateException("Invalid client state");
        return frozen("health", health, "main_hand", frozen("item", item, "count", count, "damage", damage),
                "glowing", glowing, "staff_cooldown", frozen("active", active, "fraction", fraction));
    }

    /** Server calls are no-op. Probe errors never escape into Item.use. */
    public static Scope begin(Level level, Player player, ItemStack stack) {
        long sequence = 0;
        String uuid = null;
        try {
            if (level == null || !level.isClientSide) return NOOP;
            synchronized (ClientUseTrace.class) {
                sequence = ++started;
                if (owner == null) owner = Thread.currentThread();
                if (owner != Thread.currentThread()) {
                    retain(sequence, null, false, null, null, 0, 0);
                    return NOOP;
                }
            }
            uuid = player.getUUID().toString();
            Item usedItem = stack.getItem();
            return new Scope(sequence, uuid, player, usedItem, state(player, usedItem), Thread.currentThread());
        } catch (Throwable failure) {
            if (sequence != 0) {
                try { synchronized (ClientUseTrace.class) { retain(sequence, uuid, false, null, null, 0, 0); } }
                catch (Throwable ignored) { /* A missing completion is never successful evidence. */ }
            }
            return NOOP;
        }
    }

    private static void retain(long sequence, String uuid, boolean observed,
                               Map<String, Object> before, Map<String, Object> after,
                               long effectAttempts, long cooldownAttempts) {
        // Counters remain conservative if allocation fails: no complete row means no usable assertion.
        if (observed) completed++; else unknown++;
        Map<String, Object> row = frozen("sequence", sequence, "player_uuid", uuid,
                "completed", observed, "unchanged", observed ? Boolean.valueOf(before.equals(after)) : null,
                "before", before, "after", after,
                "effect_mutation_attempts", observed ? Long.valueOf(effectAttempts) : null,
                "cooldown_mutation_attempts", observed ? Long.valueOf(cooldownAttempts) : null);
        if (RECORDS.size() == LIMIT) { RECORDS.removeFirst(); dropped++; }
        RECORDS.addLast(row);
    }

    /** Deeply immutable detached snapshot; empty/incomplete traces are not acceptance. */
    public static Map<String, Object> snapshot() {
        synchronized (ClientUseTrace.class) {
            return frozen("schema_version", 1, "limit", LIMIT, "started", started, "completed", completed,
                    "unknown", unknown, "dropped", dropped, "records", List.copyOf(RECORDS));
        }
    }

    public static final class Scope {
        private final long sequence;
        private final String uuid;
        private final Player player;
        private final Item usedItem;
        private final Map<String, Object> before;
        private final Thread thread;
        private boolean closed, failed, reportedUnknown;
        private long effectAttempts, cooldownAttempts;

        private Scope() {
            sequence = 0; uuid = null; player = null; usedItem = null; before = null; thread = null; closed = true;
        }
        private Scope(long sequence, String uuid, Player player, Item usedItem,
                      Map<String, Object> before, Thread thread) {
            this.sequence = sequence; this.uuid = uuid; this.player = player; this.usedItem = usedItem;
            this.before = before; this.thread = thread;
        }

        /** Counts only the two verified fixture write sites; never performs their writes. */
        public void mutationAttempt(String site) {
            if (sequence == 0) return;
            try {
                synchronized (ClientUseTrace.class) {
                    if (closed || thread != Thread.currentThread()
                            || !("effect".equals(site) || "cooldown".equals(site))) {
                        failed = true;
                        if (closed && !reportedUnknown) {
                            reportedUnknown = true;
                            RECORDS.removeIf(row -> ((Long) row.get("sequence")).longValue() == sequence);
                            retain(sequence, uuid, false, before, null, 0, 0);
                        }
                        return;
                    }
                    if (failed) return;
                    if ("effect".equals(site)) effectAttempts = Math.incrementExact(effectAttempts);
                    else cooldownAttempts = Math.incrementExact(cooldownAttempts);
                }
            } catch (Throwable ignored) { failed = true; }
        }

        /** Always invoked by the exact fixture hook's finally, including exceptional exits. */
        public void close() {
            try {
                synchronized (ClientUseTrace.class) {
                    if (closed) return;
                    closed = true;
                }
                Map<String, Object> after = null;
                boolean observed = false;
                try {
                    if (failed || thread != Thread.currentThread()) throw new IllegalStateException("Client trace scope invalid");
                    if (!uuid.equals(player.getUUID().toString())) throw new IllegalStateException("Player changed");
                    after = state(player, usedItem);
                    observed = true;
                } catch (Throwable failure) { /* Retain UNKNOWN, never unchanged=true. */ }
                synchronized (ClientUseTrace.class) {
                    if (failed) observed = false;
                    reportedUnknown = !observed;
                    retain(sequence, uuid, observed, before, after, effectAttempts, cooldownAttempts);
                }
            } catch (Throwable ignored) { /* A missing completion remains incomplete evidence. */ }
        }
    }
}
