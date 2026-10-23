package kneekura.manual;
import com.google.gson.*;
import java.nio.file.Path;
public final class ManualRequestSelfTest {
 public static void main(String[] args){
  var r=new JsonObject();r.addProperty("v",1);r.addProperty("purpose","MANUAL_INTERACTION");r.addProperty("mode","LIFECYCLE");
  r.addProperty("nonce","d7c0405b-e75e-4d0e-a96d-54de595ef944");r.addProperty("playerUuid","11111111-1111-4111-8111-111111111111");r.addProperty("subjectUuid","22222222-2222-4222-8222-222222222222");
  var trial=Path.of(System.getProperty("java.io.tmpdir"),"manual-validation").toAbsolutePath();r.addProperty("trialDir",trial.toString());r.addProperty("worldDir",trial.resolve("game/saves/KNEEKURA_DEBUG_WORLD").toString());
  r.addProperty("maxTicks",40);r.addProperty("maxWallMs",2000);r.addProperty("maxEvents",256);r.addProperty("captures",0);var grants=new JsonArray();grants.add("MANUAL_EVENT_OBSERVATION");r.add("grants",grants);
  var revisions=new JsonObject();revisions.addProperty("target","1".repeat(40));revisions.addProperty("techHub","2".repeat(40));r.add("sourceRevisions",revisions);r.addProperty("productHash","3".repeat(64));r.addProperty("adapterHash","4".repeat(64));r.addProperty("installHash","5".repeat(64));r.add("materials",new JsonArray());ManualRequest.validate(r);
  int checks=1;for(String name:new String[]{"native_input","scoped_mutation","MOTION_TRACE"}){var x=r.deepCopy();x.getAsJsonArray("grants").add(name);reject(x);checks++;}
  for(String key:new String[]{"purpose","mode","nonce","playerUuid","worldDir","productHash"}){var x=r.deepCopy();x.addProperty(key,"invalid");reject(x);checks++;}
  for(String key:new String[]{"maxTicks","maxWallMs","maxEvents","captures"}){var x=r.deepCopy();x.addProperty(key,-1);reject(x);checks++;}
  var fractional=r.deepCopy();fractional.addProperty("maxTicks",1.5);reject(fractional);checks++;
  var extra=r.deepCopy();extra.addProperty("autoStart",true);reject(extra);checks++;
  var binary=r.deepCopy();binary.getAsJsonObject("sourceRevisions").addProperty("target","ARTIFACT_ONLY");ManualRequest.validate(binary);checks++;
  binary.getAsJsonObject("sourceRevisions").addProperty("techHub","ARTIFACT_ONLY");reject(binary);checks++;
  var c=new com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugEnv.Config(true,"session","run",1,"snapshot","nonce-at-least-sixteen",trial,trial,trial,trial,trial,trial,trial,"KNEEKURA_DEBUG_WORLD");
  var stop=new JsonObject();stop.addProperty("v",1);stop.addProperty("debugSessionId","session");stop.addProperty("runId","run");stop.addProperty("runSnapshotId","snapshot");stop.addProperty("processEpoch",1);stop.addProperty("requestedAt",java.time.Instant.now().toString());
  if(!ManualRequest.stopMatches(stop,c))throw new AssertionError("MATCHING_STOP_REJECTED");checks++;
  for(String key:new String[]{"debugSessionId","runId","runSnapshotId","requestedAt"}){var x=stop.deepCopy();x.addProperty(key,"foreign");if(ManualRequest.stopMatches(x,c))throw new AssertionError("FOREIGN_STOP_ACCEPTED");checks++;}
  var epoch=stop.deepCopy();epoch.addProperty("processEpoch",2);if(ManualRequest.stopMatches(epoch,c))throw new AssertionError("FOREIGN_EPOCH_ACCEPTED");checks++;
  var stopped=new java.util.concurrent.atomic.AtomicBoolean();var failed=new java.util.concurrent.atomic.AtomicBoolean();
  ManualShutdown.request(()->{throw new java.io.IOException("INJECTED_RECEIPT_WRITE_FAILURE");},()->stopped.set(true),e->failed.set(e instanceof java.io.IOException));
  if(!stopped.get()||!failed.get())throw new AssertionError("RECEIPT_FAILURE_SUPPRESSED_STOP");checks++;
  stopped.set(false);ManualShutdown.request(()->{},()->stopped.set(true),e->{throw new AssertionError("UNEXPECTED_RECEIPT_FAILURE",e);});if(!stopped.get())throw new AssertionError("NORMAL_STOP_SUPPRESSED");checks++;
  var visual=r.deepCopy();visual.addProperty("v",2);visual.getAsJsonArray("grants").add("CLIENT_TANK_GRID_PRESENTATION");
  var p=JsonParser.parseString("{\"renderer\":\"tank-grid-v1\",\"grid\":true,\"brightness\":\"NATIVE\",\"recipeHash\":\"1e2ebacaf6dd1a3589fdfac681adccc28f91a5f77addabe54269fb269ad52aef\",\"min\":[0,224,0],\"max\":[52,248,52]}").getAsJsonObject();visual.add("presentation",p);ManualRequest.validate(visual);checks++;
  var saved=JsonParser.parseString("{\"status\":\"GEOMETRY_VERIFIED\",\"recipeHash\":\"sha256:1e2ebacaf6dd1a3589fdfac681adccc28f91a5f77addabe54269fb269ad52aef\",\"recipe\":{\"v\":1,\"kind\":\"tank_recipe\",\"dimension\":\"minecraft:overworld\",\"origin\":{\"x\":0,\"y\":224,\"z\":0},\"dimensions\":{\"width\":52,\"height\":24,\"depth\":52}}}").getAsJsonObject();
  try{ManualPresentation.matchesSaved(p,saved);}catch(Exception e){throw new AssertionError("MATCHED_GRID_RECIPE_REJECTED",e);}checks++;
  for(String key:new String[]{"renderer","brightness","recipeHash"}){var x=visual.deepCopy();x.getAsJsonObject("presentation").addProperty(key,"foreign");reject(x);checks++;}
  var missingGrant=visual.deepCopy();missingGrant.getAsJsonArray("grants").remove(1);reject(missingGrant);checks++;
  var implicit=r.deepCopy();implicit.add("presentation",p);reject(implicit);checks++;
  for(var change:new String[]{"fractional","tooLarge","wrongBoolean","camera"}){var x=visual.deepCopy();var q=x.getAsJsonObject("presentation");switch(change){case "fractional" -> q.getAsJsonArray("min").set(0,new JsonPrimitive(.5));case "tooLarge" -> q.getAsJsonArray("max").set(0,new JsonPrimitive(100));case "wrongBoolean" -> q.addProperty("grid","true");default -> q.addProperty("camera",true);}reject(x);checks++;}
  var mismatch=saved.deepCopy();mismatch.getAsJsonObject("recipe").getAsJsonObject("origin").addProperty("x",1);boolean rejected=false;try{ManualPresentation.matchesSaved(p,mismatch);}catch(Exception expected){rejected=true;}if(!rejected)throw new AssertionError("CHANGED_WORLD_RECIPE_ACCEPTED");checks++;
  System.out.println("PASS "+checks+" Java manual request/STOP/grid boundary checks");
 }
 private static void reject(JsonObject x){try{ManualRequest.validate(x);}catch(RuntimeException expected){return;}throw new AssertionError("INVALID_MANUAL_REQUEST_ACCEPTED");}
}
