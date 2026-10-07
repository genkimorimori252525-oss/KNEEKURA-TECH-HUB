package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.google.gson.*;
import java.io.IOException;
public final class KneekuraDebugMobPovCommandsSelfTest {
 public static void main(String[] args)throws Exception{
  var fixture=KneekuraDebugOwnerInputsSelfTest.fixture();var input=KneekuraDebugOwnerInputs.load(fixture.config());
  JsonObject rig=new JsonObject();rig.addProperty("mode","mob-eye-live-v1");rig.addProperty("fov",60);JsonArray viewport=new JsonArray();viewport.add(64);viewport.add(64);rig.add("viewport",viewport);
  input.request().add("visual_rig",rig);input.world().getAsJsonArray("permissions").add("MOB_POV_CAMERA");
  var grant=input.grant();var id=grant.identity();var arena=grant.arena();var state=new KneekuraDebugArenaController.Snapshot(id,arena.arenaId(),arena.arenaEpoch(),arena.arenaRevision(),grant.leaseId(),true,false);
  JsonObject marker=new JsonObject();marker.addProperty("schemaVersion",1);marker.addProperty("commandIndex",0);marker.addProperty("operation","attach");
  marker.addProperty("ownerEnvelopeHash",input.envelopeHash());marker.addProperty("runSnapshotId",id.runSnapshotId());marker.addProperty("runSnapshotHash",input.snapshotHash());marker.addProperty("requestHash",grant.requestHash());marker.addProperty("handshakeNonce",id.handshakeNonce());marker.addProperty("leaseId",grant.leaseId());marker.addProperty("expectedArenaEpoch",arena.arenaEpoch());marker.addProperty("expectedArenaRevision",arena.arenaRevision());
  marker.addProperty("subjectUuid",grant.subjects().values().iterator().next().uuid());marker.addProperty("durationMs",1000);
  int checks=0;if(KneekuraDebugMobPovCommands.parse(input,marker,0,state).durationMs()!=1000)throw new AssertionError("attach duration");checks++;
  for(String fault:new String[]{"order","subject","nonce","revision","duration","injection","permission"}){
   JsonObject bad=marker.deepCopy();int next=0;
   switch(fault){case "order"->next=1;case "subject"->bad.addProperty("subjectUuid","ffffffff-ffff-ffff-ffff-ffffffffffff");case "nonce"->bad.addProperty("handshakeNonce","wrong");case "revision"->bad.addProperty("expectedArenaRevision",999);case "duration"->bad.addProperty("durationMs",120001);case "injection"->bad.addProperty("executable","cmd");case "permission"->input.world().getAsJsonArray("permissions").remove(input.world().getAsJsonArray("permissions").size()-1);}
   try{KneekuraDebugMobPovCommands.parse(input,bad,next,state);throw new AssertionError(fault);}catch(IOException expected){checks++;}
  }
  System.out.println("mob POV sealed command checks="+checks);
 }
}
