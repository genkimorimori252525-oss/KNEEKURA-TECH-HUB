package com.github.tartaricacid.touhoulittlemaid.sim.debug;
public final class KneekuraDebugMotionOverlayGeometrySelfTest {
 public static void main(String[] args){
  String uuid="00000000-0000-0000-0000-000000000001";
  var fresh=KneekuraDebugMotionOverlayGeometry.ageStyle("MOB_ACTUAL",uuid,100,100);
  var middle=KneekuraDebugMotionOverlayGeometry.ageStyle("MOB_ACTUAL",uuid,100,134);
  var old=KneekuraDebugMotionOverlayGeometry.ageStyle("MOB_ACTUAL",uuid,100,167);
  if(fresh.r()!=105||fresh.g()!=215||fresh.b()!=255||middle.r()!=255||middle.g()!=211||old.r()!=255||old.g()!=96)throw new AssertionError("blue/yellow/red age bands");
  if(KneekuraDebugMotionOverlayGeometry.ageStyle("MOB_ACTUAL",uuid,100,200)!=null||KneekuraDebugMotionOverlayGeometry.ageStyle("MOB_ACTUAL",uuid,100,99)!=null)throw new AssertionError("expired/future style");
  if(KneekuraDebugMotionOverlayGeometry.ageStyle("MOB_ACTUAL",uuid,100,199).alpha()>=old.alpha())throw new AssertionError("old trace must fade");
  var bullet=KneekuraDebugMotionOverlayGeometry.ageStyle("PROJECTILE_ACTUAL",uuid,100,100);
  if(!bullet.equals(KneekuraDebugMotionOverlayGeometry.ageStyle("PROJECTILE_ACTUAL",uuid,100,100))||bullet.equals(KneekuraDebugMotionOverlayGeometry.ageStyle("PROJECTILE_ACTUAL","00000000-0000-0000-0000-000000000002",100,100)))throw new AssertionError("stable projectile identity color");
  var cache=new KneekuraDebugMotionTraceCache();cache.select(KneekuraDebugMotionTraceCacheSelfTest.context(1));
  cache.acceptFlushed(KneekuraDebugMotionTraceCacheSelfTest.row(100,0,"obs:1"));cache.acceptFlushed(KneekuraDebugMotionTraceCacheSelfTest.row(105,1,"obs:2"));
  var lines=KneekuraDebugMotionOverlayGeometry.lines(cache.snapshot(),"minecraft:overworld",105,0,64,0);
  if(lines.size()!=5||lines.stream().anyMatch(l->l.sourceIds().isEmpty()))throw new AssertionError("sampled line and markers require real IDs");
  if(!KneekuraDebugMotionOverlayGeometry.lines(cache.snapshot(),"minecraft:the_nether",105,0,64,0).isEmpty())throw new AssertionError("dimension leak");
  if(!KneekuraDebugMotionOverlayGeometry.lines(cache.snapshot(),"minecraft:overworld",300,0,64,0).isEmpty())throw new AssertionError("stale capture shown");
  if(!KneekuraDebugMotionOverlayGeometry.lines(cache.snapshot(),"minecraft:overworld",99,0,64,0).isEmpty())throw new AssertionError("future capture shown");
  if(!KneekuraDebugMotionOverlayGeometry.lines(cache.snapshot(),"minecraft:overworld",105,1000,64,0).isEmpty())throw new AssertionError("unbounded remote drawing");
  var projectile=new KneekuraDebugMotionTraceCache();projectile.select(KneekuraDebugMotionTraceCacheSelfTest.context(1));
  for(int i=0;i<2;i++){var row=KneekuraDebugMotionTraceCacheSelfTest.row(100+i*5,i,"obs:p"+i);row.getAsJsonObject("payload").addProperty("motionTraceClass","PROJECTILE_ACTUAL");projectile.acceptFlushed(row);}
  if(KneekuraDebugMotionOverlayGeometry.lines(projectile.snapshot(),"minecraft:overworld",105,0,64,0).size()!=9)throw new AssertionError("projectile requires dashed line and distinct 3-axis markers");
  if(!KneekuraDebugMotionOverlayGeometry.lines(cache.snapshot(),"minecraft:overworld",105,0,64,0,false).isEmpty())throw new AssertionError("derived drawing must be absent during raw capture");
  if(!KneekuraDebugMotionOverlayGeometry.lines(cache.snapshot(),"minecraft:overworld",105,0,64,0,true).equals(lines))throw new AssertionError("capture completion must resume the same retained view without deleting evidence");
  for(int tick=110;tick<=150;tick+=5)cache.acceptFlushed(KneekuraDebugMotionTraceCacheSelfTest.row(tick,1,"obs:stopped:"+tick));
  for(long tick:new long[]{150,180}){
   var stopped=KneekuraDebugMotionOverlayGeometry.lines(cache.snapshot(),"minecraft:overworld",tick,0,64,0,true);
   if(stopped.stream().noneMatch(l->l.role().equals("SAMPLED_ENDPOINT_CONNECTION")&&l.x0()!=l.x1()))throw new AssertionError("stationary Mob retains unexpired movement");
  }
  if(KneekuraDebugMotionOverlayGeometry.lines(cache.snapshot(),"minecraft:overworld",205,0,64,0,true).stream().anyMatch(l->l.role().equals("SAMPLED_ENDPOINT_CONNECTION")&&l.x0()!=l.x1()))throw new AssertionError("stationary Mob cannot refresh older movement age");
  System.out.println("Native overlay geometry retains source refs, gap/age/dimension/distance boundaries and non-color styles");
 }
}
