package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.google.gson.*;
public final class KneekuraDebugOwnerLifetimeSelfTest {
 public static void main(String[] args)throws Exception{
  var state=new KneekuraDebugOwnerLifetime();if(!state.reserve("a".repeat(64)))throw new AssertionError("first attempt");state.active();if(state.reserve("a".repeat(64)))throw new AssertionError("active reinstalls");state.close();if(state.reserve("a".repeat(64)))throw new AssertionError("closed renews lease");if(state.reserve("b".repeat(64)))throw new AssertionError("same process changes grant");var failed=new KneekuraDebugOwnerLifetime();failed.reserve("a".repeat(64));failed.unknown();if(failed.reserve("a".repeat(64)))throw new AssertionError("unknown replay");JsonObject manifest=new JsonObject(), result=new JsonObject(), proof=new JsonObject(), observed=new JsonObject();
  result.addProperty("status","PARTIAL");result.addProperty("restoration","RESTORED");manifest.add("result",result);observed.addProperty("cameraUuid","known-camera");observed.addProperty("paused",false);observed.addProperty("screen","NONE");proof.add("expected",observed.deepCopy());proof.add("observed",observed.deepCopy());proof.addProperty("basis","MINECRAFT_API_READBACK");manifest.add("restorationProof",proof);
  if(!KneekuraDebugOwnerLifetime.captureRestored(manifest,true,false))throw new AssertionError("partial evidence with verified restoration");
  JsonObject wrong=manifest.deepCopy();wrong.getAsJsonObject("result").addProperty("restoration","UNKNOWN");if(KneekuraDebugOwnerLifetime.captureRestored(wrong,true,false))throw new AssertionError("unknown restoration clears fence");
  wrong=manifest.deepCopy();wrong.getAsJsonObject("restorationProof").getAsJsonObject("observed").addProperty("paused",true);if(KneekuraDebugOwnerLifetime.captureRestored(wrong,true,false))throw new AssertionError("unrestored pause clears fence");
  if(KneekuraDebugOwnerLifetime.captureRestored(manifest,false,false))throw new AssertionError("held barrier clears fence");
  if(KneekuraDebugOwnerLifetime.captureRestored(manifest,true,true))throw new AssertionError("expired barrier clears fence");
  if(KneekuraDebugOwnerLifetime.captureRestored(null,false,true))throw new AssertionError("exception/timeout clears fence");
  if(KneekuraDebugOwnerLifetime.shutdownReady(true,false,false))throw new AssertionError("detached but late capture manifest may still enqueue");
  if(KneekuraDebugOwnerLifetime.shutdownReady(false,false,true))throw new AssertionError("pending detach cannot seal");
  if(KneekuraDebugOwnerLifetime.shutdownReady(true,true,true))throw new AssertionError("failed detach cannot seal");
  if(!KneekuraDebugOwnerLifetime.shutdownReady(true,false,true))throw new AssertionError("quiescent detached owner may seal");
  if(!KneekuraDebugOwnerLifetime.requiresCleanupClose("VERIFIED"))throw new AssertionError("verified epoch-changing cleanup must close original grant");
  if(KneekuraDebugOwnerLifetime.requiresCleanupClose("OUTCOME_UNKNOWN"))throw new AssertionError("unknown cleanup cannot imply completed cleanup");
  System.out.println("one-shot owner lifecycle/restoration/shutdown/cleanup fence checks=17");
 }
}
