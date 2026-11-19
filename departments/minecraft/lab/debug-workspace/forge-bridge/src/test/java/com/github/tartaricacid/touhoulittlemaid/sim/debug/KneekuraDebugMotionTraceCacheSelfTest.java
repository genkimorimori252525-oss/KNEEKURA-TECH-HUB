package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.google.gson.*;
import java.util.UUID;
/** Pure retained-source cache; no Minecraft or fake API objects. */
public final class KneekuraDebugMotionTraceCacheSelfTest {
 private static final UUID UUID_VALUE=UUID.fromString("00000000-0000-0000-0000-000000000001");
 static KneekuraDebugMotionTraceCache.Context context(long revision){return new KneekuraDebugMotionTraceCache.Context("s","r","snap",1,0,revision,UUID_VALUE);}
 static JsonObject row(long tick,double x,String id){
  return JsonParser.parseString("{\"kind\":\"observation\",\"lane\":\"SERVER_ENTITY_STATE\",\"observationId\":\""+id+"\",\"debugSessionId\":\"s\",\"runId\":\"r\",\"runSnapshotId\":\"snap\",\"processEpoch\":1,\"arenaEpoch\":0,\"gameTime\":"+tick+",\"scope\":{\"kind\":\"ENTITY_UUID\",\"entityUuid\":\""+UUID_VALUE+"\"},\"source\":{\"side\":\"SERVER\"},\"epistemicStatus\":\"OBSERVED\",\"completeness\":{\"complete\":true},\"payload\":{\"targetRevision\":1,\"motionTraceClass\":\"MOB_ACTUAL\",\"dimension\":\"minecraft:overworld\",\"x\":"+x+",\"y\":64,\"z\":0,\"alive\":true}}").getAsJsonObject();
 }
 static void require(boolean v,String name){if(!v)throw new AssertionError(name);}
 public static void main(String[] args){
  var cache=new KneekuraDebugMotionTraceCache();cache.select(context(1));
  JsonObject a=row(100,0,"obs:1"),b=row(105,1,"obs:2");cache.acceptFlushed(a);cache.acceptFlushed(b);
  require(cache.snapshot().samples().size()==2&&cache.snapshot().segments().size()==1,"actual retained endpoints");
  require(a.getAsJsonObject("payload").get("x").getAsDouble()==0,"input unchanged");
  var wrong=row(110,2,"obs:wrong");wrong.getAsJsonObject("source").addProperty("side","CLIENT");cache.acceptFlushed(wrong);
  require(cache.snapshot().samples().size()==2,"foreign source ignored");
  var missing=row(110,2,"obs:missing");missing.getAsJsonObject("payload").remove("x");cache.acceptFlushed(missing);cache.acceptFlushed(row(115,2,"obs:3"));
  require(cache.snapshot().gaps().get(0).kind().equals("MISSING_RETAINED_POSITION"),"missing breaks trace");
  cache.acceptFlushed(row(120,100,"obs:4"));require(cache.snapshot().gaps().get(1).kind().equals("DERIVED_DISTANCE_THRESHOLD_BREAK"),"no fake teleport");
  cache.select(context(2));cache.acceptFlushed(a);require(cache.snapshot().samples().isEmpty(),"reselection clears and rejects old revision");
  cache.select(context(1));for(int i=0;i<140;i++)cache.acceptFlushed(row(i*5,i,"obs:"+i));
  require(cache.snapshot().samples().size()==128&&cache.snapshot().evictedSamples()==12,"bounded retained cache");
  cache.clear();require(cache.snapshot().samples().isEmpty(),"clear removes old display");
  cache.select(context(1));cache.acceptFlushed(row(100,0,"obs:a"));
  var absent=row(105,0,"obs:absent");absent.addProperty("lane","SERVER_TARGET_TRACKED");absent.getAsJsonObject("payload").addProperty("tracked",false);
  cache.acceptFlushed(absent);cache.acceptFlushed(row(110,1,"obs:b"));
  require(cache.snapshot().segments().isEmpty()&&cache.snapshot().gaps().get(0).kind().equals("MISSING_SELECTED_ENTITY"),"explicit absent target breaks a short gap");
  cache.clear();cache.select(context(1));var start=row(100,0,"obs:start");
  start.addProperty("writerId","server");start.addProperty("writerSeq",100);cache.acceptFlushed(start);
  var teleport=row(103,100,"obs:teleport");teleport.addProperty("lane","AI_DECISION");
  teleport.addProperty("writerId","server");teleport.addProperty("writerSeq",101);
  var payload=JsonParser.parseString("{\"schema\":\"kneekura.original-decision-event/v1\",\"semantics\":\"ORIGINAL_INVOCATION_RETURN_ONLY\",\"targetRevision\":1,\"burstId\":\"burst:1:100\",\"eventIndex\":1,\"kind\":\"CONTROL_TELEPORT_RETURN\",\"observerCostNanos\":10,\"observerCostScope\":\"BUILD_AND_FIRST_BYTE_CHECK_EXCLUDES_FINAL_ENCODING_WRITER\",\"data\":{\"result\":true,\"requestedPosition\":{\"x\":1,\"y\":64,\"z\":0},\"returnedPosition\":{\"x\":1,\"y\":64,\"z\":0},\"dispatchScope\":\"BASE_RANDOM_TELEPORT_RETURN\",\"reasonStatus\":\"NOT_EXPOSED\"}}").getAsJsonObject();
  teleport.add("payload",payload);cache.acceptFlushed(teleport);cache.acceptFlushed(row(105,1,"obs:end"));
  require(cache.snapshot().samples().size()==2&&cache.snapshot().segments().isEmpty(),"Original return is a break, never a position sample");
  require(cache.snapshot().gaps().get(0).kind().equals("EXPLICIT_TELEPORT")&&cache.snapshot().gaps().get(0).sourceId().equals("obs:teleport"),"Typed native gap cites original source");
  for(String mode:new String[]{"FALSE","MALFORMED","STALE_TICK","WRONG_REVISION","UNKNOWN_SAME_TICK_ORDER","EMPTY_SAME_TICK_ORDER"}){
   cache.clear();cache.select(context(1));var initial=start.deepCopy();
   if(mode.equals("EMPTY_SAME_TICK_ORDER"))initial.addProperty("writerId","");
   cache.acceptFlushed(initial);var event=teleport.deepCopy();
   if(mode.equals("FALSE"))event.getAsJsonObject("payload").getAsJsonObject("data").addProperty("result",false);
   if(mode.equals("MALFORMED"))event.getAsJsonObject("payload").getAsJsonObject("data").addProperty("result","true");
   if(mode.equals("STALE_TICK"))event.addProperty("gameTime",99);
   if(mode.equals("WRONG_REVISION"))event.getAsJsonObject("payload").addProperty("targetRevision",2);
   if(mode.equals("UNKNOWN_SAME_TICK_ORDER")){event.addProperty("gameTime",100);event.remove("writerId");}
   if(mode.equals("EMPTY_SAME_TICK_ORDER")){event.addProperty("gameTime",100);event.addProperty("writerId","");}
   cache.acceptFlushed(event);cache.acceptFlushed(row(105,1,"obs:end"));
   require(cache.snapshot().segments().size()==1,"No successful typed break for "+mode);
  }
  System.out.println("Retained native Motion cache boundaries/source/gaps/128-sample cap passed");
 }
}
