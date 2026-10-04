package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import java.util.*;
/** Pure bounded derived lines and labels; no game objects, world mutation, interpolation or camera takeover. */
final class KneekuraDebugMotionOverlayGeometry {
 record AgeStyle(int r,int g,int b,int alpha,String ageBand) { }
 record Line(double x0,double y0,double z0,double x1,double y1,double z1,String traceClass,String role,List<String> sourceIds,AgeStyle style) { }
 record Label(UUID uuid,double x,double y,double z,long sampleTick,String text,List<String> sourceIds,AgeStyle style) { }
 static AgeStyle ageStyle(String traceClass,String identity,long sampleTick,long gameTime) {
  if(!Set.of("MOB_ACTUAL","PROJECTILE_ACTUAL").contains(traceClass)||identity==null||identity.isEmpty()||identity.length()>512||sampleTick<0||gameTime<0)throw new IllegalArgumentException("INVALID_TRACE_AGE_STYLE");
  if(sampleTick>gameTime||gameTime-sampleTick>=100)return null;
  long age=gameTime-sampleTick;int band=(int)(age*3/100);int[] yellow={255,211,83},red={255,96,83},rgb={105,215,255};
  if(traceClass.equals("PROJECTILE_ACTUAL")) {
   int hash=0x811c9dc5;for(int i=0;i<identity.length();i++)hash=(hash^identity.charAt(i))*16777619;
   double hue=(100+Integer.remainderUnsigned(hash,180))/60.0;int sector=(int)Math.floor(hue);double f=hue-sector,low=76.5,up=low+178.5*f,down=255-178.5*f;
   double[] base=switch(sector){case 1->new double[]{down,255,low};case 2->new double[]{low,255,up};case 3->new double[]{low,down,255};case 4->new double[]{up,low,255};default->throw new IllegalStateException("IDENTITY_HUE_RANGE");};
   for(int i=0;i<3;i++){rgb[i]=(int)Math.round(base[i]);if(band>0)rgb[i]=(int)Math.round(rgb[i]*(band==1?.5:.18)+(band==1?yellow:red)[i]*(band==1?.5:.82));}
  }else if(band>0)rgb=band==1?yellow:red;
  int alpha=band==0?255:band==1?210:(int)Math.round(180.0*(100-age)/33);
  return new AgeStyle(rgb[0],rgb[1],rgb[2],alpha,switch(band){case 0->"NEW";case 1->"MIDDLE";default->"OLD";});
 }
 static List<Line> lines(KneekuraDebugMotionTraceCache.Snapshot trace,String dimension,long gameTime,double cameraX,double cameraY,double cameraZ) {
  return lines(trace,dimension,gameTime,cameraX,cameraY,cameraZ,true);
 }
 static List<Line> lines(KneekuraDebugMotionTraceCache.Snapshot trace,String dimension,long gameTime,double cameraX,double cameraY,double cameraZ,boolean captureQuiescent) {
  return linesForIdentity(trace,trace.context()==null?null:trace.context().uuid().toString(),dimension,gameTime,cameraX,cameraY,cameraZ,captureQuiescent);
 }
 static List<Line> linesForIdentity(KneekuraDebugMotionTraceCache.Snapshot trace,String identity,String dimension,long gameTime,double cameraX,double cameraY,double cameraZ,boolean captureQuiescent) {
  // Raw Cardinal owns the framebuffer through restoration and its final durable acknowledgement.
  if(!captureQuiescent||trace.context()==null)return List.of();
  var out=new ArrayList<Line>();var visible=new HashMap<Integer,AgeStyle>();
  for(int i=0;i<trace.samples().size();i++){
   var s=trace.samples().get(i);
   if(!s.dimension().equals(dimension)||s.tick()>gameTime||gameTime-s.tick()>=100||
     Math.hypot(Math.hypot(s.x()-cameraX,s.y()-cameraY),s.z()-cameraZ)>64)continue;
   var ids=List.of(s.sourceId());double r=0.06;var style=ageStyle(s.traceClass(),identity,s.tick(),gameTime);visible.put(i,style);
   out.add(new Line(s.x()-r,s.y(),s.z(),s.x()+r,s.y(),s.z(),s.traceClass(),"RETAINED_SAMPLE_MARKER",ids,style));
   out.add(new Line(s.x(),s.y(),s.z()-r,s.x(),s.y(),s.z()+r,s.traceClass(),"RETAINED_SAMPLE_MARKER",ids,style));
   if(s.traceClass().equals("PROJECTILE_ACTUAL"))out.add(new Line(s.x(),s.y()-r,s.z(),s.x(),s.y()+r,s.z(),s.traceClass(),"RETAINED_SAMPLE_MARKER",ids,style));
  }
  for(var segment:trace.segments()){
   if(!visible.containsKey(segment.from())||!visible.containsKey(segment.to())||segment.distance()==0)continue;
   var a=trace.samples().get(segment.from());var b=trace.samples().get(segment.to());var ids=List.of(a.sourceId(),b.sourceId());
   int pieces=a.traceClass().equals("PROJECTILE_ACTUAL")?3:1;
   for(int i=0;i<pieces;i++){
    double from=pieces==1?0:i*0.4,to=pieces==1?1:Math.min(1,from+0.2);
    out.add(new Line(a.x()+(b.x()-a.x())*from,a.y()+(b.y()-a.y())*from,a.z()+(b.z()-a.z())*from,
      a.x()+(b.x()-a.x())*to,a.y()+(b.y()-a.y())*to,a.z()+(b.z()-a.z())*to,a.traceClass(),"SAMPLED_ENDPOINT_CONNECTION",ids,visible.get(segment.to())));
   }
  }
  if(out.size()>1024)throw new IllegalStateException("BOUNDED_OVERLAY_GEOMETRY_EXCEEDED");
  return List.copyOf(out);
 }
 static List<Line> combinedLines(KneekuraDebugMotionTraceCache.Snapshot selected,KneekuraDebugRelatedProjectileTraceCache.Snapshot related,String dimension,long gameTime,double cameraX,double cameraY,double cameraZ,boolean captureQuiescent) {
  var out=new ArrayList<>(lines(selected,dimension,gameTime,cameraX,cameraY,cameraZ,captureQuiescent));
  if(selected.context()!=null&&Objects.equals(selected.context(),related.context()))for(var group:related.traces())
   out.addAll(linesForIdentity(group.trace(),group.uuid().toString(),dimension,gameTime,cameraX,cameraY,cameraZ,captureQuiescent));
  if(out.size()>2048)throw new IllegalStateException("BOUNDED_COMBINED_OVERLAY_GEOMETRY_EXCEEDED");
  return List.copyOf(out);
 }
 static Map<UUID,String> labelNames(List<UUID> identities) {
  if(identities.size()>16)throw new IllegalArgumentException("BOUNDED_PROJECTILE_LABEL_IDENTITIES_EXCEEDED");
  var shortNames=new LinkedHashMap<UUID,String>();var counts=new HashMap<String,Integer>();
  for(var uuid:new LinkedHashSet<>(identities)){String id=uuid.toString(),name="P "+id.substring(0,4)+".."+id.substring(28);shortNames.put(uuid,name);counts.merge(name,1,Integer::sum);}
  var names=new LinkedHashMap<UUID,String>();shortNames.forEach((uuid,name)->names.put(uuid,counts.get(name)>1?"P "+uuid:name));
  return Map.copyOf(names);
 }
 static List<Label> relatedLabels(KneekuraDebugMotionTraceCache.Snapshot selected,KneekuraDebugRelatedProjectileTraceCache.Snapshot related,String dimension,long gameTime,double cameraX,double cameraY,double cameraZ,boolean captureQuiescent) {
  if(!captureQuiescent||selected.context()==null||!Objects.equals(selected.context(),related.context())||gameTime<0||!Double.isFinite(cameraX)||!Double.isFinite(cameraY)||!Double.isFinite(cameraZ))return List.of();
  var names=labelNames(related.traces().stream().map(KneekuraDebugRelatedProjectileTraceCache.Trace::uuid).toList());var labels=new ArrayList<Label>();
  for(var group:related.traces()) {
   var samples=group.trace().samples();if(samples.isEmpty())continue;
   // Last retained observation only: do not select an older point when the latest is ineligible.
   var sample=samples.get(samples.size()-1);
   if(!sample.dimension().equals(dimension)||Math.hypot(Math.hypot(sample.x()-cameraX,sample.y()-cameraY),sample.z()-cameraZ)>64)continue;
   var style=ageStyle("PROJECTILE_ACTUAL",group.uuid().toString(),sample.tick(),gameTime);if(style==null)continue;
   labels.add(new Label(group.uuid(),sample.x(),sample.y(),sample.z(),sample.tick(),names.get(group.uuid()),List.of(group.spawnSource(),sample.sourceId()),style));
  }
  return List.copyOf(labels);
 }
}
