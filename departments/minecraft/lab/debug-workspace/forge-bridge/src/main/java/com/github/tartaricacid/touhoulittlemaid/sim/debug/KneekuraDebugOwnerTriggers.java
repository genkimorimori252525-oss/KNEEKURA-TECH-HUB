package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.*;
import java.io.IOException;
import java.util.*;

/** Pure selected-event state and typed trigger contract. No scheduler, world scan or mutation. */
final class KneekuraDebugOwnerTriggers {
 private KneekuraDebugOwnerTriggers(){}
 static JsonObject validateConfig(JsonObject c,KneekuraDebugArenaOwnerGrant grant)throws IOException {
  KneekuraDebugActionJournal.keys(c,"enabled","triggerKinds","offsetsMs","toleranceMs","cooldownMs","maxWindows","captureBudget","timeoutMs","captureIndices");
  JsonElement enabled=c.get("enabled");if(enabled==null||!enabled.isJsonPrimitive()||!enabled.getAsJsonPrimitive().isBoolean()||!enabled.getAsBoolean())throw new IOException("TRIGGER_OPT_IN_REQUIRED");
  JsonArray kinds=KneekuraDebugOwnerInputs.a(c,"triggerKinds",1,1);if(!kinds.get(0).isJsonPrimitive()||!kinds.get(0).getAsJsonPrimitive().isString()||!kinds.get(0).getAsString().equals("ARENA_EXIT"))throw new IOException("UNIMPLEMENTED_TRIGGER_SOURCE");
  long previous=Long.MIN_VALUE,last=0;for(JsonElement e:KneekuraDebugOwnerInputs.a(c,"offsetsMs",1,21)){long n=number(e);if(n< -10000||n>10000||previous!=Long.MIN_VALUE&&n-previous<250)throw new IOException("TRIGGER_SAMPLE_RATE");previous=n;last=Math.max(last,n);}
  range(c,"toleranceMs",0,250);range(c,"cooldownMs",1000,60000);range(c,"maxWindows",1,8);range(c,"captureBudget",1,4);range(c,"timeoutMs",Math.max(1,last),Math.min(20000,grant.timeBudgetMs()));
  Set<Long> seen=new HashSet<>();JsonArray slots=KneekuraDebugOwnerInputs.a(c,"captureIndices",1,4);if(slots.size()!=KneekuraDebugOwnerInputs.n(c,"captureBudget"))throw new IOException("TRIGGER_SLOT_BUDGET");
  for(JsonElement e:slots){long n=number(e);if(n<0||n>=grant.maxCaptures()/4||!seen.add(n))throw new IOException("TRIGGER_CAPTURE_SLOT");}return c.deepCopy();
 }
 static void validateIntent(KneekuraDebugOwnerInputs input,JsonObject marker,long now)throws IOException {
  long index=KneekuraDebugOwnerInputs.n(marker,"captureIndex");JsonObject c=input.triggerConfig();boolean reserved=false;
  if(c!=null)for(JsonElement e:c.getAsJsonArray("captureIndices"))reserved|=number(e)==index;
  if(!marker.has("trigger")){if(reserved)throw new IOException("CAPTURE_SLOT_RESERVED_FOR_TRIGGER");return;}
  if(c==null||!reserved)throw new IOException("TRIGGER_NOT_REGISTERED");JsonObject t=KneekuraDebugOwnerInputs.o(marker,"trigger");
  KneekuraDebugActionJournal.keys(t,"configHash","kind","observationId","windowId","triggerAt","offsetMs","deadline");
  for(String key:List.of("observationId","windowId"))KneekuraDebugArenaController.id(KneekuraDebugOwnerInputs.t(t,key));
  long at=range(t,"triggerAt",0,9007199254740991L),offset=range(t,"offsetMs",0,10000),deadline=range(t,"deadline",0,9007199254740991L);
  boolean selected=false;for(JsonElement e:c.getAsJsonArray("offsetsMs"))selected|=number(e)==offset;
  if(!KneekuraDebugOwnerInputs.t(t,"configHash").equals(KneekuraDebugOwnerInputs.t(input.envelope(),"triggerConfigHash"))||!KneekuraDebugOwnerInputs.t(t,"kind").equals("ARENA_EXIT")||!selected||deadline!=at+KneekuraDebugOwnerInputs.n(c,"timeoutMs")||at+offset>now)throw new IOException("TRIGGER_IDENTITY_OR_WINDOW");
 }
 static long deadline(JsonObject marker)throws IOException{return marker.has("trigger")?KneekuraDebugOwnerInputs.n(KneekuraDebugOwnerInputs.o(marker,"trigger"),"deadline"):Long.MAX_VALUE;}
 static long remainingMillis(long deadline,long now,long max){return deadline<=now?0:Math.min(max,deadline-now);}
 private static long number(JsonElement e)throws IOException{JsonObject o=new JsonObject();o.add("value",e);return KneekuraDebugOwnerInputs.n(o,"value");}
 private static long range(JsonObject c,String key,long min,long max)throws IOException{long n=KneekuraDebugOwnerInputs.n(c,key);if(n<min||n>max)throw new IOException("TRIGGER_"+key+"_BOUND");return n;}
 static JsonObject identity(KneekuraDebugOwnerInputs input,KneekuraDebugArenaController.Snapshot state){
  var g=input.grant();var id=g.identity();JsonObject p=new JsonObject();p.addProperty("debugSessionId",id.debugSessionId());p.addProperty("runId",id.runId());p.addProperty("runSnapshotId",id.runSnapshotId());p.addProperty("processEpoch",id.processEpoch());p.addProperty("experimentId",id.experimentId());p.addProperty("generation",g.generation());p.addProperty("requestHash",g.requestHash());p.addProperty("arenaId",state.arenaId());p.addProperty("arenaEpoch",state.arenaEpoch());p.addProperty("arenaRevision",state.arenaRevision());p.addProperty("baselineHash",g.arena().baselineHash());return p;
 }
 static final class ExitDetector {
  private final KneekuraDebugArenaController.Bounds bounds;private final int maxEvents;private final long cooldownMs;
  private final Map<String,List<Double>> previous=new HashMap<>();private int events;private Long last;
  ExitDetector(KneekuraDebugArenaController.Bounds bounds,int maxEvents,long cooldownMs){this.bounds=bounds;this.maxEvents=maxEvents;this.cooldownMs=cooldownMs;}
  void missing(String subject){previous.remove(subject);}
  JsonObject sample(String subject,List<Double> position,long now){
   if(position.size()!=3||position.stream().anyMatch(n->n==null||!Double.isFinite(n))){missing(subject);return null;}
   List<Double> before=previous.put(subject,List.copyOf(position));
   if(before==null||events>=maxEvents||!inside(before)||inside(position)||last!=null&&(now<last||now-last<cooldownMs))return null;
   events++;last=now;JsonObject p=new JsonObject();p.addProperty("transition","INSIDE_TO_OUTSIDE");p.add("previousPosition",point(before));p.add("position",point(position));return p;
  }
  private boolean inside(List<Double> p){return bounds.contains(p.get(0),p.get(1),p.get(2));}
  private JsonArray point(List<Double> p){JsonArray a=new JsonArray();p.forEach(a::add);return a;}
 }
}
