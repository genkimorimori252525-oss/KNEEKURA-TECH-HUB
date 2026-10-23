package kneekura.manual;

import com.google.gson.*;
import com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugEnv;
import java.nio.file.Path;
import java.util.Set;

/** Pure fail-closed request checks; no world, input, control or launch operations. */
public final class ManualRequest {
 private ManualRequest(){}
 private static final Set<String> FIELDS=Set.of("v","purpose","mode","nonce","playerUuid","subjectUuid","trialDir","worldDir","maxTicks","maxWallMs","maxEvents","captures","grants","sourceRevisions","productHash","adapterHash","installHash","materials");
 private static void require(boolean value,String why){if(!value)throw new IllegalArgumentException("MANUAL_"+why);}
 private static boolean bounded(JsonElement element,int minimum,int maximum){if(element==null||!element.isJsonPrimitive()||!element.getAsJsonPrimitive().isNumber())return false;double x=element.getAsDouble();return Double.isFinite(x)&&x==Math.rint(x)&&x>=minimum&&x<=maximum;}
 private static String text(JsonObject obj,String key){var x=obj.get(key);require(x!=null&&x.isJsonPrimitive()&&x.getAsJsonPrimitive().isString(),"STRING_"+key);return x.getAsString();}
 public static void validate(JsonObject r){
  boolean diagnostic=bounded(r.get("v"),3,3),visual=diagnostic||bounded(r.get("v"),2,2);var fields=new java.util.HashSet<>(FIELDS);if(visual)fields.add("presentation");if(diagnostic)fields.add("diagnostics");require(r.keySet().equals(fields),"EXACT_FIELDS");require(bounded(r.get("v"),1,3),"VERSION");if(visual)ManualPresentation.validate(r.getAsJsonObject("presentation"));if(diagnostic)ManualDiagnosticsLimits.validate(r.getAsJsonObject("diagnostics"),r.get("maxWallMs").getAsLong());require(text(r,"purpose").equals("MANUAL_INTERACTION"),"PURPOSE");require(Set.of("LIFECYCLE","MANUAL_RALLY","MANUAL_OBSERVE").contains(text(r,"mode")),"MODE");
  for(String key:Set.of("nonce","playerUuid","subjectUuid"))require(text(r,key).matches("(?i)[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}"),"UUID_"+key);
  require(!text(r,"playerUuid").equals(text(r,"subjectUuid")),"DISTINCT_ACTORS");
  require(bounded(r.get("maxTicks"),1,2400)&&bounded(r.get("maxWallMs"),1,120000)&&bounded(r.get("maxEvents"),1,512)&&bounded(r.get("captures"),0,0),"BOUNDS");
  require(r.get("grants").isJsonArray()&&r.getAsJsonArray("grants").size()==(diagnostic?3:visual?2:1)&&r.getAsJsonArray("grants").get(0).getAsString().equals("MANUAL_EVENT_OBSERVATION")&&(!visual||r.getAsJsonArray("grants").get(1).getAsString().equals("CLIENT_TANK_GRID_PRESENTATION"))&&(!diagnostic||r.getAsJsonArray("grants").get(2).getAsString().equals("FINITE_MOTION_DIAGNOSTICS")),"GRANTS");
  var revisions=r.getAsJsonObject("sourceRevisions");require(revisions.keySet().equals(Set.of("target","techHub")),"SOURCE_FIELDS");for(String key:revisions.keySet())require(key.equals("target")&&text(revisions,key).equals("ARTIFACT_ONLY")||text(revisions,key).matches("[a-f0-9]{40}"),"SOURCE_PIN");
  for(String key:Set.of("productHash","adapterHash","installHash"))require(text(r,key).matches("[a-f0-9]{64}"),"MATERIAL_PIN");
  var materials=r.getAsJsonArray("materials");require(materials!=null&&materials.size()<=32,"MATERIALS");var ids=new java.util.HashSet<String>();for(var element:materials){var m=element.getAsJsonObject();require(m.keySet().equals(Set.of("id","sha256")),"MATERIAL_FIELDS");String id=text(m,"id");require(id.matches("[a-z][a-z0-9_]{1,63}")&&!Set.of("kneekura_manual_adapter","kneekura_tank_host").contains(id)&&ids.add(id),"MATERIAL_ID");require(text(m,"sha256").matches("[a-f0-9]{64}"),"MATERIAL_HASH");}
  Path trial=Path.of(text(r,"trialDir")),world=Path.of(text(r,"worldDir"));require(trial.isAbsolute()&&world.isAbsolute()&&world.normalize().equals(trial.normalize().resolve("game/saves/KNEEKURA_DEBUG_WORLD")),"PRIVATE_WORLD");
 }
 public static boolean stopMatches(JsonObject r,KneekuraDebugEnv.Config c){try{return r.keySet().equals(Set.of("v","debugSessionId","runId","runSnapshotId","processEpoch","requestedAt"))&&bounded(r.get("v"),1,1)&&text(r,"debugSessionId").equals(c.debugSessionId())&&text(r,"runId").equals(c.runId())&&text(r,"runSnapshotId").equals(c.runSnapshotId())&&bounded(r.get("processEpoch"),c.processEpoch(),c.processEpoch())&&java.time.Instant.parse(text(r,"requestedAt"))!=null;}catch(RuntimeException invalid){return false;}}
}
