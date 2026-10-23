package kneekura.manual;
import com.google.gson.*;
import java.util.Set;
public final class ManualDiagnosticsLimits {
 public static final String SCHEMA_HASH="a06284789167a3632d58058738402b0dcf24bfee7c5412a8d68cd58d65bec61d";
 private ManualDiagnosticsLimits(){}
 public static String admission(JsonObject limits,String side,int count,long usedBytes,int nextBytes,long now,long deadline){
  String cap=switch(side){case "SERVER"->"maxServerSamples";case "CLIENT"->"maxClientSamples";case "FRAME"->"maxFrameSamples";default->throw new IllegalArgumentException("DIAGNOSTIC_SIDE");};
  if(now>=deadline)return "SUBLEASE_EXPIRED";
  if(count<0||usedBytes<0||nextBytes<0)throw new IllegalArgumentException("DIAGNOSTIC_COUNTER");
  if(count>=limits.get(cap).getAsInt())return "SAMPLE_LIMIT";
  if(nextBytes>limits.get("maxBytes").getAsLong()-usedBytes)return "BYTE_LIMIT";
  return "ALLOW";
 }
 public static void validate(JsonObject d,long parentWall){
  if(d==null||!d.keySet().equals(Set.of("schemaHash","maxWallMs","maxServerSamples","maxClientSamples","maxFrameSamples","maxBytes","maxQueue"))||!d.get("schemaHash").isJsonPrimitive()||!d.get("schemaHash").getAsJsonPrimitive().isString()||!SCHEMA_HASH.equals(d.get("schemaHash").getAsString()))throw new IllegalArgumentException("MANUAL_DIAGNOSTIC_SCHEMA_FIELDS");
  String[] keys={"maxWallMs","maxServerSamples","maxClientSamples","maxFrameSamples","maxBytes","maxQueue"};int[] maxima={20000,400,400,1200,1048576,64};
  for(int i=0;i<keys.length;i++){var x=d.get(keys[i]);if(!x.isJsonPrimitive()||!x.getAsJsonPrimitive().isNumber())throw new IllegalArgumentException("MANUAL_DIAGNOSTIC_NUMBER");double n=x.getAsDouble();if(!Double.isFinite(n)||n!=Math.rint(n)||n<1||n>maxima[i])throw new IllegalArgumentException("MANUAL_DIAGNOSTIC_BOUND");}
  if(d.get("maxWallMs").getAsLong()>parentWall)throw new IllegalArgumentException("MANUAL_DIAGNOSTIC_SUBLEASE");
 }
}
