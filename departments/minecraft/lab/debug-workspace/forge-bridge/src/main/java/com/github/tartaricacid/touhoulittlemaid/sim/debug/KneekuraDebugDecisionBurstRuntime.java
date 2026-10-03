package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Mob;
import java.io.IOException;
import java.util.UUID;

/** Server-thread finite capture, bound to the actual selected object and all observation boundaries. */
final class KneekuraDebugDecisionBurstRuntime {
    private static final boolean LAUNCH_ENABLED="1".equals(System.getenv("KNEEKURA_DEBUG_DECISION_HOOKS"));
    private static KneekuraDebugDecisionHooks.Session session;
    private static long attemptedRevision;
    private static long currentTick;
    private static KneekuraDebugEnv.Config boundConfig;
    private static MinecraftServer boundServer;
    private static Mob boundMob;
    private static KneekuraDebugDecisionBurstRequest boundRequest;
    private KneekuraDebugDecisionBurstRuntime(){ }

    static void validateRequest(KneekuraDebugDecisionBurstRequest request,UUID target) {
        if(request!=null&&(!LAUNCH_ENABLED||target==null))throw new IllegalArgumentException("DECISION_HOOKS_NOT_ENABLED_OR_TARGET_MISSING");
    }
    static void selectionChanged() {
        close("SELECTION_CHANGED");attemptedRevision=0;
    }
    static void stop() {close("SERVER_STOPPED");attemptedRevision=0;}

    static void onTick(KneekuraDebugEnv.Config config,MinecraftServer server,long tick,UUID target,
                       long revision,KneekuraDebugDecisionBurstRequest request,KneekuraDebugDecisionSnapshot snapshot) {
        currentTick=tick;
        if(config==null||!config.enabled()||server==null||!server.isSameThread()) {close("SERVER_CONTEXT_UNAVAILABLE");return;}
        if(session!=null) {
            try {
                var context=config==boundConfig&&server==boundServer&&revision==attemptedRevision
                        &&boundMob.getUUID().equals(target)?context(config,server,boundMob,revision):null;
                session.budget().allows(context,tick);
                if(session.budget().reason()!=null)close(session.budget().reason());
            } catch(IOException|RuntimeException error){close("CONTEXT_UNAVAILABLE");}
        }
        if(!LAUNCH_ENABLED||request==null||target==null||revision==attemptedRevision)return;
        Mob mob=null;
        for(ServerLevel level:server.getAllLevels()) {
            if(level.getEntity(target) instanceof Mob found){mob=found;break;}
        }
        if(mob==null)return; // No enumeration or AI invocation; start only when this exact UUID resolves.
        attemptedRevision=revision;boundConfig=config;boundServer=server;boundMob=mob;boundRequest=request;
        try {
            var context=context(config,server,mob,revision);
            if(context==null)throw new IOException("TARGET_CONTEXT_UNAVAILABLE");
            var budget=new KneekuraDebugDecisionBurstBudget(context,tick,request.ticks(),request.maxEvents(),request.maxBytes());
            final Mob selected=mob;
            session=new KneekuraDebugDecisionHooks.Session(mob,mob.goalSelector,mob.targetSelector,snapshot,budget,
                    request.maxNodes(),request.channels(),()->{
                        try{return context(boundConfig,boundServer,selected,attemptedRevision);}
                        catch(IOException error){throw new IllegalStateException(error);}
                    },()->currentTick,(method,payload)->KneekuraDebugEvidenceWriter.recordDecisionObserved(
                            config,context.arenaEpoch(),currentTick,selected.level().getGameTime(),method,selected.getUUID(),payload));
            KneekuraDebugDecisionHooks.install(session);
        } catch(ReflectiveOperationException|IOException|RuntimeException error) {
            close("ARM_UNAVAILABLE");
            TouhouLittleMaid.LOGGER.error("[KNEEKURA-DEBUG] decision burst arm rejected revision={}",revision,error);
        }
    }
    static KneekuraDebugDecisionBurstBudget.Context context(KneekuraDebugEnv.Config config,
            MinecraftServer server,Mob mob,long revision)throws IOException {
        if(config==null||!config.enabled()||server==null||mob==null||mob.isRemoved()
                ||!(mob.level() instanceof ServerLevel level)||level.getServer()!=server
                ||level.getEntity(mob.getUUID())!=mob)return null;
        return new KneekuraDebugDecisionBurstBudget.Context(config.debugSessionId(),config.runId(),config.runSnapshotId(),
                config.processEpoch(),KneekuraDebugArenaRuntime.observationEpoch(config,server),revision,
                mob.getUUID().toString(),level.dimension().location().toString());
    }
    private static void close(String reason) {
        KneekuraDebugDecisionHooks.Session previous=session;session=null;
        KneekuraDebugDecisionHooks.clear(reason);
        if(previous==null)return;
        var budget=previous.budget();
        JsonObject summary=new JsonObject();summary.addProperty("schema","kneekura.decision-burst-summary/v1");
        summary.addProperty("targetRevision",budget.context().selectionRevision());
        summary.addProperty("burstId","burst:"+budget.context().selectionRevision()+":"+budget.startTick());
        summary.addProperty("startTick",budget.startTick());summary.addProperty("endTickExclusive",budget.endTickExclusive());
        summary.addProperty("capturedEvents",budget.events());summary.addProperty("capturedPayloadBytes",budget.bytes());
        summary.addProperty("stopReason",budget.reason());summary.addProperty("goalCoveragePartial",previous.goalCoveragePartial());
        summary.addProperty("byteScope","EVENT_PAYLOAD_ONLY_EXCLUDES_ENVELOPE_SUMMARY_WRITER_VIEWER");
        JsonArray channels=new JsonArray();boundRequest.channels().stream().sorted().forEach(channels::add);summary.add("channels",channels);
        try {
            // Terminal metadata stays on the captured context, never re-labelled as a new Arena or selection.
            KneekuraDebugEvidenceWriter.recordDecisionObserved(boundConfig,budget.context().arenaEpoch(),currentTick,
                    null,"KneekuraDebugDecisionBurstRuntime.close",UUID.fromString(budget.context().subjectUuid()),summary);
        } catch(IOException error){TouhouLittleMaid.LOGGER.error("[KNEEKURA-DEBUG] burst summary unavailable",error);}
        boundMob=null;boundServer=null;boundConfig=null;boundRequest=null;
    }
}
