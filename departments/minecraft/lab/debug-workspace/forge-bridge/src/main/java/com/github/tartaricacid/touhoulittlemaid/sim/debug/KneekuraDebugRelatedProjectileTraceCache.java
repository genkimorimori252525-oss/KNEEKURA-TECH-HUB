package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.google.gson.JsonObject;
import java.util.*;

/** Derived display only: accepted spawn identity plus flushed completed ticks, never entity lookups. */
final class KneekuraDebugRelatedProjectileTraceCache {
 static final int MAX_GROUPS=16,MAX_SAMPLES=128;
 record Trace(UUID uuid,String spawnSource,KneekuraDebugMotionTraceCache.Snapshot trace) { }
 record Snapshot(KneekuraDebugMotionTraceCache.Context context,List<Trace> traces,int retainedSamples,long evictedSamples,long rejectedSamples) { }
 private static final class Track {
  final UUID uuid;final String burst,source,projectileClass;final int spawnIndex;final long spawnTick;
  final ArrayList<KneekuraDebugMotionTraceCache.Sample> samples=new ArrayList<>();
  boolean ended;String pendingGap,pendingSource;
  Track(UUID uuid,String burst,String source,String projectileClass,int index,long tick){this.uuid=uuid;this.burst=burst;this.source=source;this.projectileClass=projectileClass;spawnIndex=index;spawnTick=tick;}
 }
 private record Retained(Track track,KneekuraDebugMotionTraceCache.Sample sample) { }
 private KneekuraDebugMotionTraceCache.Context context;
 private final LinkedHashMap<UUID,Track> tracks=new LinkedHashMap<>();
 private final ArrayDeque<Retained> retained=new ArrayDeque<>();
 private long evicted,rejected;
 synchronized void select(KneekuraDebugMotionTraceCache.Context next){if(Objects.equals(context,next))return;clear();context=next;}
 synchronized void clear(){context=null;tracks.clear();retained.clear();evicted=0;rejected=0;}
 private static long integer(JsonObject value,String key){var v=value.get(key);if(!v.isJsonPrimitive()||!v.getAsJsonPrimitive().isNumber())throw new IllegalArgumentException("INVALID_INTEGER");return v.getAsBigDecimal().longValueExact();}
 private static String text(JsonObject value,String key,int max){var v=value.get(key);if(!v.isJsonPrimitive()||!v.getAsJsonPrimitive().isString())throw new IllegalArgumentException("INVALID_TEXT");String s=v.getAsString();if(s.isEmpty()||s.length()>max)throw new IllegalArgumentException("INVALID_TEXT");return s;}
 private static boolean bool(JsonObject value,String key){var v=value.get(key);if(!v.isJsonPrimitive()||!v.getAsJsonPrimitive().isBoolean())throw new IllegalArgumentException("INVALID_BOOLEAN");return v.getAsBoolean();}
 private static double coordinate(JsonObject value,String key){var v=value.get(key);if(!v.isJsonPrimitive()||!v.getAsJsonPrimitive().isNumber())throw new IllegalArgumentException("INVALID_COORDINATE");double n=v.getAsDouble();if(!Double.isFinite(n)||Math.abs(n)>30000000)throw new IllegalArgumentException("INVALID_COORDINATE");return n;}
 synchronized void acceptFlushed(JsonObject row){
  if(context==null)return;
  Track track=null;String source=null;
  try{
   if(!"observation".equals(text(row,"kind",32))||!"AI_DECISION".equals(text(row,"lane",32))||
     !"SERVER".equals(text(row.getAsJsonObject("source"),"side",32))||
     !"ENTITY_UUID".equals(text(row.getAsJsonObject("scope"),"kind",32))||
     !context.uuid().toString().equals(text(row.getAsJsonObject("scope"),"entityUuid",64))||
     !context.session().equals(text(row,"debugSessionId",512))||!context.run().equals(text(row,"runId",512))||
     !context.snapshot().equals(text(row,"runSnapshotId",512))||context.process()!=integer(row,"processEpoch")||context.arena()!=integer(row,"arenaEpoch")||
     !"OBSERVED".equals(text(row,"epistemicStatus",32))||!bool(row.getAsJsonObject("completeness"),"complete"))return;
   var p=row.getAsJsonObject("payload");if(context.revision()!=integer(p,"targetRevision"))return;
   String kind=text(p,"kind",128);if(!Set.of("CONTROL_PROJECTILE_SPAWN_RETURN","CONTROL_PROJECTILE_TICK_RETURN").contains(kind))return;
   if(!"kneekura.original-decision-event/v1".equals(text(p,"schema",128))||!"ORIGINAL_INVOCATION_RETURN_ONLY".equals(text(p,"semantics",128))||
     !"BUILD_AND_FIRST_BYTE_CHECK_EXCLUDES_FINAL_ENCODING_WRITER".equals(text(p,"observerCostScope",128))||integer(p,"observerCostNanos")<0||p.toString().length()>32768)return;
   int event=Math.toIntExact(integer(p,"eventIndex"));if(event<1||event>256)return;
   String burst=text(p,"burstId",512);source=text(row,"observationId",512);long tick=integer(row,"gameTime");if(tick<0||tick>9007199254740991L)return;
   var d=p.getAsJsonObject("data");if(!context.uuid().toString().equals(text(d,"ownerUuid",64))||
     !"ACCEPTED_FRESH_SPAWN_SELECTED_CACHED_OWNER".equals(text(d,"relationshipScope",128)))return;
   String id=text(d,"projectileUuid",64);UUID uuid=UUID.fromString(id);if(!uuid.toString().equals(id))return;
   track=tracks.get(uuid);String projectileClass=text(d,"projectileClass",512);int spawn=Math.toIntExact(integer(d,"spawnEventIndex"));
   if(kind.equals("CONTROL_PROJECTILE_SPAWN_RETURN")){
    if(track!=null||tracks.size()>=MAX_GROUPS||spawn!=event||integer(d,"trackingLimit")!=16||
      !bool(d,"result")||!"SERVER_ADD_FRESH_ENTITY_RETURN".equals(text(d,"dispatchScope",128)))return;
    // Validate the original spawn receipt; its position never becomes a completed-tick sample.
    for(String key:List.of("position","velocity"))for(String axis:List.of("x","y","z"))coordinate(d.getAsJsonObject(key),axis);
    tracks.put(uuid,new Track(uuid,burst,source,projectileClass,spawn,tick));return;
   }
   if(track==null||track.ended||!track.burst.equals(burst)||track.spawnIndex!=spawn||!track.projectileClass.equals(projectileClass)||
     tick<track.spawnTick||event<=spawn||!"SERVER_NON_PASSENGER_ORIGINAL_TICK_AFTER".equals(text(d,"dispatchScope",128)))return;
   String observedSource=source;if(track.samples.stream().anyMatch(s->s.sourceId().equals(observedSource)))return;
   if(bool(d,"removed")){track.ended=true;return;}
   String dimension=text(d,"dimension",256);
   var position=d.getAsJsonObject("position");double x=coordinate(position,"x"),y=coordinate(position,"y"),z=coordinate(position,"z");
   for(String axis:List.of("x","y","z"))coordinate(d.getAsJsonObject("velocity"),axis);
   if(!track.samples.isEmpty()&&tick<=track.samples.get(track.samples.size()-1).tick()){
    Track invalid=track;retained.removeIf(r->r.track()==invalid);track.samples.clear();track.pendingGap="NONMONOTONIC_OR_DUPLICATE_TICK";track.pendingSource=source;rejected++;return;
   }
   var sample=new KneekuraDebugMotionTraceCache.Sample(tick,x,y,z,source,dimension,"PROJECTILE_ACTUAL",track.pendingGap,track.pendingSource);
   // Keep actual endpoints of a stationary run instead of letting repeated zero-length
   // ticks evict other projectiles' unexpired travelled paths. Raw evidence is untouched.
   if(track.samples.size()>=2){
    var previous=track.samples.get(track.samples.size()-1);var before=track.samples.get(track.samples.size()-2);
    if(previous.breakBefore()==null&&sample.breakBefore()==null&&previous.tick()-before.tick()<=10&&tick-previous.tick()<=10&&
      samePosition(before,previous)&&samePosition(previous,sample)){
     track.samples.remove(track.samples.size()-1);retained.remove(new Retained(track,previous));
    }
   }
   track.samples.add(sample);retained.addLast(new Retained(track,sample));track.pendingGap=null;track.pendingSource=null;
   if(retained.size()>MAX_SAMPLES){var oldest=retained.removeFirst();oldest.track().samples.remove(oldest.sample());evicted++;}
  }catch(RuntimeException invalid){rejected++;if(track!=null&&!track.ended){track.pendingGap="INVALID_RETAINED_POSITION";track.pendingSource=source;}}
 }
 private static boolean samePosition(KneekuraDebugMotionTraceCache.Sample a,KneekuraDebugMotionTraceCache.Sample b){
  return a.x()==b.x()&&a.y()==b.y()&&a.z()==b.z()&&a.dimension().equals(b.dimension())&&a.traceClass().equals(b.traceClass());
 }
 synchronized Snapshot snapshot(){
  var result=new ArrayList<Trace>();for(var track:tracks.values())result.add(new Trace(track.uuid,track.source,KneekuraDebugMotionTraceCache.derive(context,track.samples,0,0)));
  return new Snapshot(context,List.copyOf(result),retained.size(),evicted,rejected);
 }
}
