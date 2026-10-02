package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import java.io.IOException;
import java.util.*;

/** Source-owner seam. The existing Probe tick connection alone installs from sealed Supervisor inputs. */
public final class KneekuraDebugArenaRuntime {
    /** Implemented only by the Supervisor/Probe owner. Request/grant JSON cannot provide this implementation. */
    @FunctionalInterface public interface OwnerGate {
        void requireAuthorized(KneekuraDebugEnv.Config config,MinecraftServer server,KneekuraDebugArenaOwnerGrant grant)throws IOException;
    }
    public static final OwnerGate UNCONFIGURED=(config,server,grant)->{
        throw new IOException("LIVE_AUTHORIZATION_MISSING;RUNTIME_ATTESTATION_NOT_ESTABLISHED");
    };
    private record Active(KneekuraDebugEnv.Config config,MinecraftServer server,KneekuraDebugArenaOwnerGrant grant,OwnerGate gate,KneekuraDebugArenaController controller,KneekuraDebugArenaController.Lease lease) { }
    public record CaptureReservation(String token,String requestHash,int generation,String leaseId,int count) { }
    private static Active active;
    private static final Set<String> SEEN_GRANTS=new HashSet<>();
    private static int capturesReserved;
    private static final Map<String,CaptureReservation> CAPTURE_RESERVATIONS=new HashMap<>();
    private KneekuraDebugArenaRuntime(){ }

    /** Caller is trusted owner source, never a request-controlled callback/boolean. All live predicates must be verified by gate. */
    public static void installOwner(KneekuraDebugEnv.Config config,MinecraftServer server,ServerLevel level,KneekuraDebugArenaOwnerGrant grant,OwnerGate gate,KneekuraDebugForgeArenaBackend.ObservationSink sink)throws IOException {
        Objects.requireNonNull(gate).requireAuthorized(config,server,grant);
        Objects.requireNonNull(config);Objects.requireNonNull(server);Objects.requireNonNull(level);Objects.requireNonNull(grant);
        if(!server.isSameThread())throw new IOException("SERVER_THREAD_REQUIRED");
        if(active!=null)throw new IOException("ARENA_OWNER_ALREADY_INSTALLED");
        String grantKey=config.identityKey()+"|"+grant.grantId();
        if(SEEN_GRANTS.contains(grantKey))throw new IOException("OWNER_GRANT_ALREADY_CONSUMED");
        var id=grant.identity();
        if(!config.enabled()||!id.debugSessionId().equals(config.debugSessionId())||!id.runId().equals(config.runId())||!id.runSnapshotId().equals(config.runSnapshotId())||id.processEpoch()!=config.processEpoch()||!id.handshakeNonce().equals(config.handshakeNonce())||!grant.disposableWorldName().equals(config.worldName()))throw new IOException("OWNER_GRANT_IDENTITY_MISMATCH");
        long issued=System.nanoTime(),duration=grant.timeBudgetMs()*1_000_000L;
        KneekuraDebugForgeArenaBackend.AuthorityCheck authority=()->{
            gate.requireAuthorized(config,server,grant);
            long elapsed=System.nanoTime()-issued;
            if(elapsed<0||elapsed>=duration)throw new IOException("LEASE_EXPIRED_OR_CLOCK_CHANGED");
        };
        var backend=new KneekuraDebugForgeArenaBackend(config,server,level,grant.dimensionId(),grant.arena().bounds(),grant.subjects(),sink,authority);
        var lease=new KneekuraDebugArenaController.Lease(grant.leaseId(),id,issued,issued+duration,grant.maxActions(),grant.allowedActions());
        var controller=new KneekuraDebugArenaController(id,grant.arena(),lease,grant.subjects(),backend,new KneekuraDebugActionJournal(config.runDir()),System::nanoTime);
        SEEN_GRANTS.add(grantKey);active=new Active(config,server,grant,gate,controller,lease);capturesReserved=0;CAPTURE_RESERVATIONS.clear();
    }
    public static String readiness(){return active==null?"BLOCKED":active.controller().snapshot().unsafe()?"BLOCKED":"OWNER_INSTALLED";}
    public static KneekuraDebugArenaController.Snapshot snapshotOwner()throws IOException {return owner().controller().snapshot();}
    private static Active owner()throws IOException {Active a=active;if(a==null)throw new IOException("ARENA_OWNER_NOT_INSTALLED");if(!a.server().isSameThread())throw new IOException("SERVER_THREAD_REQUIRED");a.gate().requireAuthorized(a.config(),a.server(),a.grant());return a;}
    public static KneekuraDebugArenaController.Result submitOwner(KneekuraDebugArenaController.Command command,long tick)throws IOException {return owner().controller().submit(command,tick);}
    public static KneekuraDebugArenaController.Result resetOwner(KneekuraDebugArenaController.Command command,long tick)throws IOException {return owner().controller().reset(command,tick);}
    public static CaptureReservation reserveCapturesOwner(KneekuraDebugArenaController.Snapshot expected,String requestHash,int generation,int count)throws IOException {
        Active a=owner();a.controller().validateLeaseAndRevision(expected);
        if(!a.grant().requestHash().equals(requestHash)||a.grant().generation()!=generation||count<1||count>16||capturesReserved+count>a.grant().maxCaptures())throw new IOException("CAPTURE_AUTHORITY_OR_BUDGET_MISMATCH");
        var reservation=new CaptureReservation(UUID.randomUUID().toString(),requestHash,generation,a.grant().leaseId(),count);
        capturesReserved+=count;CAPTURE_RESERVATIONS.put(reservation.token(),reservation);return reservation;
    }
    public static void requireCaptureLeaseRemainingOwner(KneekuraDebugArenaController.Snapshot expected,long minRemainingMs)throws IOException {owner().controller().requireLeaseRemaining(expected,minRemainingMs);}
    static KneekuraDebugArenaController.Lease presentationLeaseOwner(KneekuraDebugArenaController.Snapshot expected)throws IOException {
        Active a=owner();a.controller().validateLeaseAndRevision(expected);return a.lease();
    }
    public static void validateCaptureOwner(CaptureReservation reservation,KneekuraDebugArenaController.Snapshot expected)throws IOException {
        Active a=owner();a.controller().validateLeaseAndRevision(expected);
        if(!reservation.equals(CAPTURE_RESERVATIONS.get(reservation.token()))||!reservation.leaseId().equals(a.grant().leaseId()))throw new IOException("CAPTURE_RESERVATION_MISMATCH");
    }
    public static void uninstallOwner()throws IOException {
        Active a=active;if(a==null)return;if(!a.server().isSameThread())throw new IOException("SERVER_THREAD_REQUIRED");try{a.controller().revoke();}finally{active=null;KneekuraDebugTankPresentation.clear();CAPTURE_RESERVATIONS.clear();capturesReserved=0;}
    }
    public static void onServerTick(KneekuraDebugEnv.Config config,MinecraftServer server,long tick)throws IOException {
        Active a=active;if(a==null)return;
        if(server!=a.server()||config==null||!a.config().identityKey().equals(config.identityKey())||!a.config().handshakeNonce().equals(config.handshakeNonce()))throw new IOException("ARENA_CONTEXT_CHANGED");
        a.controller().onTick(tick);
    }
}
