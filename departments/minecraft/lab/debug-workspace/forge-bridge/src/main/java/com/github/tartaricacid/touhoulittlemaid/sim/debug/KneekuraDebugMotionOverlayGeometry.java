package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import java.util.*;
/** Pure bounded derived lines; no game objects, world mutation, interpolation of samples or camera takeover. */
final class KneekuraDebugMotionOverlayGeometry {
 record Line(double x0,double y0,double z0,double x1,double y1,double z1,String traceClass,String role,List<String> sourceIds) { }
 static List<Line> lines(KneekuraDebugMotionTraceCache.Snapshot trace,String dimension,long gameTime,double cameraX,double cameraY,double cameraZ) {
  return lines(trace,dimension,gameTime,cameraX,cameraY,cameraZ,true);
 }
 static List<Line> lines(KneekuraDebugMotionTraceCache.Snapshot trace,String dimension,long gameTime,double cameraX,double cameraY,double cameraZ,boolean captureQuiescent) {
  // Raw Cardinal owns the framebuffer through restoration and its final durable acknowledgement.
  if(!captureQuiescent)return List.of();
  var out=new ArrayList<Line>();var visible=new HashSet<Integer>();
  for(int i=0;i<trace.samples().size();i++){
   var s=trace.samples().get(i);
   if(!s.dimension().equals(dimension)||s.tick()>gameTime||gameTime-s.tick()>100||
     Math.hypot(Math.hypot(s.x()-cameraX,s.y()-cameraY),s.z()-cameraZ)>64)continue;
   visible.add(i);var ids=List.of(s.sourceId());double r=0.06;
   out.add(new Line(s.x()-r,s.y(),s.z(),s.x()+r,s.y(),s.z(),s.traceClass(),"RETAINED_SAMPLE_MARKER",ids));
   out.add(new Line(s.x(),s.y(),s.z()-r,s.x(),s.y(),s.z()+r,s.traceClass(),"RETAINED_SAMPLE_MARKER",ids));
   if(s.traceClass().equals("PROJECTILE_ACTUAL"))out.add(new Line(s.x(),s.y()-r,s.z(),s.x(),s.y()+r,s.z(),s.traceClass(),"RETAINED_SAMPLE_MARKER",ids));
  }
  for(var segment:trace.segments()){
   if(!visible.contains(segment.from())||!visible.contains(segment.to())||segment.distance()==0)continue;
   var a=trace.samples().get(segment.from());var b=trace.samples().get(segment.to());var ids=List.of(a.sourceId(),b.sourceId());
   int pieces=a.traceClass().equals("PROJECTILE_ACTUAL")?3:1;
   for(int i=0;i<pieces;i++){
    double from=pieces==1?0:i*0.4,to=pieces==1?1:Math.min(1,from+0.2);
    out.add(new Line(a.x()+(b.x()-a.x())*from,a.y()+(b.y()-a.y())*from,a.z()+(b.z()-a.z())*from,
      a.x()+(b.x()-a.x())*to,a.y()+(b.y()-a.y())*to,a.z()+(b.z()-a.z())*to,a.traceClass(),"SAMPLED_ENDPOINT_CONNECTION",ids));
   }
  }
  if(out.size()>1024)throw new IllegalStateException("BOUNDED_OVERLAY_GEOMETRY_EXCEEDED");
  return List.copyOf(out);
 }
}
