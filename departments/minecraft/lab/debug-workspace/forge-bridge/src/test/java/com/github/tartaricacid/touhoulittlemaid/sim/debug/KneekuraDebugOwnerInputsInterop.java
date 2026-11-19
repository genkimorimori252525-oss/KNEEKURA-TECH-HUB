package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.google.gson.*;
import java.nio.file.*;
import java.io.*;
import java.util.*;
/** Tests only the actual Node closure/parser; never installs a Minecraft owner. */
public final class KneekuraDebugOwnerInputsInterop {
 public static void main(String[] args)throws Exception{
  Path fixture=Path.of(args[0]);JsonObject context=KneekuraDebugActionJournal.object(KneekuraDebugActionJournal.parse(Files.readString(fixture.resolve("context.json"))));Path run=Path.of(context.get("runDir").getAsString());JsonObject id=context.getAsJsonObject("identity");Map<String,String> env=KneekuraDebugOwnerEnvSelfTest.env(run);
  for(var pair:Map.of("debugSessionId","SESSION_ID","runId","RUN_ID","runSnapshotId","RUN_SNAPSHOT_ID","processEpoch","PROCESS_EPOCH","handshakeNonce","HANDSHAKE_NONCE").entrySet())env.put("KNEEKURA_DEBUG_"+pair.getValue(),id.get(pair.getKey()).getAsString());
  env.put("KNEEKURA_DEBUG_OWNER_ENVELOPE_FILE",run.resolve("control/owner-envelope.json").toString());env.put("KNEEKURA_DEBUG_OWNER_ENVELOPE_SHA256",context.get("envelopeHash").getAsString());
  System.out.println("OWNER_SOURCE_JVM_PID="+ProcessHandle.current().pid());System.out.flush();if(new BufferedReader(new InputStreamReader(System.in)).readLine()==null)throw new IOException("NODE_SNAPSHOT_NOT_COMMITTED");
  var input=KneekuraDebugOwnerInputs.load(KneekuraDebugEnv.fromEnvironment(env));System.out.println("NODE_JAVA_OWNER_INPUTS_VERIFIED request="+input.grant().requestHash()+"; tankRotation="+(input.tankRotation()!=null)+"; parser only; runtime installation NOT_RUN");
 }
}
