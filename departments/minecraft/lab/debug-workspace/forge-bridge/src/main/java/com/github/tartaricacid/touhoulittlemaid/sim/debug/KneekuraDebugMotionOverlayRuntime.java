package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.google.gson.JsonParser;
import java.util.*;

/** Cross-thread display handoff after the existing raw writer has actually flushed a row. */
final class KneekuraDebugMotionOverlayRuntime {
 private static final boolean ARMED="1".equals(System.getenv("KNEEKURA_DEBUG_MOTION_OVERLAY"));
 private static final KneekuraDebugMotionTraceCache CACHE=new KneekuraDebugMotionTraceCache();
 private static volatile boolean disabled;
 private static volatile KneekuraDebugEnv.Config config;
 static boolean armed(){return ARMED&&!disabled;}
 static synchronized void select(KneekuraDebugEnv.Config value,long arena,long revision,UUID uuid){
  if(!armed()||value==null||!value.enabled()||uuid==null||revision<1){clear();return;}
  config=value;CACHE.select(new KneekuraDebugMotionTraceCache.Context(value.debugSessionId(),value.runId(),value.runSnapshotId(),value.processEpoch(),arena,revision,uuid));
 }
 static void onFlushed(String line){
  if(!armed()||!CACHE.selected()||(!line.contains("\"lane\":\"SERVER_ENTITY_STATE\"")&&!line.contains("\"lane\":\"SERVER_TARGET_TRACKED\""))||!line.contains("\"side\":\"SERVER\""))return;
  try{CACHE.acceptFlushed(JsonParser.parseString(line).getAsJsonObject());}
  catch(RuntimeException error){CACHE.clear();}
 }
 static KneekuraDebugMotionTraceCache.Snapshot snapshot(){return CACHE.snapshot();}
 static KneekuraDebugEnv.Config config(){return config;}
 static synchronized void clear(){CACHE.clear();config=null;}
 static void disable(){disabled=true;clear();}
}
