package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.google.gson.*;
import java.util.*;
import java.io.IOException;
public final class KneekuraDebugOwnerDispatchSelfTest {
 public static void main(String[] args)throws Exception{
  var f=KneekuraDebugOwnerInputsSelfTest.fixture();var input=KneekuraDebugOwnerInputs.load(f.config());String key=KneekuraDebugOwnerDispatch.actionKey(input,"wait");
  JsonObject expected=new JsonObject();expected.addProperty("actionId","wait");expected.addProperty("processEpoch",1);expected.addProperty("requestHash",input.grant().requestHash());expected.addProperty("runId","run");expected.addProperty("runSnapshotId","snapshot");if(!key.equals(KneekuraDebugActionJournal.sha256(KneekuraDebugActionJournal.canonical(expected))))throw new AssertionError("Node key mapping");
  JsonObject action=KneekuraDebugOwnerDispatch.action(input,"wait",0,0);JsonObject dispatch=new JsonObject();dispatch.addProperty("schemaVersion",1);dispatch.addProperty("ownerEnvelopeHash",input.envelopeHash());dispatch.addProperty("runSnapshotId","snapshot");dispatch.addProperty("runSnapshotHash",input.snapshotHash());dispatch.addProperty("requestHash",input.grant().requestHash());dispatch.addProperty("handshakeNonce",input.grant().identity().handshakeNonce());dispatch.addProperty("leaseId",input.grant().leaseId());dispatch.addProperty("selectedActionId","wait");dispatch.addProperty("idempotencyKey",key);dispatch.addProperty("payloadHash",KneekuraDebugActionJournal.sha256(KneekuraDebugActionJournal.canonical(action)));
  KneekuraDebugOwnerDispatch.validate(input,dispatch,action,KneekuraDebugActionJournal.canonical(action).getBytes(java.nio.charset.StandardCharsets.UTF_8),0);int checks=2;
  JsonObject wrong=action.deepCopy();wrong.getAsJsonObject("args").addProperty("ticks",2);JsonObject forged=dispatch.deepCopy();forged.addProperty("payloadHash",KneekuraDebugActionJournal.sha256(KneekuraDebugActionJournal.canonical(wrong)));try{KneekuraDebugOwnerDispatch.validate(input,forged,wrong,KneekuraDebugActionJournal.canonical(wrong).getBytes(java.nio.charset.StandardCharsets.UTF_8),0);throw new AssertionError("invented args");}catch(IOException expectedError){checks++;}
  forged=dispatch.deepCopy();forged.addProperty("idempotencyKey","a".repeat(64));try{KneekuraDebugOwnerDispatch.validate(input,forged,action,KneekuraDebugActionJournal.canonical(action).getBytes(java.nio.charset.StandardCharsets.UTF_8),0);throw new AssertionError("alternate replay key");}catch(IOException expectedError){checks++;}
  try{KneekuraDebugOwnerDispatch.validate(input,dispatch,action,KneekuraDebugActionJournal.canonical(action).getBytes(java.nio.charset.StandardCharsets.UTF_8),1);throw new AssertionError("repeated action order");}catch(IOException expectedError){checks++;}
  System.out.println("sealed action selector checks="+checks);
 }
}
