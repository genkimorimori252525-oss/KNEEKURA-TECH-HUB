package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import com.google.gson.*;
public final class KneekuraDebugTankObservationSelfTest {
 public static void main(String[] args)throws Exception{
  JsonObject world=JsonParser.parseString("{\"dimensionId\":\"minecraft:overworld\",\"permissions\":[\"TANK_OBSERVATION_READ\"]}").getAsJsonObject();
  JsonObject scope=JsonParser.parseString("{\"schemaVersion\":1,\"scope\":\"TANK_OBSERVATION_READ\",\"dimensionId\":\"minecraft:overworld\",\"min\":[-17,224,-17],\"max\":[35,248,35],\"recipeHash\":\""+"a".repeat(64)+"\",\"maxEntities\":64,\"maxSamples\":8}").getAsJsonObject();
  var s=KneekuraDebugTankObservation.parse(scope,world);int checks=0;
  if(!s.overlaps(-18,230,0,-16,234,4)||s.contains(-18,230,0,-16,234,4))throw new AssertionError("body overlaps with base outside");checks++;
  if(s.overlaps(35,230,0,36,234,4)||s.overlaps(-18,230,0,-17,234,4))throw new AssertionError("touching faces are not positive overlap");checks++;
  if(!s.contains(30,240,30,35,248,35))throw new AssertionError("body maximum may reach exclusive face");checks++;
  for(String field:new String[]{"maxEntities","maxSamples"}){JsonObject bad=scope.deepCopy();bad.addProperty(field,999);reject(()->KneekuraDebugTankObservation.parse(bad,world));checks++;}
  JsonObject bad=scope.deepCopy();bad.add("max",JsonParser.parseString("[47,288,47]"));reject(()->KneekuraDebugTankObservation.parse(bad,world));checks++;
  JsonObject wrong=scope.deepCopy();wrong.add("min",JsonParser.parseString("[\"-17\",224,-17]"));reject(()->KneekuraDebugTankObservation.parse(wrong,world));checks++;
  System.out.println("tank observation checks="+checks);
 }
 interface Check{void run()throws Exception;}
 static void reject(Check c)throws Exception{try{c.run();}catch(java.io.IOException expected){return;}throw new AssertionError("unsafe scope accepted");}
}
