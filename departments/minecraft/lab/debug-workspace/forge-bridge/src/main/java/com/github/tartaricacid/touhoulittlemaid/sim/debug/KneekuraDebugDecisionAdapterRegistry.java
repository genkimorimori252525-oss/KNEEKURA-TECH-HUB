package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.entity.Mob;
import java.nio.charset.StandardCharsets;
import java.util.List;

/** SDK v1 explicit producer registration. Source data cannot register code or owner authority. */
final class KneekuraDebugDecisionAdapterRegistry {
    private static final List<KneekuraDebugDecisionAdapter> ADAPTERS=List.of(new KneekuraDebugTwilightForestAdapter());
    private KneekuraDebugDecisionAdapterRegistry(){ }
    static void captureSelected(KneekuraDebugEnv.Config config,MinecraftServer server,Mob mob,long revision,long tick) {
        if(config==null||!config.enabled()||server==null||!server.isSameThread()||mob==null)return;
        for(var adapter:ADAPTERS) {
            if(!adapter.supports(mob))continue;
            try {
                var before=KneekuraDebugDecisionBurstRuntime.context(config,server,mob,revision);
                if(before==null)return;
                long started=System.nanoTime();
                var snapshot=adapter.captureSnapshot(mob,before,new KneekuraDebugDecisionAdapter.Limits(64,24*1024));
                if(!before.equals(KneekuraDebugDecisionBurstRuntime.context(config,server,mob,revision)))return;
                snapshot.addProperty("schema","kneekura.mod-decision-snapshot/v1");
                snapshot.addProperty("semantics","SOURCE_SPECIFIC_CACHED_SNAPSHOT_ONLY");
                snapshot.addProperty("targetRevision",revision);snapshot.addProperty("sampleTick",mob.level().getGameTime());
                snapshot.addProperty("entityClass",mob.getClass().getName());
                snapshot.addProperty("observerCostNanos",Math.max(0L,System.nanoTime()-started));
                snapshot.addProperty("observerCostScope","CACHED_CAPTURE_AND_ONCE_SOURCE_PROOF_EXCLUDES_ENCODING_WRITER_VIEWER");
                if(snapshot.toString().getBytes(StandardCharsets.UTF_8).length>32768)return;
                KneekuraDebugEvidenceWriter.recordDecisionObserved(config,before.arenaEpoch(),tick,mob.level().getGameTime(),
                        "KneekuraDebugDecisionAdapterRegistry.cached_source_specific_snapshot",mob.getUUID(),snapshot);
            }catch(Exception|LinkageError unavailable) {
                TouhouLittleMaid.LOGGER.error("[KNEEKURA-DEBUG] source-specific snapshot unavailable uuid={}",mob.getUUID(),unavailable);
            }
            return;
        }
    }
}
