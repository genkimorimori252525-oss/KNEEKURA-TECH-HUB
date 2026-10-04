package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.storage.LevelResource;

/** A registered resource capsule opts the current scoped owner into client presentation only. */
public final class KneekuraDebugTankPresentation {
    private static volatile KneekuraDebugTankPresentationRecipe.Context context;
    private static String attemptedIdentity;
    private static String reportedFailureIdentity;
    private KneekuraDebugTankPresentation() {}

    static void clear() { context = null; }

    static KneekuraDebugTankPresentationRecipe.View viewForRender(MinecraftServer currentServer) {
        var current = context;
        return current == null ? null : current.viewFor(currentServer, System.nanoTime());
    }

    public static void update(KneekuraDebugEnv.Config config, MinecraftServer server) {
        try {
            if (!config.enabled() || config.ownerSetup() == null || server.isDedicatedServer()
                    || !server.isSameThread() || !"KNEEKURA_DEBUG_WORLD".equals(config.worldName())
                    || !config.worldName().equals(server.getWorldData().getLevelName())) {
                clear();
                return;
            }
            var state = KneekuraDebugArenaRuntime.snapshotOwner();
            var identity = state.identity();
            if (state.unsafe() || !identity.debugSessionId().equals(config.debugSessionId())
                    || !identity.runId().equals(config.runId()) || !identity.runSnapshotId().equals(config.runSnapshotId())
                    || identity.processEpoch() != config.processEpoch() || !identity.handshakeNonce().equals(config.handshakeNonce())) {
                clear();
                return;
            }
            KneekuraDebugArenaRuntime.requireCaptureLeaseRemainingOwner(state, 0);
            if (config.identityKey().equals(attemptedIdentity)) return;
            attemptedIdentity = config.identityKey();
            clear();
            var root = config.runDir().toRealPath();
            var envelope = KneekuraDebugOwnerFiles.json(root, "control/owner-envelope.json", config.ownerSetup().sha256(), 16 * 1024);
            if (envelope.has("tankRotationHash")) return;
            var materials = KneekuraDebugOwnerFiles.json(root, "control/owner-material-descriptor.json",
                    KneekuraDebugOwnerInputs.t(envelope, "materialDescriptorHash"), 16 * 1024);
            byte[] resource = KneekuraDebugOwnerFiles.read(root, "control/owner-materials/resources.bin",
                    KneekuraDebugOwnerInputs.t(materials, "resourceArtifactHash"), 16 * 1024 * 1024);
            var registered = KneekuraDebugTankPresentationRecipe.fromRegisteredResource(resource);
            if (registered == null) return;
            var world = server.getWorldPath(LevelResource.ROOT).toAbsolutePath().normalize().toRealPath();
            var saved = KneekuraDebugTankPresentationRecipe.parse(KneekuraDebugOwnerFiles.json(
                    world, "kneekura-tank-owner.json", null, 64 * 1024));
            if (!registered.equals(saved)) throw new IllegalArgumentException("TANK_PRESENTATION_WORLD_RESOURCE_MISMATCH");
            var lease = KneekuraDebugArenaRuntime.presentationLeaseOwner(state);
            context = new KneekuraDebugTankPresentationRecipe.Context(registered, server, lease.issuedNanos(), lease.deadlineNanos());
        } catch (Exception error) {
            clear();
            // Owner absence during startup is normal; log a failed opt-in only once per run.
            if (config.identityKey().equals(attemptedIdentity)
                    && !config.identityKey().equals(reportedFailureIdentity)) {
                TouhouLittleMaid.LOGGER.warn("[KNEEKURA-DEBUG] Tank presentation unavailable: {}", error.getClass().getSimpleName());
                reportedFailureIdentity = config.identityKey();
            }
        }
    }
}
