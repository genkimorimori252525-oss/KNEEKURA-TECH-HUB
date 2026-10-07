package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.*;
import java.io.IOException;
import java.util.*;

/** Half-open recipe interior; separate from all mutation authority. */
record KneekuraDebugTankObservation(JsonObject json,int minX,int minY,int minZ,int maxX,int maxY,int maxZ,int maxEntities,int maxSamples,String recipeHash) {
 static final String PERMISSION="TANK_OBSERVATION_READ";
 static KneekuraDebugTankObservation parse(JsonObject value,JsonObject world)throws IOException{
  KneekuraDebugActionJournal.keys(value,"schemaVersion","scope","dimensionId","min","max","recipeHash","maxEntities","maxSamples");
  if(KneekuraDebugOwnerInputs.n(value,"schemaVersion")!=1||!PERMISSION.equals(KneekuraDebugOwnerInputs.t(value,"scope"))||!KneekuraDebugOwnerInputs.t(value,"dimensionId").equals(KneekuraDebugOwnerInputs.t(world,"dimensionId"))||!world.getAsJsonArray("permissions").contains(new JsonPrimitive(PERMISSION)))throw new IOException("TANK_OBSERVATION_PERMISSION");
  int[] min=vector(value,"min"),max=vector(value,"max");long volume=1;
  for(int i=0;i<3;i++){long edge=(long)max[i]-min[i];if(edge<1||edge>64)throw new IOException("TANK_OBSERVATION_BOUNDS");volume*=edge;}
  if(volume>65536||min[1]<-63||max[1]>319||min[0]<-29999983||max[0]>29999984||min[2]<-29999983||max[2]>29999984)throw new IOException("TANK_OBSERVATION_BOUNDS");
  long entities=KneekuraDebugOwnerInputs.n(value,"maxEntities"),samples=KneekuraDebugOwnerInputs.n(value,"maxSamples");if(entities<1||entities>64||samples<1||samples>8)throw new IOException("TANK_OBSERVATION_BUDGET");
  return new KneekuraDebugTankObservation(value.deepCopy(),min[0],min[1],min[2],max[0],max[1],max[2],(int)entities,(int)samples,KneekuraDebugActionJournal.hash(KneekuraDebugOwnerInputs.t(value,"recipeHash")));
 }
 void verifySaved(JsonObject saved)throws IOException{
  try{var view=KneekuraDebugTankPresentationRecipe.parse(saved);var g=view.geometry();
   if(!view.recipeHash().equals(recipeHash)||g.x()!=minX||g.y()!=minY||g.z()!=minZ||g.x()+g.width()!=maxX||g.y()+g.height()!=maxY||g.z()+g.depth()!=maxZ)throw new IOException("TANK_OBSERVATION_RECIPE");
  }catch(IllegalArgumentException e){throw new IOException("TANK_OBSERVATION_RECIPE",e);}
 }
 boolean overlaps(double x0,double y0,double z0,double x1,double y1,double z1){return x0<maxX&&x1>minX&&y0<maxY&&y1>minY&&z0<maxZ&&z1>minZ;}
 boolean contains(double x0,double y0,double z0,double x1,double y1,double z1){return x0>=minX&&y0>=minY&&z0>=minZ&&x1<=maxX&&y1<=maxY&&z1<=maxZ;}
 private static int[] vector(JsonObject o,String key)throws IOException{JsonArray a=KneekuraDebugOwnerInputs.a(o,key,3,3);int[] out=new int[3];for(int i=0;i<3;i++)try{if(!a.get(i).isJsonPrimitive()||!a.get(i).getAsJsonPrimitive().isNumber())throw new IllegalArgumentException();out[i]=a.get(i).getAsBigDecimal().intValueExact();}catch(RuntimeException e){throw new IOException("TANK_OBSERVATION_VECTOR",e);}return out;}
}
