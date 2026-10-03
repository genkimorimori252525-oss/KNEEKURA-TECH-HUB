package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.JsonObject;
import java.util.*;

/** Bounded volatile display cache of flushed canonical SERVER samples, not a motion database. */
final class KneekuraDebugMotionTraceCache {
 static final int MAX_SAMPLES=128;
 record Context(String session,String run,String snapshot,int process,long arena,long revision,UUID uuid) {
  Context {
   for(String value:List.of(session,run,snapshot))if(value.isEmpty()||value.length()>512)throw new IllegalArgumentException("INVALID_MOTION_CONTEXT");
   if(process<1||arena<0||revision<1||uuid==null)throw new IllegalArgumentException("INVALID_MOTION_CONTEXT");
  }
 }
 record Sample(long tick,double x,double y,double z,String sourceId,String dimension,String traceClass,String breakBefore,String breakSource) { }
 record Segment(int from,int to,double distance) { }
 record Gap(long afterTick,long beforeTick,String kind,String sourceId) { }
 record Snapshot(Context context,List<Sample> samples,List<Segment> segments,List<Gap> gaps,long evictedSamples,long rejectedSamples) { }
 private Context context;
 private final ArrayList<Sample> samples=new ArrayList<>();
 private long evicted,rejected;
 private String pendingGap,pendingSource;
 private String lastWriter;
 private long lastSequence=Long.MIN_VALUE;
 synchronized void select(Context next) {
  if(Objects.equals(context,next))return;
  clear();context=next;
 }
 synchronized void clear(){context=null;samples.clear();evicted=0;rejected=0;pendingGap=null;pendingSource=null;lastWriter=null;lastSequence=Long.MIN_VALUE;}
 synchronized boolean selected(){return context!=null;}
 private static long exactLong(JsonObject value,String key){return value.get(key).getAsBigDecimal().longValueExact();}
 synchronized void acceptFlushed(JsonObject row) {
  if(context==null)return;
  try {
   String lane=row.get("lane").getAsString();
   if(!"observation".equals(row.get("kind").getAsString())||!Set.of("SERVER_ENTITY_STATE","SERVER_TARGET_TRACKED","AI_DECISION").contains(lane)||
     !"SERVER".equals(row.getAsJsonObject("source").get("side").getAsString())||
     !"ENTITY_UUID".equals(row.getAsJsonObject("scope").get("kind").getAsString())||
     !context.uuid().toString().equals(row.getAsJsonObject("scope").get("entityUuid").getAsString())||
     !context.session().equals(row.get("debugSessionId").getAsString())||!context.run().equals(row.get("runId").getAsString())||
     !context.snapshot().equals(row.get("runSnapshotId").getAsString())||context.process()!=exactLong(row,"processEpoch")||
     context.arena()!=exactLong(row,"arenaEpoch")||!"OBSERVED".equals(row.get("epistemicStatus").getAsString())||
     !row.getAsJsonObject("completeness").get("complete").getAsBoolean())return;
   var payload=row.getAsJsonObject("payload");if(context.revision()!=exactLong(payload,"targetRevision"))return;
   String id=row.get("observationId").getAsString();if(id.isEmpty()||id.length()>512)throw new IllegalArgumentException("INVALID_SOURCE_ID");
   long tick=exactLong(row,"gameTime");if(tick<0||tick>9007199254740991L)throw new IllegalArgumentException("INVALID_TICK");
   if(lane.equals("AI_DECISION")){
    if(successfulTeleport(payload)&&!samples.isEmpty()&&pendingGap==null){
     long previousTick=samples.get(samples.size()-1).tick();
     boolean after=tick>previousTick;
     if(tick==previousTick&&lastWriter!=null&&row.has("writerId")&&lastWriter.equals(row.get("writerId").getAsString())&&row.has("writerSeq"))
      after=exactLong(row,"writerSeq")>lastSequence&&lastSequence!=Long.MIN_VALUE;
     if(after){pendingGap="EXPLICIT_TELEPORT";pendingSource=id;}
    }
    return;
   }
   if(lane.equals("SERVER_TARGET_TRACKED")){
    if(payload.has("tracked")&&payload.get("tracked").isJsonPrimitive()&&payload.getAsJsonPrimitive("tracked").isBoolean()&&!payload.get("tracked").getAsBoolean()){
     pendingGap="MISSING_SELECTED_ENTITY";pendingSource=id;
    }
    return;
   }
   if(samples.stream().anyMatch(s->s.sourceId().equals(id)))return;
   if(!samples.isEmpty()&&tick<=samples.get(samples.size()-1).tick()){
    samples.clear();pendingGap="NONMONOTONIC_OR_DUPLICATE_TICK";pendingSource=id;rejected++;return;
   }
   String type=payload.get("motionTraceClass").getAsString();
   if(!Set.of("MOB_ACTUAL","PROJECTILE_ACTUAL").contains(type)){pendingGap="UNSUPPORTED_TRACE_CLASS";pendingSource=id;return;}
   if((payload.has("alive")&&!payload.get("alive").getAsBoolean())||(payload.has("removed")&&payload.get("removed").getAsBoolean())||
     !payload.has("x")||!payload.has("y")||!payload.has("z")){
    pendingGap="MISSING_RETAINED_POSITION";pendingSource=id;return;
   }
   double x=payload.get("x").getAsDouble(),y=payload.get("y").getAsDouble(),z=payload.get("z").getAsDouble();
   if(!Double.isFinite(x)||!Double.isFinite(y)||!Double.isFinite(z))throw new IllegalArgumentException("NONFINITE_POSITION");
   if(Math.abs(x)>30000000||Math.abs(y)>30000000||Math.abs(z)>30000000)throw new IllegalArgumentException("POSITION_OUTSIDE_DISPLAY_BOUNDS");
   String dimension=payload.get("dimension").getAsString();if(dimension.isEmpty()||dimension.length()>256)throw new IllegalArgumentException("INVALID_DIMENSION");
   samples.add(new Sample(tick,x,y,z,id,dimension,type,pendingGap,pendingSource));pendingGap=null;pendingSource=null;
   lastWriter=row.has("writerId")&&row.get("writerId").isJsonPrimitive()&&row.getAsJsonPrimitive("writerId").isString()&&!row.get("writerId").getAsString().isEmpty()?row.get("writerId").getAsString():null;
   lastSequence=Long.MIN_VALUE;
   if(lastWriter!=null&&row.has("writerSeq"))try{lastSequence=exactLong(row,"writerSeq");}catch(RuntimeException unknown){lastWriter=null;}
   if(samples.size()>MAX_SAMPLES){samples.remove(0);evicted++;}
  }catch(RuntimeException error){rejected++;pendingGap="INVALID_RETAINED_POSITION";pendingSource=null;}
 }
 private static boolean successfulTeleport(JsonObject payload){
  try{
   if(!"kneekura.original-decision-event/v1".equals(payload.get("schema").getAsString())||
     !"ORIGINAL_INVOCATION_RETURN_ONLY".equals(payload.get("semantics").getAsString())||
     !"CONTROL_TELEPORT_RETURN".equals(payload.get("kind").getAsString())||
     !"BUILD_AND_FIRST_BYTE_CHECK_EXCLUDES_FINAL_ENCODING_WRITER".equals(payload.get("observerCostScope").getAsString())||
     exactLong(payload,"observerCostNanos")<0||exactLong(payload,"eventIndex")<1||exactLong(payload,"eventIndex")>256)return false;
   String burst=payload.get("burstId").getAsString();if(burst.isEmpty()||burst.length()>512)return false;
   var data=payload.getAsJsonObject("data");
   if(!data.get("result").isJsonPrimitive()||!data.getAsJsonPrimitive("result").isBoolean()||!data.get("result").getAsBoolean()||
     !"BASE_RANDOM_TELEPORT_RETURN".equals(data.get("dispatchScope").getAsString())||!"NOT_EXPOSED".equals(data.get("reasonStatus").getAsString()))return false;
   for(String position:List.of("requestedPosition","returnedPosition"))for(String axis:List.of("x","y","z")){
    var value=data.getAsJsonObject(position).get(axis);
    if(!value.isJsonPrimitive()||!value.getAsJsonPrimitive().isNumber()||!Double.isFinite(value.getAsDouble()))return false;
   }
   return true;
  }catch(RuntimeException unknown){return false;}
 }
 synchronized Snapshot snapshot() {
  var segments=new ArrayList<Segment>();var gaps=new ArrayList<Gap>();
  for(int i=1;i<samples.size();i++){
   Sample a=samples.get(i-1),b=samples.get(i);double distance=Math.sqrt(Math.pow(b.x()-a.x(),2)+Math.pow(b.y()-a.y(),2)+Math.pow(b.z()-a.z(),2));
   String reason=b.breakBefore();
   if(reason==null&&(!a.dimension().equals(b.dimension())||!a.traceClass().equals(b.traceClass())))reason="IDENTITY_BOUNDARY";
   if(reason==null&&b.tick()-a.tick()>10)reason="SOURCE_GAP";
   if(reason==null&&distance>16)reason="DERIVED_DISTANCE_THRESHOLD_BREAK";
   if(reason==null)segments.add(new Segment(i-1,i,distance));
   else gaps.add(new Gap(a.tick(),b.tick(),reason,
     b.breakBefore()!=null?b.breakSource():reason.equals("DERIVED_DISTANCE_THRESHOLD_BREAK")?b.sourceId():null));
  }
  return new Snapshot(context,List.copyOf(samples),List.copyOf(segments),List.copyOf(gaps),evicted,rejected);
 }
}
