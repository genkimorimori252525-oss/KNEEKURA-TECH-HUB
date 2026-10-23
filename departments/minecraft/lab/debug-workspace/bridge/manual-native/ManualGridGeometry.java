package kneekura.manual;

/** Exact geometry/color of the existing KneekuraDebugTankView.Grid display. */
public final class ManualGridGeometry {
 public static final int RED=90,GREEN=102,BLUE=118,ALPHA=255;
 private ManualGridGeometry(){}
 @FunctionalInterface public interface Segment {void line(double x,double y,double z,double a,double b,double c);}
 public static int emit(int[] min,int[] max,Segment out){
  double x0=min[0]+.003,x1=max[0]-.003,y0=min[1]+.003,y1=max[1]-.003,z0=min[2]+.003,z1=max[2]-.003;int count=0;
  for(int x=min[0];x<=max[0];x++){
   for(double y:new double[]{y0,y1}){out.line(x,y,z0,x,y,z1);count++;}
   for(double z:new double[]{z0,z1}){out.line(x,y0,z,x,y1,z);count++;}
  }
  for(int z=min[2];z<=max[2];z++){
   for(double y:new double[]{y0,y1}){out.line(x0,y,z,x1,y,z);count++;}
   for(double x:new double[]{x0,x1}){out.line(x,y0,z,x,y1,z);count++;}
  }
  for(int y=min[1];y<=max[1];y++){
   for(double z:new double[]{z0,z1}){out.line(x0,y,z,x1,y,z);count++;}
   for(double x:new double[]{x0,x1}){out.line(x,y,z0,x,y,z1);count++;}
  }
  return count;
 }
}
