package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import java.io.IOException;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/** Server-thread adapter to the installed Arena owner's actual grant/attestation/lease checks. */
public final class KneekuraDebugCaptureOwner implements KneekuraDebugCardinalCapture.OwnerGate {
    private record Reservation(KneekuraDebugArenaController.Snapshot expected,
                               KneekuraDebugArenaRuntime.CaptureReservation token) {}
    private final KneekuraDebugArenaOwnerGrant grant;
    private final KneekuraDebugCapturePolicy visualPolicy;
    private final KneekuraDebugTankObservation observation;
    private final String observationHash;
    private final Map<String, Reservation> reservations = new HashMap<>();
    public KneekuraDebugCaptureOwner(KneekuraDebugArenaOwnerGrant grant, KneekuraDebugCapturePolicy visualPolicy) {
        this(grant,visualPolicy,null,null);
    }
    KneekuraDebugCaptureOwner(KneekuraDebugArenaOwnerGrant grant,KneekuraDebugCapturePolicy visualPolicy,KneekuraDebugTankObservation observation,String observationHash){
        this.grant = java.util.Objects.requireNonNull(grant);
        this.visualPolicy = java.util.Objects.requireNonNull(visualPolicy);
        this.observation=observation;this.observationHash=observationHash;
    }
    public void assertAuthorized(KneekuraDebugEnv.Config config, KneekuraDebugCaptureSession.Request request) {
        visualPolicy.validate(request); // Before reservation or any presentation mutation.
        try {
            var id = request.identity(); var expected = KneekuraDebugArenaRuntime.snapshotOwner();
            var owner = grant.identity(); var bounds = grant.arena().bounds();
            if(KneekuraDebugCaptureSession.TANK_RIG.equals(request.rig())&&(observation==null||!request.tankObservationHash().equals(observationHash)||
                !request.observationMin().equals(List.of(observation.minX(),observation.minY(),observation.minZ()))||!request.observationMax().equals(List.of(observation.maxX(),observation.maxY(),observation.maxZ()))))throw new IOException("CAPTURE_OBSERVATION_SCOPE_MISMATCH");
            if (!expected.identity().equals(owner) || !config.handshakeNonce().equals(owner.handshakeNonce()) ||
                    !id.debugSessionId().equals(owner.debugSessionId()) || !id.runId().equals(owner.runId()) ||
                    !id.runSnapshotId().equals(owner.runSnapshotId()) || id.processEpoch() != owner.processEpoch() ||
                    !id.experimentId().equals(owner.experimentId()) || !id.requestHash().equals(grant.requestHash()) ||
                    id.generation() != grant.generation() || !id.arenaId().equals(expected.arenaId()) ||
                    id.arenaEpoch() != expected.arenaEpoch() || id.arenaRevision() != expected.arenaRevision() ||
                    !id.baselineHash().equals(grant.arena().baselineHash()) ||
                    !request.arenaMin().equals(List.of(bounds.minX(), bounds.minY(), bounds.minZ())) ||
                    !request.arenaMax().equals(List.of(bounds.maxX(), bounds.maxY(), bounds.maxZ())) ||
                    !new HashSet<>(request.behaviorAssertionIds()).equals(visualPolicy.behaviorAssertionIds()))
                throw new IOException("CAPTURE_GRANT_MISMATCH");
            Set<String> authorized = new HashSet<>(); grant.subjects().values().forEach(s -> authorized.add(s.uuid()));
            if (!request.subjects().stream().allMatch(uuid -> authorized.contains(uuid.toString())))
                throw new IOException("CAPTURE_SUBJECT_NOT_AUTHORIZED");
            Reservation prior = reservations.get(request.captureId());
            if (prior == null) {
                if (reservations.size() >= 4) throw new IOException("CAPTURE_SET_BUDGET");
                var token = KneekuraDebugArenaRuntime.reserveCapturesOwner(expected, id.requestHash(), id.generation(), 4);
                reservations.put(request.captureId(), new Reservation(expected, token));
            } else KneekuraDebugArenaRuntime.validateCaptureOwner(prior.token(), prior.expected());
        } catch (IOException error) { throw new IllegalStateException("CAPTURE_OWNER_REJECTED", error); }
    }
    public void assertIdleArena(KneekuraDebugCaptureSession.Request request) {
        try {
            Reservation reservation = reservations.get(request.captureId());
            if (reservation == null) throw new IOException("CAPTURE_NOT_RESERVED");
            KneekuraDebugArenaRuntime.validateCaptureOwner(reservation.token(), reservation.expected());
            KneekuraDebugArenaRuntime.requireCaptureLeaseRemainingOwner(reservation.expected(), request.barrierBudgetMs() + 100);
        } catch (IOException error) { throw new IllegalStateException("CAPTURE_ARENA_NOT_IDLE", error); }
    }
    public ServerLevel level(MinecraftServer server, KneekuraDebugCaptureSession.Request request) {
        assertIdleArena(request);
        ServerLevel level=server.getLevel(ResourceKey.create(Registries.DIMENSION, new ResourceLocation(grant.dimensionId())));
        if(KneekuraDebugCaptureSession.TANK_RIG.equals(request.rig()))try{
            observation.verifySaved(KneekuraDebugOwnerFiles.json(server.getWorldPath(net.minecraft.world.level.storage.LevelResource.ROOT).toRealPath(),"kneekura-tank-owner.json",null,65536));
            for(String view:KneekuraDebugCaptureSession.VIEWS){var pose=request.pose(view);var block=net.minecraft.core.BlockPos.containing(pose.get(0),pose.get(1),pose.get(2));
                if(level==null||!level.getChunkSource().hasChunk(Math.floorDiv(block.getX(),16),Math.floorDiv(block.getZ(),16))||!level.getBlockState(block).getCollisionShape(level,block).isEmpty())throw new IOException("CAPTURE_OBSERVATION_CAMERA_BLOCKED_OR_UNLOADED");}
        }catch(IOException e){throw new IllegalStateException("CAPTURE_OBSERVATION_UNAVAILABLE",e);}
        return level;
    }
}
