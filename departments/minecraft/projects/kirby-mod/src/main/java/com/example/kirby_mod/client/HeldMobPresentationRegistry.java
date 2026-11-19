package com.example.kirby_mod.client;

import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

public final class HeldMobPresentationRegistry {

    private static final Map<Integer, State> HELD_BY_KIRBY = new HashMap<>();
    private static final Map<UUID, Integer> HIDE_REFERENCES = new HashMap<>();

    private HeldMobPresentationRegistry() {}

    public static void apply(int kirbyEntityId, int revision, List<UUID> heldMobIds) {
        State previous = HELD_BY_KIRBY.get(kirbyEntityId);
        if (previous != null && revision < previous.revision) return;
        if (previous != null) {
            removeReferences(previous.heldMobIds);
        }
        State next = new State(revision, new HashSet<>(heldMobIds));
        HELD_BY_KIRBY.put(kirbyEntityId, next);
        addReferences(next.heldMobIds);
    }

    /** Constant-time lookup on the render path. */
    public static boolean shouldHide(UUID entityId) {
        return HIDE_REFERENCES.containsKey(entityId);
    }

    public static void removeKirby(int kirbyEntityId) {
        State removed = HELD_BY_KIRBY.remove(kirbyEntityId);
        if (removed != null) {
            removeReferences(removed.heldMobIds);
        }
    }

    public static void clear() {
        HELD_BY_KIRBY.clear();
        HIDE_REFERENCES.clear();
    }

    public static int hiddenMobCountForDebug() {
        return HIDE_REFERENCES.size();
    }

    private static void addReferences(Set<UUID> ids) {
        for (UUID id : ids) {
            HIDE_REFERENCES.merge(id, 1, Integer::sum);
        }
    }

    private static void removeReferences(Set<UUID> ids) {
        for (UUID id : ids) {
            Integer count = HIDE_REFERENCES.get(id);
            if (count == null || count <= 1) {
                HIDE_REFERENCES.remove(id);
            } else {
                HIDE_REFERENCES.put(id, count - 1);
            }
        }
    }

    private static final class State {
        private final int revision;
        private final Set<UUID> heldMobIds;

        private State(int revision, Set<UUID> heldMobIds) {
            this.revision = revision;
            this.heldMobIds = heldMobIds;
        }
    }
}
