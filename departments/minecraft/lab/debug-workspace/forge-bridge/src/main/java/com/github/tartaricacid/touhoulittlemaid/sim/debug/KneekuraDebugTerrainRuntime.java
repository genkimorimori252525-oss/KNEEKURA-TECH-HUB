package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import com.google.gson.JsonObject;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.Mob;
import java.io.IOException;
import java.util.Map;
import java.util.UUID;

/** One bounded query per explicit selection revision, using the same exact observation context. */
final class KneekuraDebugTerrainRuntime {
    private static long attemptedRevision;
    private KneekuraDebugTerrainRuntime(){ }
    static void clear(){attemptedRevision=0;}
    static void onTick(KneekuraDebugEnv.Config config,MinecraftServer server,long tick,UUID target,
            long revision,KneekuraDebugTerrainQueryRequest request) {
        if(request==null||target==null||revision==attemptedRevision||config==null||!config.enabled()
                ||server==null||!server.isSameThread())return;
        Mob mob=null;
        for(ServerLevel level:server.getAllLevels())if(level.getEntity(target) instanceof Mob found){mob=found;break;}
        if(mob==null)return;
        attemptedRevision=revision;
        try {
            var before=KneekuraDebugDecisionBurstRuntime.context(config,server,mob,revision);
            if(before==null)throw new IOException("TERRAIN_CONTEXT_UNAVAILABLE");
            long started=System.nanoTime();
            BlockPos center=(BlockPos)KneekuraDebugDecisionSnapshot.read(Entity.class,"blockPosition",mob);
            Map<?,?> overrides=(Map<?,?>)KneekuraDebugDecisionSnapshot.read(Mob.class,"pathfindingMalus",mob);
            var source=new KneekuraDebugLoadedGroundSource((ServerLevel)mob.level(),center,request.radius());
            JsonObject data=KneekuraDebugTerrainField.capture(center,request.radius(),request.maxCells(),request.maxMillis()*1000000L,
                    System::nanoTime,source,overrides);
            var after=KneekuraDebugDecisionBurstRuntime.context(config,server,mob,revision);
            if(!before.equals(after))throw new IOException("TERRAIN_CONTEXT_CHANGED");
            data.addProperty("dimension",before.dimension());
            data.addProperty("centerX",center.getX());data.addProperty("centerY",center.getY());data.addProperty("centerZ",center.getZ());
            data.addProperty("chunkAccessScope","LOADED_NONBLOCKING_MAY_WARM_LOOKUP_CACHE_AND_PROFILER");
            JsonObject root=new JsonObject();root.addProperty("schema","kneekura.terrain-ground-query/v1");
            root.addProperty("semantics","OBSERVER_QUERIED_GROUND_NOT_PATHFINDER_EVALUATION");
            root.addProperty("targetRevision",revision);root.addProperty("sampleTick",mob.level().getGameTime());root.add("data",data);
            root.addProperty("observerCostNanos",Math.max(0L,System.nanoTime()-started));
            root.addProperty("observerCostScope","GROUND_CAPTURE_ONLY_EXCLUDES_ENCODING_WRITER_VIEWER");
            KneekuraDebugEvidenceWriter.recordDecisionObserved(config,before.arenaEpoch(),tick,mob.level().getGameTime(),
                    "WalkNodeEvaluator.getBlockPathTypeStatic.OBSERVER_QUERY",target,root);
        }catch(ReflectiveOperationException|IOException|RuntimeException error) {
            TouhouLittleMaid.LOGGER.error("[KNEEKURA-DEBUG] terrain query unavailable revision={}",revision,error);
        }
    }
}
