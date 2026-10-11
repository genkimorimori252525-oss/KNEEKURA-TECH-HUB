package org.kneekura.techhub.warfarewings.trace;

import net.minecraft.server.level.ServerLevel;
import net.minecraftforge.event.server.ServerStoppingEvent;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.phys.Vec3;

import java.util.HashSet;
import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.Map;
import java.util.Set;

/**
 * Short-lived Forge GameTest-only chunk tickets for a genuinely moving plane.
 * A 1x1 GameTest structure does not keep an aircraft 200 blocks above it
 * ticking after it crosses loaded world boundaries.
 *
 * Only chunks which setChunkForced() actually changed are ever released.
 * Operator-controlled aircraft never use these GameTest tickets.
 */
final class GameTestFlightChunkLease {
    // Keep a two-chunk safety margin around both current and projected
    // physical positions. A one-chunk margin still permitted a one-server-
    // tick stall as an escort crossed z=64 in the strict 340-tick GameTest,
    // despite FULL chunk prewarming. This wider *test-owned chunk ticket*
    // margin does not change any airplane control, motion, attacker, starting
    // geometry or pass threshold; a missing original Entity tick STILL fails.
    private static final int SIDE = 2;
    // A pair of planes may share a chunk. Releasing the first plane's lease
    // must not unforce a chunk required by the second one.
    private static final Map<ServerLevel, Map<Long, SharedTicket>> SHARED =
            new IdentityHashMap<>();
    private static final class SharedTicket {
        int holders = 1;
        final boolean owned;
        SharedTicket(boolean owned) { this.owned = owned; }
    }

    private final ServerLevel level;
    private final Set<Long> active = new HashSet<>();
    private int transitions;

    GameTestFlightChunkLease(ServerLevel level) {
        this.level = level;
    }

    void update(Entity aircraft) {
        if (aircraft.level() != level || aircraft.isRemoved())
            throw new IllegalStateException("Chunk lease aircraft left its test dimension");
        update(aircraft.position(), aircraft.getDeltaMovement());
    }

    /**
     * On an intermittent real entity-tick stall, synchronously confirm that
     * the same already-owned chunk area is FULL-loaded before the next server
     * tick. Minecraft must still actually update the aircraft; this method
     * cannot change an Entity tickCount, position or physical velocity and
     * the caller's existing >20-tick liveness failure remains authoritative.
     */
    void reconfirmLoaded(Entity aircraft) {
        update(aircraft);
        for (long key : active) {
            ChunkPos chunk = new ChunkPos(key);
            level.getChunk(chunk.x, chunk.z);
        }
    }

    /** Call before addFreshEntity when an actor starts outside loaded GameTest chunks. */
    void update(Vec3 p, Vec3 v) {
        Set<Long> needed = new HashSet<>();
        addSquare(needed, p.x, p.z);
        // Ahead-of-velocity loading is observation-independent: it concerns
        // only the test owner's own aircraft, never an unseen hostile.
        addSquare(needed, p.x + v.x * 28, p.z + v.z * 28);
        for (long key : needed) {
            if (active.contains(key)) continue;
            acquire(key);
            active.add(key);
            transitions++;
        }
        for (long key : Set.copyOf(active)) {
            if (needed.contains(key)) continue;
            active.remove(key);
            release(key);
        }
    }

    private static void addSquare(Set<Long> out, double x, double z) {
        int cx = ((int) Math.floor(x)) >> 4;
        int cz = ((int) Math.floor(z)) >> 4;
        for (int dx = -SIDE; dx <= SIDE; dx++)
            for (int dz = -SIDE; dz <= SIDE; dz++)
                out.add(ChunkPos.asLong(cx + dx, cz + dz));
    }

    int transitions() { return transitions; }

    private void acquire(long key) {
        Map<Long, SharedTicket> levelTickets =
                SHARED.computeIfAbsent(level, unused -> new HashMap<>());
        SharedTicket already = levelTickets.get(key);
        if (already != null) {
            already.holders++;
            return;
        }
        ChunkPos chunk = new ChunkPos(key);
        boolean owned = level.setChunkForced(chunk.x, chunk.z, true);
        levelTickets.put(key, new SharedTicket(owned));
        // A forced chunk ticket does not guarantee its FULL chunk has been
        // synchronously loaded before the *next* aircraft entity relocation.
        // Long original-Forge flights have stopped at precisely a 16-block
        // boundary while the server clock continued. This is test-only chunk
        // liveness maintenance, never an adjustment to the aircraft physics.
        // Acquire before releasing trailing chunks; synchronously stage the
        // forward/current area the real entity is physically about to cross.
        try {
            level.getChunk(chunk.x, chunk.z);
        } catch (RuntimeException unableToLoad) {
            levelTickets.remove(key);
            if (owned) level.setChunkForced(chunk.x, chunk.z, false);
            if (levelTickets.isEmpty()) SHARED.remove(level);
            throw unableToLoad;
        }
    }

    private void release(long key) {
        Map<Long, SharedTicket> levelTickets = SHARED.get(level);
        if (levelTickets == null || !levelTickets.containsKey(key))
            throw new IllegalStateException("Chunk lease reference lost for " + key);
        SharedTicket ticket = levelTickets.get(key);
        if (--ticket.holders > 0) return;
        levelTickets.remove(key);
        if (ticket.owned) {
            ChunkPos chunk = new ChunkPos(key);
            level.setChunkForced(chunk.x, chunk.z, false);
        }
        if (levelTickets.isEmpty()) SHARED.remove(level);
    }

    void close() {
        for (long key : Set.copyOf(active)) release(key);
        active.clear();
    }

    static void onServerStopping(ServerStoppingEvent event) {
        // Emergency cleanup if a GameTest throws before its normal finalizer.
        // Only undo our own setChunkForced(true), and do not alter force
        // tickets that predated this test's leases.
        for (var entry : new HashMap<>(SHARED).entrySet()) {
            ServerLevel level = entry.getKey();
            if (level.getServer() != event.getServer()) continue;
            for (var ticket : entry.getValue().entrySet()) {
                if (!ticket.getValue().owned) continue;
                ChunkPos chunk = new ChunkPos(ticket.getKey());
                level.setChunkForced(chunk.x, chunk.z, false);
            }
            SHARED.remove(level);
        }
    }
}
