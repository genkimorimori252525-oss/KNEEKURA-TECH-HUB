package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import java.nio.file.*;
import java.util.*;
public final class KneekuraDebugOwnerEnvSelfTest {
 static int checks;
 static void check(boolean b,String label){checks++;if(!b)throw new AssertionError(label);}
 static void reject(Runnable r,String label){try{r.run();throw new AssertionError(label);}catch(IllegalArgumentException expected){checks++;}}
 static Map<String,String> env(Path root){Map<String,String> e=new HashMap<>();e.put("KNEEKURA_DEBUG_ENABLED","1");e.put("KNEEKURA_DEBUG_SESSION_ID","session");e.put("KNEEKURA_DEBUG_RUN_ID","run");e.put("KNEEKURA_DEBUG_PROCESS_EPOCH","1");e.put("KNEEKURA_DEBUG_RUN_SNAPSHOT_ID","snapshot");e.put("KNEEKURA_DEBUG_HANDSHAKE_NONCE","nonce-0000000000000001");e.put("KNEEKURA_DEBUG_WORLD_NAME","KNEEKURA_DEBUG_WORLD");for(String key:List.of("READY_FILE","EVIDENCE_RAW_DIR","TARGET_FILE","SHUTDOWN_REQUEST_FILE","SHUTDOWN_ACK_FILE"))e.put("KNEEKURA_DEBUG_"+key,root.resolve(key).toString());e.put("KNEEKURA_DEBUG_RUN_DIR",root.toString());e.put("KNEEKURA_DEBUG_RUNTIME_ROOT",root.toString());return e;}
 public static void main(String[] args)throws Exception{
  Path root=Files.createTempDirectory("owner-env").toRealPath();var e=env(root);
  check(KneekuraDebugEnv.fromEnvironment(e).ownerSetup()==null,"legacy absence inert");
  e.put("KNEEKURA_DEBUG_OWNER_ENVELOPE_FILE",root.resolve("control/owner-envelope.json").toString());reject(()->KneekuraDebugEnv.fromEnvironment(e),"partial owner pair");
  e.put("KNEEKURA_DEBUG_OWNER_ENVELOPE_SHA256","a".repeat(64));check(KneekuraDebugEnv.fromEnvironment(e).ownerSetup().sha256().equals("a".repeat(64)),"fixed owner path/hash");
  e.put("KNEEKURA_DEBUG_OWNER_ENVELOPE_FILE",root.resolve("foreign.json").toString());reject(()->KneekuraDebugEnv.fromEnvironment(e),"foreign owner path");
  e.put("KNEEKURA_DEBUG_OWNER_ENVELOPE_FILE",root.resolve("control/owner-envelope.json").toString());e.put("KNEEKURA_DEBUG_OWNER_ENVELOPE_SHA256","TRUE");reject(()->KneekuraDebugEnv.fromEnvironment(e),"invalid hash is not permission");
  System.out.println("owner Env checks="+checks);
 }
}
