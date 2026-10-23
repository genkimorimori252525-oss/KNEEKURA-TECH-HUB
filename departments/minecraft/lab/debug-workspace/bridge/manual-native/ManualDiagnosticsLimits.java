package kneekura.manual;
import com.google.gson.*;
import java.util.Set;
public final class ManualDiagnosticsLimits {
 public static final String SCHEMA_HASH="04f8199d9e640211d62ec0d98879f5346e467d3d76ed3a41bda3235d02b8f899";
 private ManualDiagnosticsLimits(){}
 public static double displacement(double[] before,double[] after){
  if(before==null)return -1;
  if(before.length!=3||after.length!=3)throw new IllegalArgumentException("DIAGNOSTIC_POSITION");
  double distance=Math.hypot(Math.hypot(after[0]-before[0],after[1]-before[1]),after[2]-before[2]);
  if(!Double.isFinite(distance))throw new IllegalArgumentException("DIAGNOSTIC_POSITION_FINITE");return distance;
 }
 public static long deadline(long original,long started,long wallMs){return original-started<=wallMs*1_000_000L?original:started+wallMs*1_000_000L;}
 public static String admission(JsonObject limits,String side,int count,long usedBytes,int nextBytes,long now,long deadline){
  String cap=switch(side){case "SERVER"->"maxServerSamples";case "CLIENT"->"maxClientSamples";case "FRAME"->"maxFrameSamples";default->throw new IllegalArgumentException("DIAGNOSTIC_SIDE");};
  if(now>=deadline)return "SUBLEASE_EXPIRED";
  if(count<0||usedBytes<0||nextBytes<0)throw new IllegalArgumentException("DIAGNOSTIC_COUNTER");
  if(count>=limits.get(cap).getAsInt())return "SAMPLE_LIMIT";
  if(nextBytes>limits.get("maxBytes").getAsLong()-usedBytes)return "BYTE_LIMIT";
  return "ALLOW";
 }
 public static void validate(JsonObject d,long parentWall){
  if(d==null||!d.keySet().equals(Set.of("schemaHash","startTrigger","maxWallMs","maxServerSamples","maxClientSamples","maxFrameSamples","maxBytes","maxQueue"))||!d.get("schemaHash").isJsonPrimitive()||!d.get("schemaHash").getAsJsonPrimitive().isString()||!SCHEMA_HASH.equals(d.get("schemaHash").getAsString()))throw new IllegalArgumentException("MANUAL_DIAGNOSTIC_SCHEMA_FIELDS");
  if(!d.get("startTrigger").isJsonPrimitive()||!d.get("startTrigger").getAsJsonPrimitive().isString()||!Set.of("READY","SUBJECT_MOTION").contains(d.get("startTrigger").getAsString()))throw new IllegalArgumentException("MANUAL_DIAGNOSTIC_TRIGGER");
  String[] keys={"maxWallMs","maxServerSamples","maxClientSamples","maxFrameSamples","maxBytes","maxQueue"};int[] maxima={20000,400,400,1200,1048576,64};
  for(int i=0;i<keys.length;i++){var x=d.get(keys[i]);if(!x.isJsonPrimitive()||!x.getAsJsonPrimitive().isNumber())throw new IllegalArgumentException("MANUAL_DIAGNOSTIC_NUMBER");double n=x.getAsDouble();if(!Double.isFinite(n)||n!=Math.rint(n)||n<1||n>maxima[i])throw new IllegalArgumentException("MANUAL_DIAGNOSTIC_BOUND");}
  if(d.get("maxWallMs").getAsLong()>parentWall)throw new IllegalArgumentException("MANUAL_DIAGNOSTIC_SUBLEASE");
 }
}
