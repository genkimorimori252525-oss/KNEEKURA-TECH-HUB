package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.google.gson.JsonParser;
import java.util.*;

/** Cross-thread display handoff after the existing raw writer has actually flushed a row. */
final class KneekuraDebugMotionOverlayRuntime {
 private static final boolean ARMED="1".equals(System.getenv("KNEEKURA_DEBUG_MOTION_OVERLAY"));
 private static final KneekuraDebugMotionTraceCache CACHE=new KneekuraDebugMotionTraceCache();
 private static final KneekuraDebugRelatedProjectileTraceCache RELATED=new KneekuraDebugRelatedProjectileTraceCache();
 private static volatile boolean disabled;
 private static volatile KneekuraDebugEnv.Config config;
 static boolean armed(){return ARMED&&!disabled;}
 static synchronized void select(KneekuraDebugEnv.Config value,long arena,long revision,UUID uuid){
  if(!armed()||value==null||!value.enabled()||uuid==null||revision<1){clear();return;}
  config=value;var context=new KneekuraDebugMotionTraceCache.Context(value.debugSessionId(),value.runId(),value.runSnapshotId(),value.processEpoch(),arena,revision,uuid);CACHE.select(context);RELATED.select(context);
 }
 static void onFlushed(String line){
  if(!armed()||!CACHE.selected()||(!line.contains("\"lane\":\"SERVER_ENTITY_STATE\"")&&!line.contains("\"lane\":\"SERVER_TARGET_TRACKED\"")&&
    !(line.contains("\"lane\":\"AI_DECISION\"")&&(line.contains("\"kind\":\"CONTROL_TELEPORT_RETURN\"")||line.contains("\"kind\":\"CONTROL_PROJECTILE_SPAWN_RETURN\"")||line.contains("\"kind\":\"CONTROL_PROJECTILE_TICK_RETURN\""))))||!line.contains("\"side\":\"SERVER\""))return;
  try{var row=JsonParser.parseString(line).getAsJsonObject();CACHE.acceptFlushed(row);RELATED.acceptFlushed(row);}
  catch(RuntimeException error){CACHE.clear();RELATED.clear();}
 }
 static KneekuraDebugMotionTraceCache.Snapshot snapshot(){return CACHE.snapshot();}
 static KneekuraDebugRelatedProjectileTraceCache.Snapshot relatedSnapshot(){return RELATED.snapshot();}
 static KneekuraDebugEnv.Config config(){return config;}
 static synchronized void clear(){CACHE.clear();RELATED.clear();config=null;}
 static void disable(){disabled=true;clear();}
}
