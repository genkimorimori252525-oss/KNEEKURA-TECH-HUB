package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.google.gson.*;
/** Pure native fixture compared to shared SampledMotionTrace v1 by the portable source suite. */
public final class KneekuraDebugMotionTraceInterop {
 public static void main(String[] args) {
  var cache=new KneekuraDebugMotionTraceCache();cache.select(KneekuraDebugMotionTraceCacheSelfTest.context(1));
  for(long tick:new long[]{100,105,125,130,135,140,145}) {
   double x=tick<130?(tick-100)/5.0:tick<140?100:101;
   var row=KneekuraDebugMotionTraceCacheSelfTest.row(tick,x,"obs:"+tick);
   if(tick==135)row.getAsJsonObject("payload").remove("x");
   if(tick==145)row.getAsJsonObject("payload").addProperty("dimension","minecraft:the_nether");
   cache.acceptFlushed(row);
  }
  var snapshot=cache.snapshot();var result=new JsonObject();var samples=new JsonArray();var segments=new JsonArray();var gaps=new JsonArray();
  for(var s:snapshot.samples()){
   var item=new JsonObject();item.addProperty("tick",s.tick());item.addProperty("x",s.x());item.addProperty("y",s.y());item.addProperty("z",s.z());
   item.addProperty("dimension_id",s.dimension());item.addProperty("source_observation_id",s.sourceId());item.addProperty("source_kind","SERVER_ENTITY_STATE");samples.add(item);
  }
  for(var s:snapshot.segments()){
   var item=new JsonObject();item.addProperty("from_tick",snapshot.samples().get(s.from()).tick());item.addProperty("to_tick",snapshot.samples().get(s.to()).tick());
   item.addProperty("distance",s.distance());segments.add(item);
  }
  for(var g:snapshot.gaps()){
   var item=new JsonObject();item.addProperty("after_tick",g.afterTick());item.addProperty("before_tick",g.beforeTick());item.addProperty("kind",g.kind());
   item.add("source_observation_id",g.sourceId()==null?JsonNull.INSTANCE:new JsonPrimitive(g.sourceId()));gaps.add(item);
  }
  result.add("observations",samples);result.add("segments",segments);result.add("gaps",gaps);System.out.println(result);
 }
}
