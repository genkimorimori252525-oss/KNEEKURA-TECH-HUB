package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.google.gson.*;
/** State of the existing owner connection, not an independent runtime authority/store. */
final class KneekuraDebugOwnerLifetime {
 enum Phase{WAITING,RESERVED,ACTIVE,BLOCKED,UNKNOWN,CLOSED}
 /** This receives only the owned capture future, never a request-supplied restoration claim. */
 static boolean captureRestored(JsonObject manifest,boolean barrierReleased,boolean barrierExpired){
  try{if(manifest==null)return false;JsonObject result=manifest.getAsJsonObject("result"),proof=manifest.getAsJsonObject("restorationProof");JsonObject expected=proof.getAsJsonObject("expected"),observed=proof.getAsJsonObject("observed");
   return "RESTORED".equals(result.get("restoration").getAsString())&&"MINECRAFT_API_READBACK".equals(proof.get("basis").getAsString())&&expected!=null&&expected.equals(observed)&&!observed.get("paused").getAsBoolean()&&"NONE".equals(observed.get("screen").getAsString())&&barrierReleased&&!barrierExpired;
  }catch(RuntimeException missing){return false;}
 }
 static boolean shutdownReady(boolean detached,boolean failed,boolean captureQuiescent){return detached&&!failed&&captureQuiescent;}
 static boolean requiresCleanupClose(String status){return "VERIFIED".equals(status);}
 private Phase phase=Phase.WAITING;private String envelope;
 boolean reserve(String hash){if(hash==null||!hash.matches("[a-f0-9]{64}"))throw new IllegalArgumentException("INVALID_ENVELOPE_HASH");if(phase!=Phase.WAITING)return false;envelope=hash;phase=Phase.RESERVED;return true;}
 void active(){if(phase!=Phase.RESERVED)throw new IllegalStateException("OWNER_NOT_RESERVED");phase=Phase.ACTIVE;}
 void blocked(){phase=Phase.BLOCKED;}void unknown(){phase=Phase.UNKNOWN;}void close(){phase=Phase.CLOSED;}Phase phase(){return phase;}String envelope(){return envelope;}
}
