package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.google.gson.*;
import java.util.*;

/** Pure flushed-canonical display contracts; no Minecraft API or live entity lookup. */
public final class KneekuraDebugRelatedProjectileTraceSelfTest {
 private static final UUID SHOOTER=UUID.fromString("00000000-0000-0000-0000-000000000001");
 private static UUID shot(int n){return new UUID(1,n);}
 private static KneekuraDebugMotionTraceCache.Context context(long revision){return new KneekuraDebugMotionTraceCache.Context("s","r","snap",1,0,revision,SHOOTER);}
 static JsonObject row(int n,boolean spawn,long tick,int index,double x){
  var row=KneekuraDebugMotionTraceCacheSelfTest.row(tick,x,"obs:"+n+":"+index);row.addProperty("lane","AI_DECISION");
  var payload=new JsonObject();payload.addProperty("schema","kneekura.original-decision-event/v1");payload.addProperty("semantics","ORIGINAL_INVOCATION_RETURN_ONLY");
  payload.addProperty("targetRevision",1);payload.addProperty("burstId","burst:1:100");payload.addProperty("eventIndex",index);
  payload.addProperty("observerCostNanos",1);payload.addProperty("observerCostScope","BUILD_AND_FIRST_BYTE_CHECK_EXCLUDES_FINAL_ENCODING_WRITER");
  payload.addProperty("kind",spawn?"CONTROL_PROJECTILE_SPAWN_RETURN":"CONTROL_PROJECTILE_TICK_RETURN");
  var data=new JsonObject();data.addProperty("ownerUuid",SHOOTER.toString());data.addProperty("projectileUuid",shot(n).toString());
  data.addProperty("projectileClass","net.minecraft.world.entity.projectile.Arrow");data.addProperty("spawnEventIndex",n);
  data.addProperty("relationshipScope","ACCEPTED_FRESH_SPAWN_SELECTED_CACHED_OWNER");
  var pos=new JsonObject();pos.addProperty("x",x);pos.addProperty("y",64);pos.addProperty("z",0);data.add("position",pos);data.add("velocity",pos.deepCopy());
  if(spawn){data.addProperty("result",true);data.addProperty("trackingLimit",16);data.addProperty("dispatchScope","SERVER_ADD_FRESH_ENTITY_RETURN");}
  else{data.addProperty("removed",false);data.addProperty("dimension","minecraft:overworld");data.addProperty("dispatchScope","SERVER_NON_PASSENGER_ORIGINAL_TICK_AFTER");}
  payload.add("data",data);row.add("payload",payload);return row;
 }
 private static void require(boolean value,String label){if(!value)throw new AssertionError(label);}
 public static void main(String[] args){
  var cache=new KneekuraDebugRelatedProjectileTraceCache();cache.select(context(1));
  cache.acceptFlushed(row(1,false,100,2,0));require(cache.snapshot().traces().isEmpty(),"late arm does not invent accepted spawn");
  for(int n=1;n<=2;n++)cache.acceptFlushed(row(n,true,100,n,0));
  require(cache.snapshot().traces().stream().allMatch(t->t.trace().samples().isEmpty()),"spawn position is not a completed tick sample");
  var first=row(1,false,101,3,0);String original=first.toString();cache.acceptFlushed(first);cache.acceptFlushed(first);
  cache.acceptFlushed(row(2,false,101,4,0));cache.acceptFlushed(row(1,false,102,5,1));cache.acceptFlushed(row(2,false,102,6,2));
  var traces=cache.snapshot().traces();require(traces.size()==2&&cache.snapshot().retainedSamples()==4,"separate simultaneous UUID groups, duplicate ID suppressed");
  require(original.equals(first.toString()),"canonical row unchanged");
  var a=traces.get(0);var b=traces.get(1);
  var la=KneekuraDebugMotionOverlayGeometry.linesForIdentity(a.trace(),a.uuid().toString(),"minecraft:overworld",102,0,64,0,true);
  var lb=KneekuraDebugMotionOverlayGeometry.linesForIdentity(b.trace(),b.uuid().toString(),"minecraft:overworld",102,0,64,0,true);
  require(!la.get(0).style().equals(lb.get(0).style()),"actual projectile identity supplies its initial hue");
  require(la.stream().flatMap(l->l.sourceIds().stream()).noneMatch(id->id.startsWith("obs:2:")),"groups never cross-connect source IDs");
  require(KneekuraDebugMotionOverlayGeometry.linesForIdentity(a.trace(),a.uuid().toString(),"minecraft:overworld",202,0,64,0,true).isEmpty(),"actual ages expire without forward fill");
  require(KneekuraDebugMotionOverlayGeometry.linesForIdentity(a.trace(),a.uuid().toString(),"minecraft:overworld",102,0,64,0,false).isEmpty(),"raw capture suppresses related geometry");
  var selected=KneekuraDebugMotionTraceCache.derive(context(1),List.of(),0,0);
  var combined=KneekuraDebugMotionOverlayGeometry.combinedLines(selected,cache.snapshot(),"minecraft:overworld",102,0,64,0,true);
  require(combined.size()==la.size()+lb.size(),"same selected-shooter context combines both real groups");
  require(KneekuraDebugMotionOverlayGeometry.combinedLines(selected,cache.snapshot(),"minecraft:overworld",102,0,64,0,false).isEmpty(),"actual combined raw-capture suppression");
  require(KneekuraDebugMotionOverlayGeometry.combinedLines(KneekuraDebugMotionTraceCache.derive(context(2),List.of(),0,0),cache.snapshot(),"minecraft:overworld",102,0,64,0,true).isEmpty(),"race between separate snapshots never mixes revisions");
  for(String boundary:new String[]{"source","revision","owner","burst","spawn-index","class"}) {
   var bad=row(1,false,103,7,3);var d=bad.getAsJsonObject("payload").getAsJsonObject("data");
   switch(boundary){case "source"->bad.getAsJsonObject("source").addProperty("side","CLIENT");case "revision"->bad.getAsJsonObject("payload").addProperty("targetRevision",2);
    case "owner"->d.addProperty("ownerUuid",shot(9).toString());case "burst"->bad.getAsJsonObject("payload").addProperty("burstId","burst:1:200");case "spawn-index"->d.addProperty("spawnEventIndex",2);case "class"->d.addProperty("projectileClass","example.OtherProjectile");}
   cache.acceptFlushed(bad);require(cache.snapshot().retainedSamples()==4,"foreign context/relationship ignored: "+boundary);
  }
  var removed=row(1,false,103,8,3);removed.getAsJsonObject("payload").getAsJsonObject("data").addProperty("removed",true);cache.acceptFlushed(removed);
  cache.acceptFlushed(row(1,false,104,9,4));require(cache.snapshot().retainedSamples()==4,"removed reference never resumes or adds invented points");
  cache.acceptFlushed(row(2,false,120,10,4));require(cache.snapshot().traces().get(1).trace().gaps().get(0).kind().equals("SOURCE_GAP"),"missing actual ticks break connection");
  cache.select(context(2));cache.acceptFlushed(first);require(cache.snapshot().traces().isEmpty(),"selection revision clears related groups");
  cache.select(context(1));for(int n=1;n<=17;n++)cache.acceptFlushed(row(n,true,100,n,0));require(cache.snapshot().traces().size()==16,"finite accepted UUID groups");
  for(int t=101;t<=110;t++)for(int n=1;n<=16;n++)cache.acceptFlushed(row(n,false,t,18+(t-101)*16+n,n));
  require(cache.snapshot().retainedSamples()==128&&cache.snapshot().evictedSamples()==32,"global related position budget, not128 per projectile");
  var invalid=row(16,false,111,195,Double.NaN);cache.acceptFlushed(invalid);cache.acceptFlushed(row(16,false,112,196,16));
  require(cache.snapshot().traces().get(15).trace().gaps().stream().anyMatch(g->g.kind().equals("INVALID_RETAINED_POSITION")),"malformed actual position prevents a later false connection");
  cache.clear();require(cache.snapshot().traces().isEmpty(),"clear releases all related display state");
  System.out.println("Related native projectile display: exact accepted spawn/context/UUID, tick-only positions, no replay/forward-fill/cross-connect,16 groups/global128 positions, age/capture/gap boundaries passed");
 }
}
