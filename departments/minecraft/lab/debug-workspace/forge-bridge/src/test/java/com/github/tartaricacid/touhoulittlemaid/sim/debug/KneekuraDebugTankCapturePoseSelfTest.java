package com.github.tartaricacid.touhoulittlemaid.sim.debug;
import java.util.*;
public final class KneekuraDebugTankCapturePoseSelfTest {
 public static void main(String[] args){String hash="a".repeat(64);var id=new KneekuraDebugCaptureSession.Identity("session","run","snapshot",1,"experiment",1,hash,"arena",0,0,hash);var subjects=List.of(UUID.fromString("00000000-0000-0000-0000-000000000001"));
  var request=new KneekuraDebugCaptureSession.Request("capture-1",id,subjects,List.of(),List.of(7,224,6),List.of(13,235,13),90,640,480,2000,5000,true,true,KneekuraDebugCaptureSession.TANK_RIG,hash,List.of(0,224,0),List.of(52,248,52));
  List<List<Double>> expected=List.of(List.of(26.0,236.0,1.5,0.0,0.0),List.of(50.5,236.0,26.0,90.0,0.0),List.of(26.0,236.0,50.5,180.0,0.0),List.of(1.5,236.0,26.0,-90.0,0.0));
  for(int i=0;i<4;i++)if(!request.pose(KneekuraDebugCaptureSession.VIEWS.get(i)).equals(expected.get(i)))throw new AssertionError("inside-room eye pose");
  var legacy=new KneekuraDebugCaptureSession.Request("capture-1",id,subjects,List.of(),List.of(7,224,6),List.of(13,235,13),90,640,480,2000,5000,true,true);
  if(!legacy.pose("north").subList(0,3).equals(List.of(10.0,232.25,-3.0)))throw new AssertionError("legacy pose changed");
  if(!request.arenaMin().equals(legacy.arenaMin())||!request.arenaMax().equals(legacy.arenaMax()))throw new AssertionError("observation changed action authority");
  System.out.println("tank capture pose checks=6");
 }
}
