package com.github.tartaricacid.touhoulittlemaid.sim.debug;
public final class KneekuraDebugMotionOverlayGeometrySelfTest {
 public static void main(String[] args){
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
  System.out.println("Native overlay geometry retains source refs, gap/age/dimension/distance boundaries and non-color styles");
 }
}
