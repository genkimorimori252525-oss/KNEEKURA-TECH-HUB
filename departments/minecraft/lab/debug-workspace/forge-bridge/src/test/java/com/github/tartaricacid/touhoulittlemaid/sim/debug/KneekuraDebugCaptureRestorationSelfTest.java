package com.github.tartaricacid.touhoulittlemaid.sim.debug;
public final class KneekuraDebugCaptureRestorationSelfTest {
 public static void main(String[] args) {
  var expected=new KneekuraDebugCaptureRestoration.State("camera","FIRST_PERSON",false,true,70,false,true,"NONE",1,2,3,4,5);
  if(!KneekuraDebugCaptureRestoration.exact(expected,expected))throw new AssertionError("identity restoration");
  if(KneekuraDebugCaptureRestoration.exact(expected,new KneekuraDebugCaptureRestoration.State("camera","FIRST_PERSON",false,true,70,true,true,"NONE",1,2,3,4,5)))throw new AssertionError("pause still active");
  if(KneekuraDebugCaptureRestoration.exact(expected,new KneekuraDebugCaptureRestoration.State("foreign","FIRST_PERSON",false,true,70,false,true,"NONE",1,2,3,4,5)))throw new AssertionError("camera changed");
  if(KneekuraDebugCaptureRestoration.exact(expected,new KneekuraDebugCaptureRestoration.State("camera","FIRST_PERSON",false,true,71,false,true,"NONE",1,2,3,4,5)))throw new AssertionError("fov changed");
  if(KneekuraDebugCaptureRestoration.exact(expected,new KneekuraDebugCaptureRestoration.State("camera","FIRST_PERSON",false,true,70,false,true,"NONE",1,2,4,4,5)))throw new AssertionError("position changed");
  System.out.println("restoration checks=5");
 }
}
